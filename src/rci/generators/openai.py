"""Optional OpenAI Responses effect payloads and pure response decoding.

No public method in this module performs a live call from a semantic ``generate``
operation. Live transport is deliberately private and is invoked only by the persisted
effect executor after it has proved that the request and started attempt are committed.
The dependency and credentials are resolved lazily at that point.
"""

from __future__ import annotations

import json
from enum import StrEnum
from hashlib import sha256
from importlib import import_module
from typing import Annotated, Any, Literal
from urllib.parse import urlsplit

from pydantic import Field, StringConstraints, field_validator, model_validator

from rci.core.effects import EffectAttemptPlan, EffectRequest, RouteSnapshot
from rci.core.model import FrozenModel, Identifier, NonEmptyText
from rci.core.planning import PlanStatus, StepPlan
from rci.core.serialization import canonical_json_bytes, sha256_digest
from rci.core.state import InquiryState
from rci.generators.base import QuestionInvocation, SemanticPayload
from rci.orchestration.effects import (
    AdapterDecodeResult,
    AdapterDecodeStatus,
    EffectTransportError,
    EffectUnsupportedError,
    PersistedEffectExecutor,
    RouteDefinition,
    RouteRegistry,
)
from rci.persistence import ArtifactStore

OPENAI_ROUTE_DEFINITION_ID = "openai-responses"
OPENAI_ROUTE_DEFINITION_VERSION = "1.0.0"
OPENAI_ADAPTER_ID = "openai-responses"
OPENAI_ADAPTER_VERSION = "1.0.0"
OPENAI_BASE_URL = "https://api.openai.com/v1"

BoundedText = Annotated[str, StringConstraints(min_length=1, max_length=262_144)]


class UnpersistedEffectError(RuntimeError):
    """A caller attempted live generation outside the persisted-effect boundary."""


class OpenAIRequestEnvelope(FrozenModel):
    """Complete stateless provider input stored before execution is authorized."""

    invocation_id: NonEmptyText
    model: Identifier
    input: BoundedText
    max_output_tokens: int = Field(ge=1, le=16_384)
    tools: tuple[()] = ()
    store: Literal[False] = False


class OpenAIDecodeStatus(StrEnum):
    DECODED = "decoded"
    MALFORMED = "malformed"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


class OpenAIResponseSummary(FrozenModel):
    """Provisional interpretation; the exact provider body remains authoritative."""

    provider_request_id: str | None = None
    execution_status: NonEmptyText
    output_text: str
    usage: tuple[tuple[NonEmptyText, int], ...] = ()

    @field_validator("usage")
    @classmethod
    def validate_usage(
        cls,
        value: tuple[tuple[str, int], ...],
    ) -> tuple[tuple[str, int], ...]:
        if any(type(count) is not int or count < 0 for _, count in value):
            raise ValueError("usage counters must be nonnegative integers")
        names = [name for name, _ in value]
        if names != sorted(names) or len(names) != len(set(names)):
            raise ValueError("usage counters must be uniquely sorted")
        return value


class OpenAIDecodeResult(FrozenModel):
    status: OpenAIDecodeStatus
    summary: OpenAIResponseSummary | None = None
    diagnostic: NonEmptyText | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> OpenAIDecodeResult:
        if (self.status is OpenAIDecodeStatus.DECODED) != (self.summary is not None):
            raise ValueError("only a decoded result carries a response summary")
        if self.status is OpenAIDecodeStatus.DECODED and self.diagnostic is not None:
            raise ValueError("decoded results do not carry failure diagnostics")
        if self.status is not OpenAIDecodeStatus.DECODED and self.diagnostic is None:
            raise ValueError("non-decoded results require a diagnostic")
        return self


def compile_openai_request(
    invocation: QuestionInvocation,
    *,
    model: str,
) -> OpenAIRequestEnvelope:
    """Compile all local context into one inert, stateless provider envelope."""

    if not model:
        raise ValueError("an explicit OpenAI model is required")
    return OpenAIRequestEnvelope(
        invocation_id=invocation.invocation_id,
        model=model,
        input=invocation.prompt,
        max_output_tokens=invocation.max_output_tokens,
    )


def openai_route_definition(model: str) -> RouteDefinition:
    """Return the exact allowlist entry for one explicitly selected model."""

    request_model = OpenAIRequestEnvelope(
        invocation_id="route-definition-validation",
        model=model,
        input="route definition validation",
        max_output_tokens=1,
    )
    return RouteDefinition(
        definition_id=(
            f"{OPENAI_ROUTE_DEFINITION_ID}/{sha256(request_model.model.encode()).hexdigest()[:16]}"
        ),
        definition_version=OPENAI_ROUTE_DEFINITION_VERSION,
        backend_id=f"openai.responses/{request_model.model}",
        adapter_id=OPENAI_ADAPTER_ID,
        adapter_version=OPENAI_ADAPTER_VERSION,
        endpoint_or_channel=f"{OPENAI_BASE_URL}/responses",
        transport="https",
    )


def prepare_openai_attempt(
    invocation: QuestionInvocation,
    *,
    model: str,
    step_plan: StepPlan,
    request_id: str,
    attempt_id: str,
    route_id: str,
    client_library_version: str,
    artifacts: ArtifactStore,
    routes: RouteRegistry,
    timeout_seconds: int = 60,
) -> tuple[EffectRequest, EffectAttemptPlan]:
    """Publish a stateless request and its registry-resolved immutable route snapshot."""

    if not client_library_version:
        raise ValueError("the OpenAI client library version must be explicit")
    attempt_key = step_plan.selected_attempt_key
    if step_plan.status is not PlanStatus.READY or attempt_key is None:
        raise ValueError("an OpenAI effect requires a content-derived ready step plan")
    if step_plan.selected_obligation_id not in invocation.referent_ids:
        raise ValueError("the invocation must refer to the step plan's exact obligation")
    if (
        attempt_key.contract_id != invocation.contract_id
        or attempt_key.contract_version != invocation.contract_version
        or attempt_key.binding_revision != invocation.binding_revision
    ):
        raise ValueError("the invocation does not match the step plan's exact attempt key")
    envelope = compile_openai_request(invocation, model=model)
    input_ref = artifacts.put_bytes(
        canonical_json_bytes(envelope),
        media_type="application/vnd.rci.openai-request+json",
        encoding="utf-8",
    )
    request = EffectRequest(
        id=request_id,
        step_plan_id=step_plan.id,
        effect_kind="semantic.openai_response",
        adapter_id=OPENAI_ADAPTER_ID,
        input_artifact=input_ref,
        timeout_seconds=timeout_seconds,
    )
    definition = openai_route_definition(model)
    definition_ref = routes.definition_artifact(definition)
    environment_ref = artifacts.put_bytes(
        canonical_json_bytes(
            {
                "adapter_id": OPENAI_ADAPTER_ID,
                "adapter_version": OPENAI_ADAPTER_VERSION,
                "client_library": "openai-python",
                "client_library_version": client_library_version,
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
        request_or_action_digest=sha256_digest(canonical_json_bytes(request)),
    )
    routes.validate(request, route)
    return request, EffectAttemptPlan(id=attempt_id, request_id=request_id, route=route)


def decode_openai_response(raw_body: bytes) -> OpenAIDecodeResult:
    """Decode an exact captured Responses API body without granting warrant."""

    if type(raw_body) is not bytes:
        raise TypeError("OpenAI response decoding requires exact bytes")
    try:
        value = json.loads(raw_body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        return OpenAIDecodeResult(
            status=OpenAIDecodeStatus.MALFORMED,
            diagnostic=f"response body is not valid UTF-8 JSON: {type(error).__name__}",
        )
    if not isinstance(value, dict):
        return OpenAIDecodeResult(
            status=OpenAIDecodeStatus.UNSUPPORTED,
            diagnostic="response body is not a JSON object",
        )
    status = value.get("status")
    if not isinstance(status, str) or not status:
        return OpenAIDecodeResult(
            status=OpenAIDecodeStatus.UNSUPPORTED,
            diagnostic="response object lacks a typed execution status",
        )
    provider_id = value.get("id")
    if provider_id is not None and not isinstance(provider_id, str):
        return OpenAIDecodeResult(
            status=OpenAIDecodeStatus.MALFORMED,
            diagnostic="provider response id is not a string",
        )
    output = value.get("output", [])
    if not isinstance(output, list):
        return OpenAIDecodeResult(
            status=OpenAIDecodeStatus.MALFORMED,
            diagnostic="response output is not a list",
        )
    text_parts: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            return OpenAIDecodeResult(
                status=OpenAIDecodeStatus.MALFORMED,
                diagnostic="response output contains a non-object item",
            )
        content = item.get("content", [])
        if not isinstance(content, list):
            return OpenAIDecodeResult(
                status=OpenAIDecodeStatus.MALFORMED,
                diagnostic="response message content is not a list",
            )
        for part in content:
            if not isinstance(part, dict):
                return OpenAIDecodeResult(
                    status=OpenAIDecodeStatus.MALFORMED,
                    diagnostic="response message contains a non-object content item",
                )
            if part.get("type") == "output_text":
                text = part.get("text")
                if not isinstance(text, str):
                    return OpenAIDecodeResult(
                        status=OpenAIDecodeStatus.MALFORMED,
                        diagnostic="output_text content does not contain text",
                    )
                text_parts.append(text)

    usage_value = value.get("usage")
    usage: dict[str, int] = {}
    if usage_value is not None:
        if not isinstance(usage_value, dict):
            return OpenAIDecodeResult(
                status=OpenAIDecodeStatus.MALFORMED,
                diagnostic="response usage is not an object",
            )
        for name in ("input_tokens", "output_tokens", "total_tokens"):
            count = usage_value.get(name)
            if count is not None:
                if type(count) is not int or count < 0:
                    return OpenAIDecodeResult(
                        status=OpenAIDecodeStatus.MALFORMED,
                        diagnostic=f"usage field {name} is not a nonnegative integer",
                    )
                usage[name] = count

    return OpenAIDecodeResult(
        status=OpenAIDecodeStatus.DECODED,
        summary=OpenAIResponseSummary(
            provider_request_id=provider_id,
            execution_status=status,
            output_text="".join(text_parts),
            usage=tuple(sorted(usage.items())),
        ),
    )


class OpenAIResponsesGenerator:
    """Request compiler with an explicit guard against direct live generation.

    ``OpenAIResponsesGenerator`` remains as the familiar optional-adapter name, but its
    former direct network path is intentionally closed. The persisted effect executor
    owns live invocation through ``_perform_raw`` after ledger authorization.
    """

    def __init__(self, *, model: str, client: Any | None = None) -> None:
        self.model = openai_route_definition(model).backend_id.removeprefix("openai.responses/")
        self._client = client
        self.adapter_id = OPENAI_ADAPTER_ID
        self.adapter_version = OPENAI_ADAPTER_VERSION

    def generate(self, invocation: QuestionInvocation) -> SemanticPayload:
        del invocation
        raise UnpersistedEffectError(
            "live OpenAI generation requires a persisted EffectRequested and AttemptStarted"
        )

    def compile(self, invocation: QuestionInvocation) -> OpenAIRequestEnvelope:
        return compile_openai_request(invocation, model=self.model)

    def validate_input(self, input_bytes: bytes) -> None:
        request = OpenAIRequestEnvelope.model_validate_json(input_bytes, strict=True)
        if request.model != self.model:
            raise ValueError("persisted request model does not match the configured model")

    def preflight(self) -> None:
        self._resolve_client()

    def perform_exact(self, input_bytes: bytes, *, timeout_seconds: int) -> bytes:
        request = OpenAIRequestEnvelope.model_validate_json(input_bytes, strict=True)
        return self._perform_raw(request, timeout_seconds=timeout_seconds)

    def decode_exact(self, raw_bytes: bytes) -> AdapterDecodeResult:
        decoded = decode_openai_response(raw_bytes)
        if decoded.status is OpenAIDecodeStatus.DECODED:
            if decoded.summary is None:  # pragma: no cover - strict model invariant
                raise RuntimeError("decoded OpenAI response lost its provisional summary")
            return AdapterDecodeResult(
                status=AdapterDecodeStatus.DECODED,
                semantic_bytes=canonical_json_bytes(decoded.summary),
                semantic_media_type="application/vnd.rci.openai-response-summary+json",
                semantic_encoding="utf-8",
                operation_id="semantic.openai_response",
            )
        status = {
            OpenAIDecodeStatus.MALFORMED: AdapterDecodeStatus.MALFORMED,
            OpenAIDecodeStatus.UNSUPPORTED: AdapterDecodeStatus.UNSUPPORTED,
            OpenAIDecodeStatus.FAILED: AdapterDecodeStatus.FAILED,
        }[decoded.status]
        if decoded.diagnostic is None:  # pragma: no cover - strict model invariant
            raise RuntimeError("failed OpenAI decode lost its diagnostic")
        return AdapterDecodeResult(status=status, diagnostic=decoded.diagnostic)

    def execute_persisted(
        self,
        executor: PersistedEffectExecutor,
        *,
        inquiry_id: str,
        request_id: str,
        attempt_id: str,
    ) -> InquiryState:
        """Invoke the live adapter only through the committed-attempt coordinator."""

        return executor.execute(
            inquiry_id=inquiry_id,
            request_id=request_id,
            attempt_id=attempt_id,
            adapter=self,
        )

    def _perform_raw(
        self,
        request: OpenAIRequestEnvelope,
        *,
        timeout_seconds: int,
    ) -> bytes:
        """Perform the private raw transport after the executor's persisted guard."""

        if request.model != self.model:
            raise ValueError("persisted request model does not match the configured model")
        client = self._resolve_client()
        try:
            response = client.responses.with_raw_response.create(
                model=request.model,
                input=request.input,
                tools=[],
                max_output_tokens=request.max_output_tokens,
                store=False,
                timeout=float(timeout_seconds),
            )
        except TimeoutError:
            raise
        except Exception as error:
            if "timeout" in type(error).__name__.lower():
                raise TimeoutError("OpenAI response presentation timed out") from error
            raise EffectTransportError("OpenAI response transport is uncertain") from error
        content = response.content
        if type(content) is not bytes:
            raise TypeError("OpenAI raw response boundary did not provide exact bytes")
        return content

    @staticmethod
    def _validate_client_endpoint(client: Any) -> None:
        base_url = getattr(client, "base_url", None)
        if base_url is None:
            raise EffectUnsupportedError("OpenAI client does not expose its resolved base URL")
        parsed = urlsplit(str(base_url))
        has_userinfo = parsed.username is not None or parsed.password is not None
        endpoint_matches = (
            parsed.scheme == "https"
            and parsed.netloc == "api.openai.com"
            and parsed.path.rstrip("/") == "/v1"
            and not parsed.query
            and not parsed.fragment
            and not has_userinfo
        )
        if not endpoint_matches:
            raise EffectUnsupportedError(
                "resolved OpenAI base URL does not match the pinned sanitized endpoint"
            )

    def _resolve_client(self) -> Any:
        client = self._client
        if client is None:
            try:
                openai_module = import_module("openai")
            except ModuleNotFoundError as error:  # pragma: no cover - optional extra
                raise EffectUnsupportedError(
                    "install the 'openai' extra to use this adapter"
                ) from error
            try:
                client = openai_module.OpenAI()
            except Exception as error:
                raise EffectUnsupportedError(
                    "OpenAI client configuration is unavailable"
                ) from error
            self._client = client
        self._validate_client_endpoint(client)
        return client
