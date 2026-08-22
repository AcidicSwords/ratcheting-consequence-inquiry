"""Immutable effect request, attempt, return, and decoded-result records."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from rci.core.model import (
    ArtifactRef,
    CapturedPayload,
    FrozenModel,
    Identifier,
    NonEmptyText,
    Sha256Digest,
    require_utc,
)


class TransformEvidence(FrozenModel):
    """Exact material evidence for one applied route transform."""

    id: Identifier
    version: NonEmptyText
    input_artifact: ArtifactRef
    output_artifact: ArtifactRef


class RouteSnapshot(FrozenModel):
    """Resolved, immutable route facts for one attempt.

    A route definition remains inert configuration. This snapshot pins the definition,
    adapter, execution environment, and every transform actually used by the attempt.
    Source-reported identity belongs to ``ExternalReturn`` instead.
    """

    id: Identifier
    definition_id: Identifier
    definition_version: NonEmptyText
    definition_artifact: ArtifactRef
    backend_id: Identifier
    adapter_id: Identifier
    adapter_version: NonEmptyText
    endpoint_or_channel: NonEmptyText | None = None
    transport: NonEmptyText | None = None
    execution_environment_artifact: ArtifactRef
    request_or_action_digest: Sha256Digest
    transform_evidence: tuple[TransformEvidence, ...] = ()

    @field_validator("transform_evidence")
    @classmethod
    def validate_unique_transforms(
        cls, value: tuple[TransformEvidence, ...]
    ) -> tuple[TransformEvidence, ...]:
        ids = [item.id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError("route transform evidence ids must be unique and ordered")
        return value


class EffectRequest(FrozenModel):
    """A persisted authorization to execute one kind of external work."""

    id: Identifier
    step_plan_id: Identifier
    effect_kind: Identifier
    adapter_id: Identifier
    input_artifact: ArtifactRef
    timeout_seconds: Annotated[int, Field(ge=1, le=86_400)] = 60


class EffectAttemptPlan(FrozenModel):
    """A concrete attempt plan; retries receive distinct attempt identities."""

    id: Identifier
    request_id: Identifier
    route: RouteSnapshot


class NoAttemptReason(StrEnum):
    POLICY_DENIED = "policy_denied"
    UNSUPPORTED = "unsupported"
    BUDGET_EXHAUSTED = "budget_exhausted"
    DEPENDENCIES_OPEN = "dependencies_open"


class NotPresentedReason(StrEnum):
    POLICY_DENIED = "policy_denied"
    UNSUPPORTED = "unsupported"
    PREFLIGHT_FAILED = "preflight_failed"


class CaptureFailureReason(StrEnum):
    CAPTURE_ERROR = "capture_error"
    OUTPUT_LIMIT = "output_limit"
    STORAGE_ERROR = "storage_error"


class PresentationUnknownReason(StrEnum):
    TIMEOUT = "timeout"
    TRANSPORT_ERROR = "transport_error"
    INTERNAL_FAILURE = "internal_failure"


class CancellationReason(StrEnum):
    CALLER_CANCELLED = "caller_cancelled"
    POLICY_CANCELLED = "policy_cancelled"
    SHUTDOWN = "shutdown"


class NoAttemptDisposition(FrozenModel):
    """A plan-level disposition recording that execution was never attempted."""

    kind: Literal["no_attempt"] = "no_attempt"
    id: Identifier
    request_id: Identifier
    step_plan_id: Identifier
    reason_kind: NoAttemptReason
    diagnostics: ArtifactRef | None = None


class NotPresentedOutcome(FrozenModel):
    kind: Literal["not_presented"] = "not_presented"
    attempt_id: Identifier
    route_id: Identifier
    reason_kind: NotPresentedReason
    diagnostics: ArtifactRef | None = None


class CaptureFailedOutcome(FrozenModel):
    kind: Literal["capture_failed"] = "capture_failed"
    attempt_id: Identifier
    route_id: Identifier
    reason_kind: CaptureFailureReason
    diagnostics: ArtifactRef


class PresentationUnknownOutcome(FrozenModel):
    kind: Literal["presentation_unknown"] = "presentation_unknown"
    attempt_id: Identifier
    route_id: Identifier
    reason_kind: PresentationUnknownReason
    diagnostics: ArtifactRef


class CancelledOutcome(FrozenModel):
    kind: Literal["cancelled"] = "cancelled"
    attempt_id: Identifier
    route_id: Identifier
    reason_kind: CancellationReason
    diagnostics: ArtifactRef | None = None


class ExternalReturn(FrozenModel):
    """Immutable actuality captured from a route, before interpretation."""

    id: Identifier
    attempt_id: Identifier
    route_id: Identifier
    source_id: Identifier | None = None
    source_revision: NonEmptyText | None = None
    capture_boundary: NonEmptyText
    capture_encoding: NonEmptyText
    captured_at: datetime
    raw_payload: CapturedPayload

    _validate_captured_at = field_validator("captured_at")(require_utc)


class ReturnedOutcome(FrozenModel):
    kind: Literal["returned"] = "returned"
    attempt_id: Identifier
    route_id: Identifier
    external_return: ExternalReturn

    @model_validator(mode="after")
    def validate_external_return_link(self) -> ReturnedOutcome:
        if self.external_return.attempt_id != self.attempt_id:
            raise ValueError("external return and outcome attempt ids must match")
        if self.external_return.route_id != self.route_id:
            raise ValueError("external return and outcome route ids must match")
        return self


AttemptOutcome = Annotated[
    NotPresentedOutcome
    | CaptureFailedOutcome
    | PresentationUnknownOutcome
    | CancelledOutcome
    | ReturnedOutcome,
    Field(discriminator="kind"),
]


class ResultBase(FrozenModel):
    """Fields shared by the strict canonical decoded-result roles."""

    id: Identifier
    semantic_artifact: ArtifactRef


class WitnessResult(ResultBase):
    kind: Literal["witness"] = "witness"
    proposition_id: Identifier
    witness_artifact: ArtifactRef


class CounterexampleResult(ResultBase):
    kind: Literal["counterexample"] = "counterexample"
    proposition_id: Identifier
    counterexample_artifact: ArtifactRef


class SeparatorResult(ResultBase):
    kind: Literal["separator"] = "separator"
    left_class_id: Identifier
    right_class_id: Identifier
    separator_artifact: ArtifactRef


class EquivalenceCertificateResult(ResultBase):
    kind: Literal["equivalence_certificate"] = "equivalence_certificate"
    relation_id: Identifier
    certificate_artifact: ArtifactRef


class ConflictResult(ResultBase):
    kind: Literal["conflict"] = "conflict"
    left_proposition_id: Identifier
    right_proposition_id: Identifier


class PrerequisiteResult(ResultBase):
    kind: Literal["prerequisite"] = "prerequisite"
    condition_id: Identifier
    consequence_id: Identifier
    evidence_artifact: ArtifactRef


class ReachabilityWitnessResult(ResultBase):
    kind: Literal["reachability_witness"] = "reachability_witness"
    source_id: Identifier
    target_id: Identifier
    path_artifact: ArtifactRef


class UnreachabilityCertificateResult(ResultBase):
    kind: Literal["unreachability_certificate"] = "unreachability_certificate"
    source_id: Identifier
    target_id: Identifier
    certificate_artifact: ArtifactRef


class SuccessResult(ResultBase):
    kind: Literal["success"] = "success"
    operation_id: Identifier


class FailureResult(ResultBase):
    kind: Literal["failure"] = "failure"
    failure_kind: Identifier
    diagnostics: ArtifactRef | None = None


class UnknownResult(ResultBase):
    kind: Literal["unknown"] = "unknown"
    reason_kind: Identifier


CanonicalResult = Annotated[
    WitnessResult
    | CounterexampleResult
    | SeparatorResult
    | EquivalenceCertificateResult
    | ConflictResult
    | PrerequisiteResult
    | ReachabilityWitnessResult
    | UnreachabilityCertificateResult
    | SuccessResult
    | FailureResult
    | UnknownResult,
    Field(discriminator="kind"),
]


class DecodeBase(FrozenModel):
    id: Identifier
    external_return_id: Identifier
    decoder_id: Identifier
    decoder_version: NonEmptyText


class Decoded(DecodeBase):
    kind: Literal["decoded"] = "decoded"
    result: CanonicalResult


class MalformedDecode(DecodeBase):
    kind: Literal["malformed"] = "malformed"
    diagnostics: ArtifactRef


class UnsupportedDecode(DecodeBase):
    kind: Literal["unsupported"] = "unsupported"
    reason: NonEmptyText


class FailedDecode(DecodeBase):
    kind: Literal["failed"] = "failed"
    diagnostics: ArtifactRef


DecodeOutcome = Annotated[
    Decoded | MalformedDecode | UnsupportedDecode | FailedDecode,
    Field(discriminator="kind"),
]


class AttemptState(FrozenModel):
    plan: EffectAttemptPlan
    started: bool = False
    started_event_id: Identifier | None = None
    started_at: datetime | None = None
    outcome: AttemptOutcome | None = None

    @field_validator("started_at")
    @classmethod
    def validate_started_at(cls, value: datetime | None) -> datetime | None:
        return None if value is None else require_utc(value)

    @model_validator(mode="after")
    def validate_lifecycle(self) -> AttemptState:
        has_start_metadata = self.started_event_id is not None and self.started_at is not None
        if self.started != has_start_metadata:
            raise ValueError("started attempts require complete immutable start metadata")
        if self.outcome is not None and not self.started:
            raise ValueError("an attempt cannot terminate before it starts")
        return self


class EffectRequestState(FrozenModel):
    request: EffectRequest
    attempts: tuple[AttemptState, ...] = ()
    no_attempt_dispositions: tuple[NoAttemptDisposition, ...] = ()
    decode_outcomes: tuple[DecodeOutcome, ...] = ()
    accepted_decoded_outcome_id: Identifier | None = None

    @model_validator(mode="after")
    def validate_cardinalities(self) -> EffectRequestState:
        attempt_ids = [attempt.plan.id for attempt in self.attempts]
        if len(attempt_ids) != len(set(attempt_ids)):
            raise ValueError("attempt ids must be unique within an effect request")
        no_attempt_ids = [outcome.id for outcome in self.no_attempt_dispositions]
        if len(no_attempt_ids) != len(set(no_attempt_ids)):
            raise ValueError("no-attempt disposition ids must be unique")
        return_ids = [
            attempt.outcome.external_return.id
            for attempt in self.attempts
            if isinstance(attempt.outcome, ReturnedOutcome)
        ]
        if len(return_ids) != len(set(return_ids)):
            raise ValueError("external return ids must be unique")
        decode_ids = [outcome.id for outcome in self.decode_outcomes]
        if len(decode_ids) != len(set(decode_ids)):
            raise ValueError("decode outcome ids must be unique")
        if any(outcome.external_return_id not in return_ids for outcome in self.decode_outcomes):
            raise ValueError("each decode outcome must interpret this request's captured return")
        if self.accepted_decoded_outcome_id is not None:
            accepted = next(
                (
                    outcome
                    for outcome in self.decode_outcomes
                    if outcome.id == self.accepted_decoded_outcome_id
                ),
                None,
            )
            if not isinstance(accepted, Decoded):
                raise ValueError("only a successful Decoded outcome can be accepted")
        return self

    @property
    def accepted_result(self) -> CanonicalResult | None:
        accepted = next(
            (
                outcome
                for outcome in self.decode_outcomes
                if outcome.id == self.accepted_decoded_outcome_id
            ),
            None,
        )
        return accepted.result if isinstance(accepted, Decoded) else None
