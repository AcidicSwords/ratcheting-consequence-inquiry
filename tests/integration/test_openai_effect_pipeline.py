from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest

from rci import RCI
from rci.core import (
    AttemptKey,
    PlanEffectAttempt,
    PresentationUnknownOutcome,
    PresentationUnknownReason,
    RecordStepPlan,
    RequestEffect,
    ReturnedOutcome,
)
from rci.generators import (
    OpenAIResponsesGenerator,
    OpenAIResponseSummary,
    QuestionInvocation,
    openai_route_definition,
    prepare_openai_attempt,
)
from rci.orchestration import (
    AdapterDecodeResult,
    ObligationEntry,
    PersistedEffectExecutor,
    RouteRegistry,
    RouteValidationError,
    UnknownRouteDefinitionError,
    plan_next,
)

NOW = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)


def _invocation(
    *,
    obligation_id: str,
    binding_revision: str,
    scope_fingerprint: str,
) -> QuestionInvocation:
    return QuestionInvocation(
        invocation_id="openai-invocation-1",
        contract_id="obligation-characterization",
        contract_version="1.0.0",
        scope_fingerprint=scope_fingerprint,
        binding_revision=binding_revision,
        referent_ids=(obligation_id,),
        rendered_question="What remains?",
        local_context=("opaque local context",),
        max_output_tokens=32,
    )


class _RawResponse:
    def __init__(self, content: bytes) -> None:
        self.content = content


class _WithRawResponse:
    def __init__(self, content: bytes, on_call: Callable[[], None]) -> None:
        self.content = content
        self.on_call = on_call
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> _RawResponse:
        self.on_call()
        self.calls.append(kwargs)
        return _RawResponse(self.content)


class _Responses:
    def __init__(self, raw: _WithRawResponse) -> None:
        self.with_raw_response = raw


class _Client:
    def __init__(self, raw: _WithRawResponse) -> None:
        self.base_url = "https://api.openai.com/v1/"
        self.responses = _Responses(raw)


class _RaisingRawResponses:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def create(self, **kwargs: object) -> _RawResponse:
        del kwargs
        raise self.error


class _RaisingResponses:
    def __init__(self, error: Exception) -> None:
        self.with_raw_response = _RaisingRawResponses(error)


class _RaisingClient:
    def __init__(self, error: Exception) -> None:
        self.base_url = "https://api.openai.com/v1"
        self.responses = _RaisingResponses(error)


class _MismatchedEndpointClient:
    base_url = "https://user:secret@proxy.example/v1?token=leak"

    @property
    def responses(self) -> object:
        raise AssertionError("endpoint mismatch touched the transport")


def _prepare(
    root: Path,
    *,
    raw_body: bytes,
) -> tuple[
    RCI,
    RouteRegistry,
    OpenAIResponsesGenerator,
    _WithRawResponse,
    str,
    str,
]:
    sdk = RCI(root, clock=lambda: NOW)
    inquiry_id = "openai-pipeline"
    started = sdk.start(inquiry_id)
    assert started.context is not None
    obligation = started.obligations[0]
    invocation = _invocation(
        obligation_id=obligation.id,
        binding_revision=obligation.binding_revision,
        scope_fingerprint=obligation.scope.fingerprint,
    )
    attempt_key = AttemptKey(
        obligation_fingerprint=obligation.fingerprint,
        contract_id=invocation.contract_id,
        contract_version=invocation.contract_version,
        binding_revision=obligation.binding_revision,
    )
    step_plan = plan_next(
        (
            ObligationEntry(
                obligation=obligation,
                attempt_key=attempt_key,
                creation_sequence=1,
            ),
        ),
        steps_used=started.sequence,
        policy_version=started.context.scheduler_policy_version,
    )
    routes = RouteRegistry(
        (openai_route_definition("explicit-model"),),
        artifacts=sdk.artifacts,
    )
    request, plan = prepare_openai_attempt(
        invocation,
        model="explicit-model",
        step_plan=step_plan,
        request_id="openai-request-1",
        attempt_id="openai-attempt-1",
        route_id="openai-route-1",
        client_library_version="fake-1.0",
        artifacts=sdk.artifacts,
        routes=routes,
    )
    sdk.dispatch_batch(
        inquiry_id,
        (
            RecordStepPlan(
                event_id="openai-step-plan-recorded-event",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                plan=step_plan,
            ),
            RequestEffect(
                event_id="openai-requested-event",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                request=request,
            ),
            PlanEffectAttempt(
                event_id="openai-planned-event",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                plan=plan,
            ),
        ),
    )

    def assert_started_before_provider() -> None:
        persisted = sdk.inspect(inquiry_id).request_by_id(request.id)
        assert persisted is not None
        assert persisted.attempts[0].started is True
        assert persisted.attempts[0].outcome is None

    raw = _WithRawResponse(raw_body, assert_started_before_provider)
    adapter = OpenAIResponsesGenerator(model="explicit-model", client=_Client(raw))
    return sdk, routes, adapter, raw, request.id, plan.id


def test_openai_executes_only_after_start_and_captures_raw_before_decode(
    tmp_path: Path,
) -> None:
    raw_body = (
        b'{ "id":"response-1", "status":"completed", "output":['
        b'{"type":"message","content":[{"type":"output_text","text":"opaque"}]}'
        b'], "usage":{"input_tokens":4,"output_tokens":1,"total_tokens":5} }'
    )
    sdk, routes, adapter, raw, request_id, attempt_id = _prepare(
        tmp_path,
        raw_body=raw_body,
    )
    executor = PersistedEffectExecutor(
        events=sdk.events,
        artifacts=sdk.artifacts,
        routes=routes,
        clock=lambda: NOW,
    )

    completed = adapter.execute_persisted(
        executor,
        inquiry_id="openai-pipeline",
        request_id=request_id,
        attempt_id=attempt_id,
    )

    assert len(raw.calls) == 1
    call = raw.calls[0]
    assert call["model"] == "explicit-model"
    assert call["tools"] == []
    assert call["store"] is False
    assert call["max_output_tokens"] == 32
    assert call["timeout"] == 60.0
    request_state = completed.request_by_id(request_id)
    assert request_state is not None
    outcome = request_state.attempts[0].outcome
    assert isinstance(outcome, ReturnedOutcome)
    raw_ref = outcome.external_return.raw_payload.artifact
    assert raw_ref is not None
    assert raw_ref.encoding == "binary"
    assert outcome.external_return.capture_boundary == "adapter-perform-exact-return-bytes"
    assert outcome.external_return.capture_encoding == "binary"
    assert outcome.external_return.captured_at == NOW
    assert sdk.artifacts.get_bytes(raw_ref) == raw_body
    accepted = request_state.accepted_result
    assert accepted is not None
    assert accepted.semantic_artifact.digest != raw_ref.digest
    assert accepted.semantic_artifact.encoding == "utf-8"
    assert request_state.request.input_artifact.encoding == "utf-8"
    assert request_state.attempts[0].plan.route.definition_artifact.encoding == "utf-8"
    summary = OpenAIResponseSummary.model_validate_json(
        sdk.artifacts.get_bytes(accepted.semantic_artifact),
        strict=True,
    )
    assert summary.execution_status == "completed"
    assert summary.output_text == "opaque"
    assert dict(summary.usage)["total_tokens"] == 5
    environment_bytes = sdk.artifacts.get_bytes(
        request_state.attempts[0].plan.route.execution_environment_artifact
    )
    environment_text = environment_bytes.decode().lower()
    assert all(
        forbidden not in environment_text
        for forbidden in ("api_key", "credential", "password", "secret", "token")
    )

    replayed = sdk.replay("openai-pipeline")
    assert replayed == completed
    adapter.execute_persisted(
        executor,
        inquiry_id="openai-pipeline",
        request_id=request_id,
        attempt_id=attempt_id,
    )
    assert len(raw.calls) == 1


def test_unknown_route_and_request_digest_fail_before_attempt_start(tmp_path: Path) -> None:
    sdk, routes, adapter, raw, request_id, _attempt_id = _prepare(tmp_path, raw_body=b"{}")
    request_state = sdk.inspect("openai-pipeline").request_by_id(request_id)
    assert request_state is not None
    plan = request_state.attempts[0].plan
    tampered_route = plan.route.model_copy(update={"definition_id": "unknown-route"})
    tampered_plan = plan.model_copy(update={"id": "tampered-attempt", "route": tampered_route})
    sdk.dispatch(
        PlanEffectAttempt(
            event_id="tampered-plan-event",
            inquiry_id="openai-pipeline",
            occurred_at=NOW,
            plan=tampered_plan,
        )
    )
    executor = PersistedEffectExecutor(
        events=sdk.events,
        artifacts=sdk.artifacts,
        routes=routes,
        clock=lambda: NOW,
    )

    with pytest.raises(UnknownRouteDefinitionError):
        adapter.execute_persisted(
            executor,
            inquiry_id="openai-pipeline",
            request_id=request_id,
            attempt_id=tampered_plan.id,
        )

    persisted = sdk.inspect("openai-pipeline").request_by_id(request_id)
    assert persisted is not None
    tampered = next(item for item in persisted.attempts if item.plan.id == tampered_plan.id)
    assert tampered.started is False
    assert raw.calls == []

    digest_route = plan.route.model_copy(
        update={"id": "bad-digest-route", "request_or_action_digest": "0" * 64}
    )
    digest_plan = plan.model_copy(update={"id": "bad-digest-attempt", "route": digest_route})
    sdk.dispatch(
        PlanEffectAttempt(
            event_id="bad-digest-plan-event",
            inquiry_id="openai-pipeline",
            occurred_at=NOW,
            plan=digest_plan,
        )
    )
    with pytest.raises(RouteValidationError, match="request digest"):
        adapter.execute_persisted(
            executor,
            inquiry_id="openai-pipeline",
            request_id=request_id,
            attempt_id=digest_plan.id,
        )
    assert raw.calls == []


def test_decode_resume_does_not_repeat_a_captured_external_call(tmp_path: Path) -> None:
    raw_body = json.dumps(
        {"id": "response-1", "status": "completed", "output": []},
        separators=(",", ":"),
    ).encode()
    sdk, routes, adapter, raw, request_id, attempt_id = _prepare(
        tmp_path,
        raw_body=raw_body,
    )
    executor = PersistedEffectExecutor(
        events=sdk.events,
        artifacts=sdk.artifacts,
        routes=routes,
        clock=lambda: NOW,
    )
    original_decode = adapter.decode_exact
    decoding_available = False

    def crash_once(raw_bytes: bytes) -> AdapterDecodeResult:
        if not decoding_available:
            raise RuntimeError("simulated crash after authoritative return capture")
        return original_decode(raw_bytes)

    adapter.decode_exact = crash_once  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="simulated crash"):
        adapter.execute_persisted(
            executor,
            inquiry_id="openai-pipeline",
            request_id=request_id,
            attempt_id=attempt_id,
        )
    after_crash = sdk.inspect("openai-pipeline").request_by_id(request_id)
    assert after_crash is not None
    assert isinstance(after_crash.attempts[0].outcome, ReturnedOutcome)
    assert after_crash.decode_outcomes == ()
    assert len(raw.calls) == 1

    decoding_available = True
    completed = adapter.execute_persisted(
        executor,
        inquiry_id="openai-pipeline",
        request_id=request_id,
        attempt_id=attempt_id,
    )
    assert completed.request_by_id(request_id) is not None
    assert len(raw.calls) == 1


@pytest.mark.parametrize(
    ("error", "expected_reason"),
    (
        (TimeoutError("late"), PresentationUnknownReason.TIMEOUT),
        (ConnectionError("uncertain"), PresentationUnknownReason.TRANSPORT_ERROR),
    ),
)
def test_openai_timeout_and_transport_uncertainty_remain_typed(
    tmp_path: Path,
    error: Exception,
    expected_reason: PresentationUnknownReason,
) -> None:
    sdk, routes, _adapter, _raw, request_id, attempt_id = _prepare(
        tmp_path,
        raw_body=b"unused",
    )
    adapter = OpenAIResponsesGenerator(
        model="explicit-model",
        client=_RaisingClient(error),
    )
    state = adapter.execute_persisted(
        PersistedEffectExecutor(
            events=sdk.events,
            artifacts=sdk.artifacts,
            routes=routes,
            clock=lambda: NOW,
        ),
        inquiry_id="openai-pipeline",
        request_id=request_id,
        attempt_id=attempt_id,
    )
    request_state = state.request_by_id(request_id)
    assert request_state is not None
    outcome = request_state.attempts[0].outcome
    assert isinstance(outcome, PresentationUnknownOutcome)
    assert outcome.reason_kind is expected_reason
    assert request_state.decode_outcomes == ()
    assert request_state.accepted_result is None


def test_openai_endpoint_mismatch_fails_before_start_or_transport(tmp_path: Path) -> None:
    sdk, routes, _adapter, raw, request_id, attempt_id = _prepare(
        tmp_path,
        raw_body=b"unused",
    )
    adapter = OpenAIResponsesGenerator(
        model="explicit-model",
        client=_MismatchedEndpointClient(),
    )
    state = adapter.execute_persisted(
        PersistedEffectExecutor(
            events=sdk.events,
            artifacts=sdk.artifacts,
            routes=routes,
            clock=lambda: NOW,
        ),
        inquiry_id="openai-pipeline",
        request_id=request_id,
        attempt_id=attempt_id,
    )
    request_state = state.request_by_id(request_id)
    assert request_state is not None
    assert request_state.attempts[0].started is False
    assert request_state.no_attempt_dispositions[0].reason_kind.value == "unsupported"
    assert (
        request_state.no_attempt_dispositions[0].step_plan_id == request_state.request.step_plan_id
    )
    assert raw.calls == []
