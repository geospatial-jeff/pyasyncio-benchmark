"""Various ways of scheduling coroutines on an event loop."""

import asyncio
from datetime import datetime
from typing import Iterable, Coroutine

from benchmark.crud import WorkerState


async def gather_with_timeout(func, n_requests, timeout) -> WorkerState:
    """Run the function `n_requests` times, blocking until either they all complete
    or a certain amount of time has passed.  Returns "partial results" if not all
    coroutines finish before the timeout.

    This function is the most efficient when `n_requests` is large enough to cover
    the full timeout.
    """
    results = []
    errors = []

    async def _wrapper():
        try:
            results.append(await func())
        except Exception as exc:
            errors.append(exc)

    start_time = datetime.utcnow()
    while True:
        start_time_chunk = datetime.utcnow()
        futures = asyncio.gather(*[_wrapper() for _ in range(n_requests)])
        end_time_gather = datetime.utcnow()
        try:
            await asyncio.wait_for(futures, timeout)
            end_time_chunk = datetime.utcnow()
            timeout = max(
                timeout
                - (end_time_chunk - start_time_chunk).total_seconds()
                + (end_time_gather - start_time_chunk).total_seconds(),
                0,
            )
        except TimeoutError:
            end_time = datetime.utcnow()
            return WorkerState(
                start_time, end_time, len(results) + len(errors), len(errors)
            )


async def gather(futs: Iterable[Coroutine]) -> WorkerState:
    """Run all coroutines, blocking until they all finish."""
    # return await asyncio.gather(*futs, return_exceptions=True)
    start_time = datetime.utcnow()
    results = await asyncio.gather(*futs, return_exceptions=True)
    end_time = datetime.utcnow()
    n_failures = len([result for result in results if isinstance(result, Exception)])
    return WorkerState(start_time, end_time, len(results), n_failures)


async def queue(futs: Iterable[Coroutine], num_workers: int = 3) -> WorkerState:
    """Puts coroutines onto a queue and processes them with multiple workers"""
    failure_count = 0

    async def _worker(queue):
        global failure_count
        while True:
            fut = await queue.get()
            try:
                await fut
            except Exception:
                failure_count += 1
            queue.task_done()

    queue = asyncio.Queue()

    # Create N workers listening to the queue
    workers = []
    for _ in range(num_workers):
        task = asyncio.create_task(_worker(queue))
        workers.append(task)

    # Start placing our coroutines onto the queue
    start_time = datetime.utcnow()
    n_tasks = 0
    for fut in futs:
        queue.put_nowait(fut)
        n_tasks += 1

    # Wait until the queue is fully processed.
    await queue.join()
    end_time = datetime.utcnow()

    # Cancel our worker tasks.
    for worker in workers:
        worker.cancel()

    # Wait until all worker tasks are cancelled.
    await asyncio.gather(*workers, return_exceptions=True)

    return WorkerState(start_time, end_time, n_tasks, failure_count)
