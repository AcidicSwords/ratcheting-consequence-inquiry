"""Derived comparison for two ledger-owned deterministic weak-reasoner branches."""

from __future__ import annotations

from typing import Literal, cast

from pydantic import Field, model_validator

from rci.core.effects import ReturnedOutcome
from rci.core.model import FrozenModel, Identifier, Sha256Digest
from rci.core.serialization import canonical_json_bytes, sha256_digest
from rci.core.state import InquiryState
from rci.evaluation.capability import (
    CapabilityEvaluationBundle,
    CapabilityEvaluationProtocol,
    EvaluationPassed,
    ProtectedMismatchObserved,
)


class WeakReasonerCost(FrozenModel):
    attempts: int = Field(ge=0)
    checks: int = Field(ge=0)
    retries: int = Field(ge=0)
    context_bytes: int = Field(ge=0)


class WeakReasonerConclusion(FrozenModel):
    consequence_id: Literal["main-power-not-necessary", "may-reach-does-not-imply-must-reach"]
    correct: bool


class WeakReasonerRun(FrozenModel):
    branch: Literal["baseline", "rci_assisted"]
    actor_manifest_digest: Sha256Digest
    evidence_universe_digest: Sha256Digest
    budget_digest: Sha256Digest
    conclusions: tuple[WeakReasonerConclusion, ...]
    cost: WeakReasonerCost
    request_ids: tuple[Identifier, ...]
    used_check_ids: tuple[Identifier, ...]


class WeakReasonerFixture(FrozenModel):
    baseline: WeakReasonerRun
    assisted: WeakReasonerRun

    @model_validator(mode="after")
    def validate_pair(self) -> WeakReasonerFixture:
        if (
            self.baseline.actor_manifest_digest != self.assisted.actor_manifest_digest
            or self.baseline.evidence_universe_digest != self.assisted.evidence_universe_digest
            or self.baseline.budget_digest != self.assisted.budget_digest
        ):
            raise ValueError("weak-reasoner branches require identical actor/evidence/budget pins")
        baseline_correct = sum(item.correct for item in self.baseline.conclusions)
        assisted_correct = sum(item.correct for item in self.assisted.conclusions)
        if assisted_correct <= baseline_correct:
            raise ValueError("the bounded assisted fixture must strictly improve exact conclusions")
        return self


def _conclusion(bundle: CapabilityEvaluationBundle) -> WeakReasonerConclusion:
    if isinstance(bundle.result, EvaluationPassed):
        consequence_ids = bundle.result.protected_consequence_ids
        correct = True
    elif isinstance(bundle.result, ProtectedMismatchObserved):
        consequence_ids = tuple(item.consequence_id for item in bundle.result.violations)
        correct = False
    else:
        raise ValueError("weak-reasoner fixture requires a checked semantic result")
    if len(consequence_ids) != 1:
        raise ValueError("each weak-reasoner task must protect exactly one consequence")
    consequence_id = consequence_ids[0]
    if consequence_id not in {
        "main-power-not-necessary",
        "may-reach-does-not-imply-must-reach",
    }:
        raise ValueError("weak-reasoner fixture received an unknown protected consequence")
    return WeakReasonerConclusion(
        consequence_id=cast(
            Literal["main-power-not-necessary", "may-reach-does-not-imply-must-reach"],
            consequence_id,
        ),
        correct=correct,
    )


def _run(
    *,
    branch: Literal["baseline", "rci_assisted"],
    states: tuple[InquiryState, ...],
    protocols: tuple[CapabilityEvaluationProtocol, ...],
    bundles: tuple[CapabilityEvaluationBundle, ...],
) -> WeakReasonerRun:
    requests = tuple(
        sorted(
            (request for state in states for request in state.effect_requests),
            key=lambda item: item.request.id,
        )
    )
    checker_verdicts = tuple(
        sorted(
            (verdict for state in states for verdict in state.checker_verdicts),
            key=lambda item: item.id,
        )
    )
    if len(states) != len(protocols) or len(protocols) != len(bundles):
        raise ValueError("weak-reasoner states, protocols, and bundles must be one-to-one")
    protocol_by_id = {item.id: item for item in protocols}
    if len(protocol_by_id) != len(protocols):
        raise ValueError("weak-reasoner protocol identities must be unique")
    state_by_inquiry = {item.inquiry_id: item for item in states}
    if None in state_by_inquiry or len(state_by_inquiry) != len(states):
        raise ValueError("weak-reasoner states must belong to distinct started inquiries")
    linked_request_ids: set[str] = set()
    for bundle in bundles:
        protocol = protocol_by_id.get(bundle.result.protocol_id)
        state = state_by_inquiry.get(bundle.handoff.source_inquiry_id)
        if protocol is None or state is None:
            raise ValueError("weak-reasoner bundle is not linked to an exact protocol and stream")
        request = state.request_by_id(bundle.handoff.effect_request_id)
        if (
            request is None
            or bundle.handoff.protocol_id != protocol.id
            or bundle.handoff.evaluation_result_id != bundle.result.id
            or bundle.handoff.source_sequence != state.sequence
            or request.request.id != bundle.result.request_id
            or request.request.input_artifact != protocol.actor_task_artifact
            or state.context is None
            or state.context.binding_revision != protocol.binding_revision
            or state.context.scope_fingerprint != protocol.scope_fingerprint
            or state.context.protected_horizon_id != protocol.protected_horizon_id
        ):
            raise ValueError("weak-reasoner bundle linkage or semantic pins are stale")
        for attempt in request.attempts:
            if attempt.plan.route.definition_id != protocol.route_definition_id:
                raise ValueError("weak-reasoner actualized route differs from its protocol")
            if isinstance(attempt.outcome, ReturnedOutcome) and (
                attempt.outcome.external_return.source_id != protocol.actor_id
                or attempt.outcome.external_return.source_revision != protocol.actor_revision
            ):
                raise ValueError("weak-reasoner actualized actor differs from its protocol")
        linked_request_ids.add(request.request.id)
    if linked_request_ids != {item.request.id for item in requests}:
        raise ValueError("weak-reasoner states contain unlinked or missing requests")

    actor_pins = {
        (
            item.actor_id,
            item.actor_revision,
            item.adapter_id,
            item.route_definition_id,
            item.route_definition_version,
        )
        for item in protocols
    }
    evidence_pins = {item.evidence_access_artifact for item in protocols}
    budget_pins = {item.budget_artifact for item in protocols}
    context_pins = {item.context_artifact for item in protocols}
    if not (len(actor_pins) == len(evidence_pins) == len(budget_pins) == len(context_pins) == 1):
        raise ValueError(
            "each weak-reasoner branch requires one exact actor/context/evidence/budget"
        )
    actor_manifest_digest = sha256_digest(
        canonical_json_bytes([list(item) for item in sorted(actor_pins)])
    )
    evidence_universe_digest = next(iter(evidence_pins)).digest
    budget_digest = next(iter(budget_pins)).digest
    attempts = sum(len(item.attempts) for item in requests)
    retries = sum(max(0, len(item.attempts) - 1) for item in requests)
    return WeakReasonerRun(
        branch=branch,
        actor_manifest_digest=actor_manifest_digest,
        evidence_universe_digest=evidence_universe_digest,
        budget_digest=budget_digest,
        conclusions=tuple(
            sorted((_conclusion(item) for item in bundles), key=lambda x: x.consequence_id)
        ),
        cost=WeakReasonerCost(
            attempts=attempts,
            checks=len(checker_verdicts),
            retries=retries,
            context_bytes=sum(item.context_artifact.size for item in protocols),
        ),
        request_ids=tuple(item.request.id for item in requests),
        used_check_ids=tuple(item.id for item in checker_verdicts),
    )


def _build_weak_reasoner_fixture(
    *,
    baseline_states: tuple[InquiryState, ...],
    assisted_states: tuple[InquiryState, ...],
    baseline_protocols: tuple[CapabilityEvaluationProtocol, ...],
    assisted_protocols: tuple[CapabilityEvaluationProtocol, ...],
    baseline_bundles: tuple[CapabilityEvaluationBundle, ...],
    assisted_bundles: tuple[CapabilityEvaluationBundle, ...],
) -> WeakReasonerFixture:
    """Derive costs and conclusions from two already actualized authoritative streams."""

    baseline = _run(
        branch="baseline",
        states=baseline_states,
        protocols=baseline_protocols,
        bundles=baseline_bundles,
    )
    assisted = _run(
        branch="rci_assisted",
        states=assisted_states,
        protocols=assisted_protocols,
        bundles=assisted_bundles,
    )
    baseline_by_consequence = {
        item.expectations[0].consequence_id: item for item in baseline_protocols
    }
    assisted_by_consequence = {
        item.expectations[0].consequence_id: item for item in assisted_protocols
    }
    if set(baseline_by_consequence) != set(assisted_by_consequence):
        raise ValueError("weak-reasoner branches must evaluate identical consequence tasks")
    for consequence_id in sorted(baseline_by_consequence):
        baseline_protocol = baseline_by_consequence[consequence_id]
        assisted_protocol = assisted_by_consequence[consequence_id]
        comparable_fields = (
            "competence_id",
            "project_head_sha",
            "gate_digest",
            "binding_revision",
            "scope_fingerprint",
            "protected_horizon_id",
            "operation_id",
            "effect_kind",
            "actor_id",
            "actor_revision",
            "adapter_id",
            "route_definition_id",
            "route_definition_version",
            "context_artifact",
            "evidence_access_artifact",
            "budget_artifact",
            "timeout_seconds",
            "comparison_policy_id",
            "comparison_policy_version",
            "decoder_id",
            "decoder_version",
            "checker_id",
            "checker_version",
        )
        if (
            any(
                getattr(baseline_protocol, field) != getattr(assisted_protocol, field)
                for field in comparable_fields
            )
            or baseline_protocol.expectations != assisted_protocol.expectations
        ):
            raise ValueError("weak-reasoner branches differ on a protected comparison pin")
    return WeakReasonerFixture(baseline=baseline, assisted=assisted)
