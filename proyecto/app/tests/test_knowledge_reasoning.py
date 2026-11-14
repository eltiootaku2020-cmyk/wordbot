from canon_manager.knowledge_reasoning import (
    analyze_report_pair,
    classify_evidence_origin,
    classify_source_independence,
    compare_claims,
    parse_claim_text,
    normalize_report_text,
    summarize_corroboration_sources,
)


def test_same_bridge_same_morning_with_incompatible_states_is_candidate_conflict():
    result = analyze_report_pair(
        "El puente estaba destruido por la mañana.",
        "El puente estaba intacto por la mañana.",
        left_root_id="origin-a",
        right_root_id="origin-b",
        left_originator_id="witness-a",
        right_originator_id="witness-b",
        left_source_event_id="event-1",
        right_source_event_id="event-1",
        left_provenance_complete=True,
        right_provenance_complete=True,
    )
    assert result["relation"] == "possible_conflict"
    assert result["source_independence"] == "independent"
    assert result["is_truth_finding"] is False


def test_synonyms_and_wording_variants_are_compatible():
    left = parse_claim_text("El puente estaba íntegro por la mañana.")
    right = parse_claim_text("El puente estaba intacto por la mañana.")
    assert left is not None and right is not None
    assert compare_claims(left, right)["relation"] == "compatible"


def test_different_periods_are_not_automatically_a_contradiction():
    result = analyze_report_pair(
        "El puente estaba intacto por la mañana.",
        "El puente estaba destruido por la tarde.",
    )
    assert result["relation"] == "different_time"


def test_natural_spanish_negation_conflicts_with_positive_claim():
    negative = parse_claim_text("El puente no estaba destruido por la mañana.")
    positive = parse_claim_text("El puente estaba destruido por la mañana.")
    assert negative is not None and positive is not None
    assert negative["negated"] is True
    assert compare_claims(negative, positive)["relation"] == "possible_conflict"


def test_two_positive_claims_with_different_incompatible_values_conflict():
    left = parse_claim_text("La puerta estaba abierta por la mañana.")
    right = parse_claim_text("La puerta estaba cerrada por la mañana.")
    assert left is not None and right is not None
    assert compare_claims(left, right)["relation"] == "possible_conflict"


def test_different_locations_are_not_mixed():
    left = parse_claim_text("El puente estaba intacto en el bosque por la mañana.")
    right = parse_claim_text("El puente estaba destruido en la ciudad por la mañana.")
    assert left is not None and right is not None
    assert compare_claims(left, right)["relation"] == "different_location"


def test_different_subjects_are_different_claims():
    left = parse_claim_text("El puente estaba intacto por la mañana.")
    right = parse_claim_text("La torre estaba destruida por la mañana.")
    assert left is not None and right is not None
    assert compare_claims(left, right)["relation"] == "different_claim"


def test_absence_of_a_statement_is_not_converted_into_a_negative_claim():
    assert parse_claim_text("") is None
    assert parse_claim_text("No sé qué ocurrió con el puente.") is None
    result = compare_claims(None, parse_claim_text("El puente estaba intacto por la mañana."))
    assert result["relation"] == "unstructured"


def test_ten_relays_of_the_same_origin_count_as_one_lineage():
    independence = classify_source_independence(
        "original-transmission-1",
        "original-transmission-1",
        left_complete=True,
        left_originator_id="witness-a",
        right_originator_id="witness-a",
        left_source_event_id="event-1",
        right_source_event_id="event-1",
        right_complete=True,
    )
    assert independence == "same_lineage"
    result = analyze_report_pair(
        "El puente estaba intacto por la mañana.",
        "El puente estaba destruido por la mañana.",
        left_root_id="original-transmission-1",
        right_root_id="original-transmission-1",
        left_originator_id="witness-a",
        right_originator_id="witness-a",
        left_source_event_id="event-1",
        right_source_event_id="event-1",
        left_provenance_complete=True,
        right_provenance_complete=True,
    )
    assert result["relation"] == "same_source_possible_conflict"
    assert result["independent_corroboration_count"] == 1


def test_independent_roots_are_counted_as_two_sources():
    assert classify_source_independence(
        "origin-a", "origin-b",
        left_complete=True, right_complete=True,
        left_originator_id="witness-a",
        right_originator_id="witness-b",
        left_source_event_id="event-1",
        right_source_event_id="event-1",
    ) == "independent"
    result = analyze_report_pair(
        "El puente estaba intacto por la mañana.",
        "El puente estaba destruido por la mañana.",
        left_root_id="origin-a",
        right_root_id="origin-b",
        left_originator_id="witness-a",
        right_originator_id="witness-b",
        left_source_event_id="event-1",
        right_source_event_id="event-1",
        left_provenance_complete=True,
        right_provenance_complete=True,
    )
    assert result["independent_corroboration_count"] == 2


def test_incomplete_provenance_is_unknown_not_independent():
    assert classify_source_independence(
        "origin-a", "origin-b",
        left_complete=False, right_complete=True,
    ) == "unknown"


def test_unrecognized_modifiers_fail_closed_instead_of_being_ignored():
    assert parse_claim_text(
        "El puente estaba destruido y había soldados cerca por la mañana."
    ) is None


def test_english_assertions_are_supported_without_external_models():
    left = parse_claim_text("The bridge was destroyed in the morning.")
    right = parse_claim_text("The bridge was intact in the morning.")
    assert left is not None and right is not None
    assert compare_claims(left, right)["relation"] == "possible_conflict"


def test_only_matching_negation_is_a_conflict_when_values_match():
    negative = parse_claim_text("La puerta no estaba abierta por la mañana.")
    positive = parse_claim_text("La puerta estaba abierta por la mañana.")
    assert negative is not None and positive is not None
    assert compare_claims(negative, positive)["relation"] == "possible_conflict"


def test_missing_time_on_one_side_requires_more_context():
    left = parse_claim_text("El puente estaba intacto por la mañana.")
    right = parse_claim_text("El puente estaba destruido.")
    assert left is not None and right is not None
    assert compare_claims(left, right)["relation"] == "insufficient_context"


def test_two_root_transmissions_from_the_same_witness_are_still_one_source():
    assert classify_source_independence(
        "origin-a", "origin-b",
        left_complete=True, right_complete=True,
        left_originator_id="same-witness",
        right_originator_id="same-witness",
        left_source_event_id="same-event",
        right_source_event_id="same-event",
    ) == "same_lineage"


def test_two_different_root_witnesses_on_different_events_are_not_comparable_as_independent():
    assert classify_source_independence(
        "origin-a", "origin-b",
        left_complete=True, right_complete=True,
        left_originator_id="witness-a",
        right_originator_id="witness-b",
        left_source_event_id="event-a",
        right_source_event_id="event-b",
    ) == "unknown"


def test_evidence_origin_distinguishes_recorded_observation_physical_document_testimony_and_rumor():
    assert classify_evidence_origin(
        "testimony", "observation", provenance_complete=True
    ) == "direct_observation"
    assert classify_evidence_origin(
        "testimony", "physical_evidence", provenance_complete=True
    ) == "registered_physical_evidence"
    assert classify_evidence_origin(
        "testimony", "document", provenance_complete=True
    ) == "registered_document"
    assert classify_evidence_origin(
        "testimony", "clue", provenance_complete=True
    ) == "received_testimony"
    assert classify_evidence_origin(
        "rumor", "clue", provenance_complete=True, parent_transmission_id="parent"
    ) == "relayed_rumor"
    assert classify_evidence_origin(
        "testimony", "document", provenance_complete=False
    ) == "unknown"


def test_explicit_action_negation_detects_a_candidate_conflict():
    positive = parse_claim_text("Brina cruzó el puente por la mañana.")
    negative = parse_claim_text("Brina no cruzó el puente por la mañana.")
    assert positive is not None and negative is not None
    assert positive["predicate"] == "action:cross"
    assert positive["value"] == "puente"
    assert compare_claims(positive, negative)["relation"] == "possible_conflict"


def test_same_action_towards_a_different_target_is_a_different_claim():
    left = parse_claim_text("Brina cruzó el puente por la mañana.")
    right = parse_claim_text("Brina cruzó el río por la mañana.")
    assert left is not None and right is not None
    assert compare_claims(left, right)["relation"] == "different_claim"


def test_action_claims_keep_time_and_location_scopes():
    morning = parse_claim_text("Brina cruzó el puente por la mañana.")
    afternoon = parse_claim_text("Brina cruzó el puente por la tarde.")
    forest = parse_claim_text("Brina cruzó el puente en el bosque por la mañana.")
    city = parse_claim_text("Brina cruzó el puente en la ciudad por la mañana.")
    assert morning is not None and afternoon is not None
    assert forest is not None and city is not None
    assert compare_claims(morning, afternoon)["relation"] == "different_time"
    assert compare_claims(forest, city)["relation"] == "different_location"


def test_unknown_action_wording_is_not_guessed():
    assert parse_claim_text("Brina hizo algo extraño junto al puente por la mañana.") is None



def test_textual_match_normalizes_only_case_and_whitespace():
    assert normalize_report_text("  El puente\tESTABA intacto.  ") == normalize_report_text(
        "el puente estaba intacto."
    )
    assert normalize_report_text("El puente estaba intacto.") != normalize_report_text(
        "El puente estaba intacto!"
    )
    assert normalize_report_text("El puente íntegro.") != normalize_report_text(
        "El puente integro."
    )


def test_corroboration_counts_distinct_independent_origins_not_transmissions():
    reports = [
        {
            "source_event_id": "event-1",
            "origin_transmission_id": "root-a",
            "originator_entity_id": "witness-a",
            "provenance_complete": True,
        },
        {
            "source_event_id": "event-1",
            "origin_transmission_id": "root-b",
            "originator_entity_id": "witness-b",
            "provenance_complete": True,
        },
        {
            "source_event_id": "event-1",
            "origin_transmission_id": "root-a",
            "originator_entity_id": "witness-a",
            "provenance_complete": True,
        },
    ]
    result = summarize_corroboration_sources(reports)
    assert result["corroboration_status"] == "independent_sources"
    assert result["source_independence"] == "independent"
    assert result["independent_source_count"] == 2
    assert result["unverified_report_count"] == 0
    assert result["is_truth_finding"] is False


def test_corroboration_does_not_count_two_roots_from_the_same_witness_twice():
    result = summarize_corroboration_sources([
        {
            "source_event_id": "event-1",
            "origin_transmission_id": "root-a",
            "originator_entity_id": "witness-a",
            "provenance_complete": True,
        },
        {
            "source_event_id": "event-1",
            "origin_transmission_id": "root-b",
            "originator_entity_id": "witness-a",
            "provenance_complete": True,
        },
    ])
    assert result["corroboration_status"] == "single_origin"
    assert result["source_independence"] == "same_lineage"
    assert result["independent_source_count"] == 1


def test_corroboration_does_not_inflate_counts_with_incomplete_provenance():
    result = summarize_corroboration_sources([
        {
            "source_event_id": "event-1",
            "origin_transmission_id": "root-a",
            "originator_entity_id": "witness-a",
            "provenance_complete": True,
        },
        {
            "source_event_id": "event-1",
            "origin_transmission_id": "",
            "originator_entity_id": "",
            "provenance_complete": False,
        },
    ])
    assert result["corroboration_status"] == "one_confirmed_origin_with_unverified_reports"
    assert result["source_independence"] == "unknown"
    assert result["independent_source_count"] == 1
    assert result["unverified_report_count"] == 1


def test_corroboration_rejects_mixed_source_events():
    result = summarize_corroboration_sources([
        {
            "source_event_id": "event-1",
            "origin_transmission_id": "root-a",
            "originator_entity_id": "witness-a",
            "provenance_complete": True,
        },
        {
            "source_event_id": "event-2",
            "origin_transmission_id": "root-b",
            "originator_entity_id": "witness-b",
            "provenance_complete": True,
        },
    ])
    assert result["corroboration_status"] == "unknown"
    assert result["independent_source_count"] == 0
