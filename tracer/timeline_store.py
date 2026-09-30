"""
SQLite storage for PyChronicle execution timelines.

TimelineStore saves the history recorded by ExecutionTracer (calls, lines,
returns and exceptions) into a SQLite file and loads it back afterwards.

Day 12-15 improvements:
- Stores the literal source line of code alongside each step
- Adds query helpers (get_steps_by_function, get_steps_by_type,
  get_exceptions) so a saved timeline can be filtered without loading
  and re-scanning the entire history in Python
"""

import sqlite3


class TimelineStore:
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
                exception_message TEXT,
                source_text TEXT
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
                     changed_vars, return_value, exception_type, exception_message, source_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    step.get("source"),
                )
            )
        self.conn.commit()

    def _select(self, where_clause="", params=()):
        query = """
            SELECT step_index, event_type, function_name, depth, line_number,
                   changed_vars, return_value, exception_type, exception_message,
                   source_text
            FROM execution_steps
        """
        if where_clause:
            query += f" WHERE {where_clause}"
        query += " ORDER BY step_index"

        cursor = self.conn.execute(query, params)
        return cursor.fetchall()

    def load_history(self):
        return self._select()

    def get_steps_by_function(self, function_name):
        return self._select("function_name = ?", (function_name,))

    def get_steps_by_type(self, event_type):
        return self._select("event_type = ?", (event_type,))

    def get_exceptions(self):
        return self.get_steps_by_type("exception")

    def clear(self):
        self.conn.execute("DELETE FROM execution_steps")
        self.conn.commit()

    def close(self):
        self.conn.close()