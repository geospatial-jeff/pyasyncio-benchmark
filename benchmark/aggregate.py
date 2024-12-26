import os
import sqlite3
from datetime import datetime
import requests
import pandas as pd


DB_FILEPATH = os.getenv("DB_FILEPATH", "sqlite.db")
PROMETHEUS_BASE_URL = os.getenv("PROMETHEUS_BASE_URL", "http://localhost:9090")



def evaluate_metric(query: str, start: datetime, end: datetime, step: float = 1) -> pd.DataFrame:
    """Evaluate the given metric between two time stamps."""
    r = requests.get(
        f"{PROMETHEUS_BASE_URL}/api/v1/query_range",
        params={
            "query": query,
            "start": start.isoformat() + 'Z',
            "end": end.isoformat() + 'Z',
            "step": step
        }
    )
    r.raise_for_status()
    resp_json = r.json()

    # Parse results, for convenience
    results = resp_json['data']['result'][0]['values']

    data = []
    for time_step in results:
        time_stamp = datetime.fromtimestamp(time_step[0])
        value = float(time_step[1])
        data.append((time_stamp, value))
    
    return pd.DataFrame(data, columns=["timestamp", "metric_value"])


def fetch_test_runs() -> list[sqlite3.Row]:
    with sqlite3.connect(DB_FILEPATH) as conn:
        conn.row_factory = sqlite3.Row

        sql = "SELECT library_name, test_name, MAX(start_time) as start_time, MIN(end_time) as end_time FROM workers GROUP BY library_name,test_name;"
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
    
    return rows




def summarize():
    """Summarize metrics across all test runs."""
    test_runs = fetch_test_runs()
    for run in test_runs:
        # Request data from prometheus
        start_time = datetime.strptime(run['start_time'], '%Y-%m-%d %H:%M:%S.%f')
        end_time = datetime.strptime(run['end_time'], '%Y-%m-%d %H:%M:%S.%f')

        query = 'sum by (container_label_TAG) (rate(container_network_receive_bytes_total{image="pyasyncio-benchmark:latest"}[15s]))'
        resp = evaluate_metric(query, start_time, end_time)
        summary_stats = resp['metric_value'].describe()
        print(summary_stats)