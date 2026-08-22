"""Effect-free event replay and generic deterministic projection reduction."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from rci.core.events import DomainEvent
from rci.core.state import InquiryState, initial_state
from rci.core.transitions import evolve


def replay(
    events: Iterable[DomainEvent],
    *,
    state: InquiryState | None = None,
) -> InquiryState:
    """Rebuild aggregate state without executing any requested effect."""

    rebuilt = initial_state() if state is None else state
    for event in events:
        rebuilt = evolve(rebuilt, event)
    return rebuilt


def rebuild_projection[ProjectionT](
    events: Iterable[DomainEvent],
    *,
    initial: ProjectionT,
    apply: Callable[[ProjectionT, DomainEvent], ProjectionT],
) -> ProjectionT:
    """Fold events into a rebuildable caller-owned projection."""

    projection = initial
    for event in events:
        projection = apply(projection, event)
    return projection
