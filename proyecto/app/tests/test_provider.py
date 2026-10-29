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



def test_manual_parser_accepts_one_fenced_json_block_with_surrounding_helper_text():
    from canon_manager.providers import parse_narrator_response

    fence = chr(96) * 3
    raw = (
        "Aquí está la respuesta:\n" + fence + "json\n"
        + '{ "narration": "Maelis asiente.", "events": [], "state_changes": [], '
        + '"elapsed_minutes": 1, "movements": [], "inventory_ops": [], '
        + '"resource_ops": [], "power_uses": [], "pending": [] }\n'
        + fence + "\n"
    )
    parsed = parse_narrator_response(raw)
    assert parsed.narration == "Maelis asiente."


def test_manual_parser_rejects_duplicate_json_keys():
    import pytest
    from canon_manager.providers import parse_narrator_response

    with pytest.raises(ValueError, match="duplicada"):
        parse_narrator_response('{"narration":"Primera","narration":"Segunda"}')


def test_manual_parser_rejects_multiple_json_fences():
    import pytest
    from canon_manager.providers import parse_narrator_response

    fence = chr(96) * 3
    raw = fence + "json\n{}\n" + fence + "\n" + fence + "json\n{}\n" + fence
    with pytest.raises(ValueError, match="único bloque"):
        parse_narrator_response(raw)
