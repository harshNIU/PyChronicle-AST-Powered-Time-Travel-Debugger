import sys


class ExecutionTracer:
    """
    Tracks execution history using sys.settrace.

    Day 2 improvements:
    - Only traces the target file (ignores library/internal calls)
    - Records only variables that changed since the last line (deltas),
      instead of the full locals dict every time
    """

    def __init__(self, target_file=None):
        self.target_file = target_file
        self.history = []
        self._last_locals = {}

    def _get_changes(self, current_locals):
        changes = {}
        for key, value in current_locals.items():
            if key not in self._last_locals or self._last_locals[key] != value:
                changes[key] = value
        return changes

    def trace_calls(self, frame, event, arg):
        if self.target_file and frame.f_code.co_filename != self.target_file:
            return None  # skip code outside our target file

        if event == "line":
            changes = self._get_changes(frame.f_locals)
            if changes:
                self.history.append({
                    "line": frame.f_lineno,
                    "changed": changes,
                })
                self._last_locals = frame.f_locals.copy()

        return self.trace_calls

    def start(self):
        sys.settrace(self.trace_calls)

    def stop(self):
        sys.settrace(None)

    def print_timeline(self):
        print("\n--- Execution Timeline (deltas only) ---")
        for i, step in enumerate(self.history):
            print(f"[{i}] Line {step['line']} | Changed: {step['changed']}")


def sample_program():
    total = 0
    for i in range(3):
        total += i
    return total


if __name__ == "__main__":
    from timeline_store import TimelineStore

    tracer = ExecutionTracer(target_file=__file__)
    tracer.start()

    sample_program()

    tracer.stop()
    tracer.print_timeline()

    store = TimelineStore()
    store.clear()
    store.save_history(tracer.history)

    print("\n--- Reloaded from storage ---")
    for step_index, line_number, changed in store.load_history():
        print(f"[{step_index}] Line {line_number} | Changed: {changed}")

    store.close()
    