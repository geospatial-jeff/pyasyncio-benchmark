import argparse
from importlib import import_module
import sys


def run_test(library_name: str, test_name: str):
    mod = import_module(f"benchmark.tests.{library_name}.{test_name}")
    mod.main()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("library_name")
    parser.add_argument("test_name")
    args = parser.parse_args()

    run_test(args.library_name, args.test_name)

    # Kill the container
    sys.exit(1)
