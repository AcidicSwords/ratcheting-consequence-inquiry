from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from rci import RCI
from rci.core import (
    AttemptKey,
    InquiryState,
    PlanEffectAttempt,
    RecordStepPlan,
    RequestEffect,
    ReturnedOutcome,
    StepPlan,
)
from rci.evaluation import (
    CapturedInput,
    DockerEvidenceBackend,
    EvidenceEffectAdapter,
    EvidenceRawResult,
    EvidenceResultSummary,
    EvidenceRunRequest,
    EvidenceRunResult,
    EvidenceRunStatus,
    docker_evidence_route_definition,
    prepare_evidence_attempt,
)
from rci.orchestration import (
    ObligationEntry,
    PersistedEffectExecutor,
    RouteRegistry,
    plan_next,
)

NOW = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)


def _evidence_step_plan(state: InquiryState) -> StepPlan:
    assert state.context is not None
    obligation = state.obligations[0]
    attempt_key = AttemptKey(
        obligation_fingerprint=obligation.fingerprint,
        contract_id="evaluation.bounded-evidence",
        contract_version="1.0.0",
        binding_revision=obligation.binding_revision,
    )
    return plan_next(
        (
            ObligationEntry(
                obligation=obligation,
                attempt_key=attempt_key,
                creation_sequence=1,
            ),
        ),
        steps_used=state.sequence,
        policy_version=state.context.scheduler_policy_version,
    )


class _FakeDockerBackend(DockerEvidenceBackend):
    def __init__(self) -> None:
        super().__init__(
            image=f"example/rci-checker@sha256:{'a' * 64}",
            allowed_commands=("rci-checker",),
        )
        self.calls = 0
        self.on_execute: Callable[[], None] = lambda: None
        self.workspace: Path | None = None

    def execute(
        self,
        request: EvidenceRunRequest,
        captured_workspace: Path,
    ) -> EvidenceRunResult:
        self.on_execute()
        self.calls += 1
        self.workspace = captured_workspace
        assert request.argv == ("rci-checker", "--case", "/evidence/case.bin")
        assert (captured_workspace / "case.bin").read_bytes() == b"opaque\x00case"
        (captured_workspace / "scratch-only").write_bytes(b"discarded")
        return EvidenceRunResult(
            status=EvidenceRunStatus.COMPLETED,
            exit_code=0,
            stdout=b"result\x00bytes",
            stderr=b"warning\xff",
        )


def test_evidence_runner_is_persisted_bounded_and_workspace_isolated(tmp_path: Path) -> None:
    live_source = tmp_path / "live-source.py"
    live_source.write_text("unchanged")
    sdk = RCI(tmp_path, clock=lambda: NOW)
    inquiry_id = "evidence-pipeline"
    started = sdk.start(inquiry_id)
    step_plan = _evidence_step_plan(started)
    backend = _FakeDockerBackend()
    definition = docker_evidence_route_definition(backend, command="rci-checker")
    routes = RouteRegistry((definition,), artifacts=sdk.artifacts)
    request, plan = prepare_evidence_attempt(
        EvidenceRunRequest(
            argv=("rci-checker", "--case", "/evidence/case.bin"),
            inputs=(CapturedInput(relative_path="case.bin", content=b"opaque\x00case"),),
            timeout_seconds=7,
            max_output_bytes=4096,
        ),
        step_plan=step_plan,
        request_id="evidence-request-1",
        attempt_id="evidence-attempt-1",
        route_id="evidence-route-1",
        backend=backend,
        artifacts=sdk.artifacts,
        routes=routes,
    )
    sdk.dispatch_batch(
        inquiry_id,
        (
            RecordStepPlan(
                event_id="evidence-step-plan-recorded-event",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                plan=step_plan,
            ),
            RequestEffect(
                event_id="evidence-requested-event",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                request=request,
            ),
            PlanEffectAttempt(
                event_id="evidence-planned-event",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                plan=plan,
            ),
        ),
    )

    def assert_started() -> None:
        persisted = sdk.inspect(inquiry_id).request_by_id(request.id)
        assert persisted is not None
        assert persisted.attempts[0].started is True
        assert persisted.attempts[0].outcome is None

    backend.on_execute = assert_started
    executor = PersistedEffectExecutor(
        events=sdk.events,
        artifacts=sdk.artifacts,
        routes=routes,
        clock=lambda: NOW,
    )
    adapter = EvidenceEffectAdapter(backend=backend, artifacts=sdk.artifacts)
    completed = adapter.execute_persisted(
        executor,
        inquiry_id=inquiry_id,
        request_id=request.id,
        attempt_id=plan.id,
    )

    assert backend.calls == 1
    assert backend.workspace is not None
    assert not backend.workspace.exists()
    assert live_source.read_text() == "unchanged"
    request_state = completed.request_by_id(request.id)
    assert request_state is not None
    outcome = request_state.attempts[0].outcome
    assert isinstance(outcome, ReturnedOutcome)
    raw_ref = outcome.external_return.raw_payload.artifact
    assert raw_ref is not None
    assert raw_ref.encoding == "binary"
    assert outcome.external_return.capture_boundary == "adapter-perform-exact-return-bytes"
    assert outcome.external_return.capture_encoding == "binary"
    assert outcome.external_return.captured_at == NOW
    raw = EvidenceRawResult.model_validate_json(
        sdk.artifacts.get_bytes(raw_ref),
        strict=True,
    )
    assert raw.status is EvidenceRunStatus.COMPLETED
    accepted = request_state.accepted_result
    assert accepted is not None
    assert accepted.semantic_artifact.encoding == "utf-8"
    assert request_state.request.input_artifact.encoding == "utf-8"
    assert request_state.attempts[0].plan.route.definition_artifact.encoding == "utf-8"
    summary = EvidenceResultSummary.model_validate_json(
        sdk.artifacts.get_bytes(accepted.semantic_artifact),
        strict=True,
    )
    assert summary.execution_status is EvidenceRunStatus.COMPLETED
    assert summary.stdout_size == len(b"result\x00bytes")
    assert summary.stderr_size == len(b"warning\xff")

    environment = json.loads(sdk.artifacts.get_bytes(plan.route.execution_environment_artifact))
    assert environment["capabilities"] == {
        "cap_drop": "ALL",
        "credentials": False,
        "docker_socket_in_container": False,
        "input_mount": "read-only-captured-workspace",
        "network": "none",
        "output_mount": False,
        "root_filesystem": "read-only",
        "source_mount": False,
    }
    assert all("secret" not in key.lower() for key in environment)
    assert sdk.replay(inquiry_id) == completed
    assert backend.calls == 1


def test_unsupported_evidence_backend_is_not_accepted_as_success(tmp_path: Path) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)
    inquiry_id = "evidence-unsupported"
    started = sdk.start(inquiry_id)
    step_plan = _evidence_step_plan(started)

    class _UnsupportedDocker(_FakeDockerBackend):
        def execute(
            self,
            request: EvidenceRunRequest,
            captured_workspace: Path,
        ) -> EvidenceRunResult:
            del request, captured_workspace
            self.on_execute()
            self.calls += 1
            return EvidenceRunResult(
                status=EvidenceRunStatus.UNSUPPORTED,
                diagnostic="Docker daemon is unavailable",
            )

    backend = _UnsupportedDocker()
    definition = docker_evidence_route_definition(backend, command="rci-checker")
    routes = RouteRegistry((definition,), artifacts=sdk.artifacts)
    request, plan = prepare_evidence_attempt(
        EvidenceRunRequest(argv=("rci-checker",), timeout_seconds=1),
        step_plan=step_plan,
        request_id="unsupported-request",
        attempt_id="unsupported-attempt",
        route_id="unsupported-route",
        backend=backend,
        artifacts=sdk.artifacts,
        routes=routes,
    )
    sdk.dispatch_batch(
        inquiry_id,
        (
            RecordStepPlan(
                event_id="unsupported-step-plan-recorded",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                plan=step_plan,
            ),
            RequestEffect(
                event_id="unsupported-requested",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                request=request,
            ),
            PlanEffectAttempt(
                event_id="unsupported-planned",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                plan=plan,
            ),
        ),
    )
    state = EvidenceEffectAdapter(
        backend=backend,
        artifacts=sdk.artifacts,
    ).execute_persisted(
        PersistedEffectExecutor(
            events=sdk.events,
            artifacts=sdk.artifacts,
            routes=routes,
            clock=lambda: NOW,
        ),
        inquiry_id=inquiry_id,
        request_id=request.id,
        attempt_id=plan.id,
    )
    request_state = state.request_by_id(request.id)
    assert request_state is not None
    assert request_state.accepted_result is None
    assert request_state.decode_outcomes[0].kind == "unsupported"
