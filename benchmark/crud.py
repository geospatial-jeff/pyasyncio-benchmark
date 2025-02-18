import sqlite3
from datetime import datetime
from dataclasses import dataclass

from benchmark.clients import HttpClientConfig


@dataclass
class WorkerState:
    start_time: datetime
    end_time: datetime
    n_requests: int
    n_failures: int

    @property
    def n_successes(self) -> int:
        return self.n_requests - self.n_failures


def insert_row(
    conn: sqlite3.Connection,
    library_name: str,
    test_name: str,
    container_id: str,
    run_id: str,
    state: WorkerState,
    client_config: HttpClientConfig,
) -> None:
    # Track state about each worker
    sql = "INSERT INTO workers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"
    cur = conn.cursor()
    cur.execute(
        sql,
        (
            library_name,
            test_name,
            state.start_time,
            state.end_time,
            state.n_requests,
            state.n_failures,
            state.n_successes,
            container_id,
            run_id,
            client_config.pool_size_per_host,
            client_config.keep_alive,
            client_config.keep_alive_timeout_seconds,
            client_config.use_dns_cache,
        ),
    )
    conn.commit()
    cur.close()
