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


def plan_autonomous_behavior_agendas(
    conn, session_id: str, current_total_minutes: int
) -> int:
    """Schedule at most one safe next activity for each configured NPC.

    Planning runs inside the caller's clock transaction. It never changes the
    clock, entity location, inventory, relationships, or protagonist state.
    Only world-catalog actions explicitly marked autonomous_allowed can be
    selected. Unknown environmental conditions and resource costs fail closed.
    """
    session = conn.execute(
        "SELECT world_id,day,minute_of_day FROM sessions WHERE id=?", (session_id,)
    ).fetchone()
    if session is None:
        return 0

    world_id = str(session["world_id"])
    catalog = _world_catalog(conn, world_id)
    horizon_minutes = 240
    patterns = catalog["patterns"]
    safe_actions = []
    action_map = {}
    for raw_action in catalog["actions"]:
        action = validate_action(raw_action)
        if not action["autonomous_allowed"]:
            continue
        if action["duration_minutes"] <= 0 or action["duration_minutes"] > horizon_minutes:
            continue
        if action["category"].lower() == "movement":
            continue
        if {"movement", "travel"}.intersection(action["tags"]):
            continue
        if any(float(value) > 0 for value in action["resource_costs"].values()):
            continue
        safe_actions.append(action)
        action_map[action["action_id"]] = action
    if not safe_actions:
        return 0

    entities = conn.execute(
        "SELECT e.id,e.kind,p.location AS entity_location "
        "FROM entities e "
        "JOIN session_entity_behavior_profiles b ON b.entity_id=e.id AND b.session_id=? "
        "LEFT JOIN session_presence p ON p.session_id=? AND p.entity_id=e.id "
        "WHERE e.world_id=? AND e.kind<>'protagonist' "
        "ORDER BY e.id",
        (session_id, session_id, world_id),
    ).fetchall()

    planned = 0
    current_total = int(current_total_minutes)
    scheduled_day = current_total // 1440 + 1
    scheduled_minute = current_total % 1440

    for entity in entities:
        entity_id = str(entity["id"])
        active = conn.execute(
            "SELECT 1 FROM session_entity_agendas WHERE session_id=? AND entity_id=? "
            "AND status IN ('scheduled','running') LIMIT 1",
            (session_id, entity_id),
        ).fetchone()
        if active is not None:
            continue

        try:
            profile = _profile_for(conn, session_id, entity_id)
            context: dict[str, Any] = {
                "conditions": {},
                "available_minutes": horizon_minutes,
                "world_day": scheduled_day,
                "world_minute": scheduled_minute,
            }
            location = str(entity["entity_location"] or "").strip()
            if location:
                context["location"] = location

            recent_rows = conn.execute(
                "SELECT action_id FROM behavior_action_executions "
                "WHERE session_id=? AND entity_id=? "
                "ORDER BY completed_total_minutes DESC,id DESC LIMIT 3",
                (session_id, entity_id),
            ).fetchall()
            recent_actions = {str(row["action_id"]) for row in recent_rows}

            ranked = rank_actions(
                profile, safe_actions, patterns, context=context, limit=100
            )
            selected = next(
                (
                    item for item in ranked
                    if item["action_id"] not in recent_actions and float(item["score"]) > 0
                ),
                None,
            )
            if selected is None:
                continue

            action = action_map[selected["action_id"]]
            duration = int(action["duration_minutes"])
            agenda_context = dict(context)
            agenda_context["available_minutes"] = duration
            agenda_context["_autonomous_plan"] = {
                "planner_version": 1,
                "score": float(selected["score"]),
                "reason_codes": list(selected["reason_codes"]),
                "matched_patterns": list(selected["matched_patterns"]),
            }
            # Repeat the exact feasibility check used by manual scheduling.
            if not rank_actions(profile, [action], patterns, context=agenda_context, limit=1):
                continue

            request_seed = (
                f"{session_id}|{entity_id}|{current_total}|"
                f"{action['action_id']}|autonomous-planner-v1"
            )
            request_id = "auto-" + hashlib.sha256(request_seed.encode("utf-8")).hexdigest()[:48]
            duplicate = conn.execute(
                "SELECT 1 FROM session_entity_agendas WHERE session_id=? AND request_id=?",
                (session_id, request_id),
            ).fetchone()
            if duplicate is not None:
                continue

            end_total = current_total + duration
            overlap = conn.execute(
                "SELECT 1 FROM session_entity_agendas WHERE session_id=? AND entity_id=? "
                "AND status IN ('scheduled','running') "
                "AND scheduled_total_minutes < ? "
                "AND (scheduled_total_minutes + duration_minutes) > ? LIMIT 1",
                (session_id, entity_id, end_total, current_total),
            ).fetchone()
            if overlap is not None:
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
                    encoded_action, encoded_patterns, encoded_context, current_total,
                    duration, priority, "",
                ),
            )
            planned += 1
        except (BehaviorValidationError, BehaviorAgendaValidationError, ValueError, TypeError, KeyError):
            # A malformed or incomplete NPC profile must not stop the rest of
            # the world from advancing. That NPC simply receives no new plan.
            continue

    return planned


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
