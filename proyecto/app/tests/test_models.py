import pytest
from pydantic import ValidationError

from canon_manager.models import NarratorResponse


def test_narrator_response_accepts_complete_contract():
    result = NarratorResponse(
        narration="Maelis responde.",
        events=[],
        state_changes=[],
        elapsed_minutes=1,
        movements=[],
        inventory_ops=[],
        power_uses=[],
        pending=[]
    )
    assert result.narration == "Maelis responde."


def test_narrator_response_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        NarratorResponse(
            narration="Texto",
            events=[],
            state_changes=[],
            elapsed_minutes=1,
            movements=[],
            inventory_ops=[],
            power_uses=[],
            pending=[],
            invented_stat="should be rejected"
        )



def test_short_user_actions_are_valid_but_whitespace_only_is_rejected():
    from pydantic import ValidationError
    from canon_manager.models import TurnRequest

    short = TurnRequest(request_id="short-action-001", text="  Sí.  ")
    assert short.text == "Sí."

    with pytest.raises(ValidationError):
        TurnRequest(request_id="blank-action-001", text="   ")



def test_narrator_contract_rejects_oversized_quantities_and_long_pending_notes():
    from pydantic import ValidationError
    from canon_manager.models import NarratorResponse, InventoryOperation

    with pytest.raises(ValidationError):
        InventoryOperation(
            operation="acquire", item_name="moneda", quantity=10**15,
            reason="hallazgo", event_ref="evento-1"
        )

    with pytest.raises(ValidationError):
        NarratorResponse(narration="Una escena.", pending=["x" * 501])


def test_initial_world_lists_have_safe_caps():
    from pydantic import ValidationError
    from canon_manager.models import WorldStartCreate, InitialEntity

    with pytest.raises(ValidationError):
        WorldStartCreate(
            name="Mundo",
            protagonist_name="Protagonista",
            cast=[InitialEntity(name=f"PNJ {index}") for index in range(101)]
        )
