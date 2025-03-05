import asyncio
import functools

from cog_layers.reader.cog import open_cog
from cog_layers.reader.io import send_range_obstore
from cog_layers.reader.tiler import request_metatile, get_seed_tile
import obstore as obs

from benchmark import scheduling
from benchmark.synchronization import semaphore
from benchmark.clients import HttpClientConfig, create_obstore_store


bucket_name = "cog-layers-glad"
key = "7/28/49/0231102/tile.tif"


@semaphore(5)
async def fut(store: obs.store.S3Store):
    """Request the first 16KB of a file, simulating COG header request.

    Semaphore allows this function to be called 500 times concurrently
    """
    cog = await open_cog(
        functools.partial(send_range_obstore, client=store), bucket=bucket_name, key=key
    )

    # Request every tile in the pyramid from Z7 -> Z12
    seed_tile = get_seed_tile(cog)

    futs = []
    for idx, _ in enumerate(range(7, 12 + 1)):
        futs.append(request_metatile(cog, seed_tile, size=2**idx))

    await asyncio.gather(*futs)


async def run(config: HttpClientConfig, n_requests: int, timeout: int | None):
    store = create_obstore_store(config, bucket_name, region_name="us-west-2")
    if timeout:
        results = await scheduling.gather_with_timeout(
            functools.partial(fut, store), n_requests, timeout
        )
    else:
        futures = (fut(store) for _ in range(n_requests))
        results = await scheduling.gather(futures)
    return results


def main(config: HttpClientConfig, n_requests: int, timeout: int | None):
    return asyncio.run(run(config, n_requests, timeout))


if __name__ == "__main__":
    main(HttpClientConfig(), 10, None)
