import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS worlds (
  id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, canon_text TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS entities (
  id TEXT PRIMARY KEY, world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
  name TEXT NOT NULL, kind TEXT NOT NULL, profile TEXT NOT NULL DEFAULT '',
  canonical_status TEXT NOT NULL DEFAULT 'confirmed', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(world_id, name)
);
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY, world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
  name TEXT NOT NULL, day INTEGER NOT NULL DEFAULT 1 CHECK(day >= 1),
  minute_of_day INTEGER NOT NULL DEFAULT 480 CHECK(minute_of_day BETWEEN 0 AND 1439),
  current_location TEXT NOT NULL DEFAULT 'Lugar desconocido', protagonist_entity_id TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS session_presence (
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  location TEXT NOT NULL DEFAULT '', presence_status TEXT NOT NULL DEFAULT 'present',
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(session_id, entity_id)
);
CREATE TABLE IF NOT EXISTS lore_entries (
  id TEXT PRIMARY KEY, world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
  external_uid TEXT NOT NULL, title TEXT NOT NULL, keywords_json TEXT NOT NULL DEFAULT '[]',
  content TEXT NOT NULL, priority INTEGER NOT NULL DEFAULT 100, canon_status TEXT NOT NULL DEFAULT 'confirmed',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(world_id, external_uid)
);
CREATE TABLE IF NOT EXISTS messages (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  turn_id TEXT NOT NULL, client_request_id TEXT, turn_index INTEGER NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
  recipient_entity_id TEXT NOT NULL DEFAULT '', content TEXT NOT NULL, provider TEXT NOT NULL DEFAULT 'mock',
  generation_status TEXT NOT NULL DEFAULT 'complete', metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(session_id, turn_id, role)
);
CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  turn_id TEXT NOT NULL, external_ref TEXT NOT NULL, kind TEXT NOT NULL, entity_id TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL, witnesses_json TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL CHECK(status IN ('recorded','pending','rejected')),
  source_message_id TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id, turn_id, external_ref)
);
CREATE TABLE IF NOT EXISTS state_changes (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  turn_id TEXT NOT NULL, external_ref TEXT NOT NULL, entity_id TEXT NOT NULL DEFAULT '',
  field TEXT NOT NULL, operation TEXT NOT NULL, old_value_json TEXT, proposed_value_json TEXT NOT NULL,
  accepted_value_json TEXT, status TEXT NOT NULL CHECK(status IN ('accepted','pending','rejected')),
  reason TEXT NOT NULL DEFAULT '', source_event_id TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  applied_at TEXT, UNIQUE(session_id, turn_id, external_ref)
);
CREATE TABLE IF NOT EXISTS relationships (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  from_entity_id TEXT NOT NULL, to_entity_id TEXT NOT NULL, axis TEXT NOT NULL, value REAL,
  last_change_event_id TEXT, reason TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id, from_entity_id, to_entity_id, axis)
);
CREATE TABLE IF NOT EXISTS inventory_items (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  item_key TEXT NOT NULL, display_name TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity >= 0),
  condition TEXT NOT NULL DEFAULT 'normal', carrier_entity_id TEXT NOT NULL DEFAULT '',
  location TEXT NOT NULL DEFAULT '', properties_json TEXT NOT NULL DEFAULT '{}', last_event_id TEXT,
  UNIQUE(session_id, item_key)
);
CREATE TABLE IF NOT EXISTS ability_uses (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  turn_id TEXT NOT NULL, ability_key TEXT NOT NULL, target_entity_id TEXT NOT NULL,
  result TEXT NOT NULL, cost_applied INTEGER NOT NULL DEFAULT 1, event_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id, turn_id, ability_key, target_entity_id)
);
CREATE TABLE IF NOT EXISTS snapshots (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  event_sequence INTEGER NOT NULL, state_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_messages_session_turn ON messages(session_id, turn_index);
CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_client_request ON messages(session_id, client_request_id, role) WHERE client_request_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_changes_pending ON state_changes(session_id, status);
CREATE INDEX IF NOT EXISTS idx_lore_world_priority ON lore_entries(world_id, priority);
"""


class Database:
    def __init__(self, path: str):
        self.path = Path(path).expanduser()

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.path), timeout=20, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 20000")
        return conn

    def initialize(self) -> None:
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.executescript(SCHEMA)
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(messages)").fetchall()}
            if "client_request_id" not in columns:
                conn.execute("ALTER TABLE messages ADD COLUMN client_request_id TEXT")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_client_request ON messages(session_id, client_request_id, role) WHERE client_request_id IS NOT NULL")

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def backup_to(self, destination: str) -> None:
        target = Path(destination).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as source:
            with sqlite3.connect(str(target)) as backup:
                source.backup(backup)
