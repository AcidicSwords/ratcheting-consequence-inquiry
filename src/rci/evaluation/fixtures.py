"""Bounded deterministic G3FO weak-reasoner reference fixture."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from rci.bindings import circuit_demonstration, route_demonstration
from rci.core.model import FrozenModel, Identifier, Sha256Digest


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


def run_weak_reasoner_fixture(
    *,
    actor_manifest_digest: Sha256Digest,
    evidence_universe_digest: Sha256Digest,
    budget_digest: Sha256Digest,
) -> WeakReasonerFixture:
    """Compare scripted closure with existing exhaustive counterexample checks."""

    circuit = circuit_demonstration()
    routes = route_demonstration()
    baseline = WeakReasonerRun(
        branch="baseline",
        actor_manifest_digest=actor_manifest_digest,
        evidence_universe_digest=evidence_universe_digest,
        budget_digest=budget_digest,
        conclusions=(
            WeakReasonerConclusion(consequence_id="main-power-not-necessary", correct=False),
            WeakReasonerConclusion(
                consequence_id="may-reach-does-not-imply-must-reach", correct=False
            ),
        ),
        cost=WeakReasonerCost(attempts=2, checks=0, retries=0, context_bytes=384),
        used_check_ids=(),
    )
    assisted = WeakReasonerRun(
        branch="rci_assisted",
        actor_manifest_digest=actor_manifest_digest,
        evidence_universe_digest=evidence_universe_digest,
        budget_digest=budget_digest,
        conclusions=(
            WeakReasonerConclusion(
                consequence_id="main-power-not-necessary",
                correct=(
                    circuit.expected_findings_hold
                    and circuit.main_power_necessity_attack.witness is not None
                ),
            ),
            WeakReasonerConclusion(
                consequence_id="may-reach-does-not-imply-must-reach",
                correct=routes.expected_findings_hold,
            ),
        ),
        cost=WeakReasonerCost(attempts=2, checks=2, retries=0, context_bytes=768),
        used_check_ids=("circuit-necessity-counterexample", "route-may-must-enumerator"),
    )
    return WeakReasonerFixture(baseline=baseline, assisted=assisted)
