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


