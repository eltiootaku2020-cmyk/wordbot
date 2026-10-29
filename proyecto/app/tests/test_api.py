import os
import tempfile
from pathlib import Path
import uuid
import json

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
        assert any(resource["resource_key"] == "monedas" and resource["quantity"] == 0
                   for resource in state["resources"])

        second = client.post("/api/presets/isekai-sin-destino", json={})
        assert second.status_code == 200, second.text
        second_data = second.json()
        assert second_data["world_id"] == first_data["world_id"]
        assert second_data["session_id"] != first_data["session_id"]



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
            session_id, "Intento comprar una manzana por seis monedas", result
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
            session_id, "Intento pagar cuatro monedas por el alojamiento", unaffordable
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


def test_manual_web_turn_can_retry_corrected_json_with_same_request_id():
    """A bad pasted answer must be recoverable without consuming or duplicating a turn."""
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
        common = {
            "request_id": "manual-web-retry-0001",
            "text": "Observo el camino con cuidado.",
            "provider": "chatgpt_web",
            "visibility": "scene",
            "manual_context_hash": prepared.json()["context_hash"]
        }

        invalid = client.post(
            f"/api/sessions/{session_id}/turns",
            json={**common, "external_response": "La respuesta narrativa está fuera del JSON."}
        )
        assert invalid.status_code == 502

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

        messages = client.get(f"/api/sessions/{session_id}/messages").json()
        user_messages = [
            message for message in messages
            if message["role"] == "user" and message["content"] == "Observo el camino con cuidado."
        ]
        assistant_messages = [
            message for message in messages
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
                 "El medallón de obsidiana quedó enterrado bajo la torre del norte.", "[]", "recorded", "2020-01-01 00:00:00")
            )
            for index in range(18):
                conn.execute(
                    "INSERT INTO events(id,session_id,turn_id,external_ref,kind,entity_id,description,witnesses_json,status,created_at) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (uuid.uuid4().hex, session_id, f"noise-turn-{index}", f"noise-{index}", "observation", protagonist_id,
                     f"Un detalle cotidiano irrelevante número {index} ocurrió en la plaza.", "[]", "recorded",
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


def test_100_short_turns_persist_across_database_reinitialization_and_backup():
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
        messages = client.get(f"/api/sessions/{session_id}/messages").json()
        assert len(messages) == 200
        assert len([message for message in messages if message["role"] == "user"]) == 100
        assert len([message for message in messages if message["role"] == "assistant" and message["generation_status"] == "complete"]) == 100
        assert before_state["state"]["minute_of_day"] == 580

        with database.connection() as conn:
            event_count = conn.execute(
                "SELECT COUNT(*) FROM events WHERE session_id=?", (session_id,)
            ).fetchone()[0]
        assert event_count == 100

        # Re-run the initializer, as a lightweight restart simulation: all state
        # must be read from SQLite rather than hidden process memory.
        database.initialize()
        assert client.get(f"/api/sessions/{session_id}/state").json() == before_state
        assert len(client.get(f"/api/sessions/{session_id}/messages").json()) == 200

        backup = client.post(f"/api/sessions/{session_id}/backup")
        assert backup.status_code == 200, backup.text
        with sqlite3.connect(backup.json()["path"]) as conn:
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert conn.execute(
                "SELECT COUNT(*) FROM messages WHERE session_id=?", (session_id,)
            ).fetchone()[0] == 200
            assert conn.execute(
                "SELECT COUNT(*) FROM events WHERE session_id=?", (session_id,)
            ).fetchone()[0] == 100


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
