import asyncio
from datetime import datetime

from obstore.store import S3Store
import obstore as obs

from benchmark import scheduling
from benchmark.synchronization import semaphore
from benchmark.crud import WorkerState


key = "sentinel-s2-l2a-cogs/50/C/MA/2021/1/S2A_50CMA_20210121_0_L2A/B08.tif"


@semaphore(500)
async def fut(store: obs.store.S3Store):
    """Request the first 16KB of a file, simulating COG header request.

    Semaphore allows this function to be called 500 times concurrently
    """
    r = await obs.get_range_async(store, key, start=0, end=16384)
    r.to_bytes()


async def run():
    # Create the store.
    store = S3Store("sentinel-cogs", region="us-west-2", skip_signature=True)

    n_requests = 25000
    futures = (fut(store) for _ in range(n_requests))

    start_time = datetime.utcnow()
    results = await scheduling.gather(futures)
    end_time = datetime.utcnow()

    n_failures = len([result for result in results if isinstance(result, Exception)])
    breakpoint()
    return WorkerState(start_time, end_time, n_requests, n_failures)


def main():
    # Run the script.
    return asyncio.run(run())


if __name__ == "__main__":
    main()
