import sys


class ExecutionTracer:
    """
    Tracks execution history using sys.settrace.

    Day 4 improvements:
    - Tracks function calls and returns, not just line events
    - Records call stack depth, so nested function calls show up
      as indentation in the timeline
    - Gives the timeline a real "story": entering/exiting functions,
      not just a flat list of lines
    """

    def __init__(self, target_file=None):
        self.target_file = target_file
        self.history = []
        self._last_locals = {}
        self.call_stack = []

    def _get_changes(self, current_locals):
        changes = {}
        for key, value in current_locals.items():
            if key not in self._last_locals or self._last_locals[key] != value:
                changes[key] = value
        return changes

    def trace_calls(self, frame, event, arg):
        if self.target_file and frame.f_code.co_filename != self.target_file:
            return None  # skip code outside our target file

        func_name = frame.f_code.co_name

        if event == "call":
            self.call_stack.append(func_name)
            self.history.append({
                "type": "call",
                "function": func_name,
                "depth": len(self.call_stack),
                "line": frame.f_lineno,
            })
            return self.trace_calls

        if event == "line":
            changes = self._get_changes(frame.f_locals)
            if changes:
                self.history.append({
                    "type": "line",
                    "function": func_name,
                    "depth": len(self.call_stack),
                    "line": frame.f_lineno,
                    "changed": changes,
                })
                self._last_locals = frame.f_locals.copy()

        elif event == "return":
            self.history.append({
                "type": "return",
                "function": func_name,
                "depth": len(self.call_stack),
                "line": frame.f_lineno,
                "value": arg,
            })
            if self.call_stack:
                self.call_stack.pop()

        return self.trace_calls

    def start(self):
        sys.settrace(self.trace_calls)

    def stop(self):
        sys.settrace(None)

    def print_timeline(self):
        print("\n--- Execution Timeline (with call stack) ---")
        for i, step in enumerate(self.history):
            indent = "    " * max(step["depth"] - 1, 0)

            if step["type"] == "call":
                print(f"[{i}] {indent}-> Entering {step['function']}() at line {step['line']}")
            elif step["type"] == "return":
                print(f"[{i}] {indent}<- Exiting {step['function']}() at line {step['line']} -> returned {step['value']}")
            else:
                print(f"[{i}] {indent}Line {step['line']} ({step['function']}) | Changed: {step['changed']}")


def add_numbers(a, b):
    result = a + b
    return result


def sample_program():
    total = add_numbers(2, 3)
    return total


if __name__ == "__main__":
    from timeline_store import TimelineStore

    tracer = ExecutionTracer(target_file=__file__)
    tracer.start()

    sample_program()

    tracer.stop()
    tracer.print_timeline()

    # Storage currently only understands "line" steps, so filter
    # call/return events out before saving (Day 5 could extend the
    # schema to store all event types)
    line_only_history = [step for step in tracer.history if step["type"] == "line"]

    store = TimelineStore()
    store.clear()
    store.save_history(line_only_history)
    store.close()