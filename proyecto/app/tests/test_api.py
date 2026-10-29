import os
import tempfile
import asyncio
import threading
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import uuid
import json
import re

import pytest

_TEST_DB_DIR = tempfile.TemporaryDirectory(prefix="canon-test-")
os.environ["APP_PROVIDER"] = "mock"
os.environ["APP_DB_PATH"] = str(Path(_TEST_DB_DIR.name) / "initial.sqlite3")

from fastapi.testclient import TestClient

import canon_manager.main as main_module
from canon_manager.main import app, database, build_context, session_row, apply_narrator_result, relevance_terms
from canon_manager.models import NarratorResponse, EventProposal, StateChangeProposal, InventoryOperation, MovementProposal, PowerUseProposal, ResourceOperation


@pytest.fixture(autouse=True)
def isolate_test_database():
    """Each API test gets a clean SQLite file; TemporaryDirectory removes all of them at exit."""
    database.path = Path(_TEST_DB_DIR.name) / f"test-{uuid.uuid4().hex}.sqlite3"
    database.initialize()
    yield


def test_seeded_chat_turn_is_saved_and_changes_are_validated():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={})
        assert seed.status_code == 200
        world_id = seed.json()["world_id"]
        session_id = seed.json()["session_id"]

        entities = client.get(f"/api/worlds/{world_id}/entities").json()
        maelis = next(entity for entity in entities if entity["name"] == "Maelis Orven")

        response = client.post(
            f"/api/sessions/{session_id}/turns",
            json={"request_id": "request-test-maelis-001", "text": "Hola, linda", "recipient_id": maelis["id"], "provider": "mock"}
        )
        assert response.status_code == 200, response.text
        data = response.json()

        assert "Apenas te conozco" in data["narration"]
        assert len(data["events"]) >= 1
        assert any(change["field"] == "confidence" for change in data["state"]["pending_changes"])
        assert any(item["display_name"] == "pañuelo gastado" for item in data["state"]["inventory"])

        messages = client.get(f"/api/sessions/{session_id}/messages").json()
        assert len(messages) == 2
        assert [message["role"] for message in messages] == ["user", "assistant"]

        retry = client.post(
            f"/api/sessions/{session_id}/turns",
            json={"request_id": "request-test-maelis-001", "text": "Hola, linda", "recipient_id": maelis["id"], "provider": "mock"}
        )
        assert retry.status_code == 200
        assert retry.json()["replayed"] is True
        assert retry.json()["turn_id"] == data["turn_id"]

        messages_after_retry = client.get(f"/api/sessions/{session_id}/messages").json()
        assert len(messages_after_retry) == 2
        state = client.get(f"/api/sessions/{session_id}/state").json()
        assert state["state"]["time_label"].endswith("08:01")
        assert state["state"]["location"] == "Claro en el Bosque de las Bestias"


def test_backup_endpoint_creates_a_copy():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        response = client.post(f"/api/sessions/{seed['session_id']}/backup", json={})
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["backup_created"] is True
        assert Path(data["path"]).exists()


def test_interrupted_turn_is_recovered_without_losing_user_message():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        turn_id = "interrupted-" + uuid.uuid4().hex
        request_id = "interrupted-request-" + uuid.uuid4().hex[:16]
        with database.transaction() as conn:
            turn_index = conn.execute(
                "SELECT COALESCE(MAX(turn_index),0)+1 AS n FROM messages WHERE session_id=?",
                (session_id,)
            ).fetchone()["n"]
            conn.execute(
                "INSERT INTO messages(id,session_id,turn_id,client_request_id,turn_index,role,"
                "recipient_entity_id,content,provider,generation_status,metadata_json) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    uuid.uuid4().hex, session_id, turn_id, request_id, turn_index, "user", "",
                    "Sí, sigo por el sendero.", "mock", "processing",
                    json.dumps({"visibility": "scene", "audience_ids": []})
                )
            )

        assert main_module.recover_interrupted_turns() == 1
        messages = client.get(f"/api/sessions/{session_id}/messages").json()
        recovered = next(message for message in messages if message["turn_id"] == turn_id)
        assert recovered["generation_status"] == "failed"
        assert recovered["content"] == "Sí, sigo por el sendero."
        assert recovered["client_request_id"] == request_id
        metadata = json.loads(recovered["metadata_json"])
        assert metadata["recovered_after_restart"] is True
        assert "No se aplicaron cambios" in metadata["recovery_note"]
        assert main_module.recover_interrupted_turns() == 0



def test_startup_recovery_preserves_turn_owned_by_live_process(monkeypatch):
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        live_turn_id = "live-owner-" + uuid.uuid4().hex
        dead_turn_id = "dead-owner-" + uuid.uuid4().hex
        with database.transaction() as conn:
            next_index = int(conn.execute(
                "SELECT COALESCE(MAX(turn_index),0)+1 AS n FROM messages WHERE session_id=?",
                (session_id,)
            ).fetchone()["n"])
            for offset, (turn_id, owner_pid) in enumerate([
                (live_turn_id, 10101),
                (dead_turn_id, 20202),
            ]):
                conn.execute(
                    "INSERT INTO messages(id,session_id,turn_id,client_request_id,turn_index,role,"
                    "recipient_entity_id,content,provider,generation_status,metadata_json) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        uuid.uuid4().hex, session_id, turn_id,
                        "owner-recovery-" + uuid.uuid4().hex, next_index + offset, "user", "",
                        "Acción en curso", "mock", "processing",
                        json.dumps({
                            "visibility": "scene",
                            "audience_ids": [],
                            "processing_owner_pid": owner_pid,
                        })
                    )
                )

        # Also exercise the real liveness probe for the current OS before
        # replacing it with deterministic owners for the recovery regression.
        assert main_module._process_is_alive(os.getpid()) is True
        assert main_module._process_is_alive(2**31 - 1) is False

        # Model the OS process check deterministically: 10101 is alive, 20202 is gone.
        monkeypatch.setattr(
            main_module, "_process_is_alive", lambda pid: pid == 10101
        )
        recovered = main_module.recover_interrupted_turns()
        assert recovered == 1

        with database.connection() as conn:
            live = conn.execute(
                "SELECT generation_status FROM messages WHERE session_id=? AND turn_id=?",
                (session_id, live_turn_id)
            ).fetchone()
            dead = conn.execute(
                "SELECT generation_status,metadata_json FROM messages WHERE session_id=? AND turn_id=?",
                (session_id, dead_turn_id)
            ).fetchone()
        assert live["generation_status"] == "processing"
        assert dead["generation_status"] == "failed"
        assert json.loads(dead["metadata_json"])["recovered_after_restart"] is True

def test_backup_for_one_session_is_not_blocked_by_another_session_turn():
    with TestClient(app) as client:
        first = client.post("/api/demo/seed", json={}).json()
        second_response = client.post(
            "/api/worlds/start",
            json={
                "name": "Otra partida para respaldo " + uuid.uuid4().hex,
                "protagonist_name": "Protagonista",
                "session_name": "Partida independiente",
                "location": "Otra ubicación",
                "cast": [],
                "initial_inventory": []
            }
        )
        assert second_response.status_code == 200, second_response.text
        second = second_response.json()
        assert first["session_id"] != second["session_id"]

        with database.transaction() as conn:
            conn.execute(
                "INSERT INTO messages(id,session_id,turn_id,client_request_id,turn_index,role,"
                "recipient_entity_id,content,provider,generation_status,metadata_json) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    uuid.uuid4().hex, second["session_id"], "other-session-processing",
                    "processing-request-" + uuid.uuid4().hex[:12], 999, "user", "",
                    "Un turno de otra partida sigue en curso.", "mock", "processing",
                    json.dumps({"visibility": "scene", "audience_ids": []})
                )
            )

        response = client.post(f"/api/sessions/{first['session_id']}/backup", json={})
        assert response.status_code == 200, response.text
        assert response.json()["backup_created"] is True


def test_pending_major_event_can_be_approved_or_rejected():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        world_id = seed["world_id"]
        entities = client.get(f"/api/worlds/{world_id}/entities").json()
        maelis = next(entity for entity in entities if entity["name"] == "Maelis Orven")
        approved_id = uuid.uuid4().hex
        rejected_id = uuid.uuid4().hex
        change_id = uuid.uuid4().hex
        with database.transaction() as conn:
            conn.execute(
                "INSERT INTO events(id,session_id,turn_id,external_ref,kind,entity_id,description,witnesses_json,status) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                (approved_id, session_id, "test-turn-a", "e-a", "major_change", maelis["id"],
                 "Evento de alto impacto de prueba", "[]", "pending")
            )
            conn.execute(
                "INSERT INTO events(id,session_id,turn_id,external_ref,kind,entity_id,description,witnesses_json,status) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                (rejected_id, session_id, "test-turn-b", "e-b", "major_change", maelis["id"],
                 "Evento de prueba que se rechaza", "[]", "pending")
            )
            conn.execute(
                "INSERT INTO state_changes(id,session_id,turn_id,external_ref,entity_id,field,operation,"
                "proposed_value_json,status,reason,source_event_id) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (change_id, session_id, "test-turn-b", "c-b", maelis["id"], "confidence", "delta",
                 '{"numeric_value":-1}', "pending", "Cambio ligado al evento rechazable", rejected_id)
            )

        state = client.get(f"/api/sessions/{session_id}/state").json()
        assert any(event["id"] == approved_id for event in state["pending_events"])
        approve = client.post(f"/api/sessions/{session_id}/events/{approved_id}/approve", json={})
        assert approve.status_code == 200, approve.text
        reject = client.post(f"/api/sessions/{session_id}/events/{rejected_id}/reject", json={})
        assert reject.status_code == 200, reject.text

        with database.connection() as conn:
            approved = conn.execute("SELECT status FROM events WHERE id=?", (approved_id,)).fetchone()
            rejected = conn.execute("SELECT status FROM events WHERE id=?", (rejected_id,)).fetchone()
            linked_change = conn.execute("SELECT status FROM state_changes WHERE id=?", (change_id,)).fetchone()
        assert approved["status"] == "recorded"
        assert rejected["status"] == "rejected"
        assert linked_change["status"] == "rejected"



def test_create_world_and_start_with_cast_and_inventory():
    with TestClient(app) as client:
        response = client.post(
            "/api/worlds/start",
            json={
                "name": "Prueba mundo personalizado",
                "canon_text": "El canon breve se conserva localmente.",
                "protagonist_name": "Ari",
                "protagonist_profile": "El usuario controla al protagonista.",
                "session_name": "Primera partida",
                "location": "Puerto de prueba",
                "day": 1,
                "minute_of_day": 480,
                "cast": [
                    {"name": "Maelis Test", "kind": "character", "profile": "Maga curiosa."},
                    {"name": "Guardia Test", "kind": "npc", "profile": "Guarda la puerta."}
                ],
                "initial_inventory": [
                    {"name": "Pañuelo", "quantity": 1, "condition": "gastado"},
                    {"name": "Moneda", "quantity": 3, "condition": "normal"}
                ]
            }
        )
        assert response.status_code == 200, response.text
        data = response.json()
        world_id, session_id = data["world_id"], data["session_id"]

        entities = client.get(f"/api/worlds/{world_id}/entities").json()
        names = {entity["name"] for entity in entities}
        assert {"Ari", "Maelis Test", "Guardia Test"} <= names

        state = client.get(f"/api/sessions/{session_id}/state").json()
        assert state["state"]["location"] == "Puerto de prueba"
        assert state["state"]["time_label"].endswith("08:00")
        assert {person["name"] for person in state["participants"]} >= {"Ari", "Maelis Test", "Guardia Test"}
        items = {item["display_name"]: item for item in state["inventory"]}
        assert items["Pañuelo"]["quantity"] == 1
        assert items["Pañuelo"]["condition"] == "gastado"
        assert items["Moneda"]["quantity"] == 3


def test_world_creation_rolls_back_when_cast_has_duplicate_names():
    with TestClient(app) as client:
        before = {world["name"] for world in client.get("/api/worlds").json()}
        response = client.post(
            "/api/worlds/start",
            json={
                "name": "Prueba mundo con error",
                "canon_text": "",
                "protagonist_name": "Ari",
                "session_name": "Partida inválida",
                "location": "Bosque",
                "cast": [
                    {"name": "Mismo PNJ", "kind": "npc", "profile": ""},
                    {"name": "Mismo PNJ", "kind": "npc", "profile": ""}
                ],
                "initial_inventory": []
            }
        )
        assert response.status_code == 409
        after = {world["name"] for world in client.get("/api/worlds").json()}
        assert after == before


def test_load_actual_isekai_preset_imports_lorebook_and_starts_fresh_session():
    with TestClient(app) as client:
        first = client.post("/api/presets/isekai-sin-destino", json={})
        assert first.status_code == 200, first.text
        first_data = first.json()
        assert first_data["lore_entries"] == 77
        assert first_data["participants"] == 6
        assert first_data["inventory_items"] == 5

        state = client.get(f"/api/sessions/{first_data['session_id']}/state").json()
        assert state["state"]["location"] == "Claro del Bosque de las Bestias"
        assert state["state"]["time_label"].endswith("08:00")
        assert {person["name"] for person in state["participants"]} >= {
            "Protagonista", "Brina Solcor", "Ivar Dalen", "Maelis Orven", "Sera Linde", "Timo Venn"
        }
        item_names = {item["display_name"] for item in state["inventory"]}
        assert {"Camisa corriente", "Pantalones largos", "Pañuelo gastado", "Bolsita de tela vacía", "Cordel de cáñamo corto"} <= item_names
        assert any(resource["resource_key"] == "monedas" and resource["quantity"] == 0
                   for resource in state["resources"])

        second = client.post("/api/presets/isekai-sin-destino", json={})
        assert second.status_code == 200, second.text
        second_data = second.json()
        assert second_data["world_id"] == first_data["world_id"]
        assert second_data["session_id"] != first_data["session_id"]



def test_isekai_lorebook_import_quality_is_conservative_and_has_unique_keywords():
    lore_path = Path(__file__).resolve().parents[3] / "proyectos" / "isekai-sin-destino" / "LOREBOOK_IMPORT.json"
    payload = json.loads(lore_path.read_text(encoding="utf-8"))
    entries = list(payload["entries"].values())
    version_match = re.search(r"\bv(\d+\.\d+)\b", str(payload.get("description", "")))
    assert version_match, "La descripción del Lorebook debe declarar una versión."
    html_path = Path(__file__).resolve().parents[1] / "src" / "canon_manager" / "static" / "index.html"
    html = html_path.read_text(encoding="utf-8")
    button_match = re.search(
        r'<button id="isekaiPreset">Cargar Isekai sin Destino v(\d+\.\d+)</button>',
        html
    )
    assert button_match, "El botón del preset debe mostrar su versión."
    assert button_match.group(1) == version_match.group(1), (
        "La versión visible del preset debe coincidir con la del JSON: "
        f"interfaz={button_match.group(1)}, JSON={version_match.group(1)}"
    )

    assert len(entries) == 77
    seen_keywords = {}
    for entry in entries:
        content = str(entry.get("content", "")).strip()
        assert content, f"Entrada vacía: {entry.get('uid')}"
        assert len(content) < 1000, f"Content demasiado largo: uid={entry.get('uid')} length={len(content)}"
        for keyword in entry.get("key", []):
            normalized = str(keyword).strip().casefold()
            assert normalized, f"Palabra clave vacía: uid={entry.get('uid')}"
            assert normalized not in seen_keywords, (
                f"Palabra clave duplicada {normalized!r}: UID {seen_keywords.get(normalized)} y {entry.get('uid')}"
            )
            seen_keywords[normalized] = entry.get("uid")


def test_private_turn_is_not_visible_to_other_npcs():
    with TestClient(app) as client:
        started = client.post(
            "/api/worlds/start",
            json={
                "name": "Prueba de privacidad " + uuid.uuid4().hex,
                "canon_text": "El contexto privado solo lo conocen el protagonista y su destinataria.",
                "protagonist_name": "Protagonista",
                "session_name": "Prueba privada",
                "location": "Claro del bosque",
                "cast": [
                    {"name": "Maelis Orven", "kind": "character", "profile": "Maga curiosa."},
                    {"name": "Ivar Dalen", "kind": "character", "profile": "Lancero sarcástico."},
                    {"name": "Brina Solcor", "kind": "character", "profile": "Guerrera prudente."}
                ],
                "initial_inventory": []
            }
        )
        assert started.status_code == 200, started.text
        world_id, session_id = started.json()["world_id"], started.json()["session_id"]
        entities = client.get(f"/api/worlds/{world_id}/entities").json()
        by_name = {entity["name"]: entity for entity in entities}
        maelis = by_name["Maelis Orven"]
        ivar = by_name["Ivar Dalen"]

        private_reply = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "private-maelis-0001",
                "text": "Hola, linda; esto es confidencial",
                "recipient_id": maelis["id"],
                "provider": "mock",
                "visibility": "private"
            }
        )
        assert private_reply.status_code == 200, private_reply.text
        narration = private_reply.json()["narration"]
        assert "Maelis" in narration
        assert "Ivar" not in narration
        assert "Brina" not in narration

        # The stored event must not list bystanders as witnesses.
        with database.connection() as conn:
            private_event = conn.execute(
                "SELECT witnesses_json,status FROM events WHERE session_id=? AND turn_id=?",
                (session_id, private_reply.json()["turn_id"])
            ).fetchone()
            assert private_event is not None
            assert ivar["id"] not in json.loads(private_event["witnesses_json"])
            assert private_event["status"] == "recorded"

            session = session_row(conn, session_id)
            context_for_ivar = build_context(
                conn, session, "¿Qué dijo Maelis?", ivar["id"],
                "future-turn-not-yet-created", visibility="scene"
            )
            private_context_for_ivar = build_context(
                conn, session, "Hola", ivar["id"],
                "future-private-turn", visibility="private",
                audience_ids=[session["protagonist_entity_id"], ivar["id"]]
            )

        # A private exchange and its events are omitted from Ivar's context,
        # even though Maelis remains physically present in the wider scene.
        assert not any("esto es confidencial" in msg["content"] for msg in context_for_ivar["recent_messages"])
        assert not any("incomodidad ante un saludo" in event["description"] for event in context_for_ivar["recent_events"])
        # Explicitly private scenes include only the protagonist and recipient.
        private_participant_ids = {person["id"] for person in private_context_for_ivar["participants"]}
        assert maelis["id"] not in private_participant_ids
        assert ivar["id"] in private_participant_ids


def test_private_turn_requires_recipient():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        response = client.post(
            f"/api/sessions/{seed['session_id']}/turns",
            json={
                "request_id": "private-no-recipient",
                "text": "Hola",
                "provider": "mock",
                "visibility": "private"
            }
        )
        assert response.status_code == 422


def _create_state_ops_world(client):
    started = client.post(
        "/api/worlds/start",
        json={
            "name": "Prueba operaciones " + uuid.uuid4().hex,
            "canon_text": "Los cambios locales solo se aplican si tienen evento fuente válido.",
            "protagonist_name": "Protagonista",
            "session_name": "Prueba de operaciones",
            "location": "Claro del bosque",
            "cast": [
                {"name": "Maelis Orven", "kind": "character", "profile": "Maga curiosa."},
                {"name": "Ivar Dalen", "kind": "character", "profile": "Lancero sarcástico."},
                {"name": "Brina Solcor", "kind": "character", "profile": "Guerrera prudente."}
            ],
            "initial_inventory": [
                {"name": "Manzana", "quantity": 2, "condition": "normal"},
                {"name": "Cuerda", "quantity": 1, "condition": "normal"},
                {"name": "Cantimplora", "quantity": 1, "condition": "normal"},
                {"name": "Camisa", "quantity": 1, "condition": "normal"}
            ],
            "initial_resources": [
                {"key": "monedas", "name": "Monedas", "quantity": 5, "unit": "monedas"}
            ]
        }
    )
    assert started.status_code == 200, started.text
    data = started.json()
    entities = client.get(f"/api/worlds/{data['world_id']}/entities").json()
    return data, {entity["name"]: entity for entity in entities}


def _apply_synthetic_result(session_id, user_text, result):
    turn_id = uuid.uuid4().hex
    with database.transaction() as conn:
        session = session_row(conn, session_id)
        audience_ids = [
            row["entity_id"] for row in conn.execute(
                "SELECT entity_id FROM session_presence WHERE session_id=? AND presence_status='present'",
                (session_id,)
            ).fetchall()
        ]
        applied, pending = apply_narrator_result(
            conn, session, turn_id, "test-source-message", user_text, result, None,
            visibility="scene", audience_ids=audience_ids
        )
    return turn_id, applied, pending


def test_low_risk_inventory_consumption_is_applied_automatically():
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        protagonist_id = entities["Protagonista"]["id"]
        witnesses = list(entities[name]["id"] for name in ("Protagonista", "Maelis Orven", "Ivar Dalen", "Brina Solcor"))
        result = NarratorResponse(
            narration="El protagonista come una manzana de sus provisiones.",
            events=[
                EventProposal(
                    ref="event-consume-apple",
                    kind="object",
                    entity_id=protagonist_id,
                    description="El protagonista consume una manzana de sus provisiones.",
                    witness_ids=witnesses
                )
            ],
            inventory_ops=[
                InventoryOperation(
                    operation="consume",
                    item_name="Manzana",
                    quantity=1,
                    carrier_entity_id=protagonist_id,
                    location="Claro del bosque",
                    reason="La manzana se consume en la escena.",
                    event_ref="event-consume-apple"
                )
            ]
        )
        turn_id, applied, pending = _apply_synthetic_result(started["session_id"], "Como una manzana", result)
        with database.connection() as conn:
            item = conn.execute(
                "SELECT quantity FROM inventory_items WHERE session_id=? AND item_key='manzana'",
                (started["session_id"],)
            ).fetchone()
            change = conn.execute(
                "SELECT status,old_value_json,accepted_value_json FROM state_changes WHERE session_id=? AND turn_id=? AND field='inventory'",
                (started["session_id"], turn_id)
            ).fetchone()
        assert item["quantity"] == 1
        assert change["status"] == "accepted"
        assert json.loads(change["accepted_value_json"])["quantity_after"] == 1
        assert any("Consumido: Manzana" in note for note in applied)
        assert not any("Inventario:" in note for note in pending)


def test_free_found_object_is_added_but_purchase_without_cost_stays_pending():
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        protagonist_id = entities["Protagonista"]["id"]
        witnesses = list(entities[name]["id"] for name in ("Protagonista", "Maelis Orven", "Ivar Dalen", "Brina Solcor"))

        free_result = NarratorResponse(
            narration="Encuentras una manzana caída junto al sendero y la recoges.",
            events=[
                EventProposal(
                    ref="event-find-apple",
                    kind="object",
                    entity_id=protagonist_id,
                    description="El protagonista encuentra una manzana caída y la recoge del suelo.",
                    witness_ids=witnesses
                )
            ],
            inventory_ops=[
                InventoryOperation(
                    operation="acquire",
                    item_name="Manzana",
                    quantity=1,
                    carrier_entity_id=protagonist_id,
                    location="Claro del bosque",
                    reason="Hallazgo gratuito confirmado.",
                    event_ref="event-find-apple"
                )
            ]
        )
        free_turn, applied, pending = _apply_synthetic_result(
            started["session_id"], "Recojo la manzana que encontré", free_result
        )
        with database.connection() as conn:
            item = conn.execute(
                "SELECT quantity FROM inventory_items WHERE session_id=? AND item_key='manzana'",
                (started["session_id"],)
            ).fetchone()
        assert item["quantity"] == 3
        assert any("Hallazgo/regalo confirmado" in note for note in applied)
        assert not any("Inventario:" in note for note in pending)

        paid_result = NarratorResponse(
            narration="Pagas dos monedas y recibes otra manzana.",
            events=[
                EventProposal(
                    ref="event-buy-apple",
                    kind="object",
                    entity_id=protagonist_id,
                    description="El comerciante entrega una manzana tras el pago de dos monedas.",
                    witness_ids=witnesses
                )
            ],
            inventory_ops=[
                InventoryOperation(
                    operation="acquire",
                    item_name="Manzana",
                    quantity=1,
                    carrier_entity_id=protagonist_id,
                    location="Claro del bosque",
                    reason="Compra en el mercado.",
                    event_ref="event-buy-apple"
                )
            ]
        )
        paid_turn, paid_applied, paid_pending = _apply_synthetic_result(
            started["session_id"], "Compro una manzana por dos monedas", paid_result
        )
        with database.connection() as conn:
            item = conn.execute(
                "SELECT quantity FROM inventory_items WHERE session_id=? AND item_key='manzana'",
                (started["session_id"],)
            ).fetchone()
            change = conn.execute(
                "SELECT status,reason FROM state_changes WHERE session_id=? AND turn_id=? AND field='inventory'",
                (started["session_id"], paid_turn)
            ).fetchone()
        assert item["quantity"] == 3
        assert change["status"] == "pending"
        assert "coste total positivo" in change["reason"]
        assert any("Inventario:" in note for note in paid_pending)


def test_valid_npc_movement_is_applied_but_protagonist_movement_is_pending():
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        protagonist_id = entities["Protagonista"]["id"]
        ivar_id = entities["Ivar Dalen"]["id"]
        witnesses = [protagonist_id, ivar_id]
        result = NarratorResponse(
            narration="Ivar deja el claro y se marcha hacia Brumaclara.",
            events=[
                EventProposal(
                    ref="event-ivar-leaves",
                    kind="location",
                    entity_id=ivar_id,
                    description="Ivar deja el claro y se marcha hacia Brumaclara.",
                    witness_ids=witnesses
                ),
                EventProposal(
                    ref="event-protagonist-move",
                    kind="location",
                    entity_id=protagonist_id,
                    description="El protagonista aparece en Valdoria sin una acción que lo justifique.",
                    witness_ids=witnesses
                )
            ],
            movements=[
                MovementProposal(
                    entity_id=ivar_id,
                    destination="Brumaclara",
                    reason="Ivar decide regresar a la aldea por el sendero.",
                    event_ref="event-ivar-leaves"
                ),
                MovementProposal(
                    entity_id=protagonist_id,
                    destination="Valdoria",
                    reason="Movimiento propuesto sin orden del usuario.",
                    event_ref="event-protagonist-move"
                )
            ]
        )
        turn_id, applied, pending = _apply_synthetic_result(
            started["session_id"], "Pregunto a Ivar qué hará", result
        )
        with database.connection() as conn:
            ivar_presence = conn.execute(
                "SELECT location,presence_status FROM session_presence WHERE session_id=? AND entity_id=?",
                (started["session_id"], ivar_id)
            ).fetchone()
            session = session_row(conn, started["session_id"])
            protagonist_change = conn.execute(
                "SELECT status,reason FROM state_changes WHERE session_id=? AND turn_id=? AND entity_id=? AND field='movement'",
                (started["session_id"], turn_id, protagonist_id)
            ).fetchone()
        assert ivar_presence["location"] == "Brumaclara"
        assert ivar_presence["presence_status"] == "away"
        assert session["current_location"] == "Claro del bosque"
        assert protagonist_change["status"] == "pending"
        assert "nunca mueve al protagonista" in protagonist_change["reason"]
        assert any("Movimiento de PNJ guardado" in note for note in applied)
        assert any("Movimiento de" in note for note in pending)

        # A character who moved to another location cannot remain selectable
        # as a direct conversation partner in the old scene.
        response = client.post(
            f"/api/sessions/{started['session_id']}/turns",
            json={
                "request_id": "talk-to-away-npc-001",
                "text": "Le pregunto a Ivar qué piensa",
                "recipient_id": ivar_id,
                "provider": "mock"
            }
        )
        assert response.status_code == 422
        assert "no está en la ubicación actual" in response.json()["detail"]



def test_conflicting_npc_destinations_in_one_turn_are_all_pending():
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        protagonist_id = entities["Protagonista"]["id"]
        ivar_id = entities["Ivar Dalen"]["id"]
        witnesses = [protagonist_id, ivar_id]
        initial_state = client.get(f"/api/sessions/{session_id}/state").json()
        initial_ivar = next(
            participant for participant in initial_state["participants"]
            if participant["id"] == ivar_id
        )
        initial_location = initial_ivar["location"]

        result = NarratorResponse(
            narration=(
                "Ivar parece marcharse hacia Brumaclara, pero la misma respuesta "
                "también afirma que se dirige al Puerto Gris."
            ),
            events=[
                EventProposal(
                    ref="ivar-leaves-to-bruma",
                    kind="location",
                    entity_id=ivar_id,
                    description="Ivar deja el claro y se marcha hacia Brumaclara.",
                    witness_ids=witnesses
                ),
                EventProposal(
                    ref="ivar-leaves-to-port",
                    kind="location",
                    entity_id=ivar_id,
                    description="Ivar deja el claro y se marcha hacia el Puerto Gris.",
                    witness_ids=witnesses
                )
            ],
            movements=[
                MovementProposal(
                    entity_id=ivar_id,
                    destination="Brumaclara",
                    reason="Ivar sale del claro hacia Brumaclara.",
                    event_ref="ivar-leaves-to-bruma"
                ),
                MovementProposal(
                    entity_id=ivar_id,
                    destination="Puerto Gris",
                    reason="Ivar sale del claro hacia el Puerto Gris.",
                    event_ref="ivar-leaves-to-port"
                )
            ]
        )
        turn_id, applied, pending = _apply_synthetic_result(
            session_id,
            "Le pregunto a Ivar si se queda o se marcha",
            result
        )

        with database.connection() as conn:
            presence = conn.execute(
                "SELECT location,presence_status FROM session_presence "
                "WHERE session_id=? AND entity_id=?",
                (session_id, ivar_id)
            ).fetchone()
            movement_changes = conn.execute(
                "SELECT status,reason,proposed_value_json FROM state_changes "
                "WHERE session_id=? AND turn_id=? AND field='movement' ORDER BY created_at,id",
                (session_id, turn_id)
            ).fetchall()

        assert presence["location"] == initial_location
        assert presence["presence_status"] == "present"
        assert len(movement_changes) == 2
        assert all(change["status"] == "pending" for change in movement_changes)
        assert all("varios movimientos" in change["reason"] for change in movement_changes)
        assert not any("Movimiento de PNJ guardado" in note for note in applied)
        assert sum("varios movimientos" in note for note in pending) == 2


def test_offscreen_npc_cannot_be_teleported_by_narrator_proposal():
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        protagonist_id = entities["Protagonista"]["id"]
        ivar_id = entities["Ivar Dalen"]["id"]
        present_witnesses = [protagonist_id, ivar_id]

        leave_result = NarratorResponse(
            narration="Ivar se despide y se marcha hacia Brumaclara.",
            events=[
                EventProposal(
                    ref="ivar-leaves-scene",
                    kind="location",
                    entity_id=ivar_id,
                    description="Ivar deja el claro y se marcha hacia Brumaclara.",
                    witness_ids=present_witnesses
                )
            ],
            movements=[
                MovementProposal(
                    entity_id=ivar_id,
                    destination="Brumaclara",
                    reason="Ivar se marcha por el sendero.",
                    event_ref="ivar-leaves-scene"
                )
            ]
        )
        _, applied_leave, pending_leave = _apply_synthetic_result(
            session_id, "Ivar se marcha hacia Brumaclara", leave_result
        )
        assert any("Movimiento de PNJ guardado" in note for note in applied_leave)
        assert not any("Movimiento de Ivar" in note for note in pending_leave)

        return_result = NarratorResponse(
            narration="La respuesta afirma que Ivar, aunque sigue fuera de escena, regresa instantáneamente al claro.",
            events=[
                EventProposal(
                    ref="ivar-teleport-back",
                    kind="location",
                    entity_id=ivar_id,
                    description="Ivar vuelve al claro sin que se describa su regreso.",
                    witness_ids=[protagonist_id]
                )
            ],
            movements=[
                MovementProposal(
                    entity_id=ivar_id,
                    destination="Claro del bosque",
                    reason="El narrador propone devolver a Ivar al lugar del protagonista sin una escena de regreso.",
                    event_ref="ivar-teleport-back"
                )
            ]
        )
        turn_id, applied_return, pending_return = _apply_synthetic_result(
            session_id, "Me quedo en el claro y espero", return_result
        )

        with database.connection() as conn:
            presence = conn.execute(
                "SELECT location,presence_status FROM session_presence "
                "WHERE session_id=? AND entity_id=?",
                (session_id, ivar_id)
            ).fetchone()
            movement = conn.execute(
                "SELECT status,reason FROM state_changes "
                "WHERE session_id=? AND turn_id=? AND field='movement' AND entity_id=?",
                (session_id, turn_id, ivar_id)
            ).fetchone()

        assert presence["location"] == "Brumaclara"
        assert presence["presence_status"] == "away"
        assert movement["status"] == "pending"
        assert "fuera de escena" in movement["reason"]
        assert not any("Movimiento de PNJ guardado" in note for note in applied_return)
        assert any("fuera de escena" in note for note in pending_return)


def test_routine_drop_transfer_and_condition_are_applied_with_source_events():
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        protagonist_id = entities["Protagonista"]["id"]
        ivar_id = entities["Ivar Dalen"]["id"]
        witnesses = [protagonist_id, ivar_id]
        event_defs = [
            EventProposal(
                ref="event-drop-rope",
                kind="object",
                entity_id=protagonist_id,
                description="El protagonista deja la cuerda completa en el suelo del claro.",
                witness_ids=witnesses
            ),
            EventProposal(
                ref="event-transfer-flask",
                kind="object",
                entity_id=protagonist_id,
                description="El protagonista entrega la cantimplora a Ivar.",
                witness_ids=witnesses
            ),
            EventProposal(
                ref="event-wet-shirt",
                kind="object",
                entity_id=protagonist_id,
                description="La camisa del protagonista queda mojada al cruzar el arroyo.",
                witness_ids=witnesses
            )
        ]
        operations = [
            InventoryOperation(
                operation="drop",
                item_name="Cuerda",
                quantity=1,
                carrier_entity_id=protagonist_id,
                location="Claro del bosque",
                reason="Deja la cuerda junto al árbol.",
                event_ref="event-drop-rope"
            ),
            InventoryOperation(
                operation="transfer",
                item_name="Cantimplora",
                quantity=1,
                carrier_entity_id=ivar_id,
                location="Claro del bosque",
                reason="Entrega la cantimplora a Ivar.",
                event_ref="event-transfer-flask"
            ),
            InventoryOperation(
                operation="condition",
                item_name="Camisa",
                quantity=1,
                carrier_entity_id=protagonist_id,
                condition="mojada",
                location="Claro del bosque",
                reason="La camisa se moja al cruzar el arroyo.",
                event_ref="event-wet-shirt"
            )
        ]
        turn_id, applied, pending = _apply_synthetic_result(
            started["session_id"],
            "Dejo la cuerda, entrego la cantimplora a Ivar y cruzo el arroyo",
            NarratorResponse(
                narration="La cuerda queda junto al árbol; Ivar recibe la cantimplora y la camisa termina mojada.",
                events=event_defs,
                inventory_ops=operations
            )
        )
        with database.connection() as conn:
            items = {
                row["item_key"]: dict(row) for row in conn.execute(
                    "SELECT item_key,quantity,condition,carrier_entity_id,location,last_event_id "
                    "FROM inventory_items WHERE session_id=?",
                    (started["session_id"],)
                ).fetchall()
            }
            changes = conn.execute(
                "SELECT status,operation FROM state_changes WHERE session_id=? AND turn_id=? AND field='inventory'",
                (started["session_id"], turn_id)
            ).fetchall()
        assert items["cuerda"]["carrier_entity_id"] == ""
        assert items["cuerda"]["location"] == "Claro del bosque"
        assert items["cantimplora"]["carrier_entity_id"] == ivar_id
        assert items["camisa"]["condition"] == "mojada"
        assert len(changes) == 3
        assert all(row["status"] == "accepted" for row in changes)
        assert len([note for note in applied if "Objeto actualizado" in note or "Estado del objeto actualizado" in note]) == 3
        assert not any("Inventario:" in note for note in pending)



def test_context_preview_reports_lore_triggers_and_budget_without_calling_provider():
    with TestClient(app) as client:
        started = client.post("/api/presets/isekai-sin-destino", json={})
        assert started.status_code == 200, started.text
        session_id = started.json()["session_id"]

        specific = client.post(
            f"/api/sessions/{session_id}/context-preview",
            json={
                "text": "Quiero aprender sobre la corriente Brasa.",
                "visibility": "scene"
            }
        )
        assert specific.status_code == 200, specific.text
        preview = specific.json()
        diagnostics = preview["diagnostics"]
        lore_titles = {entry["title"] for entry in preview["context"]["relevant_lore"]}
        assert "Seis corrientes mágicas" in lore_titles
        matching = next(item for item in diagnostics["selected_lore"] if item["title"] == "Seis corrientes mágicas")
        assert any(hit["source"] == "mensaje actual" and hit["keyword"] == "corriente Brasa" for hit in matching["triggered_by"])
        assert diagnostics["lore_chars_used"] <= diagnostics["lore_chars_budget"]
        assert diagnostics["lore_entries_selected"] <= diagnostics["lore_entries_max"]
        assert len(preview["context"]["world"]["canon_core"]) <= 3050

        accidental = client.post(
            f"/api/sessions/{session_id}/context-preview",
            json={"text": "Entramos en una brasería cercana.", "visibility": "scene"}
        )
        assert accidental.status_code == 200, accidental.text
        accidental_titles = {entry["title"] for entry in accidental.json()["context"]["relevant_lore"]}
        assert "Seis corrientes mágicas" not in accidental_titles
        assert accidental.json()["diagnostics"]["context_characters"] > 0


def test_private_context_preview_requires_present_recipient():
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        preview = client.post(
            f"/api/sessions/{started['session_id']}/context-preview",
            json={
                "text": "Hola",
                "recipient_id": "",
                "visibility": "private"
            }
        )
        assert preview.status_code == 422
        assert "requiere destinatario" in preview.json()["detail"]



def test_paid_inventory_purchase_debits_local_currency_and_adds_item_atomically():
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        protagonist_id = entities["Protagonista"]["id"]
        witnesses = [entities[name]["id"] for name in ("Protagonista", "Maelis Orven", "Ivar Dalen", "Brina Solcor")]
        result = NarratorResponse(
            narration="Pagas dos monedas y recibes una manzana del comerciante.",
            events=[
                EventProposal(
                    ref="event-buy-apple-with-coins",
                    kind="object",
                    entity_id=protagonist_id,
                    description="El protagonista compra una manzana por dos monedas y la recibe.",
                    witness_ids=witnesses
                )
            ],
            inventory_ops=[
                InventoryOperation(
                    operation="acquire",
                    item_name="Manzana",
                    quantity=1,
                    carrier_entity_id=protagonist_id,
                    location="Claro del bosque",
                    reason="Compra explícita por dos monedas.",
                    event_ref="event-buy-apple-with-coins",
                    cost=2,
                    currency_key="monedas"
                )
            ]
        )
        turn_id, applied, pending = _apply_synthetic_result(
            session_id, "Compro una manzana por dos monedas", result
        )
        with database.connection() as conn:
            apple = conn.execute(
                "SELECT quantity FROM inventory_items WHERE session_id=? AND item_key='manzana'",
                (session_id,)
            ).fetchone()
            coins = conn.execute(
                "SELECT quantity FROM resources WHERE session_id=? AND resource_key='monedas'",
                (session_id,)
            ).fetchone()
            changes = conn.execute(
                "SELECT field,status,accepted_value_json FROM state_changes WHERE session_id=? AND turn_id=?",
                (session_id, turn_id)
            ).fetchall()
        assert apple["quantity"] == 3
        assert coins["quantity"] == 3
        assert len(changes) == 2
        assert all(change["status"] == "accepted" for change in changes)
        assert {change["field"] for change in changes} == {"inventory", "resource"}
        assert any("Pagado: 2 Monedas" in note for note in applied)
        assert any("Compra confirmada" in note for note in applied)
        assert not pending


def test_paid_inventory_purchase_with_insufficient_currency_remains_pending_without_mutation():
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        protagonist_id = entities["Protagonista"]["id"]
        witnesses = [entities[name]["id"] for name in ("Protagonista", "Maelis Orven", "Ivar Dalen", "Brina Solcor")]
        result = NarratorResponse(
            narration="El comerciante pide seis monedas por una manzana.",
            events=[
                EventProposal(
                    ref="event-buy-expensive-apple",
                    kind="object",
                    entity_id=protagonist_id,
                    description="El protagonista intenta comprar una manzana por seis monedas.",
                    witness_ids=witnesses
                )
            ],
            inventory_ops=[
                InventoryOperation(
                    operation="acquire",
                    item_name="Manzana",
                    quantity=1,
                    carrier_entity_id=protagonist_id,
                    location="Claro del bosque",
                    reason="Compra por seis monedas.",
                    event_ref="event-buy-expensive-apple",
                    cost=6,
                    currency_key="monedas"
                )
            ]
        )
        turn_id, applied, pending = _apply_synthetic_result(
            session_id, "Compro una manzana por seis monedas", result
        )
        with database.connection() as conn:
            apple = conn.execute(
                "SELECT quantity FROM inventory_items WHERE session_id=? AND item_key='manzana'",
                (session_id,)
            ).fetchone()
            coins = conn.execute(
                "SELECT quantity FROM resources WHERE session_id=? AND resource_key='monedas'",
                (session_id,)
            ).fetchone()
            change = conn.execute(
                "SELECT status,reason FROM state_changes WHERE session_id=? AND turn_id=? AND field='inventory'",
                (session_id, turn_id)
            ).fetchone()
        assert apple["quantity"] == 2
        assert coins["quantity"] == 5
        assert change["status"] == "pending"
        assert "Saldo insuficiente" in change["reason"]
        assert any("Inventario:" in note for note in pending)
        assert not any("Pagado:" in note for note in applied)


def test_explicit_work_reward_increases_local_currency_balance():
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        protagonist_id = entities["Protagonista"]["id"]
        witnesses = [entities[name]["id"] for name in ("Protagonista", "Maelis Orven", "Ivar Dalen", "Brina Solcor")]
        result = NarratorResponse(
            narration="La posadera te paga cinco monedas como recompensa por el trabajo.",
            events=[
                EventProposal(
                    ref="event-work-reward",
                    kind="resource",
                    entity_id=protagonist_id,
                    description="El protagonista recibe cinco monedas como recompensa por el trabajo.",
                    witness_ids=witnesses
                )
            ],
            resource_ops=[
                ResourceOperation(
                    operation="gain",
                    resource_key="monedas",
                    display_name="Monedas",
                    quantity=5,
                    unit="monedas",
                    reason="Recompensa de trabajo explícita.",
                    event_ref="event-work-reward"
                )
            ]
        )
        turn_id, applied, pending = _apply_synthetic_result(
            session_id, "Cobro cinco monedas como recompensa por el trabajo", result
        )
        with database.connection() as conn:
            coins = conn.execute(
                "SELECT quantity FROM resources WHERE session_id=? AND resource_key='monedas'",
                (session_id,)
            ).fetchone()
            change = conn.execute(
                "SELECT status,accepted_value_json FROM state_changes WHERE session_id=? AND turn_id=? AND field='resource'",
                (session_id, turn_id)
            ).fetchone()
        assert coins["quantity"] == 10
        assert change["status"] == "accepted"
        assert json.loads(change["accepted_value_json"])["quantity"] == 10
        assert any("Recurso ganado: +5 Monedas" in note for note in applied)
        assert not pending





def test_questions_and_denied_actions_cannot_change_economy_inventory_or_use_a_power():
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        protagonist_id = entities["Protagonista"]["id"]
        maelis_id = entities["Maelis Orven"]["id"]
        witnesses = [entities[name]["id"] for name in (
            "Protagonista", "Maelis Orven", "Ivar Dalen", "Brina Solcor"
        )]
        with database.transaction() as conn:
            conn.execute(
                "INSERT INTO relationships(id,session_id,from_entity_id,to_entity_id,axis,value,reason) "
                "VALUES(?,?,?,?,?,?,?)",
                (
                    uuid.uuid4().hex, session_id, protagonist_id, maelis_id,
                    "friendship", 50, "Valor inicial confirmado para prueba de negación."
                )
            )

        result = NarratorResponse(
            narration=(
                "El protagonista compra una manzana, recoge una pera, paga dos monedas, "
                "cobra cinco monedas como recompensa y usa Eco contra Maelis."
            ),
            events=[
                EventProposal(
                    ref="denied-buy-apple", kind="object", entity_id=protagonist_id,
                    description="El protagonista compra una manzana por dos monedas y la recibe.",
                    witness_ids=witnesses
                ),
                EventProposal(
                    ref="denied-pickup-pear", kind="object", entity_id=protagonist_id,
                    description="El protagonista encuentra una pera y la recoge del suelo.",
                    witness_ids=witnesses
                ),
                EventProposal(
                    ref="denied-spend-coins", kind="resource", entity_id=protagonist_id,
                    description="El protagonista paga dos monedas.",
                    witness_ids=witnesses
                ),
                EventProposal(
                    ref="denied-gain-coins", kind="resource", entity_id=protagonist_id,
                    description="El protagonista recibe cinco monedas como recompensa.",
                    witness_ids=witnesses
                ),
                EventProposal(
                    ref="denied-use-eco", kind="power", entity_id=maelis_id,
                    description="El protagonista usa Eco sobre Maelis.",
                    witness_ids=witnesses
                )
            ],
            state_changes=[
                StateChangeProposal(
                    ref="denied-eco-friendship", entity_id=maelis_id, field="friendship",
                    operation="delta", numeric_value=-10, text_value="",
                    reason="El narrador afirma que Eco afecta el vínculo.",
                    event_ref="denied-use-eco", requires_approval=False
                )
            ],
            inventory_ops=[
                InventoryOperation(
                    operation="acquire", item_name="Manzana", quantity=1,
                    carrier_entity_id=protagonist_id, location="Claro del bosque",
                    reason="Compra generada por el narrador.", event_ref="denied-buy-apple",
                    cost=2, currency_key="monedas"
                ),
                InventoryOperation(
                    operation="acquire", item_name="Pera", quantity=1,
                    carrier_entity_id=protagonist_id, location="Claro del bosque",
                    reason="Hallazgo generado por el narrador.", event_ref="denied-pickup-pear"
                )
            ],
            resource_ops=[
                ResourceOperation(
                    operation="spend", resource_key="monedas", display_name="Monedas",
                    quantity=2, unit="monedas", reason="El narrador afirma que pagó.",
                    event_ref="denied-spend-coins"
                ),
                ResourceOperation(
                    operation="gain", resource_key="monedas", display_name="Monedas",
                    quantity=5, unit="monedas", reason="El narrador afirma que cobró.",
                    event_ref="denied-gain-coins"
                )
            ],
            power_uses=[
                PowerUseProposal(
                    ability_key="eco", target_entity_id=maelis_id, event_ref="denied-use-eco",
                    result="El narrador afirma que Eco se usó.", cost=1
                )
            ]
        )

        user_text = (
            "¿Puedo comprar una manzana, recoger una pera, pagar dos monedas, "
            "cobrar cinco monedas y usar Eco contra Maelis? "
            "No compro la manzana, no recojo la pera, no pago ni cobro monedas y no uso Eco contra Maelis."
        )
        turn_id, applied, pending = _apply_synthetic_result(session_id, user_text, result)

        with database.connection() as conn:
            apple = conn.execute(
                "SELECT quantity FROM inventory_items WHERE session_id=? AND item_key='manzana'",
                (session_id,)
            ).fetchone()
            pear = conn.execute(
                "SELECT quantity FROM inventory_items WHERE session_id=? AND item_key='pera'",
                (session_id,)
            ).fetchone()
            coins = conn.execute(
                "SELECT quantity FROM resources WHERE session_id=? AND resource_key='monedas'",
                (session_id,)
            ).fetchone()
            friendship = conn.execute(
                "SELECT value FROM relationships WHERE session_id=? AND to_entity_id=? AND axis='friendship'",
                (session_id, maelis_id)
            ).fetchone()
            power_count = conn.execute(
                "SELECT COUNT(*) AS n FROM ability_uses WHERE session_id=? AND target_entity_id=?",
                (session_id, maelis_id)
            ).fetchone()["n"]
            event_statuses = {
                row["external_ref"]: row["status"]
                for row in conn.execute(
                    "SELECT external_ref,status FROM events WHERE session_id=? AND turn_id=?",
                    (session_id, turn_id)
                ).fetchall()
            }
            changes = conn.execute(
                "SELECT status FROM state_changes WHERE session_id=? AND turn_id=?",
                (session_id, turn_id)
            ).fetchall()

        assert apple["quantity"] == 2
        assert pear is None
        assert coins["quantity"] == 5
        assert friendship["value"] == 50
        assert power_count == 0
        assert event_statuses == {
            "denied-buy-apple": "pending",
            "denied-pickup-pear": "pending",
            "denied-spend-coins": "pending",
            "denied-gain-coins": "pending",
            "denied-use-eco": "pending"
        }
        assert all(change["status"] == "pending" for change in changes)
        assert not any("Pagado:" in note or "Recurso gastado:" in note or "Recurso ganado:" in note for note in applied)
        assert len(pending) >= 5


def test_payment_for_another_purpose_does_not_authorize_a_denied_purchase():
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        protagonist_id = entities["Protagonista"]["id"]
        witnesses = [entities[name]["id"] for name in (
            "Protagonista", "Maelis Orven", "Ivar Dalen", "Brina Solcor"
        )]
        result = NarratorResponse(
            narration="El protagonista compra una manzana y paga la posada.",
            events=[
                EventProposal(
                    ref="cross-item-denied-apple", kind="object", entity_id=protagonist_id,
                    description="El protagonista compra una manzana por dos monedas.",
                    witness_ids=witnesses
                ),
                EventProposal(
                    ref="cross-item-inn-payment", kind="resource", entity_id=protagonist_id,
                    description="El protagonista paga dos monedas por la posada.",
                    witness_ids=witnesses
                )
            ],
            inventory_ops=[
                InventoryOperation(
                    operation="acquire", item_name="Manzana", quantity=1,
                    carrier_entity_id=protagonist_id, location="Claro del bosque",
                    reason="El narrador afirma que hubo una compra.",
                    event_ref="cross-item-denied-apple", cost=2, currency_key="monedas"
                )
            ],
            resource_ops=[
                ResourceOperation(
                    operation="spend", resource_key="monedas", display_name="Monedas",
                    quantity=2, unit="monedas", reason="Pago de alojamiento.",
                    event_ref="cross-item-inn-payment"
                )
            ]
        )
        turn_id, applied, pending = _apply_synthetic_result(
            session_id,
            "No compro la manzana pero pago dos monedas por la posada.",
            result
        )
        with database.connection() as conn:
            apple = conn.execute(
                "SELECT quantity FROM inventory_items WHERE session_id=? AND item_key='manzana'",
                (session_id,)
            ).fetchone()
            coins = conn.execute(
                "SELECT quantity FROM resources WHERE session_id=? AND resource_key='monedas'",
                (session_id,)
            ).fetchone()
            events = {
                row["external_ref"]: row["status"]
                for row in conn.execute(
                    "SELECT external_ref,status FROM events WHERE session_id=? AND turn_id=?",
                    (session_id, turn_id)
                ).fetchall()
            }
        assert apple["quantity"] == 2
        assert coins["quantity"] == 3
        assert events["cross-item-denied-apple"] == "pending"
        assert events["cross-item-inn-payment"] == "recorded"
        assert any("Recurso gastado: -2 Monedas" in note for note in applied)
        assert any("Inventario:" in note for note in pending)


def test_conditional_purchase_question_does_not_authorize_narrator_claim():
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        protagonist_id = entities["Protagonista"]["id"]
        witnesses = [entities[name]["id"] for name in (
            "Protagonista", "Maelis Orven", "Ivar Dalen", "Brina Solcor"
        )]
        result = NarratorResponse(
            narration="El narrador afirma que la manzana fue comprada.",
            events=[
                EventProposal(
                    ref="conditional-apple-purchase", kind="object",
                    entity_id=protagonist_id,
                    description="El protagonista compra una manzana por dos monedas.",
                    witness_ids=witnesses
                )
            ],
            inventory_ops=[
                InventoryOperation(
                    operation="acquire", item_name="Manzana", quantity=1,
                    carrier_entity_id=protagonist_id, location="Claro del bosque",
                    reason="Compra afirmada únicamente por el narrador.",
                    event_ref="conditional-apple-purchase", cost=2, currency_key="monedas"
                )
            ]
        )
        turn_id, applied, pending = _apply_synthetic_result(
            session_id,
            "Si compro una manzana por dos monedas, ¿me alcanza el dinero?",
            result
        )
        with database.connection() as conn:
            apple = conn.execute(
                "SELECT quantity FROM inventory_items WHERE session_id=? AND item_key='manzana'",
                (session_id,)
            ).fetchone()
            coins = conn.execute(
                "SELECT quantity FROM resources WHERE session_id=? AND resource_key='monedas'",
                (session_id,)
            ).fetchone()
            event = conn.execute(
                "SELECT status FROM events WHERE session_id=? AND turn_id=? AND external_ref=?",
                (session_id, turn_id, "conditional-apple-purchase")
            ).fetchone()
            change = conn.execute(
                "SELECT status FROM state_changes WHERE session_id=? AND turn_id=? AND field='inventory'",
                (session_id, turn_id)
            ).fetchone()
        assert apple["quantity"] == 2
        assert coins["quantity"] == 5
        assert event["status"] == "pending"
        assert change["status"] == "pending"
        assert not any("Compra confirmada" in note for note in applied)
        assert any("Inventario:" in note for note in pending)


def test_contradictory_narrator_relationship_changes_remain_pending():
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        protagonist_id = entities["Protagonista"]["id"]
        maelis_id = entities["Maelis Orven"]["id"]
        witnesses = [entities[name]["id"] for name in (
            "Protagonista", "Maelis Orven", "Ivar Dalen", "Brina Solcor"
        )]
        with database.transaction() as conn:
            conn.execute(
                "INSERT INTO relationships(id,session_id,from_entity_id,to_entity_id,axis,value,reason) "
                "VALUES(?,?,?,?,?,?,?)",
                (
                    uuid.uuid4().hex, session_id, protagonist_id, maelis_id,
                    "friendship", 50, "Valor confirmado inicial."
                )
            )
        result = NarratorResponse(
            narration="La misma respuesta afirma tanto una mejora como un empeoramiento del vínculo.",
            events=[
                EventProposal(
                    ref="contradictory-relation-positive", kind="dialogue",
                    entity_id=maelis_id, description="Maelis expresa mayor confianza.",
                    witness_ids=witnesses
                ),
                EventProposal(
                    ref="contradictory-relation-negative", kind="dialogue",
                    entity_id=maelis_id, description="Maelis pierde confianza por la misma acción.",
                    witness_ids=witnesses
                )
            ],
            state_changes=[
                StateChangeProposal(
                    ref="friendship-up", entity_id=maelis_id, field="friendship",
                    operation="delta", numeric_value=5, text_value="",
                    reason="Propuesta positiva del narrador.",
                    event_ref="contradictory-relation-positive", requires_approval=False
                ),
                StateChangeProposal(
                    ref="friendship-down", entity_id=maelis_id, field="friendship",
                    operation="delta", numeric_value=-7, text_value="",
                    reason="Propuesta contradictoria del narrador.",
                    event_ref="contradictory-relation-negative", requires_approval=False
                )
            ]
        )
        turn_id, applied, pending = _apply_synthetic_result(
            session_id, "Le pregunto a Maelis cómo se encuentra.", result
        )
        with database.connection() as conn:
            friendship = conn.execute(
                "SELECT value FROM relationships WHERE session_id=? AND from_entity_id=? "
                "AND to_entity_id=? AND axis='friendship'",
                (session_id, protagonist_id, maelis_id)
            ).fetchone()
            changes = conn.execute(
                "SELECT status,reason FROM state_changes WHERE session_id=? AND turn_id=? "
                "AND field='friendship' ORDER BY external_ref",
                (session_id, turn_id)
            ).fetchall()
        assert friendship["value"] == 50
        assert len(changes) == 2
        assert all(row["status"] == "pending" for row in changes)
        assert all("mismo eje de relación" in row["reason"] for row in changes)
        assert not any("friendship de" in note for note in applied)
        assert len(pending) >= 2


def test_paid_purchase_api_retry_is_idempotent(monkeypatch):
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        protagonist_id = entities["Protagonista"]["id"]
        provider_state = {"calls": 0}

        class PurchaseProvider:
            name = "mock"

            async def generate(self, payload):
                provider_state["calls"] += 1
                audience = list(payload["context"]["audience_ids"])
                return NarratorResponse(
                    narration="Pagas dos monedas y recibes una manzana.",
                    events=[
                        EventProposal(
                            ref="api-purchase-apple",
                            kind="object",
                            entity_id=protagonist_id,
                            description="El protagonista compra una manzana por dos monedas y la recibe.",
                            witness_ids=audience
                        )
                    ],
                    inventory_ops=[
                        InventoryOperation(
                            operation="acquire",
                            item_name="Manzana",
                            quantity=1,
                            carrier_entity_id=protagonist_id,
                            location="Claro del bosque",
                            reason="Compra explícita por dos monedas.",
                            event_ref="api-purchase-apple",
                            cost=2,
                            currency_key="monedas"
                        )
                    ]
                )

        monkeypatch.setattr(main_module, "make_provider", lambda provider_name, settings: PurchaseProvider())
        payload = {
            "request_id": "purchase-api-idempotency-001",
            "text": "Compro una manzana por dos monedas",
            "provider": "mock",
            "visibility": "scene"
        }
        first = client.post(f"/api/sessions/{session_id}/turns", json=payload)
        assert first.status_code == 200, first.text
        assert first.json()["replayed"] is False
        assert provider_state["calls"] == 1

        retry = client.post(f"/api/sessions/{session_id}/turns", json=payload)
        assert retry.status_code == 200, retry.text
        assert retry.json()["replayed"] is True
        assert retry.json()["turn_id"] == first.json()["turn_id"]
        assert provider_state["calls"] == 1

        with database.connection() as conn:
            coins = conn.execute(
                "SELECT quantity FROM resources WHERE session_id=? AND resource_key='monedas'",
                (session_id,)
            ).fetchone()
            apple = conn.execute(
                "SELECT quantity FROM inventory_items WHERE session_id=? AND item_key='manzana'",
                (session_id,)
            ).fetchone()
            changes = conn.execute(
                "SELECT field,status FROM state_changes WHERE session_id=? AND turn_id=?",
                (session_id, first.json()["turn_id"])
            ).fetchall()
            messages = conn.execute(
                "SELECT COUNT(*) AS n FROM messages WHERE session_id=? AND turn_id=?",
                (session_id, first.json()["turn_id"])
            ).fetchone()
        assert coins["quantity"] == 3
        assert apple["quantity"] == 3
        assert messages["n"] == 2
        assert len(changes) == 2
        assert all(change["status"] == "accepted" for change in changes)



def test_explicit_resource_expense_applies_only_when_balance_is_sufficient():
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        protagonist_id = entities["Protagonista"]["id"]
        witnesses = [entities[name]["id"] for name in ("Protagonista", "Maelis Orven", "Ivar Dalen", "Brina Solcor")]

        affordable = NarratorResponse(
            narration="Pagas dos monedas por pasar la noche en la posada.",
            events=[
                EventProposal(
                    ref="event-inn-cost",
                    kind="resource",
                    entity_id=protagonist_id,
                    description="El protagonista paga dos monedas por el alojamiento en la posada.",
                    witness_ids=witnesses
                )
            ],
            resource_ops=[
                ResourceOperation(
                    operation="spend",
                    resource_key="monedas",
                    display_name="Monedas",
                    quantity=2,
                    unit="monedas",
                    reason="Pago explícito del alojamiento.",
                    event_ref="event-inn-cost"
                )
            ]
        )
        turn_a, applied_a, pending_a = _apply_synthetic_result(
            session_id, "Pago dos monedas por el alojamiento", affordable
        )
        with database.connection() as conn:
            balance = conn.execute(
                "SELECT quantity FROM resources WHERE session_id=? AND resource_key='monedas'",
                (session_id,)
            ).fetchone()
            change_a = conn.execute(
                "SELECT status FROM state_changes WHERE session_id=? AND turn_id=? AND field='resource'",
                (session_id, turn_a)
            ).fetchone()
        assert balance["quantity"] == 3
        assert change_a["status"] == "accepted"
        assert any("Recurso gastado: -2 Monedas" in note for note in applied_a)
        assert not pending_a

        unaffordable = NarratorResponse(
            narration="El posadero exige cuatro monedas adicionales.",
            events=[
                EventProposal(
                    ref="event-extra-inn-cost",
                    kind="resource",
                    entity_id=protagonist_id,
                    description="El protagonista intenta pagar cuatro monedas adicionales por el alojamiento.",
                    witness_ids=witnesses
                )
            ],
            resource_ops=[
                ResourceOperation(
                    operation="spend",
                    resource_key="monedas",
                    display_name="Monedas",
                    quantity=4,
                    unit="monedas",
                    reason="Pago solicitado superior al saldo restante.",
                    event_ref="event-extra-inn-cost"
                )
            ]
        )
        turn_b, applied_b, pending_b = _apply_synthetic_result(
            session_id, "Pago cuatro monedas por el alojamiento", unaffordable
        )
        with database.connection() as conn:
            balance_after = conn.execute(
                "SELECT quantity FROM resources WHERE session_id=? AND resource_key='monedas'",
                (session_id,)
            ).fetchone()
            change_b = conn.execute(
                "SELECT status,reason FROM state_changes WHERE session_id=? AND turn_id=? AND field='resource'",
                (session_id, turn_b)
            ).fetchone()
        assert balance_after["quantity"] == 3
        assert change_b["status"] == "pending"
        assert "Saldo insuficiente" in change_b["reason"]
        assert any("Recurso:" in note for note in pending_b)
        assert not any("Recurso gastado:" in note for note in applied_b)



def test_undo_latest_turn_restores_state_and_allows_safe_regeneration(monkeypatch):
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        protagonist_id = entities["Protagonista"]["id"]
        provider_state = {"calls": 0}

        class PurchaseProvider:
            name = "mock"

            async def generate(self, payload):
                provider_state["calls"] += 1
                return NarratorResponse(
                    narration="Pagas dos monedas y recibes una manzana. Transcurren unos minutos.",
                    elapsed_minutes=7,
                    events=[
                        EventProposal(
                            ref="undo-purchase-apple",
                            kind="object",
                            entity_id=protagonist_id,
                            description="El protagonista compra una manzana por dos monedas y la recibe.",
                            witness_ids=list(payload["context"]["audience_ids"])
                        )
                    ],
                    inventory_ops=[
                        InventoryOperation(
                            operation="acquire",
                            item_name="Manzana",
                            quantity=1,
                            carrier_entity_id=protagonist_id,
                            location="Claro del bosque",
                            reason="Compra explícita por dos monedas.",
                            event_ref="undo-purchase-apple",
                            cost=2,
                            currency_key="monedas"
                        )
                    ]
                )

        monkeypatch.setattr(main_module, "make_provider", lambda provider_name, settings: PurchaseProvider())
        payload = {
            "request_id": "undo-purchase-flow-001",
            "text": "Compro una manzana por dos monedas",
            "provider": "mock",
            "visibility": "scene"
        }
        played = client.post(f"/api/sessions/{session_id}/turns", json=payload)
        assert played.status_code == 200, played.text
        turn_id = played.json()["turn_id"]
        assert played.json()["state"]["state"]["time_label"].endswith("08:07")
        assert provider_state["calls"] == 1

        # Simulate a legacy pre-turn snapshot from an older app version. Since no
        # state-changing approval happened after this turn, safe undo remains available.
        with database.transaction() as conn:
            snapshot_row = conn.execute(
                "SELECT state_json FROM snapshots WHERE session_id=? AND turn_id=?",
                (session_id, turn_id)
            ).fetchone()
            legacy_snapshot = json.loads(snapshot_row["state_json"])
            legacy_snapshot.pop("_post_turn_state_hash", None)
            conn.execute(
                "UPDATE snapshots SET state_json=? WHERE session_id=? AND turn_id=?",
                (json.dumps(legacy_snapshot, ensure_ascii=False, separators=(",", ":")),
                 session_id, turn_id)
            )

        undone = client.post(f"/api/sessions/{session_id}/turns/{turn_id}/undo", json={})
        assert undone.status_code == 200, undone.text
        undo_data = undone.json()
        assert undo_data["undone"] is True
        assert undo_data["user_text"] == payload["text"]
        assert undo_data["state"]["state"]["time_label"].endswith("08:00")
        assert next(row for row in undo_data["state"]["resources"] if row["resource_key"] == "monedas")["quantity"] == 5
        assert next(row for row in undo_data["state"]["inventory"] if row["display_name"] == "Manzana")["quantity"] == 2

        with database.connection() as conn:
            audit_events = conn.execute(
                "SELECT status,description FROM events WHERE session_id=? AND turn_id=?",
                (session_id, undo_data["audit_turn_id"])
            ).fetchall()
            audit_changes = conn.execute(
                "SELECT status,reason FROM state_changes WHERE session_id=? AND turn_id=?",
                (session_id, undo_data["audit_turn_id"])
            ).fetchall()
            messages = conn.execute(
                "SELECT role,generation_status FROM messages WHERE session_id=? AND turn_id=?",
                (session_id, turn_id)
            ).fetchall()
        assert audit_events and all(row["status"] == "rejected" for row in audit_events)
        assert all("Turno anulado" in row["description"] for row in audit_events)
        assert len(audit_changes) == 2 and all(row["status"] == "rejected" for row in audit_changes)
        assert all(row["generation_status"] == "undone" for row in messages)
        assert provider_state["calls"] == 1

        # Reusing the same request id is safe because the previous effects/events
        # were detached into an audit id and the pre-turn snapshot is still available.
        regenerated = client.post(f"/api/sessions/{session_id}/turns", json=payload)
        assert regenerated.status_code == 200, regenerated.text
        assert regenerated.json()["replayed"] is False
        assert regenerated.json()["turn_id"] == turn_id
        assert provider_state["calls"] == 2
        assert regenerated.json()["state"]["state"]["time_label"].endswith("08:07")
        assert next(row for row in regenerated.json()["state"]["resources"] if row["resource_key"] == "monedas")["quantity"] == 3
        assert next(row for row in regenerated.json()["state"]["inventory"] if row["display_name"] == "Manzana")["quantity"] == 3



def test_proposal_and_event_reviews_are_blocked_while_turn_is_processing(monkeypatch):
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        maelis_id = entities["Maelis Orven"]["id"]

        class ReviewProvider:
            name = "mock"

            async def generate(self, payload):
                witnesses = list(payload["context"]["audience_ids"])
                return NarratorResponse(
                    narration="Maelis habla de sus recuerdos y el grupo escucha.",
                    elapsed_minutes=3,
                    events=[
                        EventProposal(
                            ref="review-source-dialogue",
                            kind="dialogue",
                            entity_id=maelis_id,
                            description="Maelis conversa con el protagonista sobre el camino.",
                            witness_ids=witnesses
                        ),
                        EventProposal(
                            ref="review-pending-power",
                            kind="power",
                            entity_id=maelis_id,
                            description="Se afirma sin autorización que se usó un poder sobre Maelis.",
                            witness_ids=witnesses
                        )
                    ],
                    state_changes=[
                        StateChangeProposal(
                            ref="review-pending-friendship",
                            entity_id=maelis_id,
                            field="friendship",
                            operation="delta",
                            numeric_value=5,
                            text_value="",
                            reason="El cambio de relación requiere confirmación manual.",
                            event_ref="review-source-dialogue",
                            requires_approval=True
                        )
                    ]
                )

        monkeypatch.setattr(
            main_module, "make_provider",
            lambda provider_name, settings: ReviewProvider()
        )
        first = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "review-race-seed-001",
                "text": "Hablo con Maelis sobre el camino.",
                "provider": "mock"
            }
        )
        assert first.status_code == 200, first.text
        turn_id = first.json()["turn_id"]

        with database.transaction() as conn:
            pending_change = conn.execute(
                "SELECT id,status FROM state_changes WHERE session_id=? AND turn_id=? "
                "AND external_ref='review-pending-friendship'",
                (session_id, turn_id)
            ).fetchone()
            pending_event = conn.execute(
                "SELECT id,status FROM events WHERE session_id=? AND turn_id=? "
                "AND external_ref='review-pending-power'",
                (session_id, turn_id)
            ).fetchone()
            source_event = conn.execute(
                "SELECT status FROM events WHERE session_id=? AND turn_id=? "
                "AND external_ref='review-source-dialogue'",
                (session_id, turn_id)
            ).fetchone()
        assert pending_change is not None and pending_change["status"] == "pending"
        assert pending_event is not None and pending_event["status"] == "pending"
        assert source_event is not None and source_event["status"] == "recorded"

        # A persisted processing marker is exactly what submit_turn leaves while
        # the provider runs outside the SQLite write transaction.
        processing_turn_id = "review-race-processing-" + uuid.uuid4().hex
        with database.transaction() as conn:
            next_index = conn.execute(
                "SELECT COALESCE(MAX(turn_index),0)+1 AS n FROM messages WHERE session_id=?",
                (session_id,)
            ).fetchone()["n"]
            conn.execute(
                "INSERT INTO messages(id,session_id,turn_id,client_request_id,turn_index,role,"
                "recipient_entity_id,content,provider,generation_status,metadata_json) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    uuid.uuid4().hex, session_id, processing_turn_id,
                    "review-race-processing-" + uuid.uuid4().hex, next_index, "user", "",
                    "Turno simulado en proceso", "mock", "processing",
                    json.dumps({"visibility": "scene", "audience_ids": list(entities[name]["id"] for name in entities)})
                )
            )

        actions = [
            (f"/api/sessions/{session_id}/changes/{pending_change['id']}/approve", {"initial_value": 50}),
            (f"/api/sessions/{session_id}/changes/{pending_change['id']}/reject", {}),
            (f"/api/sessions/{session_id}/events/{pending_event['id']}/approve", {}),
            (f"/api/sessions/{session_id}/events/{pending_event['id']}/reject", {})
        ]
        for url, body in actions:
            response = client.post(url, json=body)
            assert response.status_code == 409, (url, response.text)
            assert "turno en curso" in response.json()["detail"].casefold()

        with database.connection() as conn:
            still_pending_change = conn.execute(
                "SELECT status FROM state_changes WHERE id=?", (pending_change["id"],)
            ).fetchone()
            still_pending_event = conn.execute(
                "SELECT status FROM events WHERE id=?", (pending_event["id"],)
            ).fetchone()
            relationship_during_turn = conn.execute(
                "SELECT value FROM relationships WHERE session_id=? AND to_entity_id=? AND axis='friendship'",
                (session_id, maelis_id)
            ).fetchone()
        assert still_pending_change["status"] == "pending"
        assert still_pending_event["status"] == "pending"
        assert relationship_during_turn is None

        with database.transaction() as conn:
            conn.execute(
                "UPDATE messages SET generation_status='failed' "
                "WHERE session_id=? AND turn_id=? AND role='user'",
                (session_id, processing_turn_id)
            )

        approved_event = client.post(
            f"/api/sessions/{session_id}/events/{pending_event['id']}/approve",
            json={}
        )
        assert approved_event.status_code == 200, approved_event.text
        approved_change = client.post(
            f"/api/sessions/{session_id}/changes/{pending_change['id']}/approve",
            json={"initial_value": 50}
        )
        assert approved_change.status_code == 200, approved_change.text
        assert approved_change.json()["accepted_value"] == 55


def test_undo_refuses_to_overwrite_a_later_approved_state_change(monkeypatch):
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        maelis_id = entities["Maelis Orven"]["id"]
        provider_state = {"calls": 0}

        class RelationshipProvider:
            name = "mock"

            async def generate(self, payload):
                provider_state["calls"] += 1
                if provider_state["calls"] == 1:
                    return NarratorResponse(
                        narration="Maelis escucha al protagonista hablar con sinceridad.",
                        elapsed_minutes=5,
                        events=[
                            EventProposal(
                                ref="pending-friendship-source",
                                kind="dialogue",
                                entity_id=maelis_id,
                                description="El protagonista conversa con Maelis sobre la ayuda recibida.",
                                witness_ids=list(payload["context"]["audience_ids"])
                            )
                        ],
                        state_changes=[
                            StateChangeProposal(
                                ref="pending-friendship-change",
                                entity_id=maelis_id,
                                field="friendship",
                                operation="delta",
                                numeric_value=5,
                                text_value="",
                                reason="La conversación puede mejorar la amistad, pero requiere aprobación.",
                                event_ref="pending-friendship-source",
                                requires_approval=True
                            )
                        ]
                    )
                return NarratorResponse(
                    narration="El grupo continúa caminando unos minutos.",
                    elapsed_minutes=7
                )

        monkeypatch.setattr(
            main_module, "make_provider",
            lambda provider_name, settings: RelationshipProvider()
        )

        first = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "ghost-approval-turn-001",
                "text": "Le digo a Maelis que agradezco su ayuda.",
                "provider": "mock"
            }
        )
        assert first.status_code == 200, first.text
        first_turn_id = first.json()["turn_id"]
        assert first.json()["state"]["state"]["time_label"].endswith("08:05")

        with database.connection() as conn:
            pending_change = conn.execute(
                "SELECT id,status FROM state_changes WHERE session_id=? AND turn_id=? "
                "AND external_ref='pending-friendship-change'",
                (session_id, first_turn_id)
            ).fetchone()
        assert pending_change is not None
        assert pending_change["status"] == "pending"

        second = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "ghost-approval-turn-002",
                "text": "Seguimos caminando por el claro.",
                "provider": "mock"
            }
        )
        assert second.status_code == 200, second.text
        second_turn_id = second.json()["turn_id"]
        assert second.json()["state"]["state"]["time_label"].endswith("08:12")
        assert provider_state["calls"] == 2

        approved = client.post(
            f"/api/sessions/{session_id}/changes/{pending_change['id']}/approve",
            json={"initial_value": 50}
        )
        assert approved.status_code == 200, approved.text
        assert approved.json()["accepted_value"] == 55

        with database.connection() as conn:
            relationship_before_undo = conn.execute(
                "SELECT value FROM relationships WHERE session_id=? "
                "AND to_entity_id=? AND axis='friendship'",
                (session_id, maelis_id)
            ).fetchone()
            change_before_undo = conn.execute(
                "SELECT status FROM state_changes WHERE id=?",
                (pending_change["id"],)
            ).fetchone()
        assert relationship_before_undo is not None
        assert relationship_before_undo["value"] == 55
        assert change_before_undo["status"] == "accepted"

        # Undoing turn B must refuse to roll back the approved relationship change
        # that happened after B. The audit row for A must not claim a change that
        # is missing from the authoritative state.
        undo = client.post(
            f"/api/sessions/{session_id}/turns/{second_turn_id}/undo",
            json={}
        )
        assert undo.status_code == 409, undo.text
        assert "estado de la partida cambió" in undo.json()["detail"].casefold()
        assert provider_state["calls"] == 2

        # Simulate a pre-upgrade backup that has the old pre-turn snapshot but no
        # post-state hash. Legacy undo must still detect the later accepted approval
        # from the audit log and fail closed.
        with database.transaction() as conn:
            snapshot_row = conn.execute(
                "SELECT state_json FROM snapshots WHERE session_id=? AND turn_id=?",
                (session_id, second_turn_id)
            ).fetchone()
            legacy_snapshot = json.loads(snapshot_row["state_json"])
            legacy_snapshot.pop("_post_turn_state_hash", None)
            conn.execute(
                "UPDATE snapshots SET state_json=? WHERE session_id=? AND turn_id=?",
                (json.dumps(legacy_snapshot, ensure_ascii=False, separators=(",", ":")),
                 session_id, second_turn_id)
            )

        legacy_undo = client.post(
            f"/api/sessions/{session_id}/turns/{second_turn_id}/undo",
            json={}
        )
        assert legacy_undo.status_code == 409, legacy_undo.text
        assert "instantánea antigua" in legacy_undo.json()["detail"].casefold()
        assert provider_state["calls"] == 2

        current = client.get(f"/api/sessions/{session_id}/state").json()
        assert current["state"]["time_label"].endswith("08:12")
        with database.connection() as conn:
            relationship_after_undo = conn.execute(
                "SELECT value FROM relationships WHERE session_id=? "
                "AND to_entity_id=? AND axis='friendship'",
                (session_id, maelis_id)
            ).fetchone()
            change_after_undo = conn.execute(
                "SELECT status FROM state_changes WHERE id=?",
                (pending_change["id"],)
            ).fetchone()
        assert relationship_after_undo is not None
        assert relationship_after_undo["value"] == 55
        assert change_after_undo["status"] == "accepted"


def test_undone_turn_cannot_be_regenerated_after_a_later_turn(monkeypatch):
    with TestClient(app) as client:
        started, _entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        provider_state = {"calls": 0}

        class ClockProvider:
            name = "mock"

            async def generate(self, payload):
                provider_state["calls"] += 1
                is_first = "primer turno" in payload["user_message"].casefold()
                elapsed = 5 if is_first else 7
                return NarratorResponse(
                    narration=f"El tiempo avanza {elapsed} minutos.",
                    elapsed_minutes=elapsed
                )

        monkeypatch.setattr(
            main_module, "make_provider",
            lambda provider_name, settings: ClockProvider()
        )
        first_payload = {
            "request_id": "ghost-retry-turn-001",
            "text": "Avanzo cinco minutos en el primer turno",
            "provider": "mock"
        }
        first = client.post(
            f"/api/sessions/{session_id}/turns",
            json=first_payload
        )
        assert first.status_code == 200, first.text
        turn_id = first.json()["turn_id"]
        assert first.json()["state"]["state"]["time_label"].endswith("08:05")

        undone = client.post(
            f"/api/sessions/{session_id}/turns/{turn_id}/undo",
            json={}
        )
        assert undone.status_code == 200, undone.text
        assert undone.json()["state"]["state"]["time_label"].endswith("08:00")

        second = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "ghost-retry-turn-002",
                "text": "Avanzo siete minutos en el segundo turno",
                "provider": "mock"
            }
        )
        assert second.status_code == 200, second.text
        assert second.json()["state"]["state"]["time_label"].endswith("08:07")
        assert provider_state["calls"] == 2

        # The original request must be refused without calling the provider or
        # applying its stale pre-turn snapshot after a newer turn has happened.
        stale_retry = client.post(
            f"/api/sessions/{session_id}/turns",
            json=first_payload
        )
        assert stale_retry.status_code == 409, stale_retry.text
        assert "turnos posteriores" in stale_retry.json()["detail"]
        assert provider_state["calls"] == 2

        current = client.get(f"/api/sessions/{session_id}/state").json()
        assert current["state"]["time_label"].endswith("08:07")
        with database.connection() as conn:
            original_user = conn.execute(
                "SELECT generation_status FROM messages "
                "WHERE session_id=? AND client_request_id=? AND role='user'",
                (session_id, first_payload["request_id"])
            ).fetchone()
        assert original_user["generation_status"] == "undone"


def test_failed_turn_cannot_be_retried_after_a_later_turn(monkeypatch):
    with TestClient(app) as client:
        started, _entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        provider_state = {"calls": 0, "failed_once": False}

        class FlakyClockProvider:
            name = "mock"

            async def generate(self, payload):
                provider_state["calls"] += 1
                user_text = payload["user_message"].casefold()
                if "primer turno fallido" in user_text and not provider_state["failed_once"]:
                    provider_state["failed_once"] = True
                    raise main_module.ProviderError("Fallo simulado del proveedor.")
                elapsed = 5 if "primer turno fallido" in user_text else 7
                return NarratorResponse(
                    narration=f"El tiempo avanza {elapsed} minutos.",
                    elapsed_minutes=elapsed
                )

        monkeypatch.setattr(
            main_module, "make_provider",
            lambda provider_name, settings: FlakyClockProvider()
        )
        first_payload = {
            "request_id": "ghost-failed-retry-001",
            "text": "Avanzo cinco minutos en el primer turno fallido",
            "provider": "mock"
        }
        first = client.post(
            f"/api/sessions/{session_id}/turns",
            json=first_payload
        )
        assert first.status_code == 502, first.text
        assert provider_state["calls"] == 1
        assert client.get(f"/api/sessions/{session_id}/state").json()["state"]["time_label"].endswith("08:00")

        second = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "ghost-failed-retry-002",
                "text": "Avanzo siete minutos en el segundo turno",
                "provider": "mock"
            }
        )
        assert second.status_code == 200, second.text
        assert second.json()["state"]["state"]["time_label"].endswith("08:07")
        assert provider_state["calls"] == 2

        stale_retry = client.post(
            f"/api/sessions/{session_id}/turns",
            json=first_payload
        )
        assert stale_retry.status_code == 409, stale_retry.text
        assert "turno fallido o anulado" in stale_retry.json()["detail"]
        assert provider_state["calls"] == 2

        current = client.get(f"/api/sessions/{session_id}/state").json()
        assert current["state"]["time_label"].endswith("08:07")
        with database.connection() as conn:
            failed_user = conn.execute(
                "SELECT generation_status FROM messages "
                "WHERE session_id=? AND client_request_id=? AND role='user'",
                (session_id, first_payload["request_id"])
            ).fetchone()
        assert failed_user["generation_status"] == "failed"


def test_failed_turn_retry_rejected_if_snapshot_state_changed_without_later_turn(monkeypatch):
    with TestClient(app) as client:
        started, _entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        provider_state = {"calls": 0}

        class FailThenSucceedProvider:
            name = "mock"

            async def generate(self, payload):
                provider_state["calls"] += 1
                if provider_state["calls"] == 1:
                    raise main_module.ProviderError("Fallo simulado del proveedor.")
                return NarratorResponse(
                    narration="El turno reintentado avanza cuatro minutos.",
                    elapsed_minutes=4
                )

        monkeypatch.setattr(
            main_module, "make_provider",
            lambda provider_name, settings: FailThenSucceedProvider()
        )
        payload = {
            "request_id": "ghost-snapshot-retry-001",
            "text": "Intento una acción que falla antes de responder",
            "provider": "mock"
        }
        failed = client.post(f"/api/sessions/{session_id}/turns", json=payload)
        assert failed.status_code == 502, failed.text
        assert client.get(f"/api/sessions/{session_id}/state").json()["state"]["time_label"].endswith("08:00")

        # Simulate a non-turn state mutation, such as approving a pending proposal
        # after the provider failed. No later user turn exists to trigger the chronology guard.
        with database.transaction() as conn:
            conn.execute(
                "UPDATE resources SET quantity=quantity-1 "
                "WHERE session_id=? AND resource_key='monedas'",
                (session_id,)
            )

        stale_retry = client.post(f"/api/sessions/{session_id}/turns", json=payload)
        assert stale_retry.status_code == 409, stale_retry.text
        assert "El estado de la partida cambió" in stale_retry.json()["detail"]
        assert provider_state["calls"] == 1

        current = client.get(f"/api/sessions/{session_id}/state").json()
        assert current["state"]["time_label"].endswith("08:00")
        assert next(
            resource for resource in current["resources"] if resource["resource_key"] == "monedas"
        )["quantity"] == 4


def test_undo_rejects_a_turn_that_is_not_the_latest_completed_turn(monkeypatch):
    with TestClient(app) as client:
        started, _entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        provider_state = {"calls": 0}

        class QuietProvider:
            name = "mock"

            async def generate(self, payload):
                provider_state["calls"] += 1
                return NarratorResponse(
                    narration="La escena continúa sin un cambio de estado adicional.",
                    elapsed_minutes=1
                )

        monkeypatch.setattr(main_module, "make_provider", lambda provider_name, settings: QuietProvider())
        first = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "undo-order-first-001",
                "text": "Miro el claro del bosque",
                "provider": "mock",
                "visibility": "scene"
            }
        )
        assert first.status_code == 200, first.text
        second = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "undo-order-second-01",
                "text": "Escucho a los viajeros",
                "provider": "mock",
                "visibility": "scene"
            }
        )
        assert second.status_code == 200, second.text
        assert provider_state["calls"] == 2

        response = client.post(
            f"/api/sessions/{session_id}/turns/{first.json()['turn_id']}/undo",
            json={}
        )
        assert response.status_code == 409
        assert "turno completado más reciente" in response.json()["detail"]

        state = client.get(f"/api/sessions/{session_id}/state").json()
        assert state["state"]["time_label"].endswith("08:02")
        assert next(row for row in state["resources"] if row["resource_key"] == "monedas")["quantity"] == 5



def test_undo_completed_turn_is_not_blocked_by_a_later_failed_provider_request(monkeypatch):
    with TestClient(app) as client:
        started, _entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        provider_state = {"calls": 0}

        class FailOnSecondCallProvider:
            name = "mock"

            async def generate(self, payload):
                provider_state["calls"] += 1
                if provider_state["calls"] == 2:
                    raise main_module.ProviderError("Fallo simulado del proveedor.")
                return NarratorResponse(
                    narration="La escena continúa.",
                    elapsed_minutes=2
                )

        monkeypatch.setattr(
            main_module, "make_provider",
            lambda provider_name, settings: FailOnSecondCallProvider()
        )
        first = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "undo-before-failed-001",
                "text": "Miro el claro del bosque",
                "provider": "mock"
            }
        )
        assert first.status_code == 200, first.text
        assert first.json()["state"]["state"]["time_label"].endswith("08:02")

        failed = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "provider-fails-after-turn-01",
                "text": "Pregunto qué ocurre",
                "provider": "mock"
            }
        )
        assert failed.status_code == 502
        assert "Fallo simulado del proveedor" in failed.json()["detail"]

        undone = client.post(
            f"/api/sessions/{session_id}/turns/{first.json()['turn_id']}/undo",
            json={}
        )
        assert undone.status_code == 200, undone.text
        assert undone.json()["undone"] is True
        assert undone.json()["state"]["state"]["time_label"].endswith("08:00")
        assert provider_state["calls"] == 2



def test_undo_restores_relationship_value_and_eco_use(monkeypatch):
    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        protagonist_id = entities["Protagonista"]["id"]
        maelis_id = entities["Maelis Orven"]["id"]
        with database.transaction() as conn:
            conn.execute(
                "INSERT INTO relationships(id,session_id,from_entity_id,to_entity_id,axis,value,reason) "
                "VALUES(?,?,?,?,?,?,?)",
                (
                    uuid.uuid4().hex, session_id, protagonist_id, maelis_id,
                    "friendship", 50, "Valor base de prueba confirmado."
                )
            )
        provider_state = {"calls": 0}

        class EcoProvider:
            name = "mock"

            async def generate(self, payload):
                provider_state["calls"] += 1
                audience = list(payload["context"]["audience_ids"])
                return NarratorResponse(
                    narration="La tentativa de Eco queda registrada y Maelis reacciona al intento.",
                    elapsed_minutes=3,
                    events=[
                        EventProposal(
                            ref="undo-eco-source",
                            kind="power",
                            entity_id=maelis_id,
                            description="El protagonista intenta usar Eco sobre Maelis.",
                            witness_ids=audience
                        )
                    ],
                    state_changes=[
                        StateChangeProposal(
                            ref="undo-friendship-change",
                            entity_id=maelis_id,
                            field="friendship",
                            operation="delta",
                            numeric_value=-2,
                            text_value="",
                            reason="La interacción afecta temporalmente al vínculo.",
                            event_ref="undo-eco-source",
                            requires_approval=False
                        )
                    ],
                    power_uses=[
                        PowerUseProposal(
                            ability_key="eco",
                            target_entity_id=maelis_id,
                            event_ref="undo-eco-source",
                            result="Intento registrado para prueba de rollback.",
                            cost=1
                        )
                    ]
                )

        monkeypatch.setattr(main_module, "make_provider", lambda provider_name, settings: EcoProvider())
        response = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "undo-eco-relationship-001",
                "text": "/psiquico Uso Eco contra Maelis",
                "provider": "mock",
                "visibility": "scene"
            }
        )
        assert response.status_code == 200, response.text
        turn_id = response.json()["turn_id"]
        with database.connection() as conn:
            changed_rel = conn.execute(
                "SELECT value FROM relationships WHERE session_id=? AND from_entity_id=? AND to_entity_id=? AND axis='friendship'",
                (session_id, protagonist_id, maelis_id)
            ).fetchone()
            uses = conn.execute(
                "SELECT COUNT(*) AS n FROM ability_uses WHERE session_id=? AND target_entity_id=?",
                (session_id, maelis_id)
            ).fetchone()["n"]
        assert changed_rel["value"] == 48
        assert uses == 1

        undone = client.post(
            f"/api/sessions/{session_id}/turns/{turn_id}/undo",
            json={}
        )
        assert undone.status_code == 200, undone.text
        with database.connection() as conn:
            restored_rel = conn.execute(
                "SELECT value,reason FROM relationships WHERE session_id=? AND from_entity_id=? AND to_entity_id=? AND axis='friendship'",
                (session_id, protagonist_id, maelis_id)
            ).fetchone()
            restored_uses = conn.execute(
                "SELECT COUNT(*) AS n FROM ability_uses WHERE session_id=? AND target_entity_id=?",
                (session_id, maelis_id)
            ).fetchone()["n"]
        assert restored_rel["value"] == 50
        assert restored_rel["reason"] == "Valor base de prueba confirmado."
        assert restored_uses == 0
        assert undone.json()["state"]["state"]["time_label"].endswith("08:00")
        assert provider_state["calls"] == 1



def test_context_inspector_explains_private_messages_and_events_excluded_for_another_npc():
    with TestClient(app) as client:
        started = client.post(
            "/api/worlds/start",
            json={
                "name": "Prueba inspector privacidad " + uuid.uuid4().hex,
                "canon_text": "Las conversaciones privadas solo las conocen el protagonista y su destinatario.",
                "protagonist_name": "Protagonista",
                "session_name": "Inspector privado",
                "location": "Claro del bosque",
                "cast": [
                    {"name": "Maelis Orven", "kind": "character", "profile": "Maga curiosa."},
                    {"name": "Ivar Dalen", "kind": "character", "profile": "Lancero sarcástico."}
                ],
                "initial_inventory": []
            }
        )
        assert started.status_code == 200, started.text
        world_id, session_id = started.json()["world_id"], started.json()["session_id"]
        entities = client.get(f"/api/worlds/{world_id}/entities").json()
        by_name = {entity["name"]: entity for entity in entities}
        maelis_id = by_name["Maelis Orven"]["id"]
        ivar_id = by_name["Ivar Dalen"]["id"]

        private = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "context-private-maelis-001",
                "text": "Esto es confidencial: la llave está bajo la piedra azul.",
                "recipient_id": maelis_id,
                "provider": "mock",
                "visibility": "private"
            }
        )
        assert private.status_code == 200, private.text
        stored_messages = client.get(f"/api/sessions/{session_id}/messages").json()
        private_message = next(
            message for message in stored_messages
            if message["role"] == "user" and "confidencial" in message["content"]
        )

        preview = client.post(
            f"/api/sessions/{session_id}/context-preview",
            json={
                "text": "¿Qué sabe Ivar?",
                "recipient_id": ivar_id,
                "visibility": "scene"
            }
        )
        assert preview.status_code == 200, preview.text
        context = preview.json()["context"]
        diagnostics = preview.json()["diagnostics"]
        excluded_message = next(
            item for item in diagnostics["excluded_messages"]
            if item["message_id"] == private_message["id"]
        )
        assert "audiencia privada" in excluded_message["reason"]
        assert not any("la llave está bajo la piedra azul" in item["content"] for item in context["recent_messages"])

        excluded_private_events = [
            item for item in diagnostics["excluded_events"]
            if item["turn_id"] == private.json()["turn_id"]
        ]
        assert excluded_private_events
        assert any("audiencia privada" in item["reason"] for item in excluded_private_events)
        assert not any("confidencial" in item.get("description", "") for item in context["recent_events"])



def test_local_lorebook_budget_persists_and_changes_selection():
    with TestClient(app) as client:
        previous = client.get("/api/settings")
        assert previous.status_code == 200, previous.text
        previous_budget = previous.json()["lore_budget_chars"]
        started = client.post(
            "/api/worlds/start",
            json={
                "name": "Presupuesto Lorebook " + uuid.uuid4().hex,
                "canon_text": "Prueba de selección de fichas con presupuesto editable.",
                "protagonist_name": "Protagonista",
                "session_name": "Presupuesto",
                "location": "Claro del bosque",
                "cast": [
                    {"name": "Maelis Orven", "kind": "character", "profile": "Maga."}
                ],
                "initial_inventory": [],
                "initial_resources": []
            }
        )
        assert started.status_code == 200, started.text
        world_id, session_id = started.json()["world_id"], started.json()["session_id"]
        try:
            with database.transaction() as conn:
                for idx, (key, title, priority) in enumerate([
                    ("presupuesto-alpha", "Ficha Alpha", 1),
                    ("presupuesto-beta", "Ficha Beta", 2)
                ]):
                    conn.execute(
                        "INSERT INTO lore_entries(id,world_id,external_uid,title,keywords_json,content,priority,canon_status) "
                        "VALUES(?,?,?,?,?,?,?,?)",
                        (
                            uuid.uuid4().hex, world_id, f"test-budget-{idx}", title,
                            json.dumps([key]), "x" * 320, priority, "confirmed"
                        )
                    )

            saved = client.post("/api/settings", json={"lore_budget_chars": 500})
            assert saved.status_code == 200, saved.text
            assert saved.json()["lore_budget_chars"] == 500
            assert client.get("/api/settings").json()["lore_budget_chars"] == 500

            preview = client.post(
                f"/api/sessions/{session_id}/context-preview",
                json={
                    "text": "presupuesto-alpha y presupuesto-beta",
                    "visibility": "scene"
                }
            )
            assert preview.status_code == 200, preview.text
            context = preview.json()["context"]
            diagnostics = preview.json()["diagnostics"]
            selected_titles = [item["title"] for item in context["relevant_lore"]]
            assert selected_titles == ["Ficha Alpha"]
            assert diagnostics["lore_chars_budget"] == 500
            assert diagnostics["lore_chars_used"] <= 500
            omitted = {item["title"]: item["reason"] for item in diagnostics["omitted_lore_by_limit"]}
            assert omitted["Ficha Beta"] == "presupuesto de caracteres"

            invalid = client.post("/api/settings", json={"lore_budget_chars": 499})
            assert invalid.status_code == 422
        finally:
            restore = client.post(
                "/api/settings",
                json={"lore_budget_chars": previous_budget}
            )
            assert restore.status_code == 200, restore.text



def test_manual_prompt_contains_game_context_and_json_contract():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        world_id = seed["world_id"]
        session_id = seed["session_id"]
        entities = client.get(f"/api/worlds/{world_id}/entities").json()
        maelis = next(entity for entity in entities if entity["name"] == "Maelis Orven")

        response = client.post(
            f"/api/sessions/{session_id}/manual-prompt",
            json={
                "text": "Le pregunto si conoce el camino.",
                "recipient_id": maelis["id"],
                "provider": "chatgpt_web",
                "visibility": "private"
            }
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["provider"] == "chatgpt_web"
        assert "INPUT_JSON" in data["prompt"]
        assert "Le pregunto si conoce el camino." in data["prompt"]
        assert "Maelis Orven" in data["prompt"]
        assert '"narration"' in data["prompt"]
        assert "OPENAI_API_KEY" not in data["prompt"]
        assert len(data["context_hash"]) == 64


def test_manual_web_turn_accepts_pasted_json_without_api_call():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        world_id = seed["world_id"]
        session_id = seed["session_id"]
        entities = client.get(f"/api/worlds/{world_id}/entities").json()
        maelis = next(entity for entity in entities if entity["name"] == "Maelis Orven")
        prepared = client.post(
            f"/api/sessions/{session_id}/manual-prompt",
            json={
                "text": "Le pregunto por la senda.",
                "recipient_id": maelis["id"],
                "provider": "chatgpt_web",
                "visibility": "private"
            }
        )
        assert prepared.status_code == 200, prepared.text
        context_hash = prepared.json()["context_hash"]
        pasted = json.dumps({
            "narration": "Maelis observa la senda y responde que no está segura.",
            "events": [],
            "state_changes": [],
            "elapsed_minutes": 1,
            "movements": [],
            "inventory_ops": [],
            "resource_ops": [],
            "power_uses": [],
            "pending": []
        }, ensure_ascii=False)

        response = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "manual-web-turn-0001",
                "text": "Le pregunto por la senda.",
                "recipient_id": maelis["id"],
                "provider": "chatgpt_web",
                "visibility": "private",
                "external_response": pasted,
                "manual_context_hash": context_hash
            }
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["narration"].startswith("Maelis observa la senda")
        messages = client.get(f"/api/sessions/{session_id}/messages").json()
        assistant = next(message for message in messages if message["role"] == "assistant" and message["content"] == "Maelis observa la senda y responde que no está segura.")
        assert assistant["provider"] == "chatgpt_web"
        assert assistant["generation_status"] == "complete"


def test_manual_web_turn_rejects_non_json_response():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        prepared = client.post(
            f"/api/sessions/{session_id}/manual-prompt",
            json={
                "text": "Observo alrededor.",
                "provider": "gemini_web",
                "visibility": "scene"
            }
        )
        assert prepared.status_code == 200, prepared.text
        response = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "manual-web-invalid-0001",
                "text": "Observo alrededor.",
                "provider": "gemini_web",
                "external_response": "La respuesta es que ves una torre.",
                "manual_context_hash": prepared.json()["context_hash"]
            }
        )
        assert response.status_code == 502
        assert "JSON válido" in response.json()["detail"]
        messages = client.get(f"/api/sessions/{session_id}/messages").json()
        failed_user = next(message for message in messages if message["role"] == "user" and message["content"] == "Observo alrededor.")
        assert failed_user["generation_status"] == "failed"
        assert not any(message["role"] == "assistant" and message["turn_id"] == failed_user["turn_id"] for message in messages)



def test_manual_web_turn_rejects_stale_prepared_context():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        prepared = client.post(
            f"/api/sessions/{session_id}/manual-prompt",
            json={
                "text": "Observo alrededor con atención.",
                "provider": "chatgpt_web",
                "visibility": "scene"
            }
        )
        assert prepared.status_code == 200, prepared.text
        old_hash = prepared.json()["context_hash"]

        changed = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "change-state-before-manual-001",
                "text": "Observo la torre y describo su color.",
                "provider": "mock",
                "visibility": "scene"
            }
        )
        assert changed.status_code == 200, changed.text

        response = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "manual-stale-context-0001",
                "text": "Observo alrededor con atención.",
                "provider": "chatgpt_web",
                "visibility": "scene",
                "external_response": json.dumps({
                    "narration": "La torre parece cercana.",
                    "events": [],
                    "state_changes": [],
                    "elapsed_minutes": 1,
                    "movements": [],
                    "inventory_ops": [],
                    "resource_ops": [],
                    "power_uses": [],
                    "pending": []
                }),
                "manual_context_hash": old_hash
            }
        )
        assert response.status_code == 409
        assert "La partida cambió" in response.json()["detail"]
        messages = client.get(f"/api/sessions/{session_id}/messages").json()
        assert not any(m["role"] == "user" and m["content"] == "Observo alrededor con atención." for m in messages)


def test_manual_web_turn_can_retry_truncated_json_with_same_request_id():
    """A truncated pasted response must preserve game state and allow one clean retry."""
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        prepared = client.post(
            f"/api/sessions/{session_id}/manual-prompt",
            json={
                "text": "Observo el camino con cuidado.",
                "provider": "chatgpt_web",
                "visibility": "scene"
            }
        )
        assert prepared.status_code == 200, prepared.text
        initial_game_state = client.get(f"/api/sessions/{session_id}/state").json()["state"]
        with database.connection() as conn:
            initial_counts = {
                table: conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE session_id=?", (session_id,)
                ).fetchone()[0]
                for table in ("events", "state_changes", "inventory_items", "resources", "ability_uses")
            }
        common = {
            "request_id": "manual-web-truncated-retry-001",
            "text": "Observo el camino con cuidado.",
            "provider": "chatgpt_web",
            "visibility": "scene",
            "manual_context_hash": prepared.json()["context_hash"]
        }

        truncated = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                **common,
                "external_response": '{"narration":"El camino se abre hacia un arroyo'
            }
        )
        assert truncated.status_code == 502
        assert "JSON válido" in truncated.json()["detail"]
        assert client.get(f"/api/sessions/{session_id}/state").json()["state"] == initial_game_state
        messages_after_failure = client.get(f"/api/sessions/{session_id}/messages").json()
        failed_user = next(
            message for message in messages_after_failure
            if message["role"] == "user" and message["content"] == common["text"]
        )
        assert failed_user["generation_status"] == "failed"
        assert not any(
            message["role"] == "assistant" and message["turn_id"] == failed_user["turn_id"]
            for message in messages_after_failure
        )
        with database.connection() as conn:
            for table in ("events", "state_changes", "inventory_items", "resources", "ability_uses"):
                count = conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE session_id=?", (session_id,)
                ).fetchone()[0]
                # The malformed JSON must not create any game-state rows.
                assert count == initial_counts[table]

        corrected_json = json.dumps({
            "narration": "El camino desciende hacia un arroyo poco profundo.",
            "events": [],
            "state_changes": [],
            "elapsed_minutes": 1,
            "movements": [],
            "inventory_ops": [],
            "resource_ops": [],
            "power_uses": [],
            "pending": []
        }, ensure_ascii=False)
        recovered = client.post(
            f"/api/sessions/{session_id}/turns",
            json={**common, "external_response": corrected_json}
        )
        assert recovered.status_code == 200, recovered.text
        assert "arroyo poco profundo" in recovered.json()["narration"]

        messages_after_retry = client.get(f"/api/sessions/{session_id}/messages").json()
        user_messages = [
            message for message in messages_after_retry
            if message["role"] == "user" and message["content"] == common["text"]
        ]
        assistant_messages = [
            message for message in messages_after_retry
            if message["role"] == "assistant" and "arroyo poco profundo" in message["content"]
        ]
        assert len(user_messages) == 1
        assert user_messages[0]["generation_status"] == "complete"
        assert len(assistant_messages) == 1


def test_manual_web_mode_allows_multiple_consecutive_turns_without_api_calls():
    """Several copy/paste exchanges should work in one session without a local call quota."""
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        actions = [
            "Observo el camino.",
            "Me acerco al arroyo.",
            "Escucho si hay alguien cerca."
        ]

        for index, action in enumerate(actions, start=1):
            prepared = client.post(
                f"/api/sessions/{session_id}/manual-prompt",
                json={
                    "text": action,
                    "provider": "gemini_web",
                    "visibility": "scene"
                }
            )
            assert prepared.status_code == 200, prepared.text
            pasted_json = json.dumps({
                "narration": f"Respuesta manual número {index}.",
                "events": [],
                "state_changes": [],
                "elapsed_minutes": 1,
                "movements": [],
                "inventory_ops": [],
                "resource_ops": [],
                "power_uses": [],
                "pending": []
            }, ensure_ascii=False)
            response = client.post(
                f"/api/sessions/{session_id}/turns",
                json={
                    "request_id": f"manual-web-multi-{index:04d}",
                    "text": action,
                    "provider": "gemini_web",
                    "visibility": "scene",
                    "external_response": pasted_json,
                    "manual_context_hash": prepared.json()["context_hash"]
                }
            )
            assert response.status_code == 200, response.text
            assert response.json()["narration"] == f"Respuesta manual número {index}."

        messages = client.get(f"/api/sessions/{session_id}/messages").json()
        accepted = [
            message for message in messages
            if message["role"] == "assistant"
            and message["provider"] == "gemini_web"
            and message["generation_status"] == "complete"
            and message["content"].startswith("Respuesta manual número")
        ]
        assert len(accepted) == 3



def test_local_commands_work_without_creating_narrative_turns():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        before = client.get(f"/api/sessions/{session_id}/messages").json()

        state = client.post(
            f"/api/sessions/{session_id}/commands", json={"text": "/estado"}
        )
        inventory = client.post(
            f"/api/sessions/{session_id}/commands", json={"text": "/inventario"}
        )
        help_response = client.post(
            f"/api/sessions/{session_id}/commands", json={"text": "/ayuda"}
        )
        backup = client.post(
            f"/api/sessions/{session_id}/commands", json={"text": "/guardar"}
        )

        assert state.status_code == 200 and state.json()["command"] == "estado"
        assert state.json()["state"]["state"]["time_label"] == client.get(f"/api/sessions/{session_id}/state").json()["state"]["time_label"]
        assert inventory.status_code == 200 and inventory.json()["command"] == "inventario"
        assert "/salto" in " ".join(help_response.json()["help"])
        assert backup.status_code == 200 and Path(backup.json()["path"]).exists()
        after = client.get(f"/api/sessions/{session_id}/messages").json()
        assert len(after) == len(before)


def test_typo_of_reserved_local_command_is_rejected_without_creating_a_turn():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        before = client.get(f"/api/sessions/{session_id}/messages").json()
        response = client.post(
            f"/api/sessions/{session_id}/turns",
            json={"request_id": "unknown-command-001", "text": "/estdao", "provider": "mock"}
        )
        assert response.status_code == 422
        assert "error tipográfico" in response.json()["detail"]
        after = client.get(f"/api/sessions/{session_id}/messages").json()
        assert after == before


def test_skip_command_accepts_days_and_rejects_malformed_units():
    assert main_module.parse_skip("/salto 1 día") == {"minutes": 1440, "destination": ""}
    assert main_module.parse_skip("/salto 2 dias -> Aldea") == {"minutes": 2880, "destination": "Aldea"}
    assert main_module.parse_skip("/salto 30 minutos") == {"minutes": 30, "destination": ""}
    from fastapi import HTTPException
    import pytest

    with pytest.raises(HTTPException) as error:
        main_module.parse_skip("/salto 1 semana")
    assert error.value.status_code == 422
    assert "Formato de salto incorrecto" in error.value.detail


def test_context_recovers_relevant_old_event_beyond_the_recent_window():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        with database.transaction() as conn:
            session = session_row(conn, session_id)
            protagonist_id = session["protagonist_entity_id"]
            conn.execute(
                "INSERT INTO events(id,session_id,turn_id,external_ref,kind,entity_id,description,witnesses_json,status,created_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,?)",
                (uuid.uuid4().hex, session_id, "old-relevant-turn", "old-medallion", "object", protagonist_id,
                 "El medallón de obsidiana quedó enterrado bajo la torre del norte.", json.dumps([protagonist_id]), "recorded", "2020-01-01 00:00:00")
            )
            for index in range(18):
                conn.execute(
                    "INSERT INTO events(id,session_id,turn_id,external_ref,kind,entity_id,description,witnesses_json,status,created_at) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (uuid.uuid4().hex, session_id, f"noise-turn-{index}", f"noise-{index}", "observation", protagonist_id,
                     f"Un detalle cotidiano irrelevante número {index} ocurrió en la plaza.", json.dumps([protagonist_id]), "recorded",
                     f"2026-10-{(index % 20) + 1:02d} 12:00:00")
                )
            context = build_context(
                conn, session, "Busco el medallón de obsidiana.", "", uuid.uuid4().hex,
                visibility="scene", include_diagnostics=True
            )
        descriptions = [event["description"] for event in context["recent_events"]]
        assert any("medallón de obsidiana" in description for description in descriptions)
        diagnostics = context["_diagnostics"]
        assert diagnostics["events_recovered_by_relevance"] >= 1


def test_context_fails_closed_when_old_message_audience_metadata_is_corrupt():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        world_id = seed["world_id"]
        entities = client.get(f"/api/worlds/{world_id}/entities").json()
        maelis = next(entity for entity in entities if entity["name"] == "Maelis Orven")
        with database.transaction() as conn:
            conn.execute(
                "INSERT INTO messages(id,session_id,turn_id,client_request_id,turn_index,role,recipient_entity_id,content,provider,generation_status,metadata_json) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (uuid.uuid4().hex, session_id, "corrupt-private-turn", "corrupt-private-001", 99,
                 "user", maelis["id"], "El secreto es la llave azul.", "mock", "complete", "not-json")
            )
            session = session_row(conn, session_id)
            context = build_context(
                conn, session, "Pregunto por la llave azul.", maelis["id"], uuid.uuid4().hex,
                visibility="private", audience_ids=[session["protagonist_entity_id"], maelis["id"]],
                include_diagnostics=True
            )
        assert all("secreto es la llave azul" not in message["content"] for message in context["recent_messages"])
        assert any("metadatos dañados" in item["reason"] for item in context["_diagnostics"]["excluded_messages"])



def test_new_turn_is_rejected_while_another_turn_is_processing():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        with database.transaction() as conn:
            conn.execute(
                "INSERT INTO messages(id,session_id,turn_id,client_request_id,turn_index,role,recipient_entity_id,content,provider,generation_status,metadata_json) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (uuid.uuid4().hex, session_id, "active-turn-test", "active-turn-request-001",
                 999, "user", "", "Observa la puerta.", "mock", "processing",
                 json.dumps({"visibility":"scene","audience_ids":[]}))
            )
        before = client.get(f"/api/sessions/{session_id}/messages").json()
        response = client.post(
            f"/api/sessions/{session_id}/turns",
            json={"request_id":"overlap-turn-request-001","text":"Sigo por el camino.","provider":"mock"}
        )
        assert response.status_code == 409
        assert "otro turno en curso" in response.json()["detail"]
        assert client.get(f"/api/sessions/{session_id}/messages").json() == before



def test_multiprocess_owner_death_recovers_turn_without_duplicate_effects(monkeypatch):
    """A real child process leaves a processing marker, dies, and can be safely retried."""
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        before = client.get(f"/api/sessions/{session_id}/state").json()
        request_id = "multiprocess-owner-death-001"
        text_value = "Reanudo la marcha después de una interrupción."
        turn_id = "multiprocess-orphan-" + uuid.uuid4().hex

        # A separate OS process owns the durable processing marker. It stays alive
        # long enough for the parent to observe it, then is forcibly terminated.
        child_script = r"""
import json, os, sqlite3, sys, time, uuid
db_path, session_id, request_id, turn_id, message_text, snapshot_state_json = sys.argv[1:]
conn = sqlite3.connect(db_path, timeout=10)
conn.execute("PRAGMA foreign_keys=ON")
turn_index = conn.execute(
    "SELECT COALESCE(MAX(turn_index),0)+1 FROM messages WHERE session_id=?",
    (session_id,)
).fetchone()[0]
metadata = json.dumps({
    "visibility": "scene",
    "audience_ids": [],
    "processing_owner_pid": os.getpid()
})
conn.execute(
    "INSERT INTO messages(id,session_id,turn_id,client_request_id,turn_index,role,"
    "recipient_entity_id,content,provider,generation_status,metadata_json) "
    "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
    (uuid.uuid4().hex, session_id, turn_id, request_id, turn_index, "user", "",
     message_text, "mock", "processing", metadata)
)
# Mirror the pre-turn snapshot that the application writes before calling a provider.
conn.execute(
    "INSERT INTO snapshots(id,session_id,turn_id,event_sequence,state_json) VALUES(?,?,?,?,?)",
    (uuid.uuid4().hex, session_id, turn_id, turn_index, snapshot_state_json)
)
conn.commit()
print(os.getpid(), flush=True)
time.sleep(60)
"""
        with database.connection() as conn:
            snapshot_state_json = json.dumps(
                main_module.capture_turn_state(conn, session_id), ensure_ascii=False
            )
        owner = subprocess.Popen(
            [
                sys.executable, "-c", child_script, str(database.path), session_id,
                request_id, turn_id, text_value, snapshot_state_json
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        try:
            owner_pid_line = owner.stdout.readline()
            assert owner_pid_line.strip(), "El proceso hijo no confirmó el marcador processing."
            assert int(owner_pid_line.strip()) == owner.pid
            with database.connection() as conn:
                marker = conn.execute(
                    "SELECT generation_status,metadata_json FROM messages "
                    "WHERE session_id=? AND client_request_id=?",
                    (session_id, request_id)
                ).fetchone()
            assert marker is not None
            assert marker["generation_status"] == "processing"
            assert json.loads(marker["metadata_json"])["processing_owner_pid"] == owner.pid
        finally:
            owner.kill()
            owner.wait(timeout=10)

        # The owner is now truly dead. Recovery must fail the abandoned turn,
        # preserve its original user message, and apply no world effects.
        assert main_module.recover_interrupted_turns() == 1
        messages = client.get(f"/api/sessions/{session_id}/messages").json()
        recovered = next(m for m in messages if m["client_request_id"] == request_id)
        assert recovered["generation_status"] == "failed"
        recovered_metadata = json.loads(recovered["metadata_json"])
        assert recovered_metadata["recovered_after_restart"] is True
        assert client.get(f"/api/sessions/{session_id}/state").json() == before

        provider_calls = []

        class RetryProvider:
            name = "mock"

            async def generate(self, payload):
                provider_calls.append(payload["user_message"])
                return NarratorResponse(
                    narration="La acción se recuperó una sola vez.",
                    elapsed_minutes=1
                )

        monkeypatch.setattr(
            main_module, "make_provider",
            lambda provider_name, settings: RetryProvider()
        )
        retry = client.post(
            f"/api/sessions/{session_id}/turns",
            json={"request_id": request_id, "text": text_value, "provider": "mock"}
        )
        assert retry.status_code == 200, retry.text
        assert retry.json()["turn_id"] == turn_id
        assert retry.json()["replayed"] is False
        assert len(provider_calls) == 1

        final_messages = client.get(f"/api/sessions/{session_id}/messages").json()
        user_rows = [
            m for m in final_messages
            if m["role"] == "user" and m["client_request_id"] == request_id
        ]
        assistant_rows = [
            m for m in final_messages
            if m["role"] == "assistant" and m["turn_id"] == turn_id
            and m["generation_status"] == "complete"
        ]
        assert len(user_rows) == 1
        assert len(assistant_rows) == 1
        final_state = client.get(f"/api/sessions/{session_id}/state").json()
        assert final_state["state"]["minute_of_day"] == before["state"]["minute_of_day"] + 1
        assert main_module.recover_interrupted_turns() == 0


def test_concurrent_session_requests_stay_serial_across_two_app_clients(monkeypatch):
    """A second app client must not recover or overlap a generation owned by the first."""
    entered_provider = threading.Event()
    release_provider = threading.Event()
    provider_calls = []

    class SlowProvider:
        name = "mock"

        async def generate(self, payload):
            provider_calls.append(payload["user_message"])
            entered_provider.set()
            released = await asyncio.to_thread(release_provider.wait, 10)
            if not released:
                raise RuntimeError("La prueba no liberó el proveedor lento a tiempo.")
            return NarratorResponse(
                narration="La acción se resolvió una sola vez.",
                elapsed_minutes=1
            )

    monkeypatch.setattr(main_module, "make_provider", lambda name, settings: SlowProvider())

    with TestClient(app) as first_client:
        seed = first_client.post("/api/demo/seed", json={})
        assert seed.status_code == 200, seed.text
        session_id = seed.json()["session_id"]
        before = first_client.get(f"/api/sessions/{session_id}/state").json()

        first_payload = {
            "request_id": "concurrent-request-first-001",
            "text": "Observo el camino mientras espero.",
            "provider": "mock"
        }
        second_payload = {
            "request_id": "concurrent-request-second-001",
            "text": "Intento avanzar antes de que termine.",
            "provider": "mock"
        }

        with ThreadPoolExecutor(max_workers=1) as executor:
            first_future = executor.submit(
                first_client.post, f"/api/sessions/{session_id}/turns",
                json=first_payload
            )
            assert entered_provider.wait(5), "La primera solicitud no llegó al proveedor."

            # Starting a second app client runs startup recovery while the first
            # request is still in the provider. It must preserve the live marker.
            with TestClient(app) as second_client:
                with database.connection() as conn:
                    marker = conn.execute(
                        "SELECT generation_status,metadata_json FROM messages "
                        "WHERE session_id=? AND role='user' AND client_request_id=?",
                        (session_id, first_payload["request_id"])
                    ).fetchone()
                assert marker is not None
                assert marker["generation_status"] == "processing"
                assert json.loads(marker["metadata_json"])["processing_owner_pid"] == os.getpid()

                competing = second_client.post(
                    f"/api/sessions/{session_id}/turns", json=second_payload
                )
                assert competing.status_code == 409, competing.text
                assert "otro turno en curso" in competing.json()["detail"]
                assert len(provider_calls) == 1

            release_provider.set()
            first_response = first_future.result(timeout=10)
            assert first_response.status_code == 200, first_response.text

        # The rejected overlapping request created no message and can be submitted
        # after the first turn commits; each turn advances the clock exactly once.
        second_response = first_client.post(
            f"/api/sessions/{session_id}/turns", json=second_payload
        )
        assert second_response.status_code == 200, second_response.text
        assert len(provider_calls) == 2

        final_state = first_client.get(f"/api/sessions/{session_id}/state").json()
        assert final_state["state"]["minute_of_day"] == before["state"]["minute_of_day"] + 2
        messages = first_client.get(f"/api/sessions/{session_id}/messages").json()
        users = [m for m in messages if m["role"] == "user"]
        assistants = [m for m in messages if m["role"] == "assistant" and m["generation_status"] == "complete"]
        assert len(users) == 2
        assert len(assistants) == 2
        assert [m["content"] for m in users].count(first_payload["text"]) == 1
        assert [m["content"] for m in users].count(second_payload["text"]) == 1

def test_backup_rejects_in_flight_turn_and_keeps_no_partial_file():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        with database.transaction() as conn:
            conn.execute(
                "INSERT INTO messages(id,session_id,turn_id,client_request_id,turn_index,role,recipient_entity_id,content,provider,generation_status,metadata_json) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (uuid.uuid4().hex, session_id, "active-backup-test", "active-backup-request-001",
                 999, "user", "", "Observa la puerta.", "mock", "processing",
                 json.dumps({"visibility":"scene","audience_ids":[]}))
            )
        response = client.post(f"/api/sessions/{session_id}/backup")
        assert response.status_code == 409
        assert "turno en curso" in response.json()["detail"]
        backup_dir = database.path.parent / "backups"
        assert not list(backup_dir.glob(f"backup-{session_id}-*.sqlite3")) if backup_dir.exists() else True


def test_backup_is_a_complete_readable_sqlite_database():
    import sqlite3

    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        response = client.post(f"/api/sessions/{session_id}/backup")
        assert response.status_code == 200, response.text
        backup_path = Path(response.json()["path"])
        assert backup_path.exists()
        assert not backup_path.with_name(backup_path.name + ".tmp").exists()
        with sqlite3.connect(str(backup_path)) as conn:
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert conn.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone() is not None



def test_multi_day_skip_updates_clock_and_location_without_applying_model_side_effects():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        before_state = client.get(f"/api/sessions/{session_id}/state").json()
        before_inventory = before_state["inventory"]
        with database.connection() as conn:
            session = session_row(conn, session_id)
            protagonist_id = session["protagonist_entity_id"]
            before_events = [dict(row) for row in conn.execute(
                "SELECT id,turn_id,external_ref,kind,entity_id,description,status "
                "FROM events WHERE session_id=? ORDER BY id", (session_id,)
            ).fetchall()]
        prompt = client.post(
            f"/api/sessions/{session_id}/manual-prompt",
            json={
                "text": "/salto 2 días -> Aldea",
                "provider": "chatgpt_web",
                "visibility": "scene"
            }
        )
        assert prompt.status_code == 200, prompt.text

        external = json.dumps({
            "narration": "Transcurren dos días y llegas a la Aldea indicada.",
            "events": [{
                "ref": "e1", "kind": "object", "entity_id": protagonist_id,
                "description": "Encuentra una espada legendaria durante el viaje.",
                "witness_ids": [protagonist_id]
            }],
            "state_changes": [{
                "ref": "c1", "entity_id": protagonist_id, "field": "friendship",
                "operation": "delta", "numeric_value": 3, "text_value": "",
                "reason": "La amistad aumentó durante el viaje.", "event_ref": "e1",
                "requires_approval": False
            }],
            "elapsed_minutes": 2880,
            "movements": [{
                "entity_id": protagonist_id, "destination": "Torre",
                "reason": "Viaja a otra ubicación.", "event_ref": "e1"
            }],
            "inventory_ops": [{
                "operation": "acquire", "item_name": "Espada legendaria",
                "quantity": 1, "condition": "normal",
                "carrier_entity_id": protagonist_id, "location": "Aldea",
                "reason": "Hallazgo durante el salto.", "event_ref": "e1",
                "cost": 0, "currency_key": "monedas"
            }],
            "resource_ops": [],
            "power_uses": [],
            "pending": []
        }, ensure_ascii=False)
        response = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "manual-day-skip-test-001",
                "text": "/salto 2 días -> Aldea",
                "provider": "chatgpt_web",
                "visibility": "scene",
                "external_response": external,
                "manual_context_hash": prompt.json()["context_hash"]
            }
        )
        assert response.status_code == 200, response.text
        after_state = client.get(f"/api/sessions/{session_id}/state").json()

        assert after_state["state"]["day"] == before_state["state"]["day"] + 2
        assert after_state["state"]["minute_of_day"] == before_state["state"]["minute_of_day"]
        assert after_state["state"]["location"] == "Aldea"
        assert after_state["inventory"] == before_inventory
        with database.connection() as conn:
            after_events = [dict(row) for row in conn.execute(
                "SELECT id,turn_id,external_ref,kind,entity_id,description,status "
                "FROM events WHERE session_id=? ORDER BY id", (session_id,)
            ).fetchall()]
        assert after_events == before_events
        assert any("no aplicó" in note for note in response.json()["pending_notes"])

        with database.connection() as conn:
            presence = conn.execute(
                "SELECT location,presence_status FROM session_presence WHERE session_id=? AND entity_id=?",
                (session_id, protagonist_id)
            ).fetchone()
        assert presence["location"] == "Aldea"
        assert presence["presence_status"] == "present"


def test_duplicate_state_change_refs_are_quarantined_and_do_not_block_the_session():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        world_id, session_id = seed["world_id"], seed["session_id"]
        entities = client.get(f"/api/worlds/{world_id}/entities").json()
        protagonist = next(entity for entity in entities if entity["kind"] == "protagonist")
        maelis = next(entity for entity in entities if entity["name"] == "Maelis Orven")
        text = "Le pregunto a Maelis cómo se encuentra."
        prepared = client.post(
            f"/api/sessions/{session_id}/manual-prompt",
            json={
                "text": text, "recipient_id": maelis["id"],
                "provider": "chatgpt_web", "visibility": "private"
            }
        )
        assert prepared.status_code == 200, prepared.text
        duplicate_change = {
            "ref": "change-duplicate-1",
            "entity_id": maelis["id"],
            "field": "friendship",
            "operation": "delta",
            "numeric_value": 2,
            "text_value": "",
            "reason": "Maelis responde de manera cordial.",
            "event_ref": "event-dialogue-1",
            "requires_approval": False
        }
        external = json.dumps({
            "narration": "Maelis te escucha y responde con cautela.",
            "events": [{
                "ref": "event-dialogue-1", "kind": "dialogue",
                "entity_id": maelis["id"],
                "description": "Maelis escucha la pregunta del protagonista.",
                "witness_ids": [protagonist["id"], maelis["id"]]
            }],
            "state_changes": [duplicate_change, {**duplicate_change, "numeric_value": 3}],
            "elapsed_minutes": 1,
            "movements": [], "inventory_ops": [], "resource_ops": [],
            "power_uses": [], "pending": []
        }, ensure_ascii=False)
        request = {
            "request_id": "duplicate-state-ref-0001",
            "text": text, "recipient_id": maelis["id"],
            "provider": "chatgpt_web", "visibility": "private",
            "external_response": external,
            "manual_context_hash": prepared.json()["context_hash"]
        }
        response = client.post(f"/api/sessions/{session_id}/turns", json=request)
        assert response.status_code == 200, response.text
        assert any("se repite en la respuesta" in note for note in response.json()["pending_notes"])

        changes = client.get(f"/api/sessions/{session_id}/state").json()["pending_changes"]
        duplicate_audits = [change for change in changes if change["field"] == "friendship"]
        assert len(duplicate_audits) == 1
        assert "referencia" in duplicate_audits[0]["reason"].lower()

        # The invalid proposal must not leave a stale processing row that locks the session.
        follow_up = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "after-duplicate-ref-0001",
                "text": "Observo el camino.",
                "provider": "mock",
                "visibility": "scene"
            }
        )
        assert follow_up.status_code == 200, follow_up.text


def test_duplicate_inventory_and_resource_operations_never_apply_twice():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        world_id, session_id = seed["world_id"], seed["session_id"]
        entities = client.get(f"/api/worlds/{world_id}/entities").json()
        protagonist = next(entity for entity in entities if entity["kind"] == "protagonist")
        text = "Recibo una recompensa y encuentro pan en una cesta."
        prepared = client.post(
            f"/api/sessions/{session_id}/manual-prompt",
            json={"text": text, "provider": "gemini_web", "visibility": "scene"}
        )
        assert prepared.status_code == 200, prepared.text
        duplicate_resource = {
            "operation": "gain", "resource_key": "monedas",
            "display_name": "Monedas", "quantity": 5, "unit": "monedas",
            "reason": "Recompensa recibida.", "event_ref": "resource-event-1"
        }
        duplicate_item = {
            "operation": "acquire", "item_name": "pan", "quantity": 2,
            "condition": "normal", "carrier_entity_id": protagonist["id"],
            "location": "Claro en el Bosque de las Bestias",
            "reason": "Hallazgo recogido.", "event_ref": "object-event-1",
            "cost": 0, "currency_key": "monedas"
        }
        external = json.dumps({
            "narration": "Encuentras pan en una cesta y alguien anuncia una recompensa.",
            "events": [
                {
                    "ref": "resource-event-1", "kind": "resource",
                    "entity_id": protagonist["id"],
                    "description": "El protagonista recibe monedas como recompensa.",
                    "witness_ids": [protagonist["id"]]
                },
                {
                    "ref": "object-event-1", "kind": "object",
                    "entity_id": protagonist["id"],
                    "description": "El protagonista encuentra pan en una cesta.",
                    "witness_ids": [protagonist["id"]]
                }
            ],
            "state_changes": [], "elapsed_minutes": 1, "movements": [],
            "inventory_ops": [duplicate_item, duplicate_item],
            "resource_ops": [duplicate_resource, duplicate_resource],
            "power_uses": [], "pending": []
        }, ensure_ascii=False)
        response = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "duplicate-operations-0001",
                "text": text, "provider": "gemini_web", "visibility": "scene",
                "external_response": external,
                "manual_context_hash": prepared.json()["context_hash"]
            }
        )
        assert response.status_code == 200, response.text
        state = client.get(f"/api/sessions/{session_id}/state").json()
        assert not any(item["display_name"].casefold() == "pan" for item in state["inventory"])
        assert not any(resource["resource_key"] == "monedas" for resource in state["resources"])
        assert any("Inventario: acquire pan" in note and "varias veces" in note for note in response.json()["pending_notes"])
        assert any("Recurso: gain Monedas" in note and "varias veces" in note for note in response.json()["pending_notes"])


def test_unexpected_state_application_failure_marks_turn_failed_and_allows_same_request_retry(monkeypatch):
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        payload = {
            "request_id": "apply-failure-recovery-001",
            "text": "Observo el sendero.",
            "provider": "mock",
            "visibility": "scene"
        }
        original_apply = main_module.apply_narrator_result

        def fail_once(*args, **kwargs):
            raise RuntimeError("injected test failure during atomic application")

        monkeypatch.setattr(main_module, "apply_narrator_result", fail_once)
        failed = client.post(f"/api/sessions/{session_id}/turns", json=payload)
        assert failed.status_code == 502
        assert "No se aplicaron cambios" in failed.json()["detail"]

        messages = client.get(f"/api/sessions/{session_id}/messages").json()
        failed_user = next(
            message for message in messages
            if message["role"] == "user" and message["content"] == payload["text"]
        )
        assert failed_user["generation_status"] == "failed"

        monkeypatch.setattr(main_module, "apply_narrator_result", original_apply)
        recovered = client.post(f"/api/sessions/{session_id}/turns", json=payload)
        assert recovered.status_code == 200, recovered.text
        assert recovered.json()["turn_id"] == failed_user["turn_id"]

        messages_after = client.get(f"/api/sessions/{session_id}/messages").json()
        assert len([m for m in messages_after if m["role"] == "user" and m["content"] == payload["text"]]) == 1
        assert len([m for m in messages_after if m["role"] == "assistant" and m["turn_id"] == failed_user["turn_id"]]) == 1


def test_history_retrieval_matches_common_spanish_plural_and_verb_forms():
    old_fact = relevance_terms("Las llaves antiguas quedaron junto al cofre; recogí una bolsa.")
    current_action = relevance_terms("Busco la llave antigua y quiero recoger la bolsa.")
    assert {"llave", "antigua", "recog"}.issubset(old_fact & current_action)


def test_100_short_turns_persist_and_restore_exact_state_after_database_reinitialization():
    import sqlite3

    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        short_actions = ["Sí.", "No.", "Sigo.", "Miro alrededor.", "Escucho con atención."]

        for index in range(100):
            response = client.post(
                f"/api/sessions/{session_id}/turns",
                json={
                    "request_id": f"campaign-100-{index:03d}-request",
                    "text": short_actions[index % len(short_actions)],
                    "provider": "mock",
                    "visibility": "scene"
                }
            )
            assert response.status_code == 200, f"Turno {index + 1}: {response.text}"

        before_state = client.get(f"/api/sessions/{session_id}/state").json()
        before_messages = client.get(f"/api/sessions/{session_id}/messages").json()
        assert len(before_messages) == 200
        assert len([message for message in before_messages if message["role"] == "user"]) == 100
        assert len([
            message for message in before_messages
            if message["role"] == "assistant" and message["generation_status"] == "complete"
        ]) == 100
        assert before_state["state"]["minute_of_day"] == 580

        with database.connection() as conn:
            event_count = conn.execute(
                "SELECT COUNT(*) FROM events WHERE session_id=?", (session_id,)
            ).fetchone()[0]
            before_tables = {
                table: [
                    dict(row) for row in conn.execute(
                        f"SELECT * FROM {table} WHERE session_id=? ORDER BY rowid", (session_id,)
                    ).fetchall()
                ]
                for table in main_module.RESTORE_SESSION_TABLES
            }
        assert event_count == 100

        # Reinitialization simulates application restart; no state may live only in process memory.
        database.initialize()
        assert client.get(f"/api/sessions/{session_id}/state").json() == before_state
        assert client.get(f"/api/sessions/{session_id}/messages").json() == before_messages

        backup = client.post(f"/api/sessions/{session_id}/backup", json={})
        assert backup.status_code == 200, backup.text
        backup_data = backup.json()
        backup_name = backup_data["backup_name"]
        with sqlite3.connect(backup_data["path"]) as conn:
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert conn.execute(
                "SELECT COUNT(*) FROM messages WHERE session_id=?", (session_id,)
            ).fetchone()[0] == 200
            assert conn.execute(
                "SELECT COUNT(*) FROM events WHERE session_id=?", (session_id,)
            ).fetchone()[0] == 100

        # Introduce one real post-backup mutation so restore must undo it.
        later_turn = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "campaign-100-post-backup-mutation",
                "text": "Sigo.",
                "provider": "mock",
                "visibility": "scene"
            }
        )
        assert later_turn.status_code == 200, later_turn.text
        assert client.get(f"/api/sessions/{session_id}/messages").json() != before_messages

        restored = client.post(
            f"/api/sessions/{session_id}/restore",
            json={"backup_name": backup_name, "confirmation": "RESTAURAR"}
        )
        assert restored.status_code == 200, restored.text
        assert client.get(f"/api/sessions/{session_id}/state").json() == before_state
        assert client.get(f"/api/sessions/{session_id}/messages").json() == before_messages
        with database.connection() as conn:
            restored_tables = {
                table: [
                    dict(row) for row in conn.execute(
                        f"SELECT * FROM {table} WHERE session_id=? ORDER BY rowid", (session_id,)
                    ).fetchall()
                ]
                for table in main_module.RESTORE_SESSION_TABLES
            }
        assert restored_tables == before_tables



def test_mixed_50_turn_continuity_campaign_with_retries_privacy_and_restore(monkeypatch):
    """Deterministic mixed campaign; real ChatGPT/Gemini web remains a separate manual trial."""
    import sqlite3

    with TestClient(app) as client:
        started, entities = _create_state_ops_world(client)
        session_id = started["session_id"]
        protagonist_id = entities["Protagonista"]["id"]
        maelis_id = entities["Maelis Orven"]["id"]
        ivar_id = entities["Ivar Dalen"]["id"]
        secret = "SECRETO-CAMPANA-09"

        # Give the deterministic campaign enough currency to exercise several paid buys.
        with database.transaction() as conn:
            conn.execute(
                "UPDATE resources SET quantity=100 WHERE session_id=? AND resource_key='monedas'",
                (session_id,)
            )

        class CampaignProvider:
            name = "mock"

            async def generate(self, payload):
                text = payload["user_message"]
                audience = list(payload["context"]["audience_ids"])
                match = re.search(r"CAMPAIGN (\d+)", text)
                index = int(match.group(1)) if match else 0
                if "Compro una manzana" in text:
                    ref = f"campaign-purchase-{index}"
                    return NarratorResponse(
                        narration=f"Compra registrada en el turno {index}.",
                        events=[EventProposal(
                            ref=ref, kind="object", entity_id=protagonist_id,
                            description="El protagonista compra una manzana por dos monedas y la recibe.",
                            witness_ids=audience
                        )],
                        inventory_ops=[InventoryOperation(
                            operation="acquire", item_name="Manzana", quantity=1,
                            carrier_entity_id=protagonist_id, location="Claro del bosque",
                            reason="Compra explícita de la campaña.", event_ref=ref,
                            cost=2, currency_key="monedas"
                        )]
                    )
                if "Recojo una piedra" in text:
                    ref = f"campaign-pickup-{index}"
                    return NarratorResponse(
                        narration=f"Hallazgo registrado en el turno {index}.",
                        events=[EventProposal(
                            ref=ref, kind="object", entity_id=protagonist_id,
                            description="El protagonista recoge una piedra común del suelo.",
                            witness_ids=audience
                        )],
                        inventory_ops=[InventoryOperation(
                            operation="acquire", item_name="Piedra", quantity=1,
                            carrier_entity_id=protagonist_id, location="Claro del bosque",
                            reason="Recogida explícita de la campaña.", event_ref=ref,
                            cost=0, currency_key="monedas"
                        )]
                    )
                return NarratorResponse(
                    narration=f"La escena continúa de forma controlada en el turno {index}.",
                    elapsed_minutes=1
                )

        original_factory = main_module.make_provider
        monkeypatch.setattr(
            main_module, "make_provider",
            lambda name, settings: CampaignProvider() if name == "mock" else original_factory(name, settings)
        )

        def read_session_tables():
            with database.connection() as conn:
                return {
                    table: [
                        dict(row) for row in conn.execute(
                            f"SELECT * FROM {table} WHERE session_id=? ORDER BY rowid",
                            (session_id,)
                        ).fetchall()
                    ]
                    for table in main_module.RESTORE_SESSION_TABLES
                }

        def submit_campaign_turn(index):
            request_id = f"mixed-campaign-turn-{index:03d}"
            if index == 15:
                text = "/salto 1 minuto -> Posada"
                visibility, recipient_id = "scene", ""
            elif index == 16:
                text = "/salto 1 minuto -> Claro del bosque"
                visibility, recipient_id = "scene", ""
            elif index % 10 == 0:
                text = f"CAMPAIGN {index:02d}: Compro una manzana por dos monedas."
                visibility, recipient_id = "scene", ""
            elif index % 7 == 0:
                text = f"CAMPAIGN {index:02d}: Recojo una piedra."
                visibility, recipient_id = "scene", ""
            elif index % 9 == 0:
                text = f"CAMPAIGN {index:02d}: Esto es confidencial: {secret}."
                visibility, recipient_id = "private", maelis_id
            else:
                text = f"CAMPAIGN {index:02d}: Observo el entorno y continúo."
                visibility, recipient_id = "scene", ""

            if index == 24:
                prepared = client.post(
                    f"/api/sessions/{session_id}/manual-prompt",
                    json={"text": text, "provider": "gemini_web", "visibility": visibility}
                )
                assert prepared.status_code == 200, prepared.text
                before_state = client.get(f"/api/sessions/{session_id}/state").json()
                before_effect_tables = {
                    table: rows for table, rows in read_session_tables().items()
                    if table not in {"messages", "snapshots"}
                }
                common = {
                    "request_id": request_id, "text": text, "provider": "gemini_web",
                    "visibility": visibility, "recipient_id": recipient_id,
                    "manual_context_hash": prepared.json()["context_hash"]
                }
                truncated = client.post(
                    f"/api/sessions/{session_id}/turns",
                    json={**common, "external_response": '{"narration":"respuesta truncada'}
                )
                assert truncated.status_code == 502, truncated.text
                assert client.get(f"/api/sessions/{session_id}/state").json() == before_state
                after_effect_tables = {
                    table: rows for table, rows in read_session_tables().items()
                    if table not in {"messages", "snapshots"}
                }
                assert after_effect_tables == before_effect_tables
                corrected = json.dumps({
                    "narration": "Respuesta corregida tras el JSON truncado.",
                    "events": [], "state_changes": [], "elapsed_minutes": 1,
                    "movements": [], "inventory_ops": [], "resource_ops": [],
                    "power_uses": [], "pending": []
                }, ensure_ascii=False)
                retried = client.post(
                    f"/api/sessions/{session_id}/turns",
                    json={**common, "external_response": corrected}
                )
                assert retried.status_code == 200, retried.text
                return retried.json()

            if index == 25:
                # Simulate a process that died after persisting the request marker.
                turn_id = "campaign-interrupted-" + uuid.uuid4().hex
                before_state = client.get(f"/api/sessions/{session_id}/state").json()
                with database.transaction() as conn:
                    turn_index = int(conn.execute(
                        "SELECT COALESCE(MAX(turn_index),0)+1 AS n FROM messages WHERE session_id=?",
                        (session_id,)
                    ).fetchone()["n"])
                    audience = [
                        row["entity_id"] for row in conn.execute(
                            "SELECT entity_id FROM session_presence WHERE session_id=? AND location=("
                            "SELECT current_location FROM sessions WHERE id=?)",
                            (session_id, session_id)
                        ).fetchall()
                    ]
                    conn.execute(
                        "INSERT INTO messages(id,session_id,turn_id,client_request_id,turn_index,role,"
                        "recipient_entity_id,content,provider,generation_status,metadata_json) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            uuid.uuid4().hex, session_id, turn_id, request_id, turn_index,
                            "user", "", text, "mock", "processing",
                            json.dumps({
                                "visibility": "scene", "audience_ids": audience,
                                "processing_owner_pid": 2**31 - 1
                            })
                        )
                    )
                    main_module.create_turn_snapshot(conn, session_id, turn_id, turn_index)
                assert main_module.recover_interrupted_turns() == 1
                assert client.get(f"/api/sessions/{session_id}/state").json() == before_state
                retried = client.post(
                    f"/api/sessions/{session_id}/turns",
                    json={"request_id": request_id, "text": text, "provider": "mock", "visibility": visibility}
                )
                assert retried.status_code == 200, retried.text
                return retried.json()

            response = client.post(
                f"/api/sessions/{session_id}/turns",
                json={
                    "request_id": request_id, "text": text, "provider": "mock",
                    "visibility": visibility, "recipient_id": recipient_id
                }
            )
            assert response.status_code == 200, f"Turno {index}: {response.text}"

            if index == 9:
                # The private fact must be visible to Maelis but not to Ivar in the same scene.
                with database.connection() as conn:
                    session = session_row(conn, session_id)
                    scene_ids = [
                        row["entity_id"] for row in conn.execute(
                            "SELECT entity_id FROM session_presence WHERE session_id=? AND location=?",
                            (session_id, session["current_location"])
                        ).fetchall()
                    ]
                    ivar_context = build_context(
                        conn, session, "¿Qué secreto conoce Ivar?", ivar_id,
                        "campaign-privacy-ivar", visibility="scene", audience_ids=scene_ids
                    )
                    maelis_context = build_context(
                        conn, session, "¿Qué secreto conoce Maelis?", maelis_id,
                        "campaign-privacy-maelis", visibility="private",
                        audience_ids=[protagonist_id, maelis_id]
                    )
                assert secret not in json.dumps(ivar_context, ensure_ascii=False)
                assert secret in json.dumps(maelis_context, ensure_ascii=False)
            return response.json()

        for index in range(1, 26):
            submit_campaign_turn(index)

        # Save the full persisted state at the midpoint.
        before_restore_state = client.get(f"/api/sessions/{session_id}/state").json()
        before_restore_messages = client.get(f"/api/sessions/{session_id}/messages").json()
        before_restore_tables = read_session_tables()
        backup = client.post(f"/api/sessions/{session_id}/backup", json={})
        assert backup.status_code == 200, backup.text
        backup_path = Path(backup.json()["path"])
        with sqlite3.connect(backup_path) as conn:
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

        # Add mutations after the backup, then prove restore returns byte-for-byte-equivalent rows.
        for index in (26, 27, 28):
            submit_campaign_turn(index)
        restored = client.post(
            f"/api/sessions/{session_id}/restore",
            json={"backup_name": backup.json()["backup_name"], "confirmation": "RESTAURAR"}
        )
        assert restored.status_code == 200, restored.text
        assert client.get(f"/api/sessions/{session_id}/state").json() == before_restore_state
        assert client.get(f"/api/sessions/{session_id}/messages").json() == before_restore_messages
        assert read_session_tables() == before_restore_tables

        for index in range(26, 51):
            submit_campaign_turn(index)

        final_state = client.get(f"/api/sessions/{session_id}/state").json()
        final_messages = client.get(f"/api/sessions/{session_id}/messages").json()
        assert len([m for m in final_messages if m["role"] == "user"]) == 50
        assert len([
            m for m in final_messages
            if m["role"] == "assistant" and m["generation_status"] == "complete"
        ]) == 50
        assert final_state["state"]["minute_of_day"] == 530
        assert any(item["display_name"] == "Piedra" and item["quantity"] >= 1 for item in final_state["inventory"])
        assert any(item["display_name"] == "Manzana" and item["quantity"] >= 3 for item in final_state["inventory"])
        assert next(r["quantity"] for r in final_state["resources"] if r["resource_key"] == "monedas") == 90

def test_short_eco_command_authorizes_one_valid_power_attempt():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        world_id, session_id = seed["world_id"], seed["session_id"]
        entities = client.get(f"/api/worlds/{world_id}/entities").json()
        protagonist = next(entity for entity in entities if entity["kind"] == "protagonist")
        maelis = next(entity for entity in entities if entity["name"] == "Maelis Orven")

        prepared = client.post(
            f"/api/sessions/{session_id}/manual-prompt",
            json={"text": "/eco", "provider": "chatgpt_web", "visibility": "scene"}
        )
        assert prepared.status_code == 200, prepared.text

        external = json.dumps({
            "narration": "Intentas activar Eco sobre Maelis. El resultado aún no permite confirmar ningún cambio de memoria.",
            "events": [{
                "ref": "eco-event-1", "kind": "power", "entity_id": maelis["id"],
                "description": "El protagonista inicia un intento de Eco dirigido a Maelis.",
                "witness_ids": [protagonist["id"], maelis["id"]]
            }],
            "state_changes": [], "elapsed_minutes": 1, "movements": [],
            "inventory_ops": [], "resource_ops": [],
            "power_uses": [{
                "ability_key": "eco", "target_entity_id": maelis["id"],
                "event_ref": "eco-event-1", "result": "Intento registrado.",
                "cost": 1
            }],
            "pending": []
        }, ensure_ascii=False)
        response = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "short-eco-command-0001", "text": "/eco",
                "provider": "chatgpt_web", "visibility": "scene",
                "external_response": external,
                "manual_context_hash": prepared.json()["context_hash"]
            }
        )
        assert response.status_code == 200, response.text
        with database.connection() as conn:
            uses = conn.execute(
                "SELECT ability_key,target_entity_id FROM ability_uses WHERE session_id=? AND target_entity_id=?",
                (session_id, maelis["id"])
            ).fetchall()
        assert len(uses) == 1
        state = client.get(f"/api/sessions/{session_id}/state").json()
        attempts = next(item["attempts"] for item in state["eco_uses"] if item["target_entity_id"] == maelis["id"])
        assert attempts == 1


def test_eco_aliases_are_one_shared_power_and_cannot_double_count_in_a_turn():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        world_id, session_id = seed["world_id"], seed["session_id"]
        entities = client.get(f"/api/worlds/{world_id}/entities").json()
        protagonist = next(entity for entity in entities if entity["kind"] == "protagonist")
        maelis = next(entity for entity in entities if entity["name"] == "Maelis Orven")

        user_text = "Intento usar Eco sobre Maelis."
        prepared = client.post(
            f"/api/sessions/{session_id}/manual-prompt",
            json={"text": user_text, "provider": "gemini_web", "visibility": "scene"}
        )
        assert prepared.status_code == 200, prepared.text
        events = []
        for ref in ("eco-event-a", "eco-event-b"):
            events.append({
                "ref": ref, "kind": "power", "entity_id": maelis["id"],
                "description": "Se propone un intento de Eco sobre Maelis.",
                "witness_ids": [protagonist["id"], maelis["id"]]
            })
        external = json.dumps({
            "narration": "El mismo intento aparece descrito de dos formas; no se duplica el efecto.",
            "events": events, "state_changes": [], "elapsed_minutes": 1,
            "movements": [], "inventory_ops": [], "resource_ops": [],
            "power_uses": [
                {
                    "ability_key": "eco", "target_entity_id": maelis["id"],
                    "event_ref": "eco-event-a", "result": "Intento A.",
                    "cost": 1
                },
                {
                    "ability_key": "hipnosis", "target_entity_id": maelis["id"],
                    "event_ref": "eco-event-b", "result": "Intento B.",
                    "cost": 1
                }
            ],
            "pending": []
        }, ensure_ascii=False)
        response = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "eco-alias-duplicate-0001", "text": user_text,
                "provider": "gemini_web", "visibility": "scene",
                "external_response": external,
                "manual_context_hash": prepared.json()["context_hash"]
            }
        )
        assert response.status_code == 200, response.text
        with database.connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM ability_uses WHERE session_id=? AND target_entity_id=? "
                "AND ability_key IN ('eco','eco_humano','hipnosis')",
                (session_id, maelis["id"])
            ).fetchone()[0]
        assert count == 0
        assert sum("mismo poder" in note for note in response.json()["pending_notes"]) == 2


def test_power_use_is_rejected_when_source_event_type_or_target_does_not_match():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        world_id, session_id = seed["world_id"], seed["session_id"]
        entities = client.get(f"/api/worlds/{world_id}/entities").json()
        protagonist = next(entity for entity in entities if entity["kind"] == "protagonist")
        maelis = next(entity for entity in entities if entity["name"] == "Maelis Orven")
        prepared = client.post(
            f"/api/sessions/{session_id}/manual-prompt",
            json={"text": "/eco", "provider": "chatgpt_web", "visibility": "scene"}
        )
        assert prepared.status_code == 200, prepared.text
        external = json.dumps({
            "narration": "La respuesta describe eventos que no justifican los usos de poder propuestos.",
            "events": [
                {
                    "ref": "not-a-power-event", "kind": "object",
                    "entity_id": maelis["id"],
                    "description": "Maelis mira un objeto que está sobre la mesa.",
                    "witness_ids": [protagonist["id"], maelis["id"]]
                },
                {
                    "ref": "wrong-power-target", "kind": "power",
                    "entity_id": maelis["id"],
                    "description": "Un intento de poder sobre Maelis.",
                    "witness_ids": [protagonist["id"], maelis["id"]]
                }
            ],
            "state_changes": [], "elapsed_minutes": 1, "movements": [],
            "inventory_ops": [], "resource_ops": [],
            "power_uses": [
                {
                    "ability_key": "eco", "target_entity_id": maelis["id"],
                    "event_ref": "not-a-power-event", "result": "Propuesta sin evento de poder.",
                    "cost": 1
                },
                {
                    "ability_key": "eco", "target_entity_id": protagonist["id"],
                    "event_ref": "wrong-power-target", "result": "El objetivo no coincide con el evento.",
                    "cost": 1
                }
            ],
            "pending": []
        }, ensure_ascii=False)
        response = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "eco-source-validation-001",
                "text": "/eco", "provider": "chatgpt_web", "visibility": "scene",
                "external_response": external,
                "manual_context_hash": prepared.json()["context_hash"]
            }
        )
        assert response.status_code == 200, response.text
        assert any("tipo power" in note for note in response.json()["pending_notes"])
        assert any("no coincide" in note for note in response.json()["pending_notes"])
        with database.connection() as conn:
            uses = conn.execute(
                "SELECT COUNT(*) FROM ability_uses WHERE session_id=?", (session_id,)
            ).fetchone()[0]
        assert uses == 0


def test_session_backup_can_be_listed_and_restored_without_touching_other_sessions():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        world_id, session_id = seed["world_id"], seed["session_id"]
        entities = client.get(f"/api/worlds/{world_id}/entities").json()
        protagonist = next(entity for entity in entities if entity["kind"] == "protagonist")
        maelis = next(entity for entity in entities if entity["name"] == "Maelis Orven")

        other_created = client.post(
            f"/api/worlds/{world_id}/sessions",
            json={
                "name": "Partida que no se debe tocar",
                "location": "Aldea del Este",
                "day": 3,
                "minute_of_day": 620,
                "protagonist_entity_id": protagonist["id"],
                "present_entity_ids": [maelis["id"]],
                "initial_inventory": [{"name": "llave azul", "quantity": 2}],
                "initial_resources": [{"key": "monedas", "name": "Monedas", "quantity": 25, "unit": "monedas"}]
            }
        )
        assert other_created.status_code == 200, other_created.text
        other_session_id = other_created.json()["id"]
        other_before = client.get(f"/api/sessions/{other_session_id}/state").json()

        first_turn = client.post(
            f"/api/sessions/{session_id}/turns",
            json={"request_id": "restore-snapshot-turn-001", "text": "Miro alrededor.", "provider": "mock"}
        )
        assert first_turn.status_code == 200, first_turn.text
        snapshot_state = client.get(f"/api/sessions/{session_id}/state").json()
        snapshot_messages = client.get(f"/api/sessions/{session_id}/messages").json()
        with database.connection() as conn:
            snapshot_events = [
                dict(row) for row in conn.execute(
                    "SELECT id,turn_id,external_ref,kind,entity_id,description,witnesses_json,status "
                    "FROM events WHERE session_id=? ORDER BY created_at,id", (session_id,)
                ).fetchall()
            ]

        backup_response = client.post(f"/api/sessions/{session_id}/backup", json={})
        assert backup_response.status_code == 200, backup_response.text
        backup_name = backup_response.json()["backup_name"]
        listed = client.get(f"/api/sessions/{session_id}/backups")
        assert listed.status_code == 200
        assert any(item["name"] == backup_name and item["size_bytes"] > 0 for item in listed.json()["backups"])

        later_turn = client.post(
            f"/api/sessions/{session_id}/turns",
            json={"request_id": "restore-snapshot-turn-002", "text": "Sigo.", "provider": "mock"}
        )
        assert later_turn.status_code == 200, later_turn.text
        assert len(client.get(f"/api/sessions/{session_id}/messages").json()) == 4

        bad_path = client.post(
            f"/api/sessions/{session_id}/restore",
            json={"backup_name": "../outside.sqlite3", "confirmation": "RESTAURAR"}
        )
        assert bad_path.status_code == 422

        # A saved processing marker must block restore so it cannot erase an active turn.
        with database.transaction() as conn:
            conn.execute(
                "INSERT INTO messages(id,session_id,turn_id,client_request_id,turn_index,role,recipient_entity_id,content,provider,generation_status,metadata_json) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                ("restore-processing-row", session_id, "restore-processing-turn",
                 "restore-processing-request-001", 999, "user", "", "in progress",
                 "mock", "processing", "{}")
            )
        blocked = client.post(
            f"/api/sessions/{session_id}/restore",
            json={"backup_name": backup_name, "confirmation": "RESTAURAR"}
        )
        assert blocked.status_code == 409
        with database.transaction() as conn:
            conn.execute("DELETE FROM messages WHERE id='restore-processing-row'")

        restored = client.post(
            f"/api/sessions/{session_id}/restore",
            json={"backup_name": backup_name, "confirmation": "RESTAURAR"}
        )
        assert restored.status_code == 200, restored.text
        assert restored.json()["restored"] is True
        assert client.get(f"/api/sessions/{session_id}/state").json() == snapshot_state
        assert client.get(f"/api/sessions/{session_id}/messages").json() == snapshot_messages
        with database.connection() as conn:
            restored_events = [
                dict(row) for row in conn.execute(
                    "SELECT id,turn_id,external_ref,kind,entity_id,description,witnesses_json,status "
                    "FROM events WHERE session_id=? ORDER BY created_at,id", (session_id,)
                ).fetchall()
            ]
        assert restored_events == snapshot_events
        assert client.get(f"/api/sessions/{other_session_id}/state").json() == other_before


def test_restore_constraint_failure_rolls_back_all_changes_to_the_active_session():
    import sqlite3

    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        first = client.post(
            f"/api/sessions/{session_id}/turns",
            json={
                "request_id": "restore-rollback-seed-turn-001",
                "text": "Miro alrededor.",
                "provider": "mock",
                "visibility": "scene"
            }
        )
        assert first.status_code == 200, first.text
        before_state = client.get(f"/api/sessions/{session_id}/state").json()
        before_messages = client.get(f"/api/sessions/{session_id}/messages").json()
        with database.connection() as conn:
            before_tables = {
                table: [
                    dict(row) for row in conn.execute(
                        f"SELECT * FROM {table} WHERE session_id=? ORDER BY rowid", (session_id,)
                    ).fetchall()
                ]
                for table in main_module.RESTORE_SESSION_TABLES
            }

        backup = client.post(f"/api/sessions/{session_id}/backup", json={})
        assert backup.status_code == 200, backup.text
        backup_name = backup.json()["backup_name"]
        backup_path = database.path.parent / "backups" / backup_name

        # Make a well-formed SQLite backup with a relaxed historical inventory schema.
        # The source passes its own checks, but the active schema rejects a negative quantity.
        with sqlite3.connect(backup_path) as conn:
            conn.execute("PRAGMA foreign_keys=OFF")
            conn.execute("ALTER TABLE inventory_items RENAME TO inventory_items_legacy")
            conn.execute("""
                CREATE TABLE inventory_items (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    item_key TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    condition TEXT NOT NULL DEFAULT 'normal',
                    carrier_entity_id TEXT NOT NULL DEFAULT '',
                    location TEXT NOT NULL DEFAULT '',
                    properties_json TEXT NOT NULL DEFAULT '{}',
                    last_event_id TEXT,
                    UNIQUE(session_id, item_key)
                )
            """)
            conn.execute("""
                INSERT INTO inventory_items
                    (id,session_id,item_key,display_name,quantity,condition,
                     carrier_entity_id,location,properties_json,last_event_id)
                SELECT id,session_id,item_key,display_name,quantity,condition,
                       carrier_entity_id,location,properties_json,last_event_id
                FROM inventory_items_legacy
            """)
            conn.execute("DROP TABLE inventory_items_legacy")
            row = conn.execute(
                "SELECT id FROM inventory_items WHERE session_id=? ORDER BY rowid LIMIT 1",
                (session_id,)
            ).fetchone()
            if row:
                conn.execute("UPDATE inventory_items SET quantity=-1 WHERE id=?", (row[0],))
            else:
                conn.execute(
                    "INSERT INTO inventory_items "
                    "(id,session_id,item_key,display_name,quantity,condition,carrier_entity_id,location) "
                    "VALUES(?,?,?,?,?,?,?,?)",
                    (uuid.uuid4().hex, session_id, "corrupt-test-item", "Objeto de prueba", -1, "normal", "", "")
                )
            conn.commit()
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert conn.execute("PRAGMA foreign_key_check").fetchone() is None

        failed_restore = client.post(
            f"/api/sessions/{session_id}/restore",
            json={"backup_name": backup_name, "confirmation": "RESTAURAR"}
        )
        assert failed_restore.status_code == 422, failed_restore.text
        assert "restauración se canceló" in failed_restore.json()["detail"]
        assert client.get(f"/api/sessions/{session_id}/state").json() == before_state
        assert client.get(f"/api/sessions/{session_id}/messages").json() == before_messages
        with database.connection() as conn:
            after_tables = {
                table: [
                    dict(row) for row in conn.execute(
                        f"SELECT * FROM {table} WHERE session_id=? ORDER BY rowid", (session_id,)
                    ).fetchall()
                ]
                for table in main_module.RESTORE_SESSION_TABLES
            }
        assert after_tables == before_tables


def test_restore_rejects_backup_when_world_canon_has_changed():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        world_id, session_id = seed["world_id"], seed["session_id"]
        backup = client.post(f"/api/sessions/{session_id}/backup", json={})
        assert backup.status_code == 200, backup.text

        changed = client.post(
            f"/api/worlds/{world_id}/entities",
            json={"name": "Personaje añadido después de la copia", "kind": "character", "profile": "Cambio posterior al backup."}
        )
        assert changed.status_code == 200, changed.text
        before = client.get(f"/api/sessions/{session_id}/state").json()

        response = client.post(
            f"/api/sessions/{session_id}/restore",
            json={"backup_name": backup.json()["backup_name"], "confirmation": "RESTAURAR"}
        )
        assert response.status_code == 409
        assert "canon" in response.json()["detail"].lower()
        assert client.get(f"/api/sessions/{session_id}/state").json() == before


def test_restore_accepts_legacy_backup_without_presence_status():
    import sqlite3

    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        world_id, session_id = seed["world_id"], seed["session_id"]
        entities = client.get(f"/api/worlds/{world_id}/entities").json()
        maelis = next(entity for entity in entities if entity["name"] == "Maelis Orven")
        current_location = client.get(f"/api/sessions/{session_id}/state").json()["state"]["location"]

        # Create the checkpoint while Maelis is outside the active scene.
        with database.transaction() as conn:
            conn.execute(
                "UPDATE session_presence SET location=?,presence_status='away' "
                "WHERE session_id=? AND entity_id=?",
                ("Aldea Lejana", session_id, maelis["id"])
            )
        backup = client.post(f"/api/sessions/{session_id}/backup", json={})
        assert backup.status_code == 200, backup.text
        backup_name = backup.json()["backup_name"]
        backup_path = database.path.parent / "backups" / backup_name

        # Rewrite only the backup's presence table into the historical shape.
        with sqlite3.connect(backup_path) as conn:
            conn.execute("PRAGMA foreign_keys=OFF")
            conn.execute("ALTER TABLE session_presence RENAME TO session_presence_current")
            conn.execute("""
                CREATE TABLE session_presence (
                    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
                    location TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY(session_id, entity_id)
                )
            """)
            conn.execute(
                "INSERT INTO session_presence(session_id,entity_id,location) "
                "SELECT session_id,entity_id,location FROM session_presence_current"
            )
            conn.execute("DROP TABLE session_presence_current")
            conn.commit()
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert conn.execute("PRAGMA foreign_key_check").fetchone() is None

        # Change the active state after the checkpoint, then restore the old format.
        with database.transaction() as conn:
            conn.execute(
                "UPDATE session_presence SET location=?,presence_status='present' "
                "WHERE session_id=? AND entity_id=?",
                (current_location, session_id, maelis["id"])
            )
        response = client.post(
            f"/api/sessions/{session_id}/restore",
            json={"backup_name": backup_name, "confirmation": "RESTAURAR"}
        )
        assert response.status_code == 200, response.text

        state = client.get(f"/api/sessions/{session_id}/state").json()
        restored_maelis = next(item for item in state["participants"] if item["id"] == maelis["id"])
        assert restored_maelis["location"] == "Aldea Lejana"
        assert restored_maelis["presence_status"] == "away"
        with database.connection() as conn:
            stored = conn.execute(
                "SELECT location,presence_status FROM session_presence "
                "WHERE session_id=? AND entity_id=?",
                (session_id, maelis["id"])
            ).fetchone()
        assert stored["location"] == "Aldea Lejana"
        assert stored["presence_status"] == "away"


def test_legacy_audience_metadata_fails_closed_without_source_or_witnesses():
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        world_id = seed["world_id"]
        entities = client.get(f"/api/worlds/{world_id}/entities").json()
        maelis = next(entity for entity in entities if entity["name"] == "Maelis Orven")
        ivar = next(entity for entity in entities if entity["name"] == "Ivar Dalen")

        old_turn_id = uuid.uuid4().hex
        old_user_id = uuid.uuid4().hex
        old_assistant_id = uuid.uuid4().hex
        private_event_id = uuid.uuid4().hex
        unknown_event_id = uuid.uuid4().hex
        with database.transaction() as conn:
            # These are historical rows from before audience_ids/visibility existed.
            conn.execute(
                "INSERT INTO messages(id,session_id,turn_id,turn_index,role,recipient_entity_id,"
                "content,provider,generation_status,metadata_json) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (old_user_id, session_id, old_turn_id, 1, "user", maelis["id"],
                 "Frase heredada confidencial para Maelis", "mock", "complete", "{}")
            )
            conn.execute(
                "INSERT INTO messages(id,session_id,turn_id,turn_index,role,recipient_entity_id,"
                "content,provider,generation_status,metadata_json) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (old_assistant_id, session_id, old_turn_id, 1, "assistant", maelis["id"],
                 "Respuesta heredada solo para Maelis", "mock", "complete", "{}")
            )
            conn.execute(
                "INSERT INTO events(id,session_id,turn_id,external_ref,kind,entity_id,description,"
                "witnesses_json,status,source_message_id) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (private_event_id, session_id, old_turn_id, "legacy-private-event", "dialogue",
                 maelis["id"], "Hecho heredado de conversación dirigida a Maelis", "[]",
                 "recorded", old_user_id)
            )
            # This older event has neither a resolvable source message nor witnesses.
            conn.execute(
                "INSERT INTO events(id,session_id,turn_id,external_ref,kind,entity_id,description,"
                "witnesses_json,status,source_message_id) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (unknown_event_id, session_id, uuid.uuid4().hex, "legacy-unscoped-event", "world",
                 "", "Hecho antiguo sin fuente ni testigos", "[]", "recorded", "")
            )

        with database.connection() as conn:
            session = session_row(conn, session_id)
            maelis_context = build_context(
                conn, session, "¿Qué conversamos?", maelis["id"],
                "future-maelis-turn", visibility="scene", include_diagnostics=True
            )
            ivar_context = build_context(
                conn, session, "¿Qué conversamos?", ivar["id"],
                "future-ivar-turn", visibility="scene", include_diagnostics=True
            )

        maelis_messages = [item["content"] for item in maelis_context["recent_messages"]]
        ivar_messages = [item["content"] for item in ivar_context["recent_messages"]]
        assert any("Frase heredada confidencial" in item for item in maelis_messages)
        assert any("Respuesta heredada solo para Maelis" in item for item in maelis_messages)
        assert not any("Frase heredada confidencial" in item for item in ivar_messages)
        assert not any("Respuesta heredada solo para Maelis" in item for item in ivar_messages)

        maelis_events = [item["description"] for item in maelis_context["recent_events"]]
        ivar_events = [item["description"] for item in ivar_context["recent_events"]]
        assert any("dirigida a Maelis" in item for item in maelis_events)
        assert not any("dirigida a Maelis" in item for item in ivar_events)
        assert not any("sin fuente ni testigos" in item for item in maelis_events)
        assert not any("sin fuente ni testigos" in item for item in ivar_events)

        for context in (maelis_context, ivar_context):
            diagnostics = context["_diagnostics"]
            excluded = next(
                item for item in diagnostics["excluded_events"]
                if item["event_id"] == unknown_event_id
            )
            assert "sin mensaje fuente ni testigos" in excluded["reason"]


def test_undo_and_regenerate_private_turn_never_leaks_to_scene_bystanders(monkeypatch):
    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        world_id, session_id = seed["world_id"], seed["session_id"]
        entities = client.get(f"/api/worlds/{world_id}/entities").json()
        maelis = next(entity for entity in entities if entity["name"] == "Maelis Orven")
        ivar = next(entity for entity in entities if entity["name"] == "Ivar Dalen")
        with database.connection() as conn:
            protagonist_id = session_row(conn, session_id)["protagonist_entity_id"]
        private_code = "ORQUIDEA-314"

        class PrivateProvider:
            name = "mock"

            async def generate(self, payload):
                audience = list(payload["context"]["audience_ids"])
                return NarratorResponse(
                    narration=f"Maelis susurra el código privado {private_code}.",
                    elapsed_minutes=1,
                    events=[
                        EventProposal(
                            ref="private-undo-regenerate-code",
                            kind="dialogue",
                            entity_id=maelis["id"],
                            description=f"Maelis reveló el código confidencial {private_code}.",
                            witness_ids=audience
                        )
                    ]
                )

        monkeypatch.setattr(
            main_module, "make_provider",
            lambda provider_name, settings: PrivateProvider()
        )
        payload = {
            "request_id": "private-undo-regenerate-001",
            "text": "Le pregunto a Maelis si conoce algún código.",
            "recipient_id": maelis["id"],
            "provider": "mock",
            "visibility": "private"
        }

        first = client.post(f"/api/sessions/{session_id}/turns", json=payload)
        assert first.status_code == 200, first.text
        turn_id = first.json()["turn_id"]
        assert private_code in first.json()["narration"]

        def preview(recipient_id, visibility="scene"):
            return client.post(
                f"/api/sessions/{session_id}/context-preview",
                json={
                    "text": "¿Qué código conoce Maelis?",
                    "recipient_id": recipient_id,
                    "visibility": visibility
                }
            )

        def assert_secret_absent(context_response):
            assert context_response.status_code == 200, context_response.text
            context = context_response.json()["context"]
            assert not any(private_code in item["content"] for item in context["recent_messages"])
            assert not any(private_code in item["description"] for item in context["recent_events"])

        # The ordinary scene context excludes the private exchange even before undo.
        assert_secret_absent(preview(ivar["id"]))

        undone = client.post(f"/api/sessions/{session_id}/turns/{turn_id}/undo", json={})
        assert undone.status_code == 200, undone.text
        assert undone.json()["undone"] is True

        # Undo must also remove its narration/event from the active context, not
        # merely restore the numerical world state.
        assert_secret_absent(preview(ivar["id"]))
        with database.connection() as conn:
            audited = conn.execute(
                "SELECT status,turn_id,description FROM events WHERE session_id=? AND external_ref=?",
                (session_id, "private-undo-regenerate-code")
            ).fetchone()
            assert audited is not None
            assert audited["status"] == "rejected"
            assert audited["turn_id"] == undone.json()["audit_turn_id"]

        # Regenerating the same request reuses its turn slot, but must keep the
        # original private visibility/audience attached to the new response.
        regenerated = client.post(f"/api/sessions/{session_id}/turns", json=payload)
        assert regenerated.status_code == 200, regenerated.text
        assert regenerated.json()["replayed"] is False
        assert regenerated.json()["turn_id"] == turn_id
        assert_secret_absent(preview(ivar["id"]))

        maelis_context = preview(maelis["id"], visibility="private")
        assert maelis_context.status_code == 200, maelis_context.text
        visible_messages = [item["content"] for item in maelis_context.json()["context"]["recent_messages"]]
        visible_events = [item["description"] for item in maelis_context.json()["context"]["recent_events"]]
        assert any(private_code in content for content in visible_messages)
        assert any(private_code in description for description in visible_events)


def test_cancelled_provider_generation_marks_turn_failed_and_allows_same_request_retry(monkeypatch):
    import asyncio
    from concurrent.futures import CancelledError as FutureCancelledError

    with TestClient(app) as client:
        seed = client.post("/api/demo/seed", json={}).json()
        session_id = seed["session_id"]
        state_before = client.get(f"/api/sessions/{session_id}/state").json()
        counters = {"cancelled": 0, "recovery": 0}

        class CancelledProvider:
            async def generate(self, payload):
                counters["cancelled"] += 1
                raise asyncio.CancelledError("simulated task cancellation")

        class RecoveryProvider:
            async def generate(self, payload):
                counters["recovery"] += 1
                return NarratorResponse(
                    narration="La respuesta recuperada se guardó una sola vez.",
                    elapsed_minutes=1
                )

        monkeypatch.setattr(
            main_module, "make_provider",
            lambda provider_name, settings: CancelledProvider()
        )
        payload = {
            "request_id": "cancelled-provider-recovery-001",
            "text": "Observo el camino y espero una respuesta.",
            "provider": "mock",
            "visibility": "scene"
        }

        # Depending on the ASGI test transport, a propagated cancellation may
        # surface as asyncio.CancelledError or as a 5xx response. Either way,
        # the durable message must be failed, not left in processing.
        try:
            cancelled_response = client.post(
                f"/api/sessions/{session_id}/turns", json=payload
            )
        except (asyncio.CancelledError, FutureCancelledError):
            cancelled_response = None
        if cancelled_response is not None:
            assert cancelled_response.status_code >= 500

        messages = client.get(f"/api/sessions/{session_id}/messages").json()
        failed_user = next(
            message for message in messages
            if message["role"] == "user" and message["content"] == payload["text"]
        )
        assert failed_user["generation_status"] == "failed"
        assert not any(
            message["role"] == "assistant" and message["turn_id"] == failed_user["turn_id"]
            for message in messages
        )
        assert client.get(f"/api/sessions/{session_id}/state").json() == state_before
        assert counters["cancelled"] == 1

        monkeypatch.setattr(
            main_module, "make_provider",
            lambda provider_name, settings: RecoveryProvider()
        )
        retried = client.post(f"/api/sessions/{session_id}/turns", json=payload)
        assert retried.status_code == 200, retried.text
        assert retried.json()["turn_id"] == failed_user["turn_id"]
        assert retried.json()["replayed"] is False
        assert counters["recovery"] == 1

        messages_after = client.get(f"/api/sessions/{session_id}/messages").json()
        assert len([
            message for message in messages_after
            if message["role"] == "user" and message["content"] == payload["text"]
        ]) == 1
        assert len([
            message for message in messages_after
            if message["role"] == "assistant" and message["turn_id"] == failed_user["turn_id"]
        ]) == 1
