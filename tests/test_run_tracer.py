import os
import sys

import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, "..", "tracer"))

from basic_tracer import ExecutionTracer
from run_tracer import trace_script, main
from timeline_store import TimelineStore

GOOD_SCRIPT = "def double(x):\n    y = x * 2\n    return y\n\ndouble(4)\n"
FAILING_SCRIPT = "def boom():\n    return 1 / 0\n\nboom()\n"


def write_script(tmp_path, body):
    path = tmp_path / "demo_script.py"
    path.write_text(body)
    return str(path)


def test_trace_script_records_function_calls(tmp_path):
    script = write_script(tmp_path, GOOD_SCRIPT)

    tracer, error = trace_script(script, db_path=str(tmp_path / "timeline.db"))

    assert error is None
    assert any(s["type"] == "call" and s["function"] == "double" for s in tracer.history)
    assert any(
        s["type"] == "return" and s["function"] == "double" and s["value"] == 8
        for s in tracer.history
    )


def test_trace_script_saves_timeline_to_db(tmp_path):
    script = write_script(tmp_path, GOOD_SCRIPT)
    db_path = str(tmp_path / "timeline.db")

    tracer, _ = trace_script(script, db_path=db_path)

    store = TimelineStore(db_path)
    rows = store.load_history()
    store.close()

    assert len(rows) == len(tracer.history)
    assert len(rows) > 0


def test_trace_script_captures_uncaught_error(tmp_path):
    script = write_script(tmp_path, FAILING_SCRIPT)

    tracer, error = trace_script(script, db_path=str(tmp_path / "timeline.db"))

    assert isinstance(error, ZeroDivisionError)
    assert any(s["type"] == "exception" for s in tracer.history)


def test_trace_script_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        trace_script(str(tmp_path / "nope.py"), db_path=str(tmp_path / "timeline.db"))


def test_main_exit_codes(tmp_path):
    db = str(tmp_path / "timeline.db")
    good = write_script(tmp_path, GOOD_SCRIPT)

    assert main([good, "--db", db, "--quiet"]) == 0

    failing = tmp_path / "failing_script.py"
    failing.write_text(FAILING_SCRIPT)
    assert main([str(failing), "--db", db, "--quiet"]) == 1

    assert main([str(tmp_path / "missing.py"), "--db", db]) == 2


def test_get_changes_ignores_dunder_names():
    tracer = ExecutionTracer()

    changes = tracer._get_changes({"__name__": "__main__", "x": 1})

    assert changes == {"x": 1}