import argparse

from importlib import import_module


def run_test(test_name: str):
    mod = import_module(f"benchmark.tests.{test_name}")
    mod.main()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("test_name")
    args = parser.parse_args()

    run_test(args.test_name)
    
