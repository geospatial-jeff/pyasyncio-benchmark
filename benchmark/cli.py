import os
from collections import defaultdict
import click
import subprocess

from benchmark import main


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


@app.command
@click.argument("library_name")
@click.argument("test_name")
def docker_entrypoint(library_name: str, test_name: str):
    """Docker entrypoint, don't call this directly."""
    main.run_test(library_name, test_name)


@app.command
@click.argument("library_name")
@click.argument("test_name")
def run_test(library_name: str, test_name: str):
    """Run a single test."""
    all_tests = collect_tests()

    # Validations
    try:
        library = all_tests[library_name]
    except KeyError:
        raise ValueError(f"Library {library_name} not found.")

    if test_name not in library:
        raise ValueError(f"Test {test_name} not found.")

    # Build the container.
    subprocess.run(
        [
            "docker",
            "build",
            ".",
            "-t",
            f"pyasyncio-benchmark:{library_name}-{test_name}",
            "--build-arg",
            f"LIBRARY_NAME={library_name}",
            "--build-arg",
            f"TEST_NAME={test_name}",
        ]
    )

    # Run the docker-compose stack
    subprocess.run(["docker", "compose", "up", "-d"])


@app.command
@click.option("--library-name")
@click.option("--test-name")
def run_all(library_name: str, test_name: str):
    all_tests = collect_tests()
    del all_tests["aiohttp"]
    click.echo(f"Collected tests - {all_tests}")
    for library_name, tests in all_tests.items():
        for test_name in tests:
            click.echo(f"Running test {library_name}.{test_name}")
            run_test([library_name, test_name], standalone_mode=False)

            # TODO: Block until test finishes somehow.
            # ideally we don't have to attach.
