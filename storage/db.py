import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent / "pychronicle.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_db() -> None:
    """Create the database tables if they do not exist."""
    connection = sqlite3.connect(DB_PATH)

    with open(SCHEMA_PATH, "r") as schema_file:
        schema = schema_file.read()

    connection.executescript(schema)
    connection.commit()
    connection.close()


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
    connection = get_connection()

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

    connection.commit()
    connection.close()


def get_events() -> list[tuple]:
    """Return all stored events."""
    connection = get_connection()

    cursor = connection.execute(
        """
        SELECT id, timestamp, line_number, variable_name, serialized_value
        FROM events
        ORDER BY id
        """
    )

    events = cursor.fetchall()
    connection.close()

    return events


def clear_events() -> None:
    """Delete all stored events."""
    connection = get_connection()
    connection.execute("DELETE FROM events")
    connection.commit()
    connection.close()