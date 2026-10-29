import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .db import Database
from .models import ApprovalRequest, EntityCreate, NarratorResponse, SessionCreate, TurnRequest, WorldCreate, WorldStartCreate
from .providers import ProviderError, make_provider

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class Settings:
    def __init__(self):
        self.db_path = os.getenv("APP_DB_PATH", "./data/canon_manager.sqlite3")
        self.default_provider = os.getenv("APP_PROVIDER", "mock").strip().lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model = os.getenv("GEMINI_MODEL", "")


settings = Settings()
database = Database(settings.db_path)
database.initialize()

app = FastAPI(title="Gestor local de canon", version="0.1.0")
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

RELATION_AXES = {
    "confidence", "suspicion", "friendship", "respect", "rivalry",
    "resentment", "fear", "gratitude_debt", "cooperation", "attraction"
}
MAX_AUTO_RELATION_DELTA = 3


def new_id() -> str:
    return uuid.uuid4().hex


def parse_skip(text: str) -> dict[str, Any] | None:
    match = re.match(
        r"^\s*/salto\s+(\d+)\s*(minutos?|mins?|m|horas?|h)\s*(?:->\s*(.*))?$",
        text.strip(), re.IGNORECASE
    )
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2).lower()
    minutes = amount * 60 if unit.startswith("h") else amount
    if minutes < 1 or minutes > 7 * 24 * 60:
        raise HTTPException(status_code=422, detail="El salto debe estar entre 1 minuto y 7 días.")
    return {"minutes": minutes, "destination": (match.group(3) or "").strip()}


def time_label(day: int, minute_of_day: int) -> str:
    if minute_of_day < 240:
        block = "Madrugada"
    elif minute_of_day < 480:
        block = "Amanecer"
    elif minute_of_day < 720:
        block = "Mañana"
    elif minute_of_day < 960:
        block = "Mediodía"
    elif minute_of_day < 1200:
        block = "Tarde"
    else:
        block = "Noche"
    hour, minute = divmod(minute_of_day, 60)
    return f"Día {day} · {block} · {hour:02d}:{minute:02d}"


def session_row(conn, session_id: str):
    return conn.execute(
        "SELECT s.*, w.name AS world_name, w.canon_text FROM sessions s "
        "JOIN worlds w ON w.id=s.world_id WHERE s.id=?",
        (session_id,)
    ).fetchone()


def world_entity_ids(conn, world_id: str) -> set[str]:
    return {
        row["id"] for row in conn.execute("SELECT id FROM entities WHERE world_id=?", (world_id,)).fetchall()
    }


def build_context(
    conn,
    session,
    user_text: str,
    recipient_id: str,
    current_turn_id: str,
    visibility: str = "scene",
    audience_ids: list[str] | None = None,
) -> dict[str, Any]:
    participant_rows = conn.execute(
        "SELECT e.id,e.name,e.kind,e.profile,p.location,p.presence_status "
        "FROM session_presence p JOIN entities e ON e.id=p.entity_id "
        "WHERE p.session_id=? AND p.presence_status='present' ORDER BY e.name",
        (session["id"],)
    ).fetchall()
    scene_participants = [dict(row) for row in participant_rows]
    scene_ids = {item["id"] for item in scene_participants}
    allowed_audience = set(audience_ids or scene_ids)

    participants = scene_participants
    if visibility == "private":
        private_ids = {session["protagonist_entity_id"], recipient_id}
        participants = [item for item in scene_participants if item["id"] in private_ids]

    participant_ids = {item["id"] for item in participants}
    recipient = None
    if recipient_id:
        row = conn.execute(
            "SELECT id,name,kind,profile FROM entities WHERE id=? AND world_id=?",
            (recipient_id, session["world_id"])
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=422, detail="El destinatario no pertenece a este mundo.")
        recipient = dict(row)
        if recipient_id not in participant_ids:
            participants.append(recipient)
            participant_ids.add(recipient_id)

    relationship = []
    if recipient_id:
        relationship = [dict(row) for row in conn.execute(
            "SELECT axis,value,reason FROM relationships WHERE session_id=? AND from_entity_id=? AND to_entity_id=?",
            (session["id"], session["protagonist_entity_id"], recipient_id)
        ).fetchall()]

    inventory = [dict(row) for row in conn.execute(
        "SELECT item_key,display_name,quantity,condition,carrier_entity_id,location "
        "FROM inventory_items WHERE session_id=? AND quantity>0",
        (session["id"],)
    ).fetchall()]

    # Retrieve a larger candidate set, then keep the ten most recent messages
    # that this character could actually have seen or been told.
    message_rows = conn.execute(
        "SELECT role,recipient_entity_id,content,metadata_json,turn_id,turn_index "
        "FROM messages WHERE session_id=? AND turn_id<>? AND generation_status='complete' "
        "ORDER BY turn_index DESC, created_at DESC LIMIT 100",
        (session["id"], current_turn_id)
    ).fetchall()
    recent = []
    for row in message_rows:
        metadata = json.loads(row["metadata_json"] or "{}")
        message_visibility = metadata.get("visibility")
        message_audience = set(metadata.get("audience_ids") or [])

        if message_visibility == "private":
            # Older private messages without audience_ids are visible only to
            # their explicitly selected recipient.
            if not message_audience and row["recipient_entity_id"]:
                message_audience = {row["recipient_entity_id"]}
            if not recipient_id or recipient_id not in message_audience:
                continue
        elif message_audience:
            if recipient_id:
                if recipient_id not in message_audience:
                    continue
            elif not (message_audience & scene_ids):
                continue
        elif not message_visibility and row["recipient_entity_id"]:
            # Backward compatibility: legacy targeted turns had no audience
            # metadata, so do not expose them to a different NPC.
            if not recipient_id or row["recipient_entity_id"] != recipient_id:
                continue

        recent.append({
            "role": row["role"],
            "recipient_entity_id": row["recipient_entity_id"],
            "content": row["content"],
            "visibility": message_visibility or "legacy"
        })
        if len(recent) >= 10:
            break
    recent.reverse()

    trigger_text = (
        user_text + " " + (recipient["name"] if recipient else "") + " " +
        session["current_location"] + " " + " ".join(item["name"] for item in participants)
    ).casefold()
    lore = []
    rows = conn.execute(
        "SELECT title,keywords_json,content,priority,canon_status FROM lore_entries "
        "WHERE world_id=? ORDER BY priority ASC, title ASC",
        (session["world_id"],)
    ).fetchall()
    for row in rows:
        keywords = json.loads(row["keywords_json"])
        if any(str(key).strip() and str(key).casefold() in trigger_text for key in keywords):
            lore.append({
                "title": row["title"], "content": row["content"],
                "priority": row["priority"], "canon_status": row["canon_status"]
            })
        if len(lore) >= 12:
            break

    # Events are available only if the acting NPC witnessed them or the source
    # conversation was visible to them. Pending/rejected proposals are not facts.
    event_rows = conn.execute(
        "SELECT e.kind,e.entity_id,e.description,e.status,e.witnesses_json,"
        "m.recipient_entity_id AS source_recipient_id,m.metadata_json AS source_metadata_json "
        "FROM events e LEFT JOIN messages m ON m.id=e.source_message_id "
        "WHERE e.session_id=? AND e.status='recorded' "
        "ORDER BY e.created_at DESC LIMIT 100",
        (session["id"],)
    ).fetchall()
    recent_events = []
    for row in event_rows:
        witnesses = set(json.loads(row["witnesses_json"] or "[]"))
        source_metadata = json.loads(row["source_metadata_json"] or "{}")
        source_visibility = source_metadata.get("visibility")
        source_audience = set(source_metadata.get("audience_ids") or [])

        if source_visibility == "private":
            if not source_audience and row["source_recipient_id"]:
                source_audience = {row["source_recipient_id"]}
            if not recipient_id or recipient_id not in source_audience:
                continue
        elif source_audience:
            if recipient_id:
                if recipient_id not in source_audience:
                    continue
            elif not (source_audience & scene_ids):
                continue
        elif not source_visibility and row["source_recipient_id"]:
            if not recipient_id or row["source_recipient_id"] != recipient_id:
                continue

        if witnesses:
            if recipient_id and recipient_id not in witnesses:
                continue
            if not recipient_id and not (witnesses & scene_ids):
                continue

        recent_events.append({
            "kind": row["kind"], "entity_id": row["entity_id"],
            "description": row["description"], "status": row["status"],
            "witness_ids": sorted(witnesses)
        })
        if len(recent_events) >= 10:
            break
    recent_events.reverse()

    eco_uses = [dict(row) for row in conn.execute(
        "SELECT target_entity_id,COUNT(*) AS attempts FROM ability_uses "
        "WHERE session_id=? AND ability_key IN ('eco','eco_humano','hipnosis') "
        "GROUP BY target_entity_id", (session["id"],)
    ).fetchall()]

    day, minute = int(session["day"]), int(session["minute_of_day"])
    return {
        "world": {
            "name": session["world_name"],
            "canon_core": ((session["canon_text"] or "").strip()[:6000] +
                           ("\\n[Canon largo recortado; recuperar fichas específicas desde Lorebook.]"
                            if len((session["canon_text"] or "").strip()) > 6000 else ""))
        },
        "state": {
            "day": day, "minute_of_day": minute, "time_label": time_label(day, minute),
            "location": session["current_location"]
        },
        "visibility": visibility,
        "audience_ids": sorted(allowed_audience),
        "participants": participants,
        "recipient": recipient or {},
        "relationship_to_recipient": relationship,
        "inventory": inventory,
        "human_eco_attempts_by_target": eco_uses,
        "recent_messages": recent,
        "recent_events": recent_events,
        "relevant_lore": lore
    }


def write_event(
    conn,
    session_id: str,
    turn_id: str,
    source_message_id: str,
    event,
    valid_ids: set[str],
    allowed_witnesses: set[str] | None = None,
    private_subject_ids: set[str] | None = None,
) -> tuple[str, str, str]:
    event_id = new_id()
    status = "recorded"
    proposed_witnesses = [w for w in event.witness_ids if w]
    if event.kind == "major_change":
        status = "pending"
    if event.entity_id and event.entity_id not in valid_ids:
        status = "pending"
    if any(witness not in valid_ids for witness in proposed_witnesses):
        status = "pending"
    if allowed_witnesses is not None and any(witness not in allowed_witnesses for witness in proposed_witnesses):
        status = "pending"
    if private_subject_ids is not None and event.entity_id and event.entity_id not in private_subject_ids:
        status = "pending"

    # Never store out-of-scope characters as witnesses, even if the model
    # accidentally proposes them in a private turn.
    witnesses = [
        witness for witness in proposed_witnesses
        if witness in valid_ids and (allowed_witnesses is None or witness in allowed_witnesses)
    ]
    conn.execute(
        "INSERT INTO events(id,session_id,turn_id,external_ref,kind,entity_id,description,witnesses_json,status,source_message_id) "
        "VALUES(?,?,?,?,?,?,?,?,?,?)",
        (event_id, session_id, turn_id, event.ref, event.kind, event.entity_id,
         event.description, json.dumps(witnesses, ensure_ascii=False), status, source_message_id)
    )
    return event.ref, event_id, status


def save_change(conn, session_id, turn_id, ref, entity_id, field, operation,
                old_value, proposed_value, accepted_value, status, reason, event_id=None):
    conn.execute(
        "INSERT INTO state_changes(id,session_id,turn_id,external_ref,entity_id,field,operation,"
        "old_value_json,proposed_value_json,accepted_value_json,status,reason,source_event_id,applied_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (new_id(), session_id, turn_id, ref, entity_id, field, operation,
         None if old_value is None else json.dumps(old_value, ensure_ascii=False),
         json.dumps(proposed_value, ensure_ascii=False),
         None if accepted_value is None else json.dumps(accepted_value, ensure_ascii=False),
         status, reason, event_id,
         datetime.now(timezone.utc).isoformat(timespec="seconds") if status == "accepted" else None)
    )


def apply_narrator_result(
    conn, session, turn_id: str, source_message_id: str, user_text: str,
    result: NarratorResponse, authorized_skip, visibility: str = "scene",
    audience_ids: list[str] | None = None, recipient_id: str = "",
):
    valid_ids = world_entity_ids(conn, session["world_id"])
    allowed_witnesses = set(audience_ids or [])
    private_subject_ids = (
        {session["protagonist_entity_id"], recipient_id} if visibility == "private" else None
    )
    event_map: dict[str, dict[str, Any]] = {}
    pending_notes = list(result.pending)
    seen_refs: set[str] = set()
    for event in result.events:
        if event.ref in seen_refs:
            pending_notes.append(f"Evento duplicado omitido: {event.ref}")
            continue
        seen_refs.add(event.ref)
        ref, event_id, status = write_event(
            conn, session["id"], turn_id, source_message_id, event, valid_ids,
            allowed_witnesses=allowed_witnesses, private_subject_ids=private_subject_ids
        )
        if status == "pending":
            pending_notes.append(
                f"Evento {event.ref} requiere revisión: entidad o testigo fuera del alcance autorizado."
            )
        event_map[ref] = {
            "id": event_id, "status": status, "kind": event.kind,
            "entity_id": event.entity_id
        }

    applied = []
    for change in result.state_changes:
        source = event_map.get(change.event_ref)
        status = "pending"
        old_value = None
        accepted_value = None
        reason = change.reason
        proposed = change.model_dump()
        if source is None:
            reason = "La propuesta no referencia un evento de este turno."
        elif source["status"] != "recorded":
            reason = "El evento fuente requiere revisión."
        elif change.entity_id not in valid_ids:
            reason = "La entidad no existe en este mundo."
        elif change.requires_approval:
            reason = "El narrador solicitó aprobación."
        elif change.field == "impression" and change.operation == "note" and change.text_value.strip():
            status = "accepted"
            accepted_value = change.text_value.strip()
            applied.append(f"Impresión temporal registrada para {change.entity_id}.")
        elif change.field in RELATION_AXES and change.operation in {"delta", "set"}:
            row = conn.execute(
                "SELECT id,value FROM relationships WHERE session_id=? AND from_entity_id=? AND to_entity_id=? AND axis=?",
                (session["id"], session["protagonist_entity_id"], change.entity_id, change.field)
            ).fetchone()
            if row is None or row["value"] is None:
                reason = "No existe valor inicial confirmado; el cambio queda pendiente."
            else:
                old_value = float(row["value"])
                new_value = old_value + change.numeric_value if change.operation == "delta" else float(change.numeric_value)
                if change.operation == "delta" and abs(change.numeric_value) > MAX_AUTO_RELATION_DELTA:
                    reason = "El delta automático supera el límite pequeño de este prototipo."
                elif not 0 <= new_value <= 100:
                    reason = "El resultado quedaría fuera del rango 0–100."
                else:
                    status = "accepted"
                    accepted_value = new_value
                    conn.execute(
                        "UPDATE relationships SET value=?,last_change_event_id=?,reason=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                        (new_value, source["id"], change.reason, row["id"])
                    )
                    applied.append(f"{change.field} de {change.entity_id}: {old_value:g} → {new_value:g}.")
        if status == "pending":
            pending_notes.append(f"{change.field} / {change.entity_id or 'sin entidad'}: {reason}")
        save_change(
            conn, session["id"], turn_id, change.ref, change.entity_id, change.field,
            change.operation, old_value, proposed, accepted_value, status, reason,
            source["id"] if source else None
        )

    # Routine inventory changes can be applied only when backed by a recorded
    # object event. Paid acquisitions remain pending until currency is modeled.
    high_impact_item = re.compile(
        r"\b(m[aá]gic[oa]|legendari[oa]|artefact[oa]|reliquia|maldit[oa]|"
        r"[uú]nic[oa]|ancestral|relic|unique|cursed|legendary)\b",
        re.IGNORECASE
    )
    free_acquisition = re.compile(
        r"\b(encontr[oó]|hall[oó]|recogi[oó]|recoge|recoger|levant[oó]|"
        r"regal[oó]|regalo|gratis|te entreg[oó]|te dio|te da|recib[ií] gratis)\b",
        re.IGNORECASE
    )
    paid_acquisition = re.compile(
        r"\b(compr[oó]|comprar|compra|pag[oó]|pagar|precio|cost[oó]|"
        r"monedas? por|oro por|vende por)\b",
        re.IGNORECASE
    )

    for op_index, operation in enumerate(result.inventory_ops):
        source = event_map.get(operation.event_ref)
        status = "pending"
        old_value = None
        accepted_value = None
        reason = "La operación de inventario no superó la validación de bajo riesgo."
        item_name = operation.item_name.strip()
        item_key = item_name.casefold()
        item = None

        if not source:
            reason = "No existe el evento que justifica la operación."
        elif source["status"] != "recorded":
            reason = "El evento de origen está pendiente."
        elif source["kind"] != "object":
            reason = "La operación requiere un evento fuente de tipo object."
        elif not item_name:
            reason = "Falta el nombre del objeto."
        elif operation.carrier_entity_id and operation.carrier_entity_id not in valid_ids:
            reason = "El portador propuesto no pertenece a este mundo."
        elif high_impact_item.search(item_name):
            reason = "El objeto parece único, mágico o de alto impacto; requiere aprobación."
        else:
            item = conn.execute(
                "SELECT * FROM inventory_items WHERE session_id=? AND item_key=?",
                (session["id"], item_key)
            ).fetchone()

            if operation.operation == "acquire":
                source_text = f"{user_text} {source.get('description', '')} {operation.reason}"
                if paid_acquisition.search(source_text):
                    reason = "La adquisición parece tener un coste, pero esta versión aún no tiene contabilidad de moneda; queda pendiente."
                elif not free_acquisition.search(source_text):
                    reason = "No se confirmó que el objeto fuera un hallazgo o regalo gratuito; queda pendiente."
                else:
                    carrier = operation.carrier_entity_id or session["protagonist_entity_id"]
                    location = operation.location.strip() or session["current_location"]
                    old_value = (
                        {"quantity": int(item["quantity"]), "condition": item["condition"],
                         "carrier_entity_id": item["carrier_entity_id"], "location": item["location"]}
                        if item else None
                    )
                    if item:
                        conn.execute(
                            "UPDATE inventory_items SET quantity=quantity+?,condition=?,carrier_entity_id=?,"
                            "location=?,last_event_id=? WHERE id=?",
                            (operation.quantity, operation.condition or item["condition"], carrier,
                             location, source["id"], item["id"])
                        )
                    else:
                        conn.execute(
                            "INSERT INTO inventory_items(id,session_id,item_key,display_name,quantity,condition,"
                            "carrier_entity_id,location,last_event_id) VALUES(?,?,?,?,?,?,?,?,?)",
                            (new_id(), session["id"], item_key, item_name, operation.quantity,
                             operation.condition or "normal", carrier, location, source["id"])
                        )
                    status = "accepted"
                    accepted_value = {
                        "operation": operation.operation, "item_name": item_name,
                        "quantity": operation.quantity, "carrier_entity_id": carrier, "location": location
                    }
                    applied.append(f"Hallazgo/regalo confirmado: {item_name} ×{operation.quantity} añadido al estado.")
            elif operation.operation == "consume":
                if not item or int(item["quantity"]) < operation.quantity:
                    reason = "No existe cantidad suficiente del objeto en el inventario."
                else:
                    old_value = {
                        "quantity": int(item["quantity"]), "condition": item["condition"],
                        "carrier_entity_id": item["carrier_entity_id"], "location": item["location"]
                    }
                    new_quantity = int(item["quantity"]) - operation.quantity
                    conn.execute(
                        "UPDATE inventory_items SET quantity=?,last_event_id=? WHERE id=?",
                        (new_quantity, source["id"], item["id"])
                    )
                    status = "accepted"
                    accepted_value = {"operation": "consume", "item_name": item_name,
                                      "quantity": operation.quantity, "quantity_after": new_quantity}
                    applied.append(f"Consumido: {item_name} ×{operation.quantity}; quedan {new_quantity}.")
            elif operation.operation == "condition":
                if not item:
                    reason = "El objeto no existe en el inventario."
                elif not operation.condition.strip():
                    reason = "Falta el estado final del objeto."
                else:
                    old_value = {
                        "quantity": int(item["quantity"]), "condition": item["condition"],
                        "carrier_entity_id": item["carrier_entity_id"], "location": item["location"]
                    }
                    conn.execute(
                        "UPDATE inventory_items SET condition=?,last_event_id=? WHERE id=?",
                        (operation.condition.strip(), source["id"], item["id"])
                    )
                    status = "accepted"
                    accepted_value = {"operation": "condition", "item_name": item_name,
                                      "condition": operation.condition.strip()}
                    applied.append(f"Estado del objeto actualizado: {item_name} → {operation.condition.strip()}.")
            elif operation.operation in {"drop", "transfer"}:
                if not item:
                    reason = "El objeto no existe en el inventario."
                elif int(item["quantity"]) != operation.quantity:
                    reason = "Esta versión solo automatiza soltar/transferir una pila completa; dividir pilas queda pendiente."
                elif operation.operation == "transfer" and not operation.carrier_entity_id:
                    reason = "La transferencia requiere un portador destinatario."
                else:
                    carrier = "" if operation.operation == "drop" else operation.carrier_entity_id
                    location = operation.location.strip() or session["current_location"]
                    old_value = {
                        "quantity": int(item["quantity"]), "condition": item["condition"],
                        "carrier_entity_id": item["carrier_entity_id"], "location": item["location"]
                    }
                    conn.execute(
                        "UPDATE inventory_items SET carrier_entity_id=?,location=?,last_event_id=? WHERE id=?",
                        (carrier, location, source["id"], item["id"])
                    )
                    status = "accepted"
                    accepted_value = {
                        "operation": operation.operation, "item_name": item_name,
                        "quantity": operation.quantity, "carrier_entity_id": carrier, "location": location
                    }
                    if operation.operation == "drop":
                        applied.append(f"Objeto actualizado: {item_name} dejado en {location}.")
                    else:
                        applied.append(f"Objeto actualizado: {item_name} transferido a {carrier}.")
            else:
                reason = "Operación de inventario desconocida."

        if status == "pending":
            pending_notes.append(f"Inventario: {operation.operation} {item_name} — {reason}")
        save_change(
            conn, session["id"], turn_id, f"inventory-{op_index}-{new_id()[:8]}",
            operation.carrier_entity_id, "inventory", operation.operation, old_value,
            operation.model_dump(), accepted_value, status, reason,
            source["id"] if source else None
        )

    for move_index, movement in enumerate(result.movements):
        source = event_map.get(movement.event_ref)
        status = "pending"
        old_value = None
        accepted_value = None
        reason = "El movimiento requiere revisión."
        destination = movement.destination.strip()
        if not source:
            reason = "No existe el evento que justifica el movimiento."
        elif source["status"] != "recorded":
            reason = "El evento de origen está pendiente."
        elif source["kind"] != "location":
            reason = "El movimiento requiere un evento fuente de tipo location."
        elif source.get("entity_id") != movement.entity_id:
            reason = "La entidad del evento fuente no coincide con la entidad que se mueve."
        elif movement.entity_id not in valid_ids:
            reason = "La entidad que se mueve no existe en este mundo."
        elif movement.entity_id == session["protagonist_entity_id"]:
            reason = "El programa nunca mueve al protagonista sin una acción explícita del usuario."
        elif not destination or len(destination) > 200:
            reason = "El destino está vacío o es demasiado largo."
        elif not movement.reason.strip():
            reason = "Falta la causa narrativa del movimiento."
        else:
            presence = conn.execute(
                "SELECT location,presence_status FROM session_presence WHERE session_id=? AND entity_id=?",
                (session["id"], movement.entity_id)
            ).fetchone()
            if not presence:
                reason = "La entidad no tiene estado de presencia en esta partida."
            else:
                old_value = {"location": presence["location"], "presence_status": presence["presence_status"]}
                presence_status = "present" if destination.casefold() == session["current_location"].casefold() else "away"
                conn.execute(
                    "UPDATE session_presence SET location=?,presence_status=?,updated_at=CURRENT_TIMESTAMP "
                    "WHERE session_id=? AND entity_id=?",
                    (destination, presence_status, session["id"], movement.entity_id)
                )
                status = "accepted"
                accepted_value = {"destination": destination, "presence_status": presence_status}
                applied.append(
                    f"Movimiento de PNJ guardado: {movement.entity_id} → {destination} ({presence_status})."
                )
        if status == "pending":
            pending_notes.append(f"Movimiento de {movement.entity_id}: {reason}")
        save_change(
            conn, session["id"], turn_id, f"movement-{move_index}-{new_id()[:8]}",
            movement.entity_id, "movement", "move", old_value, movement.model_dump(),
            accepted_value, status, reason, source["id"] if source else None
        )

    explicit_power = bool(re.search(r"/psiquico|/hechizo|uso\s+eco|usar\s+eco|intento\s+usar\s+eco", user_text, re.IGNORECASE))
    for use_index, power in enumerate(result.power_uses):
        source = event_map.get(power.event_ref)
        ability = power.ability_key.strip().lower()
        can_apply = bool(explicit_power and source and source["status"] == "recorded" and power.target_entity_id in valid_ids)
        reason = ""
        if not can_apply:
            reason = "El uso no coincide con una acción explícita y un objetivo válido."
        if can_apply and ability in {"eco", "eco_humano", "hipnosis"}:
            count = conn.execute(
                "SELECT COUNT(*) AS n FROM ability_uses WHERE session_id=? AND target_entity_id=? AND ability_key IN ('eco','eco_humano','hipnosis')",
                (session["id"], power.target_entity_id)
            ).fetchone()["n"]
            if count >= 3:
                can_apply = False
                reason = "Ese objetivo ya alcanzó el límite humano de tres intentos de Eco."
        if can_apply:
            try:
                conn.execute(
                    "INSERT INTO ability_uses(id,session_id,turn_id,ability_key,target_entity_id,result,cost_applied,event_id) "
                    "VALUES(?,?,?,?,?,?,?,?)",
                    (new_id(), session["id"], turn_id, ability, power.target_entity_id,
                     power.result, power.cost, source["id"])
                )
                applied.append(f"Uso de {ability} registrado contra {power.target_entity_id}.")
            except Exception:
                can_apply = False
                reason = "El uso ya estaba registrado o la base lo rechazó."
        if not can_apply:
            save_change(
                conn, session["id"], turn_id, f"power-{use_index}-{new_id()[:8]}",
                power.target_entity_id, "power_use", ability, None, power.model_dump(), None,
                "pending", reason or "Uso pendiente de revisión.", source["id"] if source else None
            )
            pending_notes.append(f"Poder {ability}: {reason or 'pendiente de revisión'}.")

    elapsed = 0
    if authorized_skip:
        elapsed = int(authorized_skip["minutes"])
    elif 0 <= result.elapsed_minutes <= 15:
        elapsed = result.elapsed_minutes
    else:
        pending_notes.append(
            f"El narrador propuso {result.elapsed_minutes} minutos; el reloj no avanzó sin autorización."
        )
    if elapsed:
        total_minutes = (int(session["day"]) - 1) * 1440 + int(session["minute_of_day"]) + elapsed
        new_day = total_minutes // 1440 + 1
        new_minute = total_minutes % 1440
        conn.execute(
            "UPDATE sessions SET day=?,minute_of_day=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_day, new_minute, session["id"])
        )
    return applied, pending_notes


def load_state(conn, session_id: str) -> dict[str, Any]:
    session = session_row(conn, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Partida no encontrada.")
    participants = [dict(row) for row in conn.execute(
        "SELECT e.id,e.name,e.kind,p.location,p.presence_status FROM session_presence p "
        "JOIN entities e ON e.id=p.entity_id WHERE p.session_id=? ORDER BY e.name", (session_id,)
    ).fetchall()]
    inventory = [dict(row) for row in conn.execute(
        "SELECT display_name,quantity,condition,carrier_entity_id,location FROM inventory_items "
        "WHERE session_id=? AND quantity>0 ORDER BY display_name", (session_id,)
    ).fetchall()]
    relationships = [dict(row) for row in conn.execute(
        "SELECT from_entity_id,to_entity_id,axis,value,reason FROM relationships WHERE session_id=?",
        (session_id,)
    ).fetchall()]
    pending = [dict(row) for row in conn.execute(
        "SELECT id,entity_id,field,operation,proposed_value_json,reason,created_at FROM state_changes "
        "WHERE session_id=? AND status='pending' ORDER BY created_at DESC LIMIT 100", (session_id,)
    ).fetchall()]
    for item in pending:
        item["proposed_value"] = json.loads(item.pop("proposed_value_json"))
    pending_events = [dict(row) for row in conn.execute(
        "SELECT id,turn_id,kind,entity_id,description,witnesses_json,created_at FROM events "
        "WHERE session_id=? AND status='pending' ORDER BY created_at DESC LIMIT 100", (session_id,)
    ).fetchall()]
    for event in pending_events:
        event["witness_ids"] = json.loads(event.pop("witnesses_json"))
    eco = [dict(row) for row in conn.execute(
        "SELECT target_entity_id,COUNT(*) AS attempts FROM ability_uses "
        "WHERE session_id=? AND ability_key IN ('eco','eco_humano','hipnosis') GROUP BY target_entity_id",
        (session_id,)
    ).fetchall()]
    return {
        "session": {"id": session["id"], "name": session["name"], "world_id": session["world_id"], "protagonist_entity_id": session["protagonist_entity_id"]},
        "state": {
            "day": session["day"], "minute_of_day": session["minute_of_day"],
            "time_label": time_label(session["day"], session["minute_of_day"]),
            "location": session["current_location"]
        },
        "participants": participants, "inventory": inventory,
        "relationships": relationships, "eco_uses": eco, "pending_changes": pending,
        "pending_events": pending_events
    }


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    with database.connection() as conn:
        conn.execute("SELECT 1").fetchone()
    return {"ok": True, "provider": settings.default_provider, "database": "ready"}


@app.get("/api/worlds")
def list_worlds():
    with database.connection() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT id,name,created_at FROM worlds ORDER BY created_at DESC"
        ).fetchall()]


@app.post("/api/worlds/start")
def create_world_and_start(payload: WorldStartCreate):
    world_id = new_id()
    protagonist_id = new_id()
    session_id = new_id()
    entity_ids = [protagonist_id]
    try:
        with database.transaction() as conn:
            conn.execute(
                "INSERT INTO worlds(id,name,canon_text) VALUES(?,?,?)",
                (world_id, payload.name.strip(), payload.canon_text)
            )
            conn.execute(
                "INSERT INTO entities(id,world_id,name,kind,profile) VALUES(?,?,?,?,?)",
                (protagonist_id, world_id, payload.protagonist_name.strip(), "protagonist",
                 payload.protagonist_profile)
            )
            for entity in payload.cast:
                entity_id = new_id()
                conn.execute(
                    "INSERT INTO entities(id,world_id,name,kind,profile) VALUES(?,?,?,?,?)",
                    (entity_id, world_id, entity.name.strip(), entity.kind, entity.profile)
                )
                entity_ids.append(entity_id)
            conn.execute(
                "INSERT INTO sessions(id,world_id,name,day,minute_of_day,current_location,protagonist_entity_id) "
                "VALUES(?,?,?,?,?,?,?)",
                (session_id, world_id, payload.session_name, payload.day, payload.minute_of_day,
                 payload.location, protagonist_id)
            )
            for entity_id in entity_ids:
                conn.execute(
                    "INSERT INTO session_presence(session_id,entity_id,location,presence_status) "
                    "VALUES(?,?,?,'present')",
                    (session_id, entity_id, payload.location)
                )
            valid_ids = set(entity_ids)
            for item in payload.initial_inventory:
                carrier = item.carrier_entity_id or protagonist_id
                if carrier not in valid_ids:
                    raise HTTPException(status_code=422, detail="El portador inicial debe pertenecer al reparto creado.")
                location = item.location or payload.location
                item_key = item.name.strip().casefold()
                conn.execute(
                    "INSERT INTO inventory_items(id,session_id,item_key,display_name,quantity,condition,carrier_entity_id,location) "
                    "VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(session_id,item_key) DO UPDATE SET "
                    "quantity=inventory_items.quantity+excluded.quantity,condition=excluded.condition,"
                    "carrier_entity_id=excluded.carrier_entity_id,location=excluded.location",
                    (new_id(), session_id, item_key, item.name.strip(), item.quantity,
                     item.condition, carrier, location)
                )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=409, detail=f"No se pudo crear el mundo; no se guardó ninguna parte de la operación: {exc}") from exc
    return {
        "world_id": world_id, "session_id": session_id,
        "protagonist_entity_id": protagonist_id, "participant_ids": entity_ids
    }


@app.post("/api/worlds")
def create_world(payload: WorldCreate):
    world_id = new_id()
    try:
        with database.transaction() as conn:
            conn.execute("INSERT INTO worlds(id,name,canon_text) VALUES(?,?,?)",
                         (world_id, payload.name.strip(), payload.canon_text))
    except Exception as exc:
        raise HTTPException(status_code=409, detail=f"No se pudo crear el mundo: {exc}") from exc
    return {"id": world_id, "name": payload.name.strip()}


@app.get("/api/worlds/{world_id}/entities")
def list_entities(world_id: str):
    with database.connection() as conn:
        if conn.execute("SELECT 1 FROM worlds WHERE id=?", (world_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Mundo no encontrado.")
        return [dict(row) for row in conn.execute(
            "SELECT id,name,kind,profile,canonical_status FROM entities WHERE world_id=? ORDER BY name",
            (world_id,)
        ).fetchall()]


@app.post("/api/worlds/{world_id}/entities")
def create_entity(world_id: str, payload: EntityCreate):
    entity_id = new_id()
    with database.transaction() as conn:
        if conn.execute("SELECT 1 FROM worlds WHERE id=?", (world_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Mundo no encontrado.")
        try:
            conn.execute("INSERT INTO entities(id,world_id,name,kind,profile) VALUES(?,?,?,?,?)",
                         (entity_id, world_id, payload.name.strip(), payload.kind, payload.profile))
        except Exception as exc:
            raise HTTPException(status_code=409, detail=f"No se pudo crear la entidad: {exc}") from exc
    return {"id": entity_id, "name": payload.name.strip()}


@app.get("/api/worlds/{world_id}/sessions")
def list_sessions(world_id: str):
    with database.connection() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT id,name,day,minute_of_day,current_location,created_at FROM sessions "
            "WHERE world_id=? ORDER BY created_at DESC", (world_id,)
        ).fetchall()]


@app.post("/api/worlds/{world_id}/sessions")
def create_session(world_id: str, payload: SessionCreate):
    session_id = new_id()
    with database.transaction() as conn:
        if conn.execute("SELECT 1 FROM worlds WHERE id=?", (world_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Mundo no encontrado.")
        valid_ids = world_entity_ids(conn, world_id)
        if payload.protagonist_entity_id not in valid_ids:
            raise HTTPException(status_code=422, detail="El protagonista debe pertenecer al mundo.")
        if any(item not in valid_ids for item in payload.present_entity_ids):
            raise HTTPException(status_code=422, detail="Todos los participantes deben pertenecer al mundo.")
        conn.execute(
            "INSERT INTO sessions(id,world_id,name,day,minute_of_day,current_location,protagonist_entity_id) "
            "VALUES(?,?,?,?,?,?,?)",
            (session_id, world_id, payload.name, payload.day, payload.minute_of_day,
             payload.location, payload.protagonist_entity_id)
        )
        present = set(payload.present_entity_ids) | {payload.protagonist_entity_id}
        for entity_id in present:
            conn.execute(
                "INSERT INTO session_presence(session_id,entity_id,location,presence_status) VALUES(?,?,?,'present')",
                (session_id, entity_id, payload.location)
            )
        for item in payload.initial_inventory:
            carrier = item.carrier_entity_id or payload.protagonist_entity_id
            if carrier not in valid_ids:
                raise HTTPException(status_code=422, detail="El portador de un objeto inicial debe pertenecer al mundo.")
            location = item.location or payload.location
            item_key = item.name.strip().casefold()
            conn.execute(
                "INSERT INTO inventory_items(id,session_id,item_key,display_name,quantity,condition,carrier_entity_id,location) "
                "VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(session_id,item_key) DO UPDATE SET "
                "quantity=inventory_items.quantity+excluded.quantity,condition=excluded.condition,"
                "carrier_entity_id=excluded.carrier_entity_id,location=excluded.location",
                (new_id(), session_id, item_key, item.name.strip(), item.quantity,
                 item.condition, carrier, location)
            )
    return {"id": session_id, "name": payload.name}


@app.post("/api/worlds/{world_id}/lorebook/import")
def import_lorebook(world_id: str, payload: dict[str, Any]):
    entries = payload.get("entries")
    if not isinstance(entries, dict):
        raise HTTPException(status_code=422, detail="El JSON debe incluir el objeto entries compatible con SpicyChat.")
    count = 0
    with database.transaction() as conn:
        if conn.execute("SELECT 1 FROM worlds WHERE id=?", (world_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Mundo no encontrado.")
        for key, entry in entries.items():
            if not isinstance(entry, dict):
                continue
            content = str(entry.get("content", "")).strip()
            if not content:
                continue
            uid = str(entry.get("uid", key))
            title = str(entry.get("comment", f"Entrada {uid}")).strip()
            keywords = entry.get("key", [])
            if not isinstance(keywords, list):
                keywords = []
            conn.execute(
                "INSERT INTO lore_entries(id,world_id,external_uid,title,keywords_json,content,priority,canon_status) "
                "VALUES(?,?,?,?,?,?,?,'confirmed') ON CONFLICT(world_id,external_uid) DO UPDATE SET "
                "title=excluded.title,keywords_json=excluded.keywords_json,content=excluded.content,priority=excluded.priority",
                (f"{world_id}:lore:{uid}", world_id, uid, title,
                 json.dumps([str(k) for k in keywords], ensure_ascii=False), content, int(entry.get("order", 100)))
            )
            count += 1
    return {"imported": count, "world_id": world_id}


@app.post("/api/presets/isekai-sin-destino")
def create_isekai_preset_session():
    lore_path = Path(__file__).resolve().parents[4] / "proyectos" / "isekai-sin-destino" / "LOREBOOK_IMPORT.json"
    if not lore_path.exists():
        raise HTTPException(
            status_code=503,
            detail="No se encontró LOREBOOK_IMPORT.json en el repositorio. Abre el proyecto desde la carpeta organizada completa."
        )
    try:
        lorebook = json.loads(lore_path.read_text(encoding="utf-8"))
        lore_entries = lorebook.get("entries")
        if not isinstance(lore_entries, dict) or not lore_entries:
            raise ValueError("El JSON no contiene entradas válidas.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No se pudo leer el Lorebook del proyecto: {exc}") from exc

    world_name = "Isekai sin Destino"
    location = "Claro del Bosque de las Bestias"
    people = [
        ("protagonista", "Protagonista", "protagonist",
         "Persona adulta de 25 años o más; el usuario elige su género. El narrador nunca decide sus acciones, palabras, pensamientos ni emociones."),
        ("brina-solcor", "Brina Solcor", "character",
         "Guerrera humana de 26 años, prudente, disciplinada y protectora sin ser ingenua. Maneja espada, defensa de línea y retiradas. No tiene magia confirmada."),
        ("ivar-dalen", "Ivar Dalen", "character",
         "Lancero de 27 años, rudo, desconfiado, sarcástico e irónico; cabello largo rubio muy pálido, casi blanco. Su odio no tiene objetivo confirmado."),
        ("maelis-orven", "Maelis Orven", "character",
         "Maga humana de 24 años, curiosa y estudiosa. Conoce Luz tenue y Soplo; no conoce curación ni identifica automáticamente Eco."),
        ("sera-linde", "Sera Linde", "character",
         "Arquera humana de 25 años, independiente, observadora y de humor seco. Rastrea, pero la lluvia, el viento, las flechas limitadas y la cercanía reducen su ventaja."),
        ("timo-venn", "Timo Venn", "character",
         "Encargado de provisiones de 22 años, sociable y pragmático. Controla cuentas, inventario, comercio, nudos y campamento; no es un combatiente entrenado.")
    ]
    canon = (
        "Fantasía medieval abierta. El Bosque de las Bestias ocupa el centro del continente; su corazón interior permanece inexplorado. "
        "Al este están el Reino de Liria y Valdoria; al norte el Mar de las Agujas y Puerto Nácar; al sur Tazhar y Suralba; "
        "al oeste las Montañas del Fin. Nhal-Seren está oculta en el borde septentrional del bosque. "
        "No existe Rey Demonio obligatorio ni misión universal. La aventura empieza el Día 1 a las 08:00 en un claro, con bruma ligera y suelo húmedo. "
        "El protagonista lleva ropa corriente, pañuelo gastado, bolsita de tela vacía y cordel de cáñamo corto; no tiene dinero, comida, agua, armas ni mochila. "
        "Eco humano puede alterar recuerdos concretos con máximo de tres intentos por persona durante toda la aventura; cada intento cuenta y no se recarga. "
        "El volcán está inestable y puede entrar en erupción como máximo el Día 7, salvo que una cadena causal verosímil la adelante. "
        "Las decisiones del protagonista son exclusivamente del usuario. Las entradas específicas se conservan en el Lorebook."
    )
    item_seed = [
        ("Camisa corriente", 1, "normal"),
        ("Pantalones largos", 1, "normal"),
        ("Pañuelo gastado", 1, "gastado"),
        ("Bolsita de tela vacía", 1, "vacía"),
        ("Cordel de cáñamo corto", 1, "usado")
    ]
    with database.transaction() as conn:
        world = conn.execute("SELECT id FROM worlds WHERE name=?", (world_name,)).fetchone()
        if world:
            world_id = world["id"]
        else:
            world_id = new_id()
            conn.execute(
                "INSERT INTO worlds(id,name,canon_text) VALUES(?,?,?)",
                (world_id, world_name, canon)
            )

        entity_ids = []
        protagonist_id = ""
        for suffix, name, kind, profile in people:
            entity = conn.execute(
                "SELECT id FROM entities WHERE world_id=? AND name=?",
                (world_id, name)
            ).fetchone()
            if entity:
                entity_id = entity["id"]
            else:
                entity_id = new_id()
                conn.execute(
                    "INSERT INTO entities(id,world_id,name,kind,profile) VALUES(?,?,?,?,?)",
                    (entity_id, world_id, name, kind, profile)
                )
            entity_ids.append(entity_id)
            if suffix == "protagonista":
                protagonist_id = entity_id

        count = int(conn.execute(
            "SELECT COUNT(*) AS n FROM sessions WHERE world_id=?", (world_id,)
        ).fetchone()["n"])
        session_id = new_id()
        session_name = f"Partida local {count + 1}"
        conn.execute(
            "INSERT INTO sessions(id,world_id,name,day,minute_of_day,current_location,protagonist_entity_id) "
            "VALUES(?,?,?,1,480,?,?)",
            (session_id, world_id, session_name, location, protagonist_id)
        )
        for entity_id in entity_ids:
            conn.execute(
                "INSERT INTO session_presence(session_id,entity_id,location,presence_status) "
                "VALUES(?,?,?,'present')",
                (session_id, entity_id, location)
            )
        for name, quantity, condition in item_seed:
            key = name.casefold()
            conn.execute(
                "INSERT INTO inventory_items(id,session_id,item_key,display_name,quantity,condition,carrier_entity_id,location) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (new_id(), session_id, key, name, quantity, condition, protagonist_id, location)
            )
        imported = 0
        for key, entry in lore_entries.items():
            if not isinstance(entry, dict):
                continue
            content = str(entry.get("content", "")).strip()
            if not content:
                continue
            uid = str(entry.get("uid", key))
            title = str(entry.get("comment", f"Entrada {uid}")).strip()
            keywords = entry.get("key", [])
            if not isinstance(keywords, list):
                keywords = []
            conn.execute(
                "INSERT INTO lore_entries(id,world_id,external_uid,title,keywords_json,content,priority,canon_status) "
                "VALUES(?,?,?,?,?,?,?,'confirmed') ON CONFLICT(world_id,external_uid) DO UPDATE SET "
                "title=excluded.title,keywords_json=excluded.keywords_json,content=excluded.content,priority=excluded.priority",
                (f"{world_id}:lore:{uid}", world_id, uid, title,
                 json.dumps([str(k) for k in keywords], ensure_ascii=False), content, int(entry.get("order", 100)))
            )
            imported += 1
    return {
        "world_id": world_id, "session_id": session_id, "session_name": session_name,
        "participants": len(entity_ids), "lore_entries": imported, "inventory_items": len(item_seed),
        "provider": settings.default_provider
    }


@app.post("/api/demo/seed")
def seed_demo():
    world_name = "Isekai sin Destino — laboratorio local"
    with database.transaction() as conn:
        row = conn.execute("SELECT id FROM worlds WHERE name=?", (world_name,)).fetchone()
        if row:
            world_id = row["id"]
        else:
            world_id = new_id()
            conn.execute(
                "INSERT INTO worlds(id,name,canon_text) VALUES(?,?,?)",
                (world_id, world_name,
                 "Mundo de laboratorio, separado del canon principal. Inicio de ejemplo: Día 1, 08:00, claro del Bosque de las Bestias. La IA no decide las acciones del protagonista. Los PNJ solo conocen hechos presenciados o contados. Eco humano tiene tres intentos por persona, no se recarga.")
            )
        entities = [
            ("protagonista", "Protagonista", "protagonist", "Adulto con ropa corriente. La IA nunca decide sus acciones, palabras, pensamientos ni emociones."),
            ("maelis-orven", "Maelis Orven", "character", "Maga de 24 años, curiosa y estudiosa. Conoce Luz tenue y Soplo. No tiene relación inicial definida con el protagonista."),
            ("brina-solcor", "Brina Solcor", "character", "Guerrera de 26 años, prudente, disciplinada y protectora."),
            ("ivar-dalen", "Ivar Dalen", "character", "Lancero de 27 años, rudo, sarcástico e irónico; desconfía de desconocidos."),
            ("sera-linde", "Sera Linde", "character", "Arquera de 25 años, observadora, independiente y de humor seco."),
            ("timo-venn", "Timo Venn", "character", "Encargado de provisiones de 22 años, sociable y pragmático.")
        ]
        idmap = {}
        for suffix, name, kind, profile in entities:
            entity_id = f"{world_id}:{suffix}"
            idmap[suffix] = entity_id
            conn.execute(
                "INSERT OR IGNORE INTO entities(id,world_id,name,kind,profile) VALUES(?,?,?,?,?)",
                (entity_id, world_id, name, kind, profile)
            )
        session = conn.execute(
            "SELECT id FROM sessions WHERE world_id=? AND name='Prueba de continuidad'",
            (world_id,)
        ).fetchone()
        if session:
            session_id = session["id"]
        else:
            session_id = new_id()
            conn.execute(
                "INSERT INTO sessions(id,world_id,name,day,minute_of_day,current_location,protagonist_entity_id) "
                "VALUES(?,?,?,1,480,?,?)",
                (session_id, world_id, "Prueba de continuidad", "Claro en el Bosque de las Bestias",
                 idmap["protagonista"])
            )
        for entity_id in idmap.values():
            conn.execute(
                "INSERT OR IGNORE INTO session_presence(session_id,entity_id,location,presence_status) "
                "VALUES(?,?,?,'present')",
                (session_id, entity_id, "Claro en el Bosque de las Bestias")
            )
        initial_items = [
            ("ropa corriente", 1, "normal"),
            ("pañuelo gastado", 1, "gastado"),
            ("bolsita de tela vacía", 1, "vacía"),
            ("cordel de cáñamo corto", 1, "usado")
        ]
        for name, quantity, condition in initial_items:
            item_key = name.casefold()
            conn.execute(
                "INSERT OR IGNORE INTO inventory_items(id,session_id,item_key,display_name,quantity,condition,carrier_entity_id,location) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (new_id(), session_id, item_key, name, quantity, condition, idmap["protagonista"],
                 "Claro en el Bosque de las Bestias")
            )
        core_entries = [
            ("core-agency", "Agencia del protagonista", ["agencia del protagonista"],
             "No decidas acciones, diálogo, pensamientos ni emociones del protagonista.", 1),
            ("core-eco", "Eco humano", ["Eco", "hipnosis de memoria", "uso de Eco"],
             "Eco altera de forma limitada recuerdos humanos. Máximo tres intentos por persona en toda la aventura; cada intento cuenta aunque falle y no se recarga.", 2),
            ("core-time", "Reloj narrativo", ["hora", "tiempo transcurrido", "salto"],
             "Inicio Día 1 a las 08:00. La charla breve no salta horas. Los saltos de tiempo requieren autorización explícita.", 3)
        ]
        for uid, title, keywords, content, priority in core_entries:
            conn.execute(
                "INSERT OR IGNORE INTO lore_entries(id,world_id,external_uid,title,keywords_json,content,priority,canon_status) "
                "VALUES(?,?,?,?,?,?,?,'confirmed')",
                (f"{world_id}:lore:{uid}", world_id, uid, title,
                 json.dumps(keywords, ensure_ascii=False), content, priority)
            )
    return {"world_id": world_id, "session_id": session_id, "provider": settings.default_provider}


@app.get("/api/sessions/{session_id}/state")
def get_session_state(session_id: str):
    with database.connection() as conn:
        return load_state(conn, session_id)


@app.get("/api/sessions/{session_id}/messages")
def get_messages(session_id: str):
    with database.connection() as conn:
        if conn.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Partida no encontrada.")
        return [dict(row) for row in conn.execute(
            "SELECT id,turn_id,turn_index,role,recipient_entity_id,content,provider,generation_status,metadata_json,created_at "
            "FROM messages WHERE session_id=? ORDER BY turn_index ASC, CASE role WHEN 'user' THEN 0 ELSE 1 END ASC, created_at ASC", (session_id,)
        ).fetchall()]


@app.post("/api/sessions/{session_id}/turns")
async def submit_turn(session_id: str, payload: TurnRequest):
    authorized_skip = parse_skip(payload.text)
    client_request_id = payload.request_id.strip()
    if len(client_request_id) < 8:
        raise HTTPException(status_code=422, detail="request_id debe tener al menos 8 caracteres y mantenerse igual al reintentar.")
    if payload.visibility == "private" and not payload.recipient_id:
        raise HTTPException(status_code=422, detail="Un turno privado requiere seleccionar un destinatario.")
    turn_id = new_id()
    user_message_id = new_id()
    with database.transaction() as conn:
        session = session_row(conn, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Partida no encontrada.")
        if payload.recipient_id and conn.execute(
            "SELECT 1 FROM entities WHERE id=? AND world_id=?",
            (payload.recipient_id, session["world_id"])
        ).fetchone() is None:
            raise HTTPException(status_code=422, detail="El destinatario no pertenece a este mundo.")

        current_scene_ids = {
            row["entity_id"] for row in conn.execute(
                "SELECT entity_id FROM session_presence WHERE session_id=? AND presence_status='present'",
                (session_id,)
            ).fetchall()
        }
        if payload.visibility == "private":
            audience_ids = sorted({session["protagonist_entity_id"], payload.recipient_id})
        else:
            audience_ids = sorted(current_scene_ids)

        existing_user = conn.execute(
            "SELECT * FROM messages WHERE session_id=? AND client_request_id=? AND role='user'",
            (session_id, client_request_id)
        ).fetchone()
        if existing_user:
            old_metadata = json.loads(existing_user["metadata_json"] or "{}")
            old_visibility = old_metadata.get("visibility", "scene")
            if (existing_user["content"] != payload.text
                    or existing_user["recipient_entity_id"] != payload.recipient_id
                    or existing_user["provider"] != payload.provider
                    or old_visibility != payload.visibility):
                raise HTTPException(status_code=409, detail="request_id ya usado con otro contenido, destinatario, proveedor o alcance.")
            saved_audience = old_metadata.get("audience_ids")
            if isinstance(saved_audience, list) and saved_audience:
                audience_ids = [str(item) for item in saved_audience]
            existing_assistant = conn.execute(
                "SELECT content,generation_status FROM messages WHERE session_id=? AND turn_id=? AND role='assistant'",
                (session_id, existing_user["turn_id"])
            ).fetchone()
            if existing_assistant and existing_assistant["generation_status"] == "complete":
                saved_state = load_state(conn, session_id)
                saved_events = [dict(row) for row in conn.execute(
                    "SELECT kind,entity_id,description,status FROM events WHERE session_id=? AND turn_id=? ORDER BY created_at",
                    (session_id, existing_user["turn_id"])
                ).fetchall()]
                return {
                    "turn_id": existing_user["turn_id"],
                    "narration": existing_assistant["content"],
                    "events": saved_events,
                    "applied_changes": ["Reintento idempotente: se reutilizó la respuesta guardada; no se repitieron operaciones."],
                    "pending_notes": [],
                    "state": saved_state,
                    "replayed": True
                }
            if existing_user["generation_status"] == "processing":
                raise HTTPException(status_code=409, detail="Ese turno sigue procesándose; no se creó una segunda solicitud.")
            turn_id = existing_user["turn_id"]
            user_message_id = existing_user["id"]
            turn_index = int(existing_user["turn_index"])
            conn.execute(
                "UPDATE messages SET generation_status='processing' WHERE id=?",
                (user_message_id,)
            )
        else:
            turn_index = int(conn.execute(
                "SELECT COALESCE(MAX(turn_index),0)+1 AS n FROM messages WHERE session_id=?",
                (session_id,)
            ).fetchone()["n"])
            conn.execute(
                "INSERT INTO messages(id,session_id,turn_id,client_request_id,turn_index,role,recipient_entity_id,content,provider,generation_status,metadata_json) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (user_message_id, session_id, turn_id, client_request_id, turn_index, "user",
                 payload.recipient_id, payload.text, payload.provider, "processing",
                 json.dumps({"visibility": payload.visibility, "audience_ids": audience_ids}, ensure_ascii=False))
            )
        session = session_row(conn, session_id)
        context = build_context(
            conn, session, payload.text, payload.recipient_id, turn_id,
            visibility=payload.visibility, audience_ids=audience_ids
        )

    provider_name = payload.provider or settings.default_provider
    try:
        provider = make_provider(provider_name, settings)
        result = await provider.generate({
            "user_message": payload.text,
            "recipient_id": payload.recipient_id,
            "context": context,
            "authorized_skip": authorized_skip or {}
        })
    except ProviderError as exc:
        with database.transaction() as conn:
            conn.execute(
                "UPDATE messages SET generation_status='failed' WHERE id=?",
                (user_message_id,)
            )
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        with database.transaction() as conn:
            conn.execute(
                "UPDATE messages SET generation_status='failed' WHERE id=?",
                (user_message_id,)
            )
        raise HTTPException(status_code=502, detail=f"Fallo del proveedor: {exc}") from exc

    assistant_message_id = new_id()
    with database.transaction() as conn:
        session = session_row(conn, session_id)
        conn.execute(
            "INSERT INTO messages(id,session_id,turn_id,client_request_id,turn_index,role,recipient_entity_id,content,provider,generation_status,metadata_json) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (assistant_message_id, session_id, turn_id, client_request_id, turn_index, "assistant",
             payload.recipient_id, result.narration, provider_name, "complete",
             json.dumps({
                 "pending": result.pending,
                 "visibility": payload.visibility,
                 "audience_ids": audience_ids
             }, ensure_ascii=False))
        )
        conn.execute(
            "UPDATE messages SET generation_status='complete' WHERE id=?",
            (user_message_id,)
        )
        applied, pending = apply_narrator_result(
            conn, session, turn_id, user_message_id, payload.text, result, authorized_skip,
            visibility=payload.visibility, audience_ids=audience_ids, recipient_id=payload.recipient_id
        )
    with database.connection() as conn:
        state = load_state(conn, session_id)
        events = [dict(row) for row in conn.execute(
            "SELECT kind,entity_id,description,status FROM events WHERE session_id=? AND turn_id=? ORDER BY created_at",
            (session_id, turn_id)
        ).fetchall()]
    return {
        "turn_id": turn_id,
        "narration": result.narration,
        "events": events,
        "applied_changes": applied,
        "pending_notes": pending,
        "state": state,
        "replayed": False
    }

@app.post("/api/sessions/{session_id}/changes/{change_id}/approve")
def approve_change(session_id: str, change_id: str, payload: ApprovalRequest):
    with database.transaction() as conn:
        row = conn.execute(
            "SELECT * FROM state_changes WHERE id=? AND session_id=? AND status='pending'",
            (change_id, session_id)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Propuesta pendiente no encontrada.")
        source_event_id = row["source_event_id"]
        if not source_event_id:
            raise HTTPException(status_code=422, detail="La propuesta no tiene un evento fuente; no puede aprobarse como hecho.")
        source_status = conn.execute("SELECT status FROM events WHERE id=?", (source_event_id,)).fetchone()
        if source_status is None or source_status["status"] != "recorded":
            raise HTTPException(status_code=422, detail="El evento fuente no está confirmado; la propuesta no puede aplicarse.")
        proposed = json.loads(row["proposed_value_json"])
        field = row["field"]
        session = session_row(conn, session_id)
        entity_id = row["entity_id"]
        accepted = None
        if field in RELATION_AXES:
            current = conn.execute(
                "SELECT id,value FROM relationships WHERE session_id=? AND from_entity_id=? AND to_entity_id=? AND axis=?",
                (session_id, session["protagonist_entity_id"], entity_id, field)
            ).fetchone()
            number = int(proposed.get("numeric_value", 0))
            operation = row["operation"]
            if operation == "delta":
                if current is None or current["value"] is None:
                    if payload.initial_value is None:
                        raise HTTPException(status_code=422, detail="No hay valor inicial. Envía initial_value entre 0 y 100.")
                    base = payload.initial_value
                else:
                    base = float(current["value"])
                accepted = base + number
            elif operation == "set":
                accepted = float(number)
            else:
                raise HTTPException(status_code=422, detail="Operación numérica no compatible.")
            if not 0 <= accepted <= 100:
                raise HTTPException(status_code=422, detail="El resultado debe estar entre 0 y 100.")
            if current:
                conn.execute(
                    "UPDATE relationships SET value=?,reason=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (accepted, row["reason"], current["id"])
                )
            else:
                conn.execute(
                    "INSERT INTO relationships(id,session_id,from_entity_id,to_entity_id,axis,value,reason) VALUES(?,?,?,?,?,?,?)",
                    (new_id(), session_id, session["protagonist_entity_id"], entity_id, field, accepted, row["reason"])
                )
        elif field == "inventory":
            op = proposed
            name = str(op.get("item_name", "")).strip()
            quantity = int(op.get("quantity", 0))
            if not name or quantity < 1:
                raise HTTPException(status_code=422, detail="Objeto y cantidad positiva requeridos.")
            key = name.casefold()
            item = conn.execute(
                "SELECT * FROM inventory_items WHERE session_id=? AND item_key=?", (session_id, key)
            ).fetchone()
            operation = str(op.get("operation", ""))
            carrier = str(op.get("carrier_entity_id") or session["protagonist_entity_id"])
            location = str(op.get("location") or "")
            source_event_id = row["source_event_id"]
            if operation == "acquire":
                if item:
                    conn.execute(
                        "UPDATE inventory_items SET quantity=quantity+?,carrier_entity_id=?,location=?,last_event_id=? WHERE id=?",
                        (quantity, carrier, location, source_event_id, item["id"])
                    )
                else:
                    conn.execute(
                        "INSERT INTO inventory_items(id,session_id,item_key,display_name,quantity,condition,carrier_entity_id,location,last_event_id) "
                        "VALUES(?,?,?,?,?,?,?,?,?)",
                        (new_id(), session_id, key, name, quantity, op.get("condition") or "normal",
                         carrier, location, source_event_id)
                    )
            elif operation == "consume":
                if not item or item["quantity"] < quantity:
                    raise HTTPException(status_code=422, detail="No hay cantidad suficiente en el inventario.")
                conn.execute("UPDATE inventory_items SET quantity=quantity-?,last_event_id=? WHERE id=?",
                             (quantity, source_event_id, item["id"]))
            elif operation in {"drop", "transfer", "condition"}:
                if not item:
                    raise HTTPException(status_code=422, detail="El objeto no existe en el inventario.")
                if operation == "drop":
                    conn.execute("UPDATE inventory_items SET carrier_entity_id='',location=?,last_event_id=? WHERE id=?",
                                 (location, source_event_id, item["id"]))
                elif operation == "transfer":
                    conn.execute("UPDATE inventory_items SET carrier_entity_id=?,location=?,last_event_id=? WHERE id=?",
                                 (carrier, location, source_event_id, item["id"]))
                else:
                    conn.execute("UPDATE inventory_items SET condition=?,last_event_id=? WHERE id=?",
                                 (op.get("condition") or item["condition"], source_event_id, item["id"]))
            else:
                raise HTTPException(status_code=422, detail="Operación de inventario desconocida.")
            accepted = {"operation": operation, "item_name": name, "quantity": quantity}
        elif field == "movement":
            destination = str(proposed.get("destination", "")).strip()
            if not destination:
                raise HTTPException(status_code=422, detail="Falta el destino.")
            if entity_id == session["protagonist_entity_id"]:
                conn.execute("UPDATE sessions SET current_location=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                             (destination, session_id))
            else:
                conn.execute("UPDATE session_presence SET location=?,updated_at=CURRENT_TIMESTAMP "
                             "WHERE session_id=? AND entity_id=?", (destination, session_id, entity_id))
            accepted = {"destination": destination}
        elif field == "power_use":
            ability = str(proposed.get("ability_key", "")).strip().lower()
            target = str(proposed.get("target_entity_id", ""))
            if not ability or target not in world_entity_ids(conn, session["world_id"]):
                raise HTTPException(status_code=422, detail="Poder u objetivo no válido.")
            if ability in {"eco", "eco_humano", "hipnosis"}:
                count = conn.execute(
                    "SELECT COUNT(*) AS n FROM ability_uses WHERE session_id=? AND target_entity_id=? "
                    "AND ability_key IN ('eco','eco_humano','hipnosis')", (session_id, target)
                ).fetchone()["n"]
                if count >= 3:
                    raise HTTPException(status_code=422, detail="Ese objetivo ya agotó los tres intentos de Eco humano.")
            conn.execute(
                "INSERT INTO ability_uses(id,session_id,turn_id,ability_key,target_entity_id,result,cost_applied,event_id) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (new_id(), session_id, row["turn_id"], ability, target, proposed.get("result", ""),
                 max(0, int(proposed.get("cost", 1))), row["source_event_id"])
            )
            accepted = {"ability_key": ability, "target_entity_id": target}
        elif field == "impression" and row["operation"] == "note":
            accepted = proposed.get("text_value", "")
        else:
            raise HTTPException(status_code=422, detail=f"No se puede aprobar automáticamente el campo {field}.")
        conn.execute(
            "UPDATE state_changes SET status='accepted',accepted_value_json=?,applied_at=? WHERE id=?",
            (json.dumps(accepted, ensure_ascii=False), datetime.now(timezone.utc).isoformat(timespec="seconds"), change_id)
        )
    return {"approved": True, "change_id": change_id, "accepted_value": accepted}


@app.post("/api/sessions/{session_id}/changes/{change_id}/reject")
def reject_change(session_id: str, change_id: str):
    with database.transaction() as conn:
        row = conn.execute(
            "SELECT id FROM state_changes WHERE id=? AND session_id=? AND status='pending'",
            (change_id, session_id)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Propuesta pendiente no encontrada.")
        conn.execute(
            "UPDATE state_changes SET status='rejected',applied_at=? WHERE id=?",
            (datetime.now(timezone.utc).isoformat(timespec="seconds"), change_id)
        )
    return {"rejected": True, "change_id": change_id}


@app.post("/api/sessions/{session_id}/events/{event_id}/approve")
def approve_event(session_id: str, event_id: str):
    with database.transaction() as conn:
        event = conn.execute(
            "SELECT * FROM events WHERE id=? AND session_id=? AND status='pending'",
            (event_id, session_id)
        ).fetchone()
        if event is None:
            raise HTTPException(status_code=404, detail="Evento pendiente no encontrado.")
        session = session_row(conn, session_id)
        valid_ids = world_entity_ids(conn, session["world_id"])
        if event["entity_id"] and event["entity_id"] not in valid_ids:
            raise HTTPException(status_code=422, detail="La entidad del evento no existe; corrige la ficha o rechaza el evento.")
        witnesses = json.loads(event["witnesses_json"])
        if any(witness not in valid_ids for witness in witnesses):
            raise HTTPException(status_code=422, detail="Hay testigos no registrados; el evento no puede confirmarse.")
        conn.execute("UPDATE events SET status='recorded' WHERE id=?", (event_id,))
    return {"approved": True, "event_id": event_id}


@app.post("/api/sessions/{session_id}/events/{event_id}/reject")
def reject_event(session_id: str, event_id: str):
    with database.transaction() as conn:
        event = conn.execute(
            "SELECT id FROM events WHERE id=? AND session_id=? AND status='pending'",
            (event_id, session_id)
        ).fetchone()
        if event is None:
            raise HTTPException(status_code=404, detail="Evento pendiente no encontrado.")
        conn.execute("UPDATE events SET status='rejected' WHERE id=?", (event_id,))
        conn.execute(
            "UPDATE state_changes SET status='rejected',applied_at=? "
            "WHERE source_event_id=? AND status='pending'",
            (datetime.now(timezone.utc).isoformat(timespec="seconds"), event_id)
        )
    return {"rejected": True, "event_id": event_id}


@app.post("/api/sessions/{session_id}/backup")
def backup_session_database(session_id: str):
    with database.connection() as conn:
        if conn.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Partida no encontrada.")
    backup_path = database.path.parent / "backups" / f"backup-{session_id}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.sqlite3"
    database.backup_to(str(backup_path))
    return {"backup_created": True, "path": str(backup_path)}
