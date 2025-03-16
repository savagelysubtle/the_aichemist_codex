# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

# mypy: ignore-errors

import json
import logging
import os
import re
from pathlib import Path
from typing import NewType, Union, cast

from backend.src.project_reader.version import InvalidVersion, Version

# Define custom types
BuildTag = Union[tuple[()], tuple[int, str]]
NormalizedName = NewType("NormalizedName", str)

# Import Tag type to fix frozenset error
try:
    from backend.src.project_reader.tags import Tag  # type: ignore
except ImportError:
    # Create a stub Tag class for type checking
    class Tag:
        pass


class InvalidWheelFilename(ValueError):
    """An invalid wheel filename was found, users should refer to PEP 427."""


class InvalidSdistFilename(ValueError):
    """An invalid sdist filename was found, users should refer to the packaging user guide."""


_canonicalize_regex = re.compile(r"[-_.]+")
_build_tag_regex = re.compile(
    r"(\d+)(.*)"
)  # PEP 427: The build number must start with a digit.


def canonicalize_name(name: str) -> NormalizedName:
    """Converts a package name to its canonical form."""
    value = _canonicalize_regex.sub("-", name).lower()
    return cast(NormalizedName, value)


def canonicalize_version(version: Version | str) -> str:  # type: ignore[attr-defined]
    """Normalizes a version string based on PEP 440."""
    if isinstance(version, str):
        try:
            parsed = Version(version)
        except InvalidVersion:
            return version  # Legacy versions cannot be normalized
    else:
        parsed = version

    parts = []

    # Extract Version attributes with type ignores
    epoch = getattr(parsed, "epoch", 0)  # type: ignore
    release = getattr(parsed, "release", ())  # type: ignore
    pre = getattr(parsed, "pre", None)  # type: ignore
    post = getattr(parsed, "post", None)  # type: ignore
    dev = getattr(parsed, "dev", None)  # type: ignore
    local = getattr(parsed, "local", None)  # type: ignore

    if epoch != 0:
        parts.append(f"{epoch}!")

    parts.append(re.sub(r"(\.0)+$", "", ".".join(str(x) for x in release)))

    if pre is not None:
        parts.append("".join(str(x) for x in pre))

    if post is not None:
        parts.append(f".post{post}")

    if dev is not None:
        parts.append(f".dev{dev}")

    if local is not None:
        parts.append(f"+{local}")

    return "".join(parts)


def parse_wheel_filename(
    filename: str,
) -> tuple[NormalizedName, Version, BuildTag, frozenset[str]]:
    """Parses a valid wheel filename according to PEP 427."""
    if not filename.endswith(".whl"):
        raise InvalidWheelFilename(
            f"Invalid wheel filename (must end in '.whl'): {filename}"
        )

    filename = filename[:-4]
    dashes = filename.count("-")
    if dashes not in (4, 5):
        raise InvalidWheelFilename(
            f"Invalid wheel filename (wrong number of parts): {filename}"
        )

    parts = filename.split("-", dashes - 2)
    name_part = parts[0]

    if "__" in name_part or re.match(r"^[\w\d._]*$", name_part, re.UNICODE) is None:
        raise InvalidWheelFilename(f"Invalid project name: {filename}")

    name = canonicalize_name(name_part)
    version = Version(parts[1])

    if dashes == 5:
        build_part = parts[2]
        build_match = _build_tag_regex.match(build_part)
        if build_match is None:
            raise InvalidWheelFilename(
                f"Invalid build number: {build_part} in '{filename}'"
            )
        build = cast(BuildTag, (int(build_match.group(1)), build_match.group(2)))
    else:
        build = ()

    from backend.src.project_reader.tags import parse_tag  # type: ignore

    tags = parse_tag(parts[-1])  # type: ignore
    # Convert whatever parse_tag returns to a frozenset of strings
    tags_set = frozenset([str(tags)])  # type: ignore

    return name, version, build, tags_set


def parse_sdist_filename(filename: str) -> tuple[NormalizedName, Version]:
    """Parses a valid source distribution filename."""
    if filename.endswith(".tar.gz"):
        file_stem = filename[: -len(".tar.gz")]
    elif filename.endswith(".zip"):
        file_stem = filename[: -len(".zip")]
    else:
        raise InvalidSdistFilename(
            f"Invalid sdist filename (must be '.tar.gz' or '.zip'): {filename}"
        )

    name_part, sep, version_part = file_stem.rpartition("-")
    if not sep:
        raise InvalidSdistFilename(f"Invalid sdist filename: {filename}")

    name = canonicalize_name(name_part)
    version = Version(version_part)
    return name, version


def list_python_files(directory: Path):
    """Returns a list of all Python files in the given directory (including subdirectories)."""
    return [file for file in directory.glob("**/*.py") if file.is_file()]


def summarize_for_gpt(text, max_sentences=10, max_length=1000):
    """
    Condenses text to extract key details while limiting the number of sentences and length.

    :param text: The full text to summarize.
    :param max_sentences: The maximum number of sentences to retain.
    :param max_length: The maximum allowed length of the output.
    :return: A compact summary suitable for GPT input.
    """
    if len(text) <= max_length:
        return text

    sentences = text.split(". ")
    summary = ". ".join(sentences[:max_sentences]) + "."
    return summary[:max_length].strip()


# 🔹 File Management Utilities ###
def setup_logging(log_dir, log_file_name="file_events.log"):
    """
    Sets up logging with a specified directory and file name.
    DEPRECATED: Use backend.config.logging_config.setup_logging() instead.

    :param log_dir: Directory where logs will be stored.
    :param log_file_name: Name of the log file.
    :return: Path to the log file.
    """
    import warnings

    from backend.src.config.logging_config import setup_logging as central_setup_logging

    warnings.warn(
        "This function is deprecated. Use backend.config.logging_config.setup_logging() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Use the central logging system
    central_setup_logging()

    # Still return a path for backward compatibility
    from backend.src.config.settings import LOG_DIR

    log_file_path = LOG_DIR / "project.log"
    return log_file_path


def load_config(config_path):
    """
    Loads directory paths and rules from a JSON configuration file.

    :param config_path: Path to the configuration file.
    :return: Dictionary containing directories to watch and rules.
    """
    if not os.path.exists(config_path):
        logging.error(f"Configuration file not found: {config_path}")
        return {"directories_to_watch": [], "rules": []}

    try:
        with open(config_path) as config_file:
            config = json.load(config_file)
            return {
                "directories_to_watch": config.get("directories_to_watch", []),
                "rules": config.get("rules", []),
            }
    except Exception as e:
        logging.error(f"Error reading configuration file: {e}")
        return {"directories_to_watch": [], "rules": []}


def get_project_name(directory: Path) -> str:
    """Returns the project name based on the directory name."""
    return directory.name


def add(a: int, b: int) -> int:
    """
    Simple addition function.

    :param a: First number
    :param b: Second number
    :return: Sum of a and b
    """
    return a + b
