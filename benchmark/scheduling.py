"""Various ways of scheduling coroutines on an event loop."""
import asyncio
from typing import Any, Iterable, Coroutine, Generator



async def gather(futs: Iterable[Coroutine]):
    """Run all coroutines, blocking until they all finish."""
    return await asyncio.gather(*futs)


async def as_completed(futs: Iterable[Coroutine]) -> Generator[Any, None, None]:
    """Run all coroutines, returning results as they finish."""
    for task in asyncio.as_completed(futs):
        await task


async def queue(futs: Iterable[Coroutine], num_workers: int = 3):
    """Puts coroutines onto a queue and processes them with multiple workers"""

    async def _worker(queue):
        while True:
            fut = await queue.get()
            await fut
            queue.task_done()

    queue = asyncio.Queue()

    # Create N workers listening to the queue
    workers = []
    for _ in range(num_workers):
        task = asyncio.create_task(_worker(queue))
        workers.append(task)

    # Start placing our coroutines onto the queue
    for fut in futs:
        queue.put_nowait(fut)

    # Wait until the queue is fully processed.
    await queue.join()

    # Cancel our worker tasks.
    for worker in workers:
        worker.cancel()
    
    # Wait until all worker tasks are cancelled.
    await asyncio.gather(*workers, return_exceptions=True)
