from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EventProposal(StrictModel):
    ref: str = Field(min_length=1, max_length=40)
    kind: Literal["dialogue", "reaction", "observation", "rumor", "location", "object", "resource", "power", "major_change", "other"]
    entity_id: str = Field(default="", max_length=120)
    description: str = Field(min_length=1, max_length=1000)
    witness_ids: list[Annotated[str, Field(max_length=120)]] = Field(default_factory=list, max_length=30)


class StateChangeProposal(StrictModel):
    ref: str = Field(min_length=1, max_length=40)
    entity_id: str = Field(max_length=120)
    field: Literal["confidence", "suspicion", "friendship", "respect", "rivalry", "resentment", "fear", "gratitude_debt", "cooperation", "attraction", "impression"]
    operation: Literal["delta", "set", "note"]
    numeric_value: int = Field(default=0, ge=-1000, le=1000)
    text_value: str = Field(default="", max_length=1000)
    reason: str = Field(min_length=1, max_length=600)
    event_ref: str = Field(min_length=1, max_length=40)
    requires_approval: bool = False


class MovementProposal(StrictModel):
    entity_id: str = Field(max_length=120)
    destination: str = Field(min_length=1, max_length=180)
    reason: str = Field(min_length=1, max_length=600)
    event_ref: str = Field(min_length=1, max_length=40)


class InventoryOperation(StrictModel):
    operation: Literal["acquire", "consume", "drop", "transfer", "condition"]
    item_name: str = Field(min_length=1, max_length=120)
    quantity: int = Field(ge=1, le=1000000000)
    condition: str = Field(default="normal", max_length=80)
    carrier_entity_id: str = Field(default="", max_length=120)
    location: str = Field(default="", max_length=180)
    reason: str = Field(min_length=1, max_length=600)
    event_ref: str = Field(min_length=1, max_length=40)
    cost: int = Field(default=0, ge=0, le=1000000, description="Coste total de la adquisición; 0 para hallazgos/regalos gratuitos.")
    currency_key: str = Field(default="monedas", max_length=80)


class ResourceSeed(StrictModel):
    key: str = Field(default="", max_length=80)
    name: str = Field(min_length=1, max_length=100)
    quantity: int = Field(default=0, ge=0, le=1000000000)
    unit: str = Field(default="", max_length=40)


class ResourceOperation(StrictModel):
    operation: Literal["gain", "spend"]
    resource_key: str = Field(min_length=1, max_length=80)
    display_name: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=1, le=1000000000)
    unit: str = Field(default="", max_length=40)
    reason: str = Field(min_length=1, max_length=600)
    event_ref: str = Field(min_length=1, max_length=40)


class PowerUseProposal(StrictModel):
    ability_key: str = Field(min_length=1, max_length=80)
    target_entity_id: str = Field(min_length=1, max_length=120)
    event_ref: str = Field(min_length=1, max_length=40)
    result: str = Field(min_length=1, max_length=600)
    cost: int = Field(default=1, ge=0, le=1000000)


PendingNote = Annotated[str, Field(min_length=1, max_length=500)]


class NarratorResponse(StrictModel):
    narration: str = Field(min_length=1, max_length=12000)
    events: list[EventProposal] = Field(default_factory=list, max_length=30)
    state_changes: list[StateChangeProposal] = Field(default_factory=list, max_length=40)
    elapsed_minutes: int = Field(default=1, ge=0, le=1440)
    movements: list[MovementProposal] = Field(default_factory=list, max_length=20)
    inventory_ops: list[InventoryOperation] = Field(default_factory=list, max_length=40)
    resource_ops: list[ResourceOperation] = Field(default_factory=list, max_length=30)
    power_uses: list[PowerUseProposal] = Field(default_factory=list, max_length=20)
    pending: list[PendingNote] = Field(default_factory=list, max_length=30)


class WorldCreate(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    canon_text: str = Field(default="", max_length=100000)


class EntityCreate(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    kind: Literal["protagonist", "character", "creature", "npc", "other"] = "character"
    profile: str = Field(default="", max_length=8000)


class InventorySeed(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    quantity: int = Field(default=1, ge=1, le=1000000000)
    condition: str = Field(default="normal", max_length=80)
    carrier_entity_id: str = Field(default="", max_length=120)
    location: str = Field(default="", max_length=180)


class InitialEntity(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    kind: Literal["character", "creature", "npc", "other"] = "character"
    profile: str = Field(default="", max_length=8000)


class WorldStartCreate(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    canon_text: str = Field(default="", max_length=100000)
    protagonist_name: str = Field(default="Protagonista", min_length=1, max_length=120)
    protagonist_profile: str = Field(default="El usuario controla todas las acciones y diálogos del protagonista.", max_length=8000)
    session_name: str = Field(default="Partida 1", max_length=120)
    location: str = Field(default="Lugar desconocido", max_length=180)
    day: int = Field(default=1, ge=1)
    minute_of_day: int = Field(default=480, ge=0, le=1439)
    cast: list[InitialEntity] = Field(default_factory=list, max_length=100)
    initial_inventory: list[InventorySeed] = Field(default_factory=list, max_length=100)
    initial_resources: list[ResourceSeed] = Field(default_factory=list, max_length=100)


class SessionCreate(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    location: str = Field(default="Lugar desconocido", max_length=180)
    day: int = Field(default=1, ge=1)
    minute_of_day: int = Field(default=480, ge=0, le=1439)
    protagonist_entity_id: str
    present_entity_ids: list[Annotated[str, Field(max_length=120)]] = Field(default_factory=list, max_length=100)
    initial_inventory: list[InventorySeed] = Field(default_factory=list, max_length=100)
    initial_resources: list[ResourceSeed] = Field(default_factory=list, max_length=100)


class TurnRequest(StrictModel):
    request_id: str = Field(min_length=8, max_length=100)
    text: str = Field(min_length=1, max_length=8000)
    recipient_id: str = Field(default="", max_length=120)
    provider: Literal["mock", "openai", "gemini", "chatgpt_web", "gemini_web"] = "mock"
    visibility: Literal["scene", "private"] = "scene"
    external_response: str = Field(default="", max_length=60000)
    manual_context_hash: str = Field(default="", max_length=64)


class ContextPreviewRequest(StrictModel):
    text: str = Field(default="", max_length=8000)
    recipient_id: str = Field(default="", max_length=120)
    visibility: Literal["scene", "private"] = "scene"


class ManualPromptRequest(ContextPreviewRequest):
    text: str = Field(min_length=1, max_length=8000)
    provider: Literal["chatgpt_web", "gemini_web"]


class LocalCommandRequest(StrictModel):
    text: str = Field(min_length=1, max_length=200)


class ApprovalRequest(StrictModel):
    initial_value: float | None = Field(default=None, ge=0, le=100)



class LocalSettingsUpdate(StrictModel):
    lore_budget_chars: int = Field(ge=500, le=12000)
