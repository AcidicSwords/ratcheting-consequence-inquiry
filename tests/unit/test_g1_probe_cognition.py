from __future__ import annotations

from datetime import UTC, datetime

import pytest

from rci.claims import BoundArgument
from rci.core import (
    ArtifactRef,
    CancelledOutcome,
    CapturedPayload,
    Decoded,
    EffectAttemptPlan,
    ExternalReturn,
    NoAttemptDisposition,
    ReturnedOutcome,
    RouteSnapshot,
    UnknownResult,
)
from rci.core.effects import CancellationReason, NoAttemptReason
from rci.orchestration import LifecycleVerdict, validate_cognitive_lifecycle
from rci.probes import (
    CognitiveAttemptPlan,
    ComparabilityBridge,
    PredictionSeal,
    ProbeEvent,
    ProbeIdentity,
    Reconstruction,
    RelevanceStatus,
    SemanticChangeOperation,
    SemanticDelta,
    SemanticItem,
    WarrantedChange,
    build_semantic_field,
    compare_probe_events,
    reopen_semantic_item,
)


def artifact(seed: str) -> ArtifactRef:
    character = format(sum(seed.encode()) % 16, "x")
    return ArtifactRef(digest=character * 64, size=len(seed), media_type="application/test")


CAPTURED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def identity(binding_schema_id: str = "binding-schema:1") -> ProbeIdentity:
    return ProbeIdentity(
        question_contract_key="probe@1",
        relational_role="change",
        binding_schema_id=binding_schema_id,
        binding_revision="binding:1",
        scope_fingerprint="scope:1",
        comparison_semantics_id="exact-v1",
        applicability_guard_id="always",
        protected_horizon_id="horizon:test",
    )


def event(identifier: str, probe: ProbeIdentity, sequence: int) -> ProbeEvent:
    return ProbeEvent(
        id=identifier,
        probe_identity=probe,
        bound_referents=(BoundArgument(name="subject", value="S"),),
        binding_revision="binding:1",
        state_revision=sequence,
        semantic_field_id=f"field:{sequence}",
        sequence_index=sequence,
    )


def test_probe_identity_is_not_surface_wording_and_requires_bridge() -> None:
    left = event("event:1", identity("schema:1"), 1)
    right = event("event:2", identity("schema:2"), 2)
    assert not compare_probe_events(left, right)
    bridge = ComparabilityBridge(
        from_probe_fingerprint=left.probe_identity.fingerprint,
        to_probe_fingerprint=right.probe_identity.fingerprint,
        comparison_proposition_id="relation:comparable",
        scope_fingerprint="scope:1",
        warrant_lemma_id="lemma:bridge",
    )
    assert compare_probe_events(left, right, bridge=bridge)


def test_unknown_relevance_is_preserved_and_guarded_irrelevance_reopens() -> None:
    unknown = SemanticItem(structure_id="x", relevance=RelevanceStatus.UNDETERMINED)
    irrelevant = SemanticItem(
        structure_id="y",
        relevance=RelevanceStatus.IRRELEVANT,
        irrelevance_warrant_id="lemma:null",
        reopening_condition_id="condition:changed",
    )
    with pytest.raises(ValueError, match="checked consequence-null"):
        build_semantic_field(
            probe_identity=identity(),
            protected_horizon_id="horizon:test",
            items=(unknown, irrelevant),
        )
    field = build_semantic_field(
        probe_identity=identity(),
        protected_horizon_id="horizon:test",
        items=(unknown, irrelevant),
        retrieval_result_ids=("effect-result:retrieval:1",),
        reopening_condition_ids=("condition:changed",),
        authorized_irrelevance_warrant_ids=frozenset(("lemma:null",)),
    )
    assert field.items[0].relevance is RelevanceStatus.UNDETERMINED
    reopened = reopen_semantic_item(irrelevant, condition_id="condition:changed")
    assert reopened.relevance is RelevanceStatus.UNDETERMINED
    assert field.retrieval_result_ids == ("effect-result:retrieval:1",)


def test_core_return_decode_and_cognitive_reconstruction_remain_distinct() -> None:
    route = RouteSnapshot(
        id="route:1",
        definition_id="route-definition:1",
        definition_version="1",
        definition_artifact=artifact("route"),
        backend_id="backend:scripted",
        adapter_id="adapter:scripted",
        adapter_version="1",
        execution_environment_artifact=artifact("environment"),
        request_or_action_digest="e" * 64,
    )
    effect_plan = EffectAttemptPlan(id="attempt:1", request_id="request:1", route=route)
    raw_return = ExternalReturn(
        id="return:1",
        attempt_id=effect_plan.id,
        route_id=route.id,
        capture_boundary="test-native-null",
        capture_encoding="native-null",
        captured_at=CAPTURED_AT,
        raw_payload=CapturedPayload(kind="null"),
    )
    outcome = ReturnedOutcome(
        attempt_id=effect_plan.id,
        route_id=route.id,
        external_return=raw_return,
    )
    decoded = Decoded(
        id="decode:1",
        external_return_id=raw_return.id,
        decoder_id="decoder:1",
        decoder_version="1",
        result=UnknownResult(
            id="result:1",
            semantic_artifact=artifact("semantic-unknown"),
            reason_kind="backend_unknown",
        ),
    )
    plan = CognitiveAttemptPlan(
        id="cognitive-plan:1",
        obligation_id="obligation:1",
        probe_or_action_id="action:test",
        effect_request_id="request:1",
        effect_attempt_plan_id=effect_plan.id,
        source_state_revision=0,
        scope_fingerprint="scope:1",
        planned_sequence=1,
    )
    seal = PredictionSeal(
        id="prediction:1",
        cognitive_plan_id=plan.id,
        probe_or_action_id=plan.probe_or_action_id,
        predicted_return_class="success",
        predicted_consequence="unchanged",
        acceptable_variation=None,
        scope_fingerprint=plan.scope_fingerprint,
        basis_claim_ids=("claim:basis",),
        sealed_sequence=2,
    )
    reconstruction = Reconstruction(
        id="reconstruction:1",
        prior_state_revision=0,
        external_return_id=raw_return.id,
        decode_outcome_ids=(decoded.id,),
        generated_detail_ids=("generated:1",),
        reconstructed_sequence=5,
    )
    delta = SemanticDelta(
        id="delta:1",
        reconstruction_id=reconstruction.id,
        warranted_changes=(
            WarrantedChange(
                change_id="change:1",
                proposition_id="relation:1",
                scope_fingerprint=plan.scope_fingerprint,
                operation=SemanticChangeOperation.ADD,
                warrant_lemma_id="lemma:1",
            ),
        ),
        committed_sequence=6,
    )
    check = validate_cognitive_lifecycle(
        plan=plan,
        effect_plan=effect_plan,
        outcome=outcome,
        seal=seal,
        attempt_sequence=3,
        decode_outcomes=(decoded,),
        reconstruction=reconstruction,
        delta=delta,
    )
    assert check.verdict is LifecycleVerdict.VALID
    assert raw_return.raw_payload.kind == "null"
    assert decoded.result.kind == "unknown"
    assert reconstruction.generated_detail_ids == ("generated:1",)
    assert delta.warranted_changes[0].warrant_lemma_id == "lemma:1"


def test_no_attempt_and_cancelled_are_not_semantic_unknown() -> None:
    no_attempt_plan = CognitiveAttemptPlan(
        id="cognitive-plan:none",
        obligation_id="obligation:1",
        probe_or_action_id="action:test",
        effect_request_id="request:none",
        effect_attempt_plan_id=None,
        source_state_revision=0,
        scope_fingerprint="scope:1",
        planned_sequence=1,
    )
    no_attempt = NoAttemptDisposition(
        id="disposition:1",
        request_id="request:none",
        step_plan_id="step-plan:none",
        reason_kind=NoAttemptReason.POLICY_DENIED,
    )
    assert (
        validate_cognitive_lifecycle(
            plan=no_attempt_plan,
            effect_plan=None,
            outcome=None,
            no_attempt=no_attempt,
        ).verdict
        is LifecycleVerdict.VALID
    )

    route = RouteSnapshot(
        id="route:cancel",
        definition_id="route-definition:cancel",
        definition_version="1",
        definition_artifact=artifact("cancel"),
        backend_id="backend:test",
        adapter_id="adapter:test",
        adapter_version="1",
        execution_environment_artifact=artifact("environment"),
        request_or_action_digest="e" * 64,
    )
    effect_plan = EffectAttemptPlan(id="attempt:cancel", request_id="request:cancel", route=route)
    cancelled_plan = no_attempt_plan.model_copy(
        update={
            "id": "cognitive-plan:cancel",
            "effect_request_id": "request:cancel",
            "effect_attempt_plan_id": effect_plan.id,
        }
    )
    cancelled = CancelledOutcome(
        attempt_id=effect_plan.id,
        route_id=route.id,
        reason_kind=CancellationReason.CALLER_CANCELLED,
    )
    assert (
        validate_cognitive_lifecycle(
            plan=cancelled_plan,
            effect_plan=effect_plan,
            outcome=cancelled,
        ).verdict
        is LifecycleVerdict.VALID
    )
