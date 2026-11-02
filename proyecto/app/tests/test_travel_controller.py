import json
from pathlib import Path

import pytest

from canon_manager.db import Database
from canon_manager.map_persistence import save_map_state
from canon_manager.travel_controller import (
    TravelConflictError,
    advance_travel_step,
    change_travel_status,
    get_travel_state,
    plan_travel,
    register_map_region,
)
from canon_manager.world_map import (
    ExplorationState,
    ObstacleZone,
    Point,
    Polygon,
    RoadZone,
    RouteNotFoundError,
    WorldMap,
)


def rectangle(left: float, bottom: float, right: float, top: float) -> Polygon:
    return Polygon((
        Point(left, bottom),
        Point(right, bottom),
        Point(right, top),
        Point(left, top),
    ))


@pytest.fixture
def game(tmp_path: Path):
    database = Database(str(tmp_path / "travel.sqlite3"))
    database.initialize()
    with database.transaction() as conn:
        conn.execute("INSERT INTO worlds(id,name) VALUES('world-1','Test World')")
        conn.execute(
            "INSERT INTO entities(id,world_id,name,kind) VALUES('hero','world-1','Hero','protagonist')"
        )
        conn.execute(
            "INSERT INTO sessions(id,world_id,name,day,minute_of_day,current_location,protagonist_entity_id) "
            "VALUES('session-1','world-1','Campaign',1,480,'Bosque','hero')"
        )
        conn.execute(
            "INSERT INTO session_presence(session_id,entity_id,location,presence_status) "
            "VALUES('session-1','hero','Bosque','present')"
        )
    world = WorldMap(cell_size_m=100)
    register_map_region(database, "world-1", "forest", world)
    return database


def test_travel_step_updates_position_clock_and_exploration_atomically(game: Database):
    planned = plan_travel(
        game, "session-1", "forest", Point(300, 0), destination_label="Claro del Este"
    )
    assert planned["status"] == "running"
    assert planned["route"] == [[0.0, 0.0], [300.0, 0.0]]

    result = advance_travel_step(game, "session-1", "step-request-0001")

    assert result["travel"]["status"] == "completed"
    assert result["segment"]["to"] == [300.0, 0.0]
    assert result["segment"]["newly_discovered_cells"]
    assert result["clock"] == {"day": 1, "minute_of_day": 484, "minutes_advanced": 4}
    with game.connection() as conn:
        session = conn.execute(
            "SELECT day,minute_of_day,current_location FROM sessions WHERE id='session-1'"
        ).fetchone()
        state = conn.execute(
            "SELECT x_m,y_m,exploration_json FROM session_map_states "
            "WHERE session_id='session-1' AND region_id='forest'"
        ).fetchone()
        presence = conn.execute(
            "SELECT location,presence_status FROM session_presence WHERE session_id='session-1' AND entity_id='hero'"
        ).fetchone()
    assert (session["day"], session["minute_of_day"], session["current_location"]) == (
        1, 484, "Claro del Este"
    )
    assert (state["x_m"], state["y_m"]) == (300, 0)
    assert json.loads(state["exploration_json"])["discovered_cells"]
    assert (presence["location"], presence["presence_status"]) == ("Claro del Este", "present")


def test_duplicate_step_request_does_not_move_or_advance_clock_twice(game: Database):
    plan_travel(game, "session-1", "forest", Point(300, 0))
    first = advance_travel_step(game, "session-1", "retry-safe-step-01")
    duplicate = advance_travel_step(game, "session-1", "retry-safe-step-01")

    assert duplicate["duplicate_request"] is True
    assert duplicate["segment"] == first["segment"]
    with game.connection() as conn:
        session = conn.execute(
            "SELECT day,minute_of_day FROM sessions WHERE id='session-1'"
        ).fetchone()
        steps = conn.execute(
            "SELECT COUNT(*) AS n FROM session_travel_steps WHERE session_id='session-1'"
        ).fetchone()["n"]
    assert (session["day"], session["minute_of_day"]) == (1, 484)
    assert steps == 1


def test_pause_resume_and_cancel_control_travel_between_waypoints(game: Database):
    mountain = ObstacleZone(
        "mountain", "Mountain", rectangle(400, -100, 600, 100), "mountain"
    )
    register_map_region(
        game, "world-1", "forest", WorldMap(cell_size_m=100, obstacles=(mountain,))
    )
    plan_travel(game, "session-1", "forest", Point(1000, 0))

    paused = change_travel_status(game, "session-1", "pause")
    assert paused["status"] == "paused"
    with pytest.raises(TravelConflictError):
        advance_travel_step(game, "session-1", "blocked-step-0001")

    resumed = change_travel_status(game, "session-1", "resume")
    assert resumed["status"] == "running"
    stepped = advance_travel_step(game, "session-1", "valid-step-00001")
    assert stepped["travel"]["next_waypoint_index"] == 2

    cancelled = change_travel_status(game, "session-1", "cancel")
    assert cancelled["status"] == "cancelled"
    with pytest.raises(TravelConflictError):
        advance_travel_step(game, "session-1", "after-cancel-0001")


def test_retargeting_replans_from_current_saved_position(game: Database):
    mountain = ObstacleZone(
        "mountain", "Mountain", rectangle(400, -100, 600, 100), "mountain"
    )
    register_map_region(
        game, "world-1", "forest", WorldMap(cell_size_m=100, obstacles=(mountain,))
    )
    first = plan_travel(game, "session-1", "forest", Point(1000, 0))
    step = advance_travel_step(game, "session-1", "retarget-first-001")
    current_position = step["segment"]["to"]

    replacement = plan_travel(
        game, "session-1", "forest", Point(1000, 500), destination_label="Ridge Camp"
    )

    assert replacement["replaced_existing_route"] is True
    assert replacement["route"][0] == current_position
    assert replacement["destination"] == {"x_m": 1000.0, "y_m": 500.0, "label": "Ridge Camp"}
    assert replacement["elapsed_seconds"] == first["elapsed_seconds"] + step["segment"]["travel_seconds"]


def test_due_world_event_fires_once_when_travel_advances_world_clock(game: Database):
    with game.transaction() as conn:
        conn.execute(
            "INSERT INTO world_timeline_events(id,world_id,external_uid,title,description,"
            "scheduled_day,scheduled_minute,location,canon_status,enabled) "
            "VALUES('eruption','world-1','eruption','Old Alarm','A scheduled event.',1,482,'Volcano','confirmed',1)"
        )
    plan_travel(game, "session-1", "forest", Point(300, 0))
    result = advance_travel_step(game, "session-1", "timeline-step-0001")
    assert [item["external_uid"] for item in result["fired_world_events"]] == ["eruption"]

    advance_travel_step(game, "session-1", "timeline-step-0001")
    with game.connection() as conn:
        fired = conn.execute(
            "SELECT COUNT(*) AS n FROM session_timeline_events WHERE session_id='session-1'"
        ).fetchone()["n"]
    assert fired == 1


def test_route_without_path_does_not_create_a_travel_record(game: Database):
    bounds = rectangle(0, 0, 1000, 1000)
    wall = ObstacleZone("wall", "Wall", rectangle(490, 0, 510, 1000), "wall")
    register_map_region(
        game, "world-1", "forest",
        WorldMap(cell_size_m=100, obstacles=(wall,), walkable_bounds=bounds),
    )
    with pytest.raises(RouteNotFoundError):
        plan_travel(game, "session-1", "forest", Point(900, 500))
    assert get_travel_state(game, "session-1") is None



def test_cancel_accounts_for_subminute_travel_time(game: Database):
    mountain = ObstacleZone(
        "mountain", "Mountain", rectangle(400, -100, 600, 100), "mountain"
    )
    register_map_region(
        game, "world-1", "forest",
        WorldMap(cell_size_m=50, obstacles=(mountain,)),
    )
    plan_travel(game, "session-1", "forest", Point(1000, 0))
    first = advance_travel_step(game, "session-1", "partial-trip-step-01")
    assert first["travel"]["status"] == "running"
    assert first["segment"]["travel_seconds"] < 60
    assert first["clock"]["minutes_advanced"] == 0

    cancelled = change_travel_status(game, "session-1", "cancel")

    assert cancelled["status"] == "cancelled"
    assert cancelled["clock"]["minutes_advanced"] == 1
    with game.connection() as conn:
        clock = conn.execute(
            "SELECT day,minute_of_day FROM sessions WHERE id='session-1'"
        ).fetchone()
    assert (clock["day"], clock["minute_of_day"]) == (1, 481)


def test_region_geometry_cannot_change_during_active_travel(game: Database):
    mountain = ObstacleZone(
        "mountain", "Mountain", rectangle(400, -100, 600, 100), "mountain"
    )
    current_map = WorldMap(cell_size_m=100, obstacles=(mountain,))
    register_map_region(game, "world-1", "forest", current_map)
    plan_travel(game, "session-1", "forest", Point(1000, 0))

    with pytest.raises(TravelConflictError):
        register_map_region(game, "world-1", "forest", WorldMap(cell_size_m=200))


def test_active_route_cannot_retarget_to_another_region(game: Database):
    register_map_region(game, "world-1", "other-region", WorldMap(cell_size_m=100))
    obstacle = ObstacleZone(
        "mountain", "Mountain", rectangle(400, -100, 600, 100), "mountain"
    )
    register_map_region(
        game, "world-1", "forest", WorldMap(cell_size_m=100, obstacles=(obstacle,))
    )
    plan_travel(game, "session-1", "forest", Point(1000, 0))

    with pytest.raises(TravelConflictError):
        plan_travel(game, "session-1", "other-region", Point(100, 100))


def test_region_cell_size_cannot_change_after_exploration_is_saved(game: Database):
    register_map_region(game, "world-1", "forest", WorldMap(cell_size_m=100))
    save_map_state(
        game,
        "session-1",
        "forest",
        Point(0, 0),
        ExplorationState({(0, 0)}),
        cell_size_m=100,
    )

    with pytest.raises(TravelConflictError):
        register_map_region(game, "world-1", "forest", WorldMap(cell_size_m=200))
