"""Persisted adapter binding for capability-bounded evidence execution."""

from __future__ import annotations

import base64
from hashlib import sha256
from typing import Annotated

from pydantic import Field, field_validator, model_validator

from rci.core.effects import EffectAttemptPlan, EffectRequest, RouteSnapshot
from rci.core.model import ArtifactRef, FrozenModel, NonEmptyText
from rci.core.planning import PlanStatus, StepPlan
from rci.core.serialization import canonical_json_bytes, sha256_digest
from rci.core.state import InquiryState
from rci.evaluation.runner import (
    CapturedInput,
    DockerEvidenceBackend,
    EvidenceRunner,
    EvidenceRunRequest,
    EvidenceRunResult,
    EvidenceRunStatus,
)
from rci.orchestration.effects import (
    AdapterDecodeResult,
    AdapterDecodeStatus,
    PersistedEffectExecutor,
    RouteDefinition,
    RouteRegistry,
)
from rci.persistence import ArtifactStore

EVIDENCE_ADAPTER_ID = "docker-evidence"
EVIDENCE_ADAPTER_VERSION = "1.0.0"


class EvidenceArtifactInput(FrozenModel):
    relative_path: NonEmptyText
    artifact: ArtifactRef

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        return CapturedInput(relative_path=value, content=b"").relative_path


class EvidenceEffectEnvelope(FrozenModel):
    argv: Annotated[tuple[NonEmptyText, ...], Field(min_length=1, max_length=128)]
    inputs: Annotated[tuple[EvidenceArtifactInput, ...], Field(max_length=256)] = ()
    max_output_bytes: int = Field(default=1_048_576, ge=1, le=16_777_216)

    @model_validator(mode="after")
    def validate_envelope(self) -> EvidenceEffectEnvelope:
        EvidenceRunRequest(
            argv=self.argv,
            max_output_bytes=self.max_output_bytes,
            timeout_seconds=1,
        )
        paths = [item.relative_path for item in self.inputs]
        if len(paths) != len(set(paths)):
            raise ValueError("evidence artifact input paths must be unique")
        return self


class EvidenceRawResult(FrozenModel):
    status: EvidenceRunStatus
    exit_code: int | None = None
    stdout_base64: str
    stderr_base64: str
    diagnostic: str | None = None


class EvidenceResultSummary(FrozenModel):
    """Bounded interpretation that never becomes its own warrant."""

    execution_status: EvidenceRunStatus
    exit_code: int | None = None
    stdout_digest: str
    stdout_size: int = Field(ge=0)
    stderr_digest: str
    stderr_size: int = Field(ge=0)
    diagnostic: str | None = None


def docker_evidence_route_definition(
    backend: DockerEvidenceBackend,
    *,
    command: str,
) -> RouteDefinition:
    if command not in backend.allowed_commands:
        raise ValueError("evidence command is not allowlisted by the Docker backend")
    backend._validate_executable(command)
    _, digest = backend.image.rsplit("@sha256:", 1)
    command_digest = sha256(command.encode()).hexdigest()[:16]
    return RouteDefinition(
        definition_id=f"docker-evidence/{digest[:16]}/{command_digest}",
        definition_version="1.0.0",
        backend_id=f"docker-image/{digest}",
        adapter_id=EVIDENCE_ADAPTER_ID,
        adapter_version=EVIDENCE_ADAPTER_VERSION,
        endpoint_or_channel="local-docker-daemon",
        transport="docker-container",
    )


def prepare_evidence_attempt(
    request: EvidenceRunRequest,
    *,
    step_plan: StepPlan,
    request_id: str,
    attempt_id: str,
    route_id: str,
    backend: DockerEvidenceBackend,
    artifacts: ArtifactStore,
    routes: RouteRegistry,
) -> tuple[EffectRequest, EffectAttemptPlan]:
    """Capture all evidence inputs and publish a non-mutable execution plan."""

    if step_plan.status is not PlanStatus.READY or step_plan.selected_attempt_key is None:
        raise ValueError("an evidence effect requires a content-derived ready step plan")
    definition = docker_evidence_route_definition(backend, command=request.argv[0])
    captured_inputs = tuple(
        EvidenceArtifactInput(
            relative_path=item.relative_path,
            artifact=artifacts.put_bytes(
                item.content,
                media_type="application/octet-stream",
                encoding="binary",
            ),
        )
        for item in request.inputs
    )
    envelope = EvidenceEffectEnvelope(
        argv=request.argv,
        inputs=captured_inputs,
        max_output_bytes=request.max_output_bytes,
    )
    input_ref = artifacts.put_bytes(
        canonical_json_bytes(envelope),
        media_type="application/vnd.rci.evidence-request+json",
        encoding="utf-8",
    )
    effect_request = EffectRequest(
        id=request_id,
        step_plan_id=step_plan.id,
        effect_kind="evaluation.bounded_evidence",
        adapter_id=EVIDENCE_ADAPTER_ID,
        input_artifact=input_ref,
        timeout_seconds=request.timeout_seconds,
    )
    definition_ref = routes.definition_artifact(definition)
    environment_ref = artifacts.put_bytes(
        canonical_json_bytes(
            {
                "capabilities": {
                    "cap_drop": "ALL",
                    "credentials": False,
                    "docker_socket_in_container": False,
                    "input_mount": "read-only-captured-workspace",
                    "network": "none",
                    "output_mount": False,
                    "root_filesystem": "read-only",
                    "source_mount": False,
                },
                "image": backend.image,
                "resource_bounds": {
                    "cpus": backend.cpu_limit,
                    "memory": backend.memory_limit,
                    "pids": backend.pids_limit,
                },
            }
        ),
        media_type="application/vnd.rci.execution-environment+json",
        encoding="utf-8",
    )
    route = RouteSnapshot(
        id=route_id,
        definition_id=definition.definition_id,
        definition_version=definition.definition_version,
        definition_artifact=definition_ref,
        backend_id=definition.backend_id,
        adapter_id=definition.adapter_id,
        adapter_version=definition.adapter_version,
        endpoint_or_channel=definition.endpoint_or_channel,
        transport=definition.transport,
        execution_environment_artifact=environment_ref,
        request_or_action_digest=sha256_digest(canonical_json_bytes(effect_request)),
    )
    routes.validate(effect_request, route)
    return effect_request, EffectAttemptPlan(
        id=attempt_id,
        request_id=request_id,
        route=route,
    )


class EvidenceEffectAdapter:
    """Make the Docker evidence backend reachable through persisted execution only."""

    adapter_id = EVIDENCE_ADAPTER_ID
    adapter_version = EVIDENCE_ADAPTER_VERSION

    def __init__(self, *, backend: DockerEvidenceBackend, artifacts: ArtifactStore) -> None:
        self.backend = backend
        self.artifacts = artifacts
        self._runner = EvidenceRunner(backend)

    def _request(self, input_bytes: bytes, *, timeout_seconds: int) -> EvidenceRunRequest:
        envelope = EvidenceEffectEnvelope.model_validate_json(input_bytes, strict=True)
        if any(item.artifact.size > 4_194_304 for item in envelope.inputs):
            raise ValueError("an evidence artifact exceeds the per-input 4 MiB budget")
        if sum(item.artifact.size for item in envelope.inputs) > 16_777_216:
            raise ValueError("evidence artifacts exceed the aggregate 16 MiB budget")
        inputs = tuple(
            CapturedInput(
                relative_path=item.relative_path,
                content=self.artifacts.get_bytes(item.artifact),
            )
            for item in envelope.inputs
        )
        return EvidenceRunRequest(
            argv=envelope.argv,
            inputs=inputs,
            timeout_seconds=timeout_seconds,
            max_output_bytes=envelope.max_output_bytes,
        )

    def validate_input(self, input_bytes: bytes) -> None:
        self._request(input_bytes, timeout_seconds=1)

    def preflight(self) -> None:
        """Docker availability is checked only after the attempt start is durable."""

    @staticmethod
    def _raw_result(result: EvidenceRunResult) -> bytes:
        return canonical_json_bytes(
            EvidenceRawResult(
                status=result.status,
                exit_code=result.exit_code,
                stdout_base64=base64.b64encode(result.stdout).decode("ascii"),
                stderr_base64=base64.b64encode(result.stderr).decode("ascii"),
                diagnostic=result.diagnostic,
            )
        )

    def perform_exact(self, input_bytes: bytes, *, timeout_seconds: int) -> bytes:
        request = self._request(input_bytes, timeout_seconds=timeout_seconds)
        return self._raw_result(self._runner.run(request))

    def decode_exact(self, raw_bytes: bytes) -> AdapterDecodeResult:
        try:
            raw = EvidenceRawResult.model_validate_json(raw_bytes, strict=True)
            stdout = base64.b64decode(raw.stdout_base64, validate=True)
            stderr = base64.b64decode(raw.stderr_base64, validate=True)
        except Exception as error:
            return AdapterDecodeResult(
                status=AdapterDecodeStatus.MALFORMED,
                diagnostic=f"malformed evidence return: {type(error).__name__}",
            )
        if raw.status is EvidenceRunStatus.UNSUPPORTED:
            return AdapterDecodeResult(
                status=AdapterDecodeStatus.UNSUPPORTED,
                diagnostic=raw.diagnostic or "evidence runner is unsupported",
            )
        if raw.status is EvidenceRunStatus.FAILED:
            return AdapterDecodeResult(
                status=AdapterDecodeStatus.FAILED,
                diagnostic=raw.diagnostic or "evidence runner failed",
            )
        summary = EvidenceResultSummary(
            execution_status=raw.status,
            exit_code=raw.exit_code,
            stdout_digest=sha256_digest(stdout),
            stdout_size=len(stdout),
            stderr_digest=sha256_digest(stderr),
            stderr_size=len(stderr),
            diagnostic=raw.diagnostic,
        )
        return AdapterDecodeResult(
            status=AdapterDecodeStatus.DECODED,
            semantic_bytes=canonical_json_bytes(summary),
            semantic_media_type="application/vnd.rci.evidence-summary+json",
            semantic_encoding="utf-8",
            operation_id="evaluation.evidence_result",
        )

    def execute_persisted(
        self,
        executor: PersistedEffectExecutor,
        *,
        inquiry_id: str,
        request_id: str,
        attempt_id: str,
    ) -> InquiryState:
        return executor.execute(
            inquiry_id=inquiry_id,
            request_id=request_id,
            attempt_id=attempt_id,
            adapter=self,
        )
