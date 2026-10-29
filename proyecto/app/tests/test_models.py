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
