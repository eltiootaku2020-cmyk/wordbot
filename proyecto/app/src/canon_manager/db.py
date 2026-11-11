import os
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
  continuity INTEGER NOT NULL DEFAULT 0 CHECK(continuity IN (0,1)),
  importance INTEGER NOT NULL DEFAULT 1 CHECK(importance BETWEEN 1 AND 5),
  status TEXT NOT NULL CHECK(status IN ('recorded','pending','rejected')),
  source_message_id TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id, turn_id, external_ref)
);
CREATE TABLE IF NOT EXISTS session_knowledge_transmissions (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  request_id TEXT NOT NULL,
  source_event_id TEXT NOT NULL REFERENCES events(id) ON DELETE RESTRICT,
  communication_event_id TEXT NOT NULL REFERENCES events(id) ON DELETE RESTRICT,
  sender_entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  recipient_entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  transmission_kind TEXT NOT NULL CHECK(transmission_kind IN ('testimony','rumor')),
  version_text TEXT NOT NULL CHECK(length(trim(version_text)) BETWEEN 1 AND 600),
  location TEXT NOT NULL CHECK(length(trim(location)) > 0),
  transmitted_total_minutes INTEGER NOT NULL CHECK(transmitted_total_minutes >= 0),
  parent_transmission_id TEXT NOT NULL DEFAULT '',
  parent_correction_id TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id, request_id),
  UNIQUE(session_id, communication_event_id, recipient_entity_id),
  CHECK(sender_entity_id <> recipient_entity_id),
  CHECK(source_event_id <> communication_event_id)
);
CREATE INDEX IF NOT EXISTS idx_knowledge_transmissions_incoming
  ON session_knowledge_transmissions(session_id,recipient_entity_id,transmitted_total_minutes);
CREATE INDEX IF NOT EXISTS idx_knowledge_transmissions_parent_correction
  ON session_knowledge_transmissions(session_id,parent_correction_id)
  WHERE parent_correction_id<>'';
CREATE TABLE IF NOT EXISTS session_knowledge_assessments (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  request_id TEXT NOT NULL,
  transmission_id TEXT NOT NULL REFERENCES session_knowledge_transmissions(id) ON DELETE RESTRICT,
  assessor_entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  stance TEXT NOT NULL CHECK(stance IN ('believes','uncertain','doubts','contradicts')),
  confidence INTEGER NOT NULL CHECK(confidence BETWEEN 0 AND 100),
  evidence_report_id TEXT NOT NULL DEFAULT '',
  evidence_event_id TEXT NOT NULL DEFAULT '',
  rationale TEXT NOT NULL CHECK(length(trim(rationale)) BETWEEN 1 AND 600),
  assessed_total_minutes INTEGER NOT NULL CHECK(assessed_total_minutes >= 0),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id, request_id),
  CHECK((evidence_report_id <> '' AND evidence_event_id = '') OR
        (evidence_report_id = '' AND evidence_event_id <> ''))
);
CREATE INDEX IF NOT EXISTS idx_knowledge_assessments_by_report
  ON session_knowledge_assessments(session_id,assessor_entity_id,transmission_id,assessed_total_minutes);
CREATE TABLE IF NOT EXISTS session_knowledge_corrections (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  request_id TEXT NOT NULL,
  original_transmission_id TEXT NOT NULL REFERENCES session_knowledge_transmissions(id) ON DELETE RESTRICT,
  parent_correction_id TEXT REFERENCES session_knowledge_corrections(id) ON DELETE RESTRICT,
  correction_event_id TEXT NOT NULL REFERENCES events(id) ON DELETE RESTRICT,
  sender_entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  recipient_entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  correction_kind TEXT NOT NULL CHECK(correction_kind IN ('corrected','retracted')),
  replacement_text TEXT NOT NULL DEFAULT '',
  rationale TEXT NOT NULL CHECK(length(trim(rationale)) BETWEEN 1 AND 600),
  location TEXT NOT NULL CHECK(length(trim(location)) > 0),
  corrected_total_minutes INTEGER NOT NULL CHECK(corrected_total_minutes >= 0),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id, request_id),
  CHECK(sender_entity_id <> recipient_entity_id),
  CHECK((correction_kind='corrected' AND length(trim(replacement_text)) BETWEEN 1 AND 600) OR
        (correction_kind='retracted' AND replacement_text=''))
);
CREATE INDEX IF NOT EXISTS idx_knowledge_corrections_by_recipient
  ON session_knowledge_corrections(session_id,recipient_entity_id,corrected_total_minutes);
CREATE TABLE IF NOT EXISTS session_environment_observations (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  request_id TEXT NOT NULL,
  observer_entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  location TEXT NOT NULL CHECK(length(trim(location)) > 0),
  observation_kind TEXT NOT NULL CHECK(observation_kind IN ('weather','local_safety')),
  value_key TEXT NOT NULL CHECK(length(value_key) BETWEEN 1 AND 40),
  details TEXT NOT NULL DEFAULT '',
  observed_total_minutes INTEGER NOT NULL CHECK(observed_total_minutes >= 0),
  valid_until_total_minutes INTEGER NOT NULL CHECK(valid_until_total_minutes > observed_total_minutes),
  source_event_id TEXT NOT NULL REFERENCES events(id) ON DELETE RESTRICT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id, request_id)
);
CREATE INDEX IF NOT EXISTS idx_environment_observations_active
  ON session_environment_observations(session_id,observer_entity_id,location,observation_kind,observed_total_minutes);
CREATE TABLE IF NOT EXISTS world_timeline_events (
  id TEXT PRIMARY KEY, world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
  external_uid TEXT NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL,
  scheduled_day INTEGER NOT NULL CHECK(scheduled_day >= 1),
  scheduled_minute INTEGER NOT NULL CHECK(scheduled_minute BETWEEN 0 AND 1439),
  location TEXT NOT NULL DEFAULT '', canon_status TEXT NOT NULL DEFAULT 'confirmed'
    CHECK(canon_status IN ('confirmed','pending','rejected')),
  enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(world_id, external_uid)
);
CREATE TABLE IF NOT EXISTS session_timeline_events (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  world_event_id TEXT NOT NULL REFERENCES world_timeline_events(id) ON DELETE CASCADE,
  scheduled_total_minutes INTEGER NOT NULL, fired_total_minutes INTEGER NOT NULL,
  fired_day INTEGER NOT NULL, fired_minute INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id, world_event_id)
);
CREATE INDEX IF NOT EXISTS idx_world_timeline_due
  ON world_timeline_events(world_id, enabled, canon_status, scheduled_day, scheduled_minute);
CREATE INDEX IF NOT EXISTS idx_session_timeline_fired
  ON session_timeline_events(session_id, fired_total_minutes);
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
CREATE TABLE IF NOT EXISTS session_map_states (
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  region_id TEXT NOT NULL CHECK(length(region_id) > 0),
  x_m REAL NOT NULL,
  y_m REAL NOT NULL,
  cell_size_m REAL NOT NULL CHECK(cell_size_m > 0),
  coordinate_system TEXT NOT NULL DEFAULT 'local_cartesian_m_v1',
  exploration_json TEXT NOT NULL DEFAULT '{"discovered_cells":[]}',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK(schema_version >= 1),
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(session_id, region_id)
);
CREATE TABLE IF NOT EXISTS world_map_regions (
  world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
  region_id TEXT NOT NULL CHECK(length(region_id) > 0),
  map_json TEXT NOT NULL,
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK(schema_version >= 1),
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(world_id, region_id)
);
CREATE TABLE IF NOT EXISTS session_travel_states (
  session_id TEXT PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
  region_id TEXT NOT NULL CHECK(length(region_id) > 0),
  route_json TEXT NOT NULL,
  next_waypoint_index INTEGER NOT NULL DEFAULT 1 CHECK(next_waypoint_index >= 1),
  destination_x_m REAL NOT NULL,
  destination_y_m REAL NOT NULL,
  destination_label TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL CHECK(status IN ('running','paused','completed','cancelled')),
  elapsed_seconds INTEGER NOT NULL DEFAULT 0 CHECK(elapsed_seconds >= 0),
  clock_minutes_applied INTEGER NOT NULL DEFAULT 0 CHECK(clock_minutes_applied >= 0),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS session_travel_steps (
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  request_id TEXT NOT NULL CHECK(length(request_id) BETWEEN 8 AND 120),
  result_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(session_id, request_id)
);
CREATE TABLE IF NOT EXISTS world_behavior_catalogs (
  world_id TEXT PRIMARY KEY REFERENCES worlds(id) ON DELETE CASCADE,
  catalog_json TEXT NOT NULL,
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK(schema_version >= 1),
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS session_entity_behavior_profiles (
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  profile_json TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(session_id, entity_id)
);
CREATE TABLE IF NOT EXISTS session_entity_agendas (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  request_id TEXT NOT NULL CHECK(length(request_id) BETWEEN 8 AND 120),
  action_id TEXT NOT NULL,
  action_json TEXT NOT NULL,
  patterns_json TEXT NOT NULL DEFAULT '[]',
  context_json TEXT NOT NULL DEFAULT '{}',
  scheduled_total_minutes INTEGER NOT NULL CHECK(scheduled_total_minutes >= 0),
  duration_minutes INTEGER NOT NULL CHECK(duration_minutes BETWEEN 1 AND 10080),
  priority REAL NOT NULL DEFAULT 50 CHECK(priority BETWEEN 0 AND 100),
  target_entity_id TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL CHECK(status IN ('scheduled','running','completed','cancelled','blocked')),
  result_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id, request_id)
);
CREATE INDEX IF NOT EXISTS idx_session_agendas_due
  ON session_entity_agendas(session_id,status,scheduled_total_minutes,priority);
CREATE INDEX IF NOT EXISTS idx_session_agendas_entity
  ON session_entity_agendas(session_id,entity_id,status,scheduled_total_minutes);
CREATE TABLE IF NOT EXISTS behavior_action_executions (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  agenda_id TEXT NOT NULL,
  entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  action_id TEXT NOT NULL,
  started_total_minutes INTEGER NOT NULL,
  completed_total_minutes INTEGER NOT NULL,
  result_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id,agenda_id)
);
CREATE INDEX IF NOT EXISTS idx_behavior_executions_entity
  ON behavior_action_executions(session_id,entity_id,completed_total_minutes);
CREATE INDEX IF NOT EXISTS idx_behavior_profiles_entity ON session_entity_behavior_profiles(entity_id);
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

            # PR #56 used one row per original report. Rebuild that table in place
            # so existing local databases gain an append-only correction chain
            # without losing their already-approved correction records.
            correction_columns = {
                row["name"] for row in conn.execute(
                    "PRAGMA table_info(session_knowledge_corrections)"
                ).fetchall()
            }
            if "parent_correction_id" not in correction_columns:
                conn.execute("BEGIN IMMEDIATE")
                try:
                    conn.execute("""
                        CREATE TABLE session_knowledge_corrections_v2 (
                            id TEXT PRIMARY KEY,
                            session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                            request_id TEXT NOT NULL,
                            original_transmission_id TEXT NOT NULL REFERENCES session_knowledge_transmissions(id) ON DELETE RESTRICT,
                            parent_correction_id TEXT REFERENCES session_knowledge_corrections_v2(id) ON DELETE RESTRICT,
                            correction_event_id TEXT NOT NULL REFERENCES events(id) ON DELETE RESTRICT,
                            sender_entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
                            recipient_entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
                            correction_kind TEXT NOT NULL CHECK(correction_kind IN ('corrected','retracted')),
                            replacement_text TEXT NOT NULL DEFAULT '',
                            rationale TEXT NOT NULL CHECK(length(trim(rationale)) BETWEEN 1 AND 600),
                            location TEXT NOT NULL CHECK(length(trim(location)) > 0),
                            corrected_total_minutes INTEGER NOT NULL CHECK(corrected_total_minutes >= 0),
                            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(session_id, request_id),
                            CHECK(sender_entity_id <> recipient_entity_id),
                            CHECK((correction_kind='corrected' AND length(trim(replacement_text)) BETWEEN 1 AND 600) OR
                                  (correction_kind='retracted' AND replacement_text=''))
                        )
                    """)
                    conn.execute("""
                        INSERT INTO session_knowledge_corrections_v2(
                            id,session_id,request_id,original_transmission_id,parent_correction_id,
                            correction_event_id,sender_entity_id,recipient_entity_id,correction_kind,
                            replacement_text,rationale,location,corrected_total_minutes,created_at
                        )
                        SELECT id,session_id,request_id,original_transmission_id,NULL,
                               correction_event_id,sender_entity_id,recipient_entity_id,correction_kind,
                               replacement_text,rationale,location,corrected_total_minutes,created_at
                        FROM session_knowledge_corrections
                    """)
                    conn.execute("DROP TABLE session_knowledge_corrections")
                    conn.execute(
                        "ALTER TABLE session_knowledge_corrections_v2 "
                        "RENAME TO session_knowledge_corrections"
                    )
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise

            transmission_columns = {
                row["name"] for row in conn.execute(
                    "PRAGMA table_info(session_knowledge_transmissions)"
                ).fetchall()
            }
            if "parent_correction_id" not in transmission_columns:
                conn.execute(
                    "ALTER TABLE session_knowledge_transmissions "
                    "ADD COLUMN parent_correction_id TEXT NOT NULL DEFAULT ''"
                )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_knowledge_transmissions_parent_correction "
                "ON session_knowledge_transmissions(session_id,parent_correction_id) "
                "WHERE parent_correction_id<>''"
            )

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_knowledge_corrections_by_recipient "
                "ON session_knowledge_corrections(session_id,recipient_entity_id,corrected_total_minutes)"
            )
            # One root and at most one successor per version enforce a single,
            # unambiguous chain while preserving every previous version.
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_knowledge_corrections_root "
                "ON session_knowledge_corrections(session_id,original_transmission_id) "
                "WHERE parent_correction_id IS NULL"
            )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_knowledge_corrections_child "
                "ON session_knowledge_corrections(session_id,parent_correction_id) "
                "WHERE parent_correction_id IS NOT NULL"
            )

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

            event_columns = {row["name"] for row in conn.execute("PRAGMA table_info(events)").fetchall()}
            if "continuity" not in event_columns:
                conn.execute("ALTER TABLE events ADD COLUMN continuity INTEGER NOT NULL DEFAULT 0")
            if "importance" not in event_columns:
                conn.execute("ALTER TABLE events ADD COLUMN importance INTEGER NOT NULL DEFAULT 1")

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
