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
    func = functools.partial(fut, session)
    return await anyio.to_thread.run_sync(func)


@semaphore(500)
async def fut(session: requests.Session, request_size: int):
    r = session.get(
        f"https://sentinel-cogs.s3.amazonaws.com/{key}",
        headers={"Range": f"bytes=0-{request_size}"},
    )
    r.raise_for_status()
    r.content


async def run(
    config: HttpClientConfig, n_requests: int, request_size: int, timeout: int | None
):
    session = create_requests_session(config)
    if timeout:
        results = await scheduling.gather_with_timeout(
            functools.partial(fut, session, request_size), n_requests, timeout
        )
    else:
        futures = (fut(session, request_size) for _ in range(n_requests))
        results = await scheduling.gather(futures)
    return results


def main(config: HttpClientConfig, n_requests: int, timeout: int | None, params: dict):
    request_size = params.get("request_size", 16384)
    return asyncio.run(run(config, n_requests, request_size, timeout))


if __name__ == "__main__":
    main(HttpClientConfig(), 1000, None, {})
