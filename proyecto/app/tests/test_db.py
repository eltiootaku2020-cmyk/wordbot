from pathlib import Path
import sqlite3

from canon_manager.db import Database


def test_database_persists_and_backups(tmp_path: Path):
    db = Database(str(tmp_path / "data" / "canon.sqlite3"))
    db.initialize()
    with db.transaction() as conn:
        conn.execute(
            "INSERT INTO worlds(id,name,canon_text) VALUES(?,?,?)",
            ("world-test", "Test World", "Canon fixed")
        )
    with db.connection() as conn:
        row = conn.execute("SELECT name,canon_text FROM worlds WHERE id='world-test'").fetchone()
        assert row["name"] == "Test World"
        assert row["canon_text"] == "Canon fixed"
    backup = tmp_path / "backup.sqlite3"
    db.backup_to(str(backup))
    assert backup.exists()
    backup_db = Database(str(backup))
    with backup_db.connection() as conn:
        row = conn.execute("SELECT name FROM worlds WHERE id='world-test'").fetchone()
        assert row["name"] == "Test World"



def test_database_migrates_legacy_messages_table(tmp_path: Path):
    path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE messages(id TEXT PRIMARY KEY, session_id TEXT, turn_id TEXT, turn_index INTEGER, role TEXT)"
        )
    db = Database(str(path))
    db.initialize()
    with db.connection() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(messages)").fetchall()}
    assert "client_request_id" in columns



def test_database_migrates_legacy_presence_table_and_normalizes_status(tmp_path: Path):
    path = tmp_path / "legacy-presence.sqlite3"
    with sqlite3.connect(path) as conn:
        # A pre-presence-status database. Keep the parent tables sufficiently
        # complete for the current schema to initialize around this old table.
        conn.executescript("""
            CREATE TABLE worlds (
                id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE,
                canon_text TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE entities (
                id TEXT PRIMARY KEY, world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
                name TEXT NOT NULL, kind TEXT NOT NULL, profile TEXT NOT NULL DEFAULT '',
                canonical_status TEXT NOT NULL DEFAULT 'confirmed',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(world_id, name)
            );
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY, world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
                name TEXT NOT NULL, day INTEGER NOT NULL DEFAULT 1,
                minute_of_day INTEGER NOT NULL DEFAULT 480,
                current_location TEXT NOT NULL DEFAULT 'Lugar desconocido',
                protagonist_entity_id TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE session_presence (
                session_id TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                location TEXT NOT NULL DEFAULT '',
                PRIMARY KEY(session_id, entity_id)
            );
            INSERT INTO worlds(id,name,canon_text) VALUES('world-old','World old','');
            INSERT INTO entities(id,world_id,name,kind) VALUES
                ('hero-old','world-old','Protagonista','protagonist'),
                ('npc-old','world-old','Ivar','character');
            INSERT INTO sessions(id,world_id,name,current_location,protagonist_entity_id)
                VALUES('session-old','world-old','Partida antigua','Claro','hero-old');
            INSERT INTO session_presence(session_id,entity_id,location) VALUES
                ('session-old','hero-old','Claro'),
                ('session-old','npc-old','Brumaclara');
        """)

    db = Database(str(path))
    db.initialize()
    with db.connection() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(session_presence)").fetchall()}
        assert {"presence_status", "updated_at"}.issubset(columns)
        rows = {
            row["entity_id"]: dict(row)
            for row in conn.execute(
                "SELECT entity_id,location,presence_status,updated_at "
                "FROM session_presence WHERE session_id='session-old'"
            ).fetchall()
        }
        assert rows["hero-old"]["location"] == "Claro"
        assert rows["hero-old"]["presence_status"] == "present"
        assert rows["npc-old"]["location"] == "Brumaclara"
        assert rows["npc-old"]["presence_status"] == "away"
        assert rows["hero-old"]["updated_at"]
        assert rows["npc-old"]["updated_at"]

    # Existing databases can also contain a stale status from an older version.
    with db.transaction() as conn:
        conn.execute(
            "UPDATE session_presence SET presence_status='present' "
            "WHERE session_id='session-old' AND entity_id='npc-old'"
        )
    db.initialize()
    with db.connection() as conn:
        row = conn.execute(
            "SELECT location,presence_status FROM session_presence "
            "WHERE session_id='session-old' AND entity_id='npc-old'"
        ).fetchone()
    assert row["location"] == "Brumaclara"
    assert row["presence_status"] == "away"


def test_failed_backup_removes_temporary_archive(tmp_path: Path, monkeypatch):
    import pytest

    db = Database(str(tmp_path / "source.sqlite3"))
    db.initialize()

    class BrokenSource:
        def backup(self, destination):
            raise RuntimeError("simulated backup failure")

        def close(self):
            pass

    monkeypatch.setattr(db, "_connect", lambda: BrokenSource())
    target = tmp_path / "failed.sqlite3"

    with pytest.raises(RuntimeError, match="simulated backup failure"):
        db.backup_to(str(target))

    assert not target.exists()
    assert not target.with_name(target.name + ".tmp").exists()
