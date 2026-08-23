"""Derived comparison for two ledger-owned deterministic weak-reasoner branches."""

from __future__ import annotations

from typing import Literal, cast

from pydantic import Field, model_validator

from rci.core.model import FrozenModel, Identifier, Sha256Digest
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
    actor_manifest_digest: Sha256Digest,
    evidence_universe_digest: Sha256Digest,
    budget_digest: Sha256Digest,
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


def run_weak_reasoner_fixture(
    *,
    baseline_states: tuple[InquiryState, ...],
    assisted_states: tuple[InquiryState, ...],
    baseline_protocols: tuple[CapabilityEvaluationProtocol, ...],
    assisted_protocols: tuple[CapabilityEvaluationProtocol, ...],
    baseline_bundles: tuple[CapabilityEvaluationBundle, ...],
    assisted_bundles: tuple[CapabilityEvaluationBundle, ...],
    actor_manifest_digest: Sha256Digest,
    evidence_universe_digest: Sha256Digest,
    budget_digest: Sha256Digest,
) -> WeakReasonerFixture:
    """Derive costs and conclusions from two already actualized authoritative streams."""

    baseline = _run(
        branch="baseline",
        states=baseline_states,
        protocols=baseline_protocols,
        bundles=baseline_bundles,
        actor_manifest_digest=actor_manifest_digest,
        evidence_universe_digest=evidence_universe_digest,
        budget_digest=budget_digest,
    )
    assisted = _run(
        branch="rci_assisted",
        states=assisted_states,
        protocols=assisted_protocols,
        bundles=assisted_bundles,
        actor_manifest_digest=actor_manifest_digest,
        evidence_universe_digest=evidence_universe_digest,
        budget_digest=budget_digest,
    )
    return WeakReasonerFixture(baseline=baseline, assisted=assisted)
