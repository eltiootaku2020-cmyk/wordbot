import json
import math

import pytest

from canon_manager.world_map import (
    Direction,
    ExplorationState,
    MapArea,
    Point,
    Polygon,
    TerrainZone,
    WorldMap,
)


def rectangle(left: float, bottom: float, right: float, top: float) -> Polygon:
    return Polygon(
        (
            Point(left, bottom),
            Point(right, bottom),
            Point(right, top),
            Point(left, top),
        )
    )


def test_cardinal_step_uses_real_metre_coordinates() -> None:
    world = WorldMap(cell_size_m=250)
    state = ExplorationState()

    result = world.move(Point(0, 0), Direction.WEST, 500, state)

    assert result.end == Point(-500, 0)
    assert result.actual_distance_m == pytest.approx(500)
    assert result.travel_seconds == 400  # 500 m at 1.25 m/s
    assert state.discovered_cells


def test_diagonal_step_is_normalized_to_requested_distance() -> None:
    world = WorldMap()
    result = world.move(
        Point(0, 0), Direction.NORTH_WEST, 500, ExplorationState()
    )

    assert result.end.x_m == pytest.approx(-500 / math.sqrt(2))
    assert result.end.y_m == pytest.approx(500 / math.sqrt(2))
    assert result.actual_distance_m == pytest.approx(500)


def test_area_is_detected_when_path_crosses_it_but_endpoint_is_outside() -> None:
    village = MapArea("village-west", "Aldea del Oeste", rectangle(200, -30, 250, 30))
    world = WorldMap(areas=(village,))

    result = world.move(Point(0, 0), Direction.EAST, 500, ExplorationState())

    assert result.end == Point(500, 0)
    assert result.crossed_area_ids == ("village-west",)


def test_nearby_area_is_not_triggered_without_geometric_intersection() -> None:
    village = MapArea("village-east", "Aldea del Este", rectangle(100, -20, 200, 20))
    world = WorldMap(areas=(village,))

    result = world.move(Point(0, 0), Direction.NORTH_WEST, 500, ExplorationState())

    assert result.crossed_area_ids == ()


def test_terrain_zone_changes_travel_time_without_changing_distance() -> None:
    forest = TerrainZone(
        "dense-forest",
        "Bosque denso",
        rectangle(100, -10, 300, 10),
        speed_multiplier=0.5,
    )
    world = WorldMap(terrain_zones=(forest,))

    result = world.move(Point(0, 0), Direction.EAST, 500, ExplorationState())

    assert result.actual_distance_m == pytest.approx(500)
    assert result.crossed_terrain_ids == ("dense-forest",)
    assert result.travel_seconds == 560


def test_exploration_is_deterministic_and_serializable() -> None:
    world = WorldMap(cell_size_m=250)
    state = ExplorationState()

    first = world.move(Point(0, 0), Direction.EAST, 500, state)
    saved = state.to_json()
    restored = ExplorationState.from_json(saved)
    second = world.move(Point(0, 0), Direction.EAST, 500, restored)

    assert first.visited_cells
    assert second.newly_discovered_cells == ()
    assert restored.discovered_cells == state.discovered_cells
    assert json.loads(saved) == state.to_dict()


def test_invalid_distance_and_cell_size_are_rejected() -> None:
    with pytest.raises(ValueError):
        WorldMap(cell_size_m=0)
    with pytest.raises(ValueError):
        WorldMap().move(Point(0, 0), Direction.NORTH, 0, ExplorationState())


def test_exploration_payload_rejects_non_integer_cell_coordinates() -> None:
    with pytest.raises(ValueError):
        ExplorationState.from_dict({"discovered_cells": [[1, 2.5]]})
