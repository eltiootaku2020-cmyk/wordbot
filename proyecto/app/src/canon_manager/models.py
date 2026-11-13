from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EventProposal(StrictModel):
    ref: str = Field(min_length=1, max_length=40)
    kind: Literal["dialogue", "reaction", "observation", "rumor", "location", "object", "resource", "power", "major_change", "promise", "quest", "injury", "clue", "secret", "deadline", "threat", "timeline_anchor", "knowledge", "tracked_fact", "other"]
    entity_id: str = Field(default="", max_length=120)
    description: str = Field(min_length=1, max_length=1000)
    witness_ids: list[Annotated[str, Field(max_length=120)]] = Field(default_factory=list, max_length=30)
    continuity: bool = False
    importance: int = Field(default=1, ge=1, le=5)


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


class EnvironmentObservationProposal(StrictModel):
    event_ref: str = Field(min_length=1, max_length=40)
    observer_entity_id: str = Field(min_length=1, max_length=120)
    observation_kind: Literal["weather", "local_safety"]
    value_key: str = Field(min_length=1, max_length=40, pattern=r"^[a-z][a-z0-9_-]{0,39}$")
    details: str = Field(default="", max_length=300)
    valid_for_minutes: int = Field(default=60, ge=1, le=240)


class KnowledgeTransmissionProposal(StrictModel):
    event_ref: str = Field(min_length=1, max_length=40)
    source_event_id: str = Field(min_length=1, max_length=80)
    sender_entity_id: str = Field(min_length=1, max_length=120)
    recipient_entity_id: str = Field(min_length=1, max_length=120)
    transmission_kind: Literal["testimony", "rumor"]
    version_text: str = Field(min_length=1, max_length=600)
    parent_transmission_id: str = Field(default="", max_length=80)
    # When forwarding a corrected report, identify the exact approved correction received.
    parent_correction_id: str = Field(default="", max_length=80)


class KnowledgeAssessmentRequest(StrictModel):
    request_id: str = Field(min_length=1, max_length=100)
    assessor_entity_id: str = Field(min_length=1, max_length=120)
    stance: Literal["believes", "uncertain", "doubts", "contradicts"]
    confidence: int = Field(ge=0, le=100, description="Grado de confianza personal del PNJ en la versión, no probabilidad objetiva.")
    evidence_report_id: str = Field(default="", max_length=80)
    evidence_event_id: str = Field(default="", max_length=80)
    # None keeps legacy clients compatible; an explicit empty string means the original version.
    assessed_correction_id: str | None = Field(default=None, max_length=80)
    evidence_correction_id: str | None = Field(default=None, max_length=80)
    rationale: str = Field(min_length=1, max_length=600)


class KnowledgeReasoningRequest(StrictModel):
    request_id: str = Field(min_length=8, max_length=100)
    assessor_entity_id: str = Field(min_length=1, max_length=120)
    left_correction_id: str = Field(default="", max_length=80)
    right_correction_id: str = Field(default="", max_length=80)
    outcome: Literal[
        "believes_left", "believes_right", "uncertain", "contradiction",
        "compatible", "insufficient_information", "no_conclusion",
    ]
    confidence: int = Field(ge=0, le=100)
    rationale: str = Field(min_length=1, max_length=600)


class KnowledgeCorrectionProposal(StrictModel):
    event_ref: str = Field(min_length=1, max_length=40)
    original_transmission_id: str = Field(min_length=1, max_length=80)
    # Empty for the first correction; otherwise references the exact prior version.
    parent_correction_id: str = Field(default="", max_length=80)
    sender_entity_id: str = Field(min_length=1, max_length=120)
    recipient_entity_id: str = Field(min_length=1, max_length=120)
    correction_kind: Literal["corrected", "retracted"]
    replacement_text: str = Field(default="", max_length=600)
    rationale: str = Field(min_length=1, max_length=600)


class NarratorResponse(StrictModel):
    narration: str = Field(min_length=1, max_length=12000)
    events: list[EventProposal] = Field(default_factory=list, max_length=30)
    environment_observations: list[EnvironmentObservationProposal] = Field(default_factory=list, max_length=60)
    knowledge_transmissions: list[KnowledgeTransmissionProposal] = Field(default_factory=list, max_length=30)
    knowledge_corrections: list[KnowledgeCorrectionProposal] = Field(default_factory=list, max_length=30)
    state_changes: list[StateChangeProposal] = Field(default_factory=list, max_length=40)
    elapsed_minutes: int = Field(default=1, ge=0, le=10080)
    movements: list[MovementProposal] = Field(default_factory=list, max_length=20)
    inventory_ops: list[InventoryOperation] = Field(default_factory=list, max_length=40)
    resource_ops: list[ResourceOperation] = Field(default_factory=list, max_length=30)
    power_uses: list[PowerUseProposal] = Field(default_factory=list, max_length=20)
    pending: list[PendingNote] = Field(default_factory=list, max_length=30)


class WorldCreate(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    canon_text: str = Field(default="", max_length=100000)


class WorldTimelineEventCreate(StrictModel):
    external_uid: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=2000)
    scheduled_day: int = Field(ge=1)
    scheduled_minute: int = Field(ge=0, le=1439)
    location: str = Field(default="", max_length=180)


class WorldTimelineEventUpdate(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    scheduled_day: int | None = Field(default=None, ge=1)
    scheduled_minute: int | None = Field(default=None, ge=0, le=1439)
    location: str | None = Field(default=None, max_length=180)
    enabled: bool | None = None


class EnvironmentObservationRequest(StrictModel):
    request_id: str = Field(min_length=8, max_length=120)
    observer_entity_id: str = Field(min_length=1, max_length=120)
    observation_kind: Literal["weather", "local_safety"]
    value_key: str = Field(min_length=1, max_length=40, pattern=r"^[a-z][a-z0-9_-]{0,39}$")
    source_event_id: str = Field(min_length=1, max_length=80)
    details: str = Field(default="", max_length=300)
    valid_for_minutes: int = Field(default=60, ge=1, le=240)


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


class SessionRestoreRequest(StrictModel):
    backup_name: str = Field(min_length=1, max_length=200)
    confirmation: Literal["RESTAURAR"]


class LocalSettingsUpdate(StrictModel):
    lore_budget_chars: int = Field(ge=500, le=12000)


class MapRegionConfigRequest(StrictModel):
    config: dict[str, Any]


class TravelPlanRequest(StrictModel):
    region_id: str = Field(min_length=1, max_length=120)
    destination_x_m: float = Field(allow_inf_nan=False)
    destination_y_m: float = Field(allow_inf_nan=False)
    destination_label: str = Field(default="", max_length=180)


class TravelStepRequest(StrictModel):
    request_id: str = Field(min_length=8, max_length=120)


class BehaviorProfileRequest(StrictModel):
    profile: dict[str, Any]


class BehaviorCatalogRequest(StrictModel):
    schema_version: int = Field(default=1, ge=1, le=1)
    actions: list[dict[str, Any]] = Field(default_factory=list, max_length=500)
    patterns: list[dict[str, Any]] = Field(default_factory=list, max_length=500)


class BehaviorPreviewRequest(StrictModel):
    context: dict[str, Any] = Field(default_factory=dict)
    focus_candidates: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    limit: int = Field(default=10, ge=1, le=100)

class BehaviorAgendaCreateRequest(StrictModel):
    request_id: str = Field(min_length=8, max_length=120)
    action_id: str = Field(min_length=1, max_length=120)
    scheduled_day: int = Field(ge=1)
    scheduled_minute: int = Field(ge=0, le=1439)
    priority: float = Field(default=50, ge=0, le=100, allow_inf_nan=False)
    target_entity_id: str = Field(default="", max_length=120)
    context: dict[str, Any] = Field(default_factory=dict)

