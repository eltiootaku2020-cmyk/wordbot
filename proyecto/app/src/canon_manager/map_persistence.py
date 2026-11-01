"""SQLite persistence for a session's geometric map and fog of war."""
from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from .db import Database
from .world_map import ExplorationState, Point, WorldMap


CURRENT_MAP_SAVE_VERSION = 1
COORDINATE_SYSTEM = "local_cartesian_m_v1"


@dataclass(frozen=True, slots=True)
class SavedMapState:
    """The map data required to resume exploration without changing its scale."""

    position: Point
    cell_size_m: float
    exploration: ExplorationState
    coordinate_system: str = COORDINATE_SYSTEM
    schema_version: int = CURRENT_MAP_SAVE_VERSION


def _validate_key(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


def save_map_state(
    database: Database,
    session_id: str,
    region_id: str,
    position: Point,
    exploration: ExplorationState,
    *,
    cell_size_m: float,
) -> None:
    """Atomically insert/update a region's position and exploration for a session."""
    _validate_key(session_id, "session_id")
    _validate_key(region_id, "region_id")
    if not isinstance(position, Point):
        raise TypeError("position must be a Point")
    if not isinstance(exploration, ExplorationState):
        raise TypeError("exploration must be an ExplorationState")

    # Reuse the map's validation so persistence cannot accept a scale the engine rejects.
    WorldMap(cell_size_m=cell_size_m)
    encoded_exploration = exploration.to_json()

    with database.transaction() as conn:
        conn.execute(
            """
            INSERT INTO session_map_states (
                session_id, region_id, x_m, y_m, cell_size_m,
                coordinate_system, exploration_json, schema_version, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(session_id, region_id) DO UPDATE SET
                x_m = excluded.x_m,
                y_m = excluded.y_m,
                cell_size_m = excluded.cell_size_m,
                coordinate_system = excluded.coordinate_system,
                exploration_json = excluded.exploration_json,
                schema_version = excluded.schema_version,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                session_id,
                region_id,
                position.x_m,
                position.y_m,
                cell_size_m,
                COORDINATE_SYSTEM,
                encoded_exploration,
                CURRENT_MAP_SAVE_VERSION,
            ),
        )


def load_map_state(
    database: Database, session_id: str, region_id: str
) -> SavedMapState | None:
    """Load the saved region state, or return None when it has never been saved."""
    _validate_key(session_id, "session_id")
    _validate_key(region_id, "region_id")

    with database.connection() as conn:
        row = conn.execute(
            """
            SELECT x_m, y_m, cell_size_m, coordinate_system,
                   exploration_json, schema_version
            FROM session_map_states
            WHERE session_id = ? AND region_id = ?
            """,
            (session_id, region_id),
        ).fetchone()

    if row is None:
        return None

    version = int(row["schema_version"])
    if version != CURRENT_MAP_SAVE_VERSION:
        raise ValueError(
            f"Unsupported map save version {version}; "
            f"expected {CURRENT_MAP_SAVE_VERSION}"
        )
    coordinate_system = str(row["coordinate_system"])
    if coordinate_system != COORDINATE_SYSTEM:
        raise ValueError(f"Unsupported coordinate system: {coordinate_system!r}")

    cell_size_m = float(row["cell_size_m"])
    WorldMap(cell_size_m=cell_size_m)
    position = Point(float(row["x_m"]), float(row["y_m"]))
    exploration = ExplorationState.from_json(str(row["exploration_json"]))

    return SavedMapState(
        position=position,
        cell_size_m=cell_size_m,
        exploration=exploration,
        coordinate_system=coordinate_system,
        schema_version=version,
    )
