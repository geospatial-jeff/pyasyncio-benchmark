import asyncio
import functools

import obstore as obs

from benchmark import scheduling
from benchmark.synchronization import semaphore
from benchmark.clients import HttpClientConfig, create_obstore_store


key = "sentinel-s2-l2a-cogs/50/C/MA/2021/1/S2A_50CMA_20210121_0_L2A/B08.tif"


@semaphore(500)
async def fut(store: obs.store.S3Store):
    """Request the first 16KB of a file, simulating COG header request.

    Semaphore allows this function to be called 500 times concurrently
    """
    r = await obs.get_range_async(store, key, start=0, end=16384)
    r.to_bytes()


async def run(config: HttpClientConfig, n_requests: int, timeout: int | None):
    n_requests = n_requests * 3
    store = create_obstore_store(config, "sentinel-cogs", region_name="us-west-2")
    if timeout:
        results = await scheduling.gather_with_timeout(
            functools.partial(fut, store), n_requests, timeout
        )
    else:
        futures = (fut(store) for _ in range(n_requests))
        results = await scheduling.gather(futures)
    return results


def main(config: HttpClientConfig, n_requests: int, timeout: int | None):
    return asyncio.run(run(config, n_requests, timeout))


if __name__ == "__main__":
    main(HttpClientConfig(), 1000, None)
