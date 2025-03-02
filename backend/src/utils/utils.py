# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import FrozenSet, NewType, Tuple, Union, cast

from src.project_reader.version import InvalidVersion, Version

BuildTag = Union[Tuple[()], Tuple[int, str]]
NormalizedName = NewType("NormalizedName", str)


class InvalidWheelFilename(ValueError):
    """An invalid wheel filename was found, users should refer to PEP 427."""


class InvalidSdistFilename(ValueError):
    """An invalid sdist filename was found, users should refer to the packaging user guide."""


_canonicalize_regex = re.compile(r"[-_.]+")
_build_tag_regex = re.compile(r"(\d+)(.*)")  # PEP 427: The build number must start with a digit.


def canonicalize_name(name: str) -> NormalizedName:
    """Converts a package name to its canonical form."""
    value = _canonicalize_regex.sub("-", name).lower()
    return cast(NormalizedName, value)


def canonicalize_version(version: Union[Version, str]) -> str:
    """Normalizes a version string based on PEP 440."""
    if isinstance(version, str):
        try:
            parsed = Version(version)
        except InvalidVersion:
            return version  # Legacy versions cannot be normalized
    else:
        parsed = version

    parts = []

    if parsed.epoch != 0:
        parts.append(f"{parsed.epoch}!")

    parts.append(re.sub(r"(\.0)+$", "", ".".join(str(x) for x in parsed.release)))

    if parsed.pre is not None:
        parts.append("".join(str(x) for x in parsed.pre))

    if parsed.post is not None:
        parts.append(f".post{parsed.post}")

    if parsed.dev is not None:
        parts.append(f".dev{parsed.dev}")

    if parsed.local is not None:
        parts.append(f"+{parsed.local}")

    return "".join(parts)


def parse_wheel_filename(
    filename: str,
) -> Tuple[NormalizedName, Version, BuildTag, FrozenSet]:
    """Parses a valid wheel filename according to PEP 427."""
    if not filename.endswith(".whl"):
        raise InvalidWheelFilename(f"Invalid wheel filename (must end in '.whl'): {filename}")

    filename = filename[:-4]
    dashes = filename.count("-")
    if dashes not in (4, 5):
        raise InvalidWheelFilename(f"Invalid wheel filename (wrong number of parts): {filename}")

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
            raise InvalidWheelFilename(f"Invalid build number: {build_part} in '{filename}'")
        build = cast(BuildTag, (int(build_match.group(1)), build_match.group(2)))
    else:
        build = ()

    from project_reader.tags import (
        parse_tag,
    )  # ✅ Moved import inside function to prevent circular imports

    tags = parse_tag(parts[-1])

    return name, version, build, tags


def parse_sdist_filename(filename: str) -> Tuple[NormalizedName, Version]:
    """Parses a valid source distribution filename."""
    if filename.endswith(".tar.gz"):
        file_stem = filename[: -len(".tar.gz")]
    elif filename.endswith(".zip"):
        file_stem = filename[: -len(".zip")]
    else:
        raise InvalidSdistFilename(f"Invalid sdist filename (must be '.tar.gz' or '.zip'): {filename}")

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

    :param log_dir: Directory where logs will be stored.
    :param log_file_name: Name of the log file.
    :return: Path to the log file.
    """
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception as e:
        print(f"Error creating log directory: {e}")
        sys.exit(1)

    log_file_path = os.path.join(log_dir, log_file_name)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.info(f"Log file initialized at: {log_file_path}")
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
        with open(config_path, "r") as config_file:
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
