import argparse
import uuid
import sqlite3
from importlib import import_module
import sys


def run_test(library_name: str, test_name: str, worker_id: str):
    mod = import_module(f"benchmark.tests.{library_name}.{test_name}")
    start_time, end_time = mod.main()

    # Track state about each worker
    sql = "INSERT INTO workers VALUES (?,?,?,?,?)"
    with sqlite3.connect("sqlite.db") as conn:
        cur = conn.cursor()
        cur.execute(sql, (library_name, test_name, start_time, end_time, worker_id))
        conn.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("library_name")
    parser.add_argument("test_name")
    args = parser.parse_args()

    worker_id = str(uuid.uuid4())
    run_test(args.library_name, args.test_name, worker_id)

    # Kill the container
    sys.exit(1)
