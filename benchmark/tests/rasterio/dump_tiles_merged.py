import anyio
import asyncio
import functools
import threading
import concurrent.futures

import rasterio
from rasterio.windows import Window

from benchmark import scheduling
from benchmark.clients import HttpClientConfig
from benchmark.synchronization import semaphore


bucket_name = "cog-layers-glad"
key = "7/28/49/0231102/tile.tif"


def task():
    """Request the first 16KB of a file, simulating COG header request.

    Semaphore allows this function to be called 500 times concurrently
    """
    with rasterio.open(f"s3://{bucket_name}/{key}") as src:
        windows = [window for _, window in src.block_windows()]
        unique_cols = set([window.col_off for window in windows])

        read_lock = threading.Lock()

        def process(window):
            with read_lock:
                src.read(window=window)

        windows = [
            Window(
                col_off=col,
                row_off=0,
                width=src.width,
                height=src.profile["blockysize"],
            )
            for col in unique_cols
        ]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(process, windows)


@semaphore(2)
async def fut():
    func = functools.partial(task)
    return await anyio.to_thread.run_sync(func)


async def run(config: HttpClientConfig, n_requests: int, timeout: int | None):
    with rasterio.Env(
        GDAL_INGESTED_BYTES_AT_OPEN=16384,
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        AWS_NO_SIGN_REQUEST="YES",
        AWS_REGION="us-west-2",
        CPL_VSIL_CURL_NON_CACHED=f"/vsis3/{bucket_name}/{key}",
        GDAL_CACHEMAX=0,
        GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES",
    ):
        if timeout:
            results = await scheduling.gather_with_timeout(fut, n_requests, timeout)
        else:
            futures = (fut() for _ in range(n_requests))
            results = await scheduling.gather(futures)
    return results


def main(config: HttpClientConfig, n_requests: int, timeout: int | None, params: dict):
    return asyncio.run(run(config, n_requests, timeout))


if __name__ == "__main__":
    main(HttpClientConfig(), 1, None, {})
