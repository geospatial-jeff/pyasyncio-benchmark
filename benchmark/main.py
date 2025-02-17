from importlib import import_module
import sqlite3

from benchmark.docker_utils import get_container_id
from benchmark.crud import insert_row, WorkerState
from benchmark.settings import get_settings
from benchmark.clients import HttpClientConfig


def run_test(
    library_name: str, test_name: str, run_id: str, client_config: HttpClientConfig
):
    mod = import_module(f"benchmark.tests.{library_name}.{test_name}")
    worker_state: WorkerState = mod.main(client_config)

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
        )
