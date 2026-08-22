"""Deterministic bounded obligation scheduling."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from pydantic import BaseModel, ConfigDict, model_validator

from rci.claims.models import (
    Obligation,
    ObligationKind,
    ObligationStatus,
    content_fingerprint,
)
from rci.core.planning import (
    AttemptKey as AttemptKey,
)
from rci.core.planning import (
    PlanReason as PlanReason,
)
from rci.core.planning import (
    PlanStatus as PlanStatus,
)
from rci.core.planning import (
    StepPlan as StepPlan,
)
from rci.core.planning import (
    build_step_plan,
)

DEFAULT_STEP_BUDGET = 100
DEFAULT_ATTEMPTS_PER_KEY = 3
DEFAULT_EFFECT_TIMEOUT_SECONDS = 60
SCHEDULER_POLICY_VERSION = "deterministic-scheduler-v1"


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ObligationEntry(_FrozenModel):
    obligation: Obligation
    attempt_key: AttemptKey
    creation_sequence: int
    dependency_depth: int = 0

    @model_validator(mode="after")
    def validate_order_fields(self) -> ObligationEntry:
        if self.creation_sequence < 0 or self.dependency_depth < 0:
            raise ValueError("scheduler order coordinates must be nonnegative")
        if self.attempt_key.obligation_fingerprint != self.obligation.fingerprint:
            raise ValueError("attempt key must name the exact obligation fingerprint")
        if self.attempt_key.binding_revision != self.obligation.binding_revision:
            raise ValueError("attempt key and obligation binding revisions must match")
        return self


_SAFETY_KINDS = {
    ObligationKind.LOCALIZE_CONFLICT,
    ObligationKind.DISCHARGE_OPEN_DEPENDENCY,
}


def deduplicate_obligations(entries: Iterable[ObligationEntry]) -> tuple[ObligationEntry, ...]:
    """Keep the earliest stable occurrence of each exact obligation fingerprint."""

    by_fingerprint: dict[str, ObligationEntry] = {}
    for entry in sorted(entries, key=lambda item: (item.creation_sequence, item.obligation.id)):
        by_fingerprint.setdefault(entry.obligation.fingerprint, entry)
    return tuple(by_fingerprint.values())


def _priority_key(entry: ObligationEntry) -> tuple[int, tuple[int, ...], int, int, str]:
    safety_rank = 0 if entry.obligation.kind in _SAFETY_KINDS else 1
    inverted_priority = tuple(-value for value in entry.obligation.priority_vector)
    return (
        safety_rank,
        inverted_priority,
        entry.dependency_depth,
        entry.creation_sequence,
        entry.obligation.id,
    )


def plan_next(
    entries: Iterable[ObligationEntry],
    *,
    completed_obligation_ids: frozenset[str] = frozenset(),
    attempt_counts: Mapping[AttemptKey, int] | None = None,
    steps_used: int = 0,
    step_budget: int = DEFAULT_STEP_BUDGET,
    ready_event_cost: int = 1,
    max_attempts_per_key: int = DEFAULT_ATTEMPTS_PER_KEY,
    policy_version: str = SCHEDULER_POLICY_VERSION,
) -> StepPlan:
    """Select one ready obligation or terminate lawfully Unknown."""

    if steps_used < 0 or step_budget < 1 or ready_event_cost < 1 or max_attempts_per_key < 1:
        raise ValueError("scheduler budgets must be positive and usage nonnegative")
    if not policy_version:
        raise ValueError("scheduler policy version is required")
    entry_tuple = tuple(entries)
    counts = attempt_counts or {}
    if any(type(count) is not int or count < 0 for count in counts.values()):
        raise ValueError("attempt counts must be nonnegative integers")
    input_fingerprint = content_fingerprint(
        "rci.scheduler-input.v1",
        {
            "entries": [
                entry.model_dump(mode="json")
                for entry in sorted(
                    entry_tuple,
                    key=lambda item: (item.creation_sequence, item.obligation.id),
                )
            ],
            "completed_obligation_ids": sorted(completed_obligation_ids),
            "attempt_counts": [
                {
                    "attempt_key": key.model_dump(mode="json"),
                    "count": count,
                }
                for key, count in sorted(
                    counts.items(),
                    key=lambda item: (
                        item[0].obligation_fingerprint,
                        item[0].contract_id,
                        item[0].contract_version,
                        item[0].binding_revision,
                    ),
                )
            ],
            "steps_used": steps_used,
            "step_budget": step_budget,
            "ready_event_cost": ready_event_cost,
            "max_attempts_per_key": max_attempts_per_key,
            "policy_version": policy_version,
        },
    )
    remaining = max(step_budget - steps_used, 0)
    if remaining == 0:
        return build_step_plan(
            input_fingerprint=input_fingerprint,
            policy_version=policy_version,
            status=PlanStatus.UNKNOWN,
            reason=PlanReason.STEP_BUDGET_EXHAUSTED,
            remaining_budget=0,
        )
    deduplicated = deduplicate_obligations(entry_tuple)
    open_entries = [
        entry for entry in deduplicated if entry.obligation.status is ObligationStatus.OPEN
    ]
    if not open_entries:
        unresolved_nonopen = any(
            entry.obligation.status is not ObligationStatus.SATISFIED for entry in deduplicated
        )
        return build_step_plan(
            input_fingerprint=input_fingerprint,
            policy_version=policy_version,
            status=PlanStatus.UNKNOWN if unresolved_nonopen else PlanStatus.SATISFIED,
            reason=(
                PlanReason.UNRESOLVED_NONOPEN_OBLIGATION
                if unresolved_nonopen
                else PlanReason.NO_OPEN_OBLIGATION
            ),
            remaining_budget=remaining,
        )
    ready = [
        entry
        for entry in open_entries
        if set(entry.obligation.parent_obligation_ids) <= completed_obligation_ids
        and counts.get(entry.attempt_key, 0) < max_attempts_per_key
    ]
    if not ready:
        return build_step_plan(
            input_fingerprint=input_fingerprint,
            policy_version=policy_version,
            status=PlanStatus.UNKNOWN,
            reason=PlanReason.DEPENDENCIES_OR_ATTEMPTS_EXHAUSTED,
            remaining_budget=remaining,
        )
    if remaining < ready_event_cost:
        return build_step_plan(
            input_fingerprint=input_fingerprint,
            policy_version=policy_version,
            status=PlanStatus.UNKNOWN,
            reason=PlanReason.INSUFFICIENT_EVENT_BUDGET,
            remaining_budget=remaining,
        )
    selected = min(ready, key=_priority_key)
    return build_step_plan(
        input_fingerprint=input_fingerprint,
        policy_version=policy_version,
        status=PlanStatus.READY,
        selected_obligation_id=selected.obligation.id,
        selected_attempt_key=selected.attempt_key,
        reason=PlanReason.DETERMINISTIC_PRIORITY,
        remaining_budget=remaining - ready_event_cost,
    )
