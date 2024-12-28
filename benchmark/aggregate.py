import os
import sqlite3
from datetime import datetime
import requests
import pandas as pd


DB_FILEPATH = os.getenv("DB_FILEPATH", "sqlite.db")
PROMETHEUS_BASE_URL = os.getenv("PROMETHEUS_BASE_URL", "http://localhost:9090")


def evaluate_metric(
    query: str, start: datetime, end: datetime, step: float = 1
) -> pd.DataFrame:
    """Evaluate the given query between two time stamps."""
    r = requests.get(
        f"{PROMETHEUS_BASE_URL}/api/v1/query_range",
        params={
            "query": query,
            "start": start.isoformat() + "Z",
            "end": end.isoformat() + "Z",
            "step": step,
        },
    )
    r.raise_for_status()
    resp_json = r.json()

    # Parse results
    results = resp_json["data"]["result"][0]["values"]

    data = []
    for time_step in results:
        time_stamp = datetime.fromtimestamp(time_step[0])
        value = float(time_step[1])
        data.append((time_stamp, value))

    return pd.DataFrame(data, columns=["timestamp", "metric_value"])


def fetch_test_runs() -> list[sqlite3.Row]:
    """Dump all test runs from the database."""
    with sqlite3.connect(DB_FILEPATH) as conn:
        conn.row_factory = sqlite3.Row
        sql = "SELECT * FROM workers"
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()

    return rows


def summarize():
    """Summarize metrics across all test runs."""
    test_runs = fetch_test_runs()

    results = []
    for run in test_runs:
        container_id = f"/docker/{run['container_id']}"
        start_time = datetime.strptime(run["start_time"], "%Y-%m-%d %H:%M:%S.%f")
        end_time = datetime.strptime(run["end_time"], "%Y-%m-%d %H:%M:%S.%f")

        # Network throughput
        recv_query = f'sum by (id) (rate(container_network_receive_bytes_total{{id="{container_id}"}}[15s]))'
        print(recv_query)
        resp = evaluate_metric(recv_query, start_time, end_time)
        throughput_metrics = (
            resp["metric_value"]
            .describe()
            .add_prefix("recv_bytes_per_second_")
            .transpose()
            .to_dict()
        )

        # CPU utilization
        cpu_seconds_query = f'sum by (id) (rate(container_cpu_user_seconds_total{{id="{container_id}"}}[15s]))'
        resp = evaluate_metric(cpu_seconds_query, start_time, end_time)
        cpu_metrics = (
            resp["metric_value"]
            .describe()
            .add_prefix("cpu_seconds_")
            .transpose()
            .to_dict()
        )

        # Network throughput per cpu
        resp = evaluate_metric(
            f"{recv_query} / {cpu_seconds_query}", start_time, end_time
        )
        network_per_cpu_metrics = (
            resp["metric_value"]
            .describe()
            .add_prefix("recv_bytes_per_second_per_cpu")
            .transpose()
            .to_dict()
        )

        duration_seconds = (end_time - start_time).total_seconds()
        requests_per_second = run["number_requests"] / duration_seconds

        all_metrics = {
            **throughput_metrics,
            **cpu_metrics,
            **network_per_cpu_metrics,
            "duration_seconds": duration_seconds,
            "requests_per_second": requests_per_second,
        }

        results.append(all_metrics)

    # TODO: Add top level "run-id"
    # Group results across run-ids
    return pd.DataFrame.from_records(results)


if __name__ == "__main__":
    df = summarize()
    print(df)
