"""Persistent, clock-driven NPC agendas and idempotent execution.

Agendas are authored/scheduled explicitly. They do not advance the world clock.
They complete only when another authoritative action advances world time past
their scheduled end. Executed effects are deliberately limited to the NPC's
own behavior profile until world-specific spatial/social effects have explicit
preconditions and evidence rules.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Mapping

from .db import Database
from .behavior_engine import (
    BehaviorValidationError,
    advance_emotions,
    rank_actions,
    validate_action,
    validate_profile,
)
from .behavior_controller import _merge_catalog


class BehaviorAgendaNotFoundError(LookupError):
    """The requested session, entity, or agenda does not exist."""


class BehaviorAgendaConflictError(RuntimeError):
    """The requested agenda conflicts with the current NPC schedule."""


class BehaviorAgendaValidationError(ValueError):
    """The proposed agenda cannot be safely scheduled or executed."""


def _total_minutes(day: int, minute: int) -> int:
    return (int(day) - 1) * 1440 + int(minute)


def _session_entity(conn, session_id: str, entity_id: str):
    row = conn.execute(
        "SELECT s.world_id,s.day,s.minute_of_day,s.current_location,"
        "e.id AS entity_id,e.name AS entity_name,e.kind AS entity_kind,p.location AS entity_location "
        "FROM sessions s JOIN entities e ON e.world_id=s.world_id "
        "LEFT JOIN session_presence p ON p.session_id=s.id AND p.entity_id=e.id "
        "WHERE s.id=? AND e.id=?",
        (session_id, entity_id),
    ).fetchone()
    if row is None:
        if conn.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone() is None:
            raise BehaviorAgendaNotFoundError("La partida no existe.")
        raise BehaviorAgendaNotFoundError("El personaje no pertenece al mundo de esta partida.")
    if str(row["entity_kind"]) == "protagonist":
        raise BehaviorAgendaConflictError(
            "El protagonista está bajo control del usuario y no puede recibir agendas autónomas."
        )
    return row


def _profile_for(conn, session_id: str, entity_id: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT profile_json FROM session_entity_behavior_profiles "
        "WHERE session_id=? AND entity_id=?",
        (session_id, entity_id),
    ).fetchone()
    if row is None:
        raise BehaviorAgendaConflictError(
            "El personaje necesita un perfil de conducta guardado antes de programar actividades."
        )
    profile = validate_profile(json.loads(str(row["profile_json"])))
    rows = conn.execute(
        "SELECT to_entity_id,axis,value FROM relationships "
        "WHERE session_id=? AND from_entity_id=? ORDER BY to_entity_id,axis",
        (session_id, entity_id),
    ).fetchall()
    relationships: dict[str, dict[str, float | None]] = {}
    for relation in rows:
        target = str(relation["to_entity_id"])
        relationships.setdefault(target, {})[str(relation["axis"])] = (
            None if relation["value"] is None else float(relation["value"])
        )
    profile["relationships"] = relationships
    return profile


def _world_catalog(conn, world_id: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT catalog_json FROM world_behavior_catalogs WHERE world_id=?",
        (world_id,),
    ).fetchone()
    custom = json.loads(str(row["catalog_json"])) if row else None
    return _merge_catalog(custom)


def _agenda_view(row, *, duplicate: bool = False) -> dict[str, Any]:
    return {
        "agenda_id": str(row["id"]),
        "session_id": str(row["session_id"]),
        "entity_id": str(row["entity_id"]),
        "request_id": str(row["request_id"]),
        "action_id": str(row["action_id"]),
        "scheduled_total_minutes": int(row["scheduled_total_minutes"]),
        "duration_minutes": int(row["duration_minutes"]),
        "priority": float(row["priority"]),
        "target_entity_id": str(row["target_entity_id"]),
        "status": str(row["status"]),
        "context": json.loads(str(row["context_json"])),
        "result": json.loads(str(row["result_json"])),
        "created_at": str(row["created_at"]),
        "updated_at": str(row["updated_at"]),
        "duplicate_request": duplicate,
    }


def schedule_behavior_agenda(
    database: Database,
    session_id: str,
    entity_id: str,
    *,
    request_id: str,
    action_id: str,
    scheduled_day: int,
    scheduled_minute: int,
    priority: float = 50,
    target_entity_id: str = "",
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create an idempotent, non-overlapping agenda entry for one NPC."""
    if not isinstance(request_id, str) or not 8 <= len(request_id.strip()) <= 120:
        raise BehaviorAgendaValidationError("request_id debe contener entre 8 y 120 caracteres.")
    if not isinstance(action_id, str) or not action_id.strip() or len(action_id) > 120:
        raise BehaviorAgendaValidationError("action_id no es válido.")
    if isinstance(scheduled_day, bool) or not isinstance(scheduled_day, int) or scheduled_day < 1:
        raise BehaviorAgendaValidationError("scheduled_day debe ser un día válido.")
    if isinstance(scheduled_minute, bool) or not isinstance(scheduled_minute, int) or not 0 <= scheduled_minute <= 1439:
        raise BehaviorAgendaValidationError("scheduled_minute debe estar entre 0 y 1439.")
    if isinstance(priority, bool) or not isinstance(priority, (int, float)) or not 0 <= float(priority) <= 100:
        raise BehaviorAgendaValidationError("priority debe estar entre 0 y 100.")
    if context is None:
        context = {}
    if not isinstance(context, Mapping):
        raise BehaviorAgendaValidationError("context debe ser un objeto.")
    if "_autonomous_plan" in context:
        raise BehaviorAgendaValidationError("context usa un campo reservado por el planificador autónomo.")
    if len(json.dumps(context, ensure_ascii=False)) > 12000:
        raise BehaviorAgendaValidationError("context supera el límite de 12000 caracteres.")

    with database.transaction() as conn:
        duplicate = conn.execute(
            "SELECT * FROM session_entity_agendas WHERE session_id=? AND request_id=?",
            (session_id, request_id.strip()),
        ).fetchone()
        if duplicate is not None:
            return _agenda_view(duplicate, duplicate=True)

        entity = _session_entity(conn, session_id, entity_id)
        current_total = _total_minutes(int(entity["day"]), int(entity["minute_of_day"]))
        scheduled_total = _total_minutes(scheduled_day, scheduled_minute)
        if scheduled_total < current_total:
            raise BehaviorAgendaConflictError("No se puede programar una actividad en el pasado.")
        if scheduled_total > current_total + 43200:
            raise BehaviorAgendaValidationError("La agenda no puede programarse a más de 30 días.")

        action_catalog = _world_catalog(conn, str(entity["world_id"]))
        action_map = {item["action_id"]: item for item in action_catalog["actions"]}
        if action_id.strip() not in action_map:
            raise BehaviorAgendaNotFoundError("La acción no existe en el catálogo de este mundo.")
        action = validate_action(action_map[action_id.strip()])
        duration = int(action["duration_minutes"])
        if duration <= 0:
            raise BehaviorAgendaValidationError(
                "La acción necesita una duración positiva para formar parte de una agenda."
            )
        if any(float(value) > 0 for value in action["resource_costs"].values()):
            raise BehaviorAgendaValidationError(
                "Esta fase no reserva recursos entre agendas; las acciones con costes quedan bloqueadas para programación."
            )

        target_id = str(target_entity_id or "").strip()
        if target_id:
            target = conn.execute(
                "SELECT id FROM entities WHERE id=? AND world_id=?",
                (target_id, str(entity["world_id"])),
            ).fetchone()
            if target is None:
                raise BehaviorAgendaNotFoundError("El objetivo no pertenece al mundo de esta partida.")

        agenda_context = dict(context)
        if target_id:
            agenda_context["target_entity_id"] = target_id
        agenda_context["available_minutes"] = duration
        agenda_context.setdefault("world_day", scheduled_day)
        agenda_context.setdefault("world_minute", scheduled_minute)
        actor_location = str(entity["entity_location"] or "").strip()
        if actor_location:
            agenda_context["location"] = actor_location
        else:
            agenda_context.pop("location", None)

        profile = _profile_for(conn, session_id, entity_id)
        possible = rank_actions(
            profile, [action], action_catalog["patterns"],
            context=agenda_context, limit=1,
        )
        if not possible:
            raise BehaviorAgendaConflictError(
                "La acción no cumple las capacidades, condiciones o necesidades registradas del personaje."
            )

        end_total = scheduled_total + duration
        overlap = conn.execute(
            "SELECT id FROM session_entity_agendas WHERE session_id=? AND entity_id=? "
            "AND status IN ('scheduled','running') "
            "AND scheduled_total_minutes < ? "
            "AND (scheduled_total_minutes + duration_minutes) > ? LIMIT 1",
            (session_id, entity_id, end_total, scheduled_total),
        ).fetchone()
        if overlap is not None:
            raise BehaviorAgendaConflictError(
                "El personaje ya tiene otra actividad programada en ese intervalo."
            )

        agenda_id = uuid.uuid4().hex
        encoded_context = json.dumps(
            agenda_context, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        encoded_action = json.dumps(
            action, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        encoded_patterns = json.dumps(
            action_catalog["patterns"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        conn.execute(
            "INSERT INTO session_entity_agendas("
            "id,session_id,entity_id,request_id,action_id,action_json,patterns_json,context_json,"
            "scheduled_total_minutes,duration_minutes,priority,target_entity_id,status,result_json"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?, 'scheduled','{}')",
            (
                agenda_id, session_id, entity_id, request_id.strip(), action["action_id"],
                encoded_action, encoded_patterns, encoded_context, scheduled_total,
                duration, float(priority), target_id,
            ),
        )
        row = conn.execute(
            "SELECT * FROM session_entity_agendas WHERE id=?", (agenda_id,)
        ).fetchone()
        return _agenda_view(row)


def list_behavior_agendas(
    database: Database, session_id: str, entity_id: str | None = None
) -> list[dict[str, Any]]:
    with database.connection() as conn:
        if conn.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone() is None:
            raise BehaviorAgendaNotFoundError("La partida no existe.")
        if entity_id:
            _session_entity(conn, session_id, entity_id)
            rows = conn.execute(
                "SELECT * FROM session_entity_agendas WHERE session_id=? AND entity_id=? "
                "ORDER BY scheduled_total_minutes,priority DESC,created_at,id",
                (session_id, entity_id),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM session_entity_agendas WHERE session_id=? "
                "ORDER BY scheduled_total_minutes,priority DESC,created_at,id",
                (session_id,),
            ).fetchall()
        return [_agenda_view(row) for row in rows]


def cancel_behavior_agenda(
    database: Database, session_id: str, agenda_id: str
) -> dict[str, Any]:
    with database.transaction() as conn:
        row = conn.execute(
            "SELECT * FROM session_entity_agendas WHERE session_id=? AND id=?",
            (session_id, agenda_id),
        ).fetchone()
        if row is None:
            raise BehaviorAgendaNotFoundError("La actividad programada no existe en esta partida.")
        status = str(row["status"])
        if status in {"scheduled", "running"}:
            conn.execute(
                "UPDATE session_entity_agendas SET status='cancelled',updated_at=CURRENT_TIMESTAMP "
                "WHERE session_id=? AND id=?",
                (session_id, agenda_id),
            )
        updated = conn.execute(
            "SELECT * FROM session_entity_agendas WHERE session_id=? AND id=?",
            (session_id, agenda_id),
        ).fetchone()
        return _agenda_view(updated)


def _apply_profile_effects(
    profile: dict[str, Any],
    effects: Mapping[str, Any],
    event_id: str,
) -> tuple[dict[str, Any], list[str]]:
    notes: list[str] = []
    for need, delta in effects.get("need_deltas", {}).items():
        current = profile["needs"].get(need)
        if current is None:
            notes.append(f"Necesidad desconocida conservada: {need}.")
            continue
        profile["needs"][need] = max(0.0, min(100.0, float(current) + float(delta)))

    for emotion in effects.get("emotions", []):
        addition = dict(emotion)
        addition["source_event_id"] = event_id
        profile["emotions"].append(addition)

    existing_goals = {goal["goal_id"]: goal for goal in profile["goals"]}
    for update in effects.get("goal_updates", []):
        goal = existing_goals.get(update["goal_id"])
        if goal is None:
            notes.append(f"Objetivo no encontrado; no se alteró: {update['goal_id']}.")
            continue
        goal["status"] = update["status"]

    if "focus" in effects:
        profile["focus"] = None if effects["focus"] is None else dict(effects["focus"])

    return validate_profile(profile), notes


def _block_agenda(conn, agenda_id: str, reason: str) -> None:
    conn.execute(
        "UPDATE session_entity_agendas SET status='blocked',result_json=?,updated_at=CURRENT_TIMESTAMP "
        "WHERE id=?",
        (json.dumps({"executed": False, "reason": reason}, ensure_ascii=False), agenda_id),
    )


def process_due_behavior_agendas(
    conn, session_id: str, previous_total_minutes: int, current_total_minutes: int
) -> dict[str, int]:
    """Advance due NPC agendas within the caller's existing clock transaction.

    This function never advances the session clock. It only completes activities
    whose scheduled end falls at or before the already-authoritative world time.
    """
    if current_total_minutes <= previous_total_minutes:
        return {"started": 0, "completed": 0, "blocked": 0}
    rows = conn.execute(
        "SELECT * FROM session_entity_agendas WHERE session_id=? "
        "AND status IN ('scheduled','running') "
        "AND scheduled_total_minutes<=? "
        "ORDER BY scheduled_total_minutes,priority DESC,created_at,id",
        (session_id, current_total_minutes),
    ).fetchall()
    stats = {"started": 0, "completed": 0, "blocked": 0}
    for row in rows:
        agenda_id = str(row["id"])
        start = int(row["scheduled_total_minutes"])
        end = start + int(row["duration_minutes"])
        if (
            str(row["status"]) == "scheduled"
            and start <= current_total_minutes
            and not _autonomous_agenda_state_matches(conn, session_id, row)
        ):
            _block_agenda(
                conn, agenda_id,
                "La actividad autónoma cambió antes de comenzar; se bloqueó sin aplicar efectos.",
            )
            stats["blocked"] += 1
            continue
        if end > current_total_minutes:
            if str(row["status"]) == "scheduled":
                conn.execute(
                    "UPDATE session_entity_agendas SET status='running',updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (agenda_id,),
                )
                stats["started"] += 1
            continue

        entity = conn.execute(
            "SELECT e.name,e.kind,s.world_id,p.location AS entity_location FROM sessions s "
            "JOIN entities e ON e.world_id=s.world_id "
            "LEFT JOIN session_presence p ON p.session_id=s.id AND p.entity_id=e.id "
            "WHERE s.id=? AND e.id=?",
            (session_id, str(row["entity_id"])),
        ).fetchone()
        if entity is None or str(entity["kind"]) == "protagonist":
            _block_agenda(conn, agenda_id, "La entidad ya no es un PNJ válido de esta partida.")
            stats["blocked"] += 1
            continue

        profile_row = conn.execute(
            "SELECT profile_json FROM session_entity_behavior_profiles "
            "WHERE session_id=? AND entity_id=?",
            (session_id, str(row["entity_id"])),
        ).fetchone()
        if profile_row is None:
            _block_agenda(conn, agenda_id, "El perfil de conducta ya no está disponible.")
            stats["blocked"] += 1
            continue

        context_snapshot = json.loads(str(row["context_json"]))
        planned_location = str(context_snapshot.get("location", "")).strip()
        current_location = str(entity["entity_location"] or "").strip()
        if planned_location and current_location != planned_location:
            _block_agenda(
                conn, agenda_id,
                "La ubicación registrada del PNJ cambió desde que se programó la actividad.",
            )
            stats["blocked"] += 1
            continue

        try:
            action = validate_action(json.loads(str(row["action_json"])))
            if any(float(value) > 0 for value in action["resource_costs"].values()):
                raise BehaviorAgendaValidationError("La acción requiere una reserva de recursos no disponible.")
            profile = validate_profile(json.loads(str(profile_row["profile_json"])))
            relation_rows = conn.execute(
                "SELECT to_entity_id,axis,value FROM relationships "
                "WHERE session_id=? AND from_entity_id=?",
                (session_id, str(row["entity_id"])),
            ).fetchall()
            relationships: dict[str, dict[str, float | None]] = {}
            for relation in relation_rows:
                relationships.setdefault(str(relation["to_entity_id"]), {})[str(relation["axis"])] = (
                    None if relation["value"] is None else float(relation["value"])
                )
            profile["relationships"] = relationships
            context = json.loads(str(row["context_json"]))
            auto_metadata = context.get("_autonomous_plan")
            if (
                str(row["status"]) == "scheduled"
                and isinstance(auto_metadata, Mapping)
                and auto_metadata.get("planner_version") in {2, 3, 4, 5}
            ):
                _, _, _, catalog_signature = _safe_autonomous_catalog(
                    conn, str(entity["world_id"])
                )
                perceived_conditions = None
                perception_metadata = None
                if auto_metadata.get("planner_version") in {3, 4, 5}:
                    perceived_conditions, perception_summary = _entity_perception_context(
                        conn, session_id, str(row["entity_id"])
                    )
                    if auto_metadata.get("planner_version") in {4, 5}:
                        perception_metadata = _planner_perception_metadata(
                            perception_summary, int(auto_metadata["planner_version"])
                        )
                current_signature = _autonomous_state_signature(
                    profile, catalog_signature, current_location,
                    perceived_conditions, perception_metadata,
                )
                if auto_metadata.get("state_signature") != current_signature:
                    raise BehaviorAgendaValidationError(
                        "La decisión autónoma quedó obsoleta antes de comenzar; no se aplicaron sus efectos."
                    )
            context["available_minutes"] = int(row["duration_minutes"])
            patterns = json.loads(str(row["patterns_json"]))
            feasible = rank_actions(profile, [action], patterns, context=context, limit=1)
            if not feasible:
                raise BehaviorAgendaValidationError(
                    "Las condiciones o capacidades del personaje cambiaron antes de completar la actividad."
                )

            event_id = uuid.uuid4().hex
            updated_profile, notes = _apply_profile_effects(
                profile, action.get("effects", {}), event_id
            )
            event_description = (
                f"{entity['name']} completó la actividad programada "
                f"«{action['action_id']}»."
            )
            conn.execute(
                "INSERT INTO events(id,session_id,turn_id,external_ref,kind,entity_id,description,"
                "witnesses_json,continuity,importance,status) "
                "VALUES(?,?,?,?,?,?,?,?,?,?, 'recorded')",
                (
                    event_id, session_id, f"agenda:{agenda_id}", "completion", "observation",
                    str(row["entity_id"]), event_description,
                    json.dumps([str(row["entity_id"])]), 1, 1,
                ),
            )
            stored_profile = dict(updated_profile)
            stored_profile["relationships"] = {}
            conn.execute(
                "UPDATE session_entity_behavior_profiles SET profile_json=?,updated_at=CURRENT_TIMESTAMP "
                "WHERE session_id=? AND entity_id=?",
                (
                    json.dumps(stored_profile, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                    session_id, str(row["entity_id"]),
                ),
            )
            result = {
                "executed": True,
                "event_id": event_id,
                "action_id": action["action_id"],
                "started_total_minutes": start,
                "completed_total_minutes": end,
                "configured_effects": action.get("effects", {}),
                "notes": notes,
            }
            encoded_result = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            conn.execute(
                "INSERT INTO behavior_action_executions("
                "id,session_id,agenda_id,entity_id,action_id,started_total_minutes,"
                "completed_total_minutes,result_json) VALUES(?,?,?,?,?,?,?,?)",
                (
                    uuid.uuid4().hex, session_id, agenda_id, str(row["entity_id"]),
                    action["action_id"], start, end, encoded_result,
                ),
            )
            conn.execute(
                "UPDATE session_entity_agendas SET status='completed',result_json=?,updated_at=CURRENT_TIMESTAMP "
                "WHERE id=?",
                (encoded_result, agenda_id),
            )
            stats["completed"] += 1
        except (BehaviorValidationError, BehaviorAgendaValidationError, ValueError, TypeError, KeyError) as exc:
            _block_agenda(conn, agenda_id, str(exc))
            stats["blocked"] += 1
    return stats


AUTONOMOUS_MAX_DURATION_MINUTES = 240
AUTONOMOUS_MAX_ACTIVITIES_PER_DAY = 6
AUTONOMOUS_BREAK_MINUTES = 10
AUTONOMOUS_MAX_RISK_LEVEL = 20


def _safe_autonomous_catalog(conn, world_id: str):
    catalog = _world_catalog(conn, world_id)
    patterns = catalog["patterns"]
    safe_actions: list[dict[str, Any]] = []
    action_map: dict[str, dict[str, Any]] = {}
    for raw_action in catalog["actions"]:
        action = validate_action(raw_action)
        if not action["autonomous_allowed"]:
            continue
        if action["duration_minutes"] <= 0 or action["duration_minutes"] > AUTONOMOUS_MAX_DURATION_MINUTES:
            continue
        if action["risk_level"] > AUTONOMOUS_MAX_RISK_LEVEL:
            continue
        if action["category"].lower() in {"movement", "travel", "exploration"}:
            continue
        if {"movement", "travel", "exploration", "journey", "pathfinding"}.intersection(action["tags"]):
            continue
        if any(float(value) > 0 for value in action["resource_costs"].values()):
            continue
        safe_actions.append(action)
        action_map[action["action_id"]] = action

    catalog_payload = json.dumps(
        {"actions": safe_actions, "patterns": patterns},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    catalog_signature = hashlib.sha256(catalog_payload.encode("utf-8")).hexdigest()
    return patterns, safe_actions, action_map, catalog_signature


def _event_known_to_entity(row, entity_id: str) -> bool:
    """Check an event's explicit witness/audience provenance for one entity."""
    try:
        witnesses = json.loads(str(row["witnesses_json"] or "[]"))
        metadata = json.loads(str(row["source_metadata_json"] or "{}"))
    except (TypeError, ValueError, json.JSONDecodeError):
        return False
    if (
        not isinstance(witnesses, list)
        or any(not isinstance(value, str) for value in witnesses)
        or not isinstance(metadata, Mapping)
    ):
        return False

    audience_raw = metadata.get("audience_ids") or []
    if not isinstance(audience_raw, list) or any(
        not isinstance(value, str) for value in audience_raw
    ):
        return False
    audience = set(audience_raw)
    witnesses_set = set(witnesses)
    visibility = metadata.get("visibility")
    recipient_id = str(row["source_recipient_id"] or "").strip()

    if visibility not in {None, "", "private", "scene", "public"}:
        return False
    if visibility == "private":
        if not audience and recipient_id:
            audience = {recipient_id}
        if entity_id not in audience:
            return False
    elif audience and entity_id not in audience:
        return False
    elif not visibility and recipient_id and entity_id != recipient_id:
        return False

    has_explicit_path = entity_id in witnesses_set or entity_id in audience
    if not visibility and recipient_id and entity_id == recipient_id:
        has_explicit_path = True
    if not row["source_message_id"] and not witnesses_set:
        return False
    return has_explicit_path


def _perception_token(value: Any) -> str:
    raw = str(value or "").strip().casefold()
    return "".join(
        char if char.isalnum() or char in "-_" else "_"
        for char in raw
    ).strip("_")[:120]



def _knowledge_transmission_provenance(
    conn, session_id: str, transmission_id: str, current_total: int
) -> tuple[list[dict[str, Any]], bool]:
    """Return the immutable sender/recipient/version chain visible through a received rumor."""
    chain_reversed: list[dict[str, Any]] = []
    seen: set[str] = set()
    current_id = transmission_id
    child: dict[str, Any] | None = None
    complete = True

    while current_id:
        if current_id in seen or len(chain_reversed) >= 50:
            complete = False
            break
        seen.add(current_id)
        row = conn.execute(
            "SELECT t.id,t.source_event_id,t.sender_entity_id,t.recipient_entity_id,"
            "t.transmission_kind,t.version_text,t.transmitted_total_minutes,"
            "t.parent_transmission_id,t.parent_correction_id,es.name AS sender_name,er.name AS recipient_name,"
            "s.status AS source_status,c.status AS communication_status,c.kind AS communication_kind,"
            "c.created_at AS communication_created_at,c.rowid AS communication_rowid "
            "FROM session_knowledge_transmissions t "
            "JOIN entities es ON es.id=t.sender_entity_id "
            "JOIN entities er ON er.id=t.recipient_entity_id "
            "JOIN events s ON s.id=t.source_event_id AND s.session_id=t.session_id "
            "JOIN events c ON c.id=t.communication_event_id AND c.session_id=t.session_id "
            "WHERE t.id=? AND t.session_id=?",
            (current_id, session_id),
        ).fetchone()
        if row is None:
            complete = False
            break
        expected_event_kind = "knowledge" if row["transmission_kind"] == "testimony" else "rumor"
        if (
            row["source_status"] != "recorded"
            or row["communication_status"] != "recorded"
            or row["communication_kind"] != expected_event_kind
            or int(row["transmitted_total_minutes"]) > current_total
        ):
            complete = False
            break
        if child is not None and (
            str(row["source_event_id"]) != str(child["source_event_id"])
            or str(row["recipient_entity_id"]) != str(child["sender_entity_id"])
            or int(row["transmitted_total_minutes"]) > int(child["transmitted_total_minutes"])
        ):
            complete = False
            break
        parent_id = str(row["parent_transmission_id"] or "")
        parent_correction_id = str(row["parent_correction_id"] or "")
        if parent_correction_id:
            if not parent_id:
                complete = False
                break
            selected_source_correction = conn.execute(
                "SELECT c.id,c.correction_kind,c.recipient_entity_id,c.corrected_total_minutes,"
                "e.status AS correction_event_status,e.kind AS correction_event_kind,"
                "e.created_at AS correction_created_at,e.rowid AS correction_event_rowid,"
                "p.transmission_kind AS parent_transmission_kind "
                "FROM session_knowledge_corrections c "
                "JOIN events e ON e.id=c.correction_event_id AND e.session_id=c.session_id "
                "JOIN session_knowledge_transmissions p ON p.id=c.original_transmission_id AND p.session_id=c.session_id "
                "WHERE c.id=? AND c.session_id=? AND c.original_transmission_id=?",
                (parent_correction_id, session_id, parent_id),
            ).fetchone()
            latest_source_correction = conn.execute(
                "SELECT c.id,c.correction_kind,c.recipient_entity_id,c.corrected_total_minutes,"
                "e.status AS correction_event_status,e.kind AS correction_event_kind "
                "FROM session_knowledge_corrections c "
                "JOIN events e ON e.id=c.correction_event_id AND e.session_id=c.session_id "
                "WHERE c.session_id=? AND c.original_transmission_id=? "
                "AND c.corrected_total_minutes<=? "
                "AND e.rowid<=? "
                "AND NOT EXISTS (SELECT 1 FROM session_knowledge_corrections child "
                "JOIN events child_event ON child_event.id=child.correction_event_id "
                "WHERE child.session_id=c.session_id AND child.parent_correction_id=c.id "
                "AND child_event.rowid<=?) "
                "ORDER BY c.corrected_total_minutes DESC,e.rowid DESC,c.id DESC LIMIT 1",
                (
                    session_id, parent_id, int(row["transmitted_total_minutes"]),
                    row["communication_rowid"], row["communication_rowid"]
                ),
            ).fetchone()
            expected_parent_correction_event = (
                "knowledge" if selected_source_correction is not None
                and selected_source_correction["parent_transmission_kind"] == "testimony"
                else "rumor"
            )
            if (
                selected_source_correction is None
                or latest_source_correction is None
                or str(latest_source_correction["id"]) != parent_correction_id
                or selected_source_correction["correction_kind"] != "corrected"
                or selected_source_correction["recipient_entity_id"] != row["sender_entity_id"]
                or selected_source_correction["correction_event_status"] != "recorded"
                or selected_source_correction["correction_event_kind"] != expected_parent_correction_event
                or int(selected_source_correction["correction_event_rowid"]) > int(row["communication_rowid"])
                or int(selected_source_correction["corrected_total_minutes"]) > int(row["transmitted_total_minutes"])
            ):
                complete = False
                break
        else:
            if parent_id:
                latest_source_correction = conn.execute(
                    "SELECT c.id,c.correction_kind "
                    "FROM session_knowledge_corrections c "
                    "JOIN events e ON e.id=c.correction_event_id AND e.session_id=c.session_id "
                    "WHERE c.session_id=? AND c.original_transmission_id=? "
                    "AND c.corrected_total_minutes<=? AND e.rowid<=? "
                    "AND NOT EXISTS (SELECT 1 FROM session_knowledge_corrections child "
                    "JOIN events child_event ON child_event.id=child.correction_event_id "
                    "WHERE child.session_id=c.session_id AND child.parent_correction_id=c.id "
                    "AND child_event.rowid<=?) "
                    "ORDER BY c.corrected_total_minutes DESC,e.rowid DESC,c.id DESC LIMIT 1",
                    (
                        session_id, parent_id, int(row["transmitted_total_minutes"]),
                        row["communication_rowid"], row["communication_rowid"]
                    ),
                ).fetchone()
                if latest_source_correction is not None:
                    complete = False
                    break

        chain_reversed.append({
            "transmission_id": str(row["id"]),
            "sender_entity_id": str(row["sender_entity_id"]),
            "sender_name": str(row["sender_name"]),
            "recipient_entity_id": str(row["recipient_entity_id"]),
            "recipient_name": str(row["recipient_name"]),
            "transmission_kind": str(row["transmission_kind"]),
            "version_text": str(row["version_text"]),
            "transmitted_total_minutes": int(row["transmitted_total_minutes"]),
            "parent_transmission_id": parent_id,
            "parent_correction_id": parent_correction_id,
        })
        if not parent_id:
            break
        child = row
        current_id = parent_id

    if not complete:
        return [], False
    return list(reversed(chain_reversed)), bool(chain_reversed)


def _entity_perception_context(
    conn, session_id: str, entity_id: str
) -> tuple[dict[str, bool], dict[str, Any]]:
    """Build event and environmental conditions for one entity, never globally.

    Events require explicit witness/audience provenance. Environmental readings
    are personal, location-bound observations with a game-time expiry and a
    still-recorded source event. Weather and local safety remain separate keys.
    """
    session_state = conn.execute(
        "SELECT s.day,s.minute_of_day,s.current_location,e.kind,"
        "p.location AS entity_location "
        "FROM sessions s JOIN entities e ON e.id=? AND e.world_id=s.world_id "
        "LEFT JOIN session_presence p ON p.session_id=s.id AND p.entity_id=e.id "
        "WHERE s.id=?",
        (entity_id, session_id),
    ).fetchone()
    if session_state is None:
        return {}, {"source_event_ids": [], "event_kinds": [], "environment_observations": [], "knowledge_reports": []}

    current_total = _total_minutes(
        int(session_state["day"]), int(session_state["minute_of_day"])
    )
    location = str(session_state["entity_location"] or "").strip()
    if not location and str(session_state["kind"]) == "protagonist":
        location = str(session_state["current_location"] or "").strip()

    rows = conn.execute(
        "SELECT e.id,e.external_ref,e.kind,e.witnesses_json,e.source_message_id,"
        "m.recipient_entity_id AS source_recipient_id,m.metadata_json AS source_metadata_json "
        "FROM events e LEFT JOIN messages m ON m.id=e.source_message_id "
        "WHERE e.session_id=? AND e.status='recorded' "
        "ORDER BY e.created_at DESC,e.rowid DESC LIMIT 40",
        (session_id,),
    ).fetchall()

    conditions: dict[str, bool] = {}
    source_event_ids: list[str] = []
    event_kinds: set[str] = set()
    for row in rows:
        if not _event_known_to_entity(row, entity_id):
            continue
        event_id = str(row["id"] or "").strip()
        kind = _perception_token(row["kind"])
        external_ref = _perception_token(row["external_ref"])
        if not event_id or not kind:
            continue
        conditions[f"knows_event_kind:{kind}"] = True
        conditions[f"knows_event_id:{_perception_token(event_id)}"] = True
        if external_ref:
            conditions[f"knows_event_ref:{external_ref}"] = True
        source_event_ids.append(event_id)
        event_kinds.add(kind)

    # Assessments are personal judgements by the recipient. They never alter
    # the underlying event or another character's view of the same report.
    assessment_rows = conn.execute(
        "SELECT a.* FROM session_knowledge_assessments a "
        "JOIN session_knowledge_transmissions t ON t.id=a.transmission_id "
        "WHERE a.session_id=? AND a.assessor_entity_id=? "
        "AND t.recipient_entity_id=a.assessor_entity_id "
        "ORDER BY a.assessed_total_minutes DESC,a.created_at DESC,a.id DESC LIMIT 200",
        (session_id, entity_id),
    ).fetchall()
    assessments_by_report: dict[str, list[dict[str, Any]]] = {}
    for assessment in reversed(assessment_rows):
        assessments_by_report.setdefault(str(assessment["transmission_id"]), []).append({
            "stance": str(assessment["stance"]),
            "confidence": int(assessment["confidence"]),
            "evidence_report_id": str(assessment["evidence_report_id"] or ""),
            "evidence_event_id": str(assessment["evidence_event_id"] or ""),
            "rationale": str(assessment["rationale"]),
            "assessed_total_minutes": int(assessment["assessed_total_minutes"]),
        })

    # A sender may later correct or withdraw the exact statement they gave.
    # These records remain attached to the recipient's report; they never erase
    # its original wording or change the source event.
    correction_rows = conn.execute(
        "SELECT c.*,t.transmission_kind AS target_transmission_kind,"
        "e.status AS correction_event_status,e.kind AS correction_event_kind,"
        "e.witnesses_json,e.source_message_id,"
        "m.recipient_entity_id AS source_recipient_id,m.metadata_json AS source_metadata_json "
        "FROM session_knowledge_corrections c "
        "JOIN session_knowledge_transmissions t ON t.id=c.original_transmission_id AND t.session_id=c.session_id "
        "JOIN events e ON e.id=c.correction_event_id AND e.session_id=c.session_id "
        "LEFT JOIN messages m ON m.id=e.source_message_id "
        "WHERE c.session_id=? AND c.recipient_entity_id=? "
        "AND c.corrected_total_minutes<=? AND e.status='recorded' "
        "ORDER BY c.corrected_total_minutes,c.created_at,c.id",
        (session_id, entity_id, current_total),
    ).fetchall()
    correction_entries_by_report: dict[str, dict[str, dict[str, Any]]] = {}
    for correction in correction_rows:
        expected_correction_event_kind = (
            "knowledge" if correction["target_transmission_kind"] == "testimony" else "rumor"
        )
        if correction["correction_event_kind"] != expected_correction_event_kind or not _event_known_to_entity(
            correction, entity_id
        ):
            continue
        entry = {
            "correction_id": str(correction["id"]),
            "parent_correction_id": str(correction["parent_correction_id"] or ""),
            "correction_event_id": str(correction["correction_event_id"]),
            "correction_kind": str(correction["correction_kind"]),
            "sender_entity_id": str(correction["sender_entity_id"]),
            "recipient_entity_id": str(correction["recipient_entity_id"]),
            "replacement_text": str(correction["replacement_text"] or ""),
            "rationale": str(correction["rationale"]),
            "location": str(correction["location"]),
            "corrected_total_minutes": int(correction["corrected_total_minutes"]),
        }
        correction_entries_by_report.setdefault(
            str(correction["original_transmission_id"]), {}
        )[entry["correction_id"]] = entry

    # Reconstruct each chain by its explicit parent link, not timestamps: two
    # successive corrections may legitimately occur in the same game minute.
    corrections_by_report: dict[str, list[dict[str, Any]]] = {}
    for report_id, entries in correction_entries_by_report.items():
        roots = [entry for entry in entries.values() if not entry["parent_correction_id"]]
        if len(roots) != 1:
            continue
        history = [roots[0]]
        visited = {history[0]["correction_id"]}
        while True:
            children = [
                entry for entry in entries.values()
                if entry["parent_correction_id"] == history[-1]["correction_id"]
            ]
            if len(children) != 1 or children[0]["correction_id"] in visited:
                break
            history.append(children[0])
            visited.add(children[0]["correction_id"])
        if len(history) == len(entries):
            for version_number, entry in enumerate(history, start=1):
                entry["version_number"] = version_number
            corrections_by_report[report_id] = history

    # A received report is knowledge that someone made this statement, not proof
    # that the source event happened as described. Keep its attribution and wording.
    knowledge_summary: list[dict[str, Any]] = []
    report_rows = conn.execute(
        "SELECT t.id,t.sender_entity_id,t.recipient_entity_id,t.transmission_kind,"
        "t.version_text,t.location,t.transmitted_total_minutes,t.parent_transmission_id,"
        "t.parent_correction_id,s.id AS source_event_id,s.kind AS source_event_kind,"
        "c.id AS communication_event_id,c.status AS communication_status "
        "FROM session_knowledge_transmissions t "
        "JOIN events s ON s.id=t.source_event_id AND s.session_id=t.session_id "
        "JOIN events c ON c.id=t.communication_event_id AND c.session_id=t.session_id "
        "WHERE t.session_id=? AND t.recipient_entity_id=? "
        "AND t.transmitted_total_minutes<=? AND s.status='recorded' AND c.status='recorded' "
        "ORDER BY t.transmitted_total_minutes DESC,t.created_at DESC,t.id DESC LIMIT 20",
        (session_id, entity_id, current_total),
    ).fetchall()
    for report in report_rows:
        report_id = _perception_token(report["id"])
        source_id = _perception_token(report["source_event_id"])
        transmission_kind = str(report["transmission_kind"])
        if not report_id or not source_id or transmission_kind not in {"testimony", "rumor"}:
            continue
        conditions[f"heard_report_id:{report_id}"] = True
        conditions[f"heard_report_of_event:{source_id}"] = True
        conditions[f"heard_{transmission_kind}_of_event:{source_id}"] = True
        correction_history = corrections_by_report.get(str(report["id"]), [])
        correction = correction_history[-1] if correction_history else None
        report_status = "active"
        if correction:
            if correction["correction_kind"] == "corrected":
                report_status = "corrected"
                conditions[f"received_report_corrected:{report_id}"] = True
            elif correction["correction_kind"] == "retracted":
                report_status = "retracted"
                conditions[f"received_report_retracted:{report_id}"] = True
        provenance_chain, provenance_complete = _knowledge_transmission_provenance(
            conn, session_id, str(report["id"]), current_total
        )
        origin = provenance_chain[0] if provenance_chain else None
        knowledge_summary.append({
            "transmission_id": str(report["id"]),
            "transmission_kind": transmission_kind,
            "sender_entity_id": str(report["sender_entity_id"]),
            "recipient_entity_id": str(report["recipient_entity_id"]),
            "source_event_id": str(report["source_event_id"]),
            "source_event_kind": str(report["source_event_kind"]),
            "reported_version": str(report["version_text"]),
            "location": str(report["location"]),
            "transmitted_total_minutes": int(report["transmitted_total_minutes"]),
            "parent_transmission_id": str(report["parent_transmission_id"] or ""),
            "parent_correction_id": str(report["parent_correction_id"] or ""),
            "origin_transmission_id": origin["transmission_id"] if origin else "",
            "originator_entity_id": origin["sender_entity_id"] if origin else "",
            "originator_name": origin["sender_name"] if origin else "",
            "provenance_chain": provenance_chain,
            "provenance_complete": provenance_complete,
            "relay_count": max(0, len(provenance_chain) - 1),
            "epistemic_status": "reported_not_verified",
            "report_status": report_status,
            "correction": correction,
            "correction_history": correction_history,
            "current_reported_version": (
                correction["replacement_text"]
                if correction and correction["correction_kind"] == "corrected"
                else ("" if correction and correction["correction_kind"] == "retracted" else str(report["version_text"]))
            ),
            "assessment": (
                assessments_by_report.get(str(report["id"]), [])[-1]
                if assessments_by_report.get(str(report["id"])) else None
            ),
            "assessment_history": assessments_by_report.get(str(report["id"]), [])[-10:],
        })

    environment_summary: list[dict[str, Any]] = []
    if location:
        environment_rows = conn.execute(
            "SELECT o.*,e.status AS source_status,e.kind AS source_event_kind,e.witnesses_json,"
            "e.source_message_id,m.recipient_entity_id AS source_recipient_id,"
            "m.metadata_json AS source_metadata_json "
            "FROM session_environment_observations o "
            "JOIN events e ON e.id=o.source_event_id AND e.session_id=o.session_id "
            "LEFT JOIN messages m ON m.id=e.source_message_id "
            "WHERE o.session_id=? AND o.observer_entity_id=? AND LOWER(o.location)=LOWER(?) "
            "AND o.observed_total_minutes<=? AND o.valid_until_total_minutes>? "
            "AND e.status='recorded' "
            "ORDER BY o.observed_total_minutes DESC,o.created_at DESC,o.id DESC LIMIT 20",
            (session_id, entity_id, location, current_total, current_total),
        ).fetchall()
        latest_by_kind: set[str] = set()
        for observation in environment_rows:
            kind = str(observation["observation_kind"])
            if kind in latest_by_kind:
                continue
            if observation["source_event_kind"] != "observation":
                continue
            try:
                observation_witnesses = json.loads(str(observation["witnesses_json"] or "[]"))
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            if (
                not isinstance(observation_witnesses, list)
                or entity_id not in observation_witnesses
                or not _event_known_to_entity(observation, entity_id)
            ):
                continue
            value_key = _perception_token(observation["value_key"])
            if not value_key or value_key == "unknown":
                continue
            latest_by_kind.add(kind)
            condition_name = (
                "observes_weather" if kind == "weather" else "observes_local_safety"
            )
            conditions[f"{condition_name}:{value_key}"] = True
            environment_summary.append({
                "observation_id": str(observation["id"]),
                "observation_kind": kind,
                "value_key": value_key,
                "location": str(observation["location"]),
                "observed_total_minutes": int(observation["observed_total_minutes"]),
                "valid_until_total_minutes": int(observation["valid_until_total_minutes"]),
                "source_event_id": str(observation["source_event_id"]),
            })

    return conditions, {
        "source_event_ids": source_event_ids[:20],
        "event_kinds": sorted(event_kinds),
        "environment_observations": environment_summary[:10],
        "knowledge_reports": knowledge_summary[:20],
    }


def _planner_perception_metadata(
    perception_summary: Mapping[str, Any], planner_version: int
) -> Mapping[str, Any] | None:
    """Keep legacy v4 signatures stable until a new knowledge report exists.

    v5 always includes attributed reports. Existing v4 plans ignore the newly
    introduced empty field, but a received report invalidates their old plan
    so the NPC can reconsider future activity using that information.
    """
    if planner_version == 5:
        return perception_summary
    if planner_version == 4:
        if perception_summary.get("knowledge_reports"):
            return perception_summary
        legacy = dict(perception_summary)
        legacy.pop("knowledge_reports", None)
        return legacy
    return None


def _signature_bucket(value: Any) -> int | None:
    if value is None:
        return None
    return int(round(float(value) / 10))


def _autonomous_profile_signature(profile: Mapping[str, Any]) -> str:
    """Build a stable decision signature that ignores tiny emotion/need decay."""
    state = validate_profile(profile)
    projection = {
        "traits": {
            key: _signature_bucket(value)
            for key, value in sorted(state["traits"].items())
        },
        "needs": {
            key: _signature_bucket(value)
            for key, value in sorted(state["needs"].items())
        },
        "emotions": sorted(
            (
                item["kind"], _signature_bucket(item["intensity"]),
                item["target_id"], item["source_event_id"],
            )
            for item in state["emotions"]
        ),
        "goals": sorted(
            (
                item["goal_id"], _signature_bucket(item["priority"]),
                tuple(sorted(item["tags"])), item["status"], item["target_id"],
            )
            for item in state["goals"]
        ),
        "focus": None if state["focus"] is None else {
            "kind": state["focus"]["kind"],
            "target_id": state["focus"]["target_id"],
            "salience": _signature_bucket(state["focus"]["salience"]),
            "tags": sorted(state["focus"]["tags"]),
        },
        "capabilities": sorted(state["capabilities"]),
        "resources": {
            key: _signature_bucket(value)
            for key, value in sorted(state["resources"].items())
        },
        "relationships": {
            target: {
                axis: _signature_bucket(value)
                for axis, value in sorted(axes.items())
            }
            for target, axes in sorted(state["relationships"].items())
        },
    }
    encoded = json.dumps(
        projection, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _autonomous_state_signature(
    profile: Mapping[str, Any],
    catalog_signature: str,
    location: str,
    perceived_conditions: Mapping[str, bool] | None = None,
    perception_metadata: Mapping[str, Any] | None = None,
) -> str:
    profile_signature = _autonomous_profile_signature(profile)
    location_signature = hashlib.sha256(location.encode("utf-8")).hexdigest()
    if perceived_conditions is None:
        # Preserve the original v2 signature for already-scheduled legacy tasks.
        return hashlib.sha256(
            f"{profile_signature}|{catalog_signature}|{location_signature}".encode("utf-8")
        ).hexdigest()
    if perception_metadata is None:
        # Preserve the original v3 signature for agendas created by PR #50.
        perception_payload = json.dumps(
            dict(sorted(perceived_conditions.items())),
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        )
    else:
        perception_payload = json.dumps(
            {
                "conditions": dict(sorted(perceived_conditions.items())),
                "metadata": perception_metadata,
            },
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        )
    perception_signature = hashlib.sha256(perception_payload.encode("utf-8")).hexdigest()
    return hashlib.sha256(
        f"{profile_signature}|{catalog_signature}|{location_signature}|{perception_signature}".encode("utf-8")
    ).hexdigest()


def _agenda_autonomous_metadata(row) -> dict[str, Any] | None:
    try:
        context = json.loads(str(row["context_json"]))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(context, Mapping):
        return None
    metadata = context.get("_autonomous_plan")
    return dict(metadata) if isinstance(metadata, Mapping) else None


def _cancel_stale_autonomous_agenda(conn, row, reason: str) -> None:
    result = {
        "executed": False,
        "reason": reason,
        "replanned": True,
    }
    conn.execute(
        "UPDATE session_entity_agendas SET status='cancelled',result_json=?,"
        "updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='scheduled'",
        (json.dumps(result, ensure_ascii=False, sort_keys=True), str(row["id"])),
    )


def _autonomous_agenda_state_matches(conn, session_id: str, row) -> bool:
    """Fail closed if a not-yet-started automatic agenda no longer matches state."""
    metadata = _agenda_autonomous_metadata(row)
    if metadata is None or metadata.get("planner_version") not in {2, 3, 4, 5}:
        return True
    try:
        entity = conn.execute(
            "SELECT e.kind,s.world_id,p.location AS entity_location FROM sessions s "
            "JOIN entities e ON e.world_id=s.world_id "
            "LEFT JOIN session_presence p ON p.session_id=s.id AND p.entity_id=e.id "
            "WHERE s.id=? AND e.id=?",
            (session_id, str(row["entity_id"])),
        ).fetchone()
        if entity is None or str(entity["kind"]) == "protagonist":
            return False
        profile = _profile_for(conn, session_id, str(row["entity_id"]))
        _, _, _, catalog_signature = _safe_autonomous_catalog(conn, str(entity["world_id"]))
        perceived_conditions = None
        perception_metadata = None
        if metadata.get("planner_version") in {3, 4, 5}:
            perceived_conditions, perception_summary = _entity_perception_context(
                conn, session_id, str(row["entity_id"])
            )
            if metadata.get("planner_version") in {4, 5}:
                perception_metadata = _planner_perception_metadata(
                    perception_summary, int(metadata["planner_version"])
                )
        current_signature = _autonomous_state_signature(
            profile, catalog_signature, str(entity["entity_location"] or "").strip(),
            perceived_conditions, perception_metadata,
        )
        return metadata.get("state_signature") == current_signature
    except (BehaviorValidationError, BehaviorAgendaConflictError, ValueError, TypeError, KeyError):
        return False


def plan_autonomous_behavior_agendas(
    conn, session_id: str, current_total_minutes: int
) -> int:
    """Plan several safe activities for the remainder of the current world day.

    A material profile, catalog, or location change invalidates only future
    autonomous entries. Running tasks and explicit manual commitments survive.
    The planner never moves entities, consumes resources, or advances time.
    """
    session = conn.execute(
        "SELECT world_id FROM sessions WHERE id=?", (session_id,)
    ).fetchone()
    if session is None:
        return 0

    world_id = str(session["world_id"])
    patterns, safe_actions, action_map, catalog_signature = _safe_autonomous_catalog(
        conn, world_id
    )

    entities = conn.execute(
        "SELECT e.id,e.kind,p.location AS entity_location "
        "FROM entities e "
        "JOIN session_entity_behavior_profiles b ON b.entity_id=e.id AND b.session_id=? "
        "LEFT JOIN session_presence p ON p.session_id=? AND p.entity_id=e.id "
        "WHERE e.world_id=? AND e.kind<>'protagonist' "
        "ORDER BY e.id",
        (session_id, session_id, world_id),
    ).fetchall()

    day_start = (int(current_total_minutes) // 1440) * 1440
    day_end = day_start + 1440
    current_total = int(current_total_minutes)
    planned_total = 0

    for entity in entities:
        entity_id = str(entity["id"])
        location = str(entity["entity_location"] or "").strip()
        try:
            profile = _profile_for(conn, session_id, entity_id)
            profile_signature = _autonomous_profile_signature(profile)
            perceived_conditions, perception_summary = _entity_perception_context(
                conn, session_id, entity_id
            )
            state_signature = _autonomous_state_signature(
                profile, catalog_signature, location, perceived_conditions, perception_summary
            )
        except (BehaviorValidationError, BehaviorAgendaConflictError, ValueError, TypeError):
            continue

        active_rows = conn.execute(
            "SELECT * FROM session_entity_agendas WHERE session_id=? AND entity_id=? "
            "AND status IN ('scheduled','running') "
            "ORDER BY scheduled_total_minutes,priority DESC,created_at,id",
            (session_id, entity_id),
        ).fetchall()

        auto_scheduled = [
            row for row in active_rows
            if str(row["status"]) == "scheduled" and _agenda_autonomous_metadata(row) is not None
        ]
        if auto_scheduled:
            def scheduled_signature_matches(row) -> bool:
                metadata = _agenda_autonomous_metadata(row) or {}
                version = metadata.get("planner_version")
                if version == 2:
                    expected_signature = _autonomous_state_signature(
                        profile, catalog_signature, location
                    )
                elif version == 3:
                    expected_signature = _autonomous_state_signature(
                        profile, catalog_signature, location, perceived_conditions
                    )
                elif version in {4, 5}:
                    expected_signature = _autonomous_state_signature(
                        profile, catalog_signature, location,
                        perceived_conditions,
                        _planner_perception_metadata(perception_summary, int(version)),
                    )
                else:
                    return False
                return metadata.get("state_signature") == expected_signature

            signatures_match = all(scheduled_signature_matches(row) for row in auto_scheduled)
            if signatures_match:
                # A complete future plan for this state already exists.
                continue
            for row in auto_scheduled:
                _cancel_stale_autonomous_agenda(
                    conn, row,
                    "El perfil, el catálogo autorizado o la ubicación cambió; se descartó el tramo futuro para replanificar.",
                )

        reservations: list[tuple[int, int]] = []
        for row in active_rows:
            if str(row["status"]) == "scheduled" and _agenda_autonomous_metadata(row) is not None:
                # Stale future autonomous rows were cancelled above.
                continue
            start = int(row["scheduled_total_minutes"])
            end = start + int(row["duration_minutes"])
            if end > current_total:
                reservations.append((start, end))
        reservations.sort()

        if not safe_actions:
            continue

        cursor = max(current_total, day_start)
        if cursor >= day_end:
            continue

        completed_rows = conn.execute(
            "SELECT action_id,COUNT(*) AS n FROM behavior_action_executions "
            "WHERE session_id=? AND entity_id=? "
            "AND completed_total_minutes>=? AND completed_total_minutes<? "
            "GROUP BY action_id",
            (session_id, entity_id, day_start, day_end),
        ).fetchall()
        used_today = {str(row["action_id"]): int(row["n"]) for row in completed_rows}

        recent = conn.execute(
            "SELECT completed_total_minutes FROM behavior_action_executions "
            "WHERE session_id=? AND entity_id=? "
            "ORDER BY completed_total_minutes DESC,id DESC LIMIT 1",
            (session_id, entity_id),
        ).fetchone()
        if recent is not None:
            last_end = int(recent["completed_total_minutes"])
            if current_total < last_end + AUTONOMOUS_BREAK_MINUTES:
                cursor = max(cursor, last_end + AUTONOMOUS_BREAK_MINUTES)

        running_auto_count = sum(
            1 for row in active_rows
            if str(row["status"]) == "running"
            and _agenda_autonomous_metadata(row) is not None
            and day_start <= int(row["scheduled_total_minutes"]) < day_end
        )
        activity_count = sum(used_today.values()) + running_auto_count
        while cursor < day_end and activity_count < AUTONOMOUS_MAX_ACTIVITIES_PER_DAY:
            next_reservation = next(
                ((start, end) for start, end in reservations if end > cursor),
                None,
            )
            if next_reservation is not None and next_reservation[0] <= cursor:
                cursor = max(cursor, next_reservation[1]) + AUTONOMOUS_BREAK_MINUTES
                continue

            slot_end = min(
                day_end,
                cursor + AUTONOMOUS_MAX_DURATION_MINUTES,
                next_reservation[0] if next_reservation is not None else day_end,
            )
            available_minutes = slot_end - cursor
            if available_minutes <= 0:
                if next_reservation is None:
                    break
                cursor = max(cursor, next_reservation[1]) + AUTONOMOUS_BREAK_MINUTES
                continue

            context: dict[str, Any] = {
                "conditions": dict(perceived_conditions),
                "available_minutes": available_minutes,
                "world_day": day_start // 1440 + 1,
                "world_minute": cursor % 1440,
                "perception": perception_summary,
            }
            if location:
                context["location"] = location

            try:
                ranked = rank_actions(
                    profile, safe_actions, patterns, context=context, limit=100
                )
            except BehaviorValidationError:
                break

            selected = None
            for candidate in ranked:
                action = action_map[candidate["action_id"]]
                action_id = str(candidate["action_id"])
                count_today = used_today.get(action_id, 0)
                if action["autonomous_repeatable"]:
                    if count_today >= 3:
                        continue
                elif count_today > 0:
                    continue
                selected = candidate
                break

            if selected is None or float(selected["score"]) <= 0:
                if next_reservation is not None:
                    cursor = max(cursor, next_reservation[1]) + AUTONOMOUS_BREAK_MINUTES
                    continue
                break

            action = action_map[selected["action_id"]]
            duration = int(action["duration_minutes"])
            if duration > available_minutes:
                break

            agenda_context = dict(context)
            agenda_context["available_minutes"] = duration
            agenda_context["_autonomous_plan"] = {
                "planner_version": 5,
                "state_signature": state_signature,
                "profile_signature": profile_signature,
                "catalog_signature": catalog_signature,
                "score": float(selected["score"]),
                "reason_codes": list(selected["reason_codes"]),
                "matched_patterns": list(selected["matched_patterns"]),
                "day": day_start // 1440 + 1,
                "sequence": activity_count + 1,
            }

            request_seed = (
                f"{session_id}|{entity_id}|{cursor}|{action['action_id']}|"
                f"{state_signature}|autonomous-planner-v3"
            )
            request_id = "auto-" + hashlib.sha256(request_seed.encode("utf-8")).hexdigest()[:48]
            duplicate = conn.execute(
                "SELECT 1 FROM session_entity_agendas WHERE session_id=? AND request_id=?",
                (session_id, request_id),
            ).fetchone()
            if duplicate is not None:
                break

            end_total = cursor + duration
            overlap = conn.execute(
                "SELECT 1 FROM session_entity_agendas WHERE session_id=? AND entity_id=? "
                "AND status IN ('scheduled','running') "
                "AND scheduled_total_minutes < ? "
                "AND (scheduled_total_minutes + duration_minutes) > ? LIMIT 1",
                (session_id, entity_id, end_total, cursor),
            ).fetchone()
            if overlap is not None:
                reserved = conn.execute(
                    "SELECT scheduled_total_minutes,duration_minutes FROM session_entity_agendas "
                    "WHERE session_id=? AND entity_id=? AND status IN ('scheduled','running') "
                    "AND scheduled_total_minutes < ? "
                    "AND (scheduled_total_minutes + duration_minutes) > ? "
                    "ORDER BY scheduled_total_minutes LIMIT 1",
                    (session_id, entity_id, end_total, cursor),
                ).fetchone()
                if reserved is None:
                    break
                reservations.append((
                    int(reserved["scheduled_total_minutes"]),
                    int(reserved["scheduled_total_minutes"]) + int(reserved["duration_minutes"]),
                ))
                reservations.sort()
                continue

            agenda_id = uuid.uuid4().hex
            encoded_context = json.dumps(
                agenda_context, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            encoded_action = json.dumps(
                action, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            encoded_patterns = json.dumps(
                patterns, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            priority = max(0.0, min(100.0, 50.0 + float(selected["score"])))
            conn.execute(
                "INSERT INTO session_entity_agendas("
                "id,session_id,entity_id,request_id,action_id,action_json,patterns_json,context_json,"
                "scheduled_total_minutes,duration_minutes,priority,target_entity_id,status,result_json"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?, 'scheduled','{}')",
                (
                    agenda_id, session_id, entity_id, request_id, action["action_id"],
                    encoded_action, encoded_patterns, encoded_context, cursor,
                    duration, priority, "",
                ),
            )
            reservations.append((cursor, end_total))
            reservations.sort()
            used_today[action["action_id"]] = used_today.get(action["action_id"], 0) + 1
            cursor = end_total + AUTONOMOUS_BREAK_MINUTES
            activity_count += 1
            planned_total += 1

    return planned_total

def tick_behavior_runtime(
    conn, session_id: str, previous_total_minutes: int, current_total_minutes: int
) -> dict[str, int]:
    """Apply emotion decay, completed activities, and the next safe NPC plans."""
    elapsed = int(current_total_minutes) - int(previous_total_minutes)
    if elapsed <= 0:
        return {
            "emotions_updated": 0, "started": 0, "completed": 0, "blocked": 0, "planned": 0
        }

    updated = 0
    rows = conn.execute(
        "SELECT b.entity_id,b.profile_json FROM session_entity_behavior_profiles b "
        "JOIN entities e ON e.id=b.entity_id WHERE b.session_id=? AND e.kind<>'protagonist'",
        (session_id,),
    ).fetchall()
    for row in rows:
        profile = advance_emotions(
            json.loads(str(row["profile_json"])), elapsed
        )
        profile["relationships"] = {}
        conn.execute(
            "UPDATE session_entity_behavior_profiles SET profile_json=?,updated_at=CURRENT_TIMESTAMP "
            "WHERE session_id=? AND entity_id=?",
            (
                json.dumps(profile, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                session_id, str(row["entity_id"]),
            ),
        )
        updated += 1

    agenda_stats = process_due_behavior_agendas(
        conn, session_id, int(previous_total_minutes), int(current_total_minutes)
    )
    planned = plan_autonomous_behavior_agendas(conn, session_id, int(current_total_minutes))
    return {"emotions_updated": updated, **agenda_stats, "planned": planned}
