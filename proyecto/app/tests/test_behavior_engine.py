import copy

import pytest

from canon_manager.behavior_engine import (
    BehaviorValidationError,
    DEFAULT_ACTIONS,
    DEFAULT_PATTERNS,
    advance_emotions,
    append_emotion,
    rank_actions,
    rank_focuses,
    validate_profile,
)


def profile(**overrides):
    value = {
        "schema_version": 1,
        "traits": {},
        "needs": {},
        "emotions": [],
        "goals": [],
        "focus": None,
        "capabilities": [],
        "resources": {},
        "relationships": {},
    }
    value.update(overrides)
    return value


def action(action_id, **overrides):
    value = {
        "action_id": action_id,
        "category": "test",
        "base_priority": 0,
        "tags": [],
        "required_capabilities": [],
        "required_conditions": {},
        "need_relief": {},
        "trait_affinity": {},
        "emotion_modifiers": {},
        "relationship_modifiers": {},
        "focus_types": [],
        "resource_costs": {},
        "duration_minutes": 0,
        "risk_level": 0,
    }
    value.update(overrides)
    return value


def test_needs_and_traits_produce_different_choices_for_different_entities():
    actions = [
        action("rest", tags=["recovery"], need_relief={"fatigue": 1.0}),
        action("investigate", tags=["knowledge"], trait_affinity={"curiosity": 1.0}),
    ]
    tired = profile(
        needs={"fatigue": 95},
        traits={"curiosity": 10},
    )
    curious = profile(
        needs={"fatigue": 10},
        traits={"curiosity": 95},
    )

    tired_ranking = rank_actions(tired, actions)
    curious_ranking = rank_actions(curious, actions)

    assert tired_ranking[0]["action_id"] == "rest"
    assert curious_ranking[0]["action_id"] == "investigate"


def test_unknown_needs_are_not_silently_treated_as_zero():
    candidate = action("wait", base_priority=12, need_relief={"fatigue": 1.0})
    result = rank_actions(profile(needs={"fatigue": None}), [candidate])

    assert result[0]["score"] == 12
    assert "need:fatigue" not in result[0]["reason_codes"]


def test_capabilities_and_conditions_filter_impossible_actions():
    study = action(
        "study",
        required_capabilities=["study"],
        required_conditions={"book_available": True},
    )

    assert rank_actions(profile(), [study]) == []
    assert rank_actions(
        profile(capabilities=["study"]),
        [study],
        context={"conditions": {"book_available": True}},
    )[0]["action_id"] == "study"
    assert rank_actions(
        profile(capabilities=["study"]),
        [study],
        context={"conditions": {"book_available": False}},
    ) == []


def test_duration_and_resources_filter_actions_without_side_effects():
    candidate = action(
        "repair",
        duration_minutes=40,
        resource_costs={"wood": 2},
    )
    state = profile(resources={"wood": 1})
    original = copy.deepcopy(state)

    assert rank_actions(state, [candidate], context={"available_minutes": 60}) == []
    assert state == original
    state["resources"]["wood"] = 2
    assert rank_actions(state, [candidate], context={"available_minutes": 20}) == []
    assert rank_actions(state, [candidate], context={"available_minutes": 60})


def test_emotions_change_action_scores_but_do_not_overwrite_other_emotions():
    candidate = action("withdraw", tags=["safety"], emotion_modifiers={"fear": 1.0})
    calm = profile(emotions=[])
    frightened = profile(emotions=[{
        "kind": "fear", "intensity": 80, "source_event_id": "ambush-1"
    }])

    assert rank_actions(frightened, [candidate])[0]["score"] > rank_actions(calm, [candidate])[0]["score"]


def test_composable_behavior_pattern_modifies_only_matching_actions():
    candidate = action("investigate", tags=["investigate", "evidence"])
    pattern = {
        "pattern_id": "curious-investigation",
        "bonus": 14,
        "action_tags": ["investigate"],
        "required_traits": {"curiosity": 70},
    }
    curious = profile(traits={"curiosity": 90})
    cautious = profile(traits={"curiosity": 20})

    matched = rank_actions(curious, [candidate], [pattern])[0]
    unmatched = rank_actions(cautious, [candidate], [pattern])[0]

    assert matched["score"] - unmatched["score"] == pytest.approx(14)
    assert matched["matched_patterns"] == ["curious-investigation"]
    assert unmatched["matched_patterns"] == []


def test_goals_and_current_focus_influence_action_ranking():
    candidate = action(
        "protect",
        tags=["protect", "rescue"],
        focus_types=["threat"],
    )
    state = profile(
        goals=[{"goal_id": "protect-villagers", "priority": 90, "tags": ["rescue"]}],
        focus={"kind": "threat", "target_id": "wolf-1", "salience": 80},
    )

    result = rank_actions(state, [candidate])[0]

    assert "goal:rescue" in result["reason_codes"]
    assert "focus:threat" in result["reason_codes"]
    assert result["score"] > 30


def test_relationship_modifiers_are_directed_and_target_specific():
    candidate = action("reassure", relationship_modifiers={"trust": 1.0})
    towards_maelis = profile(relationships={"maelis": {"trust": 90}})
    towards_brina = profile(relationships={"brina": {"trust": 10}})

    high = rank_actions(towards_maelis, [candidate], context={"target_entity_id": "maelis"})[0]
    low = rank_actions(towards_brina, [candidate], context={"target_entity_id": "brina"})[0]
    no_target = rank_actions(towards_maelis, [candidate], context={"target_entity_id": "brina"})[0]

    assert high["score"] > low["score"]
    assert high["score"] > no_target["score"]


def test_focus_ranking_uses_goal_and_emotional_target_without_revealing_facts():
    state = profile(
        goals=[{"goal_id": "find-herbs", "priority": 85, "tags": ["herbs"]}],
        emotions=[{
            "kind": "worry", "intensity": 70,
            "target_id": "brina", "source_event_id": "injury-7",
        }],
    )
    ranked = rank_focuses(state, [
        {"kind": "place", "target_id": "glade", "salience": 10, "tags": ["herbs"]},
        {"kind": "entity", "target_id": "brina", "salience": 20},
    ])

    assert ranked[0]["target_id"] == "brina"
    assert ranked[0]["matched_emotions"] == ["worry"]
    assert {item["target_id"] for item in ranked} == {"glade", "brina"}


def test_emotion_decay_is_per_emotion_and_preserves_source():
    state = profile(emotions=[
        {"kind": "fear", "intensity": 80, "decay_per_hour": 20, "source_event_id": "wolf"},
        {"kind": "gratitude", "intensity": 50, "decay_per_hour": 0, "source_event_id": "gift"},
    ])

    advanced = advance_emotions(state, 90)

    assert advanced["emotions"][0]["intensity"] == 50
    assert advanced["emotions"][0]["source_event_id"] == "wolf"
    assert advanced["emotions"][1]["intensity"] == 50
    assert state["emotions"][0]["intensity"] == 80


def test_append_emotion_keeps_multiple_causes_instead_of_overwriting():
    state = profile(emotions=[{
        "kind": "fear", "intensity": 30, "source_event_id": "first-sighting"
    }])

    changed = append_emotion(state, {
        "kind": "fear", "intensity": 45, "source_event_id": "second-sighting"
    })

    assert len(changed["emotions"]) == 2
    assert [item["source_event_id"] for item in changed["emotions"]] == [
        "first-sighting", "second-sighting"
    ]


def test_default_catalog_is_composable_not_a_single_interaction():
    assert len(DEFAULT_ACTIONS) >= 25
    assert len(DEFAULT_PATTERNS) >= 20
    state = profile(
        traits={"curiosity": 90, "caution": 85, "discipline": 70},
        needs={"fatigue": 35, "hunger": 15},
        emotions=[{"kind": "fear", "intensity": 30, "source_event_id": "strange-noise"}],
        capabilities=["study", "investigate", "guard", "practice"],
        focus={"kind": "threat", "target_id": "unknown-sound", "salience": 80},
    )
    result = rank_actions(
        state,
        DEFAULT_ACTIONS,
        DEFAULT_PATTERNS,
        context={
            "available_minutes": 45,
            "conditions": {"safe_to_rest": False, "food_available": False, "water_available": True},
        },
        limit=12,
    )

    assert len(result) > 3
    assert len({item["action_id"] for item in result}) == len(result)
    assert any(item["matched_patterns"] for item in result)


def test_scoring_order_is_deterministic_for_ties():
    actions = [action("zeta", base_priority=10), action("alpha", base_priority=10)]
    first = rank_actions(profile(), actions)
    second = rank_actions(profile(), actions)

    assert first == second
    assert [item["action_id"] for item in first] == ["alpha", "zeta"]


def test_invalid_profile_and_catalog_are_rejected():
    with pytest.raises(BehaviorValidationError):
        validate_profile({"traits": {"curiosity": 120}})
    with pytest.raises(BehaviorValidationError):
        validate_profile({"emotions": [{"kind": "fear", "intensity": 101}]})
    with pytest.raises(BehaviorValidationError):
        rank_actions(profile(), [action("duplicate"), action("duplicate")])
    with pytest.raises(BehaviorValidationError):
        rank_actions(profile(), [action("bad", trait_affinity={"curiosity": 2})])
