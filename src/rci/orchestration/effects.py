"""Persisted external-effect execution and versioned route validation.

This module is the only G1 orchestration boundary that invokes an external adapter. It
commits ``StartEffectAttempt`` before invocation, captures exact returned bytes into CAS
before recording or decoding them, and can resume decoding after a crash without
repeating an already captured return. Replay never imports or calls this executor.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from typing import Protocol

from pydantic import model_validator

from rci.core.commands import (
    AcceptEffectResult,
    DomainCommand,
    RecordAttemptOutcome,
    RecordDecodeOutcome,
    RecordNoAttemptDisposition,
    StartEffectAttempt,
)
from rci.core.effects import (
    AttemptState,
    CaptureFailedOutcome,
    CaptureFailureReason,
    Decoded,
    DecodeOutcome,
    EffectRequest,
    EffectRequestState,
    ExternalReturn,
    FailedDecode,
    MalformedDecode,
    NoAttemptDisposition,
    NoAttemptReason,
    NotPresentedOutcome,
    NotPresentedReason,
    PresentationUnknownOutcome,
    PresentationUnknownReason,
    ReturnedOutcome,
    RouteSnapshot,
    SuccessResult,
    UnsupportedDecode,
)
from rci.core.events import DomainEvent
from rci.core.model import ArtifactRef, CapturedPayload, FrozenModel, Identifier, NonEmptyText
from rci.core.serialization import canonical_json_bytes, sha256_digest
from rci.core.state import InquiryState
from rci.core.transitions import decide, evolve
from rci.persistence import ArtifactStore, OptimisticConcurrencyError, SQLiteEventStore

Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _stable_id(prefix: str, *parts: str) -> str:
    digest = sha256("\x00".join(parts).encode()).hexdigest()[:32]
    return f"{prefix}_{digest}"


class UnknownRouteDefinitionError(RuntimeError):
    """A route snapshot does not resolve to an allowlisted definition/version."""


class RouteValidationError(RuntimeError):
    """A snapshot does not faithfully instantiate its registered definition."""


class EffectUnsupportedError(RuntimeError):
    """The adapter cannot present this persisted request in this environment."""


class EffectTransportError(RuntimeError):
    """The adapter encountered transport uncertainty after an attempt started."""


class RouteTransformDefinition(FrozenModel):
    id: Identifier
    version: NonEmptyText


class RouteDefinition(FrozenModel):
    """Allowlisted executable behavior, distinct from one attempt's snapshot."""

    definition_id: Identifier
    definition_version: NonEmptyText
    backend_id: Identifier
    adapter_id: Identifier
    adapter_version: NonEmptyText
    endpoint_or_channel: NonEmptyText | None = None
    transport: NonEmptyText
    transforms: tuple[RouteTransformDefinition, ...] = ()

    @model_validator(mode="after")
    def validate_transforms(self) -> RouteDefinition:
        keys = [(item.id, item.version) for item in self.transforms]
        if len(keys) != len(set(keys)):
            raise ValueError("route transform definitions must be uniquely ordered")
        return self


class RouteRegistry:
    """Closed versioned registry that validates resolved attempt snapshots."""

    def __init__(
        self,
        definitions: Iterable[RouteDefinition],
        *,
        artifacts: ArtifactStore,
    ) -> None:
        self._artifacts = artifacts
        self._definitions: dict[tuple[str, str], RouteDefinition] = {}
        for definition in definitions:
            key = (definition.definition_id, definition.definition_version)
            if key in self._definitions:
                raise ValueError(f"duplicate route definition: {key[0]}@{key[1]}")
            self._definitions[key] = definition
        if not self._definitions:
            raise ValueError("a route registry cannot be empty")

    def definition_artifact(self, definition: RouteDefinition) -> ArtifactRef:
        """Publish the immutable definition bytes used by a future route snapshot."""

        return self._artifacts.put_bytes(
            canonical_json_bytes(definition),
            media_type="application/vnd.rci.route-definition+json",
            encoding="utf-8",
        )

    def validate(self, request: EffectRequest, snapshot: RouteSnapshot) -> RouteDefinition:
        key = (snapshot.definition_id, snapshot.definition_version)
        definition = self._definitions.get(key)
        if definition is None:
            raise UnknownRouteDefinitionError(
                f"route definition is not allowlisted: {key[0]}@{key[1]}"
            )
        expected_definition = canonical_json_bytes(definition)
        actual_definition = self._artifacts.get_bytes(snapshot.definition_artifact)
        if actual_definition != expected_definition:
            raise RouteValidationError("route definition artifact does not match the registry")
        exact_fields = (
            (snapshot.backend_id, definition.backend_id, "backend"),
            (snapshot.adapter_id, definition.adapter_id, "adapter"),
            (snapshot.adapter_version, definition.adapter_version, "adapter version"),
            (snapshot.endpoint_or_channel, definition.endpoint_or_channel, "endpoint/channel"),
            (snapshot.transport, definition.transport, "transport"),
        )
        mismatch = next(
            (label for actual, expected, label in exact_fields if actual != expected),
            None,
        )
        if mismatch is not None:
            raise RouteValidationError(f"route snapshot {mismatch} is not allowlisted")
        request_digest = sha256_digest(canonical_json_bytes(request))
        if snapshot.request_or_action_digest != request_digest:
            raise RouteValidationError("route snapshot does not pin the exact request digest")
        self._artifacts.verify(snapshot.execution_environment_artifact)
        actual_transforms = tuple((item.id, item.version) for item in snapshot.transform_evidence)
        expected_transforms = tuple((item.id, item.version) for item in definition.transforms)
        if actual_transforms != expected_transforms:
            raise RouteValidationError("route transform order/version differs from its definition")
        return definition


class AdapterDecodeStatus(StrEnum):
    DECODED = "decoded"
    MALFORMED = "malformed"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


class AdapterDecodeResult(FrozenModel):
    status: AdapterDecodeStatus
    semantic_bytes: bytes | None = None
    semantic_media_type: NonEmptyText | None = None
    semantic_encoding: NonEmptyText | None = None
    operation_id: Identifier | None = None
    diagnostic: NonEmptyText | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> AdapterDecodeResult:
        semantic_fields = (
            self.semantic_bytes,
            self.semantic_media_type,
            self.semantic_encoding,
            self.operation_id,
        )
        if self.status is AdapterDecodeStatus.DECODED:
            if any(item is None for item in semantic_fields) or self.diagnostic is not None:
                raise ValueError("decoded adapter results require only complete semantic fields")
        elif any(item is not None for item in semantic_fields) or self.diagnostic is None:
            raise ValueError("non-decoded adapter results require only a diagnostic")
        return self


class PersistedEffectAdapter(Protocol):
    adapter_id: str
    adapter_version: str

    def validate_input(self, input_bytes: bytes) -> None: ...

    def preflight(self) -> None: ...

    def perform_exact(self, input_bytes: bytes, *, timeout_seconds: int) -> bytes: ...

    def decode_exact(self, raw_bytes: bytes) -> AdapterDecodeResult: ...


class PersistedEffectExecutor:
    """Coordinate one adapter with the authoritative ledger and CAS."""

    def __init__(
        self,
        *,
        events: SQLiteEventStore,
        artifacts: ArtifactStore,
        routes: RouteRegistry,
        clock: Clock = _utc_now,
    ) -> None:
        self.events = events
        self.artifacts = artifacts
        self.routes = routes
        self.clock = clock

    def _append(self, inquiry_id: str, commands: tuple[DomainCommand, ...]) -> InquiryState:
        """Append an idempotent command batch, retrying only optimistic fold races."""

        for _ in range(3):
            state = self.events.rebuild_state(inquiry_id)
            expected_sequence = state.sequence
            pending: list[DomainEvent] = []
            for command in commands:
                command_events = decide(state, command)
                pending.extend(command_events)
                for event in command_events:
                    state = evolve(state, event)
            if not pending:
                return state
            try:
                self.events.append(inquiry_id, expected_sequence, pending)
            except OptimisticConcurrencyError:
                continue
            return state
        raise OptimisticConcurrencyError("effect append lost three optimistic races")

    @staticmethod
    def _locate_attempt(
        state: InquiryState,
        request_id: str,
        attempt_id: str,
    ) -> tuple[EffectRequestState, AttemptState]:
        request_state = state.request_by_id(request_id)
        if request_state is None:
            raise ValueError("effect execution requires a persisted request")
        attempt = next(
            (item for item in request_state.attempts if item.plan.id == attempt_id),
            None,
        )
        if attempt is None:
            raise ValueError("effect execution requires a persisted attempt plan")
        return request_state, attempt

    def execute(
        self,
        *,
        inquiry_id: str,
        request_id: str,
        attempt_id: str,
        adapter: PersistedEffectAdapter,
        accept_decoded: bool = True,
    ) -> InquiryState:
        """Execute or resume one planned attempt without ever consulting replay hooks."""

        state = self.events.rebuild_state(inquiry_id)
        request_state, attempt = self._locate_attempt(state, request_id, attempt_id)
        if request_state.request.adapter_id != adapter.adapter_id:
            raise RouteValidationError("request adapter does not match the selected adapter")
        if attempt.plan.route.adapter_id != adapter.adapter_id:
            raise RouteValidationError("route adapter does not match the selected adapter")
        if attempt.plan.route.adapter_version != adapter.adapter_version:
            raise RouteValidationError("route adapter version does not match the selected adapter")
        self.routes.validate(request_state.request, attempt.plan.route)
        if request_state.request.input_artifact.size > 4_194_304:
            raise RouteValidationError("effect request envelope exceeds the 4 MiB G1 bound")
        input_bytes = self.artifacts.get_bytes(request_state.request.input_artifact)
        adapter.validate_input(input_bytes)

        if request_state.accepted_decoded_outcome_id is not None:
            return state
        if attempt.outcome is not None and not isinstance(attempt.outcome, ReturnedOutcome):
            return state
        if not attempt.started:
            try:
                adapter.preflight()
            except EffectUnsupportedError as error:
                diagnostic_ref = self.artifacts.put_bytes(
                    canonical_json_bytes(
                        {
                            "phase": "preflight",
                            "exception_type": type(error).__name__,
                        }
                    ),
                    media_type="application/vnd.rci.effect-diagnostic+json",
                    encoding="utf-8",
                )
                return self._append(
                    inquiry_id,
                    (
                        RecordNoAttemptDisposition(
                            event_id=_stable_id("evt", attempt_id, "no-attempt"),
                            inquiry_id=inquiry_id,
                            occurred_at=self.clock(),
                            disposition=NoAttemptDisposition(
                                id=_stable_id("disposition", attempt_id, "unsupported"),
                                request_id=request_id,
                                step_plan_id=request_state.request.step_plan_id,
                                reason_kind=NoAttemptReason.UNSUPPORTED,
                                diagnostics=diagnostic_ref,
                            ),
                        ),
                    ),
                )
            started_at = self.clock()
            state = self._append(
                inquiry_id,
                (
                    StartEffectAttempt(
                        event_id=_stable_id("evt", attempt_id, "started"),
                        inquiry_id=inquiry_id,
                        occurred_at=started_at,
                        attempt_id=attempt_id,
                    ),
                ),
            )
            request_state, attempt = self._locate_attempt(state, request_id, attempt_id)
        if not attempt.started:
            raise RuntimeError("attempt start was not durably folded before execution")

        if attempt.outcome is None:
            try:
                raw_bytes = adapter.perform_exact(
                    input_bytes,
                    timeout_seconds=request_state.request.timeout_seconds,
                )
            except EffectUnsupportedError as error:
                diagnostic_bytes = canonical_json_bytes(
                    {
                        "phase": "preflight",
                        "exception_type": type(error).__name__,
                    }
                )
                diagnostic_ref = self.artifacts.put_bytes(
                    diagnostic_bytes,
                    media_type="application/vnd.rci.effect-diagnostic+json",
                    encoding="utf-8",
                )
                return self._append(
                    inquiry_id,
                    (
                        RecordAttemptOutcome(
                            event_id=_stable_id("evt", attempt_id, "not-presented"),
                            inquiry_id=inquiry_id,
                            occurred_at=self.clock(),
                            request_id=request_id,
                            outcome=NotPresentedOutcome(
                                attempt_id=attempt_id,
                                route_id=attempt.plan.route.id,
                                reason_kind=NotPresentedReason.UNSUPPORTED,
                                diagnostics=diagnostic_ref,
                            ),
                        ),
                    ),
                )
            except Exception as error:
                reason_kind = PresentationUnknownReason.INTERNAL_FAILURE
                if isinstance(error, TimeoutError):
                    reason_kind = PresentationUnknownReason.TIMEOUT
                elif isinstance(error, EffectTransportError):
                    reason_kind = PresentationUnknownReason.TRANSPORT_ERROR
                diagnostic_ref = self.artifacts.put_bytes(
                    canonical_json_bytes(
                        {
                            "phase": "presentation_or_transport",
                            "exception_type": type(error).__name__,
                        }
                    ),
                    media_type="application/vnd.rci.effect-diagnostic+json",
                    encoding="utf-8",
                )
                return self._append(
                    inquiry_id,
                    (
                        RecordAttemptOutcome(
                            event_id=_stable_id("evt", attempt_id, "presentation-unknown"),
                            inquiry_id=inquiry_id,
                            occurred_at=self.clock(),
                            request_id=request_id,
                            outcome=PresentationUnknownOutcome(
                                attempt_id=attempt_id,
                                route_id=attempt.plan.route.id,
                                reason_kind=reason_kind,
                                diagnostics=diagnostic_ref,
                            ),
                        ),
                    ),
                )
            if type(raw_bytes) is not bytes:
                diagnostic_ref = self.artifacts.put_bytes(
                    canonical_json_bytes(
                        {
                            "phase": "capture",
                            "reason": "adapter_return_was_not_exact_bytes",
                        }
                    ),
                    media_type="application/vnd.rci.effect-diagnostic+json",
                    encoding="utf-8",
                )
                return self._append(
                    inquiry_id,
                    (
                        RecordAttemptOutcome(
                            event_id=_stable_id("evt", attempt_id, "capture-failed"),
                            inquiry_id=inquiry_id,
                            occurred_at=self.clock(),
                            request_id=request_id,
                            outcome=CaptureFailedOutcome(
                                attempt_id=attempt_id,
                                route_id=attempt.plan.route.id,
                                reason_kind=CaptureFailureReason.CAPTURE_ERROR,
                                diagnostics=diagnostic_ref,
                            ),
                        ),
                    ),
                )
            raw_ref = self.artifacts.put_bytes(
                raw_bytes,
                media_type="application/octet-stream",
                encoding="binary",
            )
            captured_at = self.clock()
            external_return = ExternalReturn(
                id=_stable_id("return", attempt_id, raw_ref.digest),
                attempt_id=attempt_id,
                route_id=attempt.plan.route.id,
                capture_boundary="adapter-perform-exact-return-bytes",
                capture_encoding="binary",
                captured_at=captured_at,
                raw_payload=CapturedPayload(kind="bytes", artifact=raw_ref),
            )
            state = self._append(
                inquiry_id,
                (
                    RecordAttemptOutcome(
                        event_id=_stable_id("evt", external_return.id, "captured"),
                        inquiry_id=inquiry_id,
                        occurred_at=captured_at,
                        request_id=request_id,
                        outcome=ReturnedOutcome(
                            attempt_id=attempt_id,
                            route_id=attempt.plan.route.id,
                            external_return=external_return,
                        ),
                    ),
                ),
            )
            request_state, attempt = self._locate_attempt(state, request_id, attempt_id)

        if not isinstance(attempt.outcome, ReturnedOutcome):
            return state
        external_return = attempt.outcome.external_return
        raw_artifact = external_return.raw_payload.artifact
        if raw_artifact is None:
            raise RuntimeError("byte-return outcome lacks its authoritative artifact")
        raw_bytes = self.artifacts.get_bytes(raw_artifact)
        existing_decode = next(
            (
                item
                for item in request_state.decode_outcomes
                if item.external_return_id == external_return.id
            ),
            None,
        )
        if existing_decode is None:
            decoded = adapter.decode_exact(raw_bytes)
            decode_id = _stable_id("decode", external_return.id, adapter.adapter_version)
            decode_outcome: DecodeOutcome
            if decoded.status is AdapterDecodeStatus.DECODED:
                if (
                    decoded.semantic_bytes is None
                    or decoded.semantic_media_type is None
                    or decoded.semantic_encoding is None
                ):
                    raise RuntimeError(
                        "decoded adapter result lost semantic bytes, media type, or encoding"
                    )
                if decoded.operation_id is None:
                    raise RuntimeError("decoded adapter result lost its operation identity")
                semantic_ref = self.artifacts.put_bytes(
                    decoded.semantic_bytes,
                    media_type=decoded.semantic_media_type,
                    encoding=decoded.semantic_encoding,
                )
                decode_outcome = Decoded(
                    id=decode_id,
                    external_return_id=external_return.id,
                    decoder_id=f"{adapter.adapter_id}-decoder",
                    decoder_version=adapter.adapter_version,
                    result=SuccessResult(
                        id=_stable_id("result", decode_id),
                        semantic_artifact=semantic_ref,
                        operation_id=decoded.operation_id,
                    ),
                )
            else:
                if decoded.diagnostic is None:
                    raise RuntimeError("failed adapter decode lost its diagnostic")
                if decoded.status is AdapterDecodeStatus.UNSUPPORTED:
                    decode_outcome = UnsupportedDecode(
                        id=decode_id,
                        external_return_id=external_return.id,
                        decoder_id=f"{adapter.adapter_id}-decoder",
                        decoder_version=adapter.adapter_version,
                        reason=decoded.diagnostic,
                    )
                else:
                    diagnostics_ref = self.artifacts.put_bytes(
                        canonical_json_bytes(
                            {
                                "diagnostic": decoded.diagnostic,
                                "status": decoded.status.value,
                            }
                        ),
                        media_type="application/vnd.rci.decode-diagnostic+json",
                        encoding="utf-8",
                    )
                    decode_class = (
                        MalformedDecode
                        if decoded.status is AdapterDecodeStatus.MALFORMED
                        else FailedDecode
                    )
                    decode_outcome = decode_class(
                        id=decode_id,
                        external_return_id=external_return.id,
                        decoder_id=f"{adapter.adapter_id}-decoder",
                        decoder_version=adapter.adapter_version,
                        diagnostics=diagnostics_ref,
                    )
            state = self._append(
                inquiry_id,
                (
                    RecordDecodeOutcome(
                        event_id=_stable_id("evt", decode_id, "decoded"),
                        inquiry_id=inquiry_id,
                        occurred_at=self.clock(),
                        request_id=request_id,
                        outcome=decode_outcome,
                    ),
                ),
            )
            request_state, _ = self._locate_attempt(state, request_id, attempt_id)
            existing_decode = next(
                item for item in request_state.decode_outcomes if item.id == decode_id
            )

        if accept_decoded and isinstance(existing_decode, Decoded):
            state = self._append(
                inquiry_id,
                (
                    AcceptEffectResult(
                        event_id=_stable_id("evt", existing_decode.id, "accepted"),
                        inquiry_id=inquiry_id,
                        occurred_at=self.clock(),
                        request_id=request_id,
                        decoded_outcome_id=existing_decode.id,
                    ),
                ),
            )
        return state
