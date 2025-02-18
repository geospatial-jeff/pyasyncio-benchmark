import asyncio
from datetime import datetime

import aiohttp

from benchmark import scheduling
from benchmark.crud import WorkerState
from benchmark.synchronization import semaphore
from benchmark.clients import HttpClientConfig, create_aiohttp_client


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


async def run(config: HttpClientConfig, n_requests: int):
    async with create_aiohttp_client(config) as session:
        futures = (fut(session) for _ in range(n_requests))

        # Schedule them using a gather.
        start_time = datetime.utcnow()
        results = await scheduling.gather(futures)
        end_time = datetime.utcnow()

    n_failures = len([result for result in results if isinstance(result, Exception)])
    return WorkerState(start_time, end_time, n_requests, n_failures)


def main(config: HttpClientConfig, n_requests: int):
    # Run the script.
    return asyncio.run(run(config, n_requests))


if __name__ == "__main__":
    main(HttpClientConfig(), 1000)
