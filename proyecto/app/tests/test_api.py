import os
import tempfile
from pathlib import Path
import uuid

os.environ["APP_PROVIDER"] = "mock"
os.environ["APP_DB_PATH"] = str(Path(tempfile.mkdtemp(prefix="canon-test-")) / "test.sqlite3")

from fastapi.testclient import TestClient

from canon_manager.main import app, database


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
        assert first_data["lore_entries"] == 76
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

        second = client.post("/api/presets/isekai-sin-destino", json={})
        assert second.status_code == 200, second.text
        second_data = second.json()
        assert second_data["world_id"] == first_data["world_id"]
        assert second_data["session_id"] != first_data["session_id"]
