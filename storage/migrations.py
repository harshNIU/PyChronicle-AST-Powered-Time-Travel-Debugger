import sqlite3


CURRENT_VERSION = 1


def get_schema_version(connection: sqlite3.Connection) -> int:
    """Return the current database schema version."""
    return connection.execute("PRAGMA user_version").fetchone()[0]


def set_schema_version(connection: sqlite3.Connection, version: int) -> None:
    """Set the database schema version."""
    connection.execute(f"PRAGMA user_version = {version}")


def migrate(connection: sqlite3.Connection) -> None:
    """Apply database migrations up to the current schema version."""
    version = get_schema_version(connection)

    if version > CURRENT_VERSION:
        raise RuntimeError(
            f"Database version {version} is newer than supported version "
            f"{CURRENT_VERSION}."
        )

    if version < 1:
        set_schema_version(connection, 1)
        version = 1
