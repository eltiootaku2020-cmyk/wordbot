import asyncio

from canon_manager.providers import MockProvider


def test_mock_narrator_returns_separate_story_and_change_proposal():
    payload = {
        "user_message": "Hola, linda",
        "context": {
            "recipient": {"id": "maelis", "name": "Maelis Orven"},
            "participants": [
                {"id": "maelis", "name": "Maelis Orven"},
                {"id": "ivar", "name": "Ivar Dalen"},
                {"id": "brina", "name": "Brina Solcor"}
            ]
        }
    }
    result = asyncio.run(MockProvider().generate(payload))
    assert "Apenas te conozco" in result.narration
    assert result.events[0].entity_id == "maelis"
    assert any(change.field == "confidence" and change.numeric_value == -1 for change in result.state_changes)
    assert any(change.field == "impression" for change in result.state_changes)
