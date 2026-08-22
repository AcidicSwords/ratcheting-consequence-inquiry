"""Acceptance evidence that the public SDK uses the bounded scheduler."""

from __future__ import annotations

from datetime import UTC, datetime

from rci import RCI
from rci.core import (
    CancellationReason,
    CancelledOutcome,
    RecordAttemptOutcome,
)

FIXED_TIME = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)


def test_sdk_stops_unknown_after_three_attempts_for_the_exact_key(tmp_path: object) -> None:
    sdk = RCI(tmp_path, clock=lambda: FIXED_TIME)  # type: ignore[arg-type]
    sdk.start("bounded-scheduler")

    for index in range(3):
        planned = sdk.step("bounded-scheduler")
        assert planned.status == "needs_input"
        state = sdk.inspect("bounded-scheduler")
        request_state = state.effect_requests[-1]
        attempt = request_state.attempts[-1]
        assert request_state.request.timeout_seconds == 60
        sdk.dispatch(
            RecordAttemptOutcome(
                event_id=f"event-cancel-{index}",
                inquiry_id="bounded-scheduler",
                occurred_at=FIXED_TIME,
                request_id=request_state.request.id,
                outcome=CancelledOutcome(
                    attempt_id=attempt.plan.id,
                    route_id=attempt.plan.route.id,
                    reason_kind=CancellationReason.CALLER_CANCELLED,
                ),
            )
        )

    stopped = sdk.step("bounded-scheduler")
    final = sdk.inspect("bounded-scheduler")
    assert stopped.status == "unknown"
    assert len(final.effect_requests) == 3
    assert len({item.request.step_plan_id for item in final.effect_requests}) == 3
    assert sdk.replay("bounded-scheduler") == final
