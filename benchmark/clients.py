from dataclasses import dataclass
import aioboto3
import aiohttp
import httpx
import requests.adapters
import botocore.config
import s3fs
import obstore as obs


@dataclass
class HttpClientConfig:
    """HTTP client configuration.

    We assume that tests are only sending requests to a single host (bucket).
    """

    pool_size_per_host: int = 50
    keep_alive: bool = True
    keep_alive_timeout_seconds: int = 30
    use_dns_cache: bool = True


def create_httpx_client(config: HttpClientConfig, **kwargs) -> httpx.Client:
    limits = httpx.Limits(
        max_connections=config.pool_size_per_host,
        max_keepalive_connections=config.pool_size_per_host,
        keepalive_expiry=config.keep_alive_timeout_seconds,
    )
    return httpx.Client(limits=limits, **kwargs)


def create_aiohttp_client(config: HttpClientConfig, **kwargs) -> aiohttp.ClientSession:
    transport = aiohttp.TCPConnector(
        force_close=config.keep_alive,
        limit=config.pool_size_per_host,
        limit_per_host=config.pool_size_per_host,
        keepalive_timeout=config.keep_alive_timeout_seconds,
        use_dns_cache=config.use_dns_cache,
    )
    return aiohttp.ClientSession(transport=transport, **kwargs)


def create_requests_session(config: HttpClientConfig) -> requests.Session:
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=config.pool_size_per_host,
        pool_maxsize=config.pool_size_per_host,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def create_aioboto3_s3_client(config: HttpClientConfig, **kwargs):
    session = aioboto3.Session()
    botocore_config = botocore.config.Config(
        max_pool_connections=config.pool_size_per_host,
        tcp_keepalive=config.keep_alive,
        **kwargs,
    )
    return session.client("s3", config=botocore_config)


def create_fsspec_s3(config: HttpClientConfig, **kwargs):
    botocore_config = {
        "max_pool_connections": config.pool_size_per_host,
        "tcp_keepalive": config.keep_alive,
        **kwargs,
    }
    return s3fs.S3FileSystem(asynchronous=True, config_kwargs=botocore_config, **kwargs)


def create_obstore_store(
    config: HttpClientConfig, bucket: str, **kwargs
) -> obs.store.S3Store:
    return obs.store.S3Store(
        bucket,
        config=obs.store.ClientConfig(
            pool_max_idle_per_host=config.pool_size_per_host,
            http2_keep_alive_timeout=config.keep_alive_timeout_seconds,
            **kwargs,
        ),
    )
