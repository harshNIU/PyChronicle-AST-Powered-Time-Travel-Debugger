import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, "..", "tracer"))

from timeline_store import TimelineStore


def make_db(tmp_path):
    db_path = str(tmp_path / "timeline.db")
    store = TimelineStore(db_path)
    store.save_history([
        {"type": "line", "function": "running_total", "depth": 1, "line": 3, "source": "total = 0", "changed": {"total": 0}},
        {"type": "line", "function": "running_total", "depth": 1, "line": 5, "source": "total += n", "changed": {"total": 1, "n": 1}},
        {"type": "line", "function": "running_total", "depth": 1, "line": 5, "source": "total += n", "changed": {"total": 3, "n": 2}},
        {"type": "call", "function": "running_total", "depth": 1, "line": 1, "source": "def running_total(numbers):"},
    ])
    store.close()
    return db_path


def test_get_variable_history_returns_ordered_changes(tmp_path):
    store = TimelineStore(make_db(tmp_path))
    history = store.get_variable_history("total")
    store.close()

    assert len(history) == 3
    assert [entry["value"] for entry in history] == ["0", "1", "3"]


def test_get_variable_history_ignores_other_variables(tmp_path):
    store = TimelineStore(make_db(tmp_path))
    history = store.get_variable_history("n")
    store.close()

    assert len(history) == 2
    assert all(entry["function_name"] == "running_total" for entry in history)


def test_get_variable_history_returns_empty_for_unknown_variable(tmp_path):
    store = TimelineStore(make_db(tmp_path))
    history = store.get_variable_history("does_not_exist")
    store.close()

    assert history == []