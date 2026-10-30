import json
import sqlite3

from canon_manager.db import SCHEMA
from canon_manager.main import capture_turn_state, restore_turn_state
from canon_manager.timeline import fire_crossed_events, fire_due_events


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



def test_catch_up_records_old_approved_fixed_events_but_not_pending_or_conditions():
    conn = make_database()
    add_event(conn, "already-due", 1, 400)
    add_event(conn, "exact-now", 1, 480)
    add_event(conn, "future", 2, 0)
    add_event(conn, "pending-past", 1, 300, approval="pending")
    add_event(conn, "condition-past", 1, 200, activation="condition")

    caught = fire_due_events(conn, "s1", 1, 480)
    assert [item["stable_key"] for item in caught] == ["already-due", "exact-now"]
    rows = conn.execute(
        "SELECT fired_turn_id,due_day,due_minute,reached_day,reached_minute "
        "FROM session_timeline_runs ORDER BY due_day,due_minute"
    ).fetchall()
    assert [(row["fired_turn_id"], row["reached_day"], row["reached_minute"]) for row in rows] == [
        ("system:timeline-catch-up", 1, 480),
        ("system:timeline-catch-up", 1, 480),
    ]
    assert fire_due_events(conn, "s1", 1, 480) == []
    assert len(fire_due_events(conn, "s1", 2, 0)) == 1
    assert conn.execute("SELECT COUNT(*) FROM session_timeline_runs").fetchone()[0] == 3


def test_catch_up_isolated_per_session_and_idempotent_with_clock_crossing():
    conn = make_database()
    conn.execute(
        "INSERT INTO sessions(id,world_id,name,protagonist_entity_id) VALUES('s2','w1','Session 2','hero')"
    )
    add_event(conn, "due", 1, 470)
    assert len(fire_due_events(conn, "s1", 1, 480)) == 1
    assert len(fire_due_events(conn, "s1", 1, 480)) == 0
    assert len(fire_due_events(conn, "s2", 1, 480)) == 1
    assert fire_crossed_events(conn, "s1", "turn-later", 1, 470, 1, 500) == []
    assert conn.execute("SELECT COUNT(*) FROM session_timeline_runs WHERE session_id='s1'").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM session_timeline_runs WHERE session_id='s2'").fetchone()[0] == 1


def test_undo_restores_timeline_ledger_with_the_clock():
    conn = make_database()
    add_event(conn, "undoable", 1, 500)
    before = capture_turn_state(conn, "s1")
    conn.execute("UPDATE sessions SET minute_of_day=510 WHERE id='s1'")
    fired = fire_crossed_events(conn, "s1", "turn-to-undo", 1, 480, 1, 510)
    assert len(fired) == 1
    assert conn.execute("SELECT COUNT(*) FROM session_timeline_runs WHERE session_id='s1'").fetchone()[0] == 1

    restore_turn_state(conn, "s1", before)
    current = conn.execute(
        "SELECT day,minute_of_day FROM sessions WHERE id='s1'"
    ).fetchone()
    assert (current["day"], current["minute_of_day"]) == (1, 480)
    assert conn.execute("SELECT COUNT(*) FROM session_timeline_runs WHERE session_id='s1'").fetchone()[0] == 0
