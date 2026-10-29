from canon_manager.providers import normalized_schema
from canon_manager.models import NarratorResponse


def test_schema_declares_all_root_fields_as_required():
    schema = normalized_schema(NarratorResponse, resolve_refs=False)
    assert schema["type"] == "object"
    assert set(schema["required"]) == set(schema["properties"])
    assert schema["additionalProperties"] is False


def test_gemini_schema_inlines_references():
    schema = normalized_schema(NarratorResponse, resolve_refs=True)
    assert "$defs" not in schema
    assert schema["additionalProperties"] is False
    assert "events" in schema["properties"]


def test_manual_chat_parser_recovers_one_json_object_surrounded_by_prose():
    import json
    from canon_manager.providers import parse_narrator_response

    payload = {
        "narration": "Maelis señala un símbolo {rojo} en la puerta.",
        "events": [], "state_changes": [], "elapsed_minutes": 1,
        "movements": [], "inventory_ops": [], "resource_ops": [],
        "power_uses": [], "pending": []
    }
    raw = "Aquí tienes el resultado solicitado:\n" + json.dumps(payload, ensure_ascii=False) + "\nFin de la respuesta."
    parsed = parse_narrator_response(raw)
    assert parsed.narration == payload["narration"]


def test_manual_chat_parser_rejects_multiple_json_objects_as_ambiguous():
    import pytest
    from canon_manager.providers import parse_narrator_response

    first = '{"narration":"Primera escena."}'
    second = '{"narration":"Segunda escena."}'
    with pytest.raises(ValueError):
        parse_narrator_response(f"Ejemplo: {first}\nRespuesta final: {second}")
