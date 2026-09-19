import sqlite3


class TimelineStore:
    """
    Persists execution history to a SQLite database so that
    a program's timeline can be inspected after it finishes running.

    Day 5 improvements:
    - Schema now supports all event types (call, line, return),
      not just line changes
    - Stores function name and call depth for every step, so the
      full call stack can be reconstructed from storage alone
    """

    def __init__(self, db_path="timeline.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS execution_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                step_index INTEGER,
                event_type TEXT,
                function_name TEXT,
                depth INTEGER,
                line_number INTEGER,
                changed_vars TEXT,
                return_value TEXT
            )
        """)
        self.conn.commit()

    def save_history(self, history):
        for i, step in enumerate(history):
            self.conn.execute(
                """
                INSERT INTO execution_steps
                    (step_index, event_type, function_name, depth, line_number, changed_vars, return_value)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    i,
                    step.get("type"),
                    step.get("function"),
                    step.get("depth"),
                    step.get("line"),
                    str(step["changed"]) if "changed" in step else None,
                    str(step["value"]) if "value" in step else None,
                )
            )
        self.conn.commit()

    def load_history(self):
        cursor = self.conn.execute(
            """
            SELECT step_index, event_type, function_name, depth,
                   line_number, changed_vars, return_value
            FROM execution_steps
            ORDER BY step_index
            """
        )
        return cursor.fetchall()

    def clear(self):
        self.conn.execute("DELETE FROM execution_steps")
        self.conn.commit()

    def close(self):
        self.conn.close()