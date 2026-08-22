"""Independent fail-closed checker for provisional recovery comparisons.

This module deliberately does not call the recovery builder's arithmetic or coverage
helpers.  Its duplicated integer cross-multiplication is an independence boundary.
"""

from __future__ import annotations

from enum import IntEnum
from functools import cmp_to_key

from rci.memory.models import (
    CostVector,
    FrontierCoverage,
    RecoveryBranch,
    RecoveryComparison,
    RecoveryComparisonOutcome,
    RecoveryFrontier,
    RecoveryFrontierPoint,
)


class _Relation(IntEnum):
    RETAINED_BETTER = -2
    EQUAL = 0
    BASELINE_BETTER = 2
    INCOMPARABLE = 3


def _vector_relation(retained: CostVector, baseline: CostVector) -> _Relation:
    if retained.axis_signature != baseline.axis_signature:
        raise ValueError("independent checker found mismatched cost axes")
    retained_no_worse = True
    baseline_no_worse = True
    for retained_cost, baseline_cost in zip(
        retained.coordinates,
        baseline.coordinates,
        strict=True,
    ):
        if retained_cost.axis != baseline_cost.axis:
            raise ValueError("independent checker found mismatched typed axes")
        retained_scaled = retained_cost.numerator * baseline_cost.denominator
        baseline_scaled = baseline_cost.numerator * retained_cost.denominator
        if retained_scaled > baseline_scaled:
            retained_no_worse = False
        if baseline_scaled > retained_scaled:
            baseline_no_worse = False
    if retained_no_worse and baseline_no_worse:
        return _Relation.EQUAL
    if retained_no_worse:
        return _Relation.RETAINED_BETTER
    if baseline_no_worse:
        return _Relation.BASELINE_BETTER
    return _Relation.INCOMPARABLE


def _point_order(left: RecoveryFrontierPoint, right: RecoveryFrontierPoint) -> int:
    if left.costs.axis_signature != right.costs.axis_signature:
        raise ValueError("independent checker cannot order mismatched cost axes")
    for left_cost, right_cost in zip(left.costs.coordinates, right.costs.coordinates, strict=True):
        left_scaled = left_cost.numerator * right_cost.denominator
        right_scaled = right_cost.numerator * left_cost.denominator
        if left_scaled != right_scaled:
            return -1 if left_scaled < right_scaled else 1
    return (left.observation_id > right.observation_id) - (
        left.observation_id < right.observation_id
    )


def _check_frontier(frontier: RecoveryFrontier) -> tuple[bool, str]:
    budget_axes = frontier.pins.budget.axis_signature
    if any(point.costs.axis_signature != budget_axes for point in frontier.points):
        return False, "independent checker found frontier axes outside the pinned budget"
    if tuple(sorted(frontier.points, key=cmp_to_key(_point_order))) != frontier.points:
        return False, "independent checker found noncanonical frontier ordering"
    for index, left in enumerate(frontier.points):
        for right in frontier.points[index + 1 :]:
            relation = _vector_relation(left.costs, right.costs)
            if relation is not _Relation.INCOMPARABLE:
                return False, "independent checker found equal or dominated frontier points"
    return True, "frontier is canonical and pairwise nondominated"


def check_recovery_comparison(comparison: RecoveryComparison) -> tuple[bool, str]:
    """Recompute pins, exact frontier coverage, outcome, and provisional standing."""

    baseline = comparison.baseline_frontier
    retained = comparison.retained_frontier
    if baseline.branch is not RecoveryBranch.BASELINE:
        return False, "independent checker found the wrong baseline branch"
    if retained.branch is not RecoveryBranch.RETAINED:
        return False, "independent checker found the wrong retained branch"
    if baseline.pins != retained.pins:
        return False, "independent checker found mismatched recovery pins"
    for frontier in (baseline, retained):
        valid, reason = _check_frontier(frontier)
        if not valid:
            return False, reason

    expected_coverage: list[FrontierCoverage] = []
    saw_incomparable = False
    for baseline_point in baseline.points:
        witness: RecoveryFrontierPoint | None = None
        strict = False
        for retained_point in retained.points:
            try:
                relation = _vector_relation(retained_point.costs, baseline_point.costs)
            except ValueError as error:
                return False, str(error)
            if relation is _Relation.INCOMPARABLE:
                saw_incomparable = True
            if relation in (_Relation.RETAINED_BETTER, _Relation.EQUAL):
                witness = retained_point
                strict = relation is _Relation.RETAINED_BETTER
                break
        if witness is not None:
            expected_coverage.append(
                FrontierCoverage(
                    baseline_observation_id=baseline_point.observation_id,
                    retained_observation_id=witness.observation_id,
                    strict=strict,
                )
            )

    complete = bool(baseline.points) and len(expected_coverage) == len(baseline.points)
    if complete and any(item.strict for item in expected_coverage):
        expected_outcome = RecoveryComparisonOutcome.STRICT_ADVANTAGE
    elif saw_incomparable:
        expected_outcome = RecoveryComparisonOutcome.INCOMPARABLE
        expected_coverage = []
    else:
        expected_outcome = RecoveryComparisonOutcome.NO_ADVANTAGE
        expected_coverage = []

    if comparison.outcome is not expected_outcome:
        return False, "independent checker found a contradictory comparison outcome"
    if comparison.coverage != tuple(expected_coverage):
        return False, "independent checker found contradictory frontier coverage"
    if comparison.standing != "provisional_soft":
        return False, "independent checker rejects non-provisional G2A standing"
    return True, "independent integer checker validated the provisional comparison"
