import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent / "pychronicle.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_db():
    connection = sqlite3.connect(DB_PATH)

    with open(SCHEMA_PATH, "r") as schema_file:
        schema = schema_file.read()

    connection.executescript(schema)
    connection.commit()
    connection.close()


def get_connection():
    """Return a connection to the PyChronicle database."""
    return sqlite3.connect(DB_PATH)