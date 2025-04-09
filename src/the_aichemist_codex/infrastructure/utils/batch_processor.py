"""Batch processing utilities for The AIchemist Codex."""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


class BatchProcessor:
    """Utility for processing items in batches asynchronously."""

    def __init__(self) -> None:
        """Initialize the batch processor."""
        pass

    async def process_batch(
        self,
        items: list[T],
        operation: Callable[[T], Coroutine[Any, Any, R]],
        batch_size: int = 10,
        timeout: float = 30.0,
    ) -> list[R | None]:
        """
        Process a list of items in batches asynchronously.

        Args:
            items: List of items to process
            operation: Async function to apply to each item
            batch_size: Number of items to process in each batch
            timeout: Timeout in seconds for each batch

        Returns:
            List of results from processing each item
        """
        if not items:
            return []

        results = []

        # Process in batches
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]

            # Create tasks for batch
            tasks = [
                asyncio.create_task(self._safe_operation(operation, item))
                for item in batch
            ]

            # Wait for all tasks in the batch with timeout
            try:
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
            except TimeoutError:
                logger.warning(f"Timeout processing batch starting at index {i}")
                # Attempt to get results from completed tasks
                for task in tasks:
                    if task.done() and not task.cancelled():
                        try:
                            results.append(task.result())
                        except Exception as e:
                            logger.error(f"Error getting result from task: {e}")

            # Small pause between batches to prevent resource exhaustion
            await asyncio.sleep(0.1)

        return results

    async def _safe_operation(
        self, operation: Callable[[T], Coroutine[Any, Any, R]], item: T
    ) -> R | None:
        """
        Safely execute an operation on an item with error handling.

        Args:
            operation: Async function to apply to the item
            item: Item to process

        Returns:
            Result of the operation or None if an error occurred
        """
        try:
            return await operation(item)
        except Exception as e:
            logger.error(f"Error processing item: {e}")
            return None
