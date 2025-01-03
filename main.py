import argparse
from importlib import import_module
import sys
import sqlite3
import requests_unixsocket


from benchmark.crud import insert_row, WorkerState
from benchmark.settings import get_settings


def get_container_id() -> str:
    """Fetches the ID of a docker container, from inside the container.  Only works if called
    from within a running container with a volume mount to `/var/run/docker.sock`, for example:

        `-v /var/run/docker.sock:/var/run/docker.sock`

    The container ID is also exposed by prometheus/cadvisor under the `id` tag
    (id=`docker/<container_id>`).  This is used to correlate each test with the metrics
    captured by prometheus.
    """
    r = requests_unixsocket.get(
        f"http+unix://%2Fvar%2Frun%2Fdocker.sock/containers/{get_settings().HOSTNAME}/json"
    )
    r.raise_for_status()
    resp_json = r.json()
    return resp_json["Id"]


def run_test(library_name: str, test_name: str):
    mod = import_module(f"benchmark.tests.{library_name}.{test_name}")
    worker_state: WorkerState = mod.main()

    container_id = get_container_id()
    with sqlite3.connect(get_settings().DB_FILEPATH) as conn:
        insert_row(
            conn,
            library_name,
            test_name,
            container_id,
            get_settings().RUN_ID,
            worker_state,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("library_name")
    parser.add_argument("test_name")
    args = parser.parse_args()

    run_test(args.library_name, args.test_name)

    # Kill the container
    sys.exit(1)
