import anyio
import asyncio
import functools

import rasterio

from benchmark import scheduling
from benchmark.clients import HttpClientConfig
from benchmark.synchronization import semaphore


key = "sentinel-s2-l2a-cogs/50/C/MA/2021/1/S2A_50CMA_20210121_0_L2A/B08.tif"


def task():
    """Request the first 16KB of a file, simulating COG header request.

    Semaphore allows this function to be called 500 times concurrently
    """
    with rasterio.open(f"s3://sentinel-cogs/{key}"):
        pass


@semaphore(500)
async def fut():
    func = functools.partial(task)
    return await anyio.to_thread.run_sync(func)


async def run(config: HttpClientConfig, n_requests: int, timeout: int | None):
    with rasterio.Env(
        GDAL_INGESTED_BYTES_AT_OPEN=16384,
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        AWS_NO_SIGN_REQUEST="YES",
        AWS_REGION="us-west-2",
        CPL_VSIL_CURL_NON_CACHED=f"/vsis3/sentinel-cogs/{key}",
    ):
        if timeout:
            results = await scheduling.gather_with_timeout(fut, n_requests, timeout)
        else:
            futures = (fut() for _ in range(n_requests))
            results = await scheduling.gather(futures)
    return results


def main(config: HttpClientConfig, n_requests: int, timeout: int | None):
    return asyncio.run(run(config, n_requests, timeout))


if __name__ == "__main__":
    main(HttpClientConfig(), 100, None)
