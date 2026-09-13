from storage.db import init_db, get_connection


def test_database_connection():
    init_db()

    connection = get_connection()

    assert connection is not None

    connection.close()