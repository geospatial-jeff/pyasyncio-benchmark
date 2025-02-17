import anyio
import asyncio
from datetime import datetime
import functools

import rasterio

from benchmark import scheduling
from benchmark.crud import WorkerState
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


async def run():
    n_requests = 1000

    with rasterio.Env(
        GDAL_INGESTED_BYTES_AT_OPEN=16384,
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        AWS_NO_SIGN_REQUEST="YES",
        AWS_REGION="us-west-2",
        CPL_VSIL_CURL_NON_CACHED=f"/vsis3/sentinel-cogs/{key}",
    ):
        start_time = datetime.utcnow()
        futures = (fut() for _ in range(n_requests))
        results = await scheduling.gather(futures)
        end_time = datetime.utcnow()

    n_failures = len([result for result in results if isinstance(result, Exception)])
    return WorkerState(start_time, end_time, n_requests, n_failures)


def main():
    # Run the script.
    return asyncio.run(run())


if __name__ == "__main__":
    main()
