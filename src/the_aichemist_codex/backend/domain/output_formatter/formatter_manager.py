"""
Formatter manager for the output formatter system.

This module provides a centralized manager for accessing and using various formatters.
"""

import logging
from typing import Any, Dict, List, Optional, Type, Union

from ...core.exceptions import ConfigError
from ...core.interfaces import OutputFormatter as OutputFormatterInterface
from ...registry import Registry
from .formatters import (
    BaseFormatter,
    TextFormatter,
    HtmlFormatter,
    MarkdownFormatter,
    JsonFormatter
)

logger = logging.getLogger(__name__)


class FormatterManager(OutputFormatterInterface):
    """
    Manager for output formatters.

    This class manages a collection of formatters and provides a unified interface
    for formatting data in various output formats.
    """

    def __init__(self):
        """Initialize the formatter manager."""
        self._registry = Registry.get_instance()
        self._formatters: Dict[str, BaseFormatter] = {}
        self._default_format = "text"
        self._is_initialized = False

    async def initialize(self) -> None:
        """Initialize the formatter manager."""
        if self._is_initialized:
            return

        logger.info("Initializing FormatterManager")

        # Register built-in formatters
        self.register_formatter(TextFormatter())
        self.register_formatter(HtmlFormatter())
        self.register_formatter(MarkdownFormatter())
        self.register_formatter(JsonFormatter())

        # Get default format from config
        config = self._registry.config_provider
        self._default_format = config.get_config("output_formatter.default_format", "text")

        self._is_initialized = True
        logger.info("FormatterManager initialized successfully")

    async def close(self) -> None:
        """Close the formatter manager."""
        if not self._is_initialized:
            return

        logger.info("Closing FormatterManager")
        self._is_initialized = False

    def register_formatter(self, formatter: BaseFormatter) -> None:
        """
        Register a formatter.

        Args:
            formatter: The formatter to register

        Raises:
            ValueError