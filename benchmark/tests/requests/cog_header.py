import anyio
import asyncio
import functools

import requests
import requests.adapters

from benchmark import scheduling
from benchmark.synchronization import semaphore
from benchmark.clients import HttpClientConfig, create_requests_session


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


async def run(config: HttpClientConfig, n_requests: int, timeout: int | None):
    session = create_requests_session(config)
    if timeout:
        results = await scheduling.gather_with_timeout(
            functools.partial(fut, session), n_requests, timeout
        )
    else:
        futures = (fut(session) for _ in range(n_requests))
        results = await scheduling.gather(futures)
    return results


def main(config: HttpClientConfig, n_requests: int, timeout: int | None):
    return asyncio.run(run(config, n_requests, timeout))


if __name__ == "__main__":
    main(HttpClientConfig(), 1000, None)
