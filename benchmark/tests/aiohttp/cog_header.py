import asyncio
from datetime import datetime

import aiohttp

from benchmark import scheduling
from benchmark.crud import WorkerState
from benchmark.synchronization import semaphore


key = "sentinel-s2-l2a-cogs/50/C/MA/2021/1/S2A_50CMA_20210121_0_L2A/B08.tif"


@semaphore(500)
async def fut(session: aiohttp.ClientSession):
    """Request the first 16KB of a file, simulating COG header request.

    Semaphore allows this function to be called 500 times concurrently
    """
    r = await session.get(
        f"https://sentinel-cogs.s3.amazonaws.com/{key}",
        headers={"Range": "bytes=0-16384"},
    )
    r.raise_for_status()
    await r.read()


async def run():
    n_requests = 10000
    async with aiohttp.ClientSession() as session:
        futures = (fut(session) for _ in range(n_requests))

        # Schedule them using a gather.
        start_time = datetime.utcnow()
        await scheduling.gather(futures)
        end_time = datetime.utcnow()

    return WorkerState(start_time, end_time, n_requests)


def main():
    # Run the script.
    return asyncio.run(run())


if __name__ == "__main__":
    main()
