from __future__ import annotations

from datetime import UTC, datetime

import pytest

from rci.backlog import BacklogFinding, EvidenceStatus, reconcile
from rci.core import (
    ArtifactRef,
    InquiryState,
    RecordBacklogEffect,
    StartInquiry,
    decide,
    evolve,
    initial_state,
)
from rci.core.errors import InvalidCommandError, InvalidTransitionError
from rci.core.events import BacklogEffectRecorded
from rci.core.serialization import decode_event, encode_event
from rci.sdk import RCI

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def started_state() -> InquiryState:
    context = RCI.default_context()
    command = StartInquiry(
        event_id="event-start",
        inquiry_id="inquiry-backlog",
        occurred_at=NOW,
        manifest_artifact=ArtifactRef(digest="a" * 64, size=1),
        policy_version=context.warrant_policy_version,
        context=context,
    )
    return evolve(initial_state(), decide(initial_state(), command)[0])


def finding(status: EvidenceStatus) -> BacklogFinding:
    return BacklogFinding(
        id=f"finding-{status.value}",
        title="Preserve the ratchet",
        protected_consequence="replay-soundness",
        source="checked-test",
        evidence_status=status,
        evidence_digest="b" * 64,
        workspace_digest="c" * 64,
    )


def test_backlog_effects_are_owned_events_not_synthetic_external_returns() -> None:
    state = started_state()
    create, rank = reconcile((), (finding(EvidenceStatus.CHECKED_OPEN),))
    for index, effect in enumerate((create, rank)):
        command = RecordBacklogEffect(
            event_id=f"event-backlog-{index}",
            inquiry_id="inquiry-backlog",
            occurred_at=NOW,
            effect=effect,
        )
        event = decide(state, command)[0]
        assert decode_event(encode_event(event)) == event
        state = evolve(state, event)

    assert state.backlog_effects == (create, rank)
    assert state.effect_requests == ()
    assert (
        decide(
            state,
            RecordBacklogEffect(
                event_id="event-idempotent",
                inquiry_id="inquiry-backlog",
                occurred_at=NOW,
                effect=create,
            ),
        )
        == ()
    )


def test_proposal_only_close_and_out_of_order_mutation_fail_before_append() -> None:
    state = started_state()
    create, rank, close = reconcile((), (finding(EvidenceStatus.CHECKED_CLOSABLE),))

    with pytest.raises(InvalidCommandError, match="proposal-only"):
        decide(
            state,
            RecordBacklogEffect(
                event_id="event-close",
                inquiry_id="inquiry-backlog",
                occurred_at=NOW,
                effect=close,
            ),
        )
    with pytest.raises(InvalidCommandError, match="unknown item"):
        decide(
            state,
            RecordBacklogEffect(
                event_id="event-rank-before-create",
                inquiry_id="inquiry-backlog",
                occurred_at=NOW,
                effect=rank,
            ),
        )

    forged = BacklogEffectRecorded(
        event_id="event-forged-close",
        inquiry_id="inquiry-backlog",
        occurred_at=NOW,
        effect=close,
    )
    with pytest.raises(InvalidTransitionError, match="proposal-only"):
        evolve(state, forged)
    assert state.backlog_effects == ()
    assert create not in state.backlog_effects
