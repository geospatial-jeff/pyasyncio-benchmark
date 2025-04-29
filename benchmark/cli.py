import os
import functools
import click
import json

import docker

from benchmark import main
from benchmark.docker_utils import block_until_container_exits
from benchmark.aggregate import (
    summarize_test_results_workers,
    summarize_test_results_deployment,
)
from benchmark.clients import (
    HttpClientConfig,
    DEFAULT_USE_DNS_CACHE,
    DEFAULT_KEEP_ALIVE,
    DEFAULT_KEEP_ALIVE_TIMEOUT_SECONDS,
    DEFAULT_POOL_SIZE_PER_HOST,
)
from benchmark.parameterize import TestConfig


@click.group
def app():
    pass


def client_options(f):
    @click.option("--pool-size", type=int, default=DEFAULT_POOL_SIZE_PER_HOST)
    @click.option("--keep-alive", type=bool, default=DEFAULT_KEEP_ALIVE)
    @click.option(
        "--keep-alive-timeout", type=int, default=DEFAULT_KEEP_ALIVE_TIMEOUT_SECONDS
    )
    @click.option("--use-dns-cache", type=bool, default=DEFAULT_USE_DNS_CACHE)
    @functools.wraps(f)
    def wrapper_common_options(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper_common_options


@app.command
@click.argument("library_name")
@click.argument("test_name")
@click.option("--replicas", type=int, default=1)
@click.option("--n-requests", type=int, default=1000)
@click.option("--timeout", type=int, default=-1)
@click.option(
    "--debug", is_flag=True, show_default=True, default=False, help="Debug mode"
)
@client_options
def run_test(
    library_name: str,
    test_name: str,
    replicas: int = 1,
    n_requests: int = 1000,
    timeout: int = -1,
    debug: bool = False,
    pool_size: int = DEFAULT_POOL_SIZE_PER_HOST,
    keep_alive: bool = DEFAULT_KEEP_ALIVE,
    keep_alive_timeout: int = DEFAULT_KEEP_ALIVE_TIMEOUT_SECONDS,
    use_dns_cache: bool = DEFAULT_USE_DNS_CACHE,
):
    """Run a single test."""
    main.run_test_docker(
        library_name,
        test_name,
        replicas,
        n_requests,
        timeout,
        debug,
        pool_size,
        keep_alive,
        keep_alive_timeout,
        use_dns_cache,
    )


@app.command
@click.option("--library-name", type=str)
@click.option("--test-name", type=str)
@click.option("--n-requests", type=int, default=1000)
@click.option("--replicas", type=int, default=1)
@click.option("--timeout", type=int, default=-1)
@click.option(
    "--debug", is_flag=True, show_default=True, default=False, help="Debug mode"
)
@client_options
def run_all(
    library_name: str,
    test_name: str,
    n_requests: int = 1000,
    replicas: int = 1,
    timeout: int = -1,
    debug: bool = False,
    pool_size: int = DEFAULT_POOL_SIZE_PER_HOST,
    keep_alive: bool = DEFAULT_KEEP_ALIVE,
    keep_alive_timeout: int = DEFAULT_KEEP_ALIVE_TIMEOUT_SECONDS,
    use_dns_cache: bool = DEFAULT_USE_DNS_CACHE,
):
    """Run all available tests."""
    docker_client = docker.from_env()

    all_tests = main.collect_tests()
    click.echo(f"Collected tests - {all_tests}")
    for library_name, tests in all_tests.items():
        for test_name in tests:
            click.echo(f"Running test {library_name}.{test_name}")
            main.run_test_docker(
                library_name,
                test_name,
                replicas,
                n_requests,
                timeout,
                debug,
                pool_size,
                keep_alive,
                keep_alive_timeout,
                use_dns_cache,
            )

            block_until_container_exits(docker_client)


@app.command
@click.argument(
    "folder_path", type=click.Path(exists=True, file_okay=False, readable=True)
)
@click.option(
    "--sampling-interval",
    type=int,
    default=5,
    help="Prometheus sampling window in seconds, should be smaller than the longest running test.",
)
def get_results(folder_path: str, sampling_interval: int = 5):
    """Save test results to CSV file."""
    summarize_test_results_workers(sampling_interval).to_csv(
        os.path.join(folder_path, "container_results.csv"), header=True, index=False
    )
    summarize_test_results_deployment(sampling_interval).to_csv(
        os.path.join(folder_path, "aggregated_results.csv"), header=True, index=False
    )


@app.command
@click.argument(
    "config_file_path", type=click.Path(exists=True, file_okay=True, readable=True)
)
def run_parameterized_test(config_file_path: str):
    """Run parameterized test."""
    main.run_parameterized_test(TestConfig.from_yaml(config_file_path))


@app.command
@click.argument("library_name")
@click.argument("test_name")
@click.argument("run_id")
@click.option("--n-requests", type=int, default=1000)
@click.option("--timeout", type=int, default=-1)
@client_options
def docker_entrypoint(
    library_name: str,
    test_name: str,
    run_id: str,
    n_requests: int = 1000,
    timeout: int = -1,
    pool_size: int = DEFAULT_POOL_SIZE_PER_HOST,
    keep_alive: bool = DEFAULT_KEEP_ALIVE,
    keep_alive_timeout: int = DEFAULT_KEEP_ALIVE_TIMEOUT_SECONDS,
    use_dns_cache: bool = DEFAULT_USE_DNS_CACHE,
):
    """Docker entrypoint, don't call this directly."""
    client_config = HttpClientConfig(
        pool_size_per_host=pool_size,
        keep_alive=keep_alive,
        keep_alive_timeout_seconds=keep_alive_timeout,
        use_dns_cache=use_dns_cache,
    )
    test_params = os.getenv("TEST_PARAMS", str({})).replace("'", '"')
    test_params = json.loads(test_params[1:-1])
    main.run_test(
        library_name, test_name, run_id, n_requests, timeout, client_config, test_params
    )
