import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent / "pychronicle.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_db() -> None:
    """Create the delta-storage database tables if they do not exist."""
    with sqlite3.connect(DB_PATH) as connection:
        with open(SCHEMA_PATH, "r") as schema_file:
            schema = schema_file.read()

        connection.executescript(schema)


def get_connection() -> sqlite3.Connection:
    """Return a connection to the PyChronicle database."""
    return sqlite3.connect(DB_PATH)


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