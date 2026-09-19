import sqlite3


class TimelineStore:
    """
    Persists execution history to a SQLite database so that
    a program's timeline can be inspected after it finishes running.
    """

    def __init__(self, db_path="timeline.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS execution_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                step_index INTEGER,
                line_number INTEGER,
                changed_vars TEXT
            )
        """)
        self.conn.commit()

    def save_history(self, history):
        for i, step in enumerate(history):
            self.conn.execute(
                "INSERT INTO execution_steps (step_index, line_number, changed_vars) VALUES (?, ?, ?)",
                (i, step["line"], str(step["changed"]))
            )
        self.conn.commit()

    def load_history(self):
        cursor = self.conn.execute(
            "SELECT step_index, line_number, changed_vars FROM execution_steps ORDER BY step_index"
        )
        return cursor.fetchall()

    def clear(self):
        self.conn.execute("DELETE FROM execution_steps")
        self.conn.commit()

    def close(self):
        self.conn.close()