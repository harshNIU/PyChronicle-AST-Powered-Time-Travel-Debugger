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


def test_multiple_events_are_stored_in_order():
    init_db()
    clear_events()

    save_event(
        timestamp=1.0,
        line_number=10,
        variable_name="x",
        serialized_value="100",
    )

    save_event(
        timestamp=2.0,
        line_number=11,
        variable_name="y",
        serialized_value="200",
    )

    save_event(
        timestamp=3.0,
        line_number=12,
        variable_name="x",
        serialized_value="150",
    )

    events = get_events()

    assert len(events) == 3
    assert events[0][1] == 1.0
    assert events[1][1] == 2.0
    assert events[2][1] == 3.0

    assert events[0][3] == "x"
    assert events[1][3] == "y"
    assert events[2][3] == "x"

    clear_events()


def test_init_db_can_be_called_multiple_times():
    init_db()
    init_db()

    events = get_events()

    assert isinstance(events, list)

def test_clear_events_removes_all_events():
    init_db()
    clear_events()

    save_event(
        timestamp=1.0,
        line_number=10,
        variable_name="x",
        serialized_value="100",
    )

    save_event(
        timestamp=2.0,
        line_number=11,
        variable_name="y",
        serialized_value="200",
    )

    assert len(get_events()) == 2

    clear_events()

    assert get_events() == []    