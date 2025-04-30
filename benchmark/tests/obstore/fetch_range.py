import asyncio
import functools

import obstore as obs

from benchmark import scheduling
from benchmark.synchronization import semaphore
from benchmark.clients import HttpClientConfig, create_obstore_store


key = "sentinel-s2-l2a-cogs/50/C/MA/2021/1/S2A_50CMA_20210121_0_L2A/B08.tif"


@semaphore(100)
async def fut(store: obs.store.S3Store, request_size: int):
    """Request the first 16KB of a file, simulating COG header request.

    Semaphore allows this function to be called 500 times concurrently
    """
    r = await obs.get_range_async(store, key, start=0, end=request_size)
    r.to_bytes()


async def run(
    config: HttpClientConfig, n_requests: int, request_size: int, timeout: int | None
):
    store = create_obstore_store(config, "sentinel-cogs", region_name="us-west-2")
    if timeout:
        results = await scheduling.gather_with_timeout(
            functools.partial(fut, store, request_size), n_requests, timeout
        )
    else:
        futures = (fut(store, request_size) for _ in range(n_requests))
        results = await scheduling.gather(futures)
    return results


def main(config: HttpClientConfig, n_requests: int, timeout: int | None, params: dict):
    request_size = params.get("request_size", 16384)
    return asyncio.run(run(config, n_requests, request_size, timeout))


if __name__ == "__main__":
    main(HttpClientConfig(), 1000, None, {})
