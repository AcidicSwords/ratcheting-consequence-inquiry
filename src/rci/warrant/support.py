"""Pure ATMS-like support calculations without hidden discharge."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from rci.warrant.checks import (
    checker_verdict_index,
    evidence_index,
    resolve_check_reference,
)
from rci.warrant.models import (
    ActiveLemmaView,
    CheckerVerdictRecord,
    Evidence,
    Nogood,
    NogoodStandingChange,
    PropositionKind,
    SupportEnvironment,
    SupportRoute,
    SupportRouteStandingChange,
    SupportStanding,
    TheorySelector,
    WarrantClass,
    WarrantedLemma,
)


def minimize_support_environments(
    environments: Iterable[SupportEnvironment],
) -> tuple[SupportEnvironment, ...]:
    """Return stable antichains without comparing different scopes or bindings."""

    unique = {environment.id: environment for environment in environments}
    ordered = sorted(
        unique.values(),
        key=lambda item: (
            item.scope_fingerprint,
            item.binding_revision,
            item.finite_universe_hash or "",
            len(item.assumption_ids),
            item.assumption_ids,
            item.id,
        ),
    )
    minimal: list[SupportEnvironment] = []
    for candidate in ordered:
        same_universe = (
            item
            for item in minimal
            if item.scope_fingerprint == candidate.scope_fingerprint
            and item.binding_revision == candidate.binding_revision
            and item.finite_universe_hash == candidate.finite_universe_hash
        )
        if any(item.assumptions <= candidate.assumptions for item in same_universe):
            continue
        minimal.append(candidate)
    return tuple(minimal)


def compute_open_boundary(
    *,
    required_dependency_ids: Iterable[str],
    environment: SupportEnvironment,
    independently_discharged_ids: Iterable[str],
) -> tuple[str, ...]:
    supplied = environment.assumptions | frozenset(independently_discharged_ids)
    return tuple(sorted(set(required_dependency_ids) - supplied))


def support_environment_stands(
    environment: SupportEnvironment,
    *,
    current_assumption_ids: Iterable[str],
    nogoods: Iterable[Nogood] = (),
    evidence_records: Iterable[Evidence] = (),
    checker_verdicts: Iterable[CheckerVerdictRecord] = (),
    authorized_checker_ids: Iterable[str] = (),
    policy_version: str,
) -> bool:
    """No-nogood is insufficient: realizability itself must have a valid check."""

    evidence_by_id = evidence_index(evidence_records)
    checker_verdict_by_id = checker_verdict_index(checker_verdicts)
    realizable, _ = resolve_check_reference(
        environment.realizability_check,
        evidence_by_id=evidence_by_id,
        checker_verdict_by_id=checker_verdict_by_id,
        proposition_id=environment.id,
        proposition_kind=PropositionKind.EXISTENTIAL,
        scope_fingerprint=environment.scope_fingerprint,
        authorized_checker_ids=authorized_checker_ids,
    )
    if not realizable:
        return False
    current = frozenset(current_assumption_ids)
    if not environment.assumptions <= current:
        return False
    for nogood in nogoods:
        checked, _ = resolve_check_reference(
            nogood.check,
            evidence_by_id=evidence_by_id,
            checker_verdict_by_id=checker_verdict_by_id,
            proposition_id=nogood.id,
            proposition_kind=PropositionKind.EXISTENTIAL,
            scope_fingerprint=nogood.scope_fingerprint,
            authorized_checker_ids=authorized_checker_ids,
        )
        if (
            nogood.scope_fingerprint == environment.scope_fingerprint
            and nogood.binding_revision == environment.binding_revision
            and nogood.finite_universe_hash == environment.finite_universe_hash
            and nogood.policy_version == policy_version
            and checked
            and frozenset(nogood.incompatible_assumption_ids) <= environment.assumptions
        ):
            return False
    return True


def _route_applicable(
    lemma: WarrantedLemma,
    route_index: int,
    *,
    current_assumption_ids: Iterable[str],
    current_context_ids: frozenset[str],
    nogoods: Iterable[Nogood],
    evidence_records: tuple[Evidence, ...],
    checker_verdicts: tuple[CheckerVerdictRecord, ...],
    authorized_checker_ids: tuple[str, ...],
) -> bool:
    route = lemma.support.support_routes[route_index]
    route_checked, _ = resolve_check_reference(
        route.certificate_check,
        evidence_by_id=evidence_index(evidence_records),
        checker_verdict_by_id=checker_verdict_index(checker_verdicts),
        proposition_id=lemma.version.relation_id,
        proposition_kind=lemma.version.proposition_kind,
        scope_fingerprint=lemma.version.scope.fingerprint,
        authorized_checker_ids=authorized_checker_ids,
    )
    return (
        route.environment.scope_fingerprint == lemma.version.scope.fingerprint
        and route.environment.binding_revision == lemma.version.scope.binding_revision
        and route.environment.finite_universe_hash == lemma.version.scope.finite_universe_hash
        and route_checked
        and _applicability_stands(
            lemma,
            current_context_ids=current_context_ids,
        )
        and support_environment_stands(
            route.environment,
            current_assumption_ids=current_assumption_ids,
            nogoods=nogoods,
            evidence_records=evidence_records,
            checker_verdicts=checker_verdicts,
            authorized_checker_ids=authorized_checker_ids,
            policy_version=lemma.support.policy_version,
        )
    )


def _applicability_stands(
    lemma: WarrantedLemma,
    *,
    current_context_ids: frozenset[str],
) -> bool:
    """Require the named guard and all contextual preconditions to be active.

    ``always`` is the sole unconditional guard in the G1 policy. Every other
    condition must be named by the caller's checked active context.
    """

    applicability = lemma.version.applicability
    guard_active = (
        applicability.condition_id == "always" or applicability.condition_id in current_context_ids
    )
    return guard_active and set(applicability.required_context_ids) <= current_context_ids


def grounded_lemma_ids(
    lemmas: Iterable[WarrantedLemma],
    *,
    current_assumption_ids: Iterable[str],
    current_context_ids: Iterable[str],
    nogoods: Iterable[Nogood] = (),
    evidence_records: Iterable[Evidence] = (),
    checker_verdicts: Iterable[CheckerVerdictRecord] = (),
    authorized_checker_ids: Iterable[str] = (),
) -> frozenset[str]:
    """Compute the least fixed point; an unsupported cycle contributes no seed."""

    lemma_tuple = tuple(lemmas)
    current_assumptions = frozenset(current_assumption_ids)
    current_context = frozenset(current_context_ids)
    nogood_tuple = tuple(nogoods)
    evidence_tuple = tuple(evidence_records)
    checker_tuple = tuple(checker_verdicts)
    authorized_tuple = tuple(authorized_checker_ids)
    grounded: set[str] = set()
    changed = True
    while changed:
        changed = False
        for lemma in lemma_tuple:
            if lemma.id in grounded or lemma.support.warrant_class is not WarrantClass.HARD:
                continue
            route_stands = any(
                _route_applicable(
                    lemma,
                    index,
                    current_assumption_ids=current_assumptions,
                    current_context_ids=current_context,
                    nogoods=nogood_tuple,
                    evidence_records=evidence_tuple,
                    checker_verdicts=checker_tuple,
                    authorized_checker_ids=authorized_tuple,
                )
                and set(route.required_dependency_ids) <= grounded
                for index, route in enumerate(lemma.support.support_routes)
            )
            if route_stands:
                grounded.add(lemma.id)
                changed = True
    return frozenset(grounded)


def select_active_theory(
    lemmas: Iterable[WarrantedLemma],
    *,
    selector: TheorySelector,
    nogoods: Iterable[Nogood] = (),
    support_route_standing_changes: Iterable[SupportRouteStandingChange] = (),
    nogood_standing_changes: Iterable[NogoodStandingChange] = (),
    evidence_records: Iterable[Evidence] = (),
    checker_verdicts: Iterable[CheckerVerdictRecord] = (),
    authorized_checker_ids: Iterable[str] = (),
) -> tuple[ActiveLemmaView, ...]:
    """Derive an exact current view without creating semantic authority.

    Routes and nogoods are immutable.  Their append-only standing histories only
    affect this derived view, so withdrawal and restoration never rewrite proof
    provenance.
    """

    route_standing = {
        change.support_route_id: change.standing for change in support_route_standing_changes
    }
    nogood_standing = {change.nogood_id: change.standing for change in nogood_standing_changes}
    selected_lemmas: list[WarrantedLemma] = []
    for lemma in lemmas:
        if (
            lemma.version.scope.fingerprint != selector.scope_fingerprint
            or lemma.version.scope.binding_revision != selector.binding_revision
            or lemma.version.scope.finite_universe_hash != selector.finite_universe_hash
            or lemma.support.policy_version != selector.policy_version
        ):
            continue
        standing_routes = tuple(
            route
            for route in lemma.support.all_support_routes
            if route_standing.get(route.id, SupportStanding.STANDING) is SupportStanding.STANDING
        )
        if standing_routes:
            selected_lemmas.append(
                lemma.model_copy(
                    update={
                        "support": lemma.support.model_copy(
                            update={
                                "support_routes": standing_routes,
                                "historical_support_routes": (),
                            }
                        )
                    }
                )
            )
    lemma_tuple = tuple(selected_lemmas)
    current_assumptions = frozenset(selector.current_assumption_ids)
    context = frozenset(selector.current_context_ids)
    nogood_tuple = tuple(
        nogood
        for nogood in nogoods
        if nogood.scope_fingerprint == selector.scope_fingerprint
        and nogood.binding_revision == selector.binding_revision
        and nogood.finite_universe_hash == selector.finite_universe_hash
        and nogood.policy_version == selector.policy_version
        and nogood_standing.get(nogood.id, SupportStanding.STANDING) is SupportStanding.STANDING
    )
    evidence_tuple = tuple(evidence_records)
    checker_tuple = tuple(checker_verdicts)
    authorized_tuple = tuple(authorized_checker_ids)
    grounded = grounded_lemma_ids(
        lemma_tuple,
        current_assumption_ids=current_assumptions,
        current_context_ids=context,
        nogoods=nogood_tuple,
        evidence_records=evidence_tuple,
        checker_verdicts=checker_tuple,
        authorized_checker_ids=authorized_tuple,
    )
    views: list[ActiveLemmaView] = []
    for lemma in sorted(lemma_tuple, key=lambda item: item.id):
        if lemma.id not in grounded:
            continue
        applicable_routes = tuple(
            route
            for index, route in enumerate(lemma.support.support_routes)
            if _route_applicable(
                lemma,
                index,
                current_assumption_ids=current_assumptions,
                current_context_ids=context,
                nogoods=nogood_tuple,
                evidence_records=evidence_tuple,
                checker_verdicts=checker_tuple,
                authorized_checker_ids=authorized_tuple,
            )
            and set(route.required_dependency_ids) <= grounded
        )
        minimal_routes: list[SupportRoute] = []
        for route in sorted(
            applicable_routes,
            key=lambda item: (
                len(item.environment.assumption_ids),
                item.environment.assumption_ids,
                item.id,
            ),
        ):
            if any(
                current.environment.assumptions <= route.environment.assumptions
                for current in minimal_routes
            ):
                continue
            minimal_routes.append(route)
        primary_route = minimal_routes[0]
        views.append(
            ActiveLemmaView(
                lemma_version_id=lemma.id,
                relation_id=lemma.version.relation_id,
                standing_support_route_id=primary_route.id,
                standing_support_route_ids=tuple(route.id for route in minimal_routes),
                scope_fingerprint=selector.scope_fingerprint,
                binding_revision=selector.binding_revision,
                finite_universe_hash=selector.finite_universe_hash,
                policy_version=selector.policy_version,
            )
        )
    return tuple(views)


def active_lemma_views(
    lemmas: Iterable[WarrantedLemma],
    *,
    selector: TheorySelector,
    nogoods: Iterable[Nogood] = (),
    support_route_standing_changes: Iterable[SupportRouteStandingChange] = (),
    nogood_standing_changes: Iterable[NogoodStandingChange] = (),
    evidence_records: Iterable[Evidence] = (),
    checker_verdicts: Iterable[CheckerVerdictRecord] = (),
    authorized_checker_ids: Iterable[str] = (),
) -> tuple[ActiveLemmaView, ...]:
    return select_active_theory(
        lemmas,
        selector=selector,
        nogoods=nogoods,
        support_route_standing_changes=support_route_standing_changes,
        nogood_standing_changes=nogood_standing_changes,
        evidence_records=evidence_records,
        checker_verdicts=checker_verdicts,
        authorized_checker_ids=authorized_checker_ids,
    )


def active_lemma_ids(
    lemmas: Iterable[WarrantedLemma],
    *,
    selector: TheorySelector,
    nogoods: Iterable[Nogood] = (),
    support_route_standing_changes: Iterable[SupportRouteStandingChange] = (),
    nogood_standing_changes: Iterable[NogoodStandingChange] = (),
    evidence_records: Iterable[Evidence] = (),
    checker_verdicts: Iterable[CheckerVerdictRecord] = (),
    authorized_checker_ids: Iterable[str] = (),
) -> frozenset[str]:
    return frozenset(
        view.lemma_version_id
        for view in select_active_theory(
            lemmas,
            selector=selector,
            nogoods=nogoods,
            support_route_standing_changes=support_route_standing_changes,
            nogood_standing_changes=nogood_standing_changes,
            evidence_records=evidence_records,
            checker_verdicts=checker_verdicts,
            authorized_checker_ids=authorized_checker_ids,
        )
    )


def ancestry_is_acyclic(predecessors_by_version: Mapping[str, Iterable[str]]) -> bool:
    """Check version ancestry separately from recursive proof/support topology."""

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(version_id: str) -> bool:
        if version_id in visiting:
            return False
        if version_id in visited:
            return True
        visiting.add(version_id)
        for predecessor in predecessors_by_version.get(version_id, ()):
            if predecessor not in predecessors_by_version or not visit(predecessor):
                return False
        visiting.remove(version_id)
        visited.add(version_id)
        return True

    return all(visit(version_id) for version_id in predecessors_by_version)


def support_graph_is_acyclic(lemmas: Iterable[WarrantedLemma]) -> bool:
    """Compatibility gate for the first Goal's atomic positive-cycle rejection."""

    lemma_tuple = tuple(lemmas)
    known = {lemma.id for lemma in lemma_tuple}
    graph = {
        lemma.id: {
            dependency
            for route in lemma.support.all_support_routes
            for dependency in route.required_dependency_ids
            if dependency in known
        }
        for lemma in lemma_tuple
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return False
        if node in visited:
            return True
        visiting.add(node)
        if not all(visit(successor) for successor in graph[node]):
            return False
        visiting.remove(node)
        visited.add(node)
        return True

    return all(visit(node) for node in graph)


def ungrounded_support_cycles(
    lemmas: Iterable[WarrantedLemma],
    *,
    current_assumption_ids: Iterable[str],
    current_context_ids: Iterable[str],
    nogoods: Iterable[Nogood] = (),
    evidence_records: Iterable[Evidence] = (),
    checker_verdicts: Iterable[CheckerVerdictRecord] = (),
    authorized_checker_ids: Iterable[str] = (),
) -> tuple[tuple[str, ...], ...]:
    """Report recursive components that have no independently grounded route."""

    lemma_tuple = tuple(lemmas)
    by_id = {lemma.id: lemma for lemma in lemma_tuple}
    grounded = grounded_lemma_ids(
        lemma_tuple,
        current_assumption_ids=current_assumption_ids,
        current_context_ids=current_context_ids,
        nogoods=nogoods,
        evidence_records=evidence_records,
        checker_verdicts=checker_verdicts,
        authorized_checker_ids=authorized_checker_ids,
    )
    unresolved = set(by_id) - set(grounded)
    graph = {
        lemma_id: {
            dependency
            for route in by_id[lemma_id].support.support_routes
            for dependency in route.open_dependency_ids
            if dependency in unresolved
        }
        for lemma_id in unresolved
    }
    index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[tuple[str, ...]] = []

    def connect(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for successor in sorted(graph[node]):
            if successor not in indices:
                connect(successor)
                lowlinks[node] = min(lowlinks[node], lowlinks[successor])
            elif successor in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[successor])
        if lowlinks[node] == indices[node]:
            component: list[str] = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node:
                    break
            ordered = tuple(sorted(component))
            if len(ordered) > 1 or node in graph[node]:
                components.append(ordered)

    for node in sorted(graph):
        if node not in indices:
            connect(node)
    return tuple(sorted(components))
