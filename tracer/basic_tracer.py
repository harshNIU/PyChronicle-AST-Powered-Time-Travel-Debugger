import sys


class ExecutionTracer:
    """
    A basic execution tracer using sys.settrace.

    Records every line executed along with local variable state
    at that point, so we can eventually browse a 'timeline'
    of how the program's state changed over time.
    """

    def __init__(self):
        self.history = []

    def trace_calls(self, frame, event, arg):
        if event == "line":
            self.history.append({
                "file": frame.f_code.co_filename,
                "line": frame.f_lineno,
                "locals": frame.f_locals.copy(),
            })
        return self.trace_calls

    def start(self):
        sys.settrace(self.trace_calls)

    def stop(self):
        sys.settrace(None)

    def print_timeline(self):
        print("\n--- Execution Timeline ---")
        for i, step in enumerate(self.history):
            print(f"[{i}] Line {step['line']} | Locals: {step['locals']}")


def sample_program():
    total = 0
    for i in range(3):
        total += i
    return total


if __name__ == "__main__":
    tracer = ExecutionTracer()
    tracer.start()

    sample_program()

    tracer.stop()
    tracer.print_timeline()