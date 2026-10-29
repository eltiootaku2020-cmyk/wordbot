import hashlib
import hmac
import json
import logging
import os
import re
import sqlite3
import unicodedata
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .db import Database
from .models import ApprovalRequest, ContextPreviewRequest, EntityCreate, LocalCommandRequest, LocalSettingsUpdate, ManualPromptRequest, NarratorResponse, SessionCreate, SessionRestoreRequest, TurnRequest, WorldCreate, WorldStartCreate
from .providers import ProviderError, build_manual_prompt, make_provider

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
logger = logging.getLogger(__name__)
database = Database(settings.db_path)
database.initialize()

def recover_interrupted_turns() -> int:
    """Mark unfinished user turns as failed after an application restart.

    The original user text and audience metadata remain available so the UI can
    offer a safe retry. No narrator output or state change is fabricated.
    """
    recovered = 0
    with database.transaction() as conn:
        rows = conn.execute(
            "SELECT id,metadata_json FROM messages "
            "WHERE role='user' AND generation_status='processing'"
        ).fetchall()
        for row in rows:
            try:
                metadata = json.loads(row["metadata_json"] or "{}")
                if not isinstance(metadata, dict):
                    metadata = {}
            except (TypeError, ValueError, json.JSONDecodeError):
                metadata = {}
            metadata["recovered_after_restart"] = True
            metadata["recovery_note"] = (
                "El turno se interrumpió antes de terminar. No se aplicaron "
                "cambios; revisa el mensaje y reintenta."
            )
            cursor = conn.execute(
                "UPDATE messages SET generation_status='failed',metadata_json=? "
                "WHERE id=? AND role='user' AND generation_status='processing'",
                (json.dumps(metadata, ensure_ascii=False), row["id"])
            )
            recovered += max(0, cursor.rowcount)
    return recovered


@asynccontextmanager
async def app_lifespan(_: FastAPI):
    """Recover stale in-progress markers before the local UI accepts new turns."""
    recovered = recover_interrupted_turns()
    if recovered:
        logger.warning(
            "Se recuperaron %s turno(s) interrumpido(s) tras reiniciar la aplicación.",
            recovered
        )
    yield


app = FastAPI(title="Gestor local de canon", version="0.1.0", lifespan=app_lifespan)
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

RELATION_AXES = {
    "confidence", "suspicion", "friendship", "respect", "rivalry",
    "resentment", "fear", "gratitude_debt", "cooperation", "attraction"
}
MAX_AUTO_RELATION_DELTA = 3
MAX_LORE_ENTRIES = 8
MAX_LORE_CHARS = 4500
MIN_LORE_CHARS = 500
MAX_CONFIGURABLE_LORE_CHARS = 12000
MAX_CANON_CORE_CHARS = 3000
MAX_HISTORY_CANDIDATES = 500
MAX_RECENT_MESSAGES = 10
MAX_RELEVANT_MESSAGES = 2
MAX_RECENT_MESSAGE_CHARS = 1000
MAX_RECENT_EVENTS = 6
MAX_RELEVANT_EVENTS = 2
MAX_EVENT_DESCRIPTION_CHARS = 450
MAX_CONTEXT_INVENTORY_ITEMS = 40


def get_lore_budget_chars(conn) -> int:
    """Read the persistent local Lorebook budget, clamped to safe bounds."""
    row = conn.execute(
        "SELECT value_json FROM app_settings WHERE setting_key='lore_budget_chars'"
    ).fetchone()
    value = MAX_LORE_CHARS
    if row is not None:
        try:
            value = int(json.loads(row["value_json"]))
        except (TypeError, ValueError, json.JSONDecodeError):
            value = MAX_LORE_CHARS
    return min(MAX_CONFIGURABLE_LORE_CHARS, max(MIN_LORE_CHARS, value))


def save_lore_budget_chars(conn, value: int) -> None:
    if not MIN_LORE_CHARS <= value <= MAX_CONFIGURABLE_LORE_CHARS:
        raise HTTPException(
            status_code=422,
            detail=f"El presupuesto Lorebook debe estar entre {MIN_LORE_CHARS} y {MAX_CONFIGURABLE_LORE_CHARS} caracteres."
        )
    conn.execute(
        "INSERT INTO app_settings(setting_key,value_json) VALUES('lore_budget_chars',?) "
        "ON CONFLICT(setting_key) DO UPDATE SET value_json=excluded.value_json,updated_at=CURRENT_TIMESTAMP",
        (json.dumps(value),)
    )


def keyword_matches(text: str, keyword: str) -> bool:
    """Match a full word/phrase, not an accidental substring in a longer word."""
    normalized_text = " ".join((text or "").casefold().split())
    normalized_keyword = " ".join((keyword or "").casefold().split())
    if not normalized_keyword:
        return False
    return re.search(rf"(?<!\w){re.escape(normalized_keyword)}(?!\w)", normalized_text) is not None


def manual_context_hash(payload: dict[str, Any]) -> str:
    """Stable fingerprint so a pasted reply cannot mutate a changed game state."""
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()




HISTORY_STOPWORDS = {
    "para", "desde", "hasta", "esto", "esta", "este", "estos", "estas", "como",
    "cuando", "donde", "porque", "pero", "sobre", "entre", "ella", "ellos", "ellas",
    "usted", "ustedes", "algo", "nada", "todo", "toda", "todos", "todas", "mismo",
    "misma", "ahora", "antes", "despues", "luego", "hacer", "hace", "tiene", "tienen",
    "tener", "estaba", "estaban", "estar", "estoy", "eres", "ser", "soy", "son", "fue",
    "hacia", "lugar", "actual", "quiero", "puedo", "puede", "pueden", "debe", "deben",
    "decir", "dijo", "dice", "responde", "responder", "personaje", "protagonista", "mirar",
    "veo", "muy", "mas", "menos", "cada", "realmente", "dentro", "fuera", "tambien",
    "mientras", "entonces", "unos", "unas", "una", "uno", "que", "por", "con", "sin",
    "del", "las", "los", "sus", "les", "nos", "hay", "seria", "serian"
}


def _relevance_token_variants(token: str) -> set[str]:
    """Return conservative Spanish inflection variants without NLP dependencies."""
    variants = {token}
    if len(token) < 5:
        return variants

    # Keep the original and common plural reductions; lexical retrieval may use
    # either variant, but never changes the stored facts or applies game actions.
    if token.endswith("ces") and len(token) > 5:
        variants.add(token[:-3] + "z")
    if token.endswith("s"):
        variants.add(token[:-1])
    if token.endswith("es") and len(token) > 5:
        variants.add(token[:-2])

    # A compact suffix set covers common verb forms (e.g. recoger/recogí,
    # hablar/hablando) and participles. The minimum stem length avoids very
    # broad matches; this is retrieval assistance, not a linguistic validator.
    suffixes = (
        "ariamos", "eriamos", "iriamos", "aremos", "eremos", "iremos",
        "asteis", "isteis", "abamos", "ieron", "aron", "iendo", "ando",
        "ados", "adas", "idos", "idas", "aste", "iste", "aban", "abas",
        "aria", "eria", "iria", "aria", "aron", "amos", "emos", "imos",
        "ado", "ido", "aba", "ian", "ias", "era", "ara", "ira",
        "ian", "ias", "io", "ia", "an", "en", "as", "es", "os",
        "ar", "er", "ir", "a", "e", "o", "i"
    )
    for suffix in suffixes:
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            variants.add(token[:-len(suffix)])
            break
    return {variant for variant in variants if len(variant) >= 4}


def relevance_terms(*texts: str) -> set[str]:
    """Build a bounded Spanish keyword set with conservative inflection matching."""
    words: set[str] = set()
    for text in texts:
        normalized = unicodedata.normalize("NFD", str(text or "").casefold())
        normalized = "".join(char for char in normalized if not unicodedata.combining(char))
        for token in re.findall(r"[a-z0-9]{4,}", normalized):
            if token not in HISTORY_STOPWORDS:
                words.update(_relevance_token_variants(token))
    return words


def history_relevance_score(text: str, query_terms: set[str]) -> int:
    return len(query_terms.intersection(relevance_terms(text)))


def select_history_items(items, text_getter, maximum: int, relevant_slots: int,
                         query_terms: set[str]) -> dict[int, str]:
    """Keep newest items plus a tiny number of older, lexically relevant facts."""
    if maximum <= 0:
        return {}
    recent_reserve = max(0, maximum - min(relevant_slots, maximum))
    selected: dict[int, str] = {}
    for index in range(min(recent_reserve, len(items))):
        selected[index] = "incluido dentro de la ventana reciente"

    scored = []
    for index in range(recent_reserve, len(items)):
        score = history_relevance_score(text_getter(items[index]), query_terms)
        if score:
            scored.append((score, index))
    for score, index in sorted(scored, key=lambda value: (-value[0], value[1]))[:relevant_slots]:
        selected[index] = f"recuperado por relevancia: coincidencia de {score} términos"

    for index in range(len(items)):
        if len(selected) >= min(maximum, len(items)):
            break
        selected.setdefault(index, "incluido para completar la ventana reciente")
    return selected


def _local_command_distance(left: str, right: str) -> int:
    """Damerau-Levenshtein distance for short command names, including transpositions."""
    rows, cols = len(left) + 1, len(right) + 1
    distance = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        distance[i][0] = i
    for j in range(cols):
        distance[0][j] = j
    for i in range(1, rows):
        for j in range(1, cols):
            cost = 0 if left[i - 1] == right[j - 1] else 1
            distance[i][j] = min(
                distance[i - 1][j] + 1,
                distance[i][j - 1] + 1,
                distance[i - 1][j - 1] + cost,
            )
            if i > 1 and j > 1 and left[i - 1] == right[j - 2] and left[i - 2] == right[j - 1]:
                distance[i][j] = min(distance[i][j], distance[i - 2][j - 2] + 1)
    return distance[-1][-1]


def parse_local_command(text: str) -> str | None:
    """Recognize local commands, flag likely typos, and leave other slash actions to the narrator."""
    candidate = (text or "").strip()
    if not candidate.startswith("/"):
        return None
    match = re.match(r"^/([\wáéíóúñü-]+)", candidate, re.IGNORECASE)
    if not match:
        return None
    token = match.group(1).casefold()
    supported = ("estado", "inventario", "guardar", "ayuda", "salto")
    if token in supported:
        if token == "salto":
            return "salto"
        if candidate[len(match.group(0)):].strip():
            raise HTTPException(status_code=422, detail=f"/{token} no admite argumentos. Usa /ayuda para ver los comandos disponibles.")
        return token
    closest = min(supported, key=lambda command: _local_command_distance(token, command))
    distance = _local_command_distance(token, closest)
    if distance <= 2:
        raise HTTPException(
            status_code=422,
            detail=f"Parece un error tipográfico en /{closest}. Usa /{closest} o /ayuda; los comandos de poderes y acciones no reservados pueden empezar con /."
        )
    # Slash-prefixed powers, spells, or game actions (e.g. /psiquico) are narrative input.
    return None


def new_id() -> str:
    return uuid.uuid4().hex


def parse_skip(text: str) -> dict[str, Any] | None:
    """Parse explicit minute/hour/day jumps; malformed /salto commands never fall through to the narrator."""
    candidate = (text or "").strip()
    if not re.match(r"^/salto\b", candidate, re.IGNORECASE):
        return None
    match = re.fullmatch(
        r"/salto\s+(\d+)\s*(minutos?|mins?|m|horas?|h|d[ií]as?)\s*(?:->\s*(.*))?",
        candidate, re.IGNORECASE
    )
    if not match:
        raise HTTPException(
            status_code=422,
            detail="Formato de salto incorrecto. Usa, por ejemplo, /salto 30 minutos, /salto 2 horas o /salto 1 día -> destino."
        )
    amount = int(match.group(1))
    unit = match.group(2).casefold()
    if unit.startswith("d"):
        minutes = amount * 1440
    elif unit.startswith("h"):
        minutes = amount * 60
    else:
        minutes = amount
    if minutes < 1 or minutes > 7 * 24 * 60:
        raise HTTPException(status_code=422, detail="El salto debe estar entre 1 minuto y 7 días.")
    destination = (match.group(3) or "").strip()
    if len(destination) > 180:
        raise HTTPException(status_code=422, detail="El destino del salto no puede superar 180 caracteres.")
    return {"minutes": minutes, "destination": destination}


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


def capture_turn_state(conn, session_id: str) -> dict[str, Any]:
    """Capture the mutable, authoritative game state before a turn."""
    session = conn.execute(
        "SELECT day,minute_of_day,current_location,updated_at FROM sessions WHERE id=?",
        (session_id,)
    ).fetchone()
    if session is None:
        raise HTTPException(status_code=404, detail="Partida no encontrada.")
    return {
        "session": dict(session),
        "presence": [dict(row) for row in conn.execute(
            "SELECT * FROM session_presence WHERE session_id=? ORDER BY entity_id", (session_id,)
        ).fetchall()],
        "inventory": [dict(row) for row in conn.execute(
            "SELECT * FROM inventory_items WHERE session_id=? ORDER BY item_key", (session_id,)
        ).fetchall()],
        "resources": [dict(row) for row in conn.execute(
            "SELECT * FROM resources WHERE session_id=? ORDER BY resource_key", (session_id,)
        ).fetchall()],
        "relationships": [dict(row) for row in conn.execute(
            "SELECT * FROM relationships WHERE session_id=? ORDER BY from_entity_id,to_entity_id,axis",
            (session_id,)
        ).fetchall()],
        "ability_uses": [dict(row) for row in conn.execute(
            "SELECT * FROM ability_uses WHERE session_id=? ORDER BY created_at,id", (session_id,)
        ).fetchall()]
    }


def create_turn_snapshot(conn, session_id: str, turn_id: str, event_sequence: int) -> None:
    state = capture_turn_state(conn, session_id)
    conn.execute(
        "INSERT OR IGNORE INTO snapshots(id,session_id,turn_id,event_sequence,state_json) "
        "VALUES(?,?,?,?,?)",
        (new_id(), session_id, turn_id, event_sequence,
         json.dumps(state, ensure_ascii=False, separators=(",", ":")))
    )


def restore_turn_state(conn, session_id: str, state: dict[str, Any]) -> None:
    """Restore only authoritative mutable state; transcript and audit rows stay available."""
    session = state.get("session") or {}
    conn.execute(
        "UPDATE sessions SET day=?,minute_of_day=?,current_location=?,updated_at=? WHERE id=?",
        (int(session["day"]), int(session["minute_of_day"]), str(session["current_location"]),
         session.get("updated_at") or datetime.now(timezone.utc).isoformat(timespec="seconds"), session_id)
    )

    # Table names are fixed in code, never supplied by the model or user.
    table_rows = [
        ("session_presence", state.get("presence", [])),
        ("inventory_items", state.get("inventory", [])),
        ("resources", state.get("resources", [])),
        ("relationships", state.get("relationships", [])),
        ("ability_uses", state.get("ability_uses", []))
    ]
    for table, rows in table_rows:
        conn.execute(f"DELETE FROM {table} WHERE session_id=?", (session_id,))
        for row in rows:
            columns = list(row.keys())
            placeholders = ",".join("?" for _ in columns)
            column_sql = ",".join(columns)
            conn.execute(
                f"INSERT INTO {table}({column_sql}) VALUES({placeholders})",
                tuple(row[column] for column in columns)
            )


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
    include_diagnostics: bool = False,
) -> dict[str, Any]:
    participant_rows = conn.execute(
        "SELECT e.id,e.name,e.kind,e.profile,p.location,"
        "CASE WHEN LOWER(p.location)=LOWER(?) THEN 'present' ELSE 'away' END AS presence_status "
        "FROM session_presence p JOIN entities e ON e.id=p.entity_id "
        "WHERE p.session_id=? AND LOWER(p.location)=LOWER(?) ORDER BY e.name",
        (session["current_location"], session["id"], session["current_location"])
    ).fetchall()
    scene_participants = [dict(row) for row in participant_rows]
    scene_ids = {item["id"] for item in scene_participants}
    # The protagonist is always the active actor at the session's current location,
    # even if an older record has not yet synchronized its presence row.
    if session["protagonist_entity_id"] not in scene_ids:
        protagonist_row = conn.execute(
            "SELECT id,name,kind,profile FROM entities WHERE id=? AND world_id=?",
            (session["protagonist_entity_id"], session["world_id"])
        ).fetchone()
        if protagonist_row:
            protagonist = dict(protagonist_row)
            protagonist.update({"location": session["current_location"], "presence_status": "present"})
            scene_participants.append(protagonist)
            scene_ids.add(protagonist["id"])
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

    include_global_inventory = bool(re.search(r"/estado|/guardar|\binventario\b", user_text, re.IGNORECASE))
    carrier_ids = sorted(participant_ids | {session["protagonist_entity_id"]})
    placeholders = ",".join("?" for _ in carrier_ids) or "?"
    if include_global_inventory:
        inventory_rows = conn.execute(
            "SELECT item_key,display_name,quantity,condition,carrier_entity_id,location "
            "FROM inventory_items WHERE session_id=? AND quantity>0 ORDER BY display_name LIMIT ?",
            (session["id"], MAX_CONTEXT_INVENTORY_ITEMS)
        ).fetchall()
    else:
        inventory_rows = conn.execute(
            "SELECT item_key,display_name,quantity,condition,carrier_entity_id,location "
            f"FROM inventory_items WHERE session_id=? AND quantity>0 AND "
            f"(carrier_entity_id IN ({placeholders}) OR (carrier_entity_id='' AND LOWER(location)=LOWER(?))) "
            "ORDER BY display_name LIMIT ?",
            (session["id"], *carrier_ids, session["current_location"], MAX_CONTEXT_INVENTORY_ITEMS)
        ).fetchall()
    inventory = [dict(row) for row in inventory_rows]
    resource_balances = [dict(row) for row in conn.execute(
        "SELECT resource_key,display_name,quantity,unit FROM resources "
        "WHERE session_id=? ORDER BY display_name LIMIT 30", (session["id"],)
    ).fetchall()]


    # Keep enough candidates for long sessions; recent dialogue is always present,
    # while two spare slots can recover older messages relevant to the current action.
    message_rows = conn.execute(
        "SELECT id,role,recipient_entity_id,content,metadata_json,turn_id,turn_index,generation_status "
        "FROM messages WHERE session_id=? AND turn_id<>? "
        "ORDER BY turn_index DESC, created_at DESC, rowid DESC LIMIT ?",
        (session["id"], current_turn_id, MAX_HISTORY_CANDIDATES)
    ).fetchall()
    recipient_name = recipient.get("name", "") if recipient else ""
    relevance_query_terms = relevance_terms(
        user_text, recipient_name, session["current_location"],
        *(item.get("name", "") for item in participants)
    )
    eligible_messages = []
    excluded_messages_debug = []
    for row in message_rows:
        try:
            metadata = json.loads(row["metadata_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            metadata = None
        if not isinstance(metadata, dict):
            excluded_messages_debug.append({
                "message_id": row["id"], "turn_id": row["turn_id"],
                "turn_index": row["turn_index"], "role": row["role"],
                "status": row["generation_status"], "visibility": "invalid",
                "reason": "metadatos dañados; se excluye por seguridad"
            })
            continue

        message_visibility = metadata.get("visibility")
        raw_audience = metadata.get("audience_ids") or []
        if not isinstance(raw_audience, list) or any(not isinstance(value, str) for value in raw_audience):
            excluded_messages_debug.append({
                "message_id": row["id"], "turn_id": row["turn_id"],
                "turn_index": row["turn_index"], "role": row["role"],
                "status": row["generation_status"], "visibility": "invalid",
                "reason": "audiencia dañada; se excluye por seguridad"
            })
            continue
        message_audience = set(raw_audience)
        reason = ""

        if row["generation_status"] != "complete":
            reason = f"mensaje en estado {row['generation_status']}; solo los turnos completos se recuperan"
        elif message_visibility == "private":
            # Older private messages without audience_ids are visible only to
            # their explicitly selected recipient.
            if not message_audience and row["recipient_entity_id"]:
                message_audience = {row["recipient_entity_id"]}
            if not recipient_id or recipient_id not in message_audience:
                reason = "el destinatario activo no pertenece a la audiencia privada"
        elif message_audience:
            if recipient_id:
                if recipient_id not in message_audience:
                    reason = "el destinatario activo no pertenece a la audiencia de escena"
            elif not (message_audience & scene_ids):
                reason = "la audiencia histórica no coincide con la escena actual"
        elif not message_visibility and row["recipient_entity_id"]:
            # Backward compatibility for targeted turns written before audience metadata existed.
            if not recipient_id or row["recipient_entity_id"] != recipient_id:
                reason = "mensaje histórico dirigido a otro destinatario"

        if reason:
            excluded_messages_debug.append({
                "message_id": row["id"], "turn_id": row["turn_id"],
                "turn_index": row["turn_index"], "role": row["role"],
                "status": row["generation_status"],
                "visibility": message_visibility or "legacy", "reason": reason
            })
            continue
        eligible_messages.append({
            "row": row, "metadata": metadata, "visibility": message_visibility or "legacy",
            "audience": message_audience
        })

    chosen_messages = select_history_items(
        eligible_messages, lambda item: item["row"]["content"] or "",
        MAX_RECENT_MESSAGES, MAX_RELEVANT_MESSAGES, relevance_query_terms
    )
    recent = []
    selected_messages_debug = []
    for index, item in enumerate(eligible_messages):
        row = item["row"]
        selection_reason = chosen_messages.get(index)
        if selection_reason is None:
            excluded_messages_debug.append({
                "message_id": row["id"], "turn_id": row["turn_id"],
                "turn_index": row["turn_index"], "role": row["role"],
                "status": row["generation_status"], "visibility": item["visibility"],
                "reason": "fuera del límite contextual; no fue priorizado por relevancia"
            })
            continue
        message_content = row["content"] or ""
        recent.append({
            "role": row["role"],
            "recipient_entity_id": row["recipient_entity_id"],
            "content": message_content[:MAX_RECENT_MESSAGE_CHARS],
            "content_truncated": len(message_content) > MAX_RECENT_MESSAGE_CHARS,
            "visibility": item["visibility"]
        })
        access_reason = (
            "la audiencia privada incluye al destinatario activo"
            if item["visibility"] == "private"
            else "destinatario incluido en audiencia de escena"
            if item["audience"] and recipient_id
            else "mensaje accesible por alcance de escena o historial compartido"
        )
        selected_messages_debug.append({
            "message_id": row["id"], "turn_id": row["turn_id"],
            "turn_index": row["turn_index"], "role": row["role"],
            "visibility": item["visibility"],
            "reason": f"{access_reason}; {selection_reason}"
        })
    recent.reverse()
    selected_messages_debug.reverse()

    trigger_sources = []
    if user_text.strip():
        trigger_sources.append({"source": "mensaje actual", "text": user_text, "score": 5})
    if recipient and recipient.get("name"):
        trigger_sources.append({"source": "destinatario", "text": recipient["name"], "score": 4})
    if session["current_location"]:
        trigger_sources.append({"source": "ubicación actual", "text": session["current_location"], "score": 4})
    for participant in participants:
        if participant.get("name"):
            trigger_sources.append({
                "source": "personaje presente", "text": participant["name"], "score": 3
            })

    lore_rows = conn.execute(
        "SELECT title,keywords_json,content,priority,canon_status FROM lore_entries "
        "WHERE world_id=? ORDER BY priority ASC, title ASC",
        (session["world_id"],)
    ).fetchall()
    lore_candidates = []
    no_trigger_count = 0
    for row in lore_rows:
        keywords = json.loads(row["keywords_json"])
        hits = []
        score = 0
        for source in trigger_sources:
            for keyword in keywords:
                key = str(keyword).strip()
                if key and keyword_matches(source["text"], key):
                    hits.append({"source": source["source"], "keyword": key})
                    score = max(score, source["score"])
        if hits:
            # De-duplicate the explanation while preserving its order.
            unique_hits = []
            seen_hits = set()
            for hit in hits:
                pair = (hit["source"], hit["keyword"])
                if pair not in seen_hits:
                    seen_hits.add(pair)
                    unique_hits.append(hit)
            lore_candidates.append({
                "title": row["title"], "content": row["content"],
                "priority": int(row["priority"]), "canon_status": row["canon_status"],
                "score": score, "hits": unique_hits,
                "chars": len(row["title"]) + len(row["content"])
            })
        else:
            no_trigger_count += 1

    lore_candidates.sort(key=lambda item: (-item["score"], item["priority"], item["title"].casefold()))
    lore_budget_chars = get_lore_budget_chars(conn)
    lore = []
    selected_lore_debug = []
    omitted_lore_debug = []
    lore_chars_used = 0
    for item in lore_candidates:
        if len(lore) >= MAX_LORE_ENTRIES:
            omitted_lore_debug.append({"title": item["title"], "reason": "límite de entradas"})
            continue
        item_chars = item["chars"]
        if lore_chars_used + item_chars > lore_budget_chars:
            omitted_lore_debug.append({"title": item["title"], "reason": "presupuesto de caracteres"})
            continue
        lore_chars_used += item_chars
        lore.append({
            "title": item["title"], "content": item["content"],
            "priority": item["priority"], "canon_status": item["canon_status"]
        })
        selected_lore_debug.append({
            "title": item["title"], "priority": item["priority"],
            "characters": item_chars, "triggered_by": item["hits"]
        })


    # Events are available only if the acting NPC witnessed them or the source
    # conversation was visible to them. Pending/rejected proposals are not facts.
    event_rows = conn.execute(
        "SELECT e.id,e.turn_id,e.kind,e.entity_id,e.description,e.status,e.witnesses_json,e.created_at,"
        "m.id AS matched_source_message_id,m.recipient_entity_id AS source_recipient_id,"
        "m.metadata_json AS source_metadata_json "
        "FROM events e LEFT JOIN messages m ON m.id=e.source_message_id "
        "WHERE e.session_id=? ORDER BY e.created_at DESC,e.rowid DESC LIMIT ?",
        (session["id"], MAX_HISTORY_CANDIDATES)
    ).fetchall()
    eligible_events = []
    excluded_events_debug = []
    for row in event_rows:
        try:
            witnesses_raw = json.loads(row["witnesses_json"] or "[]")
            source_metadata = json.loads(row["source_metadata_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            witnesses_raw, source_metadata = None, None
        if (not isinstance(witnesses_raw, list)
                or any(not isinstance(value, str) for value in witnesses_raw)
                or not isinstance(source_metadata, dict)):
            excluded_events_debug.append({
                "event_id": row["id"], "turn_id": row["turn_id"],
                "kind": row["kind"], "entity_id": row["entity_id"],
                "status": row["status"], "witness_ids": [],
                "reason": "metadatos/testigos dañados; se excluye por seguridad"
            })
            continue

        witnesses = set(witnesses_raw)
        source_visibility = source_metadata.get("visibility")
        raw_source_audience = source_metadata.get("audience_ids") or []
        if not isinstance(raw_source_audience, list) or any(not isinstance(value, str) for value in raw_source_audience):
            excluded_events_debug.append({
                "event_id": row["id"], "turn_id": row["turn_id"],
                "kind": row["kind"], "entity_id": row["entity_id"],
                "status": row["status"], "witness_ids": sorted(witnesses),
                "reason": "audiencia del evento dañada; se excluye por seguridad"
            })
            continue
        source_audience = set(raw_source_audience)
        reason = ""

        # Legacy events without audience metadata can still be scoped when the
        # linked source message retains its recipient or witnesses identify who
        # observed it. With neither provenance nor witnesses, do not disclose an
        # unscoped fact to a model; leave the record available in the audit UI.
        if not row["matched_source_message_id"] and not witnesses:
            reason = "evento histórico sin mensaje fuente ni testigos; se excluye por seguridad"
        elif row["status"] != "recorded":
            reason = f"evento en estado {row['status']}; solo los eventos registrados se recuperan como hechos"
        elif source_visibility == "private":
            if not source_audience and row["source_recipient_id"]:
                source_audience = {row["source_recipient_id"]}
            if not recipient_id or recipient_id not in source_audience:
                reason = "la audiencia privada del evento no incluye al destinatario activo"
        elif source_audience:
            if recipient_id:
                if recipient_id not in source_audience:
                    reason = "la audiencia del evento no incluye al destinatario activo"
            elif not (source_audience & scene_ids):
                reason = "la audiencia del evento no coincide con la escena actual"
        elif not source_visibility and row["source_recipient_id"]:
            if not recipient_id or row["source_recipient_id"] != recipient_id:
                reason = "el evento proviene de un mensaje dirigido a otro destinatario"

        if not reason and witnesses:
            if recipient_id and recipient_id not in witnesses:
                reason = "el destinatario activo no presenció el evento ni figura entre sus testigos"
            elif not recipient_id and not (witnesses & scene_ids):
                reason = "ningún testigo del evento coincide con la escena actual"

        if reason:
            excluded_events_debug.append({
                "event_id": row["id"], "turn_id": row["turn_id"],
                "kind": row["kind"], "entity_id": row["entity_id"],
                "status": row["status"], "witness_ids": sorted(witnesses),
                "reason": reason
            })
            continue
        eligible_events.append({
            "row": row, "witnesses": witnesses,
            "source_visibility": source_visibility
        })

    chosen_events = select_history_items(
        eligible_events, lambda item: item["row"]["description"] or "",
        MAX_RECENT_EVENTS, MAX_RELEVANT_EVENTS, relevance_query_terms
    )
    recent_events = []
    selected_events_debug = []
    for index, item in enumerate(eligible_events):
        row = item["row"]
        witnesses = item["witnesses"]
        selection_reason = chosen_events.get(index)
        if selection_reason is None:
            excluded_events_debug.append({
                "event_id": row["id"], "turn_id": row["turn_id"],
                "kind": row["kind"], "entity_id": row["entity_id"],
                "status": row["status"], "witness_ids": sorted(witnesses),
                "reason": "fuera del límite contextual; no fue priorizado por relevancia"
            })
            continue
        event_description = row["description"] or ""
        recent_events.append({
            "kind": row["kind"], "entity_id": row["entity_id"],
            "description": event_description[:MAX_EVENT_DESCRIPTION_CHARS],
            "description_truncated": len(event_description) > MAX_EVENT_DESCRIPTION_CHARS,
            "status": row["status"], "witness_ids": sorted(witnesses)
        })
        access_reason = (
            "evento accesible por audiencia privada autorizada"
            if item["source_visibility"] == "private"
            else "evento accesible por audiencia y testigos válidos"
        )
        selected_events_debug.append({
            "event_id": row["id"], "turn_id": row["turn_id"],
            "kind": row["kind"], "entity_id": row["entity_id"],
            "description_preview": event_description[:160],
            "witness_ids": sorted(witnesses),
            "reason": f"{access_reason}; {selection_reason}"
        })
    recent_events.reverse()
    selected_events_debug.reverse()

    eco_uses = [dict(row) for row in conn.execute(
        "SELECT target_entity_id,COUNT(*) AS attempts FROM ability_uses "
        "WHERE session_id=? AND ability_key IN ('eco','eco_humano','hipnosis') "
        "GROUP BY target_entity_id", (session["id"],)
    ).fetchall()]

    day, minute = int(session["day"]), int(session["minute_of_day"])
    canon_text = (session["canon_text"] or "").strip()
    context = {
        "world": {
            "name": session["world_name"],
            "canon_core": canon_text[:MAX_CANON_CORE_CHARS] +
                          ("\n[Canon largo recortado; recuperar fichas específicas desde Lorebook.]"
                           if len(canon_text) > MAX_CANON_CORE_CHARS else "")
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
        "resources": resource_balances,
        "human_eco_attempts_by_target": eco_uses,
        "recent_messages": recent,
        "recent_events": recent_events,
        "relevant_lore": lore
    }
    context_chars = len(json.dumps(context, ensure_ascii=False))
    diagnostics = {
        "selected_lore": selected_lore_debug,
        "omitted_lore_by_limit": omitted_lore_debug,
        "lore_without_trigger_count": no_trigger_count,
        "lore_chars_used": lore_chars_used,
        "lore_chars_budget": lore_budget_chars,
        "lore_entries_selected": len(lore),
        "lore_entries_max": MAX_LORE_ENTRIES,
        "selected_messages": selected_messages_debug,
        "excluded_messages": excluded_messages_debug,
        "selected_events": selected_events_debug,
        "excluded_events": excluded_events_debug,
        "recent_messages_selected": len(recent),
        "recent_events_selected": len(recent_events),
        "messages_excluded_count": len(excluded_messages_debug),
        "events_excluded_count": len(excluded_events_debug),
        "messages_recovered_by_relevance": sum(1 for item in selected_messages_debug if "recuperado por relevancia" in item["reason"]),
        "events_recovered_by_relevance": sum(1 for item in selected_events_debug if "recuperado por relevancia" in item["reason"]),
        "inventory_items_selected": len(inventory),
        "context_characters": context_chars,
        "limits": {
            "canon_core_chars": MAX_CANON_CORE_CHARS,
            "message_chars_each": MAX_RECENT_MESSAGE_CHARS,
            "messages_max": MAX_RECENT_MESSAGES,
            "messages_candidate_max": MAX_HISTORY_CANDIDATES,
            "messages_relevance_slots": MAX_RELEVANT_MESSAGES,
            "events_candidate_max": MAX_HISTORY_CANDIDATES,
            "events_relevance_slots": MAX_RELEVANT_EVENTS,
            "event_chars_each": MAX_EVENT_DESCRIPTION_CHARS,
            "events_max": MAX_RECENT_EVENTS
        }
    }
    if include_diagnostics:
        context["_diagnostics"] = diagnostics
    return context


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


def split_user_action_clauses(user_text: str) -> list[str]:
    """Remove interrogative phrases and split independent/contrasting actions."""
    text = re.sub(r"[^.!?]*\?", " ", user_text or "")
    return [
        clause.strip()
        for clause in re.split(
            r"(?<=[.!?;])\s*|\b(?:pero|sino|aunque|sin embargo|en cambio|y|e)\b\s*|[,，:]\s*|[\r\n]+",
            text,
            flags=re.IGNORECASE
        )
        if clause.strip()
    ]


def user_mentions_label(user_text: str, label: str) -> bool:
    """Return whether the current user message names the item/resource in question."""
    stopwords = {"de", "del", "la", "las", "el", "los", "un", "una", "unos", "unas", "and", "the"}
    tokens = [
        token for token in re.findall(r"[\wáéíóúüñ]+", (label or "").casefold())
        if len(token) > 1 and token not in stopwords
    ]
    for token in tokens:
        variants = {token}
        if token.endswith("s"):
            variants.add(token[:-1])
        if token.endswith("es"):
            variants.add(token[:-2])
        for variant in variants:
            if variant and re.search(rf"\b{re.escape(variant)}(?:s|es)?\b", user_text or "", re.IGNORECASE):
                return True
    return False


def has_positive_user_action(user_text: str, action_pattern: re.Pattern[str]) -> bool:
    """Only affirmative actions in the user's message are evidence; narration is never evidence."""
    negation_prefix = re.compile(
        r"\b(?:no|nunca|jam[aá]s|tampoco|ni|rechazo|evito|cancelo|me niego a)\b"
        r"(?:\s+\w+){0,3}\s*$",
        re.IGNORECASE
    )
    hypothetical_prefix = re.compile(
        r"\b(?:quiero|quisiera|puedo|podr[ií]a|deber[ií]a|intento|intentar|planeo|"
        r"pienso|considero|pregunto|preguntar|me gustar[ií]a|tal vez|quiz[aá]s|voy a|si|cuando|mientras)\b"
        r"(?:\s+\w+){0,3}\s*$",
        re.IGNORECASE
    )
    noun_prefix = re.compile(
        r"\b(?:el|la|los|las|un|una|unos|unas|mi|mis|tu|tus|su|sus|este|esta|"
        r"ese|esa|del|al)\s*$",
        re.IGNORECASE
    )
    for clause in split_user_action_clauses(user_text):
        if "¿" in clause or "?" in clause:
            continue
        for match in action_pattern.finditer(clause):
            prefix = clause[:match.start()].rstrip()
            if (negation_prefix.search(prefix) or hypothetical_prefix.search(prefix)
                    or noun_prefix.search(prefix)):
                continue
            return True
    return False


def has_positive_user_action_for_label(
    user_text: str, action_pattern: re.Pattern[str], label: str
) -> bool:
    """Require the affirmative action and the relevant item/resource in the same clause."""
    return any(
        "¿" not in clause and "?" not in clause
        and user_mentions_label(clause, label)
        and has_positive_user_action(clause, action_pattern)
        for clause in split_user_action_clauses(user_text)
    )


PURCHASE_ACTION_PATTERN = re.compile(
    r"\b(?:compro|compramos|compr[eé]|compraste|compr[oó]|compraron|"
    r"adquiero|adquirimos|adquir[ií]|adquiriste|adquiri[oó]|adquirieron|"
    r"pago|pagamos|pagu[eé]|pagaste|pag[oó]|pagaron|he comprado|hemos comprado|"
    r"he pagado|hemos pagado|me llevo|nos llevamos)\b",
    re.IGNORECASE
)
FREE_ACQUISITION_ACTION_PATTERN = re.compile(
    r"\b(?:recojo|recogemos|recog[ií]|recogiste|recogi[oó]|recogieron|"
    r"levanto|levantamos|levant[eé]|levantaste|levant[oó]|levantaron|"
    r"tomo|tomamos|tom[eé]|tomaste|tom[oó]|tomaron|agarro|agarramos|agarr[eé]|"
    r"agarraste|agarr[oó]|agarraron|recibo|recibimos|recib[ií]|recibiste|"
    r"recibi[oó]|recibieron|acepto|aceptamos|acept[eé]|aceptaste|acept[oó]|"
    r"aceptaron|me regalan|me regalaron|me entregan|me entregaron)\b",
    re.IGNORECASE
)
RESOURCE_GAIN_ACTION_PATTERN = re.compile(
    r"\b(?:recibo|recibimos|recib[ií]|recibiste|recibi[oó]|recibieron|"
    r"cobro|cobramos|cobr[eé]|cobraste|cobr[oó]|cobraron|gano|ganamos|gan[eé]|"
    r"ganaste|gan[oó]|ganaron|obtengo|obtenemos|obtuve|obtuviste|obtuvo|"
    r"obtuvieron|acepto|aceptamos|acept[eé]|aceptaste|acept[oó]|aceptaron|"
    r"me pagan|me pagaron|me entregan|me entregaron|vendo|vendemos|vend[ií]|"
    r"vendiste|vendi[oó]|vendieron|he recibido|hemos recibido)\b",
    re.IGNORECASE
)
RESOURCE_SPEND_ACTION_PATTERN = re.compile(
    r"\b(?:pago|pagamos|pagu[eé]|pagaste|pag[oó]|pagaron|he pagado|hemos pagado|"
    r"gasto|gastamos|gast[eé]|gastaste|gast[oó]|gastaron|alquilo|alquilamos|"
    r"alquil[eé]|alquilaste|alquil[oó]|alquilaron|compro|compramos|compr[eé]|"
    r"compraste|compr[oó]|compraron|entrego|entregamos|entregu[eé]|entregaste|"
    r"entreg[oó]|entregaron|pierdo|perdemos|perd[ií]|perdiste|perdi[oó]|"
    r"perdieron|he gastado|hemos gastado|me llevo|nos llevamos)\b",
    re.IGNORECASE
)
POWER_ACTION_PATTERN = re.compile(
    r"/(?:ps[ií]quic[oa]?|hechizo|eco|hipnosis)\b|"
    r"\b(?:uso|utilizo|activo|lanzo|empleo|invoco)\s+(?:el\s+)?"
    r"(?:poder\s+de\s+)?(?:eco|hipnosis)\b",
    re.IGNORECASE
)


def apply_narrator_result(
    conn, session, turn_id: str, source_message_id: str, user_text: str,
    result: NarratorResponse, authorized_skip, visibility: str = "scene",
    audience_ids: list[str] | None = None, recipient_id: str = "",
):
    if authorized_skip:
        # A time skip is a direct user command, not permission to invent loot,
        # relationships, powers or NPC movements while the protagonist is absent.
        side_effect_fields = ("events", "state_changes", "movements", "inventory_ops", "resource_ops", "power_uses")
        ignored = sum(len(getattr(result, field)) for field in side_effect_fields)
        pending = list(result.pending)
        if ignored:
            note = f"El salto temporal no aplicó {ignored} propuestas de estado del narrador; registra los hechos concretos en otro turno."
            if len(pending) >= 30:
                pending[-1] = note
            else:
                pending.append(note)
        result = result.model_copy(update={
            "events": [], "state_changes": [], "movements": [],
            "inventory_ops": [], "resource_ops": [], "power_uses": [],
            "elapsed_minutes": int(authorized_skip["minutes"]),
            "pending": pending
        })
    valid_ids = world_entity_ids(conn, session["world_id"])
    allowed_witnesses = set(audience_ids or [])
    private_subject_ids = (
        {session["protagonist_entity_id"], recipient_id} if visibility == "private" else None
    )
    explicit_power = has_positive_user_action(user_text, POWER_ACTION_PATTERN)

    # Generated event text may document a proposed outcome, but cannot authorize it.
    unauthorized_acquisition_refs = set()
    for operation in result.inventory_ops:
        if operation.operation != "acquire":
            continue
        positive_purchase = has_positive_user_action_for_label(
            user_text, PURCHASE_ACTION_PATTERN, operation.item_name
        )
        positive_pickup = has_positive_user_action_for_label(
            user_text, FREE_ACQUISITION_ACTION_PATTERN, operation.item_name
        )
        if (
            (operation.cost > 0 and not positive_purchase)
            or (operation.cost == 0 and not (positive_purchase or positive_pickup))
        ):
            unauthorized_acquisition_refs.add(operation.event_ref)

    unauthorized_resource_refs = set()
    for operation in result.resource_ops:
        action_pattern = (
            RESOURCE_GAIN_ACTION_PATTERN if operation.operation == "gain"
            else RESOURCE_SPEND_ACTION_PATTERN
        )
        user_authorized_resource = (
            has_positive_user_action_for_label(user_text, action_pattern, operation.resource_key)
            or has_positive_user_action_for_label(user_text, action_pattern, operation.display_name)
        )
        if not user_authorized_resource:
            unauthorized_resource_refs.add(operation.event_ref)

    def explicitly_used_power_for_target(power) -> bool:
        target = conn.execute(
            "SELECT name FROM entities WHERE id=? AND world_id=?",
            (power.target_entity_id, session["world_id"])
        ).fetchone()
        if target and has_positive_user_action_for_label(
            user_text, POWER_ACTION_PATTERN, target["name"]
        ):
            return True
        # A short command such as /eco is an explicit action when it yields only
        # one proposed target. Multiple targets still require target-specific evidence.
        distinct_targets = {item.target_entity_id for item in result.power_uses}
        return bool(
            explicit_power and len(distinct_targets) == 1
            and (not recipient_id or recipient_id == power.target_entity_id)
        )

    unauthorized_power_refs = set()
    power_uses_by_event: dict[str, list[PowerUseProposal]] = {}
    for power in result.power_uses:
        power_uses_by_event.setdefault(power.event_ref, []).append(power)
    for event in result.events:
        if event.kind != "power":
            continue
        associated_uses = power_uses_by_event.get(event.ref, [])
        if associated_uses:
            if any(not explicitly_used_power_for_target(power) for power in associated_uses):
                unauthorized_power_refs.add(event.ref)
        elif not explicit_power:
            unauthorized_power_refs.add(event.ref)
    unauthorized_effect_refs = (
        unauthorized_acquisition_refs | unauthorized_resource_refs | unauthorized_power_refs
    )

    event_map: dict[str, dict[str, Any]] = {}
    pending_notes = list(result.pending)
    event_ref_counts: dict[str, int] = {}
    for event in result.events:
        event_ref_counts[event.ref] = event_ref_counts.get(event.ref, 0) + 1
    duplicate_event_refs = {ref for ref, count in event_ref_counts.items() if count > 1}
    seen_refs: set[str] = set()
    for event in result.events:
        if event.ref in seen_refs:
            continue
        seen_refs.add(event.ref)
        ref, event_id, status = write_event(
            conn, session["id"], turn_id, source_message_id, event, valid_ids,
            allowed_witnesses=allowed_witnesses, private_subject_ids=private_subject_ids
        )
        if event.ref in duplicate_event_refs:
            # A repeated external reference makes every dependent proposal ambiguous.
            # Preserve one audit row, but never allow it to authorize a state change.
            conn.execute("UPDATE events SET status='pending' WHERE id=?", (event_id,))
            status = "pending"
            pending_notes.append(
                f"Referencia de evento duplicada '{event.ref}': evento y cambios asociados requieren revisión."
            )
        elif event.ref in unauthorized_effect_refs:
            conn.execute("UPDATE events SET status='pending' WHERE id=?", (event_id,))
            status = "pending"
            pending_notes.append(
                f"Evento {event.ref} requiere revisión: falta una acción afirmativa del usuario en el mensaje actual."
            )
        elif status == "pending":
            pending_notes.append(
                f"Evento {event.ref} requiere revisión: entidad o testigo fuera del alcance autorizado."
            )
        event_map[ref] = {
            "id": event_id, "status": status, "kind": event.kind,
            "entity_id": event.entity_id, "description": event.description
        }

    applied = []
    purchase_event_refs: set[str] = set()
    change_ref_counts: dict[str, int] = {}
    for change in result.state_changes:
        change_ref_counts[change.ref] = change_ref_counts.get(change.ref, 0) + 1
    duplicate_change_refs = {ref for ref, count in change_ref_counts.items() if count > 1}
    relation_key_counts: dict[tuple[str, str], int] = {}
    for change in result.state_changes:
        if change.field in RELATION_AXES:
            key = (change.entity_id, change.field)
            relation_key_counts[key] = relation_key_counts.get(key, 0) + 1
    duplicate_relation_keys = {key for key, count in relation_key_counts.items() if count > 1}
    seen_change_refs: set[str] = set()
    for change in result.state_changes:
        if change.ref in seen_change_refs:
            continue
        seen_change_refs.add(change.ref)
        source = event_map.get(change.event_ref)
        status = "pending"
        old_value = None
        accepted_value = None
        reason = change.reason
        proposed = change.model_dump()
        relation_key = (change.entity_id, change.field)
        if change.ref in duplicate_change_refs:
            reason = f"La referencia '{change.ref}' se repite en la respuesta; la propuesta ambigua no se aplicó."
        elif change.field in RELATION_AXES and relation_key in duplicate_relation_keys:
            reason = "Hay varias propuestas para el mismo eje de relación en un turno; todas quedan pendientes para evitar aplicar un cambio duplicado o contradictorio."
        elif source is None:
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
        r"\b(m[aá]gic\w*|legendari\w*|artefact\w*|reliqui\w*|maldit\w*|"
        r"[uú]nic\w*|ancestral\w*|relic|unique|cursed|legendary)\b",
        re.IGNORECASE
    )
    inventory_signature_counts: dict[tuple[str, str, str], int] = {}
    for operation in result.inventory_ops:
        signature = (operation.event_ref, operation.operation, operation.item_name.strip().casefold())
        inventory_signature_counts[signature] = inventory_signature_counts.get(signature, 0) + 1

    for op_index, operation in enumerate(result.inventory_ops):
        source = event_map.get(operation.event_ref)
        status = "pending"
        old_value = None
        accepted_value = None
        reason = "La operación de inventario no superó la validación de bajo riesgo."
        item_name = operation.item_name.strip()
        item_key = item_name.casefold()
        item = None
        signature = (operation.event_ref, operation.operation, item_key)

        if inventory_signature_counts.get(signature, 0) > 1:
            reason = "La misma operación sobre este objeto aparece varias veces para el mismo evento; se dejan todas las copias pendientes para evitar duplicar cantidades."
        elif not source:
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
                paid = has_positive_user_action_for_label(
                    user_text, PURCHASE_ACTION_PATTERN, item_name
                )
                free_pickup = has_positive_user_action_for_label(
                    user_text, FREE_ACQUISITION_ACTION_PATTERN, item_name
                )
                currency_key = (operation.currency_key or "monedas").strip().casefold()
                payment_row = None
                if paid:
                    purchase_event_refs.add(operation.event_ref)
                    if operation.cost <= 0:
                        reason = "La compra no especifica un coste total positivo."
                    else:
                        payment_row = conn.execute(
                            "SELECT * FROM resources WHERE session_id=? AND resource_key=?",
                            (session["id"], currency_key)
                        ).fetchone()
                        if not payment_row:
                            reason = f"No existe un saldo registrado para '{currency_key}'; la compra queda pendiente."
                        elif int(payment_row["quantity"]) < operation.cost:
                            reason = (
                                f"Saldo insuficiente de {payment_row['display_name']}: "
                                f"{payment_row['quantity']} disponible, {operation.cost} requerido."
                            )
                        else:
                            reason = ""
                elif operation.cost > 0:
                    reason = "El mensaje del usuario no contiene una acción afirmativa de compra/pago para este objeto; el texto del narrador no puede autorizarla."
                elif not free_pickup:
                    reason = "El mensaje del usuario no confirma afirmativamente la recogida o aceptación de este objeto; queda pendiente."
                else:
                    reason = ""

                if not reason:
                    carrier = operation.carrier_entity_id or session["protagonist_entity_id"]
                    location = operation.location.strip() or session["current_location"]
                    old_value = (
                        {"quantity": int(item["quantity"]), "condition": item["condition"],
                         "carrier_entity_id": item["carrier_entity_id"], "location": item["location"]}
                        if item else None
                    )
                    if item and not item["carrier_entity_id"]:
                        if paid:
                            reason = "Una compra no puede reutilizarse como recogida de un objeto ya registrado en el suelo."
                        elif int(item["quantity"]) != operation.quantity:
                            reason = "El objeto está en el suelo; esta versión exige recoger la pila completa."
                        else:
                            conn.execute(
                                "UPDATE inventory_items SET carrier_entity_id=?,location=?,last_event_id=? WHERE id=?",
                                (carrier, location, source["id"], item["id"])
                            )
                            status = "accepted"
                            accepted_value = {
                                "operation": "pick_up", "item_name": item_name,
                                "quantity": operation.quantity, "carrier_entity_id": carrier, "location": location
                            }
                            applied.append(f"Recogido: {item_name} ×{operation.quantity}.")
                    elif item and item["carrier_entity_id"] != carrier and int(item["quantity"]) > 0:
                        reason = "Ya existe una pila de este objeto que lleva otra entidad; requiere una transferencia explícita."
                    else:
                        if paid and payment_row:
                            old_balance = int(payment_row["quantity"])
                            new_balance = old_balance - operation.cost
                            conn.execute(
                                "UPDATE resources SET quantity=?,last_event_id=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                                (new_balance, source["id"], payment_row["id"])
                            )
                            save_change(
                                conn, session["id"], turn_id, f"purchase-debit-{op_index}-{new_id()[:8]}",
                                session["protagonist_entity_id"], "resource", "spend",
                                {"resource_key": currency_key, "quantity": old_balance},
                                {"resource_key": currency_key, "display_name": payment_row["display_name"],
                                 "quantity": operation.cost, "event_ref": operation.event_ref},
                                {"resource_key": currency_key, "quantity": new_balance},
                                "accepted", f"Pago validado por el evento: {source['description']}", source["id"]
                            )
                            applied.append(f"Pagado: {operation.cost} {payment_row['display_name']}; quedan {new_balance}.")
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
                            "quantity": operation.quantity, "carrier_entity_id": carrier, "location": location,
                            "cost": operation.cost if paid else 0,
                            "currency_key": currency_key if paid else ""
                        }
                        applied.append(
                            f"Compra confirmada: {item_name} ×{operation.quantity}."
                            if paid else f"Hallazgo/regalo confirmado: {item_name} ×{operation.quantity} añadido al estado."
                        )
            elif operation.operation == "consume":
                expected_carrier = operation.carrier_entity_id or session["protagonist_entity_id"]
                if not item or int(item["quantity"]) < operation.quantity:
                    reason = "No existe cantidad suficiente del objeto en el inventario."
                elif item["carrier_entity_id"] != expected_carrier:
                    reason = "El objeto no está en posesión del portador indicado."
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
                expected_carrier = operation.carrier_entity_id or session["protagonist_entity_id"]
                if not item:
                    reason = "El objeto no existe en el inventario."
                elif item["carrier_entity_id"] != expected_carrier:
                    reason = "El objeto no está en posesión del portador indicado."
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
                expected_source = (
                    operation.carrier_entity_id or session["protagonist_entity_id"]
                    if operation.operation == "drop" else session["protagonist_entity_id"]
                )
                if not item:
                    reason = "El objeto no existe en el inventario."
                elif item["carrier_entity_id"] != expected_source:
                    reason = "El objeto no está en posesión del portador de origen indicado."
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

    # Economic evidence must come from an affirmative user action, not a
    # narrator-generated description or operation.reason.
    explicit_gain = RESOURCE_GAIN_ACTION_PATTERN
    explicit_spend = RESOURCE_SPEND_ACTION_PATTERN
    resource_signature_counts: dict[tuple[str, str, str], int] = {}
    for operation in result.resource_ops:
        signature = (operation.event_ref, operation.operation, operation.resource_key.strip().casefold())
        resource_signature_counts[signature] = resource_signature_counts.get(signature, 0) + 1

    for resource_index, operation in enumerate(result.resource_ops):
        source = event_map.get(operation.event_ref)
        status = "pending"
        old_value = None
        accepted_value = None
        reason = "El cambio de recurso no superó la validación de bajo riesgo."
        resource_key = operation.resource_key.strip().casefold()
        signature = (operation.event_ref, operation.operation, resource_key)
        if resource_signature_counts.get(signature, 0) > 1:
            reason = "El mismo cambio de recurso aparece varias veces para el mismo evento; se dejan las copias pendientes para no duplicar ingresos o gastos."
        elif operation.event_ref in purchase_event_refs and operation.operation == "spend":
            reason = "El cargo de compra se valida dentro de la operación de inventario; se evita duplicarlo."
        elif not source:
            reason = "No existe un evento fuente que justifique el cambio de recurso."
        elif source["status"] != "recorded":
            reason = "El evento fuente está pendiente."
        elif source["kind"] != "resource":
            reason = "El cambio requiere un evento fuente de tipo resource."
        elif not resource_key or not operation.display_name.strip():
            reason = "Falta una clave o nombre de recurso."
        elif not operation.reason.strip():
            reason = "Falta el motivo del cambio."
        elif source["entity_id"] not in {"", session["protagonist_entity_id"]}:
            reason = "El recurso personal del protagonista no puede cambiar mediante un evento atribuido a otra entidad."
        else:
            action_pattern = explicit_gain if operation.operation == "gain" else explicit_spend
            user_authorized_resource = (
                has_positive_user_action_for_label(user_text, action_pattern, resource_key)
                or has_positive_user_action_for_label(user_text, action_pattern, operation.display_name)
            )
            if not user_authorized_resource:
                reason = "No hay una acción afirmativa del usuario que nombre este recurso y autorice el ingreso o gasto."
            else:
                balance = conn.execute(
                    "SELECT * FROM resources WHERE session_id=? AND resource_key=?",
                    (session["id"], resource_key)
                ).fetchone()
                if operation.operation == "gain":
                    old_qty = int(balance["quantity"]) if balance else 0
                    new_qty = old_qty + operation.quantity
                    if balance:
                        conn.execute(
                            "UPDATE resources SET quantity=?,display_name=?,unit=?,last_event_id=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                            (new_qty, operation.display_name.strip(),
                             operation.unit.strip() or balance["unit"], source["id"], balance["id"])
                        )
                    else:
                        conn.execute(
                            "INSERT INTO resources(id,session_id,resource_key,display_name,quantity,unit,last_event_id) "
                            "VALUES(?,?,?,?,?,?,?)",
                            (new_id(), session["id"], resource_key, operation.display_name.strip(), new_qty,
                             operation.unit.strip(), source["id"])
                        )
                    old_value = {"resource_key": resource_key, "quantity": old_qty}
                    accepted_value = {"resource_key": resource_key, "display_name": operation.display_name.strip(), "quantity": new_qty}
                    status = "accepted"
                    applied.append(f"Recurso ganado: +{operation.quantity} {operation.display_name.strip()} (total {new_qty}).")
                else:
                    if not balance:
                        reason = f"No hay saldo registrado para '{resource_key}'."
                    elif int(balance["quantity"]) < operation.quantity:
                        reason = f"Saldo insuficiente: {balance['quantity']} disponible, {operation.quantity} requerido."
                    else:
                        old_qty = int(balance["quantity"])
                        new_qty = old_qty - operation.quantity
                        conn.execute(
                            "UPDATE resources SET quantity=?,last_event_id=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                            (new_qty, source["id"], balance["id"])
                        )
                        old_value = {"resource_key": resource_key, "quantity": old_qty}
                        accepted_value = {"resource_key": resource_key, "display_name": balance["display_name"], "quantity": new_qty}
                        status = "accepted"
                        applied.append(f"Recurso gastado: -{operation.quantity} {balance['display_name']} (quedan {new_qty}).")
        if status == "pending":
            pending_notes.append(f"Recurso: {operation.operation} {operation.display_name} — {reason}")
        save_change(
            conn, session["id"], turn_id, f"resource-{resource_index}-{new_id()[:8]}",
            session["protagonist_entity_id"], "resource", operation.operation, old_value,
            operation.model_dump(), accepted_value, status, reason,
            source["id"] if source else None
        )

    # A single turn cannot safely commit multiple destinations for the same
    # entity, even when the model assigns a different event_ref to each move.
    # Otherwise the result depends on proposal order and the last destination wins.
    movement_signature_counts: dict[str, int] = {}
    for movement in result.movements:
        entity_key = movement.entity_id
        movement_signature_counts[entity_key] = movement_signature_counts.get(entity_key, 0) + 1

    for move_index, movement in enumerate(result.movements):
        source = event_map.get(movement.event_ref)
        status = "pending"
        old_value = None
        accepted_value = None
        reason = "El movimiento requiere revisión."
        destination = movement.destination.strip()
        if movement_signature_counts.get(movement.entity_id, 0) > 1:
            reason = "Hay varios movimientos propuestos para la misma entidad en un turno; todos quedan pendientes para evitar que el destino final dependa del orden de la respuesta."
        elif not source:
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
            elif (
                presence["presence_status"] != "present"
                or str(presence["location"]).casefold() != str(session["current_location"]).casefold()
            ):
                reason = "El PNJ no está presente en la escena actual; no se aplica un movimiento desde fuera de escena."
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

    eco_aliases = {"eco", "eco_humano", "hipnosis"}
    power_signature_counts: dict[tuple[str, str], int] = {}
    for power in result.power_uses:
        raw_ability = power.ability_key.strip().lower()
        canonical_ability = "eco_humano" if raw_ability in eco_aliases else raw_ability
        signature = (canonical_ability, power.target_entity_id)
        power_signature_counts[signature] = power_signature_counts.get(signature, 0) + 1

    for use_index, power in enumerate(result.power_uses):
        source = event_map.get(power.event_ref)
        ability = power.ability_key.strip().lower()
        canonical_ability = "eco_humano" if ability in eco_aliases else ability
        signature = (canonical_ability, power.target_entity_id)
        duplicated_power = power_signature_counts.get(signature, 0) > 1
        source_is_power_for_target = bool(
            source and source["kind"] == "power"
            and source["entity_id"] == power.target_entity_id
        )
        power_action_authorized = explicitly_used_power_for_target(power)
        can_apply = bool(
            not duplicated_power and power_action_authorized and source
            and source["status"] == "recorded" and source_is_power_for_target
            and power.target_entity_id in valid_ids
        )
        reason = ""
        if duplicated_power:
            reason = "El mismo poder contra el mismo objetivo aparece varias veces en un turno; se requiere revisión para no duplicar usos."
        elif not source:
            reason = "No existe el evento que justifica el uso del poder."
        elif source["kind"] != "power":
            reason = "El uso debe referenciar un evento de tipo power."
        elif source["entity_id"] != power.target_entity_id:
            reason = "El objetivo del evento de poder no coincide con el objetivo de la operación."
        elif source["status"] != "recorded":
            reason = "El evento que justifica el poder está pendiente de revisión."
        elif power.target_entity_id not in valid_ids:
            reason = "El objetivo del poder no pertenece a este mundo."
        elif not power_action_authorized:
            reason = "El uso no coincide con una orden afirmativa del usuario dirigida a este objetivo."
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
        destination = (authorized_skip.get("destination") or "").strip() if authorized_skip else ""
        if destination:
            conn.execute(
                "UPDATE sessions SET day=?,minute_of_day=?,current_location=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (new_day, new_minute, destination, session["id"])
            )
            # Keep the protagonist's presence record aligned with the authoritative session location.
            conn.execute(
                "INSERT INTO session_presence(session_id,entity_id,location,presence_status) VALUES(?,?,?,'present') "
                "ON CONFLICT(session_id,entity_id) DO UPDATE SET location=excluded.location,"
                "presence_status='present',updated_at=CURRENT_TIMESTAMP",
                (session["id"], session["protagonist_entity_id"], destination)
            )
        else:
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
        "SELECT e.id,e.name,e.kind,p.location,"
        "CASE WHEN LOWER(p.location)=LOWER(s.current_location) THEN 'present' ELSE 'away' END AS presence_status "
        "FROM session_presence p JOIN entities e ON e.id=p.entity_id "
        "JOIN sessions s ON s.id=p.session_id WHERE p.session_id=? ORDER BY e.name", (session_id,)
    ).fetchall()]
    inventory = [dict(row) for row in conn.execute(
        "SELECT display_name,quantity,condition,carrier_entity_id,location FROM inventory_items "
        "WHERE session_id=? AND quantity>0 ORDER BY display_name", (session_id,)
    ).fetchall()]
    relationships = [dict(row) for row in conn.execute(
        "SELECT from_entity_id,to_entity_id,axis,value,reason FROM relationships WHERE session_id=?",
        (session_id,)
    ).fetchall()]
    resources = [dict(row) for row in conn.execute(
        "SELECT resource_key,display_name,quantity,unit FROM resources WHERE session_id=? ORDER BY display_name",
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
        "participants": participants, "inventory": inventory, "resources": resources,
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


@app.get("/api/settings")
def get_local_settings():
    with database.connection() as conn:
        return {
            "lore_budget_chars": get_lore_budget_chars(conn),
            "min_lore_budget_chars": MIN_LORE_CHARS,
            "max_lore_budget_chars": MAX_CONFIGURABLE_LORE_CHARS,
            "lore_max_entries": MAX_LORE_ENTRIES
        }


@app.post("/api/settings")
def update_local_settings(payload: LocalSettingsUpdate):
    with database.transaction() as conn:
        save_lore_budget_chars(conn, payload.lore_budget_chars)
        return {
            "lore_budget_chars": get_lore_budget_chars(conn),
            "min_lore_budget_chars": MIN_LORE_CHARS,
            "max_lore_budget_chars": MAX_CONFIGURABLE_LORE_CHARS,
            "lore_max_entries": MAX_LORE_ENTRIES
        }


@app.get("/api/worlds")
def list_worlds():
    with database.connection() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT id,name,created_at FROM worlds ORDER BY created_at DESC"
        ).fetchall()]


def seed_resource(conn, session_id: str, resource) -> None:
    resource_name = resource.name.strip()
    resource_key = (resource.key.strip() or resource_name).casefold()
    if not resource_key or not resource_name:
        raise HTTPException(status_code=422, detail="Cada recurso necesita nombre y clave válidos.")
    conn.execute(
        "INSERT INTO resources(id,session_id,resource_key,display_name,quantity,unit) "
        "VALUES(?,?,?,?,?,?) ON CONFLICT(session_id,resource_key) DO UPDATE SET "
        "display_name=excluded.display_name, quantity=excluded.quantity, unit=excluded.unit, "
        "updated_at=CURRENT_TIMESTAMP",
        (new_id(), session_id, resource_key, resource_name, resource.quantity, resource.unit.strip())
    )

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
            for resource in payload.initial_resources:
                seed_resource(conn, session_id, resource)
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
        for resource in payload.initial_resources:
            seed_resource(conn, session_id, resource)
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
        conn.execute(
            "INSERT INTO resources(id,session_id,resource_key,display_name,quantity,unit) "
            "VALUES(?,?,?,?,?,?) ON CONFLICT(session_id,resource_key) DO NOTHING",
            (new_id(), session_id, "monedas", "Monedas", 0, "monedas")
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


@app.post("/api/sessions/{session_id}/commands")
def execute_local_command(session_id: str, payload: LocalCommandRequest):
    command = parse_local_command(payload.text)
    if command is None:
        raise HTTPException(status_code=422, detail="Escribe un comando local, por ejemplo /estado o /ayuda.")
    if command == "salto":
        raise HTTPException(status_code=422, detail="/salto es una acción de la partida; envíala con el botón de turno narrativo.")
    if command == "ayuda":
        with database.connection() as conn:
            if conn.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone() is None:
                raise HTTPException(status_code=404, detail="Partida no encontrada.")
        return {
            "command": command,
            "help": [
                "/estado — muestra reloj, ubicación, personajes presentes, recursos y propuestas pendientes.",
                "/inventario — muestra objetos registrados y sus portadores.",
                "/guardar — crea una copia de seguridad de la base local.",
                "/salto 30 minutos | /salto 2 horas | /salto 1 día -> destino — avanza el reloj mediante una acción explícita.",
                "/ayuda — muestra esta lista. Los comandos locales no consumen turnos narrativos."
            ]
        }
    if command == "guardar":
        result = backup_session_database(session_id)
        return {"command": command, **result}
    with database.connection() as conn:
        state = load_state(conn, session_id)
    if command == "inventario":
        return {"command": command, "inventory": state["inventory"], "resources": state["resources"]}
    return {"command": command, "state": state}


@app.get("/api/sessions/{session_id}/messages")
def get_messages(session_id: str):
    with database.connection() as conn:
        if conn.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Partida no encontrada.")
        return [dict(row) for row in conn.execute(
            "SELECT id,turn_id,client_request_id,turn_index,role,recipient_entity_id,content,provider,generation_status,metadata_json,created_at "
            "FROM messages WHERE session_id=? ORDER BY turn_index ASC, CASE role WHEN 'user' THEN 0 ELSE 1 END ASC, created_at ASC", (session_id,)
        ).fetchall()]


@app.post("/api/sessions/{session_id}/context-preview")
def preview_context(session_id: str, payload: ContextPreviewRequest):
    """Return the exact compact context builder output plus local selection diagnostics; no AI call."""
    with database.connection() as conn:
        session = session_row(conn, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Partida no encontrada.")
        if payload.visibility == "private" and not payload.recipient_id:
            raise HTTPException(status_code=422, detail="Un contexto privado requiere destinatario.")
        if payload.recipient_id:
            target = conn.execute(
                "SELECT 1 FROM entities WHERE id=? AND world_id=?",
                (payload.recipient_id, session["world_id"])
            ).fetchone()
            if target is None:
                raise HTTPException(status_code=422, detail="El destinatario no pertenece a este mundo.")
            present_here = conn.execute(
                "SELECT 1 FROM session_presence WHERE session_id=? AND entity_id=? AND LOWER(location)=LOWER(?)",
                (session_id, payload.recipient_id, session["current_location"])
            ).fetchone()
            if present_here is None:
                raise HTTPException(status_code=422, detail="El destinatario no está en la ubicación actual.")
        audience_ids = (
            sorted({session["protagonist_entity_id"], payload.recipient_id})
            if payload.visibility == "private"
            else [
                row["entity_id"] for row in conn.execute(
                    "SELECT entity_id FROM session_presence WHERE session_id=? AND LOWER(location)=LOWER(?)",
                    (session_id, session["current_location"])
                ).fetchall()
            ]
        )
        context = build_context(
            conn, session, payload.text, payload.recipient_id, new_id(),
            visibility=payload.visibility, audience_ids=audience_ids,
            include_diagnostics=True
        )
    diagnostics = context.pop("_diagnostics", {})
    return {"context": context, "diagnostics": diagnostics}


@app.post("/api/sessions/{session_id}/manual-prompt")
def create_manual_prompt(session_id: str, payload: ManualPromptRequest):
    """Create a prompt the user can paste into their own ChatGPT/Gemini web conversation."""
    authorized_skip = parse_skip(payload.text)
    with database.connection() as conn:
        session = session_row(conn, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Partida no encontrada.")
        if payload.visibility == "private" and not payload.recipient_id:
            raise HTTPException(status_code=422, detail="Un contexto privado requiere destinatario.")
        if payload.recipient_id:
            target = conn.execute(
                "SELECT 1 FROM entities WHERE id=? AND world_id=?",
                (payload.recipient_id, session["world_id"])
            ).fetchone()
            if target is None:
                raise HTTPException(status_code=422, detail="El destinatario no pertenece a este mundo.")
            present_here = conn.execute(
                "SELECT 1 FROM session_presence WHERE session_id=? AND entity_id=? AND LOWER(location)=LOWER(?)",
                (session_id, payload.recipient_id, session["current_location"])
            ).fetchone()
            if present_here is None:
                raise HTTPException(status_code=422, detail="El destinatario no está en la ubicación actual.")
        audience_ids = (
            sorted({session["protagonist_entity_id"], payload.recipient_id})
            if payload.visibility == "private"
            else [
                row["entity_id"] for row in conn.execute(
                    "SELECT entity_id FROM session_presence WHERE session_id=? AND LOWER(location)=LOWER(?)",
                    (session_id, session["current_location"])
                ).fetchall()
            ]
        )
        context = build_context(
            conn, session, payload.text, payload.recipient_id, new_id(),
            visibility=payload.visibility, audience_ids=audience_ids
        )
    input_payload = {
        "user_message": payload.text,
        "recipient_id": payload.recipient_id,
        "context": context,
        "authorized_skip": authorized_skip or {}
    }
    return {
        "provider": payload.provider,
        "prompt": build_manual_prompt(input_payload),
        "context_characters": len(json.dumps(input_payload, ensure_ascii=False)),
        "context_hash": manual_context_hash(input_payload)
    }


@app.post("/api/sessions/{session_id}/turns")
async def submit_turn(session_id: str, payload: TurnRequest):
    local_command = parse_local_command(payload.text)
    if local_command and local_command != "salto":
        raise HTTPException(status_code=422, detail=f"/{local_command} es un comando local; ejecútalo desde el panel de comandos.")
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
        if payload.recipient_id:
            if conn.execute(
                "SELECT 1 FROM entities WHERE id=? AND world_id=?",
                (payload.recipient_id, session["world_id"])
            ).fetchone() is None:
                raise HTTPException(status_code=422, detail="El destinatario no pertenece a este mundo.")
            present_here = conn.execute(
                "SELECT 1 FROM session_presence WHERE session_id=? AND entity_id=? AND LOWER(location)=LOWER(?)",
                (session_id, payload.recipient_id, session["current_location"])
            ).fetchone()
            if present_here is None:
                raise HTTPException(status_code=422, detail="El destinatario no está en la ubicación actual; no se puede iniciar un diálogo directo con él.")

        current_scene_ids = {
            row["entity_id"] for row in conn.execute(
                "SELECT entity_id FROM session_presence WHERE session_id=? AND LOWER(location)=LOWER(?)",
                (session_id, session["current_location"])
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
        active_turn = conn.execute(
            "SELECT turn_id,client_request_id FROM messages "
            "WHERE session_id=? AND role='user' AND generation_status='processing' LIMIT 1",
            (session_id,)
        ).fetchone()
        if active_turn and (not existing_user or existing_user["turn_id"] != active_turn["turn_id"]):
            raise HTTPException(
                status_code=409,
                detail="Hay otro turno en curso en esta partida. Espera a que se complete o falle antes de enviar otra acción."
            )
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
        create_turn_snapshot(conn, session_id, turn_id, turn_index)
        session = session_row(conn, session_id)
        context = build_context(
            conn, session, payload.text, payload.recipient_id, turn_id,
            visibility=payload.visibility, audience_ids=audience_ids
        )
        provider_name = payload.provider or settings.default_provider
        if provider_name in {"chatgpt_web", "gemini_web"}:
            if not payload.manual_context_hash or len(payload.manual_context_hash) != 64:
                raise HTTPException(
                    status_code=422,
                    detail="Falta la huella del prompt preparado. Vuelve a preparar el prompt desde la interfaz."
                )
            current_input_payload = {
                "user_message": payload.text,
                "recipient_id": payload.recipient_id,
                "context": context,
                "authorized_skip": authorized_skip or {}
            }
            if not hmac.compare_digest(
                manual_context_hash(current_input_payload), payload.manual_context_hash
            ):
                raise HTTPException(
                    status_code=409,
                    detail="La partida cambió desde que se preparó el prompt. Vuelve a prepararlo y pide una nueva respuesta al chat web."
                )

    provider_name = payload.provider or settings.default_provider
    try:
        provider = make_provider(provider_name, settings)
        result = await provider.generate({
            "user_message": payload.text,
            "recipient_id": payload.recipient_id,
            "context": context,
            "authorized_skip": authorized_skip or {},
            "external_response": payload.external_response
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
    try:
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
    except Exception as exc:
        # The transaction above rolls back both narration and state. Mark the
        # request failed in a separate transaction so one malformed proposal
        # cannot leave a permanent "processing" turn that blocks the session.
        logger.exception(
            "No se pudo aplicar la respuesta del narrador de forma atómica",
            extra={"session_id": session_id, "turn_id": turn_id, "provider": provider_name}
        )
        with database.transaction() as conn:
            conn.execute(
                "UPDATE messages SET generation_status='failed' WHERE id=? AND generation_status='processing'",
                (user_message_id,)
            )
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(
            status_code=502,
            detail="La respuesta se generó, pero no pudo guardarse de forma segura. No se aplicaron cambios; corrige la respuesta o vuelve a intentarlo."
        ) from exc
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

@app.post("/api/sessions/{session_id}/turns/{turn_id}/undo")
def undo_latest_turn(session_id: str, turn_id: str):
    """Undo only the latest completed turn; keep an audit trail and restore the prior game state."""
    with database.transaction() as conn:
        session = session_row(conn, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Partida no encontrada.")

        assistant = conn.execute(
            "SELECT id,turn_index,content,recipient_entity_id,metadata_json FROM messages "
            "WHERE session_id=? AND turn_id=? AND role='assistant' AND generation_status='complete'",
            (session_id, turn_id)
        ).fetchone()
        if assistant is None:
            raise HTTPException(status_code=409, detail="El turno no existe o ya fue anulado; no hay una respuesta completada que deshacer.")
        in_progress = conn.execute(
            "SELECT 1 FROM messages WHERE session_id=? AND role='user' AND generation_status='processing' LIMIT 1",
            (session_id,)
        ).fetchone()
        if in_progress:
            raise HTTPException(status_code=409, detail="Hay un turno en curso; espera a que termine antes de deshacer el último turno.")

        latest = conn.execute(
            "SELECT MAX(turn_index) AS n FROM messages "
            "WHERE session_id=? AND role='assistant' AND generation_status='complete'",
            (session_id,)
        ).fetchone()["n"]
        if latest is None or int(latest) != int(assistant["turn_index"]):
            raise HTTPException(status_code=409, detail="Solo se puede deshacer el turno completado más reciente.")
        snapshot = conn.execute(
            "SELECT state_json FROM snapshots WHERE session_id=? AND turn_id=?",
            (session_id, turn_id)
        ).fetchone()
        if snapshot is None:
            raise HTTPException(status_code=409, detail="No hay snapshot anterior a este turno; el estado no se modificó.")

        user_message = conn.execute(
            "SELECT id,content,recipient_entity_id,metadata_json FROM messages "
            "WHERE session_id=? AND turn_id=? AND role='user'",
            (session_id, turn_id)
        ).fetchone()
        if user_message is None:
            raise HTTPException(status_code=409, detail="No se encontró el mensaje de usuario asociado al turno.")

        try:
            prior_state = json.loads(snapshot["state_json"])
        except Exception as exc:
            raise HTTPException(status_code=500, detail="El snapshot del turno no se puede leer; no se cambió el estado.") from exc

        audit_turn_id = f"{turn_id}:undone:{new_id()[:10]}"
        restore_turn_state(conn, session_id, prior_state)

        # Move generated audit records to a separate audit turn id so the original request
        # can be safely retried/regenerated with the same request_id if desired.
        conn.execute(
            "UPDATE events SET turn_id=?,status='rejected',"
            "description=description || ' [Turno anulado por el usuario.]' "
            "WHERE session_id=? AND turn_id=?",
            (audit_turn_id, session_id, turn_id)
        )
        conn.execute(
            "UPDATE state_changes SET turn_id=?,status='rejected',"
            "reason=CASE WHEN reason='' THEN 'Turno anulado por el usuario.' "
            "ELSE reason || ' [Turno anulado por el usuario.]' END,applied_at=NULL "
            "WHERE session_id=? AND turn_id=?",
            (audit_turn_id, session_id, turn_id)
        )
        conn.execute(
            "UPDATE messages SET turn_id=?,client_request_id=NULL,generation_status='undone' "
            "WHERE session_id=? AND turn_id=? AND role='assistant'",
            (audit_turn_id, session_id, turn_id)
        )
        conn.execute(
            "UPDATE messages SET generation_status='undone' WHERE session_id=? AND turn_id=? AND role='user'",
            (session_id, turn_id)
        )

        user_metadata = json.loads(user_message["metadata_json"] or "{}")
        restored_state = load_state(conn, session_id)
        return {
            "undone": True,
            "turn_id": turn_id,
            "audit_turn_id": audit_turn_id,
            "user_text": user_message["content"],
            "recipient_id": user_message["recipient_entity_id"],
            "visibility": user_metadata.get("visibility", "scene"),
            "state": restored_state,
            "message": "Turno anulado. El estado anterior fue restaurado; el texto puede editarse y enviarse otra vez."
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
                conn.execute(
                    "INSERT INTO session_presence(session_id,entity_id,location,presence_status) VALUES(?,?,?,'present') "
                    "ON CONFLICT(session_id,entity_id) DO UPDATE SET location=excluded.location,"
                    "presence_status='present',updated_at=CURRENT_TIMESTAMP",
                    (session_id, entity_id, destination)
                )
            else:
                presence = conn.execute(
                    "SELECT 1 FROM session_presence WHERE session_id=? AND entity_id=?",
                    (session_id, entity_id)
                ).fetchone()
                if not presence:
                    raise HTTPException(status_code=422, detail="La entidad no forma parte del reparto de esta partida.")
                presence_status = "present" if destination.casefold() == session["current_location"].casefold() else "away"
                conn.execute(
                    "UPDATE session_presence SET location=?,presence_status=?,updated_at=CURRENT_TIMESTAMP "
                    "WHERE session_id=? AND entity_id=?",
                    (destination, presence_status, session_id, entity_id)
                )
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
    backup_path = database.path.parent / "backups" / f"backup-{session_id}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}.sqlite3"
    # Hold the writer lock between checking for in-flight turns and taking the
    # database snapshot, so a new turn cannot start halfway through the backup.
    with database.transaction() as conn:
        if conn.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Partida no encontrada.")
        in_progress = conn.execute(
            "SELECT 1 FROM messages WHERE session_id=? AND role='user' "
            "AND generation_status='processing' LIMIT 1",
            (session_id,)
        ).fetchone()
        if in_progress:
            raise HTTPException(
                status_code=409,
                detail="No se puede crear una copia coherente mientras hay un turno en curso. Espera a que termine y vuelve a guardar."
            )
        database.backup_to(str(backup_path))
    return {"backup_created": True, "backup_name": backup_path.name, "path": str(backup_path)}


RESTORE_SESSION_TABLES = (
    "session_presence",
    "inventory_items",
    "resources",
    "relationships",
    "ability_uses",
    "messages",
    "events",
    "state_changes",
    "snapshots",
)
RESTORE_REQUIRED_COLUMNS = {
    "session_presence": {"session_id", "entity_id", "location", "presence_status"},
    "inventory_items": {"id", "session_id", "item_key", "display_name", "quantity", "condition", "carrier_entity_id", "location"},
    "resources": {"id", "session_id", "resource_key", "display_name", "quantity", "unit"},
    "relationships": {"id", "session_id", "from_entity_id", "to_entity_id", "axis", "value"},
    "ability_uses": {"id", "session_id", "turn_id", "ability_key", "target_entity_id", "result"},
    "messages": {"id", "session_id", "turn_id", "turn_index", "role", "recipient_entity_id", "content", "provider", "generation_status"},
    "events": {"id", "session_id", "turn_id", "external_ref", "kind", "entity_id", "description", "witnesses_json", "status"},
    "state_changes": {"id", "session_id", "turn_id", "external_ref", "entity_id", "field", "operation", "proposed_value_json", "status", "reason"},
    "snapshots": {"id", "session_id", "event_sequence", "state_json"},
}


def _restore_world_signature(conn, world_id: str):
    """Fingerprint the world's authored content before restoring a session snapshot."""
    world = conn.execute(
        "SELECT id,name,canon_text FROM worlds WHERE id=?", (world_id,)
    ).fetchone()
    if world is None:
        return None
    entities = [
        tuple(row) for row in conn.execute(
            "SELECT id,name,kind,profile,canonical_status FROM entities WHERE world_id=? ORDER BY id",
            (world_id,)
        ).fetchall()
    ]
    lore = [
        tuple(row) for row in conn.execute(
            "SELECT id,external_uid,title,keywords_json,content,priority,canon_status "
            "FROM lore_entries WHERE world_id=? ORDER BY id",
            (world_id,)
        ).fetchall()
    ]
    return (tuple(world), tuple(entities), tuple(lore))


def _table_columns(conn, table: str) -> set[str]:
    return {
        row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }


def _read_session_backup(backup_path: Path, session_id: str):
    """Read and validate a session snapshot without modifying the active database."""
    source = None
    try:
        source_uri = backup_path.resolve().as_uri() + "?mode=ro"
        source = sqlite3.connect(source_uri, uri=True, timeout=10)
        source.row_factory = sqlite3.Row
        integrity = source.execute("PRAGMA integrity_check").fetchone()
        if not integrity or integrity[0] != "ok":
            raise HTTPException(status_code=422, detail="La copia de seguridad no supera la comprobación de integridad.")
        if source.execute("PRAGMA foreign_key_check").fetchone():
            raise HTTPException(status_code=422, detail="La copia contiene referencias internas incoherentes.")
        source_session_row = source.execute(
            "SELECT id,world_id,protagonist_entity_id,day,minute_of_day,current_location,updated_at "
            "FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
        if source_session_row is None:
            raise HTTPException(status_code=422, detail="La copia no contiene esta partida; el archivo no corresponde al identificador seleccionado.")

        source_tables = {
            row["name"] for row in source.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        missing_tables = [table for table in RESTORE_SESSION_TABLES if table not in source_tables]
        if missing_tables:
            raise HTTPException(
                status_code=422,
                detail="La copia usa un esquema antiguo o incompleto; no se modificó la partida."
            )

        table_rows = {}
        for table in RESTORE_SESSION_TABLES:
            columns = _table_columns(source, table)
            required_columns = RESTORE_REQUIRED_COLUMNS[table]
            # Older backups stored location but not the derived presence_status.
            # Accept that legacy shape and reconstruct the status below.
            if table == "session_presence" and "presence_status" not in columns:
                required_columns = required_columns - {"presence_status"}
            if not required_columns.issubset(columns):
                raise HTTPException(
                    status_code=422,
                    detail=f"La copia no contiene los campos esenciales de {table}; no se modificó la partida."
                )
            rows = [
                dict(row) for row in source.execute(
                    f"SELECT * FROM {table} WHERE session_id=? ORDER BY rowid",
                    (session_id,)
                ).fetchall()
            ]
            if table == "session_presence":
                # Location relative to the restored session is authoritative,
                # even when an older row has a missing or stale status column.
                current_location = str(source_session_row["current_location"] or "")
                for presence in rows:
                    location = str(presence.get("location") or "")
                    presence["presence_status"] = (
                        "present" if location.casefold() == current_location.casefold() else "away"
                    )
            table_rows[table] = rows
        signature = _restore_world_signature(source, source_session_row["world_id"])
        if signature is None:
            raise HTTPException(status_code=422, detail="La copia no contiene el mundo de esta partida.")
        return dict(source_session_row), signature, table_rows
    except HTTPException:
        raise
    except (sqlite3.Error, OSError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail="No se pudo leer la copia como una base de datos válida; la partida activa no se modificó."
        ) from exc
    finally:
        if source is not None:
            source.close()


def restore_session_from_backup(session_id: str, backup_path: Path) -> dict[str, Any]:
    backup_session, backup_world_signature, table_rows = _read_session_backup(backup_path, session_id)
    restored_counts = {table: len(rows) for table, rows in table_rows.items()}

    # A single immediate transaction serializes restoration against turn creation.
    # If a turn has already started, its persistent "processing" marker blocks restore.
    with database.transaction() as conn:
        active_session = session_row(conn, session_id)
        if active_session is None:
            raise HTTPException(status_code=404, detail="Partida no encontrada.")
        if (
            active_session["world_id"] != backup_session["world_id"]
            or active_session["protagonist_entity_id"] != backup_session["protagonist_entity_id"]
        ):
            raise HTTPException(
                status_code=409,
                detail="La copia pertenece a otra versión de la partida o a otro protagonista; no se restauró."
            )
        in_progress = conn.execute(
            "SELECT 1 FROM messages WHERE session_id=? AND role='user' "
            "AND generation_status='processing' LIMIT 1",
            (session_id,)
        ).fetchone()
        if in_progress:
            raise HTTPException(
                status_code=409,
                detail="No se puede restaurar mientras la partida tiene un turno en curso. No se modificó ningún dato."
            )
        current_world_signature = _restore_world_signature(conn, active_session["world_id"])
        if current_world_signature != backup_world_signature:
            raise HTTPException(
                status_code=409,
                detail="El canon, los personajes o el Lorebook del mundo cambiaron desde la copia. Para evitar mezclar versiones, restaura solo después de volver al mismo mundo."
            )

        conn.execute(
            "UPDATE sessions SET day=?,minute_of_day=?,current_location=?,updated_at=? WHERE id=?",
            (
                int(backup_session["day"]),
                int(backup_session["minute_of_day"]),
                backup_session["current_location"],
                backup_session["updated_at"],
                session_id,
            )
        )
        for table in RESTORE_SESSION_TABLES:
            conn.execute(f"DELETE FROM {table} WHERE session_id=?", (session_id,))

        for table in RESTORE_SESSION_TABLES:
            rows = table_rows[table]
            if not rows:
                continue
            destination_columns = _table_columns(conn, table)
            for row in rows:
                columns = [column for column in row if column in destination_columns]
                if not RESTORE_REQUIRED_COLUMNS[table].issubset(columns):
                    raise HTTPException(
                        status_code=422,
                        detail=f"No se puede restaurar la estructura de {table}; la transacción fue cancelada."
                    )
                placeholders = ",".join("?" for _ in columns)
                column_sql = ",".join(columns)
                conn.execute(
                    f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})",
                    tuple(row[column] for column in columns)
                )

    with database.connection() as conn:
        state = load_state(conn, session_id)
    return {"restored_tables": restored_counts, "state": state}


@app.get("/api/sessions/{session_id}/backups")
def list_session_backups(session_id: str):
    with database.connection() as conn:
        if conn.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Partida no encontrada.")
    backups_dir = (database.path.parent / "backups").resolve()
    if not backups_dir.exists():
        return {"backups": []}
    prefix = f"backup-{session_id}-"
    backups = []
    for candidate in backups_dir.glob(f"{prefix}*.sqlite3"):
        if not candidate.is_file() or candidate.name != candidate.name.strip():
            continue
        try:
            resolved = candidate.resolve()
            if resolved.parent != backups_dir or not candidate.name.startswith(prefix):
                continue
            stat = candidate.stat()
            backups.append({
                "name": candidate.name,
                "created_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds"),
                "size_bytes": stat.st_size,
            })
        except OSError:
            continue
    backups.sort(key=lambda item: item["created_at"], reverse=True)
    return {"backups": backups[:50]}


@app.post("/api/sessions/{session_id}/restore")
def restore_session_backup(session_id: str, payload: SessionRestoreRequest):
    if payload.confirmation != "RESTAURAR":
        raise HTTPException(status_code=422, detail="Para restaurar debes confirmar escribiendo RESTAURAR.")
    if Path(payload.backup_name).name != payload.backup_name:
        raise HTTPException(status_code=422, detail="Selecciona una copia de la lista; no se aceptan rutas externas.")
    backups_dir = (database.path.parent / "backups").resolve()
    expected_prefix = f"backup-{session_id}-"
    if not payload.backup_name.startswith(expected_prefix) or not payload.backup_name.endswith(".sqlite3"):
        raise HTTPException(status_code=422, detail="La copia seleccionada no pertenece a esta partida.")
    backup_path = (backups_dir / payload.backup_name).resolve()
    if backup_path.parent != backups_dir or not backup_path.is_file():
        raise HTTPException(status_code=404, detail="No se encontró la copia seleccionada.")
    try:
        result = restore_session_from_backup(session_id, backup_path)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=422,
            detail="La copia contiene datos que no cumplen el esquema actual; la restauración se canceló sin modificar la partida."
        ) from exc
    return {
        "restored": True,
        "backup_name": payload.backup_name,
        "restored_tables": result["restored_tables"],
        "state": result["state"],
        "message": "Partida restaurada desde la copia seleccionada. La narración y el estado vuelven a ese punto; los otros mundos y partidas no se modificaron."
    }

