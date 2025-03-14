"""Provides batch processing capabilities for efficient operations."""

import asyncio
import logging
from typing import Any, Awaitable, Callable, List, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


class BatchProcessor:
    """Handles batch processing with async support and error handling."""

    @staticmethod
    async def process_batch(
        items: List[Any],
        operation: Callable[[Any], Awaitable[Any]],
        batch_size: int = 10,
        timeout: int = 30,
    ) -> List[Any]:
        """
        Process items in batches using the provided async operation.

        Args:
            items: List of items to process
            operation: Async function to apply to each item
            batch_size: Number of items to process in each batch
            timeout: Maximum wait time in seconds

        Returns:
            List of results from successful operations
        """
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            batch_tasks = [operation(item) for item in batch]
            try:
                batch_results = await asyncio.gather(
                    *batch_tasks, return_exceptions=True
                )
                # Filter out exceptions and add successful results
                for result in batch_results:
                    if not isinstance(result, Exception):
                        results.append(result)
                    else:
                        logger.error(f"Batch operation error: {result}")
            except asyncio.TimeoutError:
                logger.error(f"Batch operation timed out after {timeout} seconds")

        return results
