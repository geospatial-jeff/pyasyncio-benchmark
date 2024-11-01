import argparse
from importlib import import_module
import sys
import sqlite3


from benchmark.crud import insert_row, WorkerState


def run_test(library_name: str, test_name: str):
    mod = import_module(f"benchmark.tests.{library_name}.{test_name}")
    worker_state: WorkerState = mod.main()

    with sqlite3.connect("sqlite.db") as conn:
        insert_row(conn, library_name, test_name, worker_state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("library_name")
    parser.add_argument("test_name")
    args = parser.parse_args()

    run_test(args.library_name, args.test_name)

    # Kill the container
    sys.exit(1)
