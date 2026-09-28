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