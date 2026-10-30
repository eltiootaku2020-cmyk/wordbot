import json
import sqlite3

from canon_manager.db import SCHEMA
from canon_manager.timeline import fire_crossed_events


def make_database():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.execute("INSERT INTO worlds(id,name) VALUES('w1','World')")
    conn.execute(
        "INSERT INTO sessions(id,world_id,name,protagonist_entity_id) VALUES('s1','w1','Session','hero')"
    )
    return conn


def add_event(conn, key, day, minute, *, approval="approved", activation="fixed_time"):
    conn.execute(
        "INSERT INTO world_timeline_events "
        "(id,world_id,stable_key,title,description,activation_type,scheduled_day,"
        "scheduled_minute,condition_json,approval_status) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (key, "w1", key, key, f"Description {key}", activation,
         day if activation == "fixed_time" else None,
         minute if activation == "fixed_time" else None, "{}", approval),
    )


def test_event_fires_when_clock_crosses_day_boundary():
    conn = make_database()
    add_event(conn, "day-five", 5, 15)
    fired = fire_crossed_events(conn, "s1", "turn-1", 4, 1430, 5, 30)
    assert [item["stable_key"] for item in fired] == ["day-five"]
    row = conn.execute("SELECT * FROM session_timeline_runs").fetchone()
    assert row["due_day"] == 5
    assert row["due_minute"] == 15
    assert row["reached_day"] == 5
    assert row["reached_minute"] == 30


def test_jump_records_every_crossed_event_in_chronological_order():
    conn = make_database()
    add_event(conn, "first", 5, 10)
    add_event(conn, "second", 6, 700)
    add_event(conn, "third", 7, 0)
    fired = fire_crossed_events(conn, "s1", "turn-jump", 4, 1200, 7, 30)
    assert [item["stable_key"] for item in fired] == ["first", "second", "third"]


def test_retries_do_not_duplicate_world_event_execution():
    conn = make_database()
    add_event(conn, "once", 5, 10)
    first = fire_crossed_events(conn, "s1", "turn-1", 4, 1200, 5, 20)
    retry = fire_crossed_events(conn, "s1", "turn-1", 4, 1200, 5, 20)
    assert len(first) == 1
    assert retry == []
    assert conn.execute("SELECT COUNT(*) FROM session_timeline_runs").fetchone()[0] == 1


def test_pending_and_condition_events_never_fire_automatically():
    conn = make_database()
    add_event(conn, "needs-approval", 5, 10, approval="pending")
    add_event(conn, "condition", 5, 10, activation="condition")
    assert fire_crossed_events(conn, "s1", "turn-1", 4, 1200, 5, 20) == []
    assert conn.execute("SELECT COUNT(*) FROM session_timeline_runs").fetchone()[0] == 0


def test_timeline_isolated_per_session_and_rejects_clock_regression():
    conn = make_database()
    conn.execute(
        "INSERT INTO sessions(id,world_id,name,protagonist_entity_id) VALUES('s2','w1','Session 2','hero')"
    )
    add_event(conn, "once", 5, 10)
    assert len(fire_crossed_events(conn, "s1", "turn-1", 4, 1200, 5, 20)) == 1
    assert len(fire_crossed_events(conn, "s2", "turn-1", 4, 1200, 5, 20)) == 1
    try:
        fire_crossed_events(conn, "s1", "turn-back", 5, 20, 4, 1200)
    except ValueError as exc:
        assert "backwards" in str(exc)
    else:
        raise AssertionError("backwards time movement must be rejected")
