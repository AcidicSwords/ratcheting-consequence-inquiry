"""Replay-owned deterministic scheduler plan records."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import Field, model_validator

from rci.claims.models import content_fingerprint
from rci.core.model import FrozenModel, Sha256Digest


class PlanStatus(StrEnum):
    READY = "ready"
    SATISFIED = "satisfied"
    UNKNOWN = "unknown_under_present_binding"


class PlanReason(StrEnum):
    STEP_BUDGET_EXHAUSTED = "step_budget_exhausted"
    INSUFFICIENT_EVENT_BUDGET = "insufficient_event_budget"
    NO_OPEN_OBLIGATION = "no_open_obligation"
    UNRESOLVED_NONOPEN_OBLIGATION = "unresolved_nonopen_obligation"
    DEPENDENCIES_OR_ATTEMPTS_EXHAUSTED = "dependencies_or_attempt_budget_exhausted"
    DETERMINISTIC_PRIORITY = "deterministic_priority_order"


class AttemptKey(FrozenModel):
    obligation_fingerprint: Sha256Digest
    contract_id: str
    contract_version: str
    binding_revision: str

    @model_validator(mode="after")
    def validate_key(self) -> AttemptKey:
        if not all((self.contract_id, self.contract_version, self.binding_revision)):
            raise ValueError("all attempt-key coordinates are required")
        return self


def _step_plan_id(
    *,
    input_fingerprint: str,
    policy_version: str,
    status: PlanStatus,
    selected_obligation_id: str | None,
    selected_attempt_key: AttemptKey | None,
    reason: PlanReason,
    remaining_budget: int,
) -> str:
    digest = content_fingerprint(
        "rci.step-plan.v1",
        {
            "input_fingerprint": input_fingerprint,
            "policy_version": policy_version,
            "status": status,
            "selected_obligation_id": selected_obligation_id,
            "selected_attempt_key": selected_attempt_key,
            "reason": reason,
            "remaining_budget": remaining_budget,
        },
    )
    return f"step-plan:{digest}"


class StepPlan(FrozenModel):
    id: str
    input_fingerprint: Sha256Digest
    policy_version: str
    status: PlanStatus
    selected_obligation_id: str | None = None
    selected_attempt_key: AttemptKey | None = None
    reason: PlanReason
    remaining_budget: Annotated[int, Field(ge=0)]

    @model_validator(mode="after")
    def validate_selection(self) -> StepPlan:
        selected = self.selected_obligation_id is not None and self.selected_attempt_key is not None
        if (self.status is PlanStatus.READY) != selected:
            raise ValueError("only a ready plan selects an obligation and exact attempt key")
        if (self.selected_obligation_id is None) != (self.selected_attempt_key is None):
            raise ValueError("selected obligation and attempt key must be present together")
        if not self.policy_version:
            raise ValueError("scheduler policy version is required")
        expected_id = _step_plan_id(
            input_fingerprint=self.input_fingerprint,
            policy_version=self.policy_version,
            status=self.status,
            selected_obligation_id=self.selected_obligation_id,
            selected_attempt_key=self.selected_attempt_key,
            reason=self.reason,
            remaining_budget=self.remaining_budget,
        )
        if self.id != expected_id:
            raise ValueError("step plan id does not match its complete deterministic content")
        return self


def build_step_plan(
    *,
    input_fingerprint: Sha256Digest,
    policy_version: str,
    status: PlanStatus,
    selected_obligation_id: str | None = None,
    selected_attempt_key: AttemptKey | None = None,
    reason: PlanReason,
    remaining_budget: int,
) -> StepPlan:
    """Construct a plan whose identity covers its complete replayable content."""

    return StepPlan(
        id=_step_plan_id(
            input_fingerprint=input_fingerprint,
            policy_version=policy_version,
            status=status,
            selected_obligation_id=selected_obligation_id,
            selected_attempt_key=selected_attempt_key,
            reason=reason,
            remaining_budget=remaining_budget,
        ),
        input_fingerprint=input_fingerprint,
        policy_version=policy_version,
        status=status,
        selected_obligation_id=selected_obligation_id,
        selected_attempt_key=selected_attempt_key,
        reason=reason,
        remaining_budget=remaining_budget,
    )
