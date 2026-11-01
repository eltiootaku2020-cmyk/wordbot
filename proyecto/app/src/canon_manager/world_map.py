"""Deterministic geometric movement and fog-of-war primitives.

Coordinates use a local Cartesian plane: +X is east and +Y is north.
A requested diagonal step is measured by its Euclidean path length, not by
the length of either axis component.
"""
from __future__ import annotations

import heapq
import json
import math
from dataclasses import dataclass, field
from enum import Enum
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


@dataclass(frozen=True, slots=True)
class ObstacleZone:
    """An impassable polygon such as a mountain, river without a crossing, or wall."""

    obstacle_id: str
    name: str
    footprint: Polygon
    kind: str = "terrain"

    def __post_init__(self) -> None:
        if not self.obstacle_id.strip() or not self.name.strip() or not self.kind.strip():
            raise ValueError("Obstacles require a non-empty id, name, and kind")


@dataclass(frozen=True, slots=True)
class RoadZone:
    """A polygonal road corridor that increases travel speed while traversed."""

    road_id: str
    name: str
    footprint: Polygon
    speed_multiplier: float = 1.5

    def __post_init__(self) -> None:
        if not self.road_id.strip() or not self.name.strip():
            raise ValueError("Road corridors require a non-empty id and name")
        if not math.isfinite(self.speed_multiplier) or self.speed_multiplier <= 1:
            raise ValueError("Road speed_multiplier must be greater than 1")


class BlockedPositionError(ValueError):
    """Raised when a route endpoint lies inside an obstacle or outside map bounds."""


class BlockedPathError(ValueError):
    """Raised when a direct movement step crosses an impassable obstacle."""


class RouteNotFoundError(RuntimeError):
    """Raised when no traversable route exists inside the configured search area."""


class RouteSearchLimitError(RouteNotFoundError):
    """Raised when route search reaches its deterministic node-expansion budget."""


@dataclass(frozen=True, slots=True)
class RoutePlan:
    waypoints: tuple[Point, ...]
    total_distance_m: float
    estimated_travel_seconds: int
    expanded_nodes: int


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
class SegmentTraversal:
    """Committed result for one arbitrary straight segment of a planned route."""

    start: Point
    end: Point
    distance_m: float
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
    obstacles: tuple[ObstacleZone, ...] = ()
    roads: tuple[RoadZone, ...] = ()
    walkable_bounds: Polygon | None = None
    max_route_nodes: int = 100_000

    def __post_init__(self) -> None:
        if not math.isfinite(self.cell_size_m) or self.cell_size_m <= 0:
            raise ValueError("cell_size_m must be a positive finite number")
        area_ids = [area.area_id for area in self.areas]
        terrain_ids = [zone.terrain_id for zone in self.terrain_zones]
        obstacle_ids = [zone.obstacle_id for zone in self.obstacles]
        road_ids = [road.road_id for road in self.roads]
        if len(area_ids) != len(set(area_ids)):
            raise ValueError("Map area ids must be unique")
        if len(terrain_ids) != len(set(terrain_ids)):
            raise ValueError("Terrain ids must be unique")
        if len(obstacle_ids) != len(set(obstacle_ids)):
            raise ValueError("Obstacle ids must be unique")
        if len(road_ids) != len(set(road_ids)):
            raise ValueError("Road ids must be unique")
        if (
            isinstance(self.max_route_nodes, bool)
            or not isinstance(self.max_route_nodes, int)
            or self.max_route_nodes <= 0
        ):
            raise ValueError("max_route_nodes must be a positive integer")

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

        Diagonal movement is normalized, so a 500 m NE step travels 500 m.
        Terrain and road corridors affect travel time, not distance. Direct
        steps that cross obstacles are rejected; use plan_route() for detours.
        walkable_bounds constrains planned routes, not raw movement steps.
        """
        if not math.isfinite(distance_m) or distance_m <= 0:
            raise ValueError("distance_m must be a positive finite number")
        if not math.isfinite(base_speed_mps) or base_speed_mps <= 0:
            raise ValueError("base_speed_mps must be a positive finite number")

        dx, dy = direction.unit_vector
        end = Point(start.x_m + dx * distance_m, start.y_m + dy * distance_m)
        if not self._obstacle_edge_allowed(start, end):
            raise BlockedPathError("Movement crosses an impassable obstacle without a road crossing")
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
            start, end, self.terrain_zones, base_speed_mps, self.roads
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


    def traverse_segment(
        self,
        start: Point,
        end: Point,
        exploration: ExplorationState,
        *,
        base_speed_mps: float = 1.25,
    ) -> SegmentTraversal:
        """Apply one waypoint-to-waypoint leg and reveal only its traversed cells."""
        if not isinstance(start, Point) or not isinstance(end, Point):
            raise TypeError("start and end must be Point instances")
        if not isinstance(exploration, ExplorationState):
            raise TypeError("exploration must be an ExplorationState")
        if not math.isfinite(base_speed_mps) or base_speed_mps <= 0:
            raise ValueError("base_speed_mps must be a positive finite number")
        if not self._route_edge_allowed(start, end):
            raise BlockedPathError("Route segment crosses an impassable area")
        distance = math.hypot(end.x_m - start.x_m, end.y_m - start.y_m)
        visited = _cells_intersected_by_segment(start, end, self.cell_size_m)
        newly_discovered = visited.difference(exploration.discovered_cells)
        exploration.discovered_cells.update(visited)
        crossed_areas = tuple(sorted(
            area.area_id for area in self.areas
            if _segment_intersects_polygon(start, end, area.footprint)
        ))
        crossed_terrain = tuple(sorted(
            zone.terrain_id for zone in self.terrain_zones
            if _segment_intersects_polygon(start, end, zone.footprint)
        ))
        seconds = math.ceil(_travel_time_seconds_raw(
            start, end, self.terrain_zones, base_speed_mps, self.roads
        ) - _EPSILON)
        return SegmentTraversal(
            start=start,
            end=end,
            distance_m=distance,
            travel_seconds=seconds,
            visited_cells=tuple(sorted(visited, key=lambda cell: (cell[1], cell[0]))),
            newly_discovered_cells=tuple(sorted(
                newly_discovered, key=lambda cell: (cell[1], cell[0])
            )),
            crossed_area_ids=crossed_areas,
            crossed_terrain_ids=crossed_terrain,
        )

    def plan_route(
        self,
        start: Point,
        destination: Point,
        *,
        base_speed_mps: float = 1.25,
        max_search_nodes: int | None = None,
    ) -> RoutePlan:
        """Find a deterministic, time-aware route around impassable polygons.

        Grid nodes are spaced by cell_size_m. Exact endpoints are retained as
        waypoints and connected only to nearby visible grid nodes. Roads are
        polygonal corridors; their speed bonus influences route cost but never
        makes an obstacle traversable.
        """
        if not math.isfinite(base_speed_mps) or base_speed_mps <= 0:
            raise ValueError("base_speed_mps must be a positive finite number")
        budget = self.max_route_nodes if max_search_nodes is None else max_search_nodes
        if isinstance(budget, bool) or not isinstance(budget, int) or budget <= 0:
            raise ValueError("max_search_nodes must be a positive integer")

        if not self._route_point_allowed(start):
            raise BlockedPositionError("Route start is not traversable")
        if not self._route_point_allowed(destination):
            raise BlockedPositionError("Route destination is not traversable")
        if start == destination:
            return RoutePlan((start,), 0.0, 0, 0)

        if self._route_edge_allowed(start, destination):
            seconds = _travel_time_seconds_raw(
                start, destination, self.terrain_zones, base_speed_mps, self.roads
            )
            return RoutePlan(
                (start, destination),
                math.hypot(destination.x_m - start.x_m, destination.y_m - start.y_m),
                math.ceil(seconds - _EPSILON),
                0,
            )

        cell = self.cell_size_m
        if self.walkable_bounds is not None:
            xs = [point.x_m for point in self.walkable_bounds.vertices]
            ys = [point.y_m for point in self.walkable_bounds.vertices]
            min_ix = math.ceil(min(xs) / cell)
            max_ix = math.floor(max(xs) / cell)
            min_iy = math.ceil(min(ys) / cell)
            max_iy = math.floor(max(ys) / cell)
        else:
            all_points = [start, destination]
            all_points.extend(
                vertex for obstacle in self.obstacles for vertex in obstacle.footprint.vertices
            )
            min_ix = math.floor(min(point.x_m for point in all_points) / cell) - 3
            max_ix = math.ceil(max(point.x_m for point in all_points) / cell) + 3
            min_iy = math.floor(min(point.y_m for point in all_points) / cell) - 3
            max_iy = math.ceil(max(point.y_m for point in all_points) / cell) + 3

        def point_for(node: tuple[int, int]) -> Point:
            return Point(node[0] * cell, node[1] * cell)

        def node_allowed(node: tuple[int, int]) -> bool:
            return self._route_point_allowed(point_for(node))

        def near_nodes(point: Point) -> set[tuple[int, int]]:
            center_x = round(point.x_m / cell)
            center_y = round(point.y_m / cell)
            candidates: set[tuple[int, int]] = set()
            max_attach = math.sqrt(2) * cell + _EPSILON
            for ix in range(center_x - 1, center_x + 2):
                for iy in range(center_y - 1, center_y + 2):
                    node = (ix, iy)
                    if not (min_ix <= ix <= max_ix and min_iy <= iy <= max_iy):
                        continue
                    candidate = point_for(node)
                    distance = math.hypot(candidate.x_m - point.x_m, candidate.y_m - point.y_m)
                    if (
                        distance <= max_attach
                        and node_allowed(node)
                        and self._route_edge_allowed(point, candidate)
                    ):
                        candidates.add(node)
            return candidates

        start_nodes = near_nodes(start)
        goal_nodes = near_nodes(destination)
        if not start_nodes or not goal_nodes:
            raise RouteNotFoundError("No traversable grid connection exists near an endpoint")

        road_factor = max((road.speed_multiplier for road in self.roads), default=1.0)
        terrain_factor = max((zone.speed_multiplier for zone in self.terrain_zones), default=1.0)
        fastest_speed = base_speed_mps * max(1.0, road_factor) * max(1.0, terrain_factor)

        def heuristic(node: tuple[int, int]) -> float:
            point = point_for(node)
            return math.hypot(
                destination.x_m - point.x_m, destination.y_m - point.y_m
            ) / fastest_speed

        open_heap: list[tuple[float, float, int, int]] = []
        came_from: dict[tuple[int, int], tuple[int, int] | None] = {}
        scores: dict[tuple[int, int], float] = {}
        for node in sorted(start_nodes, key=lambda item: (item[1], item[0])):
            point = point_for(node)
            cost = _travel_time_seconds_raw(
                start, point, self.terrain_zones, base_speed_mps, self.roads
            )
            if cost < scores.get(node, math.inf):
                scores[node] = cost
                came_from[node] = None
                heapq.heappush(open_heap, (cost + heuristic(node), cost, node[1], node[0]))

        expanded = 0
        best_goal: tuple[int, int] | None = None
        best_total = math.inf
        directions = (
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 1),
            (1, -1), (1, 0), (1, 1),
        )

        while open_heap:
            estimate, queued_cost, iy, ix = heapq.heappop(open_heap)
            current = (ix, iy)
            current_cost = scores.get(current, math.inf)
            if queued_cost > current_cost + _EPSILON:
                continue
            if estimate >= best_total - _EPSILON:
                break

            expanded += 1
            if expanded > budget:
                raise RouteSearchLimitError(
                    f"Route search exceeded its {budget}-node expansion budget"
                )

            current_point = point_for(current)
            if current in goal_nodes:
                final_cost = current_cost + _travel_time_seconds_raw(
                    current_point, destination, self.terrain_zones, base_speed_mps, self.roads
                )
                if final_cost < best_total:
                    best_total = final_cost
                    best_goal = current

            for dx, dy in directions:
                neighbor = (ix + dx, iy + dy)
                nx, ny = neighbor
                if not (min_ix <= nx <= max_ix and min_iy <= ny <= max_iy):
                    continue
                if not node_allowed(neighbor):
                    continue

                neighbor_point = point_for(neighbor)
                if dx and dy:
                    side_a = (ix + dx, iy)
                    side_b = (ix, iy + dy)
                    if not node_allowed(side_a) or not node_allowed(side_b):
                        continue
                if not self._route_edge_allowed(current_point, neighbor_point):
                    continue

                edge_cost = _travel_time_seconds_raw(
                    current_point, neighbor_point, self.terrain_zones, base_speed_mps, self.roads
                )
                candidate_cost = current_cost + edge_cost
                if candidate_cost + _EPSILON >= scores.get(neighbor, math.inf):
                    continue
                scores[neighbor] = candidate_cost
                came_from[neighbor] = current
                priority = candidate_cost + heuristic(neighbor)
                heapq.heappush(open_heap, (priority, candidate_cost, ny, nx))

        if best_goal is None:
            raise RouteNotFoundError("No traversable route connects the requested positions")

        grid_path: list[tuple[int, int]] = []
        cursor: tuple[int, int] | None = best_goal
        while cursor is not None:
            grid_path.append(cursor)
            cursor = came_from[cursor]
        grid_path.reverse()

        waypoints: list[Point] = [start]
        for node in grid_path:
            candidate = point_for(node)
            if candidate != waypoints[-1]:
                waypoints.append(candidate)
        if destination != waypoints[-1]:
            waypoints.append(destination)

        distance = 0.0
        seconds = 0.0
        for left, right in zip(waypoints, waypoints[1:]):
            if not self._route_edge_allowed(left, right):
                raise RouteNotFoundError("Computed route failed final geometry validation")
            distance += math.hypot(right.x_m - left.x_m, right.y_m - left.y_m)
            seconds += _travel_time_seconds_raw(
                left, right, self.terrain_zones, base_speed_mps, self.roads
            )

        return RoutePlan(tuple(waypoints), distance, math.ceil(seconds - _EPSILON), expanded)

    def _route_point_allowed(self, point: Point) -> bool:
        if self.walkable_bounds is not None and not self.walkable_bounds.contains(point):
            return False
        return not any(obstacle.footprint.contains(point) for obstacle in self.obstacles)

    def _route_edge_allowed(self, start: Point, end: Point) -> bool:
        if self.walkable_bounds is not None and not _segment_within_polygon(
            start, end, self.walkable_bounds
        ):
            return False
        return self._obstacle_edge_allowed(start, end)

    def _obstacle_edge_allowed(self, start: Point, end: Point) -> bool:
        """Allow obstacle intersections only where an explicit road covers them."""
        for obstacle in self.obstacles:
            if not _segment_intersects_polygon(start, end, obstacle.footprint):
                continue
            breakpoints = set(_polygon_breakpoints(start, end, obstacle.footprint))
            for road in self.roads:
                breakpoints.update(_polygon_breakpoints(start, end, road.footprint))
            ordered = sorted(breakpoints)
            for left, right in zip(ordered, ordered[1:]):
                if right - left <= _EPSILON:
                    continue
                midpoint_t = (left + right) / 2
                midpoint = Point(
                    start.x_m + (end.x_m - start.x_m) * midpoint_t,
                    start.y_m + (end.y_m - start.y_m) * midpoint_t,
                )
                if obstacle.footprint.contains(midpoint) and not any(
                    road.footprint.contains(midpoint) for road in self.roads
                ):
                    return False
        return True


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



def world_map_to_config(world: WorldMap) -> dict[str, Any]:
    """Serialize canonical region geometry for the renderer and travel controller."""
    def vertices(polygon: Polygon) -> list[list[float]]:
        return [[point.x_m, point.y_m] for point in polygon.vertices]

    return {
        "schema_version": 1,
        "cell_size_m": world.cell_size_m,
        "max_route_nodes": world.max_route_nodes,
        "areas": [
            {"area_id": item.area_id, "name": item.name, "vertices": vertices(item.footprint)}
            for item in world.areas
        ],
        "terrain_zones": [
            {
                "terrain_id": item.terrain_id, "name": item.name,
                "vertices": vertices(item.footprint),
                "speed_multiplier": item.speed_multiplier,
            }
            for item in world.terrain_zones
        ],
        "obstacles": [
            {
                "obstacle_id": item.obstacle_id, "name": item.name, "kind": item.kind,
                "vertices": vertices(item.footprint),
            }
            for item in world.obstacles
        ],
        "roads": [
            {
                "road_id": item.road_id, "name": item.name,
                "vertices": vertices(item.footprint),
                "speed_multiplier": item.speed_multiplier,
            }
            for item in world.roads
        ],
        "walkable_bounds": vertices(world.walkable_bounds) if world.walkable_bounds else None,
    }


def world_map_from_config(payload: dict[str, Any]) -> WorldMap:
    """Validate and reconstruct a map definition saved for a world region."""
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("Unsupported world map definition version")

    def polygon(raw: Any) -> Polygon:
        if not isinstance(raw, list) or len(raw) < 3:
            raise ValueError("Polygon vertices must be a list of at least three points")
        return Polygon(tuple(
            Point(float(pair[0]), float(pair[1]))
            for pair in raw
            if isinstance(pair, (list, tuple)) and len(pair) == 2
        ))

    try:
        areas = tuple(
            MapArea(str(item["area_id"]), str(item["name"]), polygon(item["vertices"]))
            for item in payload.get("areas", [])
        )
        terrain = tuple(
            TerrainZone(
                str(item["terrain_id"]), str(item["name"]), polygon(item["vertices"]),
                float(item.get("speed_multiplier", 1.0))
            )
            for item in payload.get("terrain_zones", [])
        )
        obstacles = tuple(
            ObstacleZone(
                str(item["obstacle_id"]), str(item["name"]), polygon(item["vertices"]),
                str(item.get("kind", "terrain"))
            )
            for item in payload.get("obstacles", [])
        )
        roads = tuple(
            RoadZone(
                str(item["road_id"]), str(item["name"]), polygon(item["vertices"]),
                float(item.get("speed_multiplier", 1.5))
            )
            for item in payload.get("roads", [])
        )
        bounds_raw = payload.get("walkable_bounds")
        bounds = polygon(bounds_raw) if bounds_raw is not None else None
        return WorldMap(
            cell_size_m=float(payload.get("cell_size_m", 250.0)),
            areas=areas,
            terrain_zones=terrain,
            obstacles=obstacles,
            roads=roads,
            walkable_bounds=bounds,
            max_route_nodes=int(payload.get("max_route_nodes", 100_000)),
        )
    except (KeyError, TypeError, ValueError, IndexError, OverflowError) as exc:
        raise ValueError(f"Invalid world map definition: {exc}") from exc
