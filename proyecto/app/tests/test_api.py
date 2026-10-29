import os
import tempfile
from pathlib import Path

os.environ["APP_PROVIDER"] = "mock"
os.environ["APP_DB_PATH"] = str(Path(tempfile.mkdtemp(prefix="canon-test-")) / "test.sqlite3")

from fastapi.testclient import TestClient

from canon_manager.main import app


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
            json={"text": "Hola, linda", "recipient_id": maelis["id"], "provider": "mock"}
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
