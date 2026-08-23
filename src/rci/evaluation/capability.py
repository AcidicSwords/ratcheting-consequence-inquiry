"""Pure failure-first evaluation over the existing authoritative effect lifecycle.

The records in this module are derived views. They add no event kind, writable
authority, model invocation, warrant, or promotion path.
"""

from __future__ import annotations

from enum import Enum, StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, model_validator

from rci.core.effects import (
    CancelledOutcome,
    CaptureFailedOutcome,
    Decoded,
    EffectRequestState,
    FailedDecode,
    MalformedDecode,
    NotPresentedOutcome,
    PresentationUnknownOutcome,
    ReturnedOutcome,
    UnsupportedDecode,
)
from rci.core.model import ArtifactRef, FrozenModel, Identifier, NonEmptyText, Sha256Digest
from rci.core.serialization import canonical_json_bytes, sha256_digest
from rci.probes import Mismatch, PredictionSeal
from rci.project import LimitationKind
from rci.warrant import CheckerVerdict, CheckerVerdictRecord, PropositionKind

GitCommitSha = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]

EVALUATION_POLICY_VERSION = "capability-evaluation-v1"
LOCALIZATION_POLICY_VERSION = "failure-localization-v1"
HANDOFF_POLICY_VERSION = "cognitive-handoff-v1"
PROTOCOL_MEDIA_TYPE = "application/vnd.rci.capability-evaluation+json"
REPORT_MEDIA_TYPE = "application/vnd.rci.capability-consequence-report+json"


def _canonical(values: tuple[str, ...], label: str, *, nonempty: bool = False) -> None:
    if nonempty and not values:
        raise ValueError(f"{label} must not be empty")
    if tuple(sorted(values)) != values or len(set(values)) != len(values):
        raise ValueError(f"{label} must be unique and canonically ordered")


def _json_material(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_material(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_material(item) for item in value]
    return value


def _content_id(prefix: str, material: FrozenModel | dict[str, object]) -> str:
    normalized = _json_material(material)
    assert isinstance(normalized, dict)
    return f"{prefix}_{sha256_digest(canonical_json_bytes(normalized))[:24]}"


def _artifact_for(data: bytes, media_type: str) -> ArtifactRef:
    return ArtifactRef(
        digest=sha256_digest(data),
        size=len(data),
        media_type=media_type,
        encoding="utf-8",
    )


def _same_captured_bytes(left: ArtifactRef, right: ArtifactRef) -> bool:
    """Artifact media metadata is descriptive; digest and size identify exact bytes."""

    return left.digest == right.digest and left.size == right.size


class ProtectedExpectation(FrozenModel):
    consequence_id: Identifier
    expected_artifact: ArtifactRef
    attack_id: Identifier
    downstream_question_id: Identifier


class CapabilityEvaluationProtocol(FrozenModel):
    """A content-addressed pre-return task and consequence commitment."""

    schema_version: Literal[1] = 1
    policy_version: Literal["capability-evaluation-v1"] = "capability-evaluation-v1"
    id: Identifier
    anchor_id: Identifier
    goal_id: Identifier
    obligation_id: Identifier
    step_plan_id: Identifier
    competence_id: Identifier
    project_head_sha: GitCommitSha
    gate_digest: Sha256Digest
    binding_revision: Identifier
    scope_fingerprint: Sha256Digest
    protected_horizon_id: Identifier
    operation_id: Identifier
    effect_kind: Identifier
    actor_id: Identifier
    actor_revision: NonEmptyText
    adapter_id: Identifier
    route_definition_id: Identifier
    route_definition_version: NonEmptyText
    context_artifact: ArtifactRef
    evidence_access_artifact: ArtifactRef
    budget_artifact: ArtifactRef
    timeout_seconds: Annotated[int, Field(ge=1, le=86_400)]
    comparison_policy_id: Identifier
    comparison_policy_version: Identifier
    decoder_id: Identifier
    decoder_version: NonEmptyText
    checker_id: Identifier
    checker_version: NonEmptyText
    expectations: tuple[ProtectedExpectation, ...]
    discriminator_route_ids: tuple[Identifier, ...]
    protected_capability_ids: tuple[Identifier, ...]
    stopping_condition_ids: tuple[Identifier, ...]
    reopening_condition_ids: tuple[Identifier, ...]

    @model_validator(mode="after")
    def validate_protocol(self) -> CapabilityEvaluationProtocol:
        expectation_ids = tuple(item.consequence_id for item in self.expectations)
        _canonical(expectation_ids, "protected expectations", nonempty=True)
        for values, label in (
            (self.discriminator_route_ids, "discriminator routes"),
            (self.protected_capability_ids, "protected capabilities"),
            (self.stopping_condition_ids, "stopping conditions"),
            (self.reopening_condition_ids, "reopening conditions"),
        ):
            _canonical(values, label, nonempty=True)
        if self.route_definition_id in self.discriminator_route_ids:
            raise ValueError("a failed evaluation route cannot be its own next discriminator")
        if self.actor_id == self.checker_id:
            raise ValueError("the candidate actor cannot independently check its own return")
        expected_id = derive_protocol_id(self.model_dump(mode="json", exclude={"id"}))
        if self.id != expected_id:
            raise ValueError("capability evaluation protocol identity must be content-derived")
        return self

    @property
    def protected_consequence_ids(self) -> tuple[str, ...]:
        return tuple(item.consequence_id for item in self.expectations)


def derive_protocol_id(material: dict[str, object]) -> str:
    return _content_id("cap_eval_protocol", material)


def build_capability_evaluation_protocol(**fields: object) -> CapabilityEvaluationProtocol:
    """Build a protocol whose identity commits to every other field."""

    reserved = {"id", "schema_version", "policy_version"} & set(fields)
    if reserved:
        raise ValueError("protocol builder fields cannot override identity or version")
    material = {
        "schema_version": 1,
        "policy_version": EVALUATION_POLICY_VERSION,
        **fields,
    }
    return CapabilityEvaluationProtocol.model_validate(
        {"id": derive_protocol_id(material), **material}, strict=True
    )


def capability_protocol_artifact(protocol: CapabilityEvaluationProtocol) -> ArtifactRef:
    return _artifact_for(canonical_json_bytes(protocol), PROTOCOL_MEDIA_TYPE)


class ConsequenceObservation(FrozenModel):
    consequence_id: Identifier
    actual_artifact: ArtifactRef
    evidence_artifacts: tuple[ArtifactRef, ...]

    @model_validator(mode="after")
    def validate_observation(self) -> ConsequenceObservation:
        if not self.evidence_artifacts:
            raise ValueError("a consequence observation requires exact evidence")
        digests = tuple(item.digest for item in self.evidence_artifacts)
        _canonical(digests, "observation evidence", nonempty=True)
        return self


class CapabilityConsequenceReport(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    protocol_id: Identifier
    observations: tuple[ConsequenceObservation, ...]

    @model_validator(mode="after")
    def validate_report(self) -> CapabilityConsequenceReport:
        ids = tuple(item.consequence_id for item in self.observations)
        _canonical(ids, "consequence observations", nonempty=True)
        expected_id = _content_id("cap_report", self.model_dump(mode="json", exclude={"id"}))
        if self.id != expected_id:
            raise ValueError("capability consequence report identity must be content-derived")
        return self


def build_capability_consequence_report(
    *, protocol_id: str, observations: tuple[ConsequenceObservation, ...]
) -> CapabilityConsequenceReport:
    material: dict[str, object] = {
        "schema_version": 1,
        "protocol_id": protocol_id,
        "observations": observations,
    }
    return CapabilityConsequenceReport.model_validate(
        {"id": _content_id("cap_report", material), **material}, strict=True
    )


def capability_report_artifact(report: CapabilityConsequenceReport) -> ArtifactRef:
    return _artifact_for(canonical_json_bytes(report), REPORT_MEDIA_TYPE)


class CapabilityEvaluationEpisode(FrozenModel):
    """Exact authoritative lifecycle projection supplied to the pure evaluator."""

    protocol: CapabilityEvaluationProtocol
    protocol_artifact: ArtifactRef
    effect: EffectRequestState
    prediction: PredictionSeal
    checker_verdict: CheckerVerdictRecord | None = None
    mismatches: tuple[Mismatch, ...] = ()

    @model_validator(mode="after")
    def validate_episode(self) -> CapabilityEvaluationEpisode:
        ids = tuple(item.id for item in self.mismatches)
        if len(set(ids)) != len(ids):
            raise ValueError("episode mismatch identities must be unique")
        return self


class ConsequenceViolation(FrozenModel):
    consequence_id: Identifier
    expected_artifact: ArtifactRef
    actual_artifact: ArtifactRef
    mismatch_id: Identifier
    difference_claim_id: Identifier
    attack_id: Identifier
    downstream_question_id: Identifier
    evidence_artifacts: tuple[ArtifactRef, ...]


class EvaluationPassed(FrozenModel):
    kind: Literal["evaluation_passed"] = "evaluation_passed"
    schema_version: Literal[1] = 1
    id: Identifier
    protocol_id: Identifier
    request_id: Identifier
    decode_outcome_id: Identifier
    checker_verdict_id: Identifier
    protected_consequence_ids: tuple[Identifier, ...]
    evidence_artifacts: tuple[ArtifactRef, ...]


class ProtectedMismatchObserved(FrozenModel):
    kind: Literal["protected_mismatch"] = "protected_mismatch"
    schema_version: Literal[1] = 1
    id: Identifier
    protocol_id: Identifier
    request_id: Identifier
    decode_outcome_id: Identifier
    checker_verdict_id: Identifier
    violations: tuple[ConsequenceViolation, ...]


class DecodeIndeterminateObserved(FrozenModel):
    kind: Literal["decode_indeterminate"] = "decode_indeterminate"
    schema_version: Literal[1] = 1
    id: Identifier
    protocol_id: Identifier
    request_id: Identifier
    decode_outcome_id: Identifier | None
    reason_kind: Literal["malformed", "unsupported", "failed", "missing"]
    evidence_artifacts: tuple[ArtifactRef, ...]


class OperationalUnknownReason(StrEnum):
    NO_ATTEMPT_UNSUPPORTED = "no_attempt_unsupported"
    NO_ATTEMPT_POLICY = "no_attempt_policy"
    NO_ATTEMPT_BUDGET = "no_attempt_budget"
    NO_ATTEMPT_DEPENDENCIES = "no_attempt_dependencies"
    NOT_PRESENTED = "not_presented"
    TIMEOUT = "timeout"
    TRANSPORT_UNKNOWN = "transport_unknown"
    CAPTURE_FAILED = "capture_failed"
    CANCELLED = "cancelled"


class OperationalUnknownObserved(FrozenModel):
    kind: Literal["operational_unknown"] = "operational_unknown"
    schema_version: Literal[1] = 1
    id: Identifier
    protocol_id: Identifier
    request_id: Identifier
    attempt_id: Identifier | None
    reason_kind: OperationalUnknownReason
    evidence_artifacts: tuple[ArtifactRef, ...]


class EvaluationProtocolInvalid(FrozenModel):
    kind: Literal["protocol_invalid"] = "protocol_invalid"
    schema_version: Literal[1] = 1
    id: Identifier
    protocol_id: Identifier
    request_id: Identifier | None
    issue_codes: tuple[Identifier, ...]
    evidence_artifacts: tuple[ArtifactRef, ...]


CapabilityEvaluationResult = Annotated[
    EvaluationPassed
    | ProtectedMismatchObserved
    | DecodeIndeterminateObserved
    | OperationalUnknownObserved
    | EvaluationProtocolInvalid,
    Field(discriminator="kind"),
]


class FailureLocalizationCell(FrozenModel):
    limitation_kind: LimitationKind
    discriminator_id: Identifier
    downstream_question_id: Identifier
    evidence_requirement_ids: tuple[Identifier, ...]

    @model_validator(mode="after")
    def validate_cell(self) -> FailureLocalizationCell:
        _canonical(self.evidence_requirement_ids, "cell evidence requirements", nonempty=True)
        return self


class FailureLocalizationFrame(FrozenModel):
    schema_version: Literal[1] = 1
    policy_version: Literal["failure-localization-v1"] = "failure-localization-v1"
    id: Identifier
    protocol_id: Identifier
    result_id: Identifier
    cells: tuple[FailureLocalizationCell, ...]
    live_limitation_kinds: tuple[LimitationKind, ...]
    applicability_exterior_ids: tuple[Identifier, ...]
    partial_evidence_cell_id: Identifier
    indeterminate_cell_id: Identifier
    next_discriminator_id: Identifier
    next_discriminator_route_id: Identifier
    selected_limitation_kind: None = None
    status: Literal["unresolved"] = "unresolved"


class CapabilityLimitationCandidate(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    status: Literal["inert_candidate"] = "inert_candidate"
    protocol_id: Identifier
    evaluation_result_id: Identifier
    localization_frame_id: Identifier
    anchor_id: Identifier
    goal_id: Identifier
    candidate_kinds: tuple[LimitationKind, ...]
    protected_consequence_ids: tuple[Identifier, ...]
    evidence_artifacts: tuple[ArtifactRef, ...]
    attack_ids: tuple[Identifier, ...]
    downstream_question_ids: tuple[Identifier, ...]


class HandoffStatus(StrEnum):
    COMPLETE = "complete"
    CONTINUE = "continue"
    STOP_UNKNOWN = "stop_unknown"


class CognitiveHandoff(FrozenModel):
    schema_version: Literal[1] = 1
    policy_version: Literal["cognitive-handoff-v1"] = "cognitive-handoff-v1"
    id: Identifier
    anchor_id: Identifier
    goal_id: Identifier
    project_head_sha: GitCommitSha
    gate_digest: Sha256Digest
    protocol_id: Identifier
    evaluation_result_id: Identifier
    protected_capability_ids: tuple[Identifier, ...]
    accepted_evidence: tuple[ArtifactRef, ...]
    failed_route_ids: tuple[Identifier, ...]
    forbidden_route_ids_until_reopen: tuple[Identifier, ...]
    live_localization_kinds: tuple[LimitationKind, ...]
    next_discriminator_id: Identifier | None
    next_discriminator_route_id: Identifier | None
    stopping_condition_ids: tuple[Identifier, ...]
    reopening_condition_ids: tuple[Identifier, ...]
    status: HandoffStatus

    @model_validator(mode="after")
    def validate_handoff(self) -> CognitiveHandoff:
        for values, label in (
            (self.protected_capability_ids, "handoff protected capabilities"),
            (tuple(item.digest for item in self.accepted_evidence), "handoff evidence"),
            (self.failed_route_ids, "handoff failed routes"),
            (self.forbidden_route_ids_until_reopen, "handoff forbidden routes"),
            (tuple(item.value for item in self.live_localization_kinds), "handoff live cells"),
            (self.stopping_condition_ids, "handoff stopping conditions"),
            (self.reopening_condition_ids, "handoff reopening conditions"),
        ):
            _canonical(values, label)
        if (
            self.next_discriminator_route_id is not None
            and self.next_discriminator_route_id in self.forbidden_route_ids_until_reopen
        ):
            raise ValueError("handoff cannot immediately repeat a failed route")
        if self.status is HandoffStatus.CONTINUE:
            if self.next_discriminator_id is None or self.next_discriminator_route_id is None:
                raise ValueError("a continuing handoff requires an exact next discriminator")
        elif self.next_discriminator_id is not None or self.next_discriminator_route_id is not None:
            raise ValueError("a non-continuing handoff cannot name a next discriminator")
        return self


class CapabilityEvaluationBundle(FrozenModel):
    result: CapabilityEvaluationResult
    localization_frame: FailureLocalizationFrame | None
    limitation_candidate: CapabilityLimitationCandidate | None
    handoff: CognitiveHandoff

    @model_validator(mode="after")
    def validate_bundle(self) -> CapabilityEvaluationBundle:
        mismatch = isinstance(self.result, ProtectedMismatchObserved)
        if mismatch != (self.localization_frame is not None):
            raise ValueError("only protected mismatch has a failure-localization frame")
        if mismatch != (self.limitation_candidate is not None):
            raise ValueError("only protected mismatch has an inert limitation candidate")
        return self


def _invalid(
    protocol: CapabilityEvaluationProtocol,
    episode: CapabilityEvaluationEpisode,
    issues: set[str],
    evidence: tuple[ArtifactRef, ...] = (),
) -> EvaluationProtocolInvalid:
    issue_codes = tuple(sorted(issues))
    material: dict[str, object] = {
        "protocol_id": protocol.id,
        "request_id": episode.effect.request.id,
        "issue_codes": issue_codes,
        "evidence": tuple(sorted(item.digest for item in evidence)),
    }
    return EvaluationProtocolInvalid(
        id=_content_id("cap_eval_invalid", material),
        protocol_id=protocol.id,
        request_id=episode.effect.request.id,
        issue_codes=issue_codes,
        evidence_artifacts=tuple(sorted(evidence, key=lambda item: item.digest)),
    )


def _lifecycle_issues(
    protocol: CapabilityEvaluationProtocol,
    episode: CapabilityEvaluationEpisode,
) -> set[str]:
    request = episode.effect.request
    issues: set[str] = set()
    if episode.protocol_artifact != capability_protocol_artifact(protocol):
        issues.add("protocol_artifact_mismatch")
    if request.input_artifact != episode.protocol_artifact:
        issues.add("request_does_not_reference_protocol")
    if request.step_plan_id != protocol.step_plan_id:
        issues.add("foreign_step_plan")
    if request.effect_kind != protocol.effect_kind:
        issues.add("foreign_effect_kind")
    if request.adapter_id != protocol.adapter_id:
        issues.add("foreign_adapter")
    if request.timeout_seconds != protocol.timeout_seconds:
        issues.add("foreign_budget")
    if episode.prediction.id == "" or episode.prediction.cognitive_plan_id != protocol.step_plan_id:
        issues.add("foreign_prediction")
    if episode.prediction.probe_or_action_id != protocol.operation_id:
        issues.add("foreign_operation")
    if episode.prediction.scope_fingerprint != protocol.scope_fingerprint:
        issues.add("foreign_scope")
    expected_prediction = {
        "comparison_policy_id": protocol.comparison_policy_id,
        "comparison_policy_version": protocol.comparison_policy_version,
        "expectations": [
            {
                "consequence_id": item.consequence_id,
                "expected_artifact_digest": item.expected_artifact.digest,
            }
            for item in protocol.expectations
        ],
        "protocol_id": protocol.id,
    }
    if episode.prediction.predicted_consequence != expected_prediction:
        issues.add("prediction_expectation_mismatch")
    if episode.prediction.acceptable_variation != {
        "comparison_policy_id": protocol.comparison_policy_id,
        "comparison_policy_version": protocol.comparison_policy_version,
    }:
        issues.add("comparison_policy_mismatch")
    for attempt in episode.effect.attempts:
        if attempt.plan.request_id != request.id:
            issues.add("foreign_attempt")
        route = attempt.plan.route
        if route.definition_id != protocol.route_definition_id:
            issues.add("foreign_route")
        if route.definition_version != protocol.route_definition_version:
            issues.add("foreign_route_version")
        if route.adapter_id != protocol.adapter_id:
            issues.add("foreign_route_adapter")
        if route.request_or_action_digest != sha256_digest(canonical_json_bytes(request)):
            issues.add("request_digest_mismatch")
        if isinstance(attempt.outcome, ReturnedOutcome):
            external_return = attempt.outcome.external_return
            if (
                external_return.source_id != protocol.actor_id
                or external_return.source_revision != protocol.actor_revision
            ):
                issues.add("foreign_actor")
    for disposition in episode.effect.no_attempt_dispositions:
        if disposition.request_id != request.id or disposition.step_plan_id != request.step_plan_id:
            issues.add("foreign_no_attempt_disposition")
    if episode.effect.accepted_decoded_outcome_id is not None:
        accepted = next(
            (
                item
                for item in episode.effect.decode_outcomes
                if item.id == episode.effect.accepted_decoded_outcome_id
            ),
            None,
        )
        accepted_return_id = accepted.external_return_id if isinstance(accepted, Decoded) else None
        returned_ids = tuple(
            attempt.outcome.external_return.id
            for attempt in episode.effect.attempts
            if isinstance(attempt.outcome, ReturnedOutcome)
        )
        if returned_ids != (accepted_return_id,):
            issues.add("late_or_competing_return")
        if tuple(item.id for item in episode.effect.decode_outcomes) != (
            episode.effect.accepted_decoded_outcome_id,
        ):
            issues.add("unaccepted_decode_present")
    return issues


def _operational_result(
    protocol: CapabilityEvaluationProtocol, episode: CapabilityEvaluationEpisode
) -> OperationalUnknownObserved | None:
    request = episode.effect.request
    evidence: list[ArtifactRef] = []
    if episode.effect.no_attempt_dispositions:
        disposition = episode.effect.no_attempt_dispositions[-1]
        if disposition.diagnostics is not None:
            evidence.append(disposition.diagnostics)
        reason = {
            "unsupported": OperationalUnknownReason.NO_ATTEMPT_UNSUPPORTED,
            "policy_denied": OperationalUnknownReason.NO_ATTEMPT_POLICY,
            "budget_exhausted": OperationalUnknownReason.NO_ATTEMPT_BUDGET,
            "dependencies_open": OperationalUnknownReason.NO_ATTEMPT_DEPENDENCIES,
        }[disposition.reason_kind.value]
        attempt_id: str | None = None
    elif episode.effect.attempts:
        attempt = episode.effect.attempts[-1]
        outcome = attempt.outcome
        if outcome is None or isinstance(outcome, ReturnedOutcome):
            return None
        attempt_id = attempt.plan.id
        if outcome.diagnostics is not None:
            evidence.append(outcome.diagnostics)
        if isinstance(outcome, NotPresentedOutcome):
            reason = OperationalUnknownReason.NOT_PRESENTED
        elif isinstance(outcome, PresentationUnknownOutcome):
            reason = (
                OperationalUnknownReason.TIMEOUT
                if outcome.reason_kind.value == "timeout"
                else OperationalUnknownReason.TRANSPORT_UNKNOWN
            )
        elif isinstance(outcome, CaptureFailedOutcome):
            reason = OperationalUnknownReason.CAPTURE_FAILED
        elif isinstance(outcome, CancelledOutcome):
            reason = OperationalUnknownReason.CANCELLED
        else:  # pragma: no cover - closed union defense
            return None
    else:
        return None
    ordered = tuple(sorted(evidence, key=lambda item: item.digest))
    material: dict[str, object] = {
        "protocol_id": protocol.id,
        "request_id": request.id,
        "attempt_id": attempt_id,
        "reason": reason.value,
        "evidence": tuple(item.digest for item in ordered),
    }
    return OperationalUnknownObserved(
        id=_content_id("cap_eval_operational", material),
        protocol_id=protocol.id,
        request_id=request.id,
        attempt_id=attempt_id,
        reason_kind=reason,
        evidence_artifacts=ordered,
    )


def evaluate_capability_episode(
    *,
    protocol: CapabilityEvaluationProtocol,
    episode: CapabilityEvaluationEpisode,
    report: CapabilityConsequenceReport | None,
) -> CapabilityEvaluationResult:
    """Derive one exact result without I/O, clocks, IDs, randomness, or effects."""

    issues = _lifecycle_issues(protocol, episode)
    if issues:
        return _invalid(protocol, episode, issues)

    operational = _operational_result(protocol, episode)
    if operational is not None:
        if episode.effect.decode_outcomes or report is not None or episode.mismatches:
            return _invalid(protocol, episode, {"post_terminal_semantic_material"})
        return operational

    accepted_id = episode.effect.accepted_decoded_outcome_id
    accepted = next(
        (item for item in episode.effect.decode_outcomes if item.id == accepted_id), None
    )
    if accepted is None:
        decode = episode.effect.decode_outcomes[-1] if episode.effect.decode_outcomes else None
        evidence: tuple[ArtifactRef, ...]
        if isinstance(decode, MalformedDecode):
            reason: Literal["malformed", "unsupported", "failed", "missing"] = "malformed"
            evidence = (decode.diagnostics,)
        elif isinstance(decode, UnsupportedDecode):
            reason = "unsupported"
            evidence = ()
        elif isinstance(decode, FailedDecode):
            reason = "failed"
            evidence = (decode.diagnostics,)
        else:
            reason = "missing"
            evidence = ()
        if report is not None or episode.mismatches:
            return _invalid(protocol, episode, {"unaccepted_semantic_material"}, evidence)
        material: dict[str, object] = {
            "protocol_id": protocol.id,
            "request_id": episode.effect.request.id,
            "decode_id": None if decode is None else decode.id,
            "reason": reason,
            "evidence": tuple(item.digest for item in evidence),
        }
        return DecodeIndeterminateObserved(
            id=_content_id("cap_eval_decode", material),
            protocol_id=protocol.id,
            request_id=episode.effect.request.id,
            decode_outcome_id=None if decode is None else decode.id,
            reason_kind=reason,
            evidence_artifacts=evidence,
        )

    if not isinstance(accepted, Decoded) or report is None:
        return _invalid(protocol, episode, {"accepted_decode_or_report_missing"})
    if (
        accepted.decoder_id != protocol.decoder_id
        or accepted.decoder_version != protocol.decoder_version
    ):
        issues.add("foreign_decoder")
    if accepted.result.semantic_artifact != capability_report_artifact(report):
        issues.add("report_artifact_mismatch")
    if report.protocol_id != protocol.id:
        issues.add("foreign_report")
    checker = episode.checker_verdict
    if checker is None:
        issues.add("checker_missing")
    else:
        if checker.evidence_artifact != accepted.result.semantic_artifact:
            issues.add("checker_evidence_mismatch")
        if checker.proposition_id != f"capability-report:{report.id}":
            issues.add("checker_proposition_mismatch")
        if checker.proposition_kind is not PropositionKind.RELATION:
            issues.add("checker_proposition_kind_mismatch")
        if checker.scope_fingerprint != protocol.scope_fingerprint:
            issues.add("checker_scope_mismatch")
        if (
            checker.checker_id != protocol.checker_id
            or checker.checker_version != protocol.checker_version
        ):
            issues.add("foreign_checker")
        if checker.verdict is not CheckerVerdict.VALID:
            issues.add("checker_not_valid")
    expected_by_id = {item.consequence_id: item for item in protocol.expectations}
    observed_by_id = {item.consequence_id: item for item in report.observations}
    if set(expected_by_id) != set(observed_by_id):
        issues.add("consequence_coverage_mismatch")
    if issues:
        return _invalid(protocol, episode, issues, (accepted.result.semantic_artifact,))

    mismatches_by_class = {item.classification: item for item in episode.mismatches}
    violations: list[ConsequenceViolation] = []
    all_evidence: dict[str, ArtifactRef] = {}
    for consequence_id in sorted(expected_by_id):
        expectation = expected_by_id[consequence_id]
        observation = observed_by_id[consequence_id]
        for artifact in observation.evidence_artifacts:
            all_evidence[artifact.digest] = artifact
        if _same_captured_bytes(observation.actual_artifact, expectation.expected_artifact):
            continue
        classification = f"capability:{consequence_id}"
        mismatch = mismatches_by_class.get(classification)
        if mismatch is None:
            issues.add("protected_mismatch_record_missing")
            continue
        if (
            mismatch.prediction_id != episode.prediction.id
            or mismatch.external_return_id != accepted.external_return_id
            or mismatch.decode_outcome_id != accepted.id
            or mismatch.scope_fingerprint != protocol.scope_fingerprint
            or not mismatch.protected_consequence_changed
        ):
            issues.add("foreign_mismatch")
            continue
        violations.append(
            ConsequenceViolation(
                consequence_id=consequence_id,
                expected_artifact=expectation.expected_artifact,
                actual_artifact=observation.actual_artifact,
                mismatch_id=mismatch.id,
                difference_claim_id=mismatch.difference_claim_id,
                attack_id=expectation.attack_id,
                downstream_question_id=expectation.downstream_question_id,
                evidence_artifacts=observation.evidence_artifacts,
            )
        )
    used_classes = {f"capability:{item.consequence_id}" for item in violations}
    if set(mismatches_by_class) != used_classes:
        issues.add("extra_or_stale_mismatch")
    if issues:
        return _invalid(protocol, episode, issues, tuple(all_evidence.values()))
    assert checker is not None
    checker_id = checker.id
    if violations:
        ordered = tuple(sorted(violations, key=lambda item: item.consequence_id))
        material = {
            "protocol_id": protocol.id,
            "request_id": episode.effect.request.id,
            "decode_id": accepted.id,
            "checker_id": checker_id,
            "violations": tuple(item.model_dump(mode="json") for item in ordered),
        }
        return ProtectedMismatchObserved(
            id=_content_id("cap_eval_mismatch", material),
            protocol_id=protocol.id,
            request_id=episode.effect.request.id,
            decode_outcome_id=accepted.id,
            checker_verdict_id=checker_id,
            violations=ordered,
        )
    evidence = tuple(all_evidence[key] for key in sorted(all_evidence))
    material = {
        "protocol_id": protocol.id,
        "request_id": episode.effect.request.id,
        "decode_id": accepted.id,
        "checker_id": checker_id,
        "consequences": protocol.protected_consequence_ids,
        "evidence": tuple(item.digest for item in evidence),
    }
    return EvaluationPassed(
        id=_content_id("cap_eval_passed", material),
        protocol_id=protocol.id,
        request_id=episode.effect.request.id,
        decode_outcome_id=accepted.id,
        checker_verdict_id=checker_id,
        protected_consequence_ids=protocol.protected_consequence_ids,
        evidence_artifacts=evidence,
    )


def derive_failure_localization_frame(
    protocol: CapabilityEvaluationProtocol,
    result: ProtectedMismatchObserved,
) -> FailureLocalizationFrame:
    """Create the fixed unresolved cause frontier; no diagnostic answer is trusted."""

    first_question = result.violations[0].downstream_question_id
    cells = tuple(
        FailureLocalizationCell(
            limitation_kind=kind,
            discriminator_id=f"locate-{kind.value}-v1",
            downstream_question_id=first_question,
            evidence_requirement_ids=(f"independent-{kind.value}-separator",),
        )
        for kind in sorted(LimitationKind, key=lambda item: item.value)
    )
    material: dict[str, object] = {
        "protocol_id": protocol.id,
        "result_id": result.id,
        "cells": tuple(item.model_dump(mode="json") for item in cells),
        "route": protocol.discriminator_route_ids[0],
    }
    return FailureLocalizationFrame(
        id=_content_id("failure_frame", material),
        protocol_id=protocol.id,
        result_id=result.id,
        cells=cells,
        live_limitation_kinds=tuple(item.limitation_kind for item in cells),
        applicability_exterior_ids=(
            "decode_indeterminate",
            "operational_unknown",
            "protocol_invalid",
        ),
        partial_evidence_cell_id="partial-localization-evidence",
        indeterminate_cell_id="localization-indeterminate",
        next_discriminator_id="failure-locus-separator-v1",
        next_discriminator_route_id=protocol.discriminator_route_ids[0],
    )


def derive_limitation_candidate(
    protocol: CapabilityEvaluationProtocol,
    result: ProtectedMismatchObserved,
    frame: FailureLocalizationFrame,
) -> CapabilityLimitationCandidate:
    violations = result.violations
    evidence = {
        item.digest: item for violation in violations for item in violation.evidence_artifacts
    }
    material: dict[str, object] = {
        "protocol_id": protocol.id,
        "result_id": result.id,
        "frame_id": frame.id,
        "kinds": tuple(item.value for item in frame.live_limitation_kinds),
        "consequences": tuple(item.consequence_id for item in violations),
    }
    return CapabilityLimitationCandidate(
        id=_content_id("cap_limitation_candidate", material),
        protocol_id=protocol.id,
        evaluation_result_id=result.id,
        localization_frame_id=frame.id,
        anchor_id=protocol.anchor_id,
        goal_id=protocol.goal_id,
        candidate_kinds=frame.live_limitation_kinds,
        protected_consequence_ids=tuple(item.consequence_id for item in violations),
        evidence_artifacts=tuple(evidence[key] for key in sorted(evidence)),
        attack_ids=tuple(sorted(item.attack_id for item in violations)),
        downstream_question_ids=tuple(sorted(item.downstream_question_id for item in violations)),
    )


def derive_cognitive_handoff(
    protocol: CapabilityEvaluationProtocol,
    result: CapabilityEvaluationResult,
    frame: FailureLocalizationFrame | None,
) -> CognitiveHandoff:
    if isinstance(result, EvaluationPassed):
        status = HandoffStatus.COMPLETE
        evidence = result.evidence_artifacts
        failed: tuple[str, ...] = ()
        live: tuple[LimitationKind, ...] = ()
        next_id = None
        next_route = None
    elif isinstance(result, ProtectedMismatchObserved):
        if frame is None:
            raise ValueError("protected mismatch handoff requires its localization frame")
        status = HandoffStatus.CONTINUE
        evidence = tuple(
            sorted(
                {
                    item.digest: item
                    for violation in result.violations
                    for item in violation.evidence_artifacts
                }.values(),
                key=lambda item: item.digest,
            )
        )
        failed = (protocol.route_definition_id,)
        live = frame.live_limitation_kinds
        next_id = frame.next_discriminator_id
        next_route = frame.next_discriminator_route_id
    else:
        status = HandoffStatus.STOP_UNKNOWN
        evidence = result.evidence_artifacts
        failed = (
            (protocol.route_definition_id,)
            if isinstance(result, OperationalUnknownObserved)
            else ()
        )
        live = ()
        next_id = None
        next_route = None
    material: dict[str, object] = {
        "protocol_id": protocol.id,
        "result_id": result.id,
        "status": status.value,
        "failed": failed,
        "live": tuple(item.value for item in live),
        "next": next_id,
        "route": next_route,
    }
    return CognitiveHandoff(
        id=_content_id("cognitive_handoff", material),
        anchor_id=protocol.anchor_id,
        goal_id=protocol.goal_id,
        project_head_sha=protocol.project_head_sha,
        gate_digest=protocol.gate_digest,
        protocol_id=protocol.id,
        evaluation_result_id=result.id,
        protected_capability_ids=protocol.protected_capability_ids,
        accepted_evidence=evidence,
        failed_route_ids=failed,
        forbidden_route_ids_until_reopen=failed,
        live_localization_kinds=live,
        next_discriminator_id=next_id,
        next_discriminator_route_id=next_route,
        stopping_condition_ids=protocol.stopping_condition_ids,
        reopening_condition_ids=protocol.reopening_condition_ids,
        status=status,
    )


def build_capability_evaluation_bundle(
    *,
    protocol: CapabilityEvaluationProtocol,
    episode: CapabilityEvaluationEpisode,
    report: CapabilityConsequenceReport | None,
) -> CapabilityEvaluationBundle:
    result = evaluate_capability_episode(protocol=protocol, episode=episode, report=report)
    frame = (
        derive_failure_localization_frame(protocol, result)
        if isinstance(result, ProtectedMismatchObserved)
        else None
    )
    candidate = (
        derive_limitation_candidate(protocol, result, frame)
        if isinstance(result, ProtectedMismatchObserved) and frame is not None
        else None
    )
    handoff = derive_cognitive_handoff(protocol, result, frame)
    return CapabilityEvaluationBundle(
        result=result,
        localization_frame=frame,
        limitation_candidate=candidate,
        handoff=handoff,
    )


def build_protocol_invalid_bundle(
    *,
    protocol: CapabilityEvaluationProtocol,
    episode: CapabilityEvaluationEpisode,
    issue_codes: tuple[str, ...],
) -> CapabilityEvaluationBundle:
    """Fail closed when CAS loading or strict decoding cannot reach pure evaluation."""

    result = _invalid(protocol, episode, set(issue_codes))
    return CapabilityEvaluationBundle(
        result=result,
        localization_frame=None,
        limitation_candidate=None,
        handoff=derive_cognitive_handoff(protocol, result, None),
    )
