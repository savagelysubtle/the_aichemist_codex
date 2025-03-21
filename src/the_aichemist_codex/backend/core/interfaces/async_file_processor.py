"""
AsyncFileProcessor interface.

This module defines the interface for asynchronous file processing.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

# Type aliases to be used in implementations
ChunkProcessor = Callable[[bytes], bytes]
AsyncChunkProcessor = Callable[[bytes], Any]  # Any represents a coroutine
ResultCollector = Callable[[list[bytes]], Any]


class AsyncFileProcessor(ABC):
    """
    Interface for asynchronous file processing.

    This interface defines methods for processing files asynchronously
    using memory-mapped I/O and a producer-consumer pattern.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the file processor."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close any resources used by the file processor."""
        pass

    @abstractmethod
    async def process_file(
        self,
        input_file: str,
        output_file: str,
        processor: ChunkProcessor | AsyncChunkProcessor,
        chunk_size: int | None = None,
        mode: Any = None,  # Implementations can define their own enum
        num_workers: int | None = None,
        result_collector: ResultCollector | None = None,
    ) -> Any:
        """
        Process a file using a producer-consumer pattern with memory-mapped I/O.

        Args:
            input_file: Path to the input file
            output_file: Path to the output file
            processor: Function to process each chunk
            chunk_size: Size of each chunk in bytes
            mode: Processing mode (sequential, parallel, or streaming)
            num_workers: Number of worker tasks
            result_collector: Function to collect and process results

        Returns:
            Result of the processing operation
        """
        pass
