"""Fail-closed conversion from inert claim payloads to validated formulas."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, TypeAdapter, ValidationError, model_validator

from rci.claims.models import Claim, FrozenModel, Scope
from rci.formal.ast import Formula


class FormalCandidate(FrozenModel):
    claim_id: str
    formal_type: Literal["boolean_finite_v1"] = "boolean_finite_v1"
    expression: Formula
    carrier_id: str
    scope: Scope
    assumption_ids: tuple[str, ...] = ()


class Reified(FrozenModel):
    kind: Literal["reified"] = "reified"
    candidate: FormalCandidate


class NeedsClarification(FrozenModel):
    kind: Literal["needs_clarification"] = "needs_clarification"
    claim_id: str
    reason: str


class UnsupportedReification(FrozenModel):
    kind: Literal["unsupported"] = "unsupported"
    claim_id: str
    capability: str


class FailedReification(FrozenModel):
    kind: Literal["failed"] = "failed"
    claim_id: str
    reason: str


type ReificationOutcome = Annotated[
    Reified | NeedsClarification | UnsupportedReification | FailedReification,
    Field(discriminator="kind"),
]

_FORMULA_ADAPTER: TypeAdapter[Formula] = TypeAdapter(Formula)


class _Envelope(FrozenModel):
    schema_id: str
    carrier_id: str
    expression: dict[str, object]

    @model_validator(mode="after")
    def validate_required_text(self) -> _Envelope:
        if not self.schema_id or not self.carrier_id:
            raise ValueError("reification envelope requires schema and carrier identity")
        return self


def reify_claim(claim: Claim) -> ReificationOutcome:
    """Reify only a versioned envelope; opaque prose never gains formal meaning."""

    if not isinstance(claim.payload, dict):
        return NeedsClarification(
            claim_id=claim.id,
            reason="a versioned structured expression is required",
        )
    schema_id = claim.payload.get("schema_id")
    if isinstance(schema_id, str) and schema_id != "rci.boolean-finite.v1":
        return UnsupportedReification(claim_id=claim.id, capability=schema_id)
    try:
        envelope = _Envelope.model_validate(claim.payload)
        expression = _FORMULA_ADAPTER.validate_python(envelope.expression, strict=True)
    except ValidationError as error:
        first = error.errors(include_url=False)[0]
        location = ".".join(str(part) for part in first["loc"])
        return FailedReification(
            claim_id=claim.id,
            reason=f"invalid_boolean_finite_ast:{location}:{first['type']}",
        )
    return Reified(
        candidate=FormalCandidate(
            claim_id=claim.id,
            expression=expression,
            carrier_id=envelope.carrier_id,
            scope=claim.scope,
            assumption_ids=claim.scope.assumption_ids,
        )
    )
