"""Various ways of scheduling coroutines on an event loop."""

import asyncio
from datetime import datetime
from typing import Iterable, Coroutine

from benchmark.crud import WorkerState


async def gather(futs: Iterable[Coroutine]) -> WorkerState:
    """Run all coroutines, blocking until they all finish."""
    # return await asyncio.gather(*futs, return_exceptions=True)
    start_time = datetime.utcnow()
    results = await asyncio.gather(*futs, return_exceptions=True)
    end_time = datetime.utcnow()
    n_failures = len([result for result in results if isinstance(result, Exception)])
    return WorkerState(start_time, end_time, len(results), n_failures)


async def queue(futs: Iterable[Coroutine], num_workers: int = 3):
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
