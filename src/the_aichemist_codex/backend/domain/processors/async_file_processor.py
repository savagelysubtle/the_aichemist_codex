"""
Asynchronous file processor module.

This module provides high-performance asynchronous file processing capabilities
using memory-mapped I/O and a producer-consumer pattern for efficient handling
of large files.
"""

import asyncio
import logging
import mmap
import os
from collections.abc import Callable
from enum import Enum, auto
from typing import Any, TypeVar, cast

from ...core.exceptions.file_error import FileError
from ...core.exceptions.processing_error import ProcessingError
from ...core.interfaces.async_file_processor import AsyncFileProcessor
from ...registry import Registry, register_service

logger = logging.getLogger(__name__)

# Type for the chunk processing function
ChunkProcessor = Callable[[bytes], bytes]
# Type for the async chunk processing function
AsyncChunkProcessor = Callable[[bytes], asyncio.Future[bytes]]
# Generic type for the result collector function
T = TypeVar("T")
ResultCollector = Callable[[list[bytes]], T]


class ProcessingMode(Enum):
    """Defines the processing mode for the file processor."""

    SEQUENTIAL = auto()  # Process chunks in order
    PARALLEL = auto()  # Process chunks in parallel
    STREAMING = auto()  # Stream chunks as they are processed


class AsyncFileProcessorImpl(AsyncFileProcessor):
    """
    Implementation of AsyncFileProcessor for high-performance file processing.

    This class provides methods for processing large files asynchronously using
    memory-mapped I/O and a producer-consumer pattern for efficient handling.
    """

    def __init__(self):
        """Initialize the AsyncFileProcessor instance."""
        self._registry = Registry.get_instance()
        self._validator = cast(Any, self._registry).file_validator
        self._paths = cast(Any, self._registry).project_paths

        # Default chunk size (10MB)
        self._default_chunk_size = 10 * 1024 * 1024

        # Default number of worker tasks
        self._default_workers = min(os.cpu_count() or 4, 8)

        # Maximum queue size
        self._max_queue_size = 20

    async def initialize(self) -> None:
        """Initialize the file processor."""
        logger.info("Initialized AsyncFileProcessor")

    async def close(self) -> None:
        """Close any resources used by the file processor."""
        logger.debug("Closed AsyncFileProcessor")

    async def process_file(
        self,
        input_file: str,
        output_file: str,
        processor: ChunkProcessor | AsyncChunkProcessor,
        chunk_size: int | None = None,
        mode: ProcessingMode = ProcessingMode.PARALLEL,
        num_workers: int | None = None,
        result_collector: ResultCollector | None = None,
    ) -> Any:
        """
        Process a file using a producer-consumer pattern with memory-mapped I/O.

        Args:
            input_file: Path to the input file
            output_file: Path to the output file
            processor: Function to process each chunk
            chunk_size: Size of each chunk in bytes (default: 10MB)
            mode: Processing mode (sequential, parallel, or streaming)
            num_workers: Number of worker tasks (default: based on CPU count)
            result_collector: Function to collect and process results

        Returns:
            Result of the processing operation

        Raises:
            FileError: If there is an error accessing the files
            ProcessingError: If there is an error during processing
        """
        # Validate file paths
        self._validator.ensure_path_safe(input_file)
        self._validator.ensure_path_safe(output_file)

        # Resolve paths
        input_path = self._paths.resolve_path(input_file)
        output_path = self._paths.resolve_path(output_file)

        # Ensure input file exists
        if not input_path.exists():
            raise FileError(
                f"Input file does not exist: {input_file}", file_path=input_file
            )

        # Set default values
        if chunk_size is None:
            chunk_size = self._default_chunk_size

        if num_workers is None:
            num_workers = self._default_workers

        # Create queues for the producer-consumer pattern
        input_queue = asyncio.Queue(maxsize=self._max_queue_size)
        output_queue = asyncio.Queue(maxsize=self._max_queue_size)

        # Create tasks based on the processing mode
        try:
            # Start producer task (always runs)
            producer_task = asyncio.create_task(
                self._read_file_chunks(str(input_path), input_queue, chunk_size)
            )

            # Start worker tasks
            worker_tasks = []

            if mode == ProcessingMode.SEQUENTIAL:
                # Sequential processing (one worker)
                worker_tasks.append(
                    asyncio.create_task(
                        self._process_chunks_sequential(
                            input_queue, output_queue, processor
                        )
                    )
                )
            elif mode == ProcessingMode.PARALLEL:
                # Parallel processing (multiple workers)
                for _ in range(num_workers):
                    worker_tasks.append(
                        asyncio.create_task(
                            self._process_chunks_parallel(
                                input_queue, output_queue, processor
                            )
                        )
                    )
            elif mode == ProcessingMode.STREAMING:
                # Streaming mode (process chunks as they arrive)
                worker_tasks.append(
                    asyncio.create_task(
                        self._process_chunks_streaming(
                            input_queue, output_queue, processor
                        )
                    )
                )

            # Start consumer task (always runs)
            consumer_task = asyncio.create_task(
                self._write_processed_chunks(str(output_path), output_queue)
            )

            # Wait for all tasks to complete
            await asyncio.gather(producer_task, *worker_tasks, consumer_task)

            # Collect results if needed
            if result_collector:
                return result_collector([])

            return True

        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise ProcessingError(f"Error processing file: {e}")

    async def _read_file_chunks(
        self, file_path: str, queue: asyncio.Queue, chunk_size: int
    ) -> None:
        """
        Read chunks from a file using memory-mapped I/O and put them in the queue.

        Args:
            file_path: Path to the file
            queue: Queue to put chunks into
            chunk_size: Size of each chunk in bytes
        """
        try:
            file_size = os.path.getsize(file_path)

            with open(file_path, "rb") as f:
                # Use memory-mapped I/O for efficient reading
                with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
                    for position in range(0, len(mm), chunk_size):
                        # Read a chunk and put it in the queue
                        chunk = mm[position : min(position + chunk_size, len(mm))]
                        await queue.put(chunk)

                        # Yield to other tasks periodically
                        await asyncio.sleep(0)

            # Signal end of file with None
            await queue.put(None)
            logger.debug(f"Finished reading file: {file_path}")

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            # Signal error
            await queue.put(None)
            raise FileError(f"Error reading file: {e}", file_path=file_path)

    async def _process_chunks_sequential(
        self,
        input_queue: asyncio.Queue,
        output_queue: asyncio.Queue,
        processor: ChunkProcessor | AsyncChunkProcessor,
    ) -> None:
        """
        Process chunks from the input queue in sequential order.

        Args:
            input_queue: Queue to get chunks from
            output_queue: Queue to put processed chunks into
            processor: Function to process each chunk
        """
        try:
            while True:
                # Get a chunk from the queue
                chunk = await input_queue.get()

                # Check for end of file
                if chunk is None:
                    await output_queue.put(None)
                    break

                # Process the chunk
                if asyncio.iscoroutinefunction(processor):
                    processed_chunk = await processor(chunk)
                else:
                    processed_chunk = processor(chunk)

                # Put the processed chunk in the output queue
                await output_queue.put(processed_chunk)

                # Mark the task as done
                input_queue.task_done()

        except Exception as e:
            logger.error(f"Error processing chunk: {e}")
            # Signal error
            await output_queue.put(None)
            raise ProcessingError(f"Error processing chunk: {e}")

    async def _process_chunks_parallel(
        self,
        input_queue: asyncio.Queue,
        output_queue: asyncio.Queue,
        processor: ChunkProcessor | AsyncChunkProcessor,
    ) -> None:
        """
        Process chunks from the input queue in parallel.

        Args:
            input_queue: Queue to get chunks from
            output_queue: Queue to put processed chunks into
            processor: Function to process each chunk
        """
        try:
            while True:
                # Get a chunk from the queue
                chunk = await input_queue.get()

                # Check for end of file
                if chunk is None:
                    # Propagate None to output queue only once
                    if input_queue.qsize() == 0:
                        await output_queue.put(None)
                    break

                # Process the chunk
                if asyncio.iscoroutinefunction(processor):
                    processed_chunk = await processor(chunk)
                else:
                    processed_chunk = processor(chunk)

                # Put the processed chunk in the output queue
                await output_queue.put(processed_chunk)

                # Mark the task as done
                input_queue.task_done()

        except Exception as e:
            logger.error(f"Error processing chunk: {e}")
            # Signal error
            await output_queue.put(None)
            raise ProcessingError(f"Error processing chunk: {e}")

    async def _process_chunks_streaming(
        self,
        input_queue: asyncio.Queue,
        output_queue: asyncio.Queue,
        processor: ChunkProcessor | AsyncChunkProcessor,
    ) -> None:
        """
        Process chunks from the input queue in streaming mode.

        Args:
            input_queue: Queue to get chunks from
            output_queue: Queue to put processed chunks into
            processor: Function to process each chunk
        """
        # Similar to sequential but optimized for low latency
        await self._process_chunks_sequential(input_queue, output_queue, processor)

    async def _write_processed_chunks(
        self, file_path: str, queue: asyncio.Queue
    ) -> None:
        """
        Write processed chunks to a file.

        Args:
            file_path: Path to the output file
            queue: Queue to get processed chunks from
        """
        try:
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

            with open(file_path, "wb") as f:
                while True:
                    # Get a processed chunk from the queue
                    chunk = await queue.get()

                    # Check for end of file or error
                    if chunk is None:
                        break

                    # Write the chunk to the file
                    f.write(chunk)

                    # Mark the task as done
                    queue.task_done()

            logger.debug(f"Finished writing file: {file_path}")

        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            raise FileError(f"Error writing file: {e}", file_path=file_path)


# Register with the Registry using the decorator
@register_service("async_file_processor", lifecycle="singleton")
def register_async_file_processor() -> AsyncFileProcessor:
    """Factory function to register the AsyncFileProcessor instance."""
    return AsyncFileProcessorImpl()
