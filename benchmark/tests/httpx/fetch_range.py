import asyncio
import functools

import httpx

from benchmark import scheduling
from benchmark.synchronization import semaphore
from benchmark.clients import HttpClientConfig, create_httpx_client

bucket_name = "sentinel-cogs"
key = "sentinel-s2-l2a-cogs/50/C/MA/2021/1/S2A_50CMA_20210121_0_L2A/B08.tif"


@semaphore(500)
async def fut(client: httpx.AsyncClient, request_size: int):
    """Request the first 16KB of a file, simulating COG header request.

    Semaphore allows this function to be called 500 times concurrently
    """
    r = await client.get(
        f"https://{bucket_name}.s3.amazonaws.com/{key}",
        headers={"Range": f"bytes=0-{request_size}"},
    )
    r.raise_for_status()
    return r.read()


async def run(
    config: HttpClientConfig, n_requests: int, request_size: int, timeout: int | None
):
    async with create_httpx_client(config) as client:
        if timeout:
            results = await scheduling.gather_with_timeout(
                functools.partial(fut, client, request_size), n_requests, timeout
            )
        else:
            futures = (fut(client, request_size) for _ in range(n_requests))
            results = await scheduling.gather(futures)
    return results


def main(config: HttpClientConfig, n_requests: int, timeout: int | None, params: dict):
    request_size = params.get("request_size", 16384)
    return asyncio.run(run(config, n_requests, request_size, timeout))


if __name__ == "__main__":
    main(HttpClientConfig(), 1000, None, {})
