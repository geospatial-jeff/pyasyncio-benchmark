import asyncio
import sys

from obstore.store import S3Store
import obstore as obs

from benchmark import scheduling
from benchmark.synchronization import semaphore


key = "sentinel-s2-l2a-cogs/50/C/MA/2021/1/S2A_50CMA_20210121_0_L2A/B08.tif"

@semaphore(500)
async def fut(store: obs.store.S3Store):
    """Request the first 16KB of a file, simulating COG header request.
    
    Semaphore allows this function to be called 500 times concurrently
    """
    await obs.get_range_async(store, key, offset=0, length=16384)


async def main():
    # Create the store.
    store = S3Store.from_env("sentinel-cogs", config={"AWS_REGION": "us-west-2", "SKIP_SIGNATURE": "true"})

    # Send 10,000 header requests
    futures = (fut(store) for _ in range(10000))

    # Schedule them using a gather.
    # Memory usage is O(10000).
    # Requests are executed 500 at a time (because of the semaphore).
    await scheduling.gather(futures)


if __name__ == "__main__":
    # Run the script.
    asyncio.run(main())

    # Exit signal kills the container when it's done sending requests.
    sys.exit(1)