import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent / "pychronicle.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_db() -> None:
    """Create the database tables if they do not exist."""
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
    """Save one variable event to the database."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO events (
                timestamp,
                line_number,
                variable_name,
                serialized_value
            )
            VALUES (?, ?, ?, ?)
            """,
            (timestamp, line_number, variable_name, serialized_value),
        )


def get_events() -> list[tuple]:
    """Return all stored events."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT id, timestamp, line_number, variable_name, serialized_value
            FROM events
            ORDER BY id
            """
        )

        return cursor.fetchall()


def clear_events() -> None:
    """Delete all stored events."""
    with get_connection() as connection:
        connection.execute("DELETE FROM events")