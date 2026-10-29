from pathlib import Path

import pytest

from canon_manager.db import Database
from canon_manager.timeline import absolute_minute, fire_due_world_events


def make_world_session(tmp_path: Path):
    database = Database(str(tmp_path / "timeline.sqlite3"))
    database.initialize()
    with database.transaction() as conn:
        conn.execute("INSERT INTO worlds(id,name) VALUES('world-a','Mundo A')")
        conn.execute(
            "INSERT INTO entities(id,world_id,name,kind) VALUES('hero','world-a','Protagonista','protagonist')"
        )
        conn.execute(
            "INSERT INTO sessions(id,world_id,name,day,minute_of_day,current_location,protagonist_entity_id) "
            "VALUES('session-a','world-a','Partida',1,480,'Bosque','hero')"
        )
    return database


def add_event(conn, event_id, uid, day, minute, *, status="confirmed", enabled=1, location="Ciudad lejana"):
    conn.execute(
        "INSERT INTO world_timeline_events(id,world_id,external_uid,title,description,"
        "scheduled_day,scheduled_minute,location,canon_status,enabled) "
        "VALUES(?,?,?,?,?,?,?,?,?,?)",
        (event_id, "world-a", uid, f"Suceso {uid}", f"Descripción {uid}", day, minute,
         location, status, enabled),
    )


def test_fixed_events_fire_in_order_even_when_the_protagonist_is_elsewhere(tmp_path):
    database = make_world_session(tmp_path)
    with database.transaction() as conn:
        add_event(conn, "later", "later", 2, 0)
        add_event(conn, "first", "first", 1, 481)
        add_event(conn, "middle", "middle", 1, 900)

        assert fire_due_world_events(conn, "session-a", 480, 480) == []
        fired = fire_due_world_events(conn, "session-a", 480, 1440)

        assert [item["external_uid"] for item in fired] == ["first", "middle", "later"]
        assert all(item["location"] == "Ciudad lejana" for item in fired)
        assert [item["fired_day"] for item in fired] == [1, 1, 2]
        assert [item["fired_minute"] for item in fired] == [481, 900, 0]

        # A retry/replay cannot fire the same world event twice.
        assert fire_due_world_events(conn, "session-a", 480, 1440) == []
        assert conn.execute(
            "SELECT COUNT(*) FROM session_timeline_events WHERE session_id='session-a'"
        ).fetchone()[0] == 3


def test_pending_disabled_and_future_events_do_not_fire(tmp_path):
    database = make_world_session(tmp_path)
    with database.transaction() as conn:
        add_event(conn, "approved", "approved", 1, 481)
        add_event(conn, "pending", "pending", 1, 482, status="pending")
        add_event(conn, "disabled", "disabled", 1, 483, enabled=0)
        add_event(conn, "future", "future", 3, 0)

        fired = fire_due_world_events(conn, "session-a", 480, 1440)

        assert [item["external_uid"] for item in fired] == ["approved"]


def test_world_clock_cannot_move_backwards():
    assert absolute_minute(2, 0) == 1440
    with pytest.raises(ValueError, match="fecha"):
        absolute_minute(0, 0)
    with pytest.raises(ValueError, match="retroceder"):
        fire_due_world_events(None, "missing", 100, 99)


def test_each_session_gets_its_own_firing_record(tmp_path):
    database = make_world_session(tmp_path)
    with database.transaction() as conn:
        add_event(conn, "event-a", "event-a", 1, 481)
        conn.execute(
            "INSERT INTO sessions(id,world_id,name,day,minute_of_day,current_location,protagonist_entity_id) "
            "VALUES('session-b','world-a','Otra partida',1,480,'Puerto','hero')"
        )
        first = fire_due_world_events(conn, "session-a", 480, 481)
        second = fire_due_world_events(conn, "session-b", 480, 481)
        assert len(first) == len(second) == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM session_timeline_events WHERE world_event_id='event-a'"
        ).fetchone()[0] == 2
