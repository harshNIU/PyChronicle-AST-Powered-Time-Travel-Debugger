from storage.db import (
    init_db,
    save_event,
    get_events,
    clear_events,
)


def test_save_and_get_event():
    init_db()
    clear_events()

    save_event(
        timestamp=1.0,
        line_number=10,
        variable_name="x",
        serialized_value="100",
    )

    events = get_events()

    assert len(events) == 1
    assert events[0][2] == 10
    assert events[0][3] == "x"
    assert events[0][4] == "100"

    clear_events()