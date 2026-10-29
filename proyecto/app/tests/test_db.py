from pathlib import Path

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
