import asyncio
import random
from benchmark import scheduling



async def fut():
    sleep_for = random.uniform(0.05, 1.0)
    await asyncio.sleep(sleep_for)
    print(f"Slept for {sleep_for} seconds")


async def main():
    # Create a bunch of coroutines

    futs = [
        scheduling.queue((fut() for _ in range(500)), num_workers=100),
        scheduling.gather((fut() for _ in range(500))),
        scheduling.as_completed([fut() for _ in range(500)]),
    ]
    await asyncio.gather(*futs)
    
if __name__ == "__main__":
    asyncio.run(main())