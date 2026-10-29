from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EventProposal(StrictModel):
    ref: str = Field(min_length=1, max_length=40)
    kind: Literal["dialogue", "reaction", "observation", "rumor", "location", "object", "power", "major_change", "other"]
    entity_id: str = ""
    description: str
    witness_ids: list[str] = Field(default_factory=list)


class StateChangeProposal(StrictModel):
    ref: str = Field(min_length=1, max_length=40)
    entity_id: str
    field: Literal["confidence", "suspicion", "friendship", "respect", "rivalry", "resentment", "fear", "gratitude_debt", "cooperation", "attraction", "impression"]
    operation: Literal["delta", "set", "note"]
    numeric_value: int = 0
    text_value: str = ""
    reason: str
    event_ref: str
    requires_approval: bool = False


class MovementProposal(StrictModel):
    entity_id: str
    destination: str
    reason: str
    event_ref: str


class InventoryOperation(StrictModel):
    operation: Literal["acquire", "consume", "drop", "transfer", "condition"]
    item_name: str
    quantity: int = Field(ge=1)
    condition: str = "normal"
    carrier_entity_id: str = ""
    location: str = ""
    reason: str
    event_ref: str


class PowerUseProposal(StrictModel):
    ability_key: str
    target_entity_id: str
    event_ref: str
    result: str
    cost: int = Field(default=1, ge=0)


class NarratorResponse(StrictModel):
    narration: str = Field(min_length=1)
    events: list[EventProposal] = Field(default_factory=list)
    state_changes: list[StateChangeProposal] = Field(default_factory=list)
    elapsed_minutes: int = Field(default=1, ge=0, le=1440)
    movements: list[MovementProposal] = Field(default_factory=list)
    inventory_ops: list[InventoryOperation] = Field(default_factory=list)
    power_uses: list[PowerUseProposal] = Field(default_factory=list)
    pending: list[str] = Field(default_factory=list)


class WorldCreate(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    canon_text: str = ""


class EntityCreate(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    kind: Literal["protagonist", "character", "creature", "npc", "other"] = "character"
    profile: str = ""


class InventorySeed(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    quantity: int = Field(default=1, ge=1)
    condition: str = "normal"
    carrier_entity_id: str = ""
    location: str = ""


class SessionCreate(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    location: str = "Lugar desconocido"
    day: int = Field(default=1, ge=1)
    minute_of_day: int = Field(default=480, ge=0, le=1439)
    protagonist_entity_id: str
    present_entity_ids: list[str] = Field(default_factory=list)
    initial_inventory: list[InventorySeed] = Field(default_factory=list)


class TurnRequest(StrictModel):
    request_id: str = Field(min_length=8, max_length=100)
    text: str = Field(min_length=1, max_length=8000)
    recipient_id: str = ""
    provider: Literal["mock", "openai", "gemini"] = "mock"


class ApprovalRequest(StrictModel):
    initial_value: float | None = Field(default=None, ge=0, le=100)
