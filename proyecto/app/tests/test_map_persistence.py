from pathlib import Path
import sqlite3

import pytest

from canon_manager.db import Database
from canon_manager.map_persistence import load_map_state, save_map_state
from canon_manager.world_map import ExplorationState, Point


def _create_session(db: Database, session_id: str = "session-map") -> None:
    with db.transaction() as conn:
        conn.execute(
            "INSERT INTO worlds(id,name,canon_text) VALUES(?,?,?)",
            ("world-map", "Map world", ""),
        )
        conn.execute(
            "INSERT INTO entities(id,world_id,name,kind) VALUES(?,?,?,?)",
            ("hero-map", "world-map", "Protagonist", "protagonist"),
        )
        conn.execute(
            """
            INSERT INTO sessions(
                id,world_id,name,day,minute_of_day,current_location,protagonist_entity_id
            ) VALUES(?,?,?,?,?,?,?)
            """,
            (session_id, "world-map", "Exploration", 1, 480, "Forest", "hero-map"),
        )


def test_map_state_round_trips_position_scale_and_discovery(tmp_path: Path) -> None:
    db = Database(str(tmp_path / "map.sqlite3"))
    db.initialize()
    _create_session(db)

    exploration = ExplorationState({(0, 0), (1, 0), (1, 1), (-2, 3)})
    save_map_state(
        db,
        "session-map",
        "beast-forest",
        Point(-375.5, 812.25),
        exploration,
        cell_size_m=125,
    )

    loaded = load_map_state(db, "session-map", "beast-forest")

    assert loaded is not None
    assert loaded.position == Point(-375.5, 812.25)
    assert loaded.cell_size_m == 125
    assert loaded.exploration.discovered_cells == exploration.discovered_cells
    assert loaded.coordinate_system == "local_cartesian_m_v1"
    assert loaded.schema_version == 1


def test_map_state_upsert_does_not_duplicate_and_replaces_current_state(
    tmp_path: Path,
) -> None:
    db = Database(str(tmp_path / "map-upsert.sqlite3"))
    db.initialize()
    _create_session(db)

    save_map_state(
        db, "session-map", "forest", Point(10, 20),
        ExplorationState({(0, 0)}), cell_size_m=250
    )
    save_map_state(
        db, "session-map", "forest", Point(510, 20),
        ExplorationState({(0, 0), (1, 0), (2, 0)}), cell_size_m=250
    )

    loaded = load_map_state(db, "session-map", "forest")
    with db.connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS count FROM session_map_states "
            "WHERE session_id=? AND region_id=?",
            ("session-map", "forest"),
        ).fetchone()["count"]

    assert count == 1
    assert loaded is not None
    assert loaded.position == Point(510, 20)
    assert loaded.exploration.discovered_cells == {(0, 0), (1, 0), (2, 0)}


def test_map_state_keeps_regions_separate(tmp_path: Path) -> None:
    db = Database(str(tmp_path / "map-regions.sqlite3"))
    db.initialize()
    _create_session(db)

    save_map_state(
        db, "session-map", "forest", Point(50, 75),
        ExplorationState({(1, 1)}), cell_size_m=250
    )
    save_map_state(
        db, "session-map", "village", Point(0, 0),
        ExplorationState({(0, 0), (0, 1)}), cell_size_m=100
    )

    forest = load_map_state(db, "session-map", "forest")
    village = load_map_state(db, "session-map", "village")

    assert forest is not None and village is not None
    assert forest.cell_size_m == 250
    assert forest.exploration.discovered_cells == {(1, 1)}
    assert village.cell_size_m == 100
    assert village.exploration.discovered_cells == {(0, 0), (0, 1)}


def test_map_state_returns_none_before_first_save(tmp_path: Path) -> None:
    db = Database(str(tmp_path / "map-empty.sqlite3"))
    db.initialize()
    _create_session(db)

    assert load_map_state(db, "session-map", "forest") is None


def test_map_state_rejects_unknown_session_through_foreign_key(tmp_path: Path) -> None:
    db = Database(str(tmp_path / "map-fk.sqlite3"))
    db.initialize()

    with pytest.raises(sqlite3.IntegrityError):
        save_map_state(
            db, "missing-session", "forest", Point(0, 0),
            ExplorationState(), cell_size_m=250
        )


def test_map_state_cascades_when_session_is_deleted(tmp_path: Path) -> None:
    db = Database(str(tmp_path / "map-cascade.sqlite3"))
    db.initialize()
    _create_session(db)
    save_map_state(
        db, "session-map", "forest", Point(100, 200),
        ExplorationState({(0, 0)}), cell_size_m=250
    )

    with db.transaction() as conn:
        conn.execute("DELETE FROM sessions WHERE id=?", ("session-map",))

    with db.connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS count FROM session_map_states"
        ).fetchone()["count"]
    assert count == 0


def test_map_state_rejects_unknown_schema_version(tmp_path: Path) -> None:
    db = Database(str(tmp_path / "map-version.sqlite3"))
    db.initialize()
    _create_session(db)
    save_map_state(
        db, "session-map", "forest", Point(0, 0),
        ExplorationState(), cell_size_m=250
    )
    with db.transaction() as conn:
        conn.execute(
            "UPDATE session_map_states SET schema_version=99 "
            "WHERE session_id=? AND region_id=?",
            ("session-map", "forest"),
        )

    with pytest.raises(ValueError, match="Unsupported map save version"):
        load_map_state(db, "session-map", "forest")
