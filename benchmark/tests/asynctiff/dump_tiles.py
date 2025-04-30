import asyncio
import functools
import math

from async_tiff import TIFF
import async_tiff.store

from benchmark import scheduling
from benchmark.synchronization import semaphore
from benchmark.clients import HttpClientConfig, create_async_tiff_s3_store


bucket_name = "cog-layers-glad"
key = "7/28/49/0231102/tile.tif"


@semaphore(500)
async def fetch_tile(tiff: TIFF, x: int, y: int, z: int):
    b = await tiff.fetch_tile(x, y, z)
    return b


async def fut(store: async_tiff.store.S3Store):
    """Request the first 16KB of a file, simulating COG header request.

    Semaphore allows this function to be called 500 times concurrently
    """
    tiff = await TIFF.open(key, store=store, prefetch=16384)
    ifd = tiff.ifds[0]
    n_tiles_width = math.ceil(ifd.image_width / ifd.tile_width)
    n_tiles_height = math.ceil(ifd.image_height / ifd.tile_height)

    tile_requests = []
    for x in range(n_tiles_width):
        for y in range(n_tiles_height):
            tile_requests.append(fetch_tile(tiff, x, y, 0))

    await asyncio.gather(*tile_requests)


async def run(config: HttpClientConfig, n_requests: int, timeout: int | None):
    store = create_async_tiff_s3_store(config, bucket_name, region_name="us-west-2")
    if timeout:
        results = await scheduling.gather_with_timeout(
            functools.partial(fut, store), n_requests, timeout
        )
    else:
        futures = (fut(store) for _ in range(n_requests))
        results = await scheduling.gather(futures)
    return results


def main(config: HttpClientConfig, n_requests: int, timeout: int | None, params: dict):
    return asyncio.run(run(config, n_requests, timeout))


if __name__ == "__main__":
    main(HttpClientConfig(), 1, None, {})
