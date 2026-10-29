import os
import tempfile
from pathlib import Path
import uuid
import json

os.environ["APP_PROVIDER"] = "mock"
os.environ["APP_DB_PATH"] = str(Path(tempfile.mkdtemp(prefix="canon-test-")) / "test.sqlite3")

from fastapi.testclient import TestClient

from canon_manager.main import app, database, build_context, session_row, apply_narrator_result
from canon_manager.models import NarratorResponse, EventProposal, InventoryOperation, MovementProposal


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
                {"name": "Manzana", "quantity": 2, "condition": "normal"}
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


def test_free_found_object_is_added_but_paid_purchase_stays_pending():
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
        assert "contabilidad de moneda" in change["reason"]
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
