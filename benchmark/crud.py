import sqlite3
from datetime import datetime
from dataclasses import dataclass


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
) -> None:
    # Track state about each worker
    sql = "INSERT INTO workers VALUES (?,?,?,?,?,?,?)"
    cur = conn.cursor()
    cur.execute(
        sql,
        (
            library_name,
            test_name,
            state.start_time,
            state.end_time,
            state.n_requests,
            container_id,
            run_id,
        ),
    )
    conn.commit()
    cur.close()
