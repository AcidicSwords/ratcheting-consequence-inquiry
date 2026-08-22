"""Strict G2B consolidation, field-evaluation, and learned-probe records."""

from __future__ import annotations

from enum import StrEnum
from hashlib import sha256
from typing import Literal

from pydantic import Field, JsonValue, field_validator, model_validator

from rci.claims.models import Scope, content_fingerprint, freeze_json
from rci.core.model import FrozenModel, Identifier, Sha256Digest
from rci.memory.models import OwnedMemoryRef
from rci.probes.models import ProbeIdentity, SemanticField
from rci.warrant.models import CheckReference

SchemaVersion = Literal[1]


def _canonical(values: tuple[str, ...], name: str) -> None:
    if len(set(values)) != len(values) or tuple(sorted(values)) != values:
        raise ValueError(f"{name} must be unique and canonically sorted")


class ConsolidationSourceRole(StrEnum):
    RECENT_EPISODE = "recent_episode"
    OLDER_EXCEPTION = "older_exception"
    COUNTEREXAMPLE = "counterexample"


class ConsolidationStatus(StrEnum):
    READY = "ready"
    INSUFFICIENT_DIVERSITY = "insufficient_diversity"


class ConsolidationPolicy(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Literal["consolidation-interleave-v1"] = "consolidation-interleave-v1"
    version: Literal["1"] = "1"
    recent_limit: Literal[4] = 4
    exception_limit: Literal[4] = 4
    counterexample_limit: Literal[4] = 4
    minimum_distinct_episodes: Literal[2] = 2


class ConsolidationSource(FrozenModel):
    schema_version: SchemaVersion = 1
    role: ConsolidationSourceRole
    reference: OwnedMemoryRef
    semantic_sequence: int = Field(ge=0)


class ConsolidationCheckpoint(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    policy: ConsolidationPolicy
    source_sequence: int = Field(ge=0)
    source_index_fingerprint: Sha256Digest
    scope_fingerprint: Identifier
    binding_revision: Identifier
    protected_horizon_id: Identifier
    sources: tuple[ConsolidationSource, ...]
    status: ConsolidationStatus

    @model_validator(mode="after")
    def validate_checkpoint(self) -> ConsolidationCheckpoint:
        keys = tuple(source.reference.key for source in self.sources)
        if len(set(keys)) != len(keys):
            raise ValueError("consolidation sources must be deduplicated")
        episode_count = sum(
            source.role
            in {ConsolidationSourceRole.RECENT_EPISODE, ConsolidationSourceRole.OLDER_EXCEPTION}
            for source in self.sources
        )
        expected = (
            ConsolidationStatus.READY
            if episode_count >= self.policy.minimum_distinct_episodes
            else ConsolidationStatus.INSUFFICIENT_DIVERSITY
        )
        if self.status is not expected:
            raise ValueError("consolidation status does not match source diversity")
        return self


class CandidateSupportBoundary(FrozenModel):
    schema_version: SchemaVersion = 1
    scope: Scope
    applicability_guard_id: Identifier
    assumption_ids: tuple[Identifier, ...] = ()
    required_dependency_ids: tuple[Identifier, ...] = ()
    open_dependency_obligation_ids: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def validate_boundary(self) -> CandidateSupportBoundary:
        _canonical(self.assumption_ids, "candidate assumptions")
        _canonical(self.required_dependency_ids, "candidate dependencies")
        _canonical(self.open_dependency_obligation_ids, "candidate open dependencies")
        if not self.applicability_guard_id:
            raise ValueError("candidate applicability guard is required")
        return self


class ConsolidationCandidate(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    checkpoint_id: Identifier
    generalization_claim_id: Identifier
    boundary: CandidateSupportBoundary
    challenge_obligation_ids: tuple[Identifier, ...]
    status: Literal["provisional"] = "provisional"

    @model_validator(mode="after")
    def validate_candidate(self) -> ConsolidationCandidate:
        _canonical(self.challenge_obligation_ids, "consolidation challenges")
        if not self.challenge_obligation_ids:
            raise ValueError("consolidation requires an explicit challenge obligation")
        return self


class MemoryPatchKind(StrEnum):
    GUARD_CHANGE = "guard_change"
    RELATION_CHANGE = "relation_change"
    SPLIT = "split"
    REBIND = "rebind"


class DependencyDispositionKind(StrEnum):
    TRANSPORTED = "transported"
    HARD_DISCHARGED = "hard_discharged"


class DependencyDisposition(FrozenModel):
    dependency_id: Identifier
    kind: DependencyDispositionKind
    warrant_decision_id: Identifier | None = None

    @model_validator(mode="after")
    def validate_disposition(self) -> DependencyDisposition:
        if self.kind is DependencyDispositionKind.HARD_DISCHARGED:
            if self.warrant_decision_id is None:
                raise ValueError("hard dependency discharge requires a warrant decision")
        elif self.warrant_decision_id is not None:
            raise ValueError("transported dependencies do not carry a discharge warrant")
        return self


class MemoryPatchCandidate(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    target_lemma_id: Identifier
    triggering_mismatch_id: Identifier
    triggering_return_id: Identifier
    proposed_claim_id: Identifier
    patch_kind: MemoryPatchKind
    predecessor_support_route_ids: tuple[Identifier, ...]
    dependency_dispositions: tuple[DependencyDisposition, ...]
    challenge_obligation_ids: tuple[Identifier, ...]
    scope_fingerprint: Identifier
    status: Literal["provisional"] = "provisional"

    @model_validator(mode="after")
    def validate_patch(self) -> MemoryPatchCandidate:
        _canonical(self.predecessor_support_route_ids, "predecessor support routes")
        _canonical(self.challenge_obligation_ids, "patch challenges")
        dependency_ids = tuple(item.dependency_id for item in self.dependency_dispositions)
        _canonical(dependency_ids, "dependency dispositions")
        if not self.predecessor_support_route_ids or not self.challenge_obligation_ids:
            raise ValueError("memory patch requires predecessor support and challenge obligations")
        return self


class ReconsolidationLink(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    memory_patch_id: Identifier
    predecessor_lemma_id: Identifier
    successor_lemma_id: Identifier
    correction_id: Identifier
    warrant_decision_id: Identifier


class SemanticFieldPolicy(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Literal["conservative-question-field-v1"] = "conservative-question-field-v1"
    version: Literal["1"] = "1"
    maximum_items: Literal[32] = 32


class SemanticFieldEvaluationStatus(StrEnum):
    VALID = "valid"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"


class SemanticFieldEvaluation(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    policy: SemanticFieldPolicy
    field_id: Identifier
    field_fingerprint: Sha256Digest
    field: SemanticField
    source_sequence: int = Field(ge=0)
    source_index_fingerprint: Sha256Digest
    probe_fingerprint: Identifier
    required_structure_ids: tuple[Identifier, ...]
    included_structure_ids: tuple[Identifier, ...]
    overflow_structure_ids: tuple[Identifier, ...]
    irrelevant_structure_ids: tuple[Identifier, ...]
    status: SemanticFieldEvaluationStatus

    @model_validator(mode="after")
    def validate_evaluation(self) -> SemanticFieldEvaluation:
        if self.field.id != self.field_id:
            raise ValueError("semantic-field evaluation must embed its exact derived field")
        actual_fingerprint = sha256(self.field.model_dump_json().encode()).hexdigest()
        if actual_fingerprint != self.field_fingerprint:
            raise ValueError("semantic-field fingerprint does not match the embedded field")
        if self.field.probe_fingerprint != self.probe_fingerprint:
            raise ValueError("semantic field and evaluation must name the same probe")
        for values, name in (
            (self.required_structure_ids, "required structures"),
            (self.included_structure_ids, "included structures"),
            (self.overflow_structure_ids, "overflow structures"),
            (self.irrelevant_structure_ids, "irrelevant structures"),
        ):
            _canonical(values, name)
        if set(self.included_structure_ids) & set(self.overflow_structure_ids):
            raise ValueError("field items cannot be both included and overflow")
        missing = set(self.required_structure_ids) - set(self.included_structure_ids)
        expected = (
            SemanticFieldEvaluationStatus.INCOMPLETE
            if missing or self.overflow_structure_ids
            else SemanticFieldEvaluationStatus.VALID
        )
        if self.status is not expected:
            raise ValueError("field status does not match exact coverage")
        return self


class RepresentationGapKind(StrEnum):
    NO_SEPARATOR = "no_separator"
    BINDING_INADEQUATE = "binding_inadequate"
    PROBE_BASIS_INADEQUATE = "probe_basis_inadequate"
    LANGUAGE_INADEQUATE = "language_inadequate"


class RepresentationGap(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    obligation_id: Identifier
    state_or_claim_ids: tuple[Identifier, ...]
    protected_consequence_difference_id: Identifier
    failed_probe_fingerprints: tuple[Identifier, ...]
    kind: RepresentationGapKind
    scope_fingerprint: Identifier
    binding_revision: Identifier
    protected_horizon_id: Identifier

    @model_validator(mode="after")
    def validate_gap(self) -> RepresentationGap:
        _canonical(self.state_or_claim_ids, "gap source ids")
        _canonical(self.failed_probe_fingerprints, "failed probes")
        if not self.failed_probe_fingerprints:
            raise ValueError("representation gap requires at least one failed probe")
        return self


class LearnedProbeCandidate(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    representation_gap_id: Identifier
    probe_identity: ProbeIdentity
    generated_payload: JsonValue
    challenge_obligation_ids: tuple[Identifier, ...]
    status: Literal["provisional"] = "provisional"

    @field_validator("generated_payload")
    @classmethod
    def freeze_payload(cls, value: JsonValue) -> JsonValue:
        return freeze_json(value)

    @model_validator(mode="after")
    def validate_probe_candidate(self) -> LearnedProbeCandidate:
        if self.probe_identity.question_contract_key != "learned-recurrent-probe@1.0.0":
            raise ValueError("learned probes use the fixed inert learned-probe contract")
        _canonical(self.challenge_obligation_ids, "probe challenges")
        if not self.challenge_obligation_ids:
            raise ValueError("learned probe requires attack obligations")
        return self


class ProbeSample(FrozenModel):
    observation_id: Identifier
    protected_consequence_class_id: Identifier
    existing_basis_class_id: Identifier
    candidate_value_id: Identifier

    @property
    def fingerprint(self) -> str:
        return content_fingerprint("rci.probe-sample.v1", self)


class ProbeEvaluationProtocol(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Literal["finite-stratified-holdout-v1"] = "finite-stratified-holdout-v1"
    version: Literal["1"] = "1"
    holdout_denominator: Literal[4] = 4


class ProbeEvaluation(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    candidate_probe_id: Identifier
    protocol: ProbeEvaluationProtocol
    sample_index_fingerprint: Sha256Digest
    samples: tuple[ProbeSample, ...]
    training_observation_ids: tuple[Identifier, ...]
    holdout_observation_ids: tuple[Identifier, ...]
    training_discrimination_gain: int = Field(ge=0)
    holdout_discrimination_gain: int = Field(ge=0)
    protected_error_count: int = Field(ge=0)
    redundancy_check: CheckReference
    protected_behavior_check: CheckReference
    evaluation_proposition_id: Identifier

    @model_validator(mode="after")
    def validate_probe_evaluation(self) -> ProbeEvaluation:
        _canonical(self.training_observation_ids, "training observations")
        _canonical(self.holdout_observation_ids, "holdout observations")
        if set(self.training_observation_ids) & set(self.holdout_observation_ids):
            raise ValueError("training and holdout observations must be disjoint")
        if not self.training_observation_ids or not self.holdout_observation_ids:
            raise ValueError("probe evaluation requires training and holdout observations")
        sample_ids = tuple(sorted(item.observation_id for item in self.samples))
        if len(sample_ids) != len(set(sample_ids)) or sample_ids != tuple(
            sorted((*self.training_observation_ids, *self.holdout_observation_ids))
        ):
            raise ValueError("probe samples must exactly cover training and holdout ids")
        return self


class ProbeAdmissionOutcome(StrEnum):
    ADMIT = "admit"
    REJECT = "reject"
    INCONCLUSIVE = "inconclusive"


class ProbeAdmissionDecision(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    candidate_probe_id: Identifier
    evaluation_id: Identifier
    controller_policy_version: Literal["g2b-probe-admission-v1"] = "g2b-probe-admission-v1"
    outcome: ProbeAdmissionOutcome
    controller_id: Identifier
