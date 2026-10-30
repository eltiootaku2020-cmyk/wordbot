"""Deterministic scheduling primitives for world-level timeline events.

Only approved fixed-time events are executable in this first layer.
Condition-based events are stored for later evaluation and never guessed by the AI.
Call fire_crossed_events inside the same SQLite transaction that advances a session clock.
"""
from __future__ import annotations

import json
import uuid
from sqlite3 import Connection
from typing import Any


def _absolute_minute(day: int, minute_of_day: int) -> int:
    if isinstance(day, bool) or not isinstance(day, int) or day < 1:
        raise ValueError("day must be an integer >= 1")
    if isinstance(minute_of_day, bool) or not isinstance(minute_of_day, int):
        raise ValueError("minute_of_day must be an integer")
    if not 0 <= minute_of_day < 1440:
        raise ValueError("minute_of_day must be between 0 and 1439")
    return (day - 1) * 1440 + minute_of_day


def _object_json(raw: str, field: str) -> dict[str, Any]:
    value = json.loads(raw or "{}")
    if not isinstance(value, dict):
        raise ValueError(f"{field} must contain a JSON object")
    return value


def fire_crossed_events(
    conn: Connection,
    session_id: str,
    turn_id: str,
    previous_day: int,
    previous_minute: int,
    current_day: int,
    current_minute: int,
) -> list[dict[str, Any]]:
    """Record approved fixed-time events crossed by this clock advance.

    The interval is open on the old timestamp and closed on the new one.
    The unique (session_id, scheduled_event_id) ledger makes retries idempotent.
    Definitions are world-scoped; executions are session-scoped.
    """
    if not session_id or not turn_id:
        raise ValueError("session_id and turn_id are required")
    start = _absolute_minute(previous_day, previous_minute)
    end = _absolute_minute(current_day, current_minute)
    if end < start:
        raise ValueError("the session clock cannot move backwards")
    if end == start:
        return []

    session = conn.execute(
        "SELECT world_id FROM sessions WHERE id=?", (session_id,)
    ).fetchone()
    if session is None:
        raise ValueError("session does not exist")

    due = conn.execute(
        "SELECT * FROM world_timeline_events "
        "WHERE world_id=? AND activation_type='fixed_time' "
        "AND approval_status='approved' AND lifecycle_status='active' "
        "AND ((scheduled_day-1)*1440 + scheduled_minute) > ? "
        "AND ((scheduled_day-1)*1440 + scheduled_minute) <= ? "
        "ORDER BY scheduled_day, scheduled_minute, id",
        (session["world_id"], start, end),
    ).fetchall()

    fired: list[dict[str, Any]] = []
    for event in due:
        record = {
            "event_id": event["id"],
            "stable_key": event["stable_key"],
            "title": event["title"],
            "description": event["description"],
            "scope_type": event["scope_type"],
            "location": event["location"],
            "consequences": _object_json(event["consequences_json"], "consequences_json"),
        }
        cursor = conn.execute(
            "INSERT OR IGNORE INTO session_timeline_runs "
            "(id,session_id,scheduled_event_id,fired_turn_id,due_day,due_minute,"
            "reached_day,reached_minute,record_json) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                uuid.uuid4().hex, session_id, event["id"], turn_id,
                event["scheduled_day"], event["scheduled_minute"],
                current_day, current_minute,
                json.dumps(record, ensure_ascii=False, separators=(",", ":")),
            ),
        )
        if cursor.rowcount == 1:
            fired.append(record)
    return fired
