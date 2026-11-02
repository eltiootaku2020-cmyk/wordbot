"""Persistence and preview orchestration for per-entity NPC behavior profiles."""
from __future__ import annotations

import json
from typing import Any, Mapping

from .db import Database
from .behavior_engine import (
    DEFAULT_ACTIONS,
    DEFAULT_PATTERNS,
    MAX_ACTIONS,
    MAX_PATTERNS,
    BehaviorValidationError,
    rank_actions,
    rank_focuses,
    validate_action,
    validate_pattern,
    validate_profile,
)


class BehaviorEntityNotFoundError(LookupError):
    """The entity does not belong to the requested session's world."""


class BehaviorProfileNotFoundError(LookupError):
    """No behavior profile has been configured for this entity in the session."""


def _entity_in_session(conn, session_id: str, entity_id: str):
    row = conn.execute(
        "SELECT s.world_id,e.id,e.name,e.kind,e.profile FROM sessions s "
        "JOIN entities e ON e.world_id=s.world_id "
        "WHERE s.id=? AND e.id=?",
        (session_id, entity_id),
    ).fetchone()
    if row is None:
        session = conn.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone()
        if session is None:
            raise BehaviorEntityNotFoundError("La partida no existe.")
        raise BehaviorEntityNotFoundError("La entidad no pertenece al mundo de esta partida.")
    return row


def _live_relationships(conn, session_id: str, entity_id: str) -> dict[str, dict[str, float | None]]:
    rows = conn.execute(
        "SELECT to_entity_id,axis,value FROM relationships "
        "WHERE session_id=? AND from_entity_id=? ORDER BY to_entity_id,axis",
        (session_id, entity_id),
    ).fetchall()
    relationships: dict[str, dict[str, float | None]] = {}
    for row in rows:
        target = str(row["to_entity_id"])
        relationships.setdefault(target, {})[str(row["axis"])] = (
            None if row["value"] is None else float(row["value"])
        )
    return relationships


def _validate_custom_catalog(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise BehaviorValidationError("catalog must be an object")
    if set(payload) - {"schema_version", "actions", "patterns"}:
        raise BehaviorValidationError("Catalog contains unsupported fields")
    if payload.get("schema_version", 1) != 1:
        raise BehaviorValidationError("Unsupported behavior catalog version")
    raw_actions = payload.get("actions", [])
    raw_patterns = payload.get("patterns", [])
    if not isinstance(raw_actions, list) or len(raw_actions) > MAX_ACTIONS:
        raise BehaviorValidationError(f"catalog.actions must contain at most {MAX_ACTIONS} entries")
    if not isinstance(raw_patterns, list) or len(raw_patterns) > MAX_PATTERNS:
        raise BehaviorValidationError(f"catalog.patterns must contain at most {MAX_PATTERNS} entries")
    actions = [validate_action(item) for item in raw_actions]
    patterns = [validate_pattern(item) for item in raw_patterns]
    action_ids = [item["action_id"] for item in actions]
    pattern_ids = [item["pattern_id"] for item in patterns]
    if len(action_ids) != len(set(action_ids)):
        raise BehaviorValidationError("Custom action ids must be unique")
    if len(pattern_ids) != len(set(pattern_ids)):
        raise BehaviorValidationError("Custom pattern ids must be unique")
    return {"schema_version": 1, "actions": actions, "patterns": patterns}


def _merge_catalog(custom: Mapping[str, Any] | None) -> dict[str, Any]:
    actions = {item["action_id"]: dict(item) for item in DEFAULT_ACTIONS}
    patterns = {item["pattern_id"]: dict(item) for item in DEFAULT_PATTERNS}
    if custom:
        for item in custom.get("actions", []):
            actions[item["action_id"]] = dict(item)
        for item in custom.get("patterns", []):
            patterns[item["pattern_id"]] = dict(item)
    return {
        "schema_version": 1,
        "actions": [actions[key] for key in sorted(actions)],
        "patterns": [patterns[key] for key in sorted(patterns)],
        "default_action_count": len(DEFAULT_ACTIONS),
        "default_pattern_count": len(DEFAULT_PATTERNS),
        "custom_action_count": len(custom.get("actions", [])) if custom else 0,
        "custom_pattern_count": len(custom.get("patterns", [])) if custom else 0,
    }


def get_world_behavior_catalog(database: Database, world_id: str) -> dict[str, Any]:
    with database.connection() as conn:
        if conn.execute("SELECT 1 FROM worlds WHERE id=?", (world_id,)).fetchone() is None:
            raise BehaviorEntityNotFoundError("El mundo no existe.")
        row = conn.execute(
            "SELECT catalog_json FROM world_behavior_catalogs WHERE world_id=?",
            (world_id,),
        ).fetchone()
        custom = json.loads(str(row["catalog_json"])) if row else None
    return _merge_catalog(custom)


def save_world_behavior_catalog(
    database: Database, world_id: str, payload: Mapping[str, Any]
) -> dict[str, Any]:
    custom = _validate_custom_catalog(payload)
    encoded = json.dumps(custom, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    with database.transaction() as conn:
        if conn.execute("SELECT 1 FROM worlds WHERE id=?", (world_id,)).fetchone() is None:
            raise BehaviorEntityNotFoundError("El mundo no existe.")
        conn.execute(
            """
            INSERT INTO world_behavior_catalogs(world_id,catalog_json,schema_version,updated_at)
            VALUES(?,?,1,CURRENT_TIMESTAMP)
            ON CONFLICT(world_id) DO UPDATE SET
                catalog_json=excluded.catalog_json,
                schema_version=excluded.schema_version,
                updated_at=CURRENT_TIMESTAMP
            """,
            (world_id, encoded),
        )
    return get_world_behavior_catalog(database, world_id)


def _profile_without_relationship_snapshot(profile: Mapping[str, Any]) -> dict[str, Any]:
    normalized = validate_profile(profile)
    # Directed relationships have their own audited SQLite table and are read
    # fresh at preview time; do not persist a stale copy inside the profile JSON.
    normalized["relationships"] = {}
    return normalized


def get_entity_behavior_profile(
    database: Database, session_id: str, entity_id: str
) -> dict[str, Any] | None:
    with database.connection() as conn:
        entity = _entity_in_session(conn, session_id, entity_id)
        row = conn.execute(
            "SELECT profile_json,updated_at FROM session_entity_behavior_profiles "
            "WHERE session_id=? AND entity_id=?",
            (session_id, entity_id),
        ).fetchone()
        if row is None:
            return None
        profile = validate_profile(json.loads(str(row["profile_json"])))
        profile["relationships"] = _live_relationships(conn, session_id, entity_id)
        return {
            "entity_id": entity_id,
            "entity_name": str(entity["name"]),
            "entity_kind": str(entity["kind"]),
            "profile": profile,
            "updated_at": str(row["updated_at"]),
        }


def save_entity_behavior_profile(
    database: Database, session_id: str, entity_id: str, profile: Mapping[str, Any]
) -> dict[str, Any]:
    normalized = _profile_without_relationship_snapshot(profile)
    encoded = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    with database.transaction() as conn:
        entity = _entity_in_session(conn, session_id, entity_id)
        conn.execute(
            """
            INSERT INTO session_entity_behavior_profiles(
                session_id,entity_id,profile_json,updated_at
            ) VALUES(?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(session_id,entity_id) DO UPDATE SET
                profile_json=excluded.profile_json,
                updated_at=CURRENT_TIMESTAMP
            """,
            (session_id, entity_id, encoded),
        )
    saved = get_entity_behavior_profile(database, session_id, entity_id)
    assert saved is not None
    return saved


def preview_entity_behavior(
    database: Database,
    session_id: str,
    entity_id: str,
    context: Mapping[str, Any] | None = None,
    *,
    limit: int = 10,
    focus_candidates: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    saved = get_entity_behavior_profile(database, session_id, entity_id)
    if saved is None:
        raise BehaviorProfileNotFoundError(
            "Este personaje todavía no tiene un perfil de conducta configurado para esta partida."
        )
    with database.connection() as conn:
        session = conn.execute(
            "SELECT world_id,day,minute_of_day,current_location FROM sessions WHERE id=?",
            (session_id,),
        ).fetchone()
        if session is None:
            raise BehaviorEntityNotFoundError("La partida no existe.")
        catalog_row = conn.execute(
            "SELECT catalog_json FROM world_behavior_catalogs WHERE world_id=?",
            (str(session["world_id"]),),
        ).fetchone()
        custom = json.loads(str(catalog_row["catalog_json"])) if catalog_row else None
    catalog = _merge_catalog(custom)
    action_context = dict(context or {})
    action_context.setdefault("world_day", int(session["day"]))
    action_context.setdefault("world_minute", int(session["minute_of_day"]))
    action_context.setdefault("location", str(session["current_location"]))
    ranked = rank_actions(
        saved["profile"],
        catalog["actions"],
        catalog["patterns"],
        context=action_context,
        limit=limit,
    )
    focus_ranking = rank_focuses(saved["profile"], focus_candidates or []) if focus_candidates else []
    return {
        "entity_id": entity_id,
        "entity_name": saved["entity_name"],
        "world_time": {
            "day": int(session["day"]),
            "minute_of_day": int(session["minute_of_day"]),
        },
        "profile_updated_at": saved["updated_at"],
        "actions": ranked,
        "focus_candidates": focus_ranking,
        "catalog": {
            "default_action_count": catalog["default_action_count"],
            "default_pattern_count": catalog["default_pattern_count"],
            "custom_action_count": catalog["custom_action_count"],
            "custom_pattern_count": catalog["custom_pattern_count"],
        },
        "side_effects_applied": False,
    }
