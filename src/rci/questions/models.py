"""Data-only question contracts.

Executable policies are named registry references. A catalog entry cannot import code,
execute a payload, or select an arbitrary command.
"""

from __future__ import annotations

from enum import StrEnum
from string import Formatter

from pydantic import model_validator

from rci.claims.logic import bind_l0_answer
from rci.claims.models import (
    BoundArgument,
    Claim,
    ClaimRole,
    FrozenModel,
    InertPayload,
    Provenance,
    Scope,
    content_fingerprint,
)


class ContractMaturity(StrEnum):
    DRAFT = "draft"
    EXPERIMENTAL = "experimental"
    STABLE = "stable"
    DEPRECATED = "deprecated"


class AnswerShape(StrEnum):
    """Closed G1 answer shapes admitted by the typed binder registry."""

    OPAQUE_L0_INERT = "opaque_l0_inert"


class QuestionContract(FrozenModel):
    id: str
    version: str
    family: str
    input_roles: tuple[str, ...]
    output_claim_role: ClaimRole
    precondition_policy_id: str
    render_template: str
    answer_shape: AnswerShape = AnswerShape.OPAQUE_L0_INERT
    answer_schema_id: str = "rci.inert-payload.v1"
    bind_policy_id: str = "bind-l0-v1"
    reifier_id: str | None = None
    verifier_id: str | None = None
    update_rule_id: str = "append-provisional-claim-v1"
    next_obligation_rule_ids: tuple[str, ...] = ()
    maturity: ContractMaturity = ContractMaturity.DRAFT
    recurrent_probe: bool = False
    comparison_semantics_id: str | None = None
    canonical_probe_rendering: str | None = None
    applicability_guard_id: str | None = None
    history_policy_id: str | None = None

    @model_validator(mode="after")
    def validate_contract(self) -> QuestionContract:
        if not self.id or not self.version or not self.family or not self.answer_schema_id:
            raise ValueError("question id, version, family, and answer schema are required")
        if len(set(self.input_roles)) != len(self.input_roles):
            raise ValueError("question input roles must be unique")
        if self.recurrent_probe:
            required = (
                self.comparison_semantics_id,
                self.applicability_guard_id,
                self.history_policy_id,
            )
            if any(value is None for value in required):
                raise ValueError("recurrent probes require comparison, guard, and history policy")
        return self

    @property
    def key(self) -> str:
        return f"{self.id}@{self.version}"


class QuestionProfile(FrozenModel):
    id: str
    version: str
    contract_keys: tuple[str, ...]

    @model_validator(mode="after")
    def validate_profile(self) -> QuestionProfile:
        if len(set(self.contract_keys)) != len(self.contract_keys):
            raise ValueError("profile contract keys must be unique")
        return self


class QuestionCatalog(FrozenModel):
    id: str
    version: str
    contracts: tuple[QuestionContract, ...]
    profiles: tuple[QuestionProfile, ...]

    @model_validator(mode="after")
    def validate_catalog(self) -> QuestionCatalog:
        keys = [contract.key for contract in self.contracts]
        if len(set(keys)) != len(keys):
            raise ValueError("catalog contract keys must be unique")
        known = set(keys)
        for profile in self.profiles:
            missing = set(profile.contract_keys) - known
            if missing:
                raise ValueError(f"profile references unknown contracts: {sorted(missing)}")
            deprecated = {
                contract.key
                for contract in self.contracts
                if contract.maturity is ContractMaturity.DEPRECATED
            }
            if deprecated.intersection(profile.contract_keys):
                raise ValueError("deprecated contracts cannot be newly scheduled")
        profile_keys = [(profile.id, profile.version) for profile in self.profiles]
        if len(set(profile_keys)) != len(profile_keys):
            raise ValueError("catalog profile versions must be unique")
        return self

    @property
    def digest(self) -> str:
        return content_fingerprint("rci.question-catalog.v1", self)

    def schedulable_contracts(self, profile_id: str, version: str) -> tuple[QuestionContract, ...]:
        profile = next(
            (item for item in self.profiles if item.id == profile_id and item.version == version),
            None,
        )
        if profile is None:
            raise KeyError(f"unknown question profile {profile_id}@{version}")
        by_key = {contract.key: contract for contract in self.contracts}
        return tuple(by_key[key] for key in profile.contract_keys)


def _render_fields(template: str) -> tuple[str, ...]:
    fields: list[str] = []
    for _, field_name, format_spec, conversion in Formatter().parse(template):
        if field_name is None:
            continue
        if not field_name or any(character in field_name for character in ".["):
            raise ValueError("templates may reference only direct named fields")
        if format_spec or conversion:
            raise ValueError("format specifications and conversions are not allowed")
        fields.append(field_name)
    return tuple(fields)


def render_question(contract: QuestionContract, bindings: dict[str, str]) -> str:
    """Render an inert catalog template with an exact set of text bindings."""

    fields = _render_fields(contract.render_template)
    if set(fields) != set(bindings):
        missing = sorted(set(fields) - set(bindings))
        extra = sorted(set(bindings) - set(fields))
        raise ValueError(f"render bindings mismatch; missing={missing}, extra={extra}")
    return contract.render_template.format_map(bindings)


def bind_answer(
    contract: QuestionContract,
    *,
    answer: InertPayload,
    bound_args: tuple[BoundArgument, ...],
    scope: Scope,
    provenance: Provenance,
) -> Claim:
    if contract.answer_shape is not AnswerShape.OPAQUE_L0_INERT:
        raise ValueError(f"unregistered answer shape {contract.answer_shape!r}")
    if contract.answer_schema_id != "rci.inert-payload.v1":
        raise ValueError(f"unregistered answer schema {contract.answer_schema_id!r}")
    if contract.bind_policy_id != "bind-l0-v1":
        raise ValueError(f"unregistered bind policy {contract.bind_policy_id!r}")
    return bind_l0_answer(
        question_contract_id=contract.key,
        role=contract.output_claim_role,
        answer=answer,
        bound_args=bound_args,
        scope=scope,
        provenance=provenance,
    )
