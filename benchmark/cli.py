import os
from collections import defaultdict
import click
import subprocess

import docker

from benchmark import main
from benchmark.docker_utils import block_until_container_exits
from benchmark.aggregate import summarize_test_results


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


def _run_test(library_name: str, test_name: str, replicas: int, debug: bool):
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


@app.command
@click.argument("library_name")
@click.argument("test_name")
@click.option("--replicas", type=int, default=1)
@click.option(
    "--debug", is_flag=True, show_default=True, default=False, help="Debug mode"
)
def run_test(library_name: str, test_name: str, replicas: int = 1, debug: bool = False):
    """Run a single test."""
    _run_test(library_name, test_name, replicas, debug)


@app.command
@click.option("--library-name")
@click.option("--test-name")
@click.option("--replicas", type=int, default=1)
@click.option(
    "--debug", is_flag=True, show_default=True, default=False, help="Debug mode"
)
def run_all(library_name: str, test_name: str, replicas: int = 1, debug: bool = False):
    """Run all available tests."""
    docker_client = docker.from_env()

    all_tests = collect_tests()
    click.echo(f"Collected tests - {all_tests}")
    for library_name, tests in all_tests.items():
        for test_name in tests:
            click.echo(f"Running test {library_name}.{test_name}")
            _run_test(library_name, test_name, replicas, debug)

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
def docker_entrypoint(library_name: str, test_name: str):
    """Docker entrypoint, don't call this directly."""
    main.run_test(library_name, test_name)
