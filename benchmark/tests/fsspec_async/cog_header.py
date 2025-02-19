import asyncio

import s3fs

from benchmark import scheduling
from benchmark.synchronization import semaphore
from benchmark.clients import HttpClientConfig, create_fsspec_s3

key = "sentinel-s2-l2a-cogs/50/C/MA/2021/1/S2A_50CMA_20210121_0_L2A/B08.tif"


@semaphore(500)
async def fut(filesystem: s3fs.S3FileSystem):
    """Request the first 16KB of a file, simulating COG header request.

    Semaphore allows this function to be called 500 times concurrently
    """
    await filesystem._cat_file(f"sentinel-cogs/{key}", start=0, end=16384)


async def run(config: HttpClientConfig, n_requests: int):
    filesystem = create_fsspec_s3(config, "us-west-2")
    futures = (fut(filesystem) for _ in range(n_requests))
    results = await scheduling.gather(futures)
    return results


def main(config: HttpClientConfig, n_requests: int):
    return asyncio.run(run(config, n_requests))


if __name__ == "__main__":
    main(HttpClientConfig(), 1000)
