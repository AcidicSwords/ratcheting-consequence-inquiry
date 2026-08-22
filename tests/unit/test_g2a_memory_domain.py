from __future__ import annotations

from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from rci.core import ArtifactRef
from rci.memory import (
    STRUCTURAL_EXACT_V1,
    ConsequenceEvaluationRoute,
    CostAxis,
    CostCoordinate,
    CostRelation,
    CostVector,
    DirectUseRoute,
    MemoryOwner,
    MemoryReconstructionCandidate,
    OwnedMemoryRef,
    OwnedRecordType,
    ProvisionalRecoveryRoute,
    ReacquisitionChildManifest,
    ReacquisitionInquiryLink,
    ReacquisitionRequest,
    ReacquisitionRoute,
    ReacquisitionScaffold,
    ReconstructionRoute,
    RecoveryBranch,
    RecoveryComparison,
    RecoveryComparisonOutcome,
    RecoveryCompatibilityError,
    RecoveryObservation,
    RecoveryProtocol,
    RetentionPackage,
    RetentionRegistration,
    RetrievalQuery,
    build_memory_reconstruction_set,
    check_recovery_comparison,
    compare_cost_vectors,
    compare_recovery_frontiers,
    derive_recovery_frontier,
    make_owned_memory_ref,
    resolve_owned_memory_ref,
    retrieve,
    structural_index_fingerprint,
)
from rci.warrant import CheckReference

UNIVERSE_HASH = "a" * 64
CONTEXT_DIGEST = "b" * 64
PREFIX_DIGEST = "c" * 64
EVENT_DIGEST = "d" * 64


def check_ref(seed: str) -> CheckReference:
    return CheckReference(
        evidence_id=f"evidence:{seed}",
        checker_verdict_id=f"checker-verdict:{seed}",
    )


def procedure_ref(identifier: str, payload: Any | None = None) -> OwnedMemoryRef:
    return make_owned_memory_ref(
        owner=MemoryOwner.PROCEDURAL,
        record_type=OwnedRecordType.PROBE_IDENTITY,
        record_id=identifier,
        record_schema_version=1,
        record=payload if payload is not None else {"id": identifier},
    )


def axis(identifier: str) -> CostAxis:
    return CostAxis(id=identifier, unit_id="count")


def costs(*, effects: int, probes: int) -> CostVector:
    return CostVector(
        coordinates=(
            CostCoordinate(axis=axis("effects"), numerator=effects),
            CostCoordinate(axis=axis("logical_probes"), numerator=probes),
        )
    )


def protocol(*, evaluator_version: str = "1") -> RecoveryProtocol:
    return RecoveryProtocol(
        id="protocol:circuit-recovery",
        version="1",
        scope_fingerprint="scope:circuit",
        target_competence_id="competence:derive-switch-necessity",
        finite_universe_hash=UNIVERSE_HASH,
        binding_revision="binding:circuit-v1",
        protected_horizon_id="horizon:circuit",
        evaluator_id="evaluator:circuit-exhaustive",
        evaluator_version=evaluator_version,
        evidence_access_id="evidence-access:circuit-table",
        evidence_access_version="1",
        budget_id="budget:circuit-recovery",
        budget_version="1",
        budget=costs(effects=10, probes=10),
        comparison_policy_id="pareto-frontier-coverage-v1",
        comparison_policy_version="1",
        cost_axes=(axis("effects"), axis("logical_probes")),
    )


def registration() -> tuple[RetentionRegistration, dict[str, str]]:
    probe = procedure_ref("probe:necessity-counterexample")
    common: dict[str, Any] = {
        "scope_fingerprint": "scope:circuit",
        "binding_revision": "binding:circuit-v1",
        "protected_horizon_id": "horizon:circuit",
        "source_refs": (probe,),
        "provenance_refs": ("event:g1-circuit",),
    }
    direct = DirectUseRoute(
        id="route:direct",
        present_use_contract_id="contract:direct-circuit",
        **common,
    )
    reconstruction = ReconstructionRoute(
        id="route:reconstruct",
        reconstruction_policy_id="reconstruction:bounded-v1",
        **common,
    )
    consequence = ConsequenceEvaluationRoute(
        id="route:consequence",
        consequence_evaluator_id="evaluator:circuit-exhaustive",
        **common,
    )
    scaffold = ReacquisitionScaffold(
        id="scaffold:circuit",
        scope_fingerprint="scope:circuit",
        binding_revision="binding:circuit-v1",
        protected_horizon_id="horizon:circuit",
        cue_refs=(probe,),
        ordered_probe_ids=(probe.record_id,),
        provenance_refs=("event:g1-circuit",),
    )
    reacquisition = ReacquisitionRoute(
        id="route:reacquire",
        recovery_protocol_id="protocol:circuit-recovery",
        reacquisition_scaffold_id=scaffold.id,
        **common,
    )
    package = RetentionPackage(
        id="retention:circuit",
        scope_fingerprint="scope:circuit",
        binding_revision="binding:circuit-v1",
        protected_horizon_id="horizon:circuit",
        owned_refs=(probe,),
        cue_ids=("cue:switch",),
        tag_ids=("tag:circuit",),
        direct_use_route_ids=(direct.id,),
        reconstruction_route_ids=(reconstruction.id,),
        consequence_evaluation_route_ids=(consequence.id,),
        reacquisition_route_ids=(reacquisition.id,),
        scaffold_ids=(scaffold.id,),
        recovery_protocol_ids=("protocol:circuit-recovery",),
        provenance_refs=("event:g1-circuit",),
    )
    aggregate = RetentionRegistration(
        package=package,
        direct_use_routes=(direct,),
        reconstruction_routes=(reconstruction,),
        consequence_evaluation_routes=(consequence,),
        reacquisition_routes=(reacquisition,),
        scaffolds=(scaffold,),
        recovery_protocols=(protocol(),),
    )
    return aggregate, {probe.key: probe.content_fingerprint}


def query_for(package: RetentionPackage, owned: dict[str, str]) -> RetrievalQuery:
    return RetrievalQuery(
        id="retrieval-query:circuit",
        policy_id=STRUCTURAL_EXACT_V1.id,
        policy_version=STRUCTURAL_EXACT_V1.version,
        scope_fingerprint=package.scope_fingerprint,
        binding_revision=package.binding_revision,
        protected_horizon_id=package.protected_horizon_id,
        source_sequence=12,
        source_index_fingerprint=structural_index_fingerprint((package,), owned),
        record_types=(OwnedRecordType.PROBE_IDENTITY,),
        reference_selectors=package.owned_refs,
        cue_ids=("cue:switch",),
        tag_ids=("tag:circuit",),
        limit=10,
    )


def observation(
    identifier: str,
    *,
    branch: RecoveryBranch,
    vector: CostVector,
    selected_protocol: RecoveryProtocol | None = None,
) -> RecoveryObservation:
    selected_protocol = selected_protocol or protocol()
    coordinate_values = {
        coordinate.axis.id: coordinate.numerator // coordinate.denominator
        for coordinate in vector.coordinates
    }
    return RecoveryObservation(
        id=identifier,
        branch=branch,
        reacquisition_request_id=f"request:{branch.value}",
        child_inquiry_id=f"inquiry:{branch.value}",
        child_prefix_sequence=6,
        child_prefix_digest=PREFIX_DIGEST,
        retention_package_id=(None if branch is RecoveryBranch.BASELINE else "retention:circuit"),
        pins=selected_protocol.pins,
        costs=vector,
        logical_probe_ids=tuple(
            f"probe-run:{branch.value}:{index + 1}"
            for index in range(coordinate_values["logical_probes"])
        ),
        effect_request_ids=tuple(
            f"effect:{branch.value}:{index + 1}" for index in range(coordinate_values["effects"])
        ),
        measurement_check=check_ref(f"measurement:{identifier}"),
        competence_established=True,
        competence_check=check_ref(f"competence:{identifier}"),
    )


def test_structural_retrieval_is_exact_stable_and_stale_closed() -> None:
    aggregate, owned = registration()
    package = aggregate.package
    query = query_for(package, owned)
    result = retrieve(
        result_id="retrieval-result:circuit",
        query=query,
        policy=STRUCTURAL_EXACT_V1,
        packages=(package, package),
        owned_fingerprints=owned,
    )
    assert tuple(hit.package_id for hit in result.hits) == (package.id,)
    assert result.hits[0].package_content_fingerprint == package.fingerprint
    assert result.hits[0].matched_ref_keys == (package.owned_refs[0].key,)
    assert result.source_sequence == query.source_sequence

    stale_owned = {package.owned_refs[0].key: "f" * 64}
    stale_query = query.model_copy(
        update={
            "source_index_fingerprint": structural_index_fingerprint((package,), stale_owned),
        }
    )
    with pytest.raises(ValueError, match="stale exact reference selector"):
        retrieve(
            result_id="retrieval-result:stale",
            query=stale_query,
            policy=STRUCTURAL_EXACT_V1,
            packages=(package,),
            owned_fingerprints=stale_owned,
        )


def test_unmatched_stale_package_does_not_perturb_result() -> None:
    aggregate, owned = registration()
    package = aggregate.package
    stale = package.model_copy(update={"id": "retention:unrelated", "cue_ids": ("cue:other",)})
    index = structural_index_fingerprint((package, stale), owned)
    query = query_for(package, owned).model_copy(update={"source_index_fingerprint": index})
    result = retrieve(
        result_id="retrieval-result:unrelated-stale",
        query=query,
        policy=STRUCTURAL_EXACT_V1,
        packages=(stale, package),
        owned_fingerprints=owned,
    )
    assert tuple(hit.package_id for hit in result.hits) == (package.id,)
    assert not result.rejected_stale_package_ids


def test_retrieval_is_permutation_stable_and_exactly_scope_isolated() -> None:
    aggregate, owned = registration()
    first = aggregate.package.model_copy(update={"id": "retention:a"})
    second = aggregate.package.model_copy(update={"id": "retention:b"})
    foreign = aggregate.package.model_copy(
        update={"id": "retention:foreign", "scope_fingerprint": "scope:foreign"}
    )
    foreign_binding = aggregate.package.model_copy(
        update={"id": "retention:foreign-binding", "binding_revision": "binding:foreign"}
    )
    foreign_horizon = aggregate.package.model_copy(
        update={"id": "retention:foreign-horizon", "protected_horizon_id": "horizon:foreign"}
    )
    packages = (second, foreign, foreign_binding, foreign_horizon, first)
    index = structural_index_fingerprint(packages, owned)
    query = query_for(first, owned).model_copy(update={"source_index_fingerprint": index})
    forward = retrieve(
        result_id="retrieval-result:forward",
        query=query,
        policy=STRUCTURAL_EXACT_V1,
        packages=tuple(reversed(packages)),
        owned_fingerprints=owned,
    )
    reverse = retrieve(
        result_id="retrieval-result:reverse",
        query=query,
        policy=STRUCTURAL_EXACT_V1,
        packages=packages,
        owned_fingerprints=owned,
    )
    assert tuple(item.package_id for item in forward.hits) == ("retention:a", "retention:b")
    assert tuple(item.package_id for item in reverse.hits) == ("retention:a", "retention:b")
    excluded = {foreign.id, foreign_binding.id, foreign_horizon.id}
    assert all(item.package_id not in excluded for item in forward.hits)


def test_retrieval_bounds_and_matching_stale_packages_fail_closed() -> None:
    aggregate, owned = registration()
    package = aggregate.package
    cue_query = query_for(package, owned).model_copy(update={"reference_selectors": ()})
    stale_owned = {package.owned_refs[0].key: "f" * 64}
    stale_query = cue_query.model_copy(
        update={
            "source_index_fingerprint": structural_index_fingerprint((package,), stale_owned),
        }
    )
    result = retrieve(
        result_id="retrieval-result:stale-package",
        query=stale_query,
        policy=STRUCTURAL_EXACT_V1,
        packages=(package,),
        owned_fingerprints=stale_owned,
    )
    assert not result.hits
    assert result.rejected_stale_package_ids == (package.id,)

    oversized = query_for(package, owned).model_copy(
        update={"limit": STRUCTURAL_EXACT_V1.max_results + 1}
    )
    with pytest.raises(ValueError, match="policy bound"):
        retrieve(
            result_id="retrieval-result:oversized",
            query=oversized,
            policy=STRUCTURAL_EXACT_V1,
            packages=(package,),
            owned_fingerprints=owned,
        )


def test_model_relevance_is_not_a_retrieval_selector_or_suppression_field() -> None:
    aggregate, owned = registration()
    query = query_for(aggregate.package, owned)
    with pytest.raises(ValidationError, match="Extra inputs"):
        RetrievalQuery.model_validate(
            {
                **query.model_dump(mode="json"),
                "model_relevance": "irrelevant",
            },
            strict=True,
        )


def test_owned_reference_fingerprint_detects_replacement() -> None:
    original = {"id": "probe:p", "contract": "counterexample-v1"}
    reference = procedure_ref("probe:p", original)
    assert resolve_owned_memory_ref(reference, owned_records={reference.key: original})[0]
    assert not resolve_owned_memory_ref(
        reference,
        owned_records={reference.key: {"id": "probe:p", "contract": "changed"}},
    )[0]


def test_registration_closes_route_and_scaffold_references() -> None:
    aggregate, _ = registration()
    assert aggregate.package.reacquisition_route_ids == ("route:reacquire",)

    foreign = procedure_ref("probe:foreign")
    bad_scaffold = aggregate.scaffolds[0].model_copy(update={"cue_refs": (foreign,)})
    with pytest.raises(ValidationError, match="scaffold sources"):
        RetentionRegistration(
            package=aggregate.package,
            direct_use_routes=aggregate.direct_use_routes,
            reconstruction_routes=aggregate.reconstruction_routes,
            consequence_evaluation_routes=aggregate.consequence_evaluation_routes,
            reacquisition_routes=aggregate.reacquisition_routes,
            scaffolds=(bad_scaffold,),
            recovery_protocols=aggregate.recovery_protocols,
        )

    invented_order = aggregate.scaffolds[0].model_copy(
        update={"ordered_probe_ids": ("probe:invented",)}
    )
    with pytest.raises(ValidationError, match="ordered scaffold probes"):
        RetentionRegistration(
            package=aggregate.package,
            direct_use_routes=aggregate.direct_use_routes,
            reconstruction_routes=aggregate.reconstruction_routes,
            consequence_evaluation_routes=aggregate.consequence_evaluation_routes,
            reacquisition_routes=aggregate.reacquisition_routes,
            scaffolds=(invented_order,),
            recovery_protocols=aggregate.recovery_protocols,
        )


def test_route_kinds_are_discriminated_and_never_licensed() -> None:
    aggregate, _ = registration()
    adapter: TypeAdapter[ProvisionalRecoveryRoute] = TypeAdapter(ProvisionalRecoveryRoute)
    routes = (
        *aggregate.direct_use_routes,
        *aggregate.reconstruction_routes,
        *aggregate.consequence_evaluation_routes,
        *aggregate.reacquisition_routes,
    )
    assert tuple(adapter.validate_python(route.model_dump()) for route in routes) == routes
    assert {str(route.model_dump()["kind"]) for route in routes} == {
        "direct_use",
        "reconstruction",
        "consequence_evaluation",
        "reacquisition",
    }
    assert all("license" not in type(route).model_fields for route in routes)


def test_memory_reconstruction_preserves_order_ambiguity_and_history_boundary() -> None:
    candidates = (
        MemoryReconstructionCandidate(
            id="candidate:b",
            rank=1,
            retention_package_ids=("retention:circuit",),
            generated_working_structure={"switch_closed": "unknown"},
            protected_consequence_class_id="class:b",
            generated_detail_ids=("detail:b",),
        ),
        MemoryReconstructionCandidate(
            id="candidate:a",
            rank=1,
            retention_package_ids=("retention:circuit",),
            generated_working_structure={"switch_closed": True},
            protected_consequence_class_id="class:a",
            generated_detail_ids=("detail:a",),
        ),
    )
    reconstructed = build_memory_reconstruction_set(
        reconstruction_set_id="memory-reconstruction:circuit",
        cue_ids=("cue:switch",),
        scope_fingerprint="scope:circuit",
        binding_revision="binding:circuit-v1",
        protected_horizon_id="horizon:circuit",
        candidates=reversed(candidates),
    )
    assert tuple(candidate.id for candidate in reconstructed.candidates) == (
        "candidate:a",
        "candidate:b",
    )
    assert reconstructed.ambiguous
    with pytest.raises(ValidationError, match="not historical fact"):
        MemoryReconstructionCandidate(
            id="candidate:invalid",
            rank=0,
            retention_package_ids=("retention:circuit",),
            generated_working_structure={},
            protected_consequence_class_id="class:invalid",
            historical_fact_ids=("detail:same",),
            generated_detail_ids=("detail:same",),
        )


def test_exact_pareto_advantage_is_checked_and_cannot_be_fabricated() -> None:
    baseline_observation = observation(
        "observation:baseline",
        branch=RecoveryBranch.BASELINE,
        vector=costs(effects=4, probes=4),
    )
    retained_observation = observation(
        "observation:retained",
        branch=RecoveryBranch.RETAINED,
        vector=costs(effects=2, probes=3),
    )
    baseline = derive_recovery_frontier(
        branch=RecoveryBranch.BASELINE,
        pins=protocol().pins,
        observations=(baseline_observation,),
    )
    retained = derive_recovery_frontier(
        branch=RecoveryBranch.RETAINED,
        pins=protocol().pins,
        observations=(retained_observation,),
    )
    comparison = compare_recovery_frontiers(
        comparison_id="recovery-comparison:circuit",
        baseline=baseline,
        retained=retained,
        comparison_check=check_ref("comparison:circuit"),
    )
    assert comparison.outcome is RecoveryComparisonOutcome.STRICT_ADVANTAGE
    assert comparison.coverage[0].strict
    assert check_recovery_comparison(comparison)[0]
    assert comparison.standing == "provisional_soft"
    assert "warrant" not in type(comparison).model_fields
    assert "license" not in type(comparison).model_fields

    with pytest.raises(ValidationError, match="outcome"):
        RecoveryComparison(
            id="recovery-comparison:forged",
            baseline_frontier=baseline,
            retained_frontier=retained,
            outcome=RecoveryComparisonOutcome.NO_ADVANTAGE,
            comparison_check=check_ref("comparison:forged"),
        )


def test_incomparable_and_mismatched_protocols_do_not_establish_advantage() -> None:
    baseline_observation = observation(
        "observation:baseline",
        branch=RecoveryBranch.BASELINE,
        vector=costs(effects=2, probes=5),
    )
    retained_observation = observation(
        "observation:retained",
        branch=RecoveryBranch.RETAINED,
        vector=costs(effects=3, probes=4),
    )
    baseline = derive_recovery_frontier(
        branch=RecoveryBranch.BASELINE,
        pins=protocol().pins,
        observations=(baseline_observation,),
    )
    retained = derive_recovery_frontier(
        branch=RecoveryBranch.RETAINED,
        pins=protocol().pins,
        observations=(retained_observation,),
    )
    comparison = compare_recovery_frontiers(
        comparison_id="recovery-comparison:incomparable",
        baseline=baseline,
        retained=retained,
        comparison_check=check_ref("comparison:incomparable"),
    )
    assert comparison.outcome is RecoveryComparisonOutcome.INCOMPARABLE

    mismatched_protocol = protocol(evaluator_version="2")
    mismatched_retained = derive_recovery_frontier(
        branch=RecoveryBranch.RETAINED,
        pins=mismatched_protocol.pins,
        observations=(
            observation(
                "observation:mismatch",
                branch=RecoveryBranch.RETAINED,
                vector=costs(effects=1, probes=1),
                selected_protocol=mismatched_protocol,
            ),
        ),
    )
    with pytest.raises(RecoveryCompatibilityError, match="pins"):
        compare_recovery_frontiers(
            comparison_id="recovery-comparison:mismatch",
            baseline=baseline,
            retained=mismatched_retained,
            comparison_check=check_ref("comparison:mismatch"),
        )


def test_eventual_success_without_strict_cost_improvement_is_not_advantage() -> None:
    baseline_observation = observation(
        "observation:baseline-eventual",
        branch=RecoveryBranch.BASELINE,
        vector=costs(effects=2, probes=2),
    )
    retained_observation = observation(
        "observation:retained-eventual",
        branch=RecoveryBranch.RETAINED,
        vector=costs(effects=2, probes=2),
    )
    baseline = derive_recovery_frontier(
        branch=RecoveryBranch.BASELINE,
        pins=protocol().pins,
        observations=(baseline_observation,),
    )
    retained = derive_recovery_frontier(
        branch=RecoveryBranch.RETAINED,
        pins=protocol().pins,
        observations=(retained_observation,),
    )
    comparison = compare_recovery_frontiers(
        comparison_id="recovery-comparison:eventual-only",
        baseline=baseline,
        retained=retained,
        comparison_check=check_ref("comparison:eventual-only"),
    )
    assert comparison.outcome is RecoveryComparisonOutcome.NO_ADVANTAGE


def test_costs_are_exact_reduced_and_use_integer_pareto_order() -> None:
    half = CostVector(
        coordinates=(CostCoordinate(axis=axis("effects"), numerator=1, denominator=2),)
    )
    two_thirds = CostVector(
        coordinates=(CostCoordinate(axis=axis("effects"), numerator=2, denominator=3),)
    )
    assert compare_cost_vectors(half, two_thirds) is CostRelation.LEFT_STRICTLY_BETTER
    with pytest.raises(ValidationError, match="reduced rational"):
        CostCoordinate(axis=axis("effects"), numerator=2, denominator=4)


def test_reacquisition_saga_records_pin_manifest_and_verified_child_prefix() -> None:
    selected_protocol = protocol()
    request = ReacquisitionRequest(
        id="request:retained",
        parent_inquiry_id="inquiry:parent",
        child_inquiry_id="inquiry:child",
        branch=RecoveryBranch.RETAINED,
        pins=selected_protocol.pins,
        child_manifest_artifact=ArtifactRef(
            digest="e" * 64,
            size=42,
            media_type="application/json",
        ),
        child_inquiry_manifest_artifact=ArtifactRef(
            digest="f" * 64,
            size=42,
            media_type="application/json",
        ),
        child_context_digest=CONTEXT_DIGEST,
        child_policy_version="policy:1",
        retention_package_id="retention:circuit",
        scaffold_id="scaffold:circuit",
    )
    manifest = ReacquisitionChildManifest(
        parent_inquiry_id=request.parent_inquiry_id,
        request_id=request.id,
        child_inquiry_id=request.child_inquiry_id,
        pins=request.pins,
        context_digest=request.child_context_digest,
        policy_version=request.child_policy_version,
        inquiry_manifest_artifact=ArtifactRef(
            digest="f" * 64,
            size=42,
            media_type="application/json",
        ),
    )
    link = ReacquisitionInquiryLink(
        id="link:retained",
        request_id=request.id,
        parent_inquiry_id=request.parent_inquiry_id,
        child_inquiry_id=request.child_inquiry_id,
        child_start_event_id="event:child-start",
        child_start_event_digest=EVENT_DIGEST,
        child_prefix_sequence=4,
        child_prefix_digest=PREFIX_DIGEST,
        child_manifest_artifact=request.child_manifest_artifact,
        child_context_digest=request.child_context_digest,
    )
    assert manifest.pins.recovery_protocol_id == selected_protocol.id
    assert link.child_start_sequence == 1


def test_zero_work_cannot_be_recorded_as_reacquisition() -> None:
    with pytest.raises(ValidationError, match="measured probe or effect"):
        RecoveryObservation(
            id="observation:zero",
            branch=RecoveryBranch.BASELINE,
            reacquisition_request_id="request:baseline",
            child_inquiry_id="inquiry:baseline",
            child_prefix_sequence=1,
            child_prefix_digest=PREFIX_DIGEST,
            retention_package_id=None,
            pins=protocol().pins,
            costs=costs(effects=0, probes=0),
            measurement_check=check_ref("measurement:zero"),
            competence_established=False,
        )


def test_reference_count_axes_equal_the_exact_cited_child_records() -> None:
    with pytest.raises(ValidationError, match="effects cost must equal"):
        RecoveryObservation(
            id="observation:miscounted",
            branch=RecoveryBranch.BASELINE,
            reacquisition_request_id="request:baseline",
            child_inquiry_id="inquiry:baseline",
            child_prefix_sequence=2,
            child_prefix_digest=PREFIX_DIGEST,
            retention_package_id=None,
            pins=protocol().pins,
            costs=costs(effects=2, probes=1),
            logical_probe_ids=("probe:1",),
            effect_request_ids=("effect:1",),
            measurement_check=check_ref("measurement:miscounted"),
            competence_established=False,
        )
