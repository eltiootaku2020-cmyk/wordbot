"""Small deterministic semantic checks for structured NPC testimony claims.

The parser is deliberately conservative: it recognizes a compact, explicit
Spanish/English state-assertion grammar and returns None for unsupported text.
It never decides which report is true. The resulting relation is a candidate
for an individual character to review, not a world-state mutation.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Mapping


_VALUE_ALIASES = {
    "intacto": "intact", "intacta": "intact", "intactos": "intact", "intactas": "intact",
    "integro": "intact", "integra": "intact", "entero": "intact", "entera": "intact",
    "intact": "intact", "whole": "intact",
    "destruido": "destroyed", "destruida": "destroyed", "derrumbado": "destroyed",
    "derrumbada": "destroyed", "demolido": "destroyed", "demolida": "destroyed",
    "destroyed": "destroyed", "demolished": "destroyed",
    "danado": "damaged", "danada": "damaged", "roto": "damaged", "rota": "damaged",
    "agrietado": "damaged", "agrietada": "damaged", "damaged": "damaged", "broken": "damaged",
    "abierto": "open", "abierta": "open", "open": "open",
    "cerrado": "closed", "cerrada": "closed", "closed": "closed",
    "presente": "present", "present": "present",
    "ausente": "absent", "absent": "absent",
    "vivo": "alive", "viva": "alive", "alive": "alive",
    "muerto": "dead", "muerta": "dead", "dead": "dead",
    "encendido": "on", "encendida": "on", "on": "on",
    "apagado": "off", "apagada": "off", "off": "off",
}

_INCOMPATIBLE_VALUES = {
    frozenset(("intact", "damaged")),
    frozenset(("intact", "destroyed")),
    frozenset(("open", "closed")),
    frozenset(("present", "absent")),
    frozenset(("alive", "dead")),
    frozenset(("on", "off")),
}

_TIME_SCOPES = {
    "dawn": ("al amanecer", "at dawn", "al alba"),
    "morning": ("por la manana", "durante la manana", "esta manana", "hoy por la manana", "in the morning", "this morning"),
    "afternoon": ("por la tarde", "durante la tarde", "esta tarde", "hoy por la tarde", "in the afternoon", "this afternoon"),
    "evening": ("al anochecer", "por la noche", "durante la noche", "esta noche", "in the evening", "at night", "tonight"),
}
_TIME_INTERVALS = {
    "dawn": (300, 420),
    "morning": (360, 720),
    "afternoon": (720, 1080),
    "evening": (1080, 1440),
}

_STATE_VERBS = (
    "se encontraba", "estaban", "estaba", "estuvieron", "estuvo",
    "se encontraba", "esta", "es", "was", "were", "is",
)
_ARTICLES = {"el", "la", "los", "las", "un", "una", "unos", "unas", "the", "a", "an"}
_LOCATION_PREFIXES = ("en el ", "en la ", "en los ", "en las ", "en ", "within ", "inside ", "at ")


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value).casefold())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _clean_phrase(value: str) -> str:
    words = re.findall(r"[a-z0-9]+", _fold(value))
    while words and words[0] in _ARTICLES:
        words.pop(0)
    return " ".join(words).strip()


def _extract_scope(text: str, markers: Mapping[str, tuple[str, ...]]) -> tuple[str, str]:
    for key, variants in markers.items():
        for marker in sorted(variants, key=len, reverse=True):
            match = re.search(r"\b" + re.escape(marker) + r"\b", text)
            if match:
                return key, (text[:match.start()] + " " + text[match.end():]).strip()
    return "", text


def parse_claim_text(text: str) -> dict[str, Any] | None:
    """Parse only a supported single state assertion; unknown wording stays unknown."""
    if not isinstance(text, str) or not text.strip() or len(text) > 600:
        return None
    folded = _fold(text).strip()
    folded = re.sub(r"^[\s¿¡\"'«»]+|[\s.!?¿¡\"'«»]+$", "", folded)
    time_scope, folded = _extract_scope(folded, _TIME_SCOPES)
    folded = re.sub(r"\s+", " ", folded).strip()

    verb_pattern = "|".join(re.escape(verb) for verb in sorted(set(_STATE_VERBS), key=len, reverse=True))
    match = re.match(
        rf"^(?P<subject>[a-z0-9][a-z0-9 '\\-]{{0,90}}?)\s+(?P<pre_negation>no\s+|not\s+)?(?P<verb>{verb_pattern})\s+(?P<tail>.+)$",
        folded,
    )
    if not match:
        return None

    subject = _clean_phrase(match.group("subject"))
    tail = match.group("tail").strip(" .!?")
    if not subject or not tail:
        return None

    negated = bool(match.group("pre_negation"))
    negative = re.match(r"^(?:no|not)\s+", tail)
    if negative:
        negated = True
        tail = tail[negative.end():]

    value_match = re.match(r"^(?P<value>[a-z]+)\b(?P<rest>.*)$", tail)
    if not value_match:
        return None
    value_token = value_match.group("value")
    value = _VALUE_ALIASES.get(value_token)
    if not value:
        return None
    rest = value_match.group("rest").strip(" .!?")

    location = ""
    if rest:
        for prefix in _LOCATION_PREFIXES:
            if rest.startswith(prefix):
                location = _clean_phrase(rest[len(prefix):])
                rest = ""
                break
    # Other qualifiers are not guessed or silently discarded.
    if rest:
        return None

    return {
        "parse_version": 1,
        "subject": subject,
        "predicate": "state",
        "value": value,
        "negated": negated,
        "time_scope": time_scope,
        "location_scope": location,
        "source_text": text.strip(),
    }


def compare_claims(
    left: Mapping[str, Any] | None,
    right: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return a conservative semantic relation; never identify a truthful source."""
    if not isinstance(left, Mapping) or not isinstance(right, Mapping):
        return {"relation": "unstructured", "comparable": False, "reason": "Una o ambas frases no encajan en la gramática local admitida."}
    if left.get("subject") != right.get("subject") or left.get("predicate") != right.get("predicate"):
        return {"relation": "different_claim", "comparable": False, "reason": "Las afirmaciones no comparten sujeto y propiedad."}

    left_time, right_time = str(left.get("time_scope") or ""), str(right.get("time_scope") or "")
    if bool(left_time) != bool(right_time):
        return {"relation": "insufficient_context", "comparable": False, "reason": "Solo una afirmación especifica el periodo."}
    if left_time and right_time:
        left_interval = _TIME_INTERVALS.get(left_time)
        right_interval = _TIME_INTERVALS.get(right_time)
        if not left_interval or not right_interval:
            return {"relation": "insufficient_context", "comparable": False, "reason": "El periodo no puede compararse con seguridad."}
        if max(left_interval[0], right_interval[0]) >= min(left_interval[1], right_interval[1]):
            return {"relation": "different_time", "comparable": False, "reason": "Las afirmaciones se refieren a periodos distintos."}

    left_location = str(left.get("location_scope") or "")
    right_location = str(right.get("location_scope") or "")
    if bool(left_location) != bool(right_location):
        return {"relation": "insufficient_context", "comparable": False, "reason": "Solo una afirmación especifica el lugar."}
    if left_location and right_location and left_location != right_location:
        return {"relation": "different_location", "comparable": False, "reason": "Las afirmaciones se refieren a lugares distintos."}

    left_value, right_value = str(left.get("value") or ""), str(right.get("value") or "")
    left_negated, right_negated = bool(left.get("negated")), bool(right.get("negated"))
    if not left_value or not right_value:
        return {"relation": "insufficient_context", "comparable": False, "reason": "Falta el valor afirmado."}

    conflict = False
    if left_value == right_value:
        conflict = left_negated != right_negated
    elif not left_negated and not right_negated:
        conflict = frozenset((left_value, right_value)) in _INCOMPATIBLE_VALUES

    if conflict:
        return {
            "relation": "possible_conflict",
            "comparable": True,
            "reason": "Mismo sujeto, propiedad, periodo y lugar con valores lógicamente incompatibles.",
        }
    return {
        "relation": "compatible",
        "comparable": True,
        "reason": "Las afirmaciones no expresan valores incompatibles dentro del alcance comparado.",
    }


def classify_evidence_origin(
    transmission_kind: str,
    source_event_kind: str,
    *,
    provenance_complete: bool,
    parent_transmission_id: str = "",
) -> str:
    """Classify only evidence types explicitly represented in the event ledger."""
    if not provenance_complete:
        return "unknown"
    if transmission_kind == "rumor" or parent_transmission_id:
        return "relayed_rumor"
    if source_event_kind == "observation":
        return "direct_observation"
    if source_event_kind == "physical_evidence":
        return "registered_physical_evidence"
    if source_event_kind == "document":
        return "registered_document"
    if transmission_kind == "testimony":
        return "received_testimony"
    return "unknown"


def classify_source_independence(
    left_root_id: str,
    right_root_id: str,
    *,
    left_complete: bool,
    right_complete: bool,
    left_originator_id: str = "",
    right_originator_id: str = "",
    left_source_event_id: str = "",
    right_source_event_id: str = "",
) -> str:
    """Count an originator once even when their account was sent through two roots."""
    if (
        not left_complete or not right_complete
        or not left_root_id or not right_root_id
        or not left_originator_id or not right_originator_id
        or not left_source_event_id or not right_source_event_id
    ):
        return "unknown"
    if left_root_id == right_root_id:
        return "same_lineage"
    if left_source_event_id != right_source_event_id:
        return "unknown"
    return "same_lineage" if left_originator_id == right_originator_id else "independent"


def analyze_report_pair(
    left_text: str,
    right_text: str,
    *,
    left_root_id: str = "",
    right_root_id: str = "",
    left_originator_id: str = "",
    right_originator_id: str = "",
    left_source_event_id: str = "",
    right_source_event_id: str = "",
    left_provenance_complete: bool = False,
    right_provenance_complete: bool = False,
) -> dict[str, Any]:
    left_claim = parse_claim_text(left_text)
    right_claim = parse_claim_text(right_text)
    relation = compare_claims(left_claim, right_claim)
    independence = classify_source_independence(
        left_root_id, right_root_id,
        left_complete=left_provenance_complete,
        right_complete=right_provenance_complete,
        left_originator_id=left_originator_id,
        right_originator_id=right_originator_id,
        left_source_event_id=left_source_event_id,
        right_source_event_id=right_source_event_id,
    )
    if relation["relation"] == "possible_conflict" and independence == "same_lineage":
        relation = {
            "relation": "same_source_possible_conflict",
            "comparable": True,
            "reason": "Las versiones discrepan, pero ambas descienden de una misma transmisión original.",
        }
    return {
        **relation,
        "left_claim": left_claim,
        "right_claim": right_claim,
        "source_independence": independence,
        "independent_corroboration_count": 2 if independence == "independent" else (1 if independence == "same_lineage" else None),
        "is_truth_finding": False,
    }
