"""
Requires running a webserver on local port 8080.
For example - `npx http-server`
"""

import asyncio
import time

import aiohttp

from benchmark import scheduling
from benchmark.synchronization import semaphore


@semaphore(500)
async def fut(session: aiohttp.ClientSession):
    start = time.time()
    async with session.get("http://host.docker.internal:8080") as resp:
        resp.raise_for_status()
        await resp.read()
        print(f"Finished request in {time.time() - start} seconds!")


async def run():
    async with aiohttp.ClientSession() as session:
        await scheduling.queue((fut(session) for _ in range(1000)), num_workers=100)


def main():
    asyncio.run(run())
