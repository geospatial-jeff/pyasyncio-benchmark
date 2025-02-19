import asyncio

import httpx

from benchmark import scheduling
from benchmark.synchronization import semaphore
from benchmark.clients import HttpClientConfig, create_httpx_client


key = "sentinel-s2-l2a-cogs/50/C/MA/2021/1/S2A_50CMA_20210121_0_L2A/B08.tif"
concurrency = 100


@semaphore(concurrency)
async def fut(client: httpx.AsyncClient):
    """Request the first 16KB of a file, simulating COG header request.

    Semaphore allows this function to be called 500 times concurrently
    """
    r = await client.get(f"/{key}", headers={"Range": "bytes=0-16384"})
    r.raise_for_status()
    r.read()


async def run(config: HttpClientConfig, n_requests: int):
    async with create_httpx_client(
        config, base_url="https://sentinel-cogs.s3.amazonaws.com"
    ) as client:
        futures = (fut(client) for _ in range(n_requests))
        results = await scheduling.gather(futures)
    return results


def main(config: HttpClientConfig, n_requests: int):
    return asyncio.run(run(config, n_requests))


if __name__ == "__main__":
    main(HttpClientConfig(), 1000)
