"""World-level scheduled events shared by every narrative setting."""
from __future__ import annotations

from typing import Any


def absolute_minute(day: int, minute_of_day: int) -> int:
    if day < 1 or not 0 <= minute_of_day < 1440:
        raise ValueError("La fecha del mundo no es válida.")
    return (day - 1) * 1440 + minute_of_day


def fire_due_world_events(
    conn, session_id: str, previous_total_minutes: int, current_total_minutes: int
) -> list[dict[str, Any]]:
    """Fire confirmed fixed events once per session when the persisted clock reaches them.

    Catch-up is intentional: a restored/advanced session activates every due event
    that has not fired yet. The UNIQUE(session_id, world_event_id) constraint makes
    this safe across retries and concurrent turn processing.
    """
    if current_total_minutes < previous_total_minutes:
        raise ValueError("El reloj del mundo no puede retroceder.")
    session = conn.execute(
        "SELECT world_id FROM sessions WHERE id=?", (session_id,)
    ).fetchone()
    if session is None:
        raise ValueError("La partida no existe.")

    rows = conn.execute(
        "SELECT w.* FROM world_timeline_events w "
        "WHERE w.world_id=? AND w.enabled=1 AND w.canon_status='confirmed' "
        "AND ((w.scheduled_day-1)*1440+w.scheduled_minute)<=? "
        "AND NOT EXISTS (SELECT 1 FROM session_timeline_events f "
        "WHERE f.session_id=? AND f.world_event_id=w.id) "
        "ORDER BY w.scheduled_day,w.scheduled_minute,w.external_uid",
        (session["world_id"], current_total_minutes, session_id),
    ).fetchall()

    fired: list[dict[str, Any]] = []
    for row in rows:
        scheduled = absolute_minute(int(row["scheduled_day"]), int(row["scheduled_minute"]))
        cursor = conn.execute(
            "INSERT OR IGNORE INTO session_timeline_events("
            "id,session_id,world_event_id,scheduled_total_minutes,fired_total_minutes,"
            "fired_day,fired_minute) VALUES(?,?,?,?,?,?,?)",
            (
                f"{session_id}:{row['id']}", session_id, row["id"], scheduled,
                scheduled, int(row["scheduled_day"]), int(row["scheduled_minute"]),
            ),
        )
        if cursor.rowcount:
            fired.append({
                "id": row["id"], "external_uid": row["external_uid"],
                "title": row["title"], "description": row["description"],
                "location": row["location"], "scheduled_day": int(row["scheduled_day"]),
                "scheduled_minute": int(row["scheduled_minute"]),
                # Record the scheduled world date, not the later catch-up processing time.
                "fired_day": int(row["scheduled_day"]),
                "fired_minute": int(row["scheduled_minute"]),
            })
    return fired
