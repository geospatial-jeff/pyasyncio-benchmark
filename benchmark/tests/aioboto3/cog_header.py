import asyncio
import functools
import typing

from botocore import UNSIGNED
from cog_layers.reader.cog import open_cog

from benchmark import scheduling
from benchmark.synchronization import semaphore
from benchmark.clients import HttpClientConfig, create_aioboto3_s3_client

bucket_name = "sentinel-cogs"
key = "sentinel-s2-l2a-cogs/50/C/MA/2021/1/S2A_50CMA_20210121_0_L2A/B08.tif"


@semaphore(500)
async def send_range_aioboto3(
    bucket: str, key: str, start: int, end: int, client: typing.Any | None
):
    resp = await client.get_object(Bucket=bucket, Key=key, Range=f"bytes={start}-{end}")
    return await resp["Body"].read()


async def fut(s3_client):
    """Request the first 16KB of a file, simulating COG header request.

    Semaphore allows this function to be called 500 times concurrently
    """
    await open_cog(
        functools.partial(send_range_aioboto3, client=s3_client),
        bucket=bucket_name,
        key=key,
        header_size_bytes=16384,
    )


async def run(config: HttpClientConfig, n_requests: int, timeout: int | None):
    async with create_aioboto3_s3_client(
        config, "us-west-2", signature_version=UNSIGNED
    ) as s3_client:
        if timeout:
            results = await scheduling.gather_with_timeout(
                functools.partial(fut, s3_client), n_requests, timeout
            )
        else:
            futures = (fut(s3_client) for _ in range(n_requests))
            results = await scheduling.gather(futures)
    return results


def main(config: HttpClientConfig, n_requests: int, timeout: int | None, params: dict):
    return asyncio.run(run(config, n_requests, timeout))


if __name__ == "__main__":
    main(HttpClientConfig(), 1000, None, {})
