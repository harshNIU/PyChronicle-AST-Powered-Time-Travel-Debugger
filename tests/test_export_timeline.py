import json
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, "..", "tracer"))

from timeline_store import TimelineStore
from export_timeline import main


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


def test_export_missing_db_returns_error_code(tmp_path):
    missing_db = str(tmp_path / "nope.db")

    exit_code = main(["--db", missing_db])

    assert exit_code == 2


def test_export_writes_valid_json_to_file(tmp_path, capsys):
    db_path = make_db(tmp_path)
    out_path = str(tmp_path / "export.json")

    exit_code = main(["--db", db_path, "--out", out_path])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Wrote 4 steps" in output

    with open(out_path) as f:
        data = json.load(f)

    assert len(data) == 4
    assert data[0]["event_type"] == "call"


def test_export_filters_by_function(tmp_path, capsys):
    db_path = make_db(tmp_path)

    main(["--db", db_path, "--function", "add"])
    data = json.loads(capsys.readouterr().out)

    assert len(data) == 3
    assert all(step["function_name"] == "add" for step in data)


def test_export_parses_changed_vars_into_real_dict(tmp_path, capsys):
    db_path = make_db(tmp_path)

    main(["--db", db_path, "--function", "add"])
    data = json.loads(capsys.readouterr().out)

    line_step = next(step for step in data if step["event_type"] == "line")
    assert isinstance(line_step["changed_vars"], dict)
    assert line_step["changed_vars"]["result"] == "5"


def test_export_pretty_flag_changes_formatting(tmp_path, capsys):
    db_path = make_db(tmp_path)

    main(["--db", db_path])
    compact_output = capsys.readouterr().out

    main(["--db", db_path, "--pretty"])
    pretty_output = capsys.readouterr().out

    assert "\n" not in compact_output.strip()
    assert "\n" in pretty_output