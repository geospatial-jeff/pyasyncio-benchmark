import asyncio
from dataclasses import dataclass
import aioboto3
import aiohttp
import async_tiff.store
import httpx
import requests.adapters
import botocore.config
import s3fs
import obstore as obs


DEFAULT_POOL_SIZE_PER_HOST: int = 100
DEFAULT_KEEP_ALIVE: bool = True
DEFAULT_KEEP_ALIVE_TIMEOUT_SECONDS: int = 30
DEFAULT_USE_DNS_CACHE: bool = True


@dataclass
class HttpClientConfig:
    """HTTP client configuration.

    We assume that tests are only sending requests to a single host (bucket).
    """

    pool_size_per_host: int = DEFAULT_POOL_SIZE_PER_HOST
    keep_alive: bool = DEFAULT_KEEP_ALIVE
    keep_alive_timeout_seconds: int = DEFAULT_KEEP_ALIVE_TIMEOUT_SECONDS
    use_dns_cache: bool = DEFAULT_USE_DNS_CACHE


def create_httpx_client(config: HttpClientConfig, **kwargs) -> httpx.Client:
    limits = httpx.Limits(
        max_connections=config.pool_size_per_host,
        max_keepalive_connections=config.pool_size_per_host,
        keepalive_expiry=config.keep_alive_timeout_seconds,
    )
    return httpx.AsyncClient(limits=limits, **kwargs)


def create_aiohttp_client(config: HttpClientConfig, **kwargs) -> aiohttp.ClientSession:
    connector = aiohttp.TCPConnector(
        force_close=not config.keep_alive,
        limit=config.pool_size_per_host,
        limit_per_host=config.pool_size_per_host,
        keepalive_timeout=config.keep_alive_timeout_seconds,
        use_dns_cache=config.use_dns_cache,
    )
    return aiohttp.ClientSession(connector=connector, **kwargs)


def create_requests_session(config: HttpClientConfig) -> requests.Session:
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=config.pool_size_per_host,
        pool_maxsize=config.pool_size_per_host,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def create_aioboto3_s3_client(config: HttpClientConfig, region_name: str, **kwargs):
    session = aioboto3.Session()
    botocore_config = botocore.config.Config(
        max_pool_connections=config.pool_size_per_host,
        tcp_keepalive=config.keep_alive,
        region_name=region_name,
        **kwargs,
    )
    return session.client("s3", config=botocore_config)


def create_fsspec_s3(config: HttpClientConfig, region_name: str, **kwargs):
    botocore_config = {
        "max_pool_connections": config.pool_size_per_host,
        "tcp_keepalive": config.keep_alive,
        "region_name": region_name,
        **kwargs,
    }
    return s3fs.S3FileSystem(
        asynchronous=True,
        loop=asyncio.get_running_loop(),
        config_kwargs=botocore_config,
        **kwargs,
    )


def create_obstore_store(
    config: HttpClientConfig, bucket: str, region_name: str, **kwargs
) -> obs.store.S3Store:
    return obs.store.S3Store(
        bucket,
        config={"aws_default_region": region_name, "aws_skip_signature": True},
        client_options={
            "pool_max_idle_per_host": str(config.pool_size_per_host),
            "http2_keep_alive_timeout": str(config.keep_alive_timeout_seconds) + "s",
            **kwargs,
        },
    )


def create_async_tiff_s3_store(
    config: HttpClientConfig, bucket: str, region_name: str, **kwargs
) -> async_tiff.store.S3Store:
    return async_tiff.store.S3Store(
        bucket,
        region=region_name,
        skip_signature=True,
        client_options={
            "pool_max_idle_per_host": str(config.pool_size_per_host),
            "http2_keep_alive_timeout": str(config.keep_alive_timeout_seconds) + "s",
            **kwargs,
        },
    )
