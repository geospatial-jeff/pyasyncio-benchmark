import asyncio
import functools

from botocore import UNSIGNED

from benchmark import scheduling
from benchmark.synchronization import semaphore
from benchmark.clients import HttpClientConfig, create_aioboto3_s3_client

bucket_name = "sentinel-cogs"
key = "sentinel-s2-l2a-cogs/50/C/MA/2021/1/S2A_50CMA_20210121_0_L2A/B08.tif"


@semaphore(500)
async def fut(s3_client, request_size: int):
    """Request the first 16KB of a file, simulating COG header request.

    Semaphore allows this function to be called 500 times concurrently
    """
    resp = await s3_client.get_object(
        Bucket=bucket_name, Key=key, Range=f"bytes=0-{request_size}"
    )
    return await resp["Body"].read()


async def run(
    config: HttpClientConfig, n_requests: int, request_size: int, timeout: int | None
):
    print("test run starting!")
    async with create_aioboto3_s3_client(
        config, "us-west-2", signature_version=UNSIGNED
    ) as s3_client:
        if timeout:
            print("running test with timeout - ", timeout)
            results = await scheduling.gather_with_timeout(
                functools.partial(fut, s3_client, request_size), n_requests, timeout
            )
        else:
            futures = (fut(s3_client, request_size) for _ in range(n_requests))
            results = await scheduling.gather(futures)
    return results


def main(config: HttpClientConfig, n_requests: int, timeout: int | None, params: dict):
    request_size = params.get("request_size", 16384)
    return asyncio.run(run(config, n_requests, request_size, timeout))


if __name__ == "__main__":
    print("inside dunder main")
    main(HttpClientConfig(), 1000, None, {})
