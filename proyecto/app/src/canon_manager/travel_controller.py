"""Transactional travel execution for a saved interactive-game session.

Each step commits position, fog-of-war, world clock, due timeline events, and
route progress in one SQLite transaction. The controller is deliberately
step-driven: clients can pause, resume, cancel, or retarget between waypoints
without a background worker or partially applied movement.
"""
from __future__ import annotations

import json
import math
import sqlite3
from typing import Any

from .db import Database
from .timeline import absolute_minute, fire_due_world_events
from .world_map import (
    ExplorationState,
    Point,
    WorldMap,
    world_map_from_config,
    world_map_to_config,
)


class TravelControllerError(RuntimeError):
    """Base error for invalid or unavailable travel actions."""


class TravelNotFoundError(TravelControllerError):
    """The requested session or active travel record does not exist."""


class TravelConflictError(TravelControllerError):
    """The requested operation conflicts with the current travel status."""


class MapRegionNotFoundError(TravelControllerError):
    """No configured map geometry exists for the requested world region."""


def _point_json(point: Point) -> list[float]:
    return [point.x_m, point.y_m]


def _point_from_json(raw: Any) -> Point:
    if not isinstance(raw, list) or len(raw) != 2:
        raise ValueError("Stored route waypoint is invalid")
    return Point(float(raw[0]), float(raw[1]))


def _load_region_map(conn, world_id: str, region_id: str) -> WorldMap:
    row = conn.execute(
        "SELECT map_json,schema_version FROM world_map_regions WHERE world_id=? AND region_id=?",
        (world_id, region_id),
    ).fetchone()
    if row is None:
        raise MapRegionNotFoundError("No hay geometría registrada para esta región.")
    if int(row["schema_version"]) != 1:
        raise ValueError("Unsupported saved map region version")
    payload = json.loads(str(row["map_json"]))
    return world_map_from_config(payload)


def _load_map_state(conn, session_id: str, region_id: str, world: WorldMap):
    row = conn.execute(
        "SELECT x_m,y_m,cell_size_m,coordinate_system,exploration_json,schema_version "
        "FROM session_map_states WHERE session_id=? AND region_id=?",
        (session_id, region_id),
    ).fetchone()
    if row is None:
        return Point(0.0, 0.0), ExplorationState()
    if int(row["schema_version"]) != 1:
        raise ValueError("Unsupported saved map state version")
    if str(row["coordinate_system"]) != "local_cartesian_m_v1":
        raise ValueError("Unsupported saved map coordinate system")
    saved_cell = float(row["cell_size_m"])
    if not math.isclose(saved_cell, world.cell_size_m, rel_tol=0, abs_tol=1e-9):
        raise ValueError("La escala de la región cambió; requiere migrar la exploración guardada.")
    position = Point(float(row["x_m"]), float(row["y_m"]))
    exploration = ExplorationState.from_json(str(row["exploration_json"]))
    return position, exploration


def _save_map_state(
    conn, session_id: str, region_id: str, position: Point,
    exploration: ExplorationState, cell_size_m: float,
) -> None:
    conn.execute(
        """
        INSERT INTO session_map_states(
            session_id,region_id,x_m,y_m,cell_size_m,coordinate_system,
            exploration_json,schema_version,updated_at
        ) VALUES(?,?,?,?,?,'local_cartesian_m_v1',?,1,CURRENT_TIMESTAMP)
        ON CONFLICT(session_id,region_id) DO UPDATE SET
            x_m=excluded.x_m,
            y_m=excluded.y_m,
            cell_size_m=excluded.cell_size_m,
            coordinate_system=excluded.coordinate_system,
            exploration_json=excluded.exploration_json,
            schema_version=excluded.schema_version,
            updated_at=CURRENT_TIMESTAMP
        """,
        (session_id, region_id, position.x_m, position.y_m,
         cell_size_m, exploration.to_json()),
    )


def register_map_region(
    database: Database, world_id: str, region_id: str, world: WorldMap
) -> None:
    """Save the single authoritative region geometry used by travel and map UI."""
    if not region_id.strip():
        raise ValueError("region_id must be a non-empty string")
    config_json = json.dumps(
        world_map_to_config(world), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    with database.transaction() as conn:
        if conn.execute("SELECT 1 FROM worlds WHERE id=?", (world_id,)).fetchone() is None:
            raise TravelNotFoundError("El mundo no existe.")
        active_trip = conn.execute(
            "SELECT 1 FROM session_travel_states t JOIN sessions s ON s.id=t.session_id "
            "WHERE s.world_id=? AND t.region_id=? AND t.status IN ('running','paused') LIMIT 1",
            (world_id, region_id),
        ).fetchone()
        if active_trip is not None:
            raise TravelConflictError(
                "No se puede modificar la geometría mientras una partida recorre esta región."
            )
        conn.execute(
            """
            INSERT INTO world_map_regions(world_id,region_id,map_json,schema_version,updated_at)
            VALUES(?,?,?,1,CURRENT_TIMESTAMP)
            ON CONFLICT(world_id,region_id) DO UPDATE SET
                map_json=excluded.map_json,
                schema_version=excluded.schema_version,
                updated_at=CURRENT_TIMESTAMP
            """,
            (world_id, region_id, config_json),
        )


def get_map_region(database: Database, world_id: str, region_id: str) -> dict[str, Any]:
    with database.connection() as conn:
        world = _load_region_map(conn, world_id, region_id)
        return world_map_to_config(world)


def _load_session(conn, session_id: str):
    row = conn.execute(
        "SELECT id,world_id,day,minute_of_day,current_location,protagonist_entity_id "
        "FROM sessions WHERE id=?",
        (session_id,),
    ).fetchone()
    if row is None:
        raise TravelNotFoundError("La partida no existe.")
    return row


def _travel_snapshot(row, *, duplicate: bool = False) -> dict[str, Any]:
    route_raw = json.loads(str(row["route_json"]))
    route = [_point_from_json(item) for item in route_raw]
    return {
        "session_id": str(row["session_id"]),
        "region_id": str(row["region_id"]),
        "status": str(row["status"]),
        "route": [_point_json(point) for point in route],
        "next_waypoint_index": int(row["next_waypoint_index"]),
        "destination": {
            "x_m": float(row["destination_x_m"]),
            "y_m": float(row["destination_y_m"]),
            "label": str(row["destination_label"]),
        },
        "elapsed_seconds": int(row["elapsed_seconds"]),
        "clock_minutes_applied": int(row["clock_minutes_applied"]),
        "duplicate_request": duplicate,
    }


def get_travel_state(database: Database, session_id: str) -> dict[str, Any] | None:
    with database.connection() as conn:
        row = conn.execute(
            "SELECT t.*,s.day,s.minute_of_day,m.x_m,m.y_m "
            "FROM session_travel_states t JOIN sessions s ON s.id=t.session_id "
            "LEFT JOIN session_map_states m ON m.session_id=t.session_id AND m.region_id=t.region_id "
            "WHERE t.session_id=?",
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        result = _travel_snapshot(row)
        result["current_position"] = (
            {"x_m": float(row["x_m"]), "y_m": float(row["y_m"])}
            if row["x_m"] is not None else None
        )
        result["clock"] = {
            "day": int(row["day"]),
            "minute_of_day": int(row["minute_of_day"]),
        }
        return result


def get_session_map_state(
    database: Database, session_id: str, region_id: str
) -> dict[str, Any]:
    """Read the exact persisted position and fog-of-war used by travel."""
    with database.connection() as conn:
        session = conn.execute(
            "SELECT world_id FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
        if session is None:
            raise TravelNotFoundError("La partida no existe.")
        world = _load_region_map(conn, str(session["world_id"]), region_id)
        row = conn.execute(
            "SELECT 1 FROM session_map_states WHERE session_id=? AND region_id=?",
            (session_id, region_id),
        ).fetchone()
        position, exploration = _load_map_state(conn, session_id, region_id, world)
        cells = sorted(
            exploration.discovered_cells, key=lambda cell: (cell[1], cell[0])
        )
        return {
            "session_id": session_id,
            "region_id": region_id,
            "initialized": row is not None,
            "position": _point_json(position),
            "cell_size_m": world.cell_size_m,
            "coordinate_system": "local_cartesian_m_v1",
            "schema_version": 1,
            "discovered_cells": [list(cell) for cell in cells],
        }


def plan_travel(
    database: Database,
    session_id: str,
    region_id: str,
    destination: Point,
    *,
    destination_label: str = "",
) -> dict[str, Any]:
    """Start a route or replace its destination from the currently saved position."""
    if not region_id.strip():
        raise ValueError("region_id must be a non-empty string")
    if len(destination_label) > 180:
        raise ValueError("destination_label cannot exceed 180 characters")
    with database.transaction() as conn:
        session = _load_session(conn, session_id)
        previous = conn.execute(
            "SELECT * FROM session_travel_states WHERE session_id=?", (session_id,)
        ).fetchone()
        active = previous is not None and str(previous["status"]) in ("running", "paused")
        if active and str(previous["region_id"]) != region_id:
            raise TravelConflictError(
                "Cancela el recorrido actual antes de cambiar de región."
            )
        world = _load_region_map(conn, str(session["world_id"]), region_id)
        position, exploration = _load_map_state(conn, session_id, region_id, world)
        elapsed_seconds = int(previous["elapsed_seconds"]) if active else 0
        clock_minutes_applied = int(previous["clock_minutes_applied"]) if active else 0

        route = world.plan_route(position, destination)
        route_json = json.dumps(
            [_point_json(point) for point in route.waypoints],
            separators=(",", ":"),
        )
        status = "running" if len(route.waypoints) > 1 else "completed"
        _save_map_state(conn, session_id, region_id, position, exploration, world.cell_size_m)
        conn.execute(
            """
            INSERT INTO session_travel_states(
                session_id,region_id,route_json,next_waypoint_index,
                destination_x_m,destination_y_m,destination_label,status,
                elapsed_seconds,clock_minutes_applied,created_at,updated_at
            ) VALUES(?,?,?,1,?,?,?,?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
            ON CONFLICT(session_id) DO UPDATE SET
                region_id=excluded.region_id,
                route_json=excluded.route_json,
                next_waypoint_index=excluded.next_waypoint_index,
                destination_x_m=excluded.destination_x_m,
                destination_y_m=excluded.destination_y_m,
                destination_label=excluded.destination_label,
                status=excluded.status,
                elapsed_seconds=excluded.elapsed_seconds,
                clock_minutes_applied=excluded.clock_minutes_applied,
                created_at=CASE WHEN ? THEN session_travel_states.created_at ELSE CURRENT_TIMESTAMP END,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                session_id, region_id, route_json,
                destination.x_m, destination.y_m, destination_label, status,
                elapsed_seconds, clock_minutes_applied, 1 if active else 0,
            ),
        )
        saved = conn.execute(
            "SELECT * FROM session_travel_states WHERE session_id=?", (session_id,)
        ).fetchone()
        result = _travel_snapshot(saved)
        result.update({
            "start": _point_json(position),
            "planned_distance_m": route.total_distance_m,
            "estimated_travel_seconds": route.estimated_travel_seconds,
            "expanded_nodes": route.expanded_nodes,
            "replaced_existing_route": active,
        })
        return result


def advance_travel_step(
    database: Database, session_id: str, request_id: str
) -> dict[str, Any]:
    """Commit one route leg. Repeating request_id returns the original result."""
    if not request_id or len(request_id) < 8 or len(request_id) > 120:
        raise ValueError("request_id must contain between 8 and 120 characters")
    with database.transaction() as conn:
        cached = conn.execute(
            "SELECT result_json FROM session_travel_steps WHERE session_id=? AND request_id=?",
            (session_id, request_id),
        ).fetchone()
        if cached is not None:
            result = json.loads(str(cached["result_json"]))
            result["duplicate_request"] = True
            return result

        session = _load_session(conn, session_id)
        travel = conn.execute(
            "SELECT * FROM session_travel_states WHERE session_id=?", (session_id,)
        ).fetchone()
        if travel is None:
            raise TravelNotFoundError("No hay ningún recorrido preparado.")
        if str(travel["status"]) != "running":
            raise TravelConflictError("El recorrido no está en ejecución.")
        region_id = str(travel["region_id"])
        world = _load_region_map(conn, str(session["world_id"]), region_id)
        position, exploration = _load_map_state(conn, session_id, region_id, world)
        route_raw = json.loads(str(travel["route_json"]))
        route = [_point_from_json(item) for item in route_raw]
        next_index = int(travel["next_waypoint_index"])
        if next_index >= len(route):
            raise TravelConflictError("El recorrido no tiene más tramos pendientes.")

        next_point = route[next_index]
        segment = world.traverse_segment(position, next_point, exploration)
        old_elapsed = int(travel["elapsed_seconds"])
        new_elapsed = old_elapsed + segment.travel_seconds
        old_clock_minutes = int(travel["clock_minutes_applied"])
        final_step = next_index + 1 >= len(route)
        new_clock_minutes = new_elapsed // 60
        if final_step and new_elapsed % 60:
            new_clock_minutes += 1
        minutes_to_apply = new_clock_minutes - old_clock_minutes

        old_total = absolute_minute(int(session["day"]), int(session["minute_of_day"]))
        new_total = old_total + minutes_to_apply
        new_day = new_total // 1440 + 1
        new_minute = new_total % 1440
        if minutes_to_apply:
            conn.execute(
                "UPDATE sessions SET day=?,minute_of_day=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (new_day, new_minute, session_id),
            )
        _save_map_state(conn, session_id, region_id, next_point, exploration, world.cell_size_m)

        fired = fire_due_world_events(conn, session_id, old_total, new_total)
        new_index = next_index + 1
        status = "completed" if final_step else "running"
        if final_step and str(travel["destination_label"]).strip():
            label = str(travel["destination_label"]).strip()
            conn.execute(
                "UPDATE sessions SET current_location=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (label, session_id),
            )
            conn.execute(
                """
                INSERT INTO session_presence(session_id,entity_id,location,presence_status)
                VALUES(?,?,?,'present')
                ON CONFLICT(session_id,entity_id) DO UPDATE SET
                    location=excluded.location,presence_status='present',updated_at=CURRENT_TIMESTAMP
                """,
                (session_id, str(session["protagonist_entity_id"]), label),
            )
        conn.execute(
            """
            UPDATE session_travel_states SET next_waypoint_index=?,status=?,
                elapsed_seconds=?,clock_minutes_applied=?,updated_at=CURRENT_TIMESTAMP
            WHERE session_id=?
            """,
            (new_index, status, new_elapsed, new_clock_minutes, session_id),
        )
        travel_after = conn.execute(
            "SELECT * FROM session_travel_states WHERE session_id=?", (session_id,)
        ).fetchone()
        result = {
            "travel": _travel_snapshot(travel_after),
            "segment": {
                "from": _point_json(segment.start),
                "to": _point_json(segment.end),
                "distance_m": segment.distance_m,
                "travel_seconds": segment.travel_seconds,
                "newly_discovered_cells": [list(cell) for cell in segment.newly_discovered_cells],
                "visited_cells": [list(cell) for cell in segment.visited_cells],
                "crossed_area_ids": list(segment.crossed_area_ids),
                "crossed_terrain_ids": list(segment.crossed_terrain_ids),
            },
            "clock": {"day": new_day, "minute_of_day": new_minute, "minutes_advanced": minutes_to_apply},
            "fired_world_events": fired,
        }
        conn.execute(
            "INSERT INTO session_travel_steps(session_id,request_id,result_json) VALUES(?,?,?)",
            (session_id, request_id, json.dumps(result, ensure_ascii=False, separators=(",", ":"))),
        )
        return result


def change_travel_status(
    database: Database, session_id: str, action: str
) -> dict[str, Any]:
    allowed = {
        "pause": ("running", "paused"),
        "resume": ("paused", "running"),
        "cancel": (("running", "paused"), "cancelled"),
    }
    if action not in allowed:
        raise ValueError("Unsupported travel action")
    expected, new_status = allowed[action]
    with database.transaction() as conn:
        session = _load_session(conn, session_id)
        row = conn.execute(
            "SELECT * FROM session_travel_states WHERE session_id=?", (session_id,)
        ).fetchone()
        if row is None:
            raise TravelNotFoundError("No hay ningún recorrido preparado.")
        current = str(row["status"])
        valid = current in expected if isinstance(expected, tuple) else current == expected
        if not valid:
            raise TravelConflictError(f"No se puede {action} un recorrido en estado {current}.")

        fired: list[dict[str, Any]] = []
        minutes_to_apply = 0
        clock = {
            "day": int(session["day"]),
            "minute_of_day": int(session["minute_of_day"]),
            "minutes_advanced": 0,
        }
        if action == "cancel":
            elapsed_seconds = int(row["elapsed_seconds"])
            applied_minutes = int(row["clock_minutes_applied"])
            final_minutes = (elapsed_seconds + 59) // 60
            minutes_to_apply = max(0, final_minutes - applied_minutes)
            if minutes_to_apply:
                previous_total = absolute_minute(
                    int(session["day"]), int(session["minute_of_day"])
                )
                new_total = previous_total + minutes_to_apply
                new_day = new_total // 1440 + 1
                new_minute = new_total % 1440
                conn.execute(
                    "UPDATE sessions SET day=?,minute_of_day=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (new_day, new_minute, session_id),
                )
                fired = fire_due_world_events(conn, session_id, previous_total, new_total)
                clock = {
                    "day": new_day,
                    "minute_of_day": new_minute,
                    "minutes_advanced": minutes_to_apply,
                }
            conn.execute(
                "UPDATE session_travel_states SET status=?,clock_minutes_applied=?,updated_at=CURRENT_TIMESTAMP "
                "WHERE session_id=?",
                (new_status, final_minutes, session_id),
            )
        else:
            conn.execute(
                "UPDATE session_travel_states SET status=?,updated_at=CURRENT_TIMESTAMP WHERE session_id=?",
                (new_status, session_id),
            )

        after = conn.execute(
            "SELECT * FROM session_travel_states WHERE session_id=?", (session_id,)
        ).fetchone()
        result = _travel_snapshot(after)
        result["clock"] = clock
        result["fired_world_events"] = fired
        return result
