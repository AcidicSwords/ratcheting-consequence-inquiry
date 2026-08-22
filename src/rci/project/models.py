"""Strict records for recursive inquiry over the RCI repository itself.

These records do not give the runtime source-writing or Git authority.  They make a
development argument replayable: limitation, alternatives, sealed goal, candidate
evidence, independent review, and promotion remain different facts.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from rci.core.model import ArtifactRef, FrozenModel, Identifier, NonEmptyText, Sha256Digest
from rci.questions.models import QuestionContract

GitCommitSha = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]


def _canonical(values: tuple[str, ...], label: str, *, nonempty: bool = False) -> None:
    if nonempty and not values:
        raise ValueError(f"{label} must not be empty")
    if len(set(values)) != len(values) or tuple(sorted(values)) != values:
        raise ValueError(f"{label} must be unique and canonically ordered")


def _repository_relative_path(value: str, label: str) -> None:
    path = PurePosixPath(value)
    if (
        "\\" in value
        or path.is_absolute()
        or value != path.as_posix()
        or value in {"", "."}
        or ".." in path.parts
    ):
        raise ValueError(f"{label} must be a normalized repository-relative path")


class LimitationKind(StrEnum):
    THEORY = "theory"
    QUESTION = "question"
    PROBE = "probe"
    REPRESENTATION = "representation"
    METHOD = "method"
    EVIDENCE = "evidence"
    IMPLEMENTATION = "implementation"
    AUTHORITY = "authority"


class SuccessorKind(StrEnum):
    THEORY = "theory"
    QUESTION_REPERTOIRE = "question_repertoire"
    PROBE_REPERTOIRE = "probe_repertoire"
    REPRESENTATION = "representation"
    METHOD_REPERTOIRE = "method_repertoire"
    IMPLEMENTATION = "implementation"
    GOAL_DECOMPOSITION = "goal_decomposition"


class ProjectGainKind(StrEnum):
    REPAIRED_FAILURE = "repaired_failure"
    NEW_SEPARATOR = "new_separator"
    EXECUTABLE_RELATION = "executable_relation"
    COMPLEXITY_REDUCTION = "complexity_reduction"
    DEVELOPMENT_RECOVERY = "development_recovery"
    SCOPE_EXTENSION = "scope_extension"
    NEW_METHOD = "new_method"
    INDEPENDENT_CHECKABILITY = "independent_checkability"


class AdmissionOutcome(StrEnum):
    ADMIT = "admit"
    REJECT = "reject"
    INCONCLUSIVE = "inconclusive"


class EvidenceKind(StrEnum):
    REPRODUCTION = "reproduction"
    TEST = "test"
    STATIC_CHECK = "static_check"
    PROPERTY_CHECK = "property_check"
    BENCHMARK = "benchmark"
    SOLVER = "solver"
    REFERENCE_IMPLEMENTATION = "reference_implementation"
    BUILD = "build"
    CI = "ci"
    RESEARCH = "research"


class EvidenceOutcome(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    INDETERMINATE = "indeterminate"
    UNSUPPORTED = "unsupported"


class ReviewOutcome(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    INDETERMINATE = "indeterminate"


class ProjectDisposition(StrEnum):
    REPLACE = "replace"
    KEEP = "keep"
    FRONTIER = "frontier"
    REJECT = "reject"


class PromotionOutcome(StrEnum):
    PROPOSED = "proposed"
    MERGED = "merged"
    REJECTED = "rejected"
    REVERT_REQUIRED = "revert_required"


class CyclePhase(StrEnum):
    ANCHORED = "anchored"
    LIMITATION_RECORDED = "limitation_recorded"
    BASIS_TESTED = "basis_tested"
    FRONTIER_CONSTRUCTED = "frontier_constructed"
    GOAL_SEALED = "goal_sealed"
    CANDIDATE_DEVELOPED = "candidate_developed"
    LOCALLY_VERIFIED = "locally_verified"
    INDEPENDENTLY_REVIEWED = "independently_reviewed"
    PR_VERIFIED = "pr_verified"
    MERGED = "merged"
    POSTMERGE_VERIFIED = "postmerge_verified"
    RETAINED = "retained"


class StopReason(StrEnum):
    NO_CONSEQUENTIAL_RESIDUE = "no_consequential_residue"
    NO_DISCRIMINATOR = "no_discriminator"
    REPEATED_BLOCKER = "repeated_blocker"
    AUTHORITY_EXPANSION_REQUIRED = "authority_expansion_required"
    EVIDENCE_INVALID = "evidence_invalid"
    EVIDENCE_INDETERMINATE = "evidence_indeterminate"
    UNKNOWN = "unknown"


class ProjectAnchor(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    repository: NonEmptyText
    protected_branch: Identifier
    commit_sha: GitCommitSha
    tree_digest: Sha256Digest
    authority_digest: Sha256Digest
    gate_digest: Sha256Digest
    clean: Literal[True]


class CapabilityLimitation(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    anchor_id: Identifier
    kind: LimitationKind
    current_capability: NonEmptyText
    missing_capability: NonEmptyText
    consequential_boundary: NonEmptyText
    protected_consequence_ids: tuple[Identifier, ...]
    observed_evidence: tuple[ArtifactRef, ...]
    existing_question_contract_keys: tuple[Identifier, ...] = ()
    blocked_dependency_ids: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def validate_limitation(self) -> CapabilityLimitation:
        _canonical(self.protected_consequence_ids, "protected consequences", nonempty=True)
        _canonical(self.existing_question_contract_keys, "existing question contracts")
        _canonical(self.blocked_dependency_ids, "blocked dependencies")
        if not self.observed_evidence:
            raise ValueError("a project limitation requires preserved observation evidence")
        return self


class ConsequentialReturn(FrozenModel):
    return_class_id: Identifier
    downstream_state_id: Identifier
    downstream_obligation_kind: LimitationKind


class QuestionContractCandidate(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    limitation_id: Identifier
    contract: QuestionContract
    typed_referent_ids: tuple[Identifier, ...]
    precondition_ids: tuple[Identifier, ...]
    possible_returns: tuple[ConsequentialReturn, ...]
    comparison_policy_id: Identifier
    downstream_consumer_ids: tuple[Identifier, ...]
    falsifying_attack_ids: tuple[Identifier, ...]
    status: Literal["inert_candidate"] = "inert_candidate"

    @model_validator(mode="after")
    def validate_candidate(self) -> QuestionContractCandidate:
        for values, label, nonempty in (
            (self.typed_referent_ids, "question referents", True),
            (self.precondition_ids, "question preconditions", False),
            (self.downstream_consumer_ids, "question consumers", True),
            (self.falsifying_attack_ids, "question attacks", True),
        ):
            _canonical(values, label, nonempty=nonempty)
        states = {item.downstream_state_id for item in self.possible_returns}
        if len(states) < 2:
            raise ValueError("a new question must expose two consequentially distinct returns")
        if self.contract.maturity.value == "stable":
            raise ValueError("generated question candidates cannot declare themselves stable")
        return self


class QuestionRepertoireDecision(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    candidate_id: Identifier
    outcome: AdmissionOutcome
    controller_policy_version: Identifier
    evidence_ids: tuple[Identifier, ...]
    admitted_profile_id: Literal["recursive-project-v1"] | None = None

    @model_validator(mode="after")
    def validate_decision(self) -> QuestionRepertoireDecision:
        _canonical(self.evidence_ids, "question admission evidence", nonempty=True)
        if (self.outcome is AdmissionOutcome.ADMIT) != (self.admitted_profile_id is not None):
            raise ValueError("only admission may name the confined recursive project profile")
        return self


class MethodBindingCandidate(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    limitation_id: Identifier
    relation_id: Identifier
    native_field: NonEmptyText
    method_id: Identifier
    primary_source_urls: tuple[NonEmptyText, ...]
    source_artifacts: tuple[ArtifactRef, ...]
    assumption_ids: tuple[Identifier, ...]
    applicability_check_ids: tuple[Identifier, ...]
    license_id: Identifier
    adapter_required: bool
    status: Literal["inert_candidate"] = "inert_candidate"

    @model_validator(mode="after")
    def validate_method(self) -> MethodBindingCandidate:
        if not self.primary_source_urls or not self.source_artifacts:
            raise ValueError("method binding requires preserved primary sources")
        _canonical(self.assumption_ids, "method assumptions", nonempty=True)
        _canonical(self.applicability_check_ids, "method applicability checks", nonempty=True)
        return self


class MethodAdmissionDecision(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    candidate_id: Identifier
    outcome: AdmissionOutcome
    method_policy_version: Identifier
    evidence_ids: tuple[Identifier, ...]
    implementation_goal_id: Identifier | None = None

    @model_validator(mode="after")
    def validate_decision(self) -> MethodAdmissionDecision:
        _canonical(self.evidence_ids, "method admission evidence", nonempty=True)
        return self


class ProjectCost(FrozenModel):
    axis: Identifier
    value: int | None = Field(default=None, ge=0)


class CapabilitySuccessorCandidate(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    anchor_id: Identifier
    limitation_id: Identifier
    kind: SuccessorKind
    current_state: NonEmptyText
    desired_state: NonEmptyText
    preserved_capability_ids: tuple[Identifier, ...]
    explicitly_disposed_capability_ids: tuple[Identifier, ...] = ()
    gain_kinds: tuple[ProjectGainKind, ...]
    discriminator_id: Identifier | None
    evidence_mechanism_ids: tuple[Identifier, ...]
    estimated_costs: tuple[ProjectCost, ...]
    reversible: bool

    @model_validator(mode="after")
    def validate_successor(self) -> CapabilitySuccessorCandidate:
        for values, label, nonempty in (
            (self.preserved_capability_ids, "preserved capabilities", True),
            (self.explicitly_disposed_capability_ids, "disposed capabilities", False),
            (tuple(item.value for item in self.gain_kinds), "project gains", True),
            (self.evidence_mechanism_ids, "evidence mechanisms", True),
            (tuple(item.axis for item in self.estimated_costs), "cost axes", True),
        ):
            _canonical(values, label, nonempty=nonempty)
        if set(self.preserved_capability_ids) & set(self.explicitly_disposed_capability_ids):
            raise ValueError("a predecessor capability cannot be preserved and disposed")
        return self


class CapabilityFrontier(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    anchor_id: Identifier
    limitation_id: Identifier
    candidate_ids: tuple[Identifier, ...]
    nondominated_candidate_ids: tuple[Identifier, ...]
    incomparable_pairs: tuple[tuple[Identifier, Identifier], ...]
    selected_discriminator_candidate_id: Identifier | None
    selection_policy_version: Literal["project-frontier-v1"] = "project-frontier-v1"
    status: Literal["ready", "unknown"]

    @model_validator(mode="after")
    def validate_frontier(self) -> CapabilityFrontier:
        _canonical(self.candidate_ids, "frontier candidates", nonempty=True)
        _canonical(self.nondominated_candidate_ids, "nondominated candidates", nonempty=True)
        if not set(self.nondominated_candidate_ids) <= set(self.candidate_ids):
            raise ValueError("nondominated candidates must belong to the frontier")
        if self.status == "ready" and self.selected_discriminator_candidate_id is None:
            raise ValueError("a ready frontier must select the smallest discriminator")
        if self.status == "unknown" and self.selected_discriminator_candidate_id is not None:
            raise ValueError("an unknown frontier cannot fabricate a discriminator")
        return self


class ImplementationGoalContract(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    cycle_id: Identifier
    anchor_id: Identifier
    frontier_id: Identifier
    candidate_id: Identifier
    current: NonEmptyText
    desired: NonEmptyText
    separator: NonEmptyText
    expected_incumbent_return: NonEmptyText
    expected_candidate_return: NonEmptyText
    preserve_capability_ids: tuple[Identifier, ...]
    acceptance_commands: tuple[NonEmptyText, ...]
    allowed_mutation_roots: tuple[NonEmptyText, ...]
    forbidden_authority_roots: tuple[NonEmptyText, ...]
    assumption_ids: tuple[Identifier, ...]
    incumbent_gate_digest: Sha256Digest
    proposed_gate_digest: Sha256Digest
    rollback_condition: NonEmptyText
    reopening_condition: NonEmptyText

    @model_validator(mode="after")
    def validate_goal(self) -> ImplementationGoalContract:
        for values, label in (
            (self.preserve_capability_ids, "goal preserved capabilities"),
            (self.acceptance_commands, "goal acceptance commands"),
            (self.allowed_mutation_roots, "allowed mutation roots"),
            (self.forbidden_authority_roots, "forbidden authority roots"),
            (self.assumption_ids, "goal assumptions"),
        ):
            _canonical(values, label, nonempty=True)
        for value in (*self.allowed_mutation_roots, *self.forbidden_authority_roots):
            _repository_relative_path(value, "goal mutation root")
        for allowed in self.allowed_mutation_roots:
            if any(
                allowed == forbidden or allowed.startswith(f"{forbidden}/")
                for forbidden in self.forbidden_authority_roots
            ):
                raise ValueError("allowed mutation roots cannot enter forbidden authority roots")
        return self


class ImplementationGoalCandidate(FrozenModel):
    """Inert deterministic derivation of one possible implementation Goal."""

    schema_version: Literal[1] = 1
    id: Identifier
    compiler_version: Literal["implementation-goal-compiler-v1"] = "implementation-goal-compiler-v1"
    status: Literal["inert_candidate"] = "inert_candidate"
    question_candidate_id: Identifier
    question_candidate_fingerprint: Sha256Digest
    question_decision_id: Identifier
    question_decision_fingerprint: Sha256Digest
    compiled_question_id: Identifier
    compiled_question_fingerprint: Sha256Digest
    source_obligation_id: Identifier
    source_obligation_fingerprint: Sha256Digest
    effect_request_id: Identifier
    accepted_decode_id: Identifier
    accepted_decode_fingerprint: Sha256Digest
    source_claim_id: Identifier
    source_claim_fingerprint: Sha256Digest
    downstream_obligation_id: Identifier
    downstream_obligation_fingerprint: Sha256Digest
    matched_return_class_id: Literal["goal-derivation-required"]
    anchor_id: Identifier
    anchor_fingerprint: Sha256Digest
    limitation_id: Identifier
    limitation_fingerprint: Sha256Digest
    frontier_id: Identifier
    frontier_fingerprint: Sha256Digest
    selected_candidate_id: Identifier
    selected_candidate_fingerprint: Sha256Digest
    binding_revision: Identifier
    scope_fingerprint: Sha256Digest
    protected_horizon_id: Identifier
    acceptance_registry_version: Literal["project-gate-registry-v1"] = "project-gate-registry-v1"
    mutation_registry_version: Literal["project-mutation-registry-v1"] = (
        "project-mutation-registry-v1"
    )
    goal: ImplementationGoalContract
    goal_fingerprint: Sha256Digest

    @model_validator(mode="after")
    def validate_candidate(self) -> ImplementationGoalCandidate:
        if (
            self.goal.anchor_id != self.anchor_id
            or self.goal.frontier_id != self.frontier_id
            or self.goal.candidate_id != self.selected_candidate_id
        ):
            raise ValueError("derived Goal must preserve its exact project inputs")
        return self


class GoalAdmissionDecision(FrozenModel):
    """One total controller decision over an exact inert Goal candidate."""

    schema_version: Literal[1] = 1
    id: Identifier
    candidate_id: Identifier
    candidate_fingerprint: Sha256Digest
    outcome: AdmissionOutcome
    controller_policy_version: Literal["goal-admission-policy-v1"] = "goal-admission-policy-v1"
    evidence_record_ids: tuple[Identifier, ...]
    admitted_goal_id: Identifier | None = None

    @model_validator(mode="after")
    def validate_decision(self) -> GoalAdmissionDecision:
        _canonical(self.evidence_record_ids, "Goal admission evidence", nonempty=True)
        if (self.outcome is AdmissionOutcome.ADMIT) != (self.admitted_goal_id is not None):
            raise ValueError("only Goal admission may name the derived Goal")
        return self


class CandidateEnvironmentManifest(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    goal_id: Identifier
    developer_id: Identifier
    base_commit_sha: GitCommitSha
    candidate_branch: Identifier
    worktree_path: NonEmptyText
    initial_tree_digest: Sha256Digest
    toolchain_artifact: ArtifactRef
    toolchain_digest: Sha256Digest
    direct_promotion_authorized: Literal[False] = False


class DevelopmentEvidence(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    goal_id: Identifier
    candidate_environment_id: Identifier
    kind: EvidenceKind
    command_or_method: NonEmptyText
    outcome: EvidenceOutcome
    observed_return: ArtifactRef
    base_commit_sha: GitCommitSha
    candidate_commit_sha: GitCommitSha
    gate_digest: Sha256Digest


class IndependentReview(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    goal_id: Identifier
    candidate_environment_id: Identifier
    reviewer_id: Identifier
    reviewer_context_digest: Sha256Digest
    reviewed_commit_sha: GitCommitSha
    evidence_ids: tuple[Identifier, ...]
    outcome: ReviewOutcome
    findings_artifact: ArtifactRef

    @model_validator(mode="after")
    def validate_review(self) -> IndependentReview:
        _canonical(self.evidence_ids, "review evidence", nonempty=True)
        return self


class ProjectSuccessorDecision(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    goal_id: Identifier
    candidate_id: Identifier
    candidate_environment_id: Identifier
    review_id: Identifier
    evidence_ids: tuple[Identifier, ...]
    disposition: ProjectDisposition
    preserved_capability_ids: tuple[Identifier, ...]
    explicitly_disposed_capability_ids: tuple[Identifier, ...] = ()
    gain_kinds: tuple[ProjectGainKind, ...] = ()
    reason: NonEmptyText

    @model_validator(mode="after")
    def validate_successor(self) -> ProjectSuccessorDecision:
        for values, label in (
            (self.evidence_ids, "successor evidence"),
            (self.preserved_capability_ids, "successor preserved capabilities"),
            (self.explicitly_disposed_capability_ids, "successor disposed capabilities"),
            (tuple(item.value for item in self.gain_kinds), "successor gains"),
        ):
            _canonical(
                values,
                label,
                nonempty=label in {"successor evidence", "successor preserved capabilities"},
            )
        if self.disposition is ProjectDisposition.REPLACE and not self.gain_kinds:
            raise ValueError("implementation replacement requires a typed strict gain")
        return self


class CheckConclusion(FrozenModel):
    context: NonEmptyText
    conclusion: Literal["success", "failure", "cancelled", "skipped"]


class PromotionDecision(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    successor_decision_id: Identifier
    candidate_commit_sha: GitCommitSha
    pull_request_url: NonEmptyText
    required_checks: tuple[CheckConclusion, ...]
    outcome: PromotionOutcome
    merged_commit_sha: GitCommitSha | None = None

    @model_validator(mode="after")
    def validate_promotion(self) -> PromotionDecision:
        contexts = tuple(item.context for item in self.required_checks)
        _canonical(contexts, "promotion checks", nonempty=True)
        if self.outcome is PromotionOutcome.MERGED:
            if self.merged_commit_sha is None or any(
                item.conclusion != "success" for item in self.required_checks
            ):
                raise ValueError(
                    "merged promotion requires an exact merge SHA and all checks passing"
                )
        elif self.merged_commit_sha is not None:
            raise ValueError("only a merged promotion may name a merge SHA")
        return self


class RecursiveCycleCheckpoint(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    cycle_id: Identifier
    phase: CyclePhase
    predecessor_id: Identifier | None
    record_ids: tuple[Identifier, ...]
    report_artifact: ArtifactRef

    @model_validator(mode="after")
    def validate_checkpoint(self) -> RecursiveCycleCheckpoint:
        _canonical(self.record_ids, "cycle checkpoint records", nonempty=True)
        if self.predecessor_id == self.id:
            raise ValueError("cycle checkpoint cannot succeed itself")
        return self


class RecursiveStopDisposition(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    cycle_id: Identifier
    reason: StopReason
    consequential_residual_ids: tuple[Identifier, ...] = ()
    blocked_dependency_ids: tuple[Identifier, ...] = ()
    evidence_artifact: ArtifactRef

    @model_validator(mode="after")
    def validate_stop(self) -> RecursiveStopDisposition:
        _canonical(self.consequential_residual_ids, "stop residuals")
        _canonical(self.blocked_dependency_ids, "stop dependencies")
        if self.reason is StopReason.NO_CONSEQUENTIAL_RESIDUE and self.consequential_residual_ids:
            raise ValueError("no-residue stop cannot retain consequential residue")
        return self
