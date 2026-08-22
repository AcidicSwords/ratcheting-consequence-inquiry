"""Exact Pareto recovery arithmetic and independent comparison checks."""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from functools import cmp_to_key

from rci.memory.models import (
    CostCoordinate,
    CostVector,
    FrontierCoverage,
    RecoveryBranch,
    RecoveryComparison,
    RecoveryComparisonOutcome,
    RecoveryFrontier,
    RecoveryFrontierPoint,
    RecoveryObservation,
    RecoveryPins,
)
from rci.warrant.models import CheckReference


class RecoveryCompatibilityError(ValueError):
    """Recovery data cannot lawfully participate in one comparison."""


class CostRelation(StrEnum):
    LEFT_STRICTLY_BETTER = "left_strictly_better"
    RIGHT_STRICTLY_BETTER = "right_strictly_better"
    EQUAL = "equal"
    INCOMPARABLE = "incomparable"


def compare_cost_coordinates(left: CostCoordinate, right: CostCoordinate) -> int:
    """Return -1/0/1 using integer cross multiplication only."""

    if left.axis != right.axis:
        raise RecoveryCompatibilityError("cost coordinates use different typed axes")
    left_scaled = left.numerator * right.denominator
    right_scaled = right.numerator * left.denominator
    return (left_scaled > right_scaled) - (left_scaled < right_scaled)


def compare_cost_vectors(left: CostVector, right: CostVector) -> CostRelation:
    """Return the exact Pareto relation between matching cost vectors."""

    if left.axis_signature != right.axis_signature:
        raise RecoveryCompatibilityError("cost vectors use different named axes")
    directions = tuple(
        compare_cost_coordinates(left_coordinate, right_coordinate)
        for left_coordinate, right_coordinate in zip(
            left.coordinates,
            right.coordinates,
            strict=True,
        )
    )
    left_no_worse = all(direction <= 0 for direction in directions)
    right_no_worse = all(direction >= 0 for direction in directions)
    if left_no_worse and right_no_worse:
        return CostRelation.EQUAL
    if left_no_worse:
        return CostRelation.LEFT_STRICTLY_BETTER
    if right_no_worse:
        return CostRelation.RIGHT_STRICTLY_BETTER
    return CostRelation.INCOMPARABLE


def _compare_vectors_lexicographically(left: CostVector, right: CostVector) -> int:
    if left.axis_signature != right.axis_signature:
        raise RecoveryCompatibilityError("cannot order vectors with different axes")
    for left_coordinate, right_coordinate in zip(
        left.coordinates,
        right.coordinates,
        strict=True,
    ):
        direction = compare_cost_coordinates(left_coordinate, right_coordinate)
        if direction:
            return direction
    return 0


def _compare_points(left: RecoveryFrontierPoint, right: RecoveryFrontierPoint) -> int:
    vector_order = _compare_vectors_lexicographically(left.costs, right.costs)
    if vector_order:
        return vector_order
    return (left.observation_id > right.observation_id) - (
        left.observation_id < right.observation_id
    )


def _deduplicate_observations(
    observations: Iterable[RecoveryObservation],
) -> tuple[RecoveryObservation, ...]:
    by_id: dict[str, RecoveryObservation] = {}
    for observation in observations:
        prior = by_id.get(observation.id)
        if prior is not None and prior != observation:
            raise RecoveryCompatibilityError(
                f"recovery observation identity {observation.id!r} has conflicting contents"
            )
        by_id[observation.id] = observation
    return tuple(by_id[identifier] for identifier in sorted(by_id))


def derive_recovery_frontier(
    *,
    branch: RecoveryBranch,
    pins: RecoveryPins,
    observations: Iterable[RecoveryObservation],
) -> RecoveryFrontier:
    """Derive the stable nondominated successful-observation set."""

    deduplicated = _deduplicate_observations(observations)
    for observation in deduplicated:
        if observation.branch is not branch:
            raise RecoveryCompatibilityError("frontier observations have different branches")
        if observation.pins != pins:
            raise RecoveryCompatibilityError("frontier observations have different recovery pins")
        if observation.costs.axis_signature != pins.budget.axis_signature:
            raise RecoveryCompatibilityError("frontier observation axes differ from budget axes")

    successful_points = [
        RecoveryFrontierPoint(observation_id=observation.id, costs=observation.costs)
        for observation in deduplicated
        if observation.competence_established
    ]

    # Equal vectors are one Pareto point; retain the stable lowest observation identity.
    unique_points: list[RecoveryFrontierPoint] = []
    for point in sorted(successful_points, key=lambda item: item.observation_id):
        if any(
            compare_cost_vectors(point.costs, prior.costs) is CostRelation.EQUAL
            for prior in unique_points
        ):
            continue
        unique_points.append(point)

    frontier_points = tuple(
        sorted(
            (
                point
                for point in unique_points
                if not any(
                    other.observation_id != point.observation_id
                    and compare_cost_vectors(other.costs, point.costs)
                    is CostRelation.LEFT_STRICTLY_BETTER
                    for other in unique_points
                )
            ),
            key=cmp_to_key(_compare_points),
        )
    )
    return RecoveryFrontier(
        branch=branch,
        pins=pins,
        source_observation_ids=tuple(observation.id for observation in deduplicated),
        points=frontier_points,
    )


def check_recovery_frontier(frontier: RecoveryFrontier) -> tuple[bool, str]:
    """Check canonical point order, axes, and pairwise nondominance."""

    if any(
        point.costs.axis_signature != frontier.pins.budget.axis_signature
        for point in frontier.points
    ):
        return False, "frontier point axes differ from pinned budget axes"
    expected_order = tuple(sorted(frontier.points, key=cmp_to_key(_compare_points)))
    if expected_order != frontier.points:
        return False, "frontier points are not in canonical exact order"
    for index, left in enumerate(frontier.points):
        for right in frontier.points[index + 1 :]:
            relation = compare_cost_vectors(left.costs, right.costs)
            if relation is not CostRelation.INCOMPARABLE:
                return False, "frontier contains equal or dominated points"
    return True, "frontier points are exact, canonical, and pairwise nondominated"


def _evaluate_frontiers(
    baseline: RecoveryFrontier,
    retained: RecoveryFrontier,
) -> tuple[RecoveryComparisonOutcome, tuple[FrontierCoverage, ...]]:
    if baseline.branch is not RecoveryBranch.BASELINE:
        raise RecoveryCompatibilityError("baseline frontier has the wrong branch")
    if retained.branch is not RecoveryBranch.RETAINED:
        raise RecoveryCompatibilityError("retained frontier has the wrong branch")
    if baseline.pins != retained.pins:
        raise RecoveryCompatibilityError("recovery frontier pins do not match exactly")
    for frontier in (baseline, retained):
        valid, reason = check_recovery_frontier(frontier)
        if not valid:
            raise RecoveryCompatibilityError(reason)

    coverage: list[FrontierCoverage] = []
    observed_incomparability = False
    for baseline_point in baseline.points:
        covering_point: RecoveryFrontierPoint | None = None
        covering_strict = False
        for retained_point in retained.points:
            relation = compare_cost_vectors(retained_point.costs, baseline_point.costs)
            if relation is CostRelation.INCOMPARABLE:
                observed_incomparability = True
            if relation in (CostRelation.LEFT_STRICTLY_BETTER, CostRelation.EQUAL):
                covering_point = retained_point
                covering_strict = relation is CostRelation.LEFT_STRICTLY_BETTER
                break
        if covering_point is not None:
            coverage.append(
                FrontierCoverage(
                    baseline_observation_id=baseline_point.observation_id,
                    retained_observation_id=covering_point.observation_id,
                    strict=covering_strict,
                )
            )

    complete_coverage = bool(baseline.points) and len(coverage) == len(baseline.points)
    if complete_coverage and any(item.strict for item in coverage):
        outcome = RecoveryComparisonOutcome.STRICT_ADVANTAGE
    elif observed_incomparability:
        outcome = RecoveryComparisonOutcome.INCOMPARABLE
        coverage = []
    else:
        outcome = RecoveryComparisonOutcome.NO_ADVANTAGE
        coverage = []
    return outcome, tuple(coverage)


def compare_recovery_frontiers(
    *,
    comparison_id: str,
    baseline: RecoveryFrontier,
    retained: RecoveryFrontier,
    comparison_check: CheckReference,
) -> RecoveryComparison:
    """Build a provisional comparison after an independent check has been referenced."""

    outcome, coverage = _evaluate_frontiers(baseline, retained)
    return RecoveryComparison(
        id=comparison_id,
        baseline_frontier=baseline,
        retained_frontier=retained,
        outcome=outcome,
        coverage=coverage,
        comparison_check=comparison_check,
    )
