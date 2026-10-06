"""SQLite state storage and connection management for PyChronicle."""

import atexit
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from storage.migrations import migrate


DB_PATH = Path(__file__).parent / "pychronicle.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

_CONNECTION_POOL: list[sqlite3.Connection] = []
_MAX_POOL_SIZE = 5


def _create_connection() -> sqlite3.Connection:
    """Create a database connection with foreign-key enforcement enabled."""
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _release_connection(connection: sqlite3.Connection) -> None:
    """Return a connection to the pool or close it when the pool is full."""
    # Keep only a small number of idle connections for reuse.
    if len(_CONNECTION_POOL) < _MAX_POOL_SIZE:
        _CONNECTION_POOL.append(connection)
    else:
        connection.close()


@contextmanager
def get_connection():
    """Provide a reusable database connection and return it to the pool."""
    # Reuse an idle connection when one is available.
    if _CONNECTION_POOL:
        connection = _CONNECTION_POOL.pop()
    else:
        connection = _create_connection()

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        _release_connection(connection)


def init_db() -> None:
    """Create the delta-storage database tables if they do not exist."""
    with get_connection() as connection:
        with open(SCHEMA_PATH, "r") as schema_file:
            schema = schema_file.read()

        connection.executescript(schema)
        migrate(connection)


def close_connections() -> None:
    """Close all idle database connections before the application exits."""
    while _CONNECTION_POOL:
        connection = _CONNECTION_POOL.pop()
        try:
            connection.close()
        except sqlite3.Error:
            pass


# Close pooled connections automatically when Python exits.
atexit.register(close_connections)


def save_event(
    timestamp: float,
    line_number: int,
    variable_name: str,
    serialized_value: str,
) -> None:
    """Save a variable change as a delta frame."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO frames (
                timestamp_ns,
                line_number,
                event,
                scope
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                int(timestamp * 1_000_000_000),
                line_number,
                "change",
                "global",
            ),
        )

        frame_id = cursor.lastrowid

        connection.execute(
            """
            INSERT INTO changes (
                frame_id,
                scope,
                variable_name,
                value_json,
                operation
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                frame_id,
                "global",
                variable_name,
                serialized_value,
                "set",
            ),
        )


def get_events() -> list[tuple]:
    """Return stored variable changes in frame order."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT
                f.id,
                f.timestamp_ns / 1000000000.0,
                f.line_number,
                c.variable_name,
                c.value_json
            FROM frames AS f
            JOIN changes AS c
                ON c.frame_id = f.id
            ORDER BY f.id
            """
        )

        return cursor.fetchall()


def clear_events() -> None:
    """Delete all stored frames and changes."""
    with get_connection() as connection:
        connection.execute("DELETE FROM changes")
        connection.execute("DELETE FROM frames")
