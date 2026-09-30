import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, "..", "tracer"))

from basic_tracer import ExecutionTracer


def add(a, b):
    result = a + b
    return result


def long_loop():
    total = 0
    for i in range(5000):
        total += i
    return total


def will_fail():
    return 1 / 0


def run_traced(func, *args, max_steps=None):
    tracer = ExecutionTracer(target_file=__file__, max_steps=max_steps)
    tracer.start()
    try:
        func(*args)
    except Exception:
        pass
    tracer.stop()
    return tracer


def test_line_steps_capture_source_text():
    tracer = run_traced(add, 2, 3)

    line_steps = [s for s in tracer.history if s["type"] == "line"]
    assert len(line_steps) > 0
    assert any("result" in s["source"] for s in line_steps)


def test_max_steps_truncates_long_runs():
    tracer = run_traced(long_loop, max_steps=20)

    assert tracer.truncated is True
    assert len(tracer.history) <= 20


def test_no_max_steps_means_no_truncation():
    tracer = run_traced(add, 2, 3)

    assert tracer.truncated is False


def test_build_summary_counts_function_calls():
    def helper():
        return add(1, 1)

    tracer = run_traced(helper)
    summary = tracer.build_summary()

    assert summary["function_calls"].get("add") == 1
    assert summary["function_calls"].get("helper") == 1
    assert summary["truncated"] is False


def test_build_summary_lists_exceptions():
    tracer = run_traced(will_fail)
    summary = tracer.build_summary()

    assert len(summary["exceptions"]) == 1
    assert summary["exceptions"][0]["type"] == "ZeroDivisionError"
