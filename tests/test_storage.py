import sqlite3

import pytest

from pychronicle.storage import TraceStore


def test_trace_store_records_and_reconstructs_state():
    store = TraceStore()

    frame_id = store.record(
        line_number=10,
        event="assign",
        scope="<module>",
        values={"x": 100},
    )

    assert frame_id is not None
    assert store.frame_count() == 1

    state = store.state_at(frame_id, "<module>")

    assert state["x"] == 100

    store.close()


def test_trace_store_reconstructs_deleted_variable():
    store = TraceStore()

    first_frame = store.record(
        line_number=10,
        event="assign",
        scope="<module>",
        values={"x": 100, "y": 200},
    )

    second_frame = store.record(
        line_number=11,
        event="delete",
        scope="<module>",
        values={"x": 100},
    )

    assert first_frame is not None
    assert second_frame is not None

    state = store.state_at(second_frame, "<module>")

    assert state["x"] == 100
    assert "y" not in state

    delete_changes = [
        change
        for change in store.changes_for("y")
        if change["operation"] == "delete"
    ]

    assert len(delete_changes) == 1

    store.close()


def test_trace_store_enforces_foreign_keys():
    store = TraceStore()

    try:
        with pytest.raises(sqlite3.IntegrityError):
            store.connection.execute(
                """
                INSERT INTO changes (
                    frame_id,
                    scope,
                    variable_name,
                    value_json,
                    operation
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (999, "<module>", "x", "100", "set"),
            )
    finally:
        store.close()