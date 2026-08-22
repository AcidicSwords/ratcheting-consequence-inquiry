"""Acceptance evidence for the installable offline inquiry vertical slice."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from rci import RCI, AnswerSubmissionError
from rci.claims import Claim, RepresentationLevel
from rci.core import ArtifactRef, ReturnedOutcome

FIXED_TIME = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)


def test_manual_answer_moves_through_raw_and_semantic_stages(tmp_path: object) -> None:
    sdk = RCI(tmp_path, clock=lambda: FIXED_TIME)  # type: ignore[arg-type]

    started = sdk.start("vertical-slice")
    planned = sdk.step("vertical-slice")
    completed = sdk.submit_answer("vertical-slice", "backup power can also light it")

    assert started.sequence == 2
    assert len(started.obligations) == 1
    assert started.context is not None
    assert started.context.binding_revision == "binding-v1"
    assert started.context.scope_fingerprint
    assert started.manifest_artifact is not None
    manifest_bytes = sdk.artifacts.get_bytes(started.manifest_artifact)
    assert manifest_bytes.startswith(b'{"context":')
    manifest = json.loads(manifest_bytes)
    catalog_ref = ArtifactRef.model_validate(manifest["question_catalog_artifact"])
    assert sdk.artifacts.get_bytes(catalog_ref)
    assert planned.status == "needs_input"
    assert planned.sequence == 6
    assert completed.sequence == 11
    request = completed.effect_requests[0]
    outcome = request.attempts[0].outcome
    assert isinstance(outcome, ReturnedOutcome)
    raw_ref = outcome.external_return.raw_payload.artifact
    assert raw_ref is not None
    assert raw_ref.encoding == "utf-8"
    assert outcome.external_return.capture_boundary == "manual-answer-submission"
    assert outcome.external_return.captured_at == FIXED_TIME
    result = request.accepted_result
    assert result is not None
    assert raw_ref.digest != result.semantic_artifact.digest
    assert sdk.artifacts.get_bytes(raw_ref) == b"backup power can also light it"

    claim = Claim.model_validate_json(
        sdk.artifacts.get_bytes(result.semantic_artifact), strict=True
    )
    assert claim.representation_level is RepresentationLevel.L0_OPAQUE
    assert claim.payload == "backup power can also light it"
    assert completed.claims == (claim,)
    obligation_status = completed.current_obligation_status(started.obligations[0].id)
    assert obligation_status is not None
    assert obligation_status.value == "satisfied"
    assert sdk.step("vertical-slice").status == "satisfied"


def test_start_and_answer_are_idempotent_at_the_public_boundary(tmp_path: object) -> None:
    sdk = RCI(tmp_path, clock=lambda: FIXED_TIME)  # type: ignore[arg-type]

    first = sdk.start("idempotent")
    second = sdk.start("idempotent")
    sdk.step("idempotent")
    answered = sdk.submit_answer("idempotent", "opaque")
    repeated = sdk.submit_answer("idempotent", "opaque")

    assert first == second
    assert answered == repeated
    assert len(repeated.effect_requests) == 1
    with pytest.raises(AnswerSubmissionError, match="no pending manual answer"):
        sdk.submit_answer("idempotent", "different text is rejected")
