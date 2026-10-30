import os
import tempfile
from pathlib import Path

import pytest

from canon_manager.db import Database
_TEST_MAIN_DB_DIR = tempfile.TemporaryDirectory(prefix="timeline-main-")
os.environ.setdefault("APP_DB_PATH", str(Path(_TEST_MAIN_DB_DIR.name) / "main.sqlite3"))

from canon_manager.timeline import absolute_minute, fire_due_world_events
from canon_manager.main import (
    apply_narrator_result, capture_turn_state, restore_turn_state, session_row
)
from canon_manager.models import NarratorResponse


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



def test_turn_clock_advance_automatically_fires_crossed_world_events(tmp_path):
    database = make_world_session(tmp_path)
    with database.transaction() as conn:
        add_event(conn, "before-midnight", "before-midnight", 1, 900)
        add_event(conn, "midnight", "midnight", 2, 0)
        add_event(conn, "after-midnight", "after-midnight", 2, 30)
        session = session_row(conn, "session-a")

        result = NarratorResponse(
            narration="El tiempo autorizado transcurre.",
            elapsed_minutes=0,
        )
        applied, pending = apply_narrator_result(
            conn, session, "turn-a", "message-a", "Avanzo hasta el día siguiente.",
            result, {"minutes": 990, "destination": ""},
        )

        assert pending == []
        assert [row["external_uid"] for row in conn.execute(
            "SELECT w.external_uid FROM session_timeline_events f "
            "JOIN world_timeline_events w ON w.id=f.world_event_id "
            "WHERE f.session_id=? ORDER BY f.scheduled_total_minutes",
            ("session-a",),
        ).fetchall()] == ["before-midnight", "midnight", "after-midnight"]
        assert sum("Suceso mundial activado" in item for item in applied) == 3
        clock = conn.execute(
            "SELECT day,minute_of_day FROM sessions WHERE id='session-a'"
        ).fetchone()
        assert (clock["day"], clock["minute_of_day"]) == (2, 30)



def test_undo_snapshot_restores_timeline_firing_ledger_and_allows_replay(tmp_path):
    database = make_world_session(tmp_path)
    with database.transaction() as conn:
        add_event(conn, "event-one", "event-one", 1, 481)
        add_event(conn, "event-two", "event-two", 1, 482)

        # The snapshot is taken before the turn that crosses the first event.
        before_turn = capture_turn_state(conn, "session-a")
        first = fire_due_world_events(conn, "session-a", 480, 481)
        assert [item["external_uid"] for item in first] == ["event-one"]

        # A later turn crosses the second event; undo must restore the earlier ledger.
        conn.execute(
            "UPDATE sessions SET day=1,minute_of_day=482 WHERE id='session-a'"
        )
        before_second_turn = capture_turn_state(conn, "session-a")
        second = fire_due_world_events(conn, "session-a", 481, 482)
        assert [item["external_uid"] for item in second] == ["event-two"]

        restore_turn_state(conn, "session-a", before_second_turn)
        current = conn.execute(
            "SELECT w.external_uid FROM session_timeline_events f "
            "JOIN world_timeline_events w ON w.id=f.world_event_id "
            "WHERE f.session_id=? ORDER BY f.scheduled_total_minutes",
            ("session-a",),
        ).fetchall()
        assert [row["external_uid"] for row in current] == ["event-one"]

        # Restoring the pre-first-turn snapshot clears that activation, so replay can fire it again.
        restore_turn_state(conn, "session-a", before_turn)
        replay = fire_due_world_events(conn, "session-a", 480, 481)
        assert [item["external_uid"] for item in replay] == ["event-one"]



def test_undo_restores_session_ledger_but_keeps_world_timeline_edits_and_creations(tmp_path):
    database = make_world_session(tmp_path)
    with database.transaction() as conn:
        add_event(conn, "event-one", "event-one", 1, 481)
        before_turn = capture_turn_state(conn, "session-a")

        # World chronology edits are authored outside the turn and must not be
        # rolled back with a session snapshot.
        conn.execute(
            "UPDATE world_timeline_events SET title=?,scheduled_minute=? WHERE id=?",
            ("Suceso corregido", 490, "event-one"),
        )
        add_event(conn, "event-two", "event-two", 1, 491)

        conn.execute(
            "UPDATE sessions SET day=1,minute_of_day=495 WHERE id='session-a'"
        )
        fired = fire_due_world_events(conn, "session-a", 480, 495)
        assert [item["external_uid"] for item in fired] == ["event-one", "event-two"]

        # Undo returns the per-session clock and activation ledger to the
        # snapshot, while preserving shared world-level definitions.
        restore_turn_state(conn, "session-a", before_turn)
        clock = conn.execute(
            "SELECT day,minute_of_day FROM sessions WHERE id='session-a'"
        ).fetchone()
        assert (clock["day"], clock["minute_of_day"]) == (1, 480)
        assert conn.execute(
            "SELECT COUNT(*) FROM session_timeline_events WHERE session_id='session-a'"
        ).fetchone()[0] == 0

        definitions = conn.execute(
            "SELECT external_uid,title,scheduled_minute FROM world_timeline_events "
            "WHERE world_id='world-a' ORDER BY external_uid"
        ).fetchall()
        assert [(row["external_uid"], row["title"], row["scheduled_minute"]) for row in definitions] == [
            ("event-one", "Suceso corregido", 490),
            ("event-two", "Suceso event-two", 491),
        ]

        replay = fire_due_world_events(conn, "session-a", 480, 491)
        assert [item["external_uid"] for item in replay] == ["event-one", "event-two"]
