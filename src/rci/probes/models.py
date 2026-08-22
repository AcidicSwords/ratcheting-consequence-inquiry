"""Strict cognitive records; effect/return/decode authority remains in ``rci.core``."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import JsonValue, field_validator, model_validator

from rci.claims.models import BoundArgument, FrozenModel, content_fingerprint, freeze_json


class ProbeIdentity(FrozenModel):
    question_contract_key: str
    relational_role: str
    binding_schema_id: str
    binding_revision: str
    scope_fingerprint: str
    comparison_semantics_id: str
    applicability_guard_id: str
    protected_horizon_id: str

    @model_validator(mode="after")
    def validate_identity(self) -> ProbeIdentity:
        if any(
            not value
            for value in (
                self.question_contract_key,
                self.relational_role,
                self.binding_schema_id,
                self.binding_revision,
                self.scope_fingerprint,
                self.comparison_semantics_id,
                self.applicability_guard_id,
                self.protected_horizon_id,
            )
        ):
            raise ValueError("all probe identity coordinates are required")
        return self

    @property
    def fingerprint(self) -> str:
        return content_fingerprint("rci.probe-identity.v1", self)


class ComparabilityBridge(FrozenModel):
    from_probe_fingerprint: str
    to_probe_fingerprint: str
    comparison_proposition_id: str
    scope_fingerprint: str
    warrant_lemma_id: str

    @model_validator(mode="after")
    def validate_bridge(self) -> ComparabilityBridge:
        if any(
            not value
            for value in (
                self.from_probe_fingerprint,
                self.to_probe_fingerprint,
                self.comparison_proposition_id,
                self.scope_fingerprint,
                self.warrant_lemma_id,
            )
        ):
            raise ValueError("comparability bridges require exact proposition, scope, and warrant")
        return self

    def connects(self, left: str, right: str) -> bool:
        return {self.from_probe_fingerprint, self.to_probe_fingerprint} == {left, right}


class ProbeEvent(FrozenModel):
    id: str
    probe_identity: ProbeIdentity
    bound_referents: tuple[BoundArgument, ...]
    binding_revision: str
    state_revision: int
    semantic_field_id: str
    generated_answer_claim_id: str | None = None
    external_return_ids: tuple[str, ...] = ()
    interpretation_claim_ids: tuple[str, ...] = ()
    sequence_index: int
    comparability_bridge: ComparabilityBridge | None = None
    fresh_observation_required: bool = False
    prior_answer_exposure: Literal[
        "not_applicable", "withheld_until_capture", "exposed_before_capture"
    ] = "not_applicable"

    @field_validator("state_revision", "sequence_index")
    @classmethod
    def validate_nonnegative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("revision and sequence values must be nonnegative")
        return value

    @model_validator(mode="after")
    def validate_event(self) -> ProbeEvent:
        if not self.id or not self.binding_revision or not self.semantic_field_id:
            raise ValueError("probe event identity, binding, and semantic field are required")
        names = [argument.name for argument in self.bound_referents]
        if len(set(names)) != len(names):
            raise ValueError("probe bound referent names must be unique")
        for collection in (self.external_return_ids, self.interpretation_claim_ids):
            if len(set(collection)) != len(collection):
                raise ValueError("probe event references must be unique")
        if self.fresh_observation_required:
            if not self.external_return_ids:
                raise ValueError("fresh observations require an actually captured return")
            if self.prior_answer_exposure != "withheld_until_capture":
                raise ValueError("fresh observation must withhold prior answers until capture")
        return self


class ProbeTrace(FrozenModel):
    probe_fingerprint: str
    events: tuple[ProbeEvent, ...]
    protected_horizon_id: str
    comparison_policy_id: str
    active_guard_id: str
    reopening_condition_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_trace(self) -> ProbeTrace:
        if any(event.probe_identity.fingerprint != self.probe_fingerprint for event in self.events):
            raise ValueError("trace contains an event with a different probe identity")
        sequences = [event.sequence_index for event in self.events]
        if sequences != sorted(sequences) or len(set(sequences)) != len(sequences):
            raise ValueError("probe trace events must have a strict sequence order")
        event_ids = [event.id for event in self.events]
        if len(set(event_ids)) != len(event_ids):
            raise ValueError("probe trace event ids must be unique")
        return self


class RelevanceStatus(StrEnum):
    ACTIVE = "active"
    UNDETERMINED = "undetermined"
    IRRELEVANT = "irrelevant"


class SemanticItem(FrozenModel):
    structure_id: str
    relevance: RelevanceStatus
    irrelevance_warrant_id: str | None = None
    reopening_condition_id: str | None = None

    @model_validator(mode="after")
    def validate_item(self) -> SemanticItem:
        if not self.structure_id:
            raise ValueError("semantic structure identity is required")
        if self.relevance is RelevanceStatus.IRRELEVANT:
            if self.irrelevance_warrant_id is None or self.reopening_condition_id is None:
                raise ValueError("irrelevant structure requires warrant and reopening condition")
        elif self.irrelevance_warrant_id is not None:
            raise ValueError("only guarded irrelevant structure carries an irrelevance warrant")
        return self


class SemanticField(FrozenModel):
    id: str
    probe_fingerprint: str
    protected_horizon_id: str
    items: tuple[SemanticItem, ...]
    same_probe_history_event_ids: tuple[str, ...] = ()
    cross_probe_trace_ids: tuple[str, ...] = ()
    retrieval_result_ids: tuple[str, ...] = ()
    method_contract_ids: tuple[str, ...] = ()
    reopening_condition_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_field(self) -> SemanticField:
        ids = [item.structure_id for item in self.items]
        if len(set(ids)) != len(ids):
            raise ValueError("semantic structures must appear exactly once in the field")
        for collection in (
            self.same_probe_history_event_ids,
            self.cross_probe_trace_ids,
            self.retrieval_result_ids,
            self.method_contract_ids,
            self.reopening_condition_ids,
        ):
            if len(set(collection)) != len(collection):
                raise ValueError("semantic field reference collections must be unique")
        return self


class CognitiveAttemptPlan(FrozenModel):
    """Inquiry intent linked to, but not duplicating, the core effect-attempt plan."""

    id: str
    obligation_id: str
    probe_or_action_id: str
    effect_request_id: str
    effect_attempt_plan_id: str | None
    source_state_revision: int
    scope_fingerprint: str
    planned_sequence: int

    @field_validator("source_state_revision", "planned_sequence")
    @classmethod
    def validate_nonnegative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("revision and sequence values must be nonnegative")
        return value


class PredictionSeal(FrozenModel):
    id: str
    cognitive_plan_id: str
    probe_or_action_id: str
    predicted_return_class: str
    predicted_consequence: JsonValue
    acceptable_variation: JsonValue
    scope_fingerprint: str
    basis_claim_ids: tuple[str, ...]
    sealed_sequence: int

    @field_validator("predicted_consequence", "acceptable_variation")
    @classmethod
    def freeze_payload(cls, value: JsonValue) -> JsonValue:
        return freeze_json(value)

    @field_validator("sealed_sequence")
    @classmethod
    def validate_nonnegative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("seal sequence must be nonnegative")
        return value


class Mismatch(FrozenModel):
    id: str
    prediction_id: str
    external_return_id: str
    decode_outcome_id: str
    difference_claim_id: str
    scope_fingerprint: str
    protected_consequence_changed: bool
    classification: str

    @model_validator(mode="after")
    def validate_mismatch(self) -> Mismatch:
        if any(
            not value
            for value in (
                self.id,
                self.prediction_id,
                self.external_return_id,
                self.decode_outcome_id,
                self.difference_claim_id,
                self.scope_fingerprint,
                self.classification,
            )
        ):
            raise ValueError("mismatch identity and exact lifecycle references are required")
        return self


class Reconstruction(FrozenModel):
    id: str
    prior_state_revision: int
    external_return_id: str
    decode_outcome_ids: tuple[str, ...]
    activated_memory_ids: tuple[str, ...] = ()
    candidate_claim_ids: tuple[str, ...] = ()
    candidate_repair_ids: tuple[str, ...] = ()
    residual_obligation_ids: tuple[str, ...] = ()
    generated_detail_ids: tuple[str, ...] = ()
    historical_fact_ids: tuple[str, ...] = ()
    reconstructed_sequence: int

    @field_validator("prior_state_revision", "reconstructed_sequence")
    @classmethod
    def validate_nonnegative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("revision and sequence values must be nonnegative")
        return value

    @model_validator(mode="after")
    def preserve_history_boundary(self) -> Reconstruction:
        if set(self.generated_detail_ids) & set(self.historical_fact_ids):
            raise ValueError("generated reconstruction detail is not historical fact")
        return self


class ReconstructionCandidate(FrozenModel):
    id: str
    retained_package_ids: tuple[str, ...]
    generated_working_structure: JsonValue
    protected_consequence_class_id: str
    historical_fact_ids: tuple[str, ...] = ()
    generated_detail_ids: tuple[str, ...] = ()

    @field_validator("generated_working_structure")
    @classmethod
    def freeze_working_structure(cls, value: JsonValue) -> JsonValue:
        return freeze_json(value)

    @model_validator(mode="after")
    def preserve_history_boundary(self) -> ReconstructionCandidate:
        if set(self.generated_detail_ids) & set(self.historical_fact_ids):
            raise ValueError("generated reconstruction detail is not historical fact")
        return self


class ReconstructionSet(FrozenModel):
    cue_id: str
    protected_horizon_id: str
    candidates: tuple[ReconstructionCandidate, ...]

    @property
    def consequence_class_ids(self) -> frozenset[str]:
        return frozenset(candidate.protected_consequence_class_id for candidate in self.candidates)

    @property
    def resolved(self) -> bool:
        return bool(self.candidates) and len(self.consequence_class_ids) == 1


class SemanticChangeOperation(StrEnum):
    ADD = "add"
    REOPEN = "reopen"
    RETIRE = "retire"


class WarrantedChange(FrozenModel):
    change_id: str
    proposition_id: str
    scope_fingerprint: str
    operation: SemanticChangeOperation
    warrant_lemma_id: str

    @model_validator(mode="after")
    def validate_change(self) -> WarrantedChange:
        if any(
            not value
            for value in (
                self.change_id,
                self.proposition_id,
                self.scope_fingerprint,
                self.warrant_lemma_id,
            )
        ):
            raise ValueError("semantic changes require proposition, scope, and warrant identity")
        return self


class SemanticDelta(FrozenModel):
    id: str
    reconstruction_id: str
    warranted_changes: tuple[WarrantedChange, ...]
    reopened_structure_ids: tuple[str, ...] = ()
    retired_structure_ids: tuple[str, ...] = ()
    committed_sequence: int

    @field_validator("committed_sequence")
    @classmethod
    def validate_nonnegative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("commit sequence must be nonnegative")
        return value

    @model_validator(mode="after")
    def validate_delta(self) -> SemanticDelta:
        change_ids = [change.change_id for change in self.warranted_changes]
        if len(set(change_ids)) != len(change_ids):
            raise ValueError("semantic changes must be unique")
        if set(self.reopened_structure_ids) & set(self.retired_structure_ids):
            raise ValueError("a structure cannot be reopened and retired in one delta")
        return self
