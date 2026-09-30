import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, "..", "tracer"))

from timeline_store import TimelineStore
from query_timeline import main


def make_db(tmp_path):
    db_path = str(tmp_path / "timeline.db")
    store = TimelineStore(db_path)
    store.save_history([
        {"type": "call", "function": "add", "depth": 1, "line": 2, "source": "def add(a, b):"},
        {"type": "line", "function": "add", "depth": 1, "line": 3, "source": "result = a + b", "changed": {"result": 5}},
        {"type": "return", "function": "add", "depth": 1, "line": 4, "source": "return result", "value": 5},
        {
            "type": "exception", "function": "divide", "depth": 1, "line": 8,
            "source": "return a / b",
            "exception_type": "ZeroDivisionError",
            "exception_message": "division by zero",
        },
    ])
    store.close()
    return db_path


def test_query_missing_db_returns_error_code(tmp_path):
    missing_db = str(tmp_path / "nope.db")

    exit_code = main(["--db", missing_db])

    assert exit_code == 2


def test_query_by_function_filters_rows(tmp_path, capsys):
    db_path = make_db(tmp_path)

    exit_code = main(["--db", db_path, "--function", "add"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "add" in output
    assert "divide" not in output


def test_query_exceptions_flag(tmp_path, capsys):
    db_path = make_db(tmp_path)

    exit_code = main(["--db", db_path, "--exceptions"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "ZeroDivisionError" in output


def test_query_summary_flag(tmp_path, capsys):
    db_path = make_db(tmp_path)

    exit_code = main(["--db", db_path, "--summary"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Total steps in database: 4" in output
    assert "add: 1" in output
    assert "Exceptions: 1" in output