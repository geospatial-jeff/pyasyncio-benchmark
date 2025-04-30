import asyncio
import functools
import typing
import anyio

import imagecodecs
import aiohttp
from cog_layers.reader.cog import open_cog, read_row

from benchmark import scheduling
from benchmark.synchronization import semaphore
from benchmark.clients import HttpClientConfig, create_aiohttp_client


bucket_name = "cog-layers-glad"
key = "7/28/49/0231102/tile.tif"


async def send_range_aiohttp(
    bucket: str, key: str, start: int, end: int, client: typing.Any | None = None
):
    r = await client.get(
        f"https://{bucket}.s3.amazonaws.com/{key}",
        headers={"Range": f"bytes={start}-{end}"},
    )
    r.raise_for_status()
    return await r.read()


async def request_and_decode_row(cog, row):
    tiles = await read_row(row, 0, cog)

    futs = []
    for tile in tiles:
        futs.append(anyio.to_thread.run_sync(imagecodecs.jpeg_decode, tile))
    return await asyncio.gather(*futs)


@semaphore(2)
async def fut(session: aiohttp.ClientSession):
    """Request the first 16KB of a file, simulating COG header request.

    Semaphore allows this function to be called 500 times concurrently
    """
    cog = await open_cog(
        functools.partial(send_range_aiohttp, client=session),
        bucket=bucket_name,
        key=key,
    )

    # Request tiles, merging requests across rows.
    image_height = cog.ifds[0].tags["ImageHeight"].value[0]
    tile_height = cog.ifds[0].tags["TileHeight"].value[0]
    n_rows = image_height // tile_height
    return await asyncio.gather(
        *[request_and_decode_row(cog, row) for row in range(n_rows - 1)]
    )


async def run(config: HttpClientConfig, n_requests: int, timeout: int | None):
    async with create_aiohttp_client(config) as session:
        if timeout:
            results = await scheduling.gather_with_timeout(
                functools.partial(fut, session), n_requests, timeout
            )
        else:
            futures = (fut(session) for _ in range(n_requests))
            results = await scheduling.gather(futures)

    return results


def main(config: HttpClientConfig, n_requests: int, timeout: int | None, params: dict):
    return asyncio.run(run(config, n_requests, timeout))


if __name__ == "__main__":
    main(HttpClientConfig(), 1, None, {})
