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


def test_manual_parser_accepts_one_json_object_surrounded_by_prose_and_braces_in_strings():
    import json
    from canon_manager.models import NarratorResponse
    from canon_manager.providers import parse_narrator_response

    payload = NarratorResponse(
        narration='El cartel dice: {“salida”} y alguien añadió } al margen.',
        events=[], state_changes=[], elapsed_minutes=1,
        movements=[], inventory_ops=[], resource_ops=[], power_uses=[], pending=[]
    ).model_dump()
    raw = "Respuesta revisada (no copies esta explicación):\n" + json.dumps(payload, ensure_ascii=False) + "\nFin de la respuesta."
    parsed = parse_narrator_response(raw)
    assert parsed.narration == payload["narration"]


def test_manual_parser_rejects_two_json_objects_even_if_both_are_valid():
    import json
    import pytest
    from canon_manager.models import NarratorResponse
    from canon_manager.providers import parse_narrator_response

    payload = NarratorResponse(
        narration="Respuesta.", events=[], state_changes=[], elapsed_minutes=1,
        movements=[], inventory_ops=[], resource_ops=[], power_uses=[], pending=[]
    ).model_dump()
    one = json.dumps(payload, ensure_ascii=False)
    with pytest.raises(ValueError):
        parse_narrator_response("Borrador:\n" + one + "\nVersión final:\n" + one)
