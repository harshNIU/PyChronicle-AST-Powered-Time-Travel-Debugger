from pychronicle.engine import Chronicle
from pychronicle.instrumentation import find_assignments


def test_assignment_analysis_finds_loop_and_augmented_values():
    found = find_assignments("total = 0\nfor item in range(3):\n    total += item\n")
    assert [(entry.kind, entry.names) for entry in found] == [
        ("assign", ("total",)), ("loop", ("item",)), ("augmented", ("total",))
    ]


def test_delta_trace_replays_loop_history():
    result = Chronicle().run_source("total = 0\nfor item in range(4):\n    total += item\n", "loop_example.py")
    frames = list(result.store.frames())
    assert result.store.frame_count() >= 5
    final_state = result.store.state_at(frames[-1].id, "<module>")
    assert final_state["total"] == 6
    assert len(result.store.changes_for("total")) == 4


def test_function_scope_tracing():
    code = """
def compute(x):
    y = x * 2
    return y

res = compute(5)
"""
    result = Chronicle().run_source(code, "func_example.py")
    frames = list(result.store.frames())
    assert result.store.frame_count() > 0
    # Search for frames with compute scope
    func_frames = [f for f in frames if f.scope.startswith("compute")]
    assert len(func_frames) > 0
    func_state = result.store.state_at(func_frames[-1].id, "compute")
    assert func_state["x"] == 5
    assert func_state["y"] == 10


def test_file_persistence_and_store_reopen(tmp_path):
    db_file = tmp_path / "trace.sqlite"
    chronicle = Chronicle(database=db_file)
    chronicle.run_source("a = 10\na += 5\n", "test.py")
    chronicle.store.close()

    # Re-open TraceStore from file
    from pychronicle.storage import TraceStore
    reopened = TraceStore(db_file)
    assert reopened.frame_count() > 0
    last_frame = list(reopened.frames())[-1]
    state = reopened.state_at(last_frame.id, "<module>")
    assert state["a"] == 15
    reopened.close()


def test_tui_launch_import_and_setup(monkeypatch):
    from unittest.mock import MagicMock
    import pychronicle.tui as tui_module
    from pychronicle.engine import Chronicle
    from pathlib import Path

    result = Chronicle().run_source("a = 1", "test.py")

    # Mock App.run so it doesn't open interactive TUI terminal during test suite execution
    mock_run = MagicMock()
    monkeypatch.setattr("textual.app.App.run", mock_run)

    tui_module.launch(result.store, Path("test.py"))
    assert mock_run.called
def test_execution_history_records_variable_changes():
    code = """
x = 10
x = 20
x = 30
"""

    result = Chronicle().run_source(code, "history_example.py")

    frames = list(result.store.frames())

    assert len(frames) > 0

    states = [
        result.store.state_at(frame.id, "<module>")
        for frame in frames
    ]

    assert any(state.get("x") == 10 for state in states)
    assert any(state.get("x") == 20 for state in states)
    assert any(state.get("x") == 30 for state in states)


# ---------------------------------------------------------
# Day 19 - Cross-module smoke test: recursion
# ---------------------------------------------------------


def test_recursive_function_tracing():
    """The full pipeline should capture recursive function execution."""

    code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(4)
"""

    result = Chronicle().run_source(
        code,
        "recursive_example.py",
    )

    frames = list(result.store.frames())

    assert result.store.frame_count() > 0

    factorial_frames = [
        frame
        for frame in frames
        if frame.scope.startswith("factorial")
    ]

    assert len(factorial_frames) >= 4

    factorial_values = []

    for frame in factorial_frames:
        state = result.store.state_at(
            frame.id,
            "factorial",
        )

        if "n" in state:
            factorial_values.append(state["n"])

    assert 4 in factorial_values
    assert 3 in factorial_values
    assert 2 in factorial_values
    assert 1 in factorial_values


# ---------------------------------------------------------
# Day 19 - Cross-module smoke test: class methods
# ---------------------------------------------------------


def test_class_method_tracing():
    """The full pipeline should capture execution inside a class method."""

    code = """
class Calculator:
    def double(self, value):
        result = value * 2
        return result

calculator = Calculator()
answer = calculator.double(5)
"""

    result = Chronicle().run_source(
        code,
        "class_method_example.py",
    )

    frames = list(result.store.frames())

    assert result.store.frame_count() > 0

    method_frames = [
        frame
        for frame in frames
        if frame.scope.startswith("double")
    ]

    assert len(method_frames) > 0

    method_states = [
        result.store.state_at(
            frame.id,
            "double",
        )
        for frame in method_frames
    ]

    assert any(
        state.get("value") == 5
        for state in method_states
    )

    assert any(
        state.get("result") == 10
        for state in method_states
    )
