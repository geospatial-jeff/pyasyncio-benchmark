import anyio
import asyncio
from datetime import datetime
import functools

import requests
import requests.adapters

from benchmark import scheduling
from benchmark.crud import WorkerState
from benchmark.synchronization import semaphore


key = "sentinel-s2-l2a-cogs/50/C/MA/2021/1/S2A_50CMA_20210121_0_L2A/B08.tif"


async def run_in_threadpool(session: requests.Session):
    func = functools.partial(task, session)
    return await anyio.to_thread.run_sync(func)


def task(session: requests.Session):
    """Request the first 16KB of a file, simulating COG header request.

    Semaphore allows this function to be called 500 times concurrently
    """
    r = session.get(
        f"https://sentinel-cogs.s3.amazonaws.com/{key}",
        headers={"Range": "bytes=0-16384"},
    )
    r.raise_for_status()
    r.content


@semaphore(500)
async def fut(session: requests.Session):
    await run_in_threadpool(session)


async def run():
    n_requests = 10000

    # Crete connection pool
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter()
    session.mount("https://", adapter)

    start_time = datetime.utcnow()
    futures = (fut(session) for _ in range(n_requests))
    results = await scheduling.gather(futures)
    end_time = datetime.utcnow()

    n_failures = len([result for result in results if isinstance(result, Exception)])
    return WorkerState(start_time, end_time, n_requests, n_failures)


def main():
    # Run the script.
    return asyncio.run(run())


if __name__ == "__main__":
    main()
