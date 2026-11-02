"""Data-driven, deterministic NPC decision scoring.

This module does not narrate dialogue or execute world effects. It ranks feasible
actions for one entity from that entity's own traits, needs, goals, emotions,
focus, capabilities and relationships. Unknown values stay unknown: they do not
silently become zero or "neutral".
"""
from __future__ import annotations

import math
from copy import deepcopy
from typing import Any, Iterable, Mapping


PROFILE_VERSION = 1
MAX_TRAITS = 80
MAX_NEEDS = 80
MAX_EMOTIONS = 200
MAX_GOALS = 100
MAX_ACTIONS = 500
MAX_PATTERNS = 500
FOCUS_TYPES = {
    "self", "entity", "group", "place", "object", "task", "threat",
    "knowledge", "event", "resource",
}


class BehaviorValidationError(ValueError):
    """Raised when a profile, action or pattern catalog is malformed."""


def _number(value: Any, label: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BehaviorValidationError(f"{label} must be a number")
    result = float(value)
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise BehaviorValidationError(f"{label} must be between {minimum} and {maximum}")
    return result


def _text(value: Any, label: str, maximum: int = 120, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise BehaviorValidationError(f"{label} must be text")
    result = value.strip()
    if (not result and not allow_empty) or len(result) > maximum:
        raise BehaviorValidationError(f"{label} must contain 1-{maximum} characters")
    return result


def _string_list(value: Any, label: str, *, maximum_items: int = 80) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum_items:
        raise BehaviorValidationError(f"{label} must be a list of at most {maximum_items} strings")
    result = [_text(item, label) for item in value]
    if len(result) != len(set(result)):
        raise BehaviorValidationError(f"{label} cannot contain duplicates")
    return result


def _number_map(
    value: Any, label: str, minimum: float, maximum: float, *, allow_unknown: bool = False
) -> dict[str, float | None]:
    if not isinstance(value, dict) or len(value) > 120:
        raise BehaviorValidationError(f"{label} must be an object with at most 120 entries")
    result: dict[str, float | None] = {}
    for raw_key, raw_value in value.items():
        key = _text(raw_key, f"{label} key")
        if raw_value is None and allow_unknown:
            result[key] = None
        else:
            result[key] = _number(raw_value, f"{label}.{key}", minimum, maximum)
    return result


def validate_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and detach a per-entity behavior profile.

    Traits, needs, emotions, goals, focus, capabilities and resources are
    independent per entity. Missing/None needs and traits are not treated as
    zero. Relationships are directed: A→B is not copied to B→A.
    """
    if not isinstance(profile, Mapping):
        raise BehaviorValidationError("profile must be an object")
    allowed = {
        "schema_version", "traits", "needs", "emotions", "goals", "focus",
        "capabilities", "resources", "relationships",
    }
    extras = set(profile) - allowed
    if extras:
        raise BehaviorValidationError(f"Unsupported profile fields: {', '.join(sorted(extras))}")
    version = profile.get("schema_version", PROFILE_VERSION)
    if version != PROFILE_VERSION:
        raise BehaviorValidationError("Unsupported behavior profile version")

    traits = _number_map(profile.get("traits", {}), "traits", 0, 100, allow_unknown=True)
    needs = _number_map(profile.get("needs", {}), "needs", 0, 100, allow_unknown=True)
    if len(traits) > MAX_TRAITS or len(needs) > MAX_NEEDS:
        raise BehaviorValidationError("Too many trait or need values")

    raw_emotions = profile.get("emotions", [])
    if not isinstance(raw_emotions, list) or len(raw_emotions) > MAX_EMOTIONS:
        raise BehaviorValidationError(f"emotions must be a list of at most {MAX_EMOTIONS} entries")
    emotions: list[dict[str, Any]] = []
    for item in raw_emotions:
        if not isinstance(item, Mapping):
            raise BehaviorValidationError("Each emotion must be an object")
        emotions.append({
            "kind": _text(item.get("kind"), "emotion.kind", 80),
            "intensity": _number(item.get("intensity"), "emotion.intensity", 0, 100),
            "decay_per_hour": _number(item.get("decay_per_hour", 0), "emotion.decay_per_hour", 0, 100),
            "target_id": _text(item.get("target_id", ""), "emotion.target_id", 120, allow_empty=True),
            "source_event_id": _text(item.get("source_event_id", ""), "emotion.source_event_id", 120, allow_empty=True),
        })

    raw_goals = profile.get("goals", [])
    if not isinstance(raw_goals, list) or len(raw_goals) > MAX_GOALS:
        raise BehaviorValidationError(f"goals must be a list of at most {MAX_GOALS} entries")
    goals: list[dict[str, Any]] = []
    seen_goal_ids: set[str] = set()
    for item in raw_goals:
        if not isinstance(item, Mapping):
            raise BehaviorValidationError("Each goal must be an object")
        goal_id = _text(item.get("goal_id"), "goal.goal_id")
        if goal_id in seen_goal_ids:
            raise BehaviorValidationError("Goal ids must be unique per entity")
        seen_goal_ids.add(goal_id)
        status = item.get("status", "active")
        if status not in {"active", "paused", "completed", "abandoned"}:
            raise BehaviorValidationError("Invalid goal status")
        goals.append({
            "goal_id": goal_id,
            "priority": _number(item.get("priority", 50), "goal.priority", 0, 100),
            "tags": _string_list(item.get("tags", []), "goal.tags", maximum_items=40),
            "status": status,
            "target_id": _text(item.get("target_id", ""), "goal.target_id", 120, allow_empty=True),
        })

    focus_raw = profile.get("focus")
    focus = None
    if focus_raw is not None:
        if not isinstance(focus_raw, Mapping):
            raise BehaviorValidationError("focus must be an object or null")
        focus_kind = _text(focus_raw.get("kind"), "focus.kind", 40)
        if focus_kind not in FOCUS_TYPES:
            raise BehaviorValidationError("Unsupported focus kind")
        focus = {
            "kind": focus_kind,
            "target_id": _text(focus_raw.get("target_id", ""), "focus.target_id", 120, allow_empty=True),
            "salience": _number(focus_raw.get("salience", 50), "focus.salience", 0, 100),
            "tags": _string_list(focus_raw.get("tags", []), "focus.tags", maximum_items=40),
        }

    raw_relationships = profile.get("relationships", {})
    if not isinstance(raw_relationships, Mapping) or len(raw_relationships) > 200:
        raise BehaviorValidationError("relationships must be an object keyed by target entity id")
    relationships: dict[str, dict[str, float | None]] = {}
    for target_id, axes in raw_relationships.items():
        target = _text(target_id, "relationship target")
        if not isinstance(axes, Mapping):
            raise BehaviorValidationError("Each directed relationship must contain an object of axes")
        relationships[target] = _number_map(axes, f"relationships.{target}", 0, 100, allow_unknown=True)

    resources = _number_map(profile.get("resources", {}), "resources", 0, 1_000_000)
    capabilities = _string_list(profile.get("capabilities", []), "capabilities", maximum_items=200)
    return {
        "schema_version": PROFILE_VERSION,
        "traits": traits,
        "needs": needs,
        "emotions": emotions,
        "goals": goals,
        "focus": focus,
        "capabilities": capabilities,
        "resources": resources,
        "relationships": relationships,
    }


def validate_action(action: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one reusable action template in a world-specific catalog."""
    if not isinstance(action, Mapping):
        raise BehaviorValidationError("Each action definition must be an object")
    action_id = _text(action.get("action_id"), "action.action_id")
    base_priority = _number(action.get("base_priority", 0), "action.base_priority", -100, 100)
    duration = action.get("duration_minutes", 0)
    if isinstance(duration, bool) or not isinstance(duration, int) or not 0 <= duration <= 10080:
        raise BehaviorValidationError("action.duration_minutes must be an integer from 0 to 10080")
    risk = _number(action.get("risk_level", 0), "action.risk_level", 0, 100)
    tags = _string_list(action.get("tags", []), "action.tags", maximum_items=40)
    required_capabilities = _string_list(
        action.get("required_capabilities", []), "action.required_capabilities", maximum_items=40
    )
    focus_types = _string_list(action.get("focus_types", []), "action.focus_types", maximum_items=20)
    if any(item not in FOCUS_TYPES for item in focus_types):
        raise BehaviorValidationError("Action contains an unsupported focus type")
    conditions = action.get("required_conditions", {})
    if not isinstance(conditions, Mapping) or len(conditions) > 40:
        raise BehaviorValidationError("action.required_conditions must be an object")
    if any(not isinstance(key, str) or not isinstance(value, bool) for key, value in conditions.items()):
        raise BehaviorValidationError("Action conditions must map names to booleans")
    return {
        "action_id": action_id,
        "category": _text(action.get("category", "general"), "action.category", 60),
        "base_priority": base_priority,
        "tags": tags,
        "required_capabilities": required_capabilities,
        "required_conditions": dict(conditions),
        "need_relief": _number_map(action.get("need_relief", {}), "action.need_relief", 0, 1),
        "trait_affinity": _number_map(action.get("trait_affinity", {}), "action.trait_affinity", -1, 1),
        "emotion_modifiers": _number_map(action.get("emotion_modifiers", {}), "action.emotion_modifiers", -1, 1),
        "relationship_modifiers": _number_map(
            action.get("relationship_modifiers", {}), "action.relationship_modifiers", -1, 1
        ),
        "focus_types": focus_types,
        "resource_costs": _number_map(action.get("resource_costs", {}), "action.resource_costs", 0, 1_000_000),
        "duration_minutes": duration,
        "risk_level": risk,
    }


def validate_pattern(pattern: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one composable behavior pattern; patterns modify, never force, actions."""
    if not isinstance(pattern, Mapping):
        raise BehaviorValidationError("Each behavior pattern must be an object")
    focus_types = _string_list(pattern.get("required_focus_types", []), "pattern.required_focus_types", maximum_items=20)
    if any(item not in FOCUS_TYPES for item in focus_types):
        raise BehaviorValidationError("Pattern contains an unsupported focus type")
    action_ids = _string_list(pattern.get("action_ids", []), "pattern.action_ids", maximum_items=MAX_ACTIONS)
    action_tags = _string_list(pattern.get("action_tags", []), "pattern.action_tags", maximum_items=40)
    return {
        "pattern_id": _text(pattern.get("pattern_id"), "pattern.pattern_id"),
        "bonus": _number(pattern.get("bonus", 0), "pattern.bonus", -50, 50),
        "action_ids": action_ids,
        "action_tags": action_tags,
        "required_traits": _number_map(pattern.get("required_traits", {}), "pattern.required_traits", 0, 100),
        "required_needs": _number_map(pattern.get("required_needs", {}), "pattern.required_needs", 0, 100),
        "required_emotions": _number_map(pattern.get("required_emotions", {}), "pattern.required_emotions", 0, 100),
        "required_focus_types": focus_types,
    }


def _pattern_matches(
    pattern: Mapping[str, Any], profile: Mapping[str, Any], action: Mapping[str, Any]
) -> bool:
    if pattern["action_ids"] and action["action_id"] not in pattern["action_ids"]:
        return False
    if pattern["action_tags"] and not set(pattern["action_tags"]).intersection(action["tags"]):
        return False
    for trait, minimum in pattern["required_traits"].items():
        current = profile["traits"].get(trait)
        if current is None or current < minimum:
            return False
    for need, minimum in pattern["required_needs"].items():
        current = profile["needs"].get(need)
        if current is None or current < minimum:
            return False
    current_focus = profile["focus"]
    if pattern["required_focus_types"] and (
        current_focus is None or current_focus["kind"] not in pattern["required_focus_types"]
    ):
        return False
    if pattern["required_emotions"]:
        intensities: dict[str, float] = {}
        for emotion in profile["emotions"]:
            intensities[emotion["kind"]] = max(
                intensities.get(emotion["kind"], 0), emotion["intensity"]
            )
        for kind, minimum in pattern["required_emotions"].items():
            if intensities.get(kind, 0) < minimum:
                return False
    return True


def rank_actions(
    profile: Mapping[str, Any],
    actions: Iterable[Mapping[str, Any]],
    patterns: Iterable[Mapping[str, Any]] = (),
    *,
    context: Mapping[str, Any] | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return feasible actions ordered by deterministic utility score.

    The result is a proposal list only. It does not spend resources, move an
    entity, update relationships, advance the clock or create story events.
    """
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise BehaviorValidationError("limit must be an integer from 1 to 100")
    state = validate_profile(profile)
    context = context or {}
    if not isinstance(context, Mapping):
        raise BehaviorValidationError("context must be an object")
    conditions = context.get("conditions", {})
    if not isinstance(conditions, Mapping):
        raise BehaviorValidationError("context.conditions must be an object")
    available_minutes = context.get("available_minutes")
    if available_minutes is not None:
        available_minutes = _number(available_minutes, "context.available_minutes", 0, 10080)
    target_id = context.get("target_entity_id", "")
    if target_id:
        target_id = _text(target_id, "context.target_entity_id")
    catalog_actions = [validate_action(item) for item in actions]
    catalog_patterns = [validate_pattern(item) for item in patterns]
    if len(catalog_actions) > MAX_ACTIONS or len(catalog_patterns) > MAX_PATTERNS:
        raise BehaviorValidationError("Action or pattern catalog exceeds its configured limit")
    action_ids = [item["action_id"] for item in catalog_actions]
    pattern_ids = [item["pattern_id"] for item in catalog_patterns]
    if len(action_ids) != len(set(action_ids)) or len(pattern_ids) != len(set(pattern_ids)):
        raise BehaviorValidationError("Action and pattern ids must be unique within their catalogs")

    scores: list[dict[str, Any]] = []
    for action in catalog_actions:
        reasons: list[str] = []
        if not set(action["required_capabilities"]).issubset(state["capabilities"]):
            continue
        if available_minutes is not None and action["duration_minutes"] > available_minutes:
            continue
        if any(conditions.get(key) is not expected for key, expected in action["required_conditions"].items()):
            continue
        if any(state["resources"].get(key, 0) < cost for key, cost in action["resource_costs"].items()):
            continue

        score = action["base_priority"]
        for need, relief in action["need_relief"].items():
            urgency = state["needs"].get(need)
            if urgency is not None and relief:
                score += urgency * relief * 0.25
                reasons.append(f"need:{need}")
        for trait, affinity in action["trait_affinity"].items():
            value = state["traits"].get(trait)
            if value is not None and affinity:
                score += ((value - 50) / 50) * affinity * 12
                reasons.append(f"trait:{trait}")
        active_goal_tags = {
            tag
            for goal in state["goals"] if goal["status"] == "active"
            for tag in goal["tags"]
        }
        overlap = active_goal_tags.intersection(action["tags"])
        if overlap:
            best_priority = max(
                goal["priority"] for goal in state["goals"]
                if goal["status"] == "active" and overlap.intersection(goal["tags"])
            )
            score += best_priority * 0.25
            reasons.append("goal:" + ",".join(sorted(overlap)))
        focus = state["focus"]
        if focus is not None:
            if focus["kind"] in action["focus_types"]:
                score += focus["salience"] * 0.15
                reasons.append(f"focus:{focus['kind']}")
            elif set(focus["tags"]).intersection(action["tags"]):
                score += focus["salience"] * 0.1
                reasons.append("focus:tag-match")

        emotion_intensities: dict[str, float] = {}
        for emotion in state["emotions"]:
            emotion_intensities[emotion["kind"]] = max(
                emotion_intensities.get(emotion["kind"], 0), emotion["intensity"]
            )
        for kind, modifier in action["emotion_modifiers"].items():
            intensity = emotion_intensities.get(kind)
            if intensity is not None and modifier:
                score += intensity * modifier * 0.15
                reasons.append(f"emotion:{kind}")

        if target_id and target_id in state["relationships"]:
            for axis, modifier in action["relationship_modifiers"].items():
                value = state["relationships"][target_id].get(axis)
                if value is not None and modifier:
                    score += ((value - 50) / 50) * modifier * 8
                    reasons.append(f"relationship:{axis}")

        risk_tolerance = state["traits"].get("risk_tolerance")
        if risk_tolerance is not None and action["risk_level"]:
            score -= action["risk_level"] * (1 - risk_tolerance / 100) * 0.2
            reasons.append("risk_tolerance")

        matched_patterns = [
            pattern for pattern in catalog_patterns
            if _pattern_matches(pattern, state, action)
        ]
        if matched_patterns:
            score += sum(pattern["bonus"] for pattern in matched_patterns)
            reasons.extend(f"pattern:{pattern['pattern_id']}" for pattern in matched_patterns)

        scores.append({
            "action_id": action["action_id"],
            "category": action["category"],
            "score": round(score, 4),
            "duration_minutes": action["duration_minutes"],
            "risk_level": action["risk_level"],
            "reason_codes": sorted(set(reasons)),
            "matched_patterns": sorted(pattern["pattern_id"] for pattern in matched_patterns),
        })

    scores.sort(key=lambda item: (-item["score"], item["action_id"]))
    for index, item in enumerate(scores[:limit], start=1):
        item["rank"] = index
    return scores[:limit]


def rank_focuses(
    profile: Mapping[str, Any], candidates: Iterable[Mapping[str, Any]], *, limit: int = 5
) -> list[dict[str, Any]]:
    """Score attention targets using goals, emotion targets and candidate salience."""
    state = validate_profile(profile)
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 50:
        raise BehaviorValidationError("limit must be an integer from 1 to 50")
    goals = [goal for goal in state["goals"] if goal["status"] == "active"]
    results: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise BehaviorValidationError("Each focus candidate must be an object")
        kind = _text(candidate.get("kind"), "focus candidate kind", 40)
        if kind not in FOCUS_TYPES:
            raise BehaviorValidationError("Unsupported candidate focus kind")
        target_id = _text(candidate.get("target_id", ""), "focus candidate target", 120, allow_empty=True)
        key = (kind, target_id)
        if key in seen:
            raise BehaviorValidationError("Focus candidates must be unique by kind and target")
        seen.add(key)
        tags = _string_list(candidate.get("tags", []), "focus candidate tags", maximum_items=40)
        score = _number(candidate.get("salience", 0), "focus candidate salience", 0, 100)
        matched_goals = [goal for goal in goals if set(goal["tags"]).intersection(tags)]
        if matched_goals:
            score += max(goal["priority"] for goal in matched_goals) * 0.2
        matched_emotions = [
            emotion for emotion in state["emotions"]
            if emotion["target_id"] and emotion["target_id"] == target_id
        ]
        if matched_emotions:
            score += max(emotion["intensity"] for emotion in matched_emotions) * 0.15
        current = state["focus"]
        if current is not None and current["kind"] == kind and current["target_id"] == target_id:
            score += current["salience"] * 0.05
        results.append({
            "kind": kind,
            "target_id": target_id,
            "score": round(score, 4),
            "matched_goals": sorted(goal["goal_id"] for goal in matched_goals),
            "matched_emotions": sorted({emotion["kind"] for emotion in matched_emotions}),
        })
    results.sort(key=lambda item: (-item["score"], item["kind"], item["target_id"]))
    return results[:limit]


def advance_emotions(profile: Mapping[str, Any], elapsed_minutes: int) -> dict[str, Any]:
    """Return a profile with emotion intensity decayed by elapsed world time.

    Emotion decay is data-driven. An emotion with decay_per_hour=0 is held
    unchanged until another system changes it; no universal emotional clock is
    assumed. Source event and target provenance are retained.
    """
    if isinstance(elapsed_minutes, bool) or not isinstance(elapsed_minutes, int) or elapsed_minutes < 0:
        raise BehaviorValidationError("elapsed_minutes must be a non-negative integer")
    state = validate_profile(profile)
    for emotion in state["emotions"]:
        decrease = emotion["decay_per_hour"] * elapsed_minutes / 60
        emotion["intensity"] = round(max(0, emotion["intensity"] - decrease), 4)
    state["emotions"] = [emotion for emotion in state["emotions"] if emotion["intensity"] > 0]
    return state


def append_emotion(profile: Mapping[str, Any], emotion: Mapping[str, Any]) -> dict[str, Any]:
    """Record one sourced emotional response without overwriting other feelings."""
    state = validate_profile(profile)
    if len(state["emotions"]) >= MAX_EMOTIONS:
        raise BehaviorValidationError("Entity emotion history reached its configured capacity")
    entry = {
        "kind": emotion.get("kind"),
        "intensity": emotion.get("intensity"),
        "decay_per_hour": emotion.get("decay_per_hour", 0),
        "target_id": emotion.get("target_id", ""),
        "source_event_id": emotion.get("source_event_id", ""),
    }
    # Revalidate the complete profile so every new emotion follows the same contract.
    state["emotions"].append(entry)
    return validate_profile(state)


DEFAULT_ACTIONS: tuple[dict[str, Any], ...] = (
    {"action_id":"observe","category":"perception","base_priority":8,"tags":["observe","evidence"],"focus_types":["threat","place","entity","object","event"],"trait_affinity":{"curiosity":0.5,"caution":0.3}},
    {"action_id":"ask_question","category":"social","base_priority":7,"tags":["social","information"],"focus_types":["entity","knowledge","event"],"trait_affinity":{"curiosity":0.35,"sociability":0.3},"emotion_modifiers":{"fear":-0.35,"confidence":0.25}},
    {"action_id":"listen","category":"social","base_priority":6,"tags":["social","information"],"focus_types":["entity","group","knowledge"],"trait_affinity":{"empathy":0.35,"patience":0.3}},
    {"action_id":"explain","category":"social","base_priority":5,"tags":["social","information","cooperation"],"focus_types":["entity","group"],"trait_affinity":{"sociability":0.25,"honesty":0.3}},
    {"action_id":"approach","category":"movement","base_priority":4,"tags":["movement","social"],"focus_types":["entity","place","resource"],"trait_affinity":{"sociability":0.35,"risk_tolerance":0.2},"emotion_modifiers":{"fear":-0.3}},
    {"action_id":"keep_distance","category":"movement","base_priority":5,"tags":["safety","movement"],"focus_types":["threat","entity"],"trait_affinity":{"caution":0.55,"independence":0.2},"emotion_modifiers":{"fear":0.35}},
    {"action_id":"withdraw","category":"safety","base_priority":4,"tags":["safety","retreat","movement"],"need_relief":{"safety":0.7},"trait_affinity":{"caution":0.55,"risk_tolerance":-0.4},"emotion_modifiers":{"fear":0.4},"risk_level":5},
    {"action_id":"help","category":"social","base_priority":5,"tags":["help","cooperation","care"],"focus_types":["entity","group","task"],"trait_affinity":{"empathy":0.55,"cooperation":0.35},"emotion_modifiers":{"compassion":0.35}},
    {"action_id":"refuse","category":"social","base_priority":3,"tags":["boundaries","independence"],"focus_types":["entity","task"],"trait_affinity":{"independence":0.55,"assertiveness":0.35}},
    {"action_id":"negotiate","category":"social","base_priority":4,"tags":["social","cooperation","resources"],"focus_types":["entity","group","task"],"trait_affinity":{"assertiveness":0.3,"cooperation":0.3}},
    {"action_id":"protect","category":"safety","base_priority":5,"tags":["safety","protect","care"],"focus_types":["threat","entity","group"],"required_capabilities":["protect"],"trait_affinity":{"protectiveness":0.6,"courage":0.25},"emotion_modifiers":{"fear":-0.15}},
    {"action_id":"rest","category":"recovery","base_priority":2,"tags":["recovery","self"],"need_relief":{"fatigue":1.0,"stress":0.25},"focus_types":["self","place"],"required_conditions":{"safe_to_rest":True}},
    {"action_id":"eat","category":"recovery","base_priority":2,"tags":["recovery","food","self"],"need_relief":{"hunger":1.0},"required_conditions":{"food_available":True}},
    {"action_id":"drink","category":"recovery","base_priority":2,"tags":["recovery","water","self"],"need_relief":{"thirst":1.0},"required_conditions":{"water_available":True}},
    {"action_id":"sleep","category":"recovery","base_priority":1,"tags":["recovery","self"],"need_relief":{"fatigue":1.0,"sleep":1.0},"duration_minutes":60,"required_conditions":{"safe_to_sleep":True}},
    {"action_id":"practice","category":"development","base_priority":3,"tags":["training","skill","self"],"focus_types":["self","task"],"required_capabilities":["practice"],"trait_affinity":{"discipline":0.3,"ambition":0.3}},
    {"action_id":"study","category":"development","base_priority":3,"tags":["study","knowledge","self"],"focus_types":["knowledge","task","object"],"required_capabilities":["study"],"trait_affinity":{"curiosity":0.4,"discipline":0.25}},
    {"action_id":"investigate","category":"perception","base_priority":4,"tags":["investigate","evidence","knowledge"],"focus_types":["event","object","place","knowledge"],"required_capabilities":["investigate"],"trait_affinity":{"curiosity":0.5,"analytical":0.4}},
    {"action_id":"guard","category":"safety","base_priority":4,"tags":["safety","protect","watch"],"focus_types":["threat","place","group"],"required_capabilities":["guard"],"trait_affinity":{"caution":0.35,"discipline":0.3}},
    {"action_id":"follow_track","category":"exploration","base_priority":3,"tags":["exploration","track","evidence"],"focus_types":["place","event","knowledge"],"required_capabilities":["tracking"],"trait_affinity":{"curiosity":0.25,"patience":0.2},"risk_level":25},
    {"action_id":"repair","category":"craft","base_priority":2,"tags":["repair","resources","self"],"focus_types":["object","task"],"required_capabilities":["repair"],"resource_costs":{"materials":1}},
    {"action_id":"gather","category":"exploration","base_priority":2,"tags":["resources","exploration"],"focus_types":["place","resource"],"required_capabilities":["gather"],"risk_level":10},
    {"action_id":"travel","category":"movement","base_priority":2,"tags":["movement","travel","goal"],"focus_types":["place","task"],"required_capabilities":["travel"],"risk_level":15},
    {"action_id":"wait","category":"time","base_priority":0,"tags":["wait","self"],"focus_types":["self","event","place"]},
    {"action_id":"share_information","category":"social","base_priority":2,"tags":["social","information","cooperation"],"focus_types":["entity","group"],"trait_affinity":{"honesty":0.35,"cooperation":0.25}},
    {"action_id":"conceal_information","category":"social","base_priority":1,"tags":["social","secrecy","self"],"focus_types":["entity","group"],"trait_affinity":{"caution":0.25,"honesty":-0.4},"emotion_modifiers":{"fear":0.2}},
    {"action_id":"plan","category":"cognition","base_priority":3,"tags":["planning","goal","self"],"focus_types":["task","threat","place"],"trait_affinity":{"discipline":0.3,"analytical":0.35}},
    {"action_id":"mediate","category":"social","base_priority":2,"tags":["social","conflict","cooperation"],"focus_types":["group","entity"],"trait_affinity":{"empathy":0.4,"patience":0.35}},
    {"action_id":"wait_and_watch","category":"perception","base_priority":2,"tags":["observe","safety","wait"],"focus_types":["threat","place"],"trait_affinity":{"patience":0.4,"caution":0.25}},
)


DEFAULT_PATTERNS: tuple[dict[str, Any], ...] = (
    {"pattern_id":"cautious_assessment","bonus":9,"action_tags":["observe","safety"],"required_traits":{"caution":65}},
    {"pattern_id":"curious_inquiry","bonus":8,"action_tags":["investigate","information"],"required_traits":{"curiosity":65}},
    {"pattern_id":"protective_response","bonus":10,"action_tags":["protect","care"],"required_traits":{"protectiveness":60}},
    {"pattern_id":"independent_boundary","bonus":8,"action_ids":["refuse"],"required_traits":{"independence":65}},
    {"pattern_id":"cooperative_bridge","bonus":7,"action_tags":["cooperation","help"],"required_traits":{"cooperation":60}},
    {"pattern_id":"evidence_first","bonus":8,"action_tags":["evidence","investigate"],"required_traits":{"analytical":65}},
    {"pattern_id":"duty_and_discipline","bonus":7,"action_tags":["planning","watch"],"required_traits":{"discipline":65}},
    {"pattern_id":"high_fatigue_recovery","bonus":15,"action_tags":["recovery"],"required_needs":{"fatigue":65}},
    {"pattern_id":"hunger_priority","bonus":16,"action_tags":["food","recovery"],"required_needs":{"hunger":65}},
    {"pattern_id":"thirst_priority","bonus":16,"action_tags":["water","recovery"],"required_needs":{"thirst":65}},
    {"pattern_id":"fearful_distance","bonus":10,"action_tags":["safety","retreat"],"required_emotions":{"fear":45}},
    {"pattern_id":"anger_confrontation","bonus":7,"action_tags":["boundaries","conflict"],"required_emotions":{"anger":55}},
    {"pattern_id":"compassionate_attention","bonus":8,"action_tags":["help","care"],"required_emotions":{"compassion":40}},
    {"pattern_id":"grief_and_withdrawal","bonus":6,"action_tags":["self","recovery"],"required_emotions":{"grief":50}},
    {"pattern_id":"focus_on_threat","bonus":8,"action_tags":["safety","watch"],"required_focus_types":["threat"]},
    {"pattern_id":"focus_on_knowledge","bonus":6,"action_tags":["study","knowledge"],"required_focus_types":["knowledge"]},
    {"pattern_id":"focus_on_goal","bonus":7,"action_tags":["goal","planning"],"required_focus_types":["task"]},
    {"pattern_id":"social_attention","bonus":5,"action_tags":["social"],"required_focus_types":["entity","group"]},
    {"pattern_id":"resource_conservation","bonus":6,"action_tags":["resources"],"required_traits":{"caution":60}},
    {"pattern_id":"patient_observation","bonus":5,"action_tags":["observe","wait"],"required_traits":{"patience":65}},
    {"pattern_id":"ambitious_development","bonus":6,"action_tags":["training","skill"],"required_traits":{"ambition":65}},
    {"pattern_id":"conflict_deescalation","bonus":8,"action_tags":["mediate","cooperation"],"required_traits":{"empathy":65}},
)
