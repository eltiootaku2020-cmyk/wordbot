import json
import os
import sqlite3
import uuid
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
CREATE TABLE IF NOT EXISTS entity_knowledge (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  knower_entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  knowledge_kind TEXT NOT NULL CHECK(knowledge_kind IN ('direct_observation','testimony','rumor')),
  about_event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  transmission_event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  source_entity_id TEXT REFERENCES entities(id) ON DELETE SET NULL,
  source_knowledge_id TEXT REFERENCES entity_knowledge(id) ON DELETE SET NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id,knower_entity_id,knowledge_kind,about_event_id,transmission_event_id)
);
CREATE INDEX IF NOT EXISTS idx_entity_knowledge_knower_time
  ON entity_knowledge(session_id,knower_entity_id,created_at);
CREATE INDEX IF NOT EXISTS idx_entity_knowledge_source
  ON entity_knowledge(session_id,source_entity_id,about_event_id);
CREATE TABLE IF NOT EXISTS event_evidence (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  about_event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  evidence_event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  discovered_by_entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  evidence_kind TEXT NOT NULL CHECK(evidence_kind IN ('physical','testimonial','circumstantial','alibi','other')),
  effect TEXT NOT NULL CHECK(effect IN ('supports','contradicts','neutral')),
  source_knowledge_id TEXT REFERENCES entity_knowledge(id) ON DELETE SET NULL,
  source_knowledge_kind TEXT NOT NULL DEFAULT 'unknown',
  description TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('recorded','pending','rejected')),
  reason TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id,evidence_event_id,discovered_by_entity_id,about_event_id,evidence_kind)
);
CREATE INDEX IF NOT EXISTS idx_event_evidence_about
  ON event_evidence(session_id,about_event_id,status);
CREATE TABLE IF NOT EXISTS event_attributions (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  turn_id TEXT NOT NULL, external_ref TEXT NOT NULL,
  about_event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  subject_entity_id TEXT REFERENCES entities(id) ON DELETE SET NULL,
  attribution_level TEXT NOT NULL CHECK(attribution_level IN ('description','suspected','identified','confirmed')),
  description TEXT NOT NULL,
  evidence_ids_json TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL CHECK(status IN ('recorded','pending','rejected')),
  reason TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id,turn_id,external_ref)
);
CREATE INDEX IF NOT EXISTS idx_event_attributions_about
  ON event_attributions(session_id,about_event_id,status);
CREATE TABLE IF NOT EXISTS local_reputation (
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  location_key TEXT NOT NULL,
  location_label TEXT NOT NULL,
  value INTEGER NOT NULL DEFAULT 0 CHECK(value BETWEEN -100 AND 100),
  last_attribution_id TEXT REFERENCES event_attributions(id) ON DELETE SET NULL,
  last_awareness_event_id TEXT REFERENCES events(id) ON DELETE SET NULL,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(session_id,entity_id,location_key)
);
CREATE TABLE IF NOT EXISTS local_reputation_history (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  turn_id TEXT NOT NULL, external_ref TEXT NOT NULL,
  entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  location_key TEXT NOT NULL, location_label TEXT NOT NULL,
  delta INTEGER NOT NULL, old_value INTEGER NOT NULL, new_value INTEGER NOT NULL,
  attribution_id TEXT NOT NULL REFERENCES event_attributions(id) ON DELETE CASCADE,
  awareness_event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  reason TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('accepted','pending','rejected')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id,turn_id,external_ref)
);
CREATE INDEX IF NOT EXISTS idx_local_reputation_location
  ON local_reputation(session_id,location_key,value);
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
CREATE TABLE IF NOT EXISTS resources (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  resource_key TEXT NOT NULL, display_name TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity >= 0),
  unit TEXT NOT NULL DEFAULT '', last_event_id TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id, resource_key)
);
CREATE TABLE IF NOT EXISTS ability_uses (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  turn_id TEXT NOT NULL, ability_key TEXT NOT NULL, target_entity_id TEXT NOT NULL,
  result TEXT NOT NULL, cost_applied INTEGER NOT NULL DEFAULT 1, event_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id, turn_id, ability_key, target_entity_id)
);
CREATE TABLE IF NOT EXISTS app_settings (
  setting_key TEXT PRIMARY KEY, value_json TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS snapshots (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  turn_id TEXT NOT NULL DEFAULT '', event_sequence INTEGER NOT NULL,
  state_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_messages_session_turn ON messages(session_id, turn_index);
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
            snapshot_columns = {row["name"] for row in conn.execute("PRAGMA table_info(snapshots)").fetchall()}
            if "turn_id" not in snapshot_columns:
                conn.execute("ALTER TABLE snapshots ADD COLUMN turn_id TEXT NOT NULL DEFAULT ''")
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_snapshots_session_turn "
                "ON snapshots(session_id,turn_id) WHERE turn_id<>''"
            )

            # Backfill per-entity knowledge from previously recorded events.
            # Stored witness lists were already restricted to the turn's authorized audience.
            legacy_events = conn.execute(
                "SELECT id,session_id,kind,witnesses_json,description,created_at "
                "FROM events WHERE status='recorded'"
            ).fetchall()
            for event in legacy_events:
                # A report event gives listeners testimony/rumor knowledge through
                # its explicit provenance; do not also treat its claim as direct fact.
                if event["kind"] in {"testimony", "rumor"}:
                    continue
                try:
                    witnesses = json.loads(event["witnesses_json"] or "[]")
                except (TypeError, ValueError, json.JSONDecodeError):
                    continue
                if not isinstance(witnesses, list):
                    continue
                session_world = conn.execute(
                    "SELECT world_id FROM sessions WHERE id=?",
                    (event["session_id"],)
                ).fetchone()
                if session_world is None:
                    continue
                for knower_id in witnesses:
                    if not isinstance(knower_id, str) or not knower_id:
                        continue
                    known_entity = conn.execute(
                        "SELECT 1 FROM entities WHERE id=? AND world_id=?",
                        (knower_id, session_world["world_id"])
                    ).fetchone()
                    if known_entity is None:
                        continue
                    conn.execute(
                        "INSERT OR IGNORE INTO entity_knowledge("
                        "id,session_id,knower_entity_id,knowledge_kind,about_event_id,"
                        "transmission_event_id,source_entity_id,source_knowledge_id,content,created_at"
                        ") VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (
                            uuid.uuid4().hex, event["session_id"], knower_id,
                            "direct_observation", event["id"], event["id"], None, None,
                            event["description"], event["created_at"]
                        )
                    )

            # Older local databases may predate presence_status/updated_at. Add
            # these columns in place so the existing session and its cast survive.
            presence_columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(session_presence)").fetchall()
            }
            if "presence_status" not in presence_columns:
                conn.execute(
                    "ALTER TABLE session_presence ADD COLUMN presence_status TEXT NOT NULL DEFAULT 'present'"
                )
            if "updated_at" not in presence_columns:
                conn.execute(
                    "ALTER TABLE session_presence ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''"
                )

            # Location is the source of truth for presence. Historical rows may
            # contain a stale status or a defaulted 'present' from the migration.
            conn.execute(
                "UPDATE session_presence "
                "SET presence_status = CASE "
                "WHEN LOWER(location) = LOWER(COALESCE(("
                "SELECT current_location FROM sessions WHERE sessions.id=session_presence.session_id"
                "), '')) THEN 'present' ELSE 'away' END, "
                "updated_at = CASE WHEN COALESCE(updated_at, '') = '' "
                "THEN CURRENT_TIMESTAMP ELSE updated_at END "
                "WHERE session_id IN (SELECT id FROM sessions)"
            )

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
        temporary = target.with_name(target.name + ".tmp")
        temporary.unlink(missing_ok=True)
        try:
            source = self._connect()
            try:
                backup = sqlite3.connect(str(temporary))
                try:
                    source.backup(backup)
                finally:
                    # Connection context managers commit/rollback but do not close files.
                    # Close both handles explicitly before os.replace (required on Windows).
                    backup.close()
            finally:
                source.close()
            os.replace(temporary, target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
