import sqlite3


class TimelineStore:
    """
    Persists execution history to a SQLite database so that
    a program's timeline can be inspected after it finishes running.

    Day 7 improvements:
    - Schema now also supports "exception" events, alongside
      call/line/return, so tracebacks are part of the persisted
      timeline, not just call/line/return
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
                    str(step["changed"]) if "changed" in step else None,
                    str(step["value"]) if "value" in step else None,
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


if __name__ == "__main__":
    from timeline_store import TimelineStore

    tracer = ExecutionTracer(target_file=__file__)
    tracer.start()

    sample_program()

    tracer.stop()
    tracer.print_timeline()

    store = TimelineStore()
    store.clear()
    store.save_history(tracer.history)  # exceptions are now saved too

    print("\n--- Reloaded from storage ---")
    for (step_index, event_type, function_name, depth, line_number,
         changed_vars, return_value, exception_type, exception_message) in store.load_history():

        indent = "    " * max((depth or 1) - 1, 0)

        if event_type == "call":
            print(f"[{step_index}] {indent}-> Entering {function_name}() at line {line_number}")
        elif event_type == "return":
            print(f"[{step_index}] {indent}<- Exiting {function_name}() at line {line_number} -> returned {return_value}")
        elif event_type == "exception":
            print(f"[{step_index}] {indent}!! Exception in {function_name}() at line {line_number}: "
                  f"{exception_type}: {exception_message}")
        else:
            print(f"[{step_index}] {indent}Line {line_number} ({function_name}) | Changed: {changed_vars}")

    store.close()