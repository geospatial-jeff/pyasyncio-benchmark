import asyncio
from datetime import datetime

import s3fs

from benchmark import scheduling
from benchmark.crud import WorkerState
from benchmark.synchronization import semaphore


key = "sentinel-s2-l2a-cogs/50/C/MA/2021/1/S2A_50CMA_20210121_0_L2A/B08.tif"


@semaphore(500)
async def fut(filesystem: s3fs.S3FileSystem):
    """Request the first 16KB of a file, simulating COG header request.

    Semaphore allows this function to be called 500 times concurrently
    """
    await filesystem._cat_file(f"sentinel-cogs/{key}", start=0, end=16384)


async def run():
    n_requests = 10000
    filesystem = s3fs.S3FileSystem(
        anon=True, asynchronous=True, loop=asyncio.get_running_loop()
    )

    futures = (fut(filesystem) for _ in range(n_requests))

    # Schedule them using a gather.
    start_time = datetime.utcnow()
    await scheduling.gather(futures)
    end_time = datetime.utcnow()

    return WorkerState(start_time, end_time, n_requests)


def main():
    # Run the script.
    return asyncio.run(run())


if __name__ == "__main__":
    main()
