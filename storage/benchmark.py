import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "benchmark.db"

EVENT_COUNT = 10_000


def run_benchmark():
    """Insert synthetic events and measure SQLite write throughput."""

    if DB_PATH.exists():
        DB_PATH.unlink()

    connection = sqlite3.connect(DB_PATH)

    connection.execute(
        """
        CREATE TABLE events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            line_number INTEGER NOT NULL,
            variable_name TEXT NOT NULL,
            serialized_value TEXT NOT NULL
        )
        """
    )

    events = [
        (
            float(index),
            index % 100,
            f"variable_{index % 20}",
            str(index),
        )
        for index in range(EVENT_COUNT)
    ]

    start_time = time.perf_counter()

    connection.executemany(
        """
        INSERT INTO events (
            timestamp,
            line_number,
            variable_name,
            serialized_value
        )
        VALUES (?, ?, ?, ?)
        """,
        events,
    )

    connection.commit()

    elapsed = time.perf_counter() - start_time

    connection.close()

    events_per_second = EVENT_COUNT / elapsed

    print(f"Events inserted: {EVENT_COUNT}")
    print(f"Time taken: {elapsed:.6f} seconds")
    print(f"Write throughput: {events_per_second:.2f} events/second")


if __name__ == "__main__":
    run_benchmark()