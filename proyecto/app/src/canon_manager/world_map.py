"""Deterministic geometric movement and fog-of-war primitives.

Coordinates use a local Cartesian plane: +X is east and +Y is north.
A requested diagonal step is measured by its Euclidean path length, not by
the length of either axis component.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
import math
from typing import Any, Iterable


_EPSILON = 1e-9


@dataclass(frozen=True, slots=True)
class Point:
    """A world position measured in metres in a local east/north plane."""

    x_m: float
    y_m: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.x_m) or not math.isfinite(self.y_m):
            raise ValueError("Point coordinates must be finite numbers")


class Direction(str, Enum):
    NORTH = "N"
    NORTH_EAST = "NE"
    EAST = "E"
    SOUTH_EAST = "SE"
    SOUTH = "S"
    SOUTH_WEST = "SW"
    WEST = "W"
    NORTH_WEST = "NW"

    @property
    def unit_vector(self) -> tuple[float, float]:
        diagonal = math.sqrt(0.5)
        return {
            Direction.NORTH: (0.0, 1.0),
            Direction.NORTH_EAST: (diagonal, diagonal),
            Direction.EAST: (1.0, 0.0),
            Direction.SOUTH_EAST: (diagonal, -diagonal),
            Direction.SOUTH: (0.0, -1.0),
            Direction.SOUTH_WEST: (-diagonal, -diagonal),
            Direction.WEST: (-1.0, 0.0),
            Direction.NORTH_WEST: (-diagonal, diagonal),
        }[self]


@dataclass(frozen=True, slots=True)
class Polygon:
    """A simple polygon footprint; vertices are ordered around its boundary."""

    vertices: tuple[Point, ...]

    def __post_init__(self) -> None:
        if len(self.vertices) < 3:
            raise ValueError("A polygon requires at least three vertices")

    def contains(self, point: Point) -> bool:
        """Return True for points inside or on the polygon boundary."""
        inside = False
        count = len(self.vertices)
        for index in range(count):
            a = self.vertices[index]
            b = self.vertices[(index + 1) % count]
            if _point_on_segment(point, a, b):
                return True
            if (a.y_m > point.y_m) != (b.y_m > point.y_m):
                cross_x = (
                    (b.x_m - a.x_m) * (point.y_m - a.y_m)
                    / (b.y_m - a.y_m)
                    + a.x_m
                )
                if point.x_m < cross_x:
                    inside = not inside
        return inside


@dataclass(frozen=True, slots=True)
class MapArea:
    """A named physical area, not a point that triggers at a distance threshold."""

    area_id: str
    name: str
    footprint: Polygon

    def __post_init__(self) -> None:
        if not self.area_id.strip() or not self.name.strip():
            raise ValueError("Map areas require a non-empty id and name")


@dataclass(frozen=True, slots=True)
class TerrainZone:
    """A terrain polygon with a local walking-speed multiplier."""

    terrain_id: str
    name: str
    footprint: Polygon
    speed_multiplier: float = 1.0

    def __post_init__(self) -> None:
        if not self.terrain_id.strip() or not self.name.strip():
            raise ValueError("Terrain zones require a non-empty id and name")
        if not math.isfinite(self.speed_multiplier) or self.speed_multiplier <= 0:
            raise ValueError("Terrain speed multiplier must be a positive finite number")


@dataclass
class ExplorationState:
    """Persistent fog-of-war state represented as integer grid-cell coordinates."""

    discovered_cells: set[tuple[int, int]] = field(default_factory=set)

    def to_dict(self) -> dict[str, list[list[int]]]:
        return {
            "discovered_cells": [
                [x, y] for x, y in sorted(self.discovered_cells, key=lambda cell: (cell[1], cell[0]))
            ]
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ExplorationState":
        raw_cells = payload.get("discovered_cells", [])
        if not isinstance(raw_cells, list):
            raise ValueError("discovered_cells must be a list")
        cells: set[tuple[int, int]] = set()
        for cell in raw_cells:
            if (
                not isinstance(cell, (list, tuple))
                or len(cell) != 2
                or any(isinstance(value, bool) or not isinstance(value, int) for value in cell)
            ):
                raise ValueError("Each discovered cell must contain two integers")
            cells.add((cell[0], cell[1]))
        return cls(discovered_cells=cells)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> "ExplorationState":
        decoded = json.loads(payload)
        if not isinstance(decoded, dict):
            raise ValueError("Exploration save must be a JSON object")
        return cls.from_dict(decoded)


@dataclass(frozen=True, slots=True)
class MovementResult:
    start: Point
    end: Point
    direction: Direction
    requested_distance_m: float
    actual_distance_m: float
    travel_seconds: int
    visited_cells: tuple[tuple[int, int], ...]
    newly_discovered_cells: tuple[tuple[int, int], ...]
    crossed_area_ids: tuple[str, ...]
    crossed_terrain_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorldMap:
    """Geometry and movement rules for one world or map region."""

    cell_size_m: float = 250.0
    areas: tuple[MapArea, ...] = ()
    terrain_zones: tuple[TerrainZone, ...] = ()

    def __post_init__(self) -> None:
        if not math.isfinite(self.cell_size_m) or self.cell_size_m <= 0:
            raise ValueError("cell_size_m must be a positive finite number")
        area_ids = [area.area_id for area in self.areas]
        terrain_ids = [zone.terrain_id for zone in self.terrain_zones]
        if len(area_ids) != len(set(area_ids)):
            raise ValueError("Map area ids must be unique")
        if len(terrain_ids) != len(set(terrain_ids)):
            raise ValueError("Terrain ids must be unique")

    def move(
        self,
        start: Point,
        direction: Direction,
        distance_m: float,
        exploration: ExplorationState,
        *,
        base_speed_mps: float = 1.25,
    ) -> MovementResult:
        """Move exactly the requested path length and update fog-of-war.

        Diagonal movement is normalized, so a 500 m NE step travels 500 m,
        with equal east and north components. Terrain affects travel time,
        not the geometric distance. Impassable boundaries/route finding are
        deliberately a separate layer and are not implied by this primitive.
        """
        if not math.isfinite(distance_m) or distance_m <= 0:
            raise ValueError("distance_m must be a positive finite number")
        if not math.isfinite(base_speed_mps) or base_speed_mps <= 0:
            raise ValueError("base_speed_mps must be a positive finite number")

        dx, dy = direction.unit_vector
        end = Point(start.x_m + dx * distance_m, start.y_m + dy * distance_m)
        visited = _cells_intersected_by_segment(start, end, self.cell_size_m)
        new_cells = visited.difference(exploration.discovered_cells)
        exploration.discovered_cells.update(visited)

        crossed_areas = tuple(
            sorted(
                area.area_id
                for area in self.areas
                if _segment_intersects_polygon(start, end, area.footprint)
            )
        )
        crossed_terrain = tuple(
            sorted(
                zone.terrain_id
                for zone in self.terrain_zones
                if _segment_intersects_polygon(start, end, zone.footprint)
            )
        )
        travel_seconds = _travel_time_seconds(
            start, end, self.terrain_zones, base_speed_mps
        )

        return MovementResult(
            start=start,
            end=end,
            direction=direction,
            requested_distance_m=distance_m,
            actual_distance_m=math.hypot(end.x_m - start.x_m, end.y_m - start.y_m),
            travel_seconds=travel_seconds,
            visited_cells=tuple(sorted(visited, key=lambda cell: (cell[1], cell[0]))),
            newly_discovered_cells=tuple(
                sorted(new_cells, key=lambda cell: (cell[1], cell[0]))
            ),
            crossed_area_ids=crossed_areas,
            crossed_terrain_ids=crossed_terrain,
        )


def _cross(ax: float, ay: float, bx: float, by: float) -> float:
    return ax * by - ay * bx


def _point_on_segment(point: Point, start: Point, end: Point) -> bool:
    cross = _cross(
        point.x_m - start.x_m,
        point.y_m - start.y_m,
        end.x_m - start.x_m,
        end.y_m - start.y_m,
    )
    if abs(cross) > _EPSILON:
        return False
    dot = (
        (point.x_m - start.x_m) * (point.x_m - end.x_m)
        + (point.y_m - start.y_m) * (point.y_m - end.y_m)
    )
    return dot <= _EPSILON


def _segment_intersection_t(
    start: Point, end: Point, edge_start: Point, edge_end: Point
) -> float | None:
    rx, ry = end.x_m - start.x_m, end.y_m - start.y_m
    sx = edge_end.x_m - edge_start.x_m
    sy = edge_end.y_m - edge_start.y_m
    denominator = _cross(rx, ry, sx, sy)
    if abs(denominator) <= _EPSILON:
        return None
    qpx, qpy = edge_start.x_m - start.x_m, edge_start.y_m - start.y_m
    t = _cross(qpx, qpy, sx, sy) / denominator
    u = _cross(qpx, qpy, rx, ry) / denominator
    if -_EPSILON <= t <= 1 + _EPSILON and -_EPSILON <= u <= 1 + _EPSILON:
        return min(1.0, max(0.0, t))
    return None


def _polygon_breakpoints(start: Point, end: Point, polygon: Polygon) -> list[float]:
    values = [0.0, 1.0]
    for index, edge_start in enumerate(polygon.vertices):
        edge_end = polygon.vertices[(index + 1) % len(polygon.vertices)]
        t = _segment_intersection_t(start, end, edge_start, edge_end)
        if t is not None:
            values.append(t)
    return sorted(set(values))


def _segment_intersects_polygon(start: Point, end: Point, polygon: Polygon) -> bool:
    if polygon.contains(start) or polygon.contains(end):
        return True
    for index, edge_start in enumerate(polygon.vertices):
        edge_end = polygon.vertices[(index + 1) % len(polygon.vertices)]
        if _segment_intersection_t(start, end, edge_start, edge_end) is not None:
            return True
    return False


def _cells_intersected_by_segment(
    start: Point, end: Point, cell_size_m: float
) -> set[tuple[int, int]]:
    min_x = math.floor(min(start.x_m, end.x_m) / cell_size_m)
    max_x = math.floor(max(start.x_m, end.x_m) / cell_size_m)
    min_y = math.floor(min(start.y_m, end.y_m) / cell_size_m)
    max_y = math.floor(max(start.y_m, end.y_m) / cell_size_m)
    visited: set[tuple[int, int]] = set()

    for cell_x in range(min_x, max_x + 1):
        left = cell_x * cell_size_m
        right = left + cell_size_m
        for cell_y in range(min_y, max_y + 1):
            bottom = cell_y * cell_size_m
            top = bottom + cell_size_m
            if _segment_intersects_rectangle(start, end, left, bottom, right, top):
                visited.add((cell_x, cell_y))
    return visited


def _segment_intersects_rectangle(
    start: Point,
    end: Point,
    left: float,
    bottom: float,
    right: float,
    top: float,
) -> bool:
    """Liang–Barsky segment/axis-aligned rectangle intersection."""
    dx, dy = end.x_m - start.x_m, end.y_m - start.y_m
    p_values = (-dx, dx, -dy, dy)
    q_values = (
        start.x_m - left,
        right - start.x_m,
        start.y_m - bottom,
        top - start.y_m,
    )
    t_min, t_max = 0.0, 1.0
    for p_value, q_value in zip(p_values, q_values):
        if abs(p_value) <= _EPSILON:
            if q_value < -_EPSILON:
                return False
            continue
        ratio = q_value / p_value
        if p_value < 0:
            t_min = max(t_min, ratio)
        else:
            t_max = min(t_max, ratio)
        if t_min - _EPSILON > t_max:
            return False
    return True



def _segment_within_polygon(start: Point, end: Point, polygon: Polygon) -> bool:
    """Return True only when the complete segment remains inside a boundary polygon."""
    if not polygon.contains(start) or not polygon.contains(end):
        return False
    breakpoints = _polygon_breakpoints(start, end, polygon)
    for left, right in zip(breakpoints, breakpoints[1:]):
        if right - left <= _EPSILON:
            continue
        midpoint_t = (left + right) / 2
        midpoint = Point(
            start.x_m + (end.x_m - start.x_m) * midpoint_t,
            start.y_m + (end.y_m - start.y_m) * midpoint_t,
        )
        if not polygon.contains(midpoint):
            return False
    return True


def _travel_time_seconds_raw(
    start: Point,
    end: Point,
    terrain_zones: Iterable[TerrainZone],
    base_speed_mps: float,
    road_zones: Iterable[RoadZone] = (),
) -> float:
    distance = math.hypot(end.x_m - start.x_m, end.y_m - start.y_m)
    terrain = tuple(terrain_zones)
    roads = tuple(road_zones)
    breakpoints = {0.0, 1.0}
    for zone in (*terrain, *roads):
        breakpoints.update(_polygon_breakpoints(start, end, zone.footprint))
    ordered = sorted(breakpoints)

    seconds = 0.0
    for left, right in zip(ordered, ordered[1:]):
        if right - left <= _EPSILON:
            continue
        midpoint_t = (left + right) / 2
        midpoint = Point(
            start.x_m + (end.x_m - start.x_m) * midpoint_t,
            start.y_m + (end.y_m - start.y_m) * midpoint_t,
        )
        terrain_factor = min(
            (zone.speed_multiplier for zone in terrain if zone.footprint.contains(midpoint)),
            default=1.0,
        )
        road_factor = max(
            (road.speed_multiplier for road in roads if road.footprint.contains(midpoint)),
            default=1.0,
        )
        seconds += (
            distance * (right - left)
            / (base_speed_mps * terrain_factor * road_factor)
        )
    return seconds


def _travel_time_seconds(
    start: Point,
    end: Point,
    terrain_zones: Iterable[TerrainZone],
    base_speed_mps: float,
    road_zones: Iterable[RoadZone] = (),
) -> int:
    return math.ceil(
        _travel_time_seconds_raw(start, end, terrain_zones, base_speed_mps, road_zones)
        - _EPSILON
    )
