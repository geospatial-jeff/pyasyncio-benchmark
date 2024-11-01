import asyncio

import aioboto3
from botocore import UNSIGNED
from botocore.config import Config

from benchmark import scheduling
from benchmark.synchronization import semaphore


key = "sentinel-s2-l2a-cogs/50/C/MA/2021/1/S2A_50CMA_20210121_0_L2A/B08.tif"


@semaphore(500)
async def fut(s3_client):
    """Request the first 16KB of a file, simulating COG header request.

    Semaphore allows this function to be called 500 times concurrently
    """
    resp = await s3_client.get_object(
        Bucket="sentinel-cogs", Key=key, Range="bytes=0-16384"
    )
    await resp["Body"].read()


async def run():
    session = aioboto3.Session()
    async with session.client(
        "s3", config=Config(signature_version=UNSIGNED)
    ) as s3_client:
        # Send 10,000 header requests
        futures = (fut(s3_client) for _ in range(10000))

        # Schedule them using a gather.
        # Memory usage is O(10000).
        # Requests are executed 500 at a time (because of the semaphore).
        await scheduling.gather(futures)


def main():
    # Run the script.
    asyncio.run(run())