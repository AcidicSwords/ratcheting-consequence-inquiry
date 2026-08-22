"""Pure bounded review equivalence and inert semantic-breaker parsing.

This module deliberately does not implement fresh semantic review.  It mutation-tests
an exact review surface against a closed fault profile and reports only what that finite
profile establishes.  No record here is authoritative state or promotion evidence.
"""

from __future__ import annotations

from enum import StrEnum
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Literal

from pydantic import model_validator

from rci.claims.models import canonical_json, content_fingerprint
from rci.core.model import FrozenModel, Identifier, NonEmptyText, Sha256Digest
from rci.project.models import (
    CandidateEnvironmentManifest,
    DevelopmentEvidence,
    EvidenceKind,
    EvidenceOutcome,
    GitCommitSha,
    ImplementationGoalContract,
)

REVIEW_FAULT_PROFILE_VERSION: Literal["project-review-faults-v1"] = "project-review-faults-v1"
MECHANICAL_REVIEWER_ID: Literal["rci-mechanical-review-v1"] = "rci-mechanical-review-v1"


def _canonical_bytes(value: object) -> bytes:
    return canonical_json(value).encode("utf-8")


def _sha256_digest(value: bytes) -> str:
    return sha256(value).hexdigest()


class ReviewFaultId(StrEnum):
    EXACT_HEAD_SUBSTITUTION = "exact-head-substitution"
    EVIDENCE_SUBSTITUTION = "evidence-substitution"
    SELF_REVIEW = "self-review"
    STAGE_COLLAPSE = "stage-collapse"
    UNKNOWN_AS_SUCCESS = "unknown-as-success"
    GATE_WEAKENING = "gate-weakening"
    ALLOWLIST_BROADENING = "allowlist-broadening"
    REPLAY_EFFECT_COLLAPSE = "replay-effect-collapse"


class ReviewInvariantId(StrEnum):
    EXACT_HEAD_BINDING = "exact-head-binding"
    EVIDENCE_OWNERSHIP = "evidence-ownership"
    REVIEWER_INDEPENDENCE = "reviewer-independence"
    STAGE_SEPARATION = "stage-separation"
    UNKNOWN_NONPROMOTION = "unknown-nonpromotion"
    GATE_MONOTONICITY = "gate-monotonicity"
    AUTHORITY_ROOT_CONFINEMENT = "authority-root-confinement"
    REPLAY_EFFECT_FREEDOM = "replay-effect-freedom"


class MechanicalReviewOutcome(StrEnum):
    VALID_WITHIN_PROFILE = "valid_within_profile"
    INVALID = "invalid"
    INDETERMINATE = "indeterminate"


class SemanticCoverage(StrEnum):
    UNKNOWN = "unknown"
    CLAIMED_SUCCESS = "claimed_success"


class FaultDisposition(StrEnum):
    DETECTED = "detected"
    SURVIVED = "survived"
    INDETERMINATE = "indeterminate"


class ReviewIndeterminateReason(StrEnum):
    MISSING_RECORD = "missing_record"
    FOREIGN_RECORD = "foreign_record"
    STALE_COMMIT = "stale_commit"
    GATE_MISMATCH = "gate_mismatch"
    INCOMPLETE_PROFILE = "incomplete_profile"
    MALFORMED_OBSERVATION = "malformed_observation"
    UNSUPPORTED_EVIDENCE = "unsupported_evidence"


class BreakerIndeterminateReason(StrEnum):
    INVALID_UTF8 = "invalid_utf8"
    MALFORMED_JSON = "malformed_json"
    WRONG_COMMIT = "wrong_commit"
    UNKNOWN_INVARIANT = "unknown_invariant"
    INVALID_LOCATION = "invalid_location"


class ReviewFaultDefinition(FrozenModel):
    id: ReviewFaultId
    invariant_id: ReviewInvariantId


PROJECT_REVIEW_FAULTS = (
    ReviewFaultDefinition(
        id=ReviewFaultId.ALLOWLIST_BROADENING,
        invariant_id=ReviewInvariantId.AUTHORITY_ROOT_CONFINEMENT,
    ),
    ReviewFaultDefinition(
        id=ReviewFaultId.EVIDENCE_SUBSTITUTION,
        invariant_id=ReviewInvariantId.EVIDENCE_OWNERSHIP,
    ),
    ReviewFaultDefinition(
        id=ReviewFaultId.EXACT_HEAD_SUBSTITUTION,
        invariant_id=ReviewInvariantId.EXACT_HEAD_BINDING,
    ),
    ReviewFaultDefinition(
        id=ReviewFaultId.GATE_WEAKENING,
        invariant_id=ReviewInvariantId.GATE_MONOTONICITY,
    ),
    ReviewFaultDefinition(
        id=ReviewFaultId.REPLAY_EFFECT_COLLAPSE,
        invariant_id=ReviewInvariantId.REPLAY_EFFECT_FREEDOM,
    ),
    ReviewFaultDefinition(
        id=ReviewFaultId.SELF_REVIEW,
        invariant_id=ReviewInvariantId.REVIEWER_INDEPENDENCE,
    ),
    ReviewFaultDefinition(
        id=ReviewFaultId.STAGE_COLLAPSE,
        invariant_id=ReviewInvariantId.STAGE_SEPARATION,
    ),
    ReviewFaultDefinition(
        id=ReviewFaultId.UNKNOWN_AS_SUCCESS,
        invariant_id=ReviewInvariantId.UNKNOWN_NONPROMOTION,
    ),
)
REQUIRED_FAULT_IDS = tuple(item.id for item in PROJECT_REVIEW_FAULTS)
REQUIRED_INVARIANT_IDS = tuple(sorted(item.invariant_id for item in PROJECT_REVIEW_FAULTS))


class FaultEvidenceBinding(FrozenModel):
    fault_id: ReviewFaultId
    evidence_id: Identifier


class MechanicalReviewContract(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    fingerprint: Sha256Digest
    profile_version: Literal["project-review-faults-v1"] = REVIEW_FAULT_PROFILE_VERSION
    goal_id: Identifier
    candidate_environment_id: Identifier
    base_commit_sha: GitCommitSha
    candidate_commit_sha: GitCommitSha
    gate_digest: Sha256Digest
    developer_id: Identifier
    reviewer_id: Literal["rci-mechanical-review-v1"] = MECHANICAL_REVIEWER_ID
    invariant_ids: tuple[ReviewInvariantId, ...]
    fault_evidence: tuple[FaultEvidenceBinding, ...]
    semantic_claim: Literal["bounded_profile_only"] = "bounded_profile_only"
    promotion_authorized: Literal[False] = False

    @model_validator(mode="after")
    def validate_contract(self) -> MechanicalReviewContract:
        if self.invariant_ids != REQUIRED_INVARIANT_IDS:
            raise ValueError(
                "mechanical review contract must retain the complete invariant registry"
            )
        if tuple(item.fault_id for item in self.fault_evidence) != REQUIRED_FAULT_IDS:
            raise ValueError("mechanical review contract must retain the complete fault profile")
        evidence_ids = tuple(item.evidence_id for item in self.fault_evidence)
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("each seeded fault requires distinct development evidence")
        if self.reviewer_id == self.developer_id:
            raise ValueError("mechanical reviewer identity must differ from the developer")
        fingerprint = _contract_fingerprint(self)
        if self.fingerprint != fingerprint or self.id != f"mechanical-review-{fingerprint[:24]}":
            raise ValueError("mechanical review identity must be content-derived")
        return self


class SeededReviewProbe(FrozenModel):
    candidate_commit_sha: GitCommitSha
    evidence_ids: tuple[Identifier, ...]
    developer_id: Identifier
    reviewer_id: Identifier
    stages_separate: bool
    semantic_coverage: SemanticCoverage
    gate_digest: Sha256Digest
    authority_roots_confined: bool
    replay_effect_free: bool

    @model_validator(mode="after")
    def validate_probe(self) -> SeededReviewProbe:
        if tuple(sorted(set(self.evidence_ids))) != self.evidence_ids:
            raise ValueError("review-probe evidence must be unique and canonically ordered")
        return self


class FaultObservation(FrozenModel):
    fault_id: Identifier
    evidence_id: Identifier
    probe: SeededReviewProbe
    reproducer_digest: Sha256Digest

    @model_validator(mode="after")
    def validate_observation(self) -> FaultObservation:
        if self.reproducer_digest != _sha256_digest(_canonical_bytes(self.probe)):
            raise ValueError("fault reproducer digest must bind the exact probe")
        return self


class FaultObservationManifest(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    fingerprint: Sha256Digest
    contract_id: Identifier
    contract_fingerprint: Sha256Digest
    profile_version: Literal["project-review-faults-v1"] = REVIEW_FAULT_PROFILE_VERSION
    candidate_commit_sha: GitCommitSha
    observations: tuple[FaultObservation, ...]

    @model_validator(mode="after")
    def validate_manifest(self) -> FaultObservationManifest:
        fault_ids = tuple(item.fault_id for item in self.observations)
        if tuple(sorted(fault_ids)) != fault_ids:
            raise ValueError("fault observations must be canonically ordered")
        fingerprint = _manifest_fingerprint(self)
        if self.fingerprint != fingerprint or self.id != f"fault-manifest-{fingerprint[:24]}":
            raise ValueError("fault manifest identity must be content-derived")
        return self


class MechanicalReviewAssessment(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    contract_id: Identifier
    contract_fingerprint: Sha256Digest
    manifest_id: Identifier
    outcome: MechanicalReviewOutcome
    detected_fault_ids: tuple[ReviewFaultId, ...] = ()
    surviving_fault_ids: tuple[ReviewFaultId, ...] = ()
    indeterminate_fault_ids: tuple[ReviewFaultId, ...] = ()
    profile_error_ids: tuple[Identifier, ...] = ()
    evidence_ids: tuple[Identifier, ...] = ()
    semantic_residual: Literal[SemanticCoverage.UNKNOWN] = SemanticCoverage.UNKNOWN
    model_required: Literal[False] = False
    independent_review_satisfied: Literal[False] = False
    promotion_authorized: Literal[False] = False

    @model_validator(mode="after")
    def validate_assessment(self) -> MechanicalReviewAssessment:
        for values in (
            self.detected_fault_ids,
            self.surviving_fault_ids,
            self.indeterminate_fault_ids,
            self.profile_error_ids,
            self.evidence_ids,
        ):
            if tuple(sorted(set(values))) != values:
                raise ValueError("assessment collections must be unique and canonical")
        fingerprint = content_fingerprint(
            "rci.mechanical-review-assessment.v1",
            self.model_dump(mode="json", exclude={"id"}),
        )
        if self.id != f"mechanical-assessment-{fingerprint[:24]}":
            raise ValueError("mechanical assessment identity must be content-derived")
        return self


class MechanicalReviewIndeterminate(FrozenModel):
    schema_version: Literal[1] = 1
    outcome: Literal[MechanicalReviewOutcome.INDETERMINATE] = MechanicalReviewOutcome.INDETERMINATE
    reason: ReviewIndeterminateReason
    input_digest: Sha256Digest
    semantic_residual: Literal[SemanticCoverage.UNKNOWN] = SemanticCoverage.UNKNOWN
    independent_review_satisfied: Literal[False] = False
    promotion_authorized: Literal[False] = False


class SemanticBreakerCandidate(FrozenModel):
    schema_version: Literal[1] = 1
    status: Literal["inert_candidate"] = "inert_candidate"
    base_commit_sha: GitCommitSha
    candidate_commit_sha: GitCommitSha
    reviewer_route_id: Identifier
    invariant_id: Identifier
    location: NonEmptyText
    claim: NonEmptyText
    reproduction: NonEmptyText
    warrant_claimed: Literal[False] = False

    @model_validator(mode="after")
    def validate_location(self) -> SemanticBreakerCandidate:
        path_text, _, line = self.location.partition(":")
        path = PurePosixPath(path_text)
        if (
            "\\" in path_text
            or path.is_absolute()
            or path_text != path.as_posix()
            or path_text in {"", "."}
            or ".." in path.parts
            or (line and not line.isdigit())
        ):
            raise ValueError(
                "breaker location must be a repository-relative path with optional line"
            )
        return self


class ModelReviewIndeterminate(FrozenModel):
    schema_version: Literal[1] = 1
    outcome: Literal["indeterminate"] = "indeterminate"
    reason: BreakerIndeterminateReason
    raw_digest: Sha256Digest
    promotion_authorized: Literal[False] = False


def _contract_fingerprint(contract: MechanicalReviewContract) -> str:
    return content_fingerprint(
        "rci.mechanical-review-contract.v1",
        contract.model_dump(mode="json", exclude={"id", "fingerprint"}),
    )


def _manifest_fingerprint(manifest: FaultObservationManifest) -> str:
    return content_fingerprint(
        "rci.fault-observation-manifest.v1",
        manifest.model_dump(mode="json", exclude={"id", "fingerprint"}),
    )


def _indeterminate(
    reason: ReviewIndeterminateReason, value: object
) -> MechanicalReviewIndeterminate:
    return MechanicalReviewIndeterminate(
        reason=reason,
        input_digest=content_fingerprint("rci.review-indeterminate.v1", value),
    )


def compile_mechanical_review_contract(
    *,
    goal: ImplementationGoalContract,
    environment: CandidateEnvironmentManifest,
    evidence: tuple[DevelopmentEvidence, ...],
) -> MechanicalReviewContract | MechanicalReviewIndeterminate:
    """Compile the closed profile from exact owned project records."""

    if environment.goal_id != goal.id:
        return _indeterminate(ReviewIndeterminateReason.FOREIGN_RECORD, environment)
    if environment.developer_id == MECHANICAL_REVIEWER_ID:
        return _indeterminate(ReviewIndeterminateReason.FOREIGN_RECORD, environment)
    if len(evidence) != len(REQUIRED_FAULT_IDS):
        return _indeterminate(ReviewIndeterminateReason.INCOMPLETE_PROFILE, evidence)
    evidence_by_method = {item.command_or_method: item for item in evidence}
    if len(evidence_by_method) != len(evidence):
        return _indeterminate(ReviewIndeterminateReason.INCOMPLETE_PROFILE, evidence)
    bindings: list[FaultEvidenceBinding] = []
    candidate_shas: set[str] = set()
    for fault_id in REQUIRED_FAULT_IDS:
        method = f"{REVIEW_FAULT_PROFILE_VERSION}:{fault_id.value}"
        item = evidence_by_method.get(method)
        if item is None:
            return _indeterminate(ReviewIndeterminateReason.INCOMPLETE_PROFILE, evidence)
        if item.goal_id != goal.id or item.candidate_environment_id != environment.id:
            return _indeterminate(ReviewIndeterminateReason.FOREIGN_RECORD, item)
        if item.base_commit_sha != environment.base_commit_sha:
            return _indeterminate(ReviewIndeterminateReason.STALE_COMMIT, item)
        if item.gate_digest != goal.proposed_gate_digest:
            return _indeterminate(ReviewIndeterminateReason.GATE_MISMATCH, item)
        if item.kind is not EvidenceKind.PROPERTY_CHECK:
            return _indeterminate(ReviewIndeterminateReason.UNSUPPORTED_EVIDENCE, item)
        candidate_shas.add(item.candidate_commit_sha)
        bindings.append(FaultEvidenceBinding(fault_id=fault_id, evidence_id=item.id))
    if len(candidate_shas) != 1:
        return _indeterminate(ReviewIndeterminateReason.STALE_COMMIT, evidence)
    candidate_sha = next(iter(candidate_shas))
    payload = {
        "schema_version": 1,
        "profile_version": REVIEW_FAULT_PROFILE_VERSION,
        "goal_id": goal.id,
        "candidate_environment_id": environment.id,
        "base_commit_sha": environment.base_commit_sha,
        "candidate_commit_sha": candidate_sha,
        "gate_digest": goal.proposed_gate_digest,
        "developer_id": environment.developer_id,
        "reviewer_id": MECHANICAL_REVIEWER_ID,
        "invariant_ids": REQUIRED_INVARIANT_IDS,
        "fault_evidence": tuple(bindings),
        "semantic_claim": "bounded_profile_only",
        "promotion_authorized": False,
    }
    fingerprint = content_fingerprint("rci.mechanical-review-contract.v1", payload)
    return MechanicalReviewContract(
        id=f"mechanical-review-{fingerprint[:24]}",
        fingerprint=fingerprint,
        goal_id=goal.id,
        candidate_environment_id=environment.id,
        base_commit_sha=environment.base_commit_sha,
        candidate_commit_sha=candidate_sha,
        gate_digest=goal.proposed_gate_digest,
        developer_id=environment.developer_id,
        invariant_ids=REQUIRED_INVARIANT_IDS,
        fault_evidence=tuple(bindings),
    )


def baseline_review_probe(contract: MechanicalReviewContract) -> SeededReviewProbe:
    return SeededReviewProbe(
        candidate_commit_sha=contract.candidate_commit_sha,
        evidence_ids=tuple(sorted(item.evidence_id for item in contract.fault_evidence)),
        developer_id=contract.developer_id,
        reviewer_id=contract.reviewer_id,
        stages_separate=True,
        semantic_coverage=SemanticCoverage.UNKNOWN,
        gate_digest=contract.gate_digest,
        authority_roots_confined=True,
        replay_effect_free=True,
    )


def seed_review_fault(
    contract: MechanicalReviewContract, fault_id: ReviewFaultId
) -> SeededReviewProbe:
    """Return the one-field mutation for a registered review fault."""

    baseline = baseline_review_probe(contract)
    alternate_sha = "0" * 40 if contract.candidate_commit_sha != "0" * 40 else "1" * 40
    alternate_digest = "0" * 64 if contract.gate_digest != "0" * 64 else "1" * 64
    updates_by_fault: dict[ReviewFaultId, dict[str, object]] = {
        ReviewFaultId.EXACT_HEAD_SUBSTITUTION: {"candidate_commit_sha": alternate_sha},
        ReviewFaultId.EVIDENCE_SUBSTITUTION: {
            "evidence_ids": tuple(sorted((*baseline.evidence_ids[1:], "substituted-evidence")))
        },
        ReviewFaultId.SELF_REVIEW: {"reviewer_id": baseline.developer_id},
        ReviewFaultId.STAGE_COLLAPSE: {"stages_separate": False},
        ReviewFaultId.UNKNOWN_AS_SUCCESS: {"semantic_coverage": SemanticCoverage.CLAIMED_SUCCESS},
        ReviewFaultId.GATE_WEAKENING: {"gate_digest": alternate_digest},
        ReviewFaultId.ALLOWLIST_BROADENING: {"authority_roots_confined": False},
        ReviewFaultId.REPLAY_EFFECT_COLLAPSE: {"replay_effect_free": False},
    }
    updates = updates_by_fault[fault_id]
    return baseline.model_copy(update=updates)


def build_fault_observation_manifest(
    *,
    contract: MechanicalReviewContract,
    probes: tuple[tuple[ReviewFaultId, SeededReviewProbe], ...],
) -> FaultObservationManifest:
    evidence_by_fault = {item.fault_id: item.evidence_id for item in contract.fault_evidence}
    observations = tuple(
        sorted(
            (
                FaultObservation(
                    fault_id=fault_id,
                    evidence_id=evidence_by_fault[fault_id],
                    probe=probe,
                    reproducer_digest=_sha256_digest(_canonical_bytes(probe)),
                )
                for fault_id, probe in probes
            ),
            key=lambda item: item.fault_id,
        )
    )
    payload = {
        "schema_version": 1,
        "contract_id": contract.id,
        "contract_fingerprint": contract.fingerprint,
        "profile_version": REVIEW_FAULT_PROFILE_VERSION,
        "candidate_commit_sha": contract.candidate_commit_sha,
        "observations": observations,
    }
    fingerprint = content_fingerprint("rci.fault-observation-manifest.v1", payload)
    return FaultObservationManifest(
        id=f"fault-manifest-{fingerprint[:24]}",
        fingerprint=fingerprint,
        contract_id=contract.id,
        contract_fingerprint=contract.fingerprint,
        candidate_commit_sha=contract.candidate_commit_sha,
        observations=observations,
    )


def _classify_probe(
    contract: MechanicalReviewContract,
    observation: FaultObservation,
) -> FaultDisposition:
    fault_id = ReviewFaultId(observation.fault_id)
    baseline = baseline_review_probe(contract)
    expected = seed_review_fault(contract, fault_id)
    if observation.probe not in {baseline, expected}:
        return FaultDisposition.INDETERMINATE
    return (
        FaultDisposition.SURVIVED
        if _review_invariant_stands(contract, fault_id, observation.probe)
        else FaultDisposition.DETECTED
    )


def _review_invariant_stands(
    contract: MechanicalReviewContract,
    fault_id: ReviewFaultId,
    probe: SeededReviewProbe,
) -> bool:
    """Independently evaluate the invariant attacked by one registered mutation."""

    checks = {
        ReviewFaultId.EXACT_HEAD_SUBSTITUTION: (
            probe.candidate_commit_sha == contract.candidate_commit_sha
        ),
        ReviewFaultId.EVIDENCE_SUBSTITUTION: (
            probe.evidence_ids
            == tuple(sorted(item.evidence_id for item in contract.fault_evidence))
        ),
        ReviewFaultId.SELF_REVIEW: probe.reviewer_id != probe.developer_id,
        ReviewFaultId.STAGE_COLLAPSE: probe.stages_separate,
        ReviewFaultId.UNKNOWN_AS_SUCCESS: (probe.semantic_coverage is SemanticCoverage.UNKNOWN),
        ReviewFaultId.GATE_WEAKENING: probe.gate_digest == contract.gate_digest,
        ReviewFaultId.ALLOWLIST_BROADENING: probe.authority_roots_confined,
        ReviewFaultId.REPLAY_EFFECT_COLLAPSE: probe.replay_effect_free,
    }
    return checks[fault_id]


def assess_mechanical_review(
    *,
    contract: MechanicalReviewContract,
    manifest: FaultObservationManifest,
    evidence: tuple[DevelopmentEvidence, ...],
) -> MechanicalReviewAssessment:
    """Recompute every fault result and retain permanent semantic Unknown."""

    detected: list[ReviewFaultId] = []
    survived: list[ReviewFaultId] = []
    indeterminate: list[ReviewFaultId] = []
    profile_errors: list[str] = []
    evidence_by_id = {item.id: item for item in evidence}
    expected_bindings = {item.fault_id: item.evidence_id for item in contract.fault_evidence}
    observation_groups: dict[str, list[FaultObservation]] = {}
    for item in manifest.observations:
        observation_groups.setdefault(item.fault_id, []).append(item)
    for fault_id, items in observation_groups.items():
        if fault_id not in REQUIRED_FAULT_IDS:
            profile_errors.append(f"unknown-fault:{fault_id}")
        elif len(items) != 1:
            profile_errors.append(f"duplicate-fault:{fault_id}")
    manifest_exact = (
        manifest.contract_id == contract.id
        and manifest.contract_fingerprint == contract.fingerprint
        and manifest.candidate_commit_sha == contract.candidate_commit_sha
    )
    if not manifest_exact:
        profile_errors.append("manifest-pin-mismatch")
    for fault_id in REQUIRED_FAULT_IDS:
        grouped = observation_groups.get(fault_id, [])
        if not manifest_exact or len(grouped) != 1:
            indeterminate.append(fault_id)
            continue
        observation = grouped[0]
        evidence_record = evidence_by_id.get(observation.evidence_id)
        if (
            evidence_record is None
            or observation.evidence_id != expected_bindings[fault_id]
            or evidence_record.goal_id != contract.goal_id
            or evidence_record.candidate_environment_id != contract.candidate_environment_id
            or evidence_record.base_commit_sha != contract.base_commit_sha
            or evidence_record.candidate_commit_sha != contract.candidate_commit_sha
            or evidence_record.gate_digest != contract.gate_digest
            or evidence_record.kind is not EvidenceKind.PROPERTY_CHECK
            or evidence_record.command_or_method
            != f"{REVIEW_FAULT_PROFILE_VERSION}:{fault_id.value}"
            or evidence_record.observed_return.digest != observation.reproducer_digest
        ):
            indeterminate.append(fault_id)
            continue
        disposition = _classify_probe(contract, observation)
        expected_outcomes = {
            FaultDisposition.DETECTED: {EvidenceOutcome.PASS},
            FaultDisposition.SURVIVED: {EvidenceOutcome.FAIL},
            FaultDisposition.INDETERMINATE: {
                EvidenceOutcome.INDETERMINATE,
                EvidenceOutcome.UNSUPPORTED,
            },
        }
        if evidence_record.outcome not in expected_outcomes[disposition]:
            indeterminate.append(fault_id)
        elif disposition is FaultDisposition.DETECTED:
            detected.append(fault_id)
        elif disposition is FaultDisposition.SURVIVED:
            survived.append(fault_id)
        else:
            indeterminate.append(fault_id)
    outcome = (
        MechanicalReviewOutcome.INVALID
        if survived
        else MechanicalReviewOutcome.INDETERMINATE
        if indeterminate or profile_errors
        else MechanicalReviewOutcome.VALID_WITHIN_PROFILE
    )
    payload = {
        "schema_version": 1,
        "contract_id": contract.id,
        "contract_fingerprint": contract.fingerprint,
        "manifest_id": manifest.id,
        "outcome": outcome,
        "detected_fault_ids": tuple(sorted(detected)),
        "surviving_fault_ids": tuple(sorted(survived)),
        "indeterminate_fault_ids": tuple(sorted(indeterminate)),
        "profile_error_ids": tuple(sorted(profile_errors)),
        "evidence_ids": tuple(sorted({item.evidence_id for item in manifest.observations})),
        "semantic_residual": SemanticCoverage.UNKNOWN,
        "model_required": False,
        "independent_review_satisfied": False,
        "promotion_authorized": False,
    }
    fingerprint = content_fingerprint("rci.mechanical-review-assessment.v1", payload)
    return MechanicalReviewAssessment(
        id=f"mechanical-assessment-{fingerprint[:24]}",
        contract_id=contract.id,
        contract_fingerprint=contract.fingerprint,
        manifest_id=manifest.id,
        outcome=outcome,
        detected_fault_ids=tuple(sorted(detected)),
        surviving_fault_ids=tuple(sorted(survived)),
        indeterminate_fault_ids=tuple(sorted(indeterminate)),
        profile_error_ids=tuple(sorted(profile_errors)),
        evidence_ids=tuple(sorted({item.evidence_id for item in manifest.observations})),
    )


def parse_semantic_breaker_candidate(
    raw: bytes,
    *,
    expected_base_commit_sha: str,
    expected_candidate_commit_sha: str,
) -> SemanticBreakerCandidate | ModelReviewIndeterminate:
    """Parse one strict inert candidate; never interpret prose as JSON or warrant."""

    raw_digest = sha256(raw).hexdigest()
    try:
        raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return ModelReviewIndeterminate(
            reason=BreakerIndeterminateReason.INVALID_UTF8, raw_digest=raw_digest
        )
    try:
        candidate = SemanticBreakerCandidate.model_validate_json(raw, strict=True)
    except ValueError as error:
        reason = (
            BreakerIndeterminateReason.INVALID_LOCATION
            if "breaker location" in str(error)
            else BreakerIndeterminateReason.MALFORMED_JSON
        )
        return ModelReviewIndeterminate(reason=reason, raw_digest=raw_digest)
    if (
        candidate.base_commit_sha != expected_base_commit_sha
        or candidate.candidate_commit_sha != expected_candidate_commit_sha
    ):
        return ModelReviewIndeterminate(
            reason=BreakerIndeterminateReason.WRONG_COMMIT, raw_digest=raw_digest
        )
    if candidate.invariant_id not in REQUIRED_INVARIANT_IDS:
        return ModelReviewIndeterminate(
            reason=BreakerIndeterminateReason.UNKNOWN_INVARIANT, raw_digest=raw_digest
        )
    return candidate
