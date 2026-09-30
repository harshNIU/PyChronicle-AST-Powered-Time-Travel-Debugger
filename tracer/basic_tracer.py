"""
Execution tracer for PyChronicle.

Uses sys.settrace to record what happens while Python code runs:
function calls, line-by-line variable changes, returns and exceptions.
The recorded history is a list of dicts (one per event) which can be
printed with print_timeline(), summarized with print_summary(), or
saved with TimelineStore (see timeline_store.py).

To trace any Python file from the command line, use run_tracer.py.
To inspect an already-saved timeline, use query_timeline.py.

Day 12-15 improvements:
- Each recorded step now includes the literal source text of that
  line, read with linecache, so the timeline reads like an annotated
  transcript instead of bare line numbers
- ExecutionTracer(max_steps=N) stops recording (without crashing)
  once N steps have been captured, so tracing a long-running or
  accidentally-infinite program doesn't hang or blow up memory
- build_summary() / print_summary() aggregate a run into per-function
  call counts and a list of exceptions raised
"""

import linecache
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
    "return" or "exception", plus the function name, call depth, line
    number and the source text of that line. Line steps also hold the
    variables that changed, return steps hold the returned value, and
    exception steps hold the exception type and message.

    Usage:
        tracer = ExecutionTracer(target_file=__file__, max_steps=5000)
        tracer.start()
        ...code to trace...
        tracer.stop()
        tracer.print_timeline()
        tracer.print_summary()
    """

    def __init__(self, target_file=None, max_steps=None):
        """
        target_file: only code from this file is traced. If None,
        code from every file is traced.

        max_steps: stop recording once this many steps have been
        captured. Useful for long loops or programs that might run
        forever; tracing itself is turned off once the limit is hit,
        so the traced program keeps running normally, just unrecorded.
        If None, there is no limit.
        """
        self.target_file = target_file
        self.max_steps = max_steps
        self.history = []
        self._last_locals = {}
        self.call_stack = []
        self.truncated = False

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

    def _source_line(self, filename, lineno):
        """Return the stripped source text at filename:lineno, or "" if unavailable."""
        text = linecache.getline(filename, lineno)
        return text.strip() if text else ""

    def trace_calls(self, frame, event, arg):
        """
        Callback given to sys.settrace. Python calls it on every
        call / line / return / exception event, and each one is appended
        to self.history as a dict, until max_steps is reached.
        """
        if self.truncated:
            return None

        if self.target_file and frame.f_code.co_filename != self.target_file:
            return None

        if self.max_steps is not None and len(self.history) >= self.max_steps:
            self.truncated = True
            self.stop()
            return None

        func_name = frame.f_code.co_name
        filename = frame.f_code.co_filename
        source = self._source_line(filename, frame.f_lineno)

        if event == "call":
            self.call_stack.append(func_name)
            self.history.append({
                "type": "call",
                "function": func_name,
                "depth": len(self.call_stack),
                "line": frame.f_lineno,
                "source": source,
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
                    "source": source,
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
                "source": source,
                "exception_type": exc_type.__name__,
                "exception_message": str(exc_value),
            })

        elif event == "return":
            self.history.append({
                "type": "return",
                "function": func_name,
                "depth": len(self.call_stack),
                "line": frame.f_lineno,
                "source": source,
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

    def build_summary(self):
        """
        Aggregate self.history into a dict:
            total_steps, function_calls ({name: count}),
            exceptions (list of {function, line, type, message}), truncated
        """
        function_calls = {}
        exceptions = []

        for step in self.history:
            if step["type"] == "call":
                function_calls[step["function"]] = function_calls.get(step["function"], 0) + 1
            elif step["type"] == "exception":
                exceptions.append({
                    "function": step["function"],
                    "line": step["line"],
                    "type": step["exception_type"],
                    "message": step["exception_message"],
                })

        return {
            "total_steps": len(self.history),
            "function_calls": function_calls,
            "exceptions": exceptions,
            "truncated": self.truncated,
        }

    def print_timeline(self):
        """Print the recorded history, indented by call depth."""
        print("\n--- Execution Timeline (with call stack) ---")
        for i, step in enumerate(self.history):
            indent = "    " * max(step["depth"] - 1, 0)
            source = f"  # {step['source']}" if step.get("source") else ""

            if step["type"] == "call":
                print(f"[{i}] {indent}-> Entering {step['function']}() at line {step['line']}{source}")
            elif step["type"] == "return":
                print(f"[{i}] {indent}<- Exiting {step['function']}() at line {step['line']} -> returned {safe_repr(step['value'])}{source}")
            elif step["type"] == "exception":
                print(f"[{i}] {indent}!! Exception in {step['function']}() at line {step['line']}: "
                      f"{step['exception_type']}: {step['exception_message']}{source}")
            else:
                print(f"[{i}] {indent}Line {step['line']} ({step['function']}){source} | Changed: {format_changes(step['changed'])}")

        if self.truncated:
            print(f"\n(recording stopped early: reached the {self.max_steps}-step limit)")

    def print_summary(self):
        """Print the aggregate summary from build_summary()."""
        summary = self.build_summary()

        print("\n--- Summary ---")
        print(f"Total steps recorded: {summary['total_steps']}")
        if summary["truncated"]:
            print(f"(recording stopped early at the {self.max_steps}-step limit)")

        print("Function calls:")
        if summary["function_calls"]:
            for name, count in summary["function_calls"].items():
                print(f"  {name}: {count}")
        else:
            print("  (none)")

        print("Exceptions:")
        if summary["exceptions"]:
            for exc in summary["exceptions"]:
                print(f"  {exc['type']} in {exc['function']}() at line {exc['line']}: {exc['message']}")
        else:
            print("  (none)")


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


def running_total(numbers):
    total = 0
    for n in numbers:
        total += n
    return total


def sample_program():
    total = add_numbers(2, 3)

    try:
        divide_numbers(total, 0)
    except ZeroDivisionError:
        pass

    tricky_value = Unprintable()  # should not crash the tracer

    running_total([1, 2, 3, 4, 5])

    return total


if __name__ == "__main__":
    from timeline_store import TimelineStore

    tracer = ExecutionTracer(target_file=__file__, max_steps=500)
    tracer.start()

    sample_program()

    tracer.stop()
    tracer.print_timeline()
    tracer.print_summary()

    store = TimelineStore()
    store.clear()
    store.save_history(tracer.history)
    store.close()

    print("\nSaved to timeline.db. Try:")
    print("  python3 tracer/query_timeline.py --function add_numbers")
    print("  python3 tracer/query_timeline.py --summary")