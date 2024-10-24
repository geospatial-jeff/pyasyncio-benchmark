import asyncio
from benchmark import scheduling
from benchmark.synchronization import semaphore


@semaphore(10)
async def fut():
    sleep_for = 1
    await asyncio.sleep(sleep_for)
    print(f"Slept for {sleep_for} seconds")


async def main():
    # Create a bunch of coroutines

    futs = [
        scheduling.queue((fut() for _ in range(500)), num_workers=100),
        scheduling.gather((fut() for _ in range(100))),
        scheduling.as_completed([fut() for _ in range(500)]),
    ]
    await asyncio.gather(*futs)
    
if __name__ == "__main__":
    asyncio.run(main())