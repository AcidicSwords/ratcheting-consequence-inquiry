"""Blocking G3V acceptance for bounded model-disconnected review equivalence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from rci.claims.models import content_fingerprint
from rci.cli import app
from rci.core.errors import InvalidCommandError
from rci.core.serialization import canonical_json_bytes
from rci.project import (
    REQUIRED_FAULT_IDS,
    REVIEW_FAULT_PROFILE_VERSION,
    BreakerIndeterminateReason,
    CandidateEnvironmentManifest,
    CapabilityLimitation,
    CapabilitySuccessorCandidate,
    DevelopmentEvidence,
    EvidenceKind,
    EvidenceOutcome,
    FaultObservationManifest,
    ImplementationGoalContract,
    LimitationKind,
    MechanicalReviewContract,
    MechanicalReviewIndeterminate,
    MechanicalReviewOutcome,
    ModelReviewIndeterminate,
    ProjectAnchor,
    ProjectCost,
    ProjectDisposition,
    ProjectGainKind,
    ProjectSuccessorDecision,
    ReviewFaultId,
    ReviewInvariantId,
    SemanticBreakerCandidate,
    SemanticCoverage,
    SuccessorKind,
    assess_mechanical_review,
    baseline_review_probe,
    build_fault_observation_manifest,
    compile_mechanical_review_contract,
    derive_capability_frontier,
    seed_review_fault,
)
from rci.sdk import RCI

BASE = "a" * 40
HEAD = "b" * 40
DIGEST = "c" * 64


def _setup(
    root: Path,
) -> tuple[
    RCI,
    ImplementationGoalContract,
    CandidateEnvironmentManifest,
    CapabilitySuccessorCandidate,
    tuple[DevelopmentEvidence, ...],
    MechanicalReviewContract,
    FaultObservationManifest,
]:
    sdk = RCI(root)
    sdk.start("project-review-inquiry")
    anchor = ProjectAnchor(
        id="anchor-g3v",
        repository="AcidicSwords/ratcheting-consequence-inquiry",
        protected_branch="main",
        commit_sha=BASE,
        tree_digest=DIGEST,
        authority_digest="d" * 64,
        gate_digest="e" * 64,
        clean=True,
    )
    sdk.record_project_anchor("project-review-inquiry", anchor)
    limitation = CapabilityLimitation(
        id="limitation-bounded-review",
        anchor_id=anchor.id,
        kind=LimitationKind.EVIDENCE,
        current_capability="Malformed local-model returns cannot provide reliable review evidence.",
        missing_capability="Detect a closed family of review-boundary faults without a model.",
        consequential_boundary=(
            "A surviving seeded fault permits an unlawful successor while a detected "
            "fault does not."
        ),
        protected_consequence_ids=("fresh-review-separation", "promotion-nonauthority"),
        observed_evidence=(sdk.artifacts.put_bytes(b"malformed qwen review"),),
    )
    sdk.record_capability_limitation("project-review-inquiry", limitation)
    successor = CapabilitySuccessorCandidate(
        id="candidate-bounded-review",
        anchor_id=anchor.id,
        limitation_id=limitation.id,
        kind=SuccessorKind.IMPLEMENTATION,
        current_state=limitation.current_capability,
        desired_state=limitation.missing_capability,
        preserved_capability_ids=("g1", "g2a", "g2b", "g3ah", "g3g", "g3q", "g3r"),
        gain_kinds=(ProjectGainKind.INDEPENDENT_CHECKABILITY,),
        discriminator_id="review-equivalence-acceptance",
        evidence_mechanism_ids=("predecessor-gate", "property-checks"),
        estimated_costs=(
            ProjectCost(axis="authority_risk", value=0),
            ProjectCost(axis="missing_executable_seams", value=1),
        ),
        reversible=True,
    )
    sdk.record_capability_successor_candidate("project-review-inquiry", successor)
    frontier = derive_capability_frontier(frontier_id="frontier-g3v", candidates=(successor,))
    sdk.record_capability_frontier("project-review-inquiry", frontier)
    goal = ImplementationGoalContract(
        id="goal-g3v",
        cycle_id="cycle-g3v",
        anchor_id=anchor.id,
        frontier_id=frontier.id,
        candidate_id=successor.id,
        current=successor.current_state,
        desired=successor.desired_state,
        separator="Every closed-profile seeded review fault is independently detected.",
        expected_incumbent_return="Malformed review or an untested review boundary remains.",
        expected_candidate_return="The closed profile returns valid_within_profile only.",
        preserve_capability_ids=successor.preserved_capability_ids,
        acceptance_commands=("uv run pytest -q tests/acceptance/test_review_equivalence.py",),
        allowed_mutation_roots=("src/rci/project", "tests"),
        forbidden_authority_roots=(".github", "AGENTS.md", "PLAN.md"),
        assumption_ids=("closed-fault-profile-is-bounded", "fresh-review-remains-separate"),
        incumbent_gate_digest=anchor.gate_digest,
        proposed_gate_digest="f" * 64,
        rollback_condition="A seeded review fault survives or a predecessor gate fails.",
        reopening_condition="A new semantic fault lies outside the closed profile.",
    )
    sdk.seal_implementation_goal("project-review-inquiry", goal)
    environment = CandidateEnvironmentManifest(
        id="environment-g3v",
        goal_id=goal.id,
        developer_id="codex-developer",
        base_commit_sha=BASE,
        candidate_branch="codex/g3v-review-equivalence",
        worktree_path=".rci/workspaces/g3v",
        initial_tree_digest=DIGEST,
        toolchain_artifact=sdk.artifacts.put_bytes(b"python=3.12;uv=0.9.18"),
        toolchain_digest="1" * 64,
    )
    sdk.record_candidate_environment("project-review-inquiry", environment)

    placeholder = sdk.artifacts.put_bytes(b"placeholder")
    draft_evidence = tuple(
        DevelopmentEvidence(
            id=f"evidence-{fault_id.value}",
            goal_id=goal.id,
            candidate_environment_id=environment.id,
            kind=EvidenceKind.PROPERTY_CHECK,
            command_or_method=f"{REVIEW_FAULT_PROFILE_VERSION}:{fault_id.value}",
            outcome=EvidenceOutcome.PASS,
            observed_return=placeholder,
            base_commit_sha=BASE,
            candidate_commit_sha=HEAD,
            gate_digest=goal.proposed_gate_digest,
        )
        for fault_id in REQUIRED_FAULT_IDS
    )
    compiled = compile_mechanical_review_contract(
        goal=goal, environment=environment, evidence=draft_evidence
    )
    assert isinstance(compiled, MechanicalReviewContract)
    probes = tuple(
        (fault_id, seed_review_fault(compiled, fault_id)) for fault_id in REQUIRED_FAULT_IDS
    )
    probe_by_fault = dict(probes)
    evidence = tuple(
        item.model_copy(
            update={
                "observed_return": sdk.artifacts.put_bytes(
                    canonical_json_bytes(
                        probe_by_fault[ReviewFaultId(item.id.removeprefix("evidence-"))]
                    ),
                    media_type="application/vnd.rci.seeded-review-probe+json",
                    encoding="utf-8",
                )
            }
        )
        for item in draft_evidence
    )
    for item in evidence:
        sdk.record_development_evidence("project-review-inquiry", item)
    contract = sdk.compile_mechanical_review(
        "project-review-inquiry",
        goal_id=goal.id,
        candidate_environment_id=environment.id,
        evidence_ids=tuple(reversed(tuple(item.id for item in evidence))),
    )
    assert isinstance(contract, MechanicalReviewContract)
    assert contract == compiled
    manifest = build_fault_observation_manifest(contract=contract, probes=tuple(reversed(probes)))
    return sdk, goal, environment, successor, evidence, contract, manifest


def test_closed_profile_is_deterministic_and_only_valid_within_profile(tmp_path: Path) -> None:
    sdk, goal, environment, successor, evidence, contract, manifest = _setup(tmp_path)

    left = sdk.assess_mechanical_review(
        "project-review-inquiry", contract=contract, manifest=manifest
    )
    right = assess_mechanical_review(
        contract=contract, manifest=manifest, evidence=tuple(reversed(evidence))
    )
    assert left == right
    assert left.outcome is MechanicalReviewOutcome.VALID_WITHIN_PROFILE
    assert left.detected_fault_ids == REQUIRED_FAULT_IDS
    assert left.semantic_residual is SemanticCoverage.UNKNOWN
    assert left.model_required is False
    assert left.independent_review_satisfied is False
    assert left.promotion_authorized is False
    assert sdk.inspect("project-review-inquiry").independent_reviews == ()

    with pytest.raises(InvalidCommandError, match="proof chain"):
        sdk.decide_project_successor(
            "project-review-inquiry",
            ProjectSuccessorDecision(
                id="forged-successor-from-mechanical-assessment",
                goal_id=goal.id,
                candidate_id=successor.id,
                candidate_environment_id=environment.id,
                review_id=left.id,
                evidence_ids=tuple(sorted(item.id for item in evidence)),
                disposition=ProjectDisposition.REPLACE,
                preserved_capability_ids=successor.preserved_capability_ids,
                gain_kinds=(ProjectGainKind.INDEPENDENT_CHECKABILITY,),
                reason="Mechanical profile is deliberately not fresh semantic review.",
            ),
        )


def test_survival_missing_stale_and_tampered_returns_fail_closed(tmp_path: Path) -> None:
    _, _, _, _, evidence, contract, manifest = _setup(tmp_path)
    target = ReviewFaultId.STAGE_COLLAPSE
    probes = tuple(
        (
            ReviewFaultId(item.fault_id),
            baseline_review_probe(contract) if item.fault_id == target else item.probe,
        )
        for item in manifest.observations
    )
    survived_manifest = build_fault_observation_manifest(contract=contract, probes=probes)
    survived_observation = next(
        item for item in survived_manifest.observations if item.fault_id == target
    )
    survived_evidence = tuple(
        item.model_copy(
            update={
                "outcome": EvidenceOutcome.FAIL,
                "observed_return": item.observed_return.model_copy(
                    update={"digest": survived_observation.reproducer_digest}
                ),
            }
        )
        if item.id == survived_observation.evidence_id
        else item
        for item in evidence
    )
    survived = assess_mechanical_review(
        contract=contract, manifest=survived_manifest, evidence=survived_evidence
    )
    assert survived.outcome is MechanicalReviewOutcome.INVALID
    assert survived.surviving_fault_ids == (target,)

    missing_manifest = build_fault_observation_manifest(
        contract=contract,
        probes=tuple(
            (ReviewFaultId(item.fault_id), item.probe)
            for item in manifest.observations
            if item.fault_id != ReviewFaultId.EVIDENCE_SUBSTITUTION
        ),
    )
    missing = assess_mechanical_review(
        contract=contract, manifest=missing_manifest, evidence=evidence
    )
    assert missing.outcome is MechanicalReviewOutcome.INDETERMINATE
    assert missing.indeterminate_fault_ids == (ReviewFaultId.EVIDENCE_SUBSTITUTION,)

    duplicate_manifest = build_fault_observation_manifest(
        contract=contract,
        probes=(
            *tuple((ReviewFaultId(item.fault_id), item.probe) for item in manifest.observations),
            (
                ReviewFaultId(manifest.observations[0].fault_id),
                manifest.observations[0].probe,
            ),
        ),
    )
    duplicate = assess_mechanical_review(
        contract=contract, manifest=duplicate_manifest, evidence=evidence
    )
    assert duplicate.outcome is MechanicalReviewOutcome.INDETERMINATE
    assert duplicate.profile_error_ids == (f"duplicate-fault:{manifest.observations[0].fault_id}",)

    unknown_observations = tuple(
        sorted(
            (
                manifest.observations[0].model_copy(update={"fault_id": "invented-fault"}),
                *manifest.observations[1:],
            ),
            key=lambda item: item.fault_id,
        )
    )
    unknown_payload = {
        "schema_version": 1,
        "contract_id": contract.id,
        "contract_fingerprint": contract.fingerprint,
        "profile_version": REVIEW_FAULT_PROFILE_VERSION,
        "candidate_commit_sha": contract.candidate_commit_sha,
        "observations": unknown_observations,
    }
    unknown_fingerprint = content_fingerprint("rci.fault-observation-manifest.v1", unknown_payload)
    unknown_manifest = FaultObservationManifest(
        id=f"fault-manifest-{unknown_fingerprint[:24]}",
        fingerprint=unknown_fingerprint,
        contract_id=contract.id,
        contract_fingerprint=contract.fingerprint,
        candidate_commit_sha=contract.candidate_commit_sha,
        observations=unknown_observations,
    )
    unknown = assess_mechanical_review(
        contract=contract, manifest=unknown_manifest, evidence=evidence
    )
    assert unknown.outcome is MechanicalReviewOutcome.INDETERMINATE
    assert unknown.profile_error_ids == ("unknown-fault:invented-fault",)

    stale_evidence = tuple(
        item.model_copy(update={"candidate_commit_sha": "9" * 40})
        if item.id == manifest.observations[0].evidence_id
        else item
        for item in evidence
    )
    stale = assess_mechanical_review(contract=contract, manifest=manifest, evidence=stale_evidence)
    assert stale.outcome is MechanicalReviewOutcome.INDETERMINATE
    assert stale.indeterminate_fault_ids == (manifest.observations[0].fault_id,)

    malformed_probe = manifest.observations[0].probe.model_copy(update={"stages_separate": False})
    malformed_manifest = build_fault_observation_manifest(
        contract=contract,
        probes=((ReviewFaultId(manifest.observations[0].fault_id), malformed_probe),),
    )
    malformed = assess_mechanical_review(
        contract=contract, manifest=malformed_manifest, evidence=evidence
    )
    assert malformed.outcome is MechanicalReviewOutcome.INDETERMINATE


def test_contract_rejects_profile_omission_and_foreign_pins(tmp_path: Path) -> None:
    _, goal, environment, _, evidence, contract, _ = _setup(tmp_path)
    reversed_contract = compile_mechanical_review_contract(
        goal=goal, environment=environment, evidence=tuple(reversed(evidence))
    )
    assert reversed_contract == contract

    incomplete = compile_mechanical_review_contract(
        goal=goal, environment=environment, evidence=evidence[:-1]
    )
    assert isinstance(incomplete, MechanicalReviewIndeterminate)
    foreign = compile_mechanical_review_contract(
        goal=goal,
        environment=environment,
        evidence=(evidence[0].model_copy(update={"goal_id": "foreign-goal"}), *evidence[1:]),
    )
    assert isinstance(foreign, MechanicalReviewIndeterminate)

    with pytest.raises(ValueError, match="complete invariant registry"):
        MechanicalReviewContract.model_validate(
            {
                **contract.model_dump(mode="python"),
                "invariant_ids": (ReviewInvariantId.EXACT_HEAD_BINDING,),
            },
            strict=True,
        )


def test_model_breakers_are_strict_inert_candidates_or_indeterminate() -> None:
    malformed_qwen = (
        b"<think>I should write tests</think>\n```json\n"
        b'{"file":"invented_test.py","code":"assert True"}\n```'
    )
    malformed = RCI.parse_semantic_breaker(
        malformed_qwen,
        expected_base_commit_sha=BASE,
        expected_candidate_commit_sha=HEAD,
    )
    assert isinstance(malformed, ModelReviewIndeterminate)
    assert malformed.reason is BreakerIndeterminateReason.MALFORMED_JSON
    assert malformed.promotion_authorized is False

    payload = {
        "schema_version": 1,
        "status": "inert_candidate",
        "base_commit_sha": BASE,
        "candidate_commit_sha": HEAD,
        "reviewer_route_id": "optional-local-model-v1",
        "invariant_id": ReviewInvariantId.STAGE_SEPARATION.value,
        "location": "src/rci/project/review_equivalence.py:1",
        "claim": "A candidate appears to collapse two review stages.",
        "reproduction": "Inspect the exact referenced transition and run its focused attack.",
        "warrant_claimed": False,
    }
    parsed = RCI.parse_semantic_breaker(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(),
        expected_base_commit_sha=BASE,
        expected_candidate_commit_sha=HEAD,
    )
    assert isinstance(parsed, SemanticBreakerCandidate)
    assert parsed.status == "inert_candidate"
    assert parsed.warrant_claimed is False

    payload["invariant_id"] = "invented-invariant"
    unknown = RCI.parse_semantic_breaker(
        json.dumps(payload).encode(),
        expected_base_commit_sha=BASE,
        expected_candidate_commit_sha=HEAD,
    )
    assert isinstance(unknown, ModelReviewIndeterminate)
    assert unknown.reason is BreakerIndeterminateReason.UNKNOWN_INVARIANT


def test_cli_and_sdk_emit_identical_canonical_review_results(tmp_path: Path) -> None:
    sdk, goal, environment, _, evidence, contract, manifest = _setup(tmp_path)
    expected = sdk.assess_mechanical_review(
        "project-review-inquiry", contract=contract, manifest=manifest
    )
    contract_path = tmp_path / "review-contract.json"
    manifest_path = tmp_path / "review-manifest.json"
    contract_path.write_bytes(canonical_json_bytes(contract))
    manifest_path.write_bytes(canonical_json_bytes(manifest))

    runner = CliRunner()
    contract_args = [
        "project",
        "review-contract",
        "project-review-inquiry",
        "--goal-id",
        goal.id,
        "--candidate-environment-id",
        environment.id,
    ]
    for item in reversed(evidence):
        contract_args.extend(("--evidence-id", item.id))
    contract_args.extend(("--root", str(tmp_path)))
    compiled_result = runner.invoke(app, contract_args)
    assert compiled_result.exit_code == 0, compiled_result.output
    assert json.loads(compiled_result.stdout) == contract.model_dump(mode="json")

    assessed_result = runner.invoke(
        app,
        [
            "project",
            "review-assess",
            "project-review-inquiry",
            "--contract",
            str(contract_path),
            "--manifest",
            str(manifest_path),
            "--root",
            str(tmp_path),
        ],
    )
    assert assessed_result.exit_code == 0, assessed_result.output
    assert json.loads(assessed_result.stdout) == expected.model_dump(mode="json")

    malformed_path = tmp_path / "malformed-qwen.txt"
    malformed_path.write_text("Here is a test instead of the requested record.", encoding="utf-8")
    breaker_result = runner.invoke(
        app,
        [
            "project",
            "review-breaker",
            "--record",
            str(malformed_path),
            "--base-commit-sha",
            BASE,
            "--candidate-commit-sha",
            HEAD,
        ],
    )
    assert breaker_result.exit_code == 0, breaker_result.output
    assert json.loads(breaker_result.stdout)["outcome"] == "indeterminate"


def test_profile_registry_and_gate_are_exact() -> None:
    assert tuple(sorted(REQUIRED_FAULT_IDS)) == REQUIRED_FAULT_IDS
    assert set(REQUIRED_FAULT_IDS) == set(ReviewFaultId)
    assert content_fingerprint("rci.review-profile.v1", REQUIRED_FAULT_IDS)
