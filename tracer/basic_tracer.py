import sys


def safe_repr(value, max_length=200):
    """
    Safely convert any value to a string representation.

    Some objects raise exceptions from __repr__ (see the Unprintable
    class below), so this guards against crashing just because one
    traced value couldn't be printed.
    """
    try:
        text = repr(value)
    except Exception as e:
        return f"<unrepresentable {type(value).__name__}: {e}>"

    if len(text) > max_length:
        return text[:max_length] + f"...<truncated, {len(text)} chars total>"

    return text


def format_changes(changed_vars):
    return {key: safe_repr(value) for key, value in changed_vars.items()}


class ExecutionTracer:
    """
    Tracks execution history using sys.settrace.

    Day 8 improvements:
    - Safely handles values that raise exceptions when compared
      (some custom objects have __eq__ methods that raise instead
      of returning True/False)
    """

    def __init__(self, target_file=None):
        self.target_file = target_file
        self.history = []
        self._last_locals = {}
        self.call_stack = []

    def _get_changes(self, current_locals):
        changes = {}
        for key, value in current_locals.items():
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