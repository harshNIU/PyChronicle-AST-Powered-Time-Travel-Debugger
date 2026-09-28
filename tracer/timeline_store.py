import sqlite3


class TimelineStore:
    """
    Persists execution history to a SQLite database so that
    a program's timeline can be inspected after it finishes running.

    Day 8 improvements:
    - Safely serializes values that raise exceptions in repr()/str(),
      or that produce excessively long output
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
                return_value TEXT,
                exception_type TEXT,
                exception_message TEXT
            )
        """)
        self.conn.commit()

    @staticmethod
    def _safe_repr(value, max_length=200):
        try:
            text = repr(value)
        except Exception as e:
            return f"<unrepresentable {type(value).__name__}: {e}>"

        if len(text) > max_length:
            return text[:max_length] + f"...<truncated, {len(text)} chars total>"

        return text

    def _serialize_changes(self, changed_vars):
        safe_items = {key: self._safe_repr(value) for key, value in changed_vars.items()}
        return str(safe_items)

    def save_history(self, history):
        for i, step in enumerate(history):
            self.conn.execute(
                """
                INSERT INTO execution_steps
                    (step_index, event_type, function_name, depth, line_number,
                     changed_vars, return_value, exception_type, exception_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    i,
                    step.get("type"),
                    step.get("function"),
                    step.get("depth"),
                    step.get("line"),
                    self._serialize_changes(step["changed"]) if "changed" in step else None,
                    self._safe_repr(step["value"]) if "value" in step else None,
                    step.get("exception_type"),
                    step.get("exception_message"),
                )
            )
        self.conn.commit()

    def load_history(self):
        cursor = self.conn.execute(
            """
            SELECT step_index, event_type, function_name, depth, line_number,
                   changed_vars, return_value, exception_type, exception_message
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