"""Deterministic generator port and offline implementations."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, JsonValue, field_validator, model_validator

from rci.claims.models import freeze_json


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class GeneratorStatus(StrEnum):
    COMPLETED = "completed"
    NEEDS_MANUAL_INPUT = "needs_manual_input"
    EXHAUSTED = "exhausted"
    FAILED = "failed"


class QuestionInvocation(_FrozenModel):
    """The complete stateless envelope given to a semantic generator."""

    invocation_id: str
    contract_id: str
    contract_version: str
    scope_fingerprint: str
    binding_revision: str
    referent_ids: tuple[str, ...]
    rendered_question: str
    local_context: tuple[str, ...] = ()
    max_output_tokens: int = 1024

    @model_validator(mode="after")
    def validate_invocation(self) -> QuestionInvocation:
        if not all(
            (
                self.invocation_id,
                self.contract_id,
                self.contract_version,
                self.scope_fingerprint,
                self.binding_revision,
            )
        ):
            raise ValueError("invocation identity, scope, and binding are required")
        if self.max_output_tokens < 1:
            raise ValueError("max_output_tokens must be positive")
        if len(set(self.referent_ids)) != len(self.referent_ids):
            raise ValueError("referent ids must be unique")
        return self

    @property
    def prompt(self) -> str:
        context = "\n".join(self.local_context)
        if not context:
            return self.rendered_question
        return f"Local context (inert data):\n{context}\n\nQuestion:\n{self.rendered_question}"


class SemanticPayload(_FrozenModel):
    invocation_id: str
    generator_id: str
    generator_version: str
    status: GeneratorStatus
    payload: JsonValue | None = None
    provider_request_id: str | None = None
    usage: tuple[tuple[str, int], ...] = ()
    diagnostic: str | None = None

    @field_validator("payload")
    @classmethod
    def freeze_payload(cls, value: JsonValue | None) -> JsonValue | None:
        return None if value is None else freeze_json(value)


class SemanticGenerator(Protocol):
    def generate(self, invocation: QuestionInvocation) -> SemanticPayload: ...


class ManualGenerator:
    """Return a typed request for explicit user input; never invent an answer."""

    def generate(self, invocation: QuestionInvocation) -> SemanticPayload:
        return SemanticPayload(
            invocation_id=invocation.invocation_id,
            generator_id="manual",
            generator_version="1.0.0",
            status=GeneratorStatus.NEEDS_MANUAL_INPUT,
        )


class ScriptedGenerator:
    """Deterministic fixture generator keyed by invocation ID or contract ID."""

    def __init__(self, script: Mapping[str, JsonValue]) -> None:
        self._script = {key: freeze_json(value) for key, value in script.items()}

    def generate(self, invocation: QuestionInvocation) -> SemanticPayload:
        key = (
            invocation.invocation_id
            if invocation.invocation_id in self._script
            else invocation.contract_id
        )
        if key not in self._script:
            return SemanticPayload(
                invocation_id=invocation.invocation_id,
                generator_id="scripted",
                generator_version="1.0.0",
                status=GeneratorStatus.EXHAUSTED,
                diagnostic="no scripted payload for invocation or contract",
            )
        return SemanticPayload(
            invocation_id=invocation.invocation_id,
            generator_id="scripted",
            generator_version="1.0.0",
            status=GeneratorStatus.COMPLETED,
            payload=self._script[key],
        )
