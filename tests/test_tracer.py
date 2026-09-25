import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TRACER_DIR = os.path.join(CURRENT_DIR, "..", "tracer")
sys.path.insert(0, TRACER_DIR)

from basic_tracer import ExecutionTracer, safe_repr, format_changes, Unprintable
from timeline_store import TimelineStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def add(a, b):
    result = a + b
    return result


def divide(a, b):
    result = a / b
    return result


def run_traced(func, *args):
    """Trace a call to func(*args) and return the tracer's recorded history."""
    tracer = ExecutionTracer(target_file=__file__)
    tracer.start()
    func(*args)
    tracer.stop()
    return tracer.history


# ---------------------------------------------------------------------------
# ExecutionTracer
# ---------------------------------------------------------------------------

def test_tracer_records_line_changes():
    history = run_traced(add, 2, 3)

    line_events = [step for step in history if step["type"] == "line"]
    assert len(line_events) > 0

    all_changes = {}
    for step in line_events:
        all_changes.update(step["changed"])

    assert all_changes.get("result") == 5


def test_tracer_records_call_and_return_events():
    history = run_traced(add, 2, 3)

    call_events = [step for step in history if step["type"] == "call"]
    return_events = [step for step in history if step["type"] == "return"]

    assert any(step["function"] == "add" for step in call_events)
    assert any(step["function"] == "add" and step["value"] == 5 for step in return_events)


def test_tracer_tracks_nested_call_depth():
    def wrapper():
        return add(1, 1)

    history = run_traced(wrapper)

    wrapper_call = next(step for step in history if step["type"] == "call" and step["function"] == "wrapper")
    add_call = next(step for step in history if step["type"] == "call" and step["function"] == "add")

    assert add_call["depth"] > wrapper_call["depth"]


def test_tracer_records_exceptions():
    def will_fail():
        try:
            divide(1, 0)
        except ZeroDivisionError:
            pass

    history = run_traced(will_fail)

    exception_events = [step for step in history if step["type"] == "exception"]
    assert len(exception_events) > 0
    assert exception_events[0]["exception_type"] == "ZeroDivisionError"


def test_get_changes_handles_uncomparable_values():
    class Unequal:
        def __eq__(self, other):
            raise RuntimeError("cannot compare")

    tracer = ExecutionTracer()

    first_changes = tracer._get_changes({"value": Unequal()})
    assert "value" in first_changes

    tracer._last_locals = {"value": Unequal()}

    # Comparing two Unequal instances raises; this should be treated
    # as "changed" instead of crashing the tracer.
    second_changes = tracer._get_changes({"value": Unequal()})
    assert "value" in second_changes


# ---------------------------------------------------------------------------
# safe_repr / format_changes
# ---------------------------------------------------------------------------

def test_safe_repr_handles_normal_values():
    assert safe_repr(42) == "42"
    assert safe_repr("hello") == "'hello'"


def test_safe_repr_handles_unprintable_objects():
    result = safe_repr(Unprintable())
    assert result.startswith("<unrepresentable")
    assert "Unprintable" in result


def test_safe_repr_truncates_long_values():
    long_string = "x" * 500
    result = safe_repr(long_string, max_length=50)

    assert result.endswith("total>")
    assert len(result) < len(repr(long_string))


def test_format_changes_handles_mixed_values():
    formatted = format_changes({"a": 1, "b": Unprintable()})

    assert formatted["a"] == "1"
    assert "<unrepresentable" in formatted["b"]


# ---------------------------------------------------------------------------
# TimelineStore
# ---------------------------------------------------------------------------

def test_timeline_store_saves_and_loads_line_events(tmp_path):
    store = TimelineStore(db_path=str(tmp_path / "timeline.db"))

    store.save_history([
        {"type": "line", "function": "add", "depth": 1, "line": 10, "changed": {"x": 1}},
    ])

    rows = store.load_history()
    store.close()

    assert len(rows) == 1
    assert rows[0][1] == "line"
    assert rows[0][2] == "add"
    assert "x" in rows[0][5]


def test_timeline_store_saves_call_and_return_events(tmp_path):
    store = TimelineStore(db_path=str(tmp_path / "timeline.db"))

    store.save_history([
        {"type": "call", "function": "add", "depth": 1, "line": 5},
        {"type": "return", "function": "add", "depth": 1, "line": 6, "value": 5},
    ])

    rows = store.load_history()
    store.close()

    assert rows[0][1] == "call"
    assert rows[1][1] == "return"
    assert rows[1][6] == "5"


def test_timeline_store_saves_exception_events(tmp_path):
    store = TimelineStore(db_path=str(tmp_path / "timeline.db"))

    store.save_history([{
        "type": "exception",
        "function": "divide",
        "depth": 1,
        "line": 7,
        "exception_type": "ZeroDivisionError",
        "exception_message": "division by zero",
    }])

    rows = store.load_history()
    store.close()

    assert rows[0][7] == "ZeroDivisionError"
    assert rows[0][8] == "division by zero"


def test_timeline_store_handles_unprintable_values_safely(tmp_path):
    store = TimelineStore(db_path=str(tmp_path / "timeline.db"))

    # Should not raise, even though Unprintable() fails on repr()
    store.save_history([
        {"type": "line", "function": "make_value", "depth": 1, "line": 12, "changed": {"tricky": Unprintable()}},
    ])

    rows = store.load_history()
    store.close()

    assert "<unrepresentable" in rows[0][5]


def test_timeline_store_clear_removes_all_rows(tmp_path):
    store = TimelineStore(db_path=str(tmp_path / "timeline.db"))

    store.save_history([{"type": "line", "function": "x", "depth": 1, "line": 1, "changed": {}}])
    assert len(store.load_history()) == 1

    store.clear()
    assert len(store.load_history()) == 0

    store.close()