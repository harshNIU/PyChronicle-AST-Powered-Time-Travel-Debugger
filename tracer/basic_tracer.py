"""
Execution tracer for PyChronicle.

Uses sys.settrace to record what happens while Python code runs:
function calls, line-by-line variable changes, returns and exceptions.
The recorded history is a list of dicts (one per event) which can be
printed with print_timeline() or saved with TimelineStore
(see timeline_store.py).

To trace any Python file from the command line, use run_tracer.py.
"""

import sys


def safe_repr(value, max_length=200):
    """
    Return repr(value) without ever raising.

    Some objects raise from __repr__ (see the Unprintable class below).
    Those are described as "<unrepresentable ...>" instead, and very long
    results are cut to max_length characters.
    """
    try:
        text = repr(value)
    except Exception as e:
        return f"<unrepresentable {type(value).__name__}: {e}>"

    if len(text) > max_length:
        return text[:max_length] + f"...<truncated, {len(text)} chars total>"

    return text


def format_changes(changed_vars):
    """Turn a {name: value} dict into a {name: safe string} dict for printing."""
    return {key: safe_repr(value) for key, value in changed_vars.items()}


class ExecutionTracer:
    """
    Records execution history using sys.settrace.

    Every recorded step is a dict with a "type" of "call", "line",
    "return" or "exception", plus the function name, call depth and
    line number. Line steps also hold the variables that changed,
    return steps hold the returned value, and exception steps hold the
    exception type and message.

    Usage:
        tracer = ExecutionTracer(target_file=__file__)
        tracer.start()
        ...code to trace...
        tracer.stop()
        tracer.print_timeline()
    """

    def __init__(self, target_file=None):
        """
        target_file: only code from this file is traced. If None,
        code from every file is traced.
        """
        self.target_file = target_file
        self.history = []
        self._last_locals = {}
        self.call_stack = []

    def _get_changes(self, current_locals):
        """
        Return only the variables that are new or changed since the last
        recorded line.

        Dunder names such as __name__ or __builtins__ are skipped, since
        they appear in module-level code and are just noise. Values that
        raise when compared are treated as changed, so nothing is dropped.
        """
        changes = {}
        for key, value in current_locals.items():
            if key.startswith("__") and key.endswith("__"):
                continue

            if key not in self._last_locals:
                changes[key] = value
                continue

            try:
                is_different = self._last_locals[key] != value
            except Exception:
                is_different = True

            if is_different:
                changes[key] = value

        return changes

    def trace_calls(self, frame, event, arg):
        """
        Callback given to sys.settrace. Python calls it on every
        call / line / return / exception event, and each one is appended
        to self.history as a dict.
        """
        if self.target_file and frame.f_code.co_filename != self.target_file:
            return None

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

        elif event == "exception":
            exc_type, exc_value, _ = arg
            self.history.append({
                "type": "exception",
                "function": func_name,
                "depth": len(self.call_stack),
                "line": frame.f_lineno,
                "exception_type": exc_type.__name__,
                "exception_message": str(exc_value),
            })

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
        """Start recording. Code that runs after this call is traced."""
        sys.settrace(self.trace_calls)

    def stop(self):
        """Stop recording."""
        sys.settrace(None)

    def print_timeline(self):
        """Print the recorded history, indented by call depth."""
        print("\n--- Execution Timeline (with call stack) ---")
        for i, step in enumerate(self.history):
            indent = "    " * max(step["depth"] - 1, 0)

            if step["type"] == "call":
                print(f"[{i}] {indent}-> Entering {step['function']}() at line {step['line']}")
            elif step["type"] == "return":
                print(f"[{i}] {indent}<- Exiting {step['function']}() at line {step['line']} -> returned {safe_repr(step['value'])}")
            elif step["type"] == "exception":
                print(f"[{i}] {indent}!! Exception in {step['function']}() at line {step['line']}: "
                      f"{step['exception_type']}: {step['exception_message']}")
            else:
                print(f"[{i}] {indent}Line {step['line']} ({step['function']}) | Changed: {format_changes(step['changed'])}")


class Unprintable:
    """A deliberately troublesome object to test safe handling."""
    def __repr__(self):
        raise ValueError("I refuse to be printed")


def add_numbers(a, b):
    result = a + b
    return result


def divide_numbers(a, b):
    result = a / b
    return result


def sample_program():
    total = add_numbers(2, 3)

    try:
        divide_numbers(total, 0)
    except ZeroDivisionError:
        pass

    tricky_value = Unprintable()  # should not crash the tracer

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