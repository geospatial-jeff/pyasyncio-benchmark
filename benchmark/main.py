from importlib import import_module
import itertools
from collections import defaultdict
import subprocess
import os
import uuid

import docker
import sqlite3

from benchmark.docker_utils import get_container_id, block_until_container_exits
from benchmark.crud import insert_row, WorkerState
from benchmark.settings import get_settings
from benchmark.clients import HttpClientConfig
from benchmark.parameterize import TestConfig


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


def run_parameterized_test(test_config: TestConfig):
    for test in test_config.tests:
        d = {}
        # Parse parameters for each test
        for param_name, param_config in test.params.items():
            if expression := param_config.get("expression"):
                d[param_name] = eval(expression)
            elif value := param_config.get("value"):
                d[param_name] = [value]

        prod = list(itertools.product(*list(d.values())))
        keys = list(d.keys())
        test_params = [dict(zip(keys, values)) for values in prod]

        for params in test_params:
            run_test_docker(
                test.library_name.value,
                test.test_name.value,
                test.replicas,
                test.n_requests,
                test.timeout,
                test.debug,
                test.client_config.pool_size_per_host,
                test.client_config.keep_alive,
                test.client_config.keep_alive_timeout_seconds,
                test.client_config.use_dns_cache,
                params,
            )
            block_until_container_exits(docker.from_env())


def run_test_docker(
    library_name: str,
    test_name: str,
    replicas: int,
    n_requests: int,
    timeout: int,
    debug: bool,
    pool_size: int,
    keep_alive: bool,
    keep_alive_timeout: int,
    use_dns_cache: bool,
    test_params: dict,
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
        args=[
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
            f"N_REQUESTS={n_requests}",
            "--build-arg",
            f"TIMEOUT={timeout}",
            "--build-arg",
            f"POOL_SIZE={pool_size}",
            "--build-arg",
            f"KEEP_ALIVE={keep_alive}",
            "--build-arg",
            f"KEEP_ALIVE_TIMEOUT={keep_alive_timeout}",
            "--build-arg",
            f"USE_DNS_CACHE={use_dns_cache}",
            "--build-arg",
            f"RUN_ID={str(uuid.uuid4())}",
            "--build-arg",
            f"TEST_PARAMS='{test_params}'",
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


def run_test(
    library_name: str,
    test_name: str,
    run_id: str,
    n_requests: int,
    timeout: int,
    client_config: HttpClientConfig,
    test_params: dict | None,
):
    timeout = None if timeout == -1 else timeout

    mod = import_module(f"benchmark.tests.{library_name}.{test_name}")
    worker_state: WorkerState = mod.main(
        client_config, n_requests, timeout, test_params
    )

    container_id = get_container_id()
    with sqlite3.connect(get_settings().DB_FILEPATH) as conn:
        insert_row(
            conn,
            library_name,
            test_name,
            container_id,
            run_id,
            worker_state,
            client_config,
            test_params,
        )
