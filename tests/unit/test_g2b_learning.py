from __future__ import annotations

from rci.learning import (
    ConsolidationPolicy,
    ConsolidationStatus,
    ProbeEvaluationProtocol,
    ProbeSample,
    SemanticFieldPolicy,
    derive_conservative_field,
    select_consolidation_checkpoint,
    stratified_probe_split,
)
from rci.probes import ProbeEvent, ProbeIdentity, RelevanceStatus


def _probe() -> ProbeIdentity:
    return ProbeIdentity(
        question_contract_key="necessity-counterexample@1.0.0",
        relational_role="counterexample",
        binding_schema_id="schema:circuit",
        binding_revision="binding:circuit",
        scope_fingerprint="scope:circuit",
        comparison_semantics_id="comparison:exact",
        applicability_guard_id="always",
        protected_horizon_id="horizon:circuit",
    )


def _episode(identifier: str, sequence: int) -> ProbeEvent:
    probe = _probe()
    return ProbeEvent(
        id=identifier,
        probe_identity=probe,
        bound_referents=(),
        binding_revision=probe.binding_revision,
        state_revision=sequence,
        semantic_field_id="field:circuit",
        sequence_index=sequence,
    )


def test_one_episode_cannot_self_consolidate() -> None:
    probe = _probe()
    checkpoint = select_consolidation_checkpoint(
        checkpoint_id="checkpoint:one",
        policy=ConsolidationPolicy(),
        source_sequence=1,
        scope_fingerprint=probe.scope_fingerprint,
        binding_revision=probe.binding_revision,
        protected_horizon_id=probe.protected_horizon_id,
        probe_observations=(_episode("episode:one", 0),),
        claims=(),
        conflicts=(),
        mismatches=(),
        accepted_counterexample_requests={},
    )
    assert checkpoint.status is ConsolidationStatus.INSUFFICIENT_DIVERSITY


def test_conservative_field_is_stable_bounded_and_never_model_suppressed() -> None:
    probe = _probe()
    safety = tuple(f"safety:{index:02}" for index in reversed(range(20)))
    exceptions = tuple(f"exception:{index:02}" for index in reversed(range(10)))
    dependencies = tuple(f"dependency:{index:02}" for index in reversed(range(10)))
    retrieval = ("retrieved:model-says-irrelevant",)
    left = derive_conservative_field(
        probe_identity=probe,
        source_sequence=7,
        policy=SemanticFieldPolicy(),
        safety_structure_ids=safety,
        exception_structure_ids=exceptions,
        dependency_structure_ids=dependencies,
        retrieval_structure_ids=retrieval,
    )
    right = derive_conservative_field(
        probe_identity=probe,
        source_sequence=7,
        policy=SemanticFieldPolicy(),
        safety_structure_ids=tuple(reversed(safety)),
        exception_structure_ids=tuple(reversed(exceptions)),
        dependency_structure_ids=dependencies,
        retrieval_structure_ids=retrieval,
    )
    assert left == right
    field, required, overflow, _ = left
    assert len(field.items) == 32
    assert len(required) == 40
    assert len(overflow) == 9
    assert all(item.relevance is RelevanceStatus.ACTIVE for item in field.items)


def test_stratified_holdout_is_permutation_stable() -> None:
    samples = tuple(
        ProbeSample(
            observation_id=f"observation:{index}",
            protected_consequence_class_id="off" if index < 4 else "on",
            existing_basis_class_id="same",
            candidate_value_id="zero" if index < 4 else "one",
        )
        for index in range(8)
    )
    forward = stratified_probe_split(samples, ProbeEvaluationProtocol())
    reverse = stratified_probe_split(tuple(reversed(samples)), ProbeEvaluationProtocol())
    assert forward == reverse
    assert {item.protected_consequence_class_id for item in forward[1]} == {"off", "on"}
