import os
import tempfile
from pathlib import Path
import uuid
import json

os.environ["APP_PROVIDER"] = "mock"
os.environ["APP_DB_PATH"] = str(Path(tempfile.mkdtemp(prefix="canon-test-")) / "test.sqlite3")

from fastapi.testclient import TestClient

import canon_manager.main as main_module
from canon_manager.main import app, database, build_context, session_row, apply_narrator_result
from canon_manager.models import NarratorResponse, EventProposal, InventoryOperation, MovementProposal, ResourceOperation


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
