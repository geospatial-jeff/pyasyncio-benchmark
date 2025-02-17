import os
from collections import defaultdict
import functools
import click
import subprocess

import docker

from benchmark import main
from benchmark.docker_utils import block_until_container_exits
from benchmark.aggregate import summarize_test_results
from benchmark.clients import (
    HttpClientConfig,
    DEFAULT_USE_DNS_CACHE,
    DEFAULT_KEEP_ALIVE,
    DEFAULT_KEEP_ALIVE_TIMEOUT_SECONDS,
    DEFAULT_POOL_SIZE_PER_HOST,
)


def collect_tests() -> dict:
    dir_path = os.path.dirname(os.path.realpath(__file__))

    tests = defaultdict(list)
    for path, _, files in os.walk(dir_path + "/tests"):
        for name in files:
            if not name.endswith(".py"):
                continue
            if name.endswith("__init__.py"):
                continue

            full_path = os.path.join(path, name)
            splits = full_path.split("/")

            library_name = splits[-2]
            test_name = splits[-1].replace(".py", "")
            tests[library_name].append(test_name)
    return dict(tests)


@click.group
def app():
    pass


def _run_test(
    library_name: str,
    test_name: str,
    replicas: int,
    debug: bool,
    pool_size: int,
    keep_alive: bool,
    keep_alive_timeout: int,
    use_dns_cache: bool,
):
    all_tests = collect_tests()

    # Validations
    try:
        library = all_tests[library_name]
    except KeyError:
        raise ValueError(f"Library {library_name} not found.")

    if test_name not in library:
        raise ValueError(f"Test {test_name} not found.")

    # Build the container.
    image_tag = f"{library_name}-{test_name}"
    subprocess.run(
        [
            "docker",
            "build",
            ".",
            "-t",
            f"pyasyncio-benchmark:{image_tag}",
            "--build-arg",
            f"LIBRARY_NAME={library_name}",
            "--build-arg",
            f"TEST_NAME={test_name}",
            "--build-arg",
            f"POOL_SIZE={pool_size}",
            "--build-arg",
            f"KEEP_ALIVE={keep_alive}",
            "--build-arg",
            f"KEEP_ALIVE_TIMEOUT={keep_alive_timeout}",
            "--build-arg",
            f"USE_DNS_CACHE={use_dns_cache}",
        ]
    )

    # Run the docker-compose stack
    command = ["docker", "compose", "up"]
    if not debug:
        command.append("-d")
    container_env = os.environ.copy() | {
        "IMAGE_TAG": image_tag,
        "REPLICA_COUNT": str(replicas),
    }
    subprocess.run(command, env=container_env)


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
@click.option(
    "--debug", is_flag=True, show_default=True, default=False, help="Debug mode"
)
@client_options
def run_test(
    library_name: str,
    test_name: str,
    replicas: int = 1,
    debug: bool = False,
    pool_size: int = DEFAULT_POOL_SIZE_PER_HOST,
    keep_alive: bool = DEFAULT_KEEP_ALIVE,
    keep_alive_timeout: int = DEFAULT_KEEP_ALIVE_TIMEOUT_SECONDS,
    use_dns_cache: bool = DEFAULT_USE_DNS_CACHE,
):
    """Run a single test."""
    _run_test(
        library_name,
        test_name,
        replicas,
        debug,
        pool_size,
        keep_alive,
        keep_alive_timeout,
        use_dns_cache,
    )


@app.command
@click.option("--library-name")
@click.option("--test-name")
@click.option("--replicas", type=int, default=1)
@click.option(
    "--debug", is_flag=True, show_default=True, default=False, help="Debug mode"
)
@client_options
def run_all(
    library_name: str,
    test_name: str,
    replicas: int = 1,
    debug: bool = False,
    pool_size: int = DEFAULT_POOL_SIZE_PER_HOST,
    keep_alive: bool = DEFAULT_KEEP_ALIVE,
    keep_alive_timeout: int = DEFAULT_KEEP_ALIVE_TIMEOUT_SECONDS,
    use_dns_cache: bool = DEFAULT_USE_DNS_CACHE,
):
    """Run all available tests."""
    docker_client = docker.from_env()

    all_tests = collect_tests()
    click.echo(f"Collected tests - {all_tests}")
    for library_name, tests in all_tests.items():
        for test_name in tests:
            click.echo(f"Running test {library_name}.{test_name}")
            _run_test(
                library_name,
                test_name,
                replicas,
                debug,
                pool_size,
                keep_alive,
                keep_alive_timeout,
                use_dns_cache,
            )

            block_until_container_exits(docker_client)


@app.command
@click.argument("filepath")
@click.option(
    "--sampling-interval",
    type=int,
    default=5,
    help="Prometheus sampling window in seconds, should be smaller than the longest running test.",
)
def get_results(filepath: str, sampling_interval: int = 5):
    """Save test results to CSV file."""
    summarize_test_results(sampling_interval).to_csv(filepath, header=True, index=False)


@app.command
@click.argument("library_name")
@click.argument("test_name")
@client_options
def docker_entrypoint(
    library_name: str,
    test_name: str,
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
    main.run_test(library_name, test_name, client_config)
