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
