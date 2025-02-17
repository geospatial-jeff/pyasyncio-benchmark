import sqlite3
from datetime import datetime, timedelta
import requests
import pandas as pd

from benchmark.settings import get_settings


def evaluate_metric(
    query: str, start: datetime, end: datetime, step: float = 1
) -> pd.DataFrame:
    """Evaluate the given query between two time stamps."""
    r = requests.get(
        f"{get_settings().PROMETHEUS_BASE_URL}/api/v1/query_range",
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
    with sqlite3.connect(get_settings().DB_FILEPATH) as conn:
        conn.row_factory = sqlite3.Row
        sql = "SELECT * FROM workers"
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()

    return rows


def summarize_test_results_workers(sampling_interval_seconds: int):
    """Summarize metrics for individual workers across all test runs."""
    test_runs = fetch_test_runs()

    results = []
    for run in test_runs:
        container_id = f"/docker/{run['container_id']}"
        print(f"Fetching metrics for container {container_id}")
        start_time = datetime.strptime(run["start_time"], "%Y-%m-%d %H:%M:%S.%f")
        end_time = datetime.strptime(run["end_time"], "%Y-%m-%d %H:%M:%S.%f")

        # Buffer `start_time` by prometheus sampling interval
        promql_start_time = start_time + timedelta(seconds=sampling_interval_seconds)

        # Network throughput
        recv_query = f'sum by (id) (rate(container_network_receive_bytes_total{{id="{container_id}"}}[{sampling_interval_seconds}s]))'
        resp = evaluate_metric(recv_query, promql_start_time, end_time)
        throughput_metrics = (
            resp["metric_value"]
            .describe()
            .add_prefix("recv_bytes_per_second_")
            .transpose()
            .to_dict()
        )

        # CPU utilization
        cpu_seconds_query = f'sum by (id) (rate(container_cpu_user_seconds_total{{id="{container_id}"}}[{sampling_interval_seconds}s]))'
        resp = evaluate_metric(cpu_seconds_query, promql_start_time, end_time)
        cpu_metrics = (
            resp["metric_value"]
            .describe()
            .add_prefix("cpu_seconds_")
            .transpose()
            .to_dict()
        )

        # Memory
        memory_query = f'sum by (id) (rate(container_memory_usage_bytes{{id="{container_id}"}}[{sampling_interval_seconds}s]))'
        resp = evaluate_metric(memory_query, promql_start_time, end_time)
        memory_usage_metrics = (
            resp["metric_value"]
            .describe()
            .add_prefix("memory_usage_bytes_")
            .transpose()
            .to_dict()
        )

        # Network throughput per cpu
        resp = evaluate_metric(
            f"{recv_query} / {cpu_seconds_query}", promql_start_time, end_time
        )
        network_per_cpu_metrics = (
            resp["metric_value"]
            .describe()
            .add_prefix("recv_bytes_per_second_per_cpu_")
            .transpose()
            .to_dict()
        )

        duration_seconds = (end_time - start_time).total_seconds()
        requests_per_second = run["number_requests"] / duration_seconds

        all_metrics = {
            **run,
            **throughput_metrics,
            **cpu_metrics,
            **network_per_cpu_metrics,
            **memory_usage_metrics,
            "duration_seconds": duration_seconds,
            "requests_per_second": requests_per_second,
        }

        results.append(all_metrics)

    return pd.DataFrame.from_records(results)


def summarize_test_results_deployment(sampling_interval_seconds: int) -> pd.DataFrame:
    """Summarize metrics for individual deployments (multiple workers) across all test runs."""
    test_runs = fetch_test_runs()
    df = pd.DataFrame.from_records([dict(run) for run in test_runs])
    df["start_time"] = pd.to_datetime(df["start_time"])
    df["end_time"] = pd.to_datetime(df["end_time"])
    grouped = df.groupby("run_id")

    results = []
    for run_id, group in grouped:
        start_time = group["start_time"].min()
        end_time = group["end_time"].max()

        # Buffer `start_time` by prometheus sampling interval
        promql_start_time = start_time + timedelta(seconds=sampling_interval_seconds)

        # Network throughput
        recv_query = f'sum by (container_label_RUN_ID) (rate(container_network_receive_bytes_total{{container_label_RUN_ID="{run_id}"}}[{sampling_interval_seconds}s]))'
        resp = evaluate_metric(recv_query, promql_start_time, end_time)
        throughput_metrics = (
            resp["metric_value"]
            .describe()
            .add_prefix("recv_bytes_per_second_")
            .transpose()
            .to_dict()
        )

        # CPU utilization
        cpu_seconds_query = f'sum by (container_label_RUN_ID) (rate(container_cpu_user_seconds_total{{container_label_RUN_ID="{run_id}"}}[{sampling_interval_seconds}s]))'
        resp = evaluate_metric(cpu_seconds_query, promql_start_time, end_time)
        cpu_metrics = (
            resp["metric_value"]
            .describe()
            .add_prefix("cpu_seconds_")
            .transpose()
            .to_dict()
        )

        # Memory
        memory_query = f'sum by (container_label_RUN_ID) (rate(container_memory_usage_bytes{{container_label_RUN_ID="{run_id}"}}[{sampling_interval_seconds}s]))'
        resp = evaluate_metric(memory_query, promql_start_time, end_time)
        memory_usage_metrics = (
            resp["metric_value"]
            .describe()
            .add_prefix("memory_usage_bytes_")
            .transpose()
            .to_dict()
        )

        # Network throughput per cpu
        resp = evaluate_metric(
            f"{recv_query} / {cpu_seconds_query}", promql_start_time, end_time
        )
        network_per_cpu_metrics = (
            resp["metric_value"]
            .describe()
            .add_prefix("recv_bytes_per_second_per_cpu_")
            .transpose()
            .to_dict()
        )

        duration_seconds = (end_time - start_time).total_seconds()
        num_requests = int(group["number_requests"].sum())
        requests_per_second = num_requests / duration_seconds

        group.drop(["container_id"], axis=1, inplace=True)
        all_metrics = {
            "library_name": group.iloc[0].library_name,
            "test_name": group.iloc[0].test_name,
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
            "number_requests": num_requests,
            "number_failures": int(group["number_failures"].sum()),
            "run_id": run_id,
            "pool_size": int(group.iloc[0].pool_size),
            "keep_alive": bool(group.iloc[0].keep_alive),
            "keep_alive_timeout_seconds": int(group.iloc[0].keep_alive_timeout_seconds),
            "use_dns_cache": bool(group.iloc[0].use_dns_cache),
            **throughput_metrics,
            **cpu_metrics,
            **network_per_cpu_metrics,
            **memory_usage_metrics,
            "duration_seconds": duration_seconds,
            "requests_per_second": requests_per_second,
        }
        results.append(all_metrics)

    return pd.DataFrame.from_records(results)
