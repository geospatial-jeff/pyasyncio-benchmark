import uuid
import sqlite3
from datetime import datetime
from dataclasses import dataclass


@dataclass
class WorkerState:
    start_time: datetime
    end_time: datetime
    n_requests: int
    worker_id: str = str(uuid.uuid4())


def insert_row(
    conn: sqlite3.Connection, library_name: str, test_name: str, state: WorkerState
) -> None:
    # Track state about each worker
    sql = "INSERT INTO workers VALUES (?,?,?,?,?,?)"
    cur = conn.cursor()
    cur.execute(
        sql,
        (
            library_name,
            test_name,
            state.start_time,
            state.end_time,
            state.worker_id,
            state.n_requests,
        ),
    )
    conn.commit()
    cur.close()
