"""Provides enhanced concurrency tools for efficient parallel processing."""

import asyncio
import functools
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


class TaskPriority(Enum):
    """Task priority levels for scheduling."""

    LOW = 0
    MEDIUM = 1
    HIGH = 2


class AsyncThreadPoolExecutor:
    """Thread pool executor with async interface and priority scheduling."""

    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize executor with optional worker limit.

        Args:
            max_workers: Maximum number of worker threads (defaults to CPU count * 5)
        """
        if max_workers is None:
            max_workers = min(32, os.cpu_count() * 5)

        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = asyncio.Semaphore(max_workers)
        self._tasks: Dict[asyncio.Task, TaskPriority] = {}

    async def submit(
        self,
        func: Callable[..., T],
        *args: Any,
        priority: TaskPriority = TaskPriority.MEDIUM,
        **kwargs: Any,
    ) -> T:
        """
        Submit a function for execution with priority scheduling.

        Args:
            func: Function to execute
            *args: Arguments for the function
            priority: Task priority level
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function execution
        """
        async with self.semaphore:
            loop = asyncio.get_event_loop()

            # Create the task
            task = loop.create_task(
                loop.run_in_executor(
                    self.executor, functools.partial(func, *args, **kwargs)
                )
            )

            # Store task with priority
            self._tasks[task] = priority

            try:
                return await task
            finally:
                if task in self._tasks:
                    del self._tasks[task]

    async def submit_batch(
        self,
        func: Callable[[Any], T],
        items: List[Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        max_concurrent: Optional[int] = None,
    ) -> List[T]:
        """
        Submit a batch of items for concurrent processing.

        Args:
            func: Function to execute on each item
            items: List of items to process
            priority: Task priority level
            max_concurrent: Maximum number of concurrent tasks

        Returns:
            List of results in the order of input items
        """
        if max_concurrent is None:
            # Use a reasonable number based on CPU cores
            max_concurrent = os.cpu_count() or 4

        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_item(item):
            async with semaphore:
                return await self.submit(func, item, priority=priority)

        tasks = [process_item(item) for item in items]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def shutdown(self, wait: bool = True):
        """
        Shutdown the executor.

        Args:
            wait: Whether to wait for pending futures to complete
        """
        self.executor.shutdown(wait=wait)


class RateLimiter:
    """Rate limiter for controlling operation frequency."""

    def __init__(self, max_rate: float, time_period: float = 1.0):
        """
        Initialize rate limiter.

        Args:
            max_rate: Maximum number of operations per time period
            time_period: Time period in seconds
        """
        self.max_rate = max_rate
        self.time_period = time_period
        self.tokens = max_rate
        self.last_update = asyncio.get_event_loop().time()
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Acquire a token, waiting if necessary."""
        async with self.lock:
            while self.tokens <= 0:
                now = asyncio.get_event_loop().time()
                time_passed = now - self.last_update
                self.tokens = min(
                    self.max_rate,
                    self.tokens + time_passed * (self.max_rate / self.time_period),
                )
                self.last_update = now
                if self.tokens <= 0:
                    await asyncio.sleep(self.time_period / self.max_rate)
            self.tokens -= 1


class TaskQueue:
    """Priority task queue with rate limiting."""

    def __init__(
        self,
        max_concurrent: int = 10,
        max_rate: Optional[float] = None,
        time_period: float = 1.0,
    ):
        """
        Initialize task queue.

        Args:
            max_concurrent: Maximum number of concurrent tasks
            max_rate: Maximum tasks per time period (None for no limit)
            time_period: Time period in seconds for rate limiting
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.rate_limiter = (
            RateLimiter(max_rate, time_period) if max_rate is not None else None
        )
        self.tasks: Dict[TaskPriority, List[asyncio.Task]] = {
            priority: [] for priority in TaskPriority
        }

    async def add_task(
        self,
        coro: Callable[..., T],
        *args: Any,
        priority: TaskPriority = TaskPriority.MEDIUM,
        **kwargs: Any,
    ) -> T:
        """
        Add a task to the queue.

        Args:
            coro: Coroutine to execute
            *args: Arguments for the coroutine
            priority: Task priority level
            **kwargs: Keyword arguments for the coroutine

        Returns:
            Result of the coroutine execution
        """
        async with self.semaphore:
            if self.rate_limiter is not None:
                await self.rate_limiter.acquire()

            task = asyncio.create_task(coro(*args, **kwargs))
            self.tasks[priority].append(task)

            try:
                return await task
            finally:
                self.tasks[priority].remove(task)

    async def add_batch(
        self,
        coro: Callable[[Any], T],
        items: List[Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        **kwargs: Any,
    ) -> List[T]:
        """
        Add a batch of items for processing.

        Args:
            coro: Coroutine to execute for each item
            items: List of items to process
            priority: Task priority level
            **kwargs: Additional keyword arguments for the coroutine

        Returns:
            List of results in the order of input items
        """
        tasks = [
            self.add_task(coro, item, priority=priority, **kwargs) for item in items
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)


# Create singleton instances for application-wide use
thread_pool = AsyncThreadPoolExecutor()
task_queue = TaskQueue()
