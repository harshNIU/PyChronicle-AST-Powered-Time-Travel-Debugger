import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, "..", "tracer"))

from timeline_store import TimelineStore
from compare_timelines import compare, main

OLD_HISTORY = [
    {"type": "call", "function": "add", "depth": 1, "line": 2, "source": "def add(a, b):"},
    {"type": "call", "function": "add", "depth": 1, "line": 2, "source": "def add(a, b):"},
]

NEW_HISTORY_WITH_EXTRA_CALL = OLD_HISTORY + [
    {"type": "call", "function": "add", "depth": 1, "line": 2, "source": "def add(a, b):"},
]

NEW_HISTORY_WITH_NEW_EXCEPTION = OLD_HISTORY + [
    {
        "type": "exception", "function": "divide", "depth": 1, "line": 8,
        "source": "return a / b",
        "exception_type": "ZeroDivisionError",
        "exception_message": "division by zero",
    },
]


def make_db(tmp_path, name, history):
    db_path = str(tmp_path / name)
    store = TimelineStore(db_path)
    store.save_history(history)
    store.close()
    return db_path


def load_rows(db_path):
    store = TimelineStore(db_path)
    try:
        return store.load_history()
    finally:
        store.close()


def test_compare_detects_call_count_changes(tmp_path):
    old_rows = load_rows(make_db(tmp_path, "old.db", OLD_HISTORY))
    new_rows = load_rows(make_db(tmp_path, "new.db", NEW_HISTORY_WITH_EXTRA_CALL))

    result = compare(old_rows, new_rows)

    assert result["call_count_diffs"]["add"] == {"old": 2, "new": 3}


def test_compare_detects_new_exception(tmp_path):
    old_rows = load_rows(make_db(tmp_path, "old.db", OLD_HISTORY))
    new_rows = load_rows(make_db(tmp_path, "new.db", NEW_HISTORY_WITH_NEW_EXCEPTION))

    result = compare(old_rows, new_rows)

    assert len(result["new_exceptions_only"]) == 1
    assert result["new_exceptions_only"][0][2] == "ZeroDivisionError"


def test_compare_no_differences_when_identical(tmp_path):
    old_rows = load_rows(make_db(tmp_path, "old.db", OLD_HISTORY))
    new_rows = load_rows(make_db(tmp_path, "new.db", OLD_HISTORY))

    result = compare(old_rows, new_rows)

    assert result["call_count_diffs"] == {}
    assert result["new_exceptions_only"] == []
    assert result["resolved_exceptions"] == []


def test_main_missing_old_db_returns_error_code(tmp_path):
    new_db = make_db(tmp_path, "new.db", OLD_HISTORY)

    exit_code = main(["--old", str(tmp_path / "missing.db"), "--new", new_db])

    assert exit_code == 2


def test_main_runs_successfully_with_valid_dbs(tmp_path, capsys):
    old_db = make_db(tmp_path, "old.db", OLD_HISTORY)
    new_db = make_db(tmp_path, "new.db", NEW_HISTORY_WITH_EXTRA_CALL)

    exit_code = main(["--old", old_db, "--new", new_db])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "add: 2 -> 3" in output