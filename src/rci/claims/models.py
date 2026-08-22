"""Strict domain records for the Phase 1 inquiry kernel.

The records in this module deliberately contain no clocks, generated IDs, or I/O.
Callers must supply those values or use a deterministic constructor from ``logic``.
"""

from __future__ import annotations

import json
import math
from enum import StrEnum
from hashlib import sha256
from typing import Any

from pydantic import BaseModel, ConfigDict, JsonValue, field_validator, model_validator

from rci.core.model import ArtifactRef


class FrozenModel(BaseModel):
    """Repository-wide shape used by immutable domain records in this slice."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class FrozenJsonDict(dict[str, Any]):
    """JSON object with recursively frozen children."""

    @staticmethod
    def _blocked(*_args: Any, **_kwargs: Any) -> None:
        raise TypeError("frozen JSON objects cannot be mutated")

    __setitem__ = _blocked
    __delitem__ = _blocked
    clear = _blocked
    pop = _blocked
    popitem = _blocked  # type: ignore[assignment]
    setdefault = _blocked
    update = _blocked
    __ior__ = _blocked  # type: ignore[assignment]


class FrozenJsonList(list[Any]):
    """JSON array with recursively frozen children."""

    @staticmethod
    def _blocked(*_args: Any, **_kwargs: Any) -> None:
        raise TypeError("frozen JSON arrays cannot be mutated")

    __setitem__ = _blocked
    __delitem__ = _blocked
    append = _blocked
    clear = _blocked
    extend = _blocked
    insert = _blocked
    pop = _blocked
    remove = _blocked
    reverse = _blocked
    sort = _blocked
    __iadd__ = _blocked  # type: ignore[assignment]
    __imul__ = _blocked  # type: ignore[assignment]


type InertPayload = ArtifactRef | JsonValue


class ClaimRole(StrEnum):
    OBSERVATION = "observation"
    CHARACTERIZATION = "characterization"
    VARIATION = "variation"
    BOUNDARY = "boundary"
    FACTOR = "factor"
    NECESSITY = "necessity"
    SUFFICIENCY = "sufficiency"
    PREREQUISITE = "prerequisite"
    CONFLICT = "conflict"
    RESIDUAL = "residual"
    LOCALIZATION = "localization"
    GENERALIZATION = "generalization"
    ACTUALIZATION = "actualization"
    INVARIANT = "invariant"
    PATTERN = "pattern"
    INTERPRETATION = "interpretation"
    UNKNOWN = "unknown"


class ClaimStatus(StrEnum):
    """Lifecycle standing only; it carries no truth or warrant judgment."""

    PROVISIONAL = "provisional"
    SUSPENDED = "suspended"
    SUPERSEDED = "superseded"


class ClaimAssessment(StrEnum):
    """Fallible assessment kept orthogonal to lifecycle and promotion."""

    UNASSESSED = "unassessed"
    SUPPORTED = "supported"
    CONTESTED = "contested"
    REFUTED = "refuted"
    UNKNOWN = "unknown"


class RepresentationLevel(StrEnum):
    L0_OPAQUE = "l0_opaque"
    L1_STRUCTURED = "l1_structured"
    L2_FORMAL = "l2_formal"
    L3_PROMOTED_VIEW = "l3_promoted_view"


class Polarity(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    UNSPECIFIED = "unspecified"


class ConflictKind(StrEnum):
    STRUCTURAL_POLARITY = "structural_polarity"
    CANDIDATE_SEMANTIC = "candidate_semantic"


class ObligationKind(StrEnum):
    CHARACTERIZE = "characterize"
    SAME_CLASS_VARIATION = "same_class_variation"
    MINIMAL_BOUNDARY_CROSSING = "minimal_boundary_crossing"
    PROPOSE_FACTOR = "propose_factor"
    NECESSITY_COUNTEREXAMPLE = "necessity_counterexample"
    SUFFICIENCY_COUNTEREXAMPLE = "sufficiency_counterexample"
    PREREQUISITE_BYPASS = "prerequisite_bypass"
    LOCALIZE_CONFLICT = "localize_conflict"
    CHARACTERIZE_RESIDUAL = "characterize_residual"
    DISCHARGE_OPEN_DEPENDENCY = "discharge_open_dependency"
    CLARIFY_REIFICATION = "clarify_reification"
    DISCRIMINATE_RECONSTRUCTION = "discriminate_reconstruction"
    SEPARATE_CONSEQUENCE_CLASSES = "separate_consequence_classes"


class ObligationStatus(StrEnum):
    OPEN = "open"
    BLOCKED = "blocked"
    SATISFIED = "satisfied"
    IMPOSSIBLE = "impossible"
    UNKNOWN = "unknown"


class CandidateKind(StrEnum):
    QUESTION_ANSWER = "question_answer"
    FORMALIZATION = "formalization"
    RECONSTRUCTION = "reconstruction"
    GENERATED_PROBE = "generated_probe"


class CorrectionKind(StrEnum):
    SUPERSEDES = "supersedes"
    SPLITS_FROM = "splits_from"
    MERGES_FROM = "merges_from"
    REBINDS = "rebinds"
    REFUTES = "refutes"
    SUSPENDS = "suspends"
    PROMOTES = "promotes"
    REOPENS = "reopens"


class GuardStanding(StrEnum):
    STANDING = "standing"
    INVALIDATED = "invalidated"


def freeze_json(value: JsonValue) -> JsonValue:
    """Return a JSON-equivalent value whose nested containers reject mutation."""

    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("JSON payload numbers must be finite")
    if isinstance(value, list):
        return FrozenJsonList(freeze_json(item) for item in value)
    if isinstance(value, dict):
        return FrozenJsonDict((key, freeze_json(item)) for key, item in value.items())
    return value


def _json_ready(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _json_ready(value.model_dump(mode="json"))
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    """Return the stable JSON form used by fingerprints in this package."""

    return json.dumps(
        _json_ready(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def content_fingerprint(namespace: str, value: Any) -> str:
    material = f"{namespace}\x00{canonical_json(value)}".encode()
    return sha256(material).hexdigest()


class BoundArgument(FrozenModel):
    name: str
    value: JsonValue

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value:
            raise ValueError("bound argument names cannot be empty")
        return value

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: JsonValue) -> JsonValue:
        return freeze_json(value)


class Scope(FrozenModel):
    """The exact semantic universe within which a claim may be assessed."""

    id: str
    binding_revision: str
    assumption_ids: tuple[str, ...] = ()
    applicability_guard_id: str | None = None
    finite_universe_hash: str | None = None
    closed_world: bool = False

    @model_validator(mode="after")
    def validate_scope(self) -> Scope:
        if not self.id or not self.binding_revision:
            raise ValueError("scope id and binding revision are required")
        if len(set(self.assumption_ids)) != len(self.assumption_ids):
            raise ValueError("scope assumptions must be unique")
        if self.closed_world and self.finite_universe_hash is None:
            raise ValueError("closed-world scopes require a finite-universe hash")
        return self

    @property
    def fingerprint(self) -> str:
        return content_fingerprint("rci.scope.v1", self)


class Provenance(FrozenModel):
    kind: str
    source_id: str
    source_revision: str | None = None

    @model_validator(mode="after")
    def validate_required_text(self) -> Provenance:
        if not self.kind or not self.source_id:
            raise ValueError("provenance kind and source id are required")
        return self


class Claim(FrozenModel):
    id: str
    role: ClaimRole
    bound_args: tuple[BoundArgument, ...]
    payload: InertPayload
    scope: Scope
    provenance: Provenance
    status: ClaimStatus = ClaimStatus.PROVISIONAL
    assessment: ClaimAssessment = ClaimAssessment.UNASSESSED
    representation_level: RepresentationLevel = RepresentationLevel.L0_OPAQUE
    parent_ids: tuple[str, ...] = ()
    proposition_id: str | None = None
    polarity: Polarity = Polarity.UNSPECIFIED

    @field_validator("payload")
    @classmethod
    def validate_payload(cls, value: InertPayload) -> InertPayload:
        if isinstance(value, ArtifactRef):
            return value
        return freeze_json(value)

    @model_validator(mode="after")
    def validate_claim(self) -> Claim:
        if not self.id:
            raise ValueError("claim id is required")
        names = [argument.name for argument in self.bound_args]
        if len(set(names)) != len(names):
            raise ValueError("bound argument names must be unique")
        if len(set(self.parent_ids)) != len(self.parent_ids):
            raise ValueError("parent claim ids must be unique")
        if self.representation_level is RepresentationLevel.L3_PROMOTED_VIEW:
            raise ValueError("L3 is a linked warranted-lemma view, not a Claim mutation")
        return self

    @property
    def structural_key(self) -> tuple[str, ClaimRole, str, str] | None:
        """Return the explicit identity used for L0 structural opposition.

        Opaque payload content is intentionally absent from this key.
        """

        if self.proposition_id is None or self.polarity is Polarity.UNSPECIFIED:
            return None
        args = canonical_json([item.model_dump(mode="json") for item in self.bound_args])
        return self.proposition_id, self.role, args, self.scope.fingerprint


class Conflict(FrozenModel):
    id: str
    claim_ids: tuple[str, str]
    kind: ConflictKind
    scope: Scope
    proposition_id: str | None = None

    @model_validator(mode="after")
    def validate_conflict(self) -> Conflict:
        if self.claim_ids[0] == self.claim_ids[1]:
            raise ValueError("a claim cannot conflict with itself")
        if tuple(sorted(self.claim_ids)) != self.claim_ids:
            raise ValueError("conflict claim ids must be sorted")
        return self


class Obligation(FrozenModel):
    id: str
    kind: ObligationKind
    carrier_id: str
    args: tuple[BoundArgument, ...]
    scope: Scope
    binding_revision: str
    parent_obligation_ids: tuple[str, ...] = ()
    priority_vector: tuple[int, ...] = (0,)
    status: ObligationStatus = ObligationStatus.OPEN

    @model_validator(mode="after")
    def validate_obligation(self) -> Obligation:
        if not self.id or not self.carrier_id:
            raise ValueError("obligation id and carrier id are required")
        if self.binding_revision != self.scope.binding_revision:
            raise ValueError("obligation and scope binding revisions must match")
        names = [argument.name for argument in self.args]
        if len(set(names)) != len(names):
            raise ValueError("obligation argument names must be unique")
        if len(set(self.parent_obligation_ids)) != len(self.parent_obligation_ids):
            raise ValueError("parent obligation ids must be unique")
        return self

    @property
    def fingerprint(self) -> str:
        normalized_args = sorted(
            (item.model_dump(mode="json") for item in self.args),
            key=lambda item: (str(item["name"]), canonical_json(item["value"])),
        )
        return content_fingerprint(
            "rci.obligation.v1",
            {
                "kind": self.kind,
                "args": normalized_args,
                "scope": self.scope.fingerprint,
                "binding_revision": self.binding_revision,
            },
        )


class Candidate(FrozenModel):
    """An inert candidate that has not acquired semantic or policy authority."""

    id: str
    kind: CandidateKind
    payload: InertPayload
    scope: Scope
    provenance: Provenance
    source_ids: tuple[str, ...] = ()

    @field_validator("payload")
    @classmethod
    def validate_payload(cls, value: InertPayload) -> InertPayload:
        if isinstance(value, ArtifactRef):
            return value
        return freeze_json(value)

    @model_validator(mode="after")
    def validate_candidate(self) -> Candidate:
        if not self.id:
            raise ValueError("candidate identity is required")
        if len(set(self.source_ids)) != len(self.source_ids):
            raise ValueError("candidate source references must be unique")
        return self


class Residual(FrozenModel):
    """Unresolved remainder preserved as data rather than silently discarded."""

    id: str
    carrier_id: str
    payload: InertPayload
    scope: Scope
    provenance: Provenance
    source_obligation_ids: tuple[str, ...] = ()

    @field_validator("payload")
    @classmethod
    def validate_payload(cls, value: InertPayload) -> InertPayload:
        if isinstance(value, ArtifactRef):
            return value
        return freeze_json(value)

    @model_validator(mode="after")
    def validate_residual(self) -> Residual:
        if not self.id or not self.carrier_id:
            raise ValueError("residual identity and carrier are required")
        if len(set(self.source_obligation_ids)) != len(self.source_obligation_ids):
            raise ValueError("residual obligation references must be unique")
        return self


class Correction(FrozenModel):
    """An immutable succession relation; it never rewrites its target."""

    id: str
    kind: CorrectionKind
    target_id: str
    related_ids: tuple[str, ...]
    scope: Scope
    provenance: Provenance

    @model_validator(mode="after")
    def validate_correction(self) -> Correction:
        if not self.id or not self.target_id:
            raise ValueError("correction identity and target are required")
        if len(set(self.related_ids)) != len(self.related_ids):
            raise ValueError("correction relations must be unique")
        if self.target_id in self.related_ids:
            raise ValueError("a correction cannot relate an object to itself")
        return self


class ObligationDisposition(FrozenModel):
    """Append-only status evidence for an immutable obligation record."""

    id: str
    obligation_id: str
    status: ObligationStatus
    reason: str
    evidence_refs: tuple[str, ...] = ()
    predecessor_id: str | None = None

    @model_validator(mode="after")
    def validate_disposition(self) -> ObligationDisposition:
        if not self.id or not self.obligation_id or not self.reason:
            raise ValueError("obligation disposition identity, target, and reason are required")
        if len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise ValueError("obligation evidence references must be unique")
        if self.predecessor_id == self.id:
            raise ValueError("an obligation disposition cannot succeed itself")
        return self


class GuardChange(FrozenModel):
    """One immutable standing change in a guard's append-only history."""

    id: str
    condition_id: str
    scope_fingerprint: str
    standing: GuardStanding
    reason: str
    predecessor_id: str | None = None

    @model_validator(mode="after")
    def validate_change(self) -> GuardChange:
        if not self.id or not self.condition_id or not self.scope_fingerprint or not self.reason:
            raise ValueError("guard change identity, condition, scope, and reason are required")
        if self.predecessor_id == self.id:
            raise ValueError("a guard change cannot succeed itself")
        return self
