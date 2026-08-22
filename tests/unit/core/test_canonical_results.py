"""Strict canonical decoded-result roles fail closed."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from rci.core import (
    ArtifactRef,
    CanonicalResult,
    ConflictResult,
    CounterexampleResult,
    EquivalenceCertificateResult,
    FailureResult,
    PrerequisiteResult,
    ReachabilityWitnessResult,
    SeparatorResult,
    SuccessResult,
    UnknownResult,
    UnreachabilityCertificateResult,
    WitnessResult,
)


def ref(character: str) -> ArtifactRef:
    return ArtifactRef(digest=character * 64, size=1)


def test_every_g1_canonical_role_has_a_strict_schema() -> None:
    semantic = ref("a")
    evidence = ref("b")
    results: tuple[CanonicalResult, ...] = (
        WitnessResult(
            id="witness-1",
            semantic_artifact=semantic,
            proposition_id="proposition-1",
            witness_artifact=evidence,
        ),
        CounterexampleResult(
            id="counterexample-1",
            semantic_artifact=semantic,
            proposition_id="proposition-1",
            counterexample_artifact=evidence,
        ),
        SeparatorResult(
            id="separator-1",
            semantic_artifact=semantic,
            left_class_id="left",
            right_class_id="right",
            separator_artifact=evidence,
        ),
        EquivalenceCertificateResult(
            id="equivalence-1",
            semantic_artifact=semantic,
            relation_id="relation-1",
            certificate_artifact=evidence,
        ),
        ConflictResult(
            id="conflict-1",
            semantic_artifact=semantic,
            left_proposition_id="left",
            right_proposition_id="right",
        ),
        PrerequisiteResult(
            id="prerequisite-1",
            semantic_artifact=semantic,
            condition_id="condition-1",
            consequence_id="consequence-1",
            evidence_artifact=evidence,
        ),
        ReachabilityWitnessResult(
            id="reachability-1",
            semantic_artifact=semantic,
            source_id="source",
            target_id="target",
            path_artifact=evidence,
        ),
        UnreachabilityCertificateResult(
            id="unreachability-1",
            semantic_artifact=semantic,
            source_id="source",
            target_id="target",
            certificate_artifact=evidence,
        ),
        SuccessResult(
            id="success-1",
            semantic_artifact=semantic,
            operation_id="bind-l0",
        ),
        FailureResult(
            id="failure-1",
            semantic_artifact=semantic,
            failure_kind="logical_failure",
            diagnostics=evidence,
        ),
        UnknownResult(
            id="unknown-1",
            semantic_artifact=semantic,
            reason_kind="search_exhausted",
        ),
    )

    adapter: TypeAdapter[CanonicalResult] = TypeAdapter(CanonicalResult)
    assert {
        adapter.validate_python(result.model_dump(mode="python"), strict=True).kind
        for result in results
    } == {
        "witness",
        "counterexample",
        "separator",
        "equivalence_certificate",
        "conflict",
        "prerequisite",
        "reachability_witness",
        "unreachability_certificate",
        "success",
        "failure",
        "unknown",
    }


def test_unknown_or_malformed_roles_fail_closed() -> None:
    adapter: TypeAdapter[CanonicalResult] = TypeAdapter(CanonicalResult)
    with pytest.raises(ValidationError):
        adapter.validate_python(
            {
                "kind": "controller_certificate",
                "id": "later-role",
                "semantic_artifact": ref("a").model_dump(mode="python"),
            },
            strict=True,
        )
    with pytest.raises(ValidationError):
        adapter.validate_python(
            {
                "kind": "witness",
                "id": "missing-evidence",
                "semantic_artifact": ref("a").model_dump(mode="python"),
                "proposition_id": "p",
            },
            strict=True,
        )
