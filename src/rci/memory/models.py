"""Strict, immutable records for G2A retrieval and measured reacquisition.

These records describe provisional memory relations only.  They intentionally carry no
license, promotion, or warrant-class field.
"""

from __future__ import annotations

from enum import StrEnum
from math import gcd
from typing import Annotated, Literal

from pydantic import Field, JsonValue, field_validator, model_validator

from rci.claims.models import content_fingerprint, freeze_json
from rci.core.model import ArtifactRef, FrozenModel, Identifier, Sha256Digest
from rci.warrant.models import CheckReference

SchemaVersion = Literal[1]
NonNegativeInt = Annotated[int, Field(ge=0)]
PositiveInt = Annotated[int, Field(gt=0)]


def _require_canonical_ids(values: tuple[str, ...], *, field_name: str) -> None:
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must be unique")
    if tuple(sorted(values)) != values:
        raise ValueError(f"{field_name} must use canonical order")


class MemoryOwner(StrEnum):
    """The single folded-state owner of a referenced record."""

    EPISODIC = "M_E"
    SEMANTIC = "M_S"
    PROCEDURAL = "M_P"
    RETENTION = "M_L"
    WARRANT = "W"
    ACTION = "A"
    PREDICTION = "Pi"


class OwnedRecordType(StrEnum):
    """G2A allowlist of aggregate-owned record shapes usable by memory packages."""

    PROBE_EVENT = "probe_event"
    LEMMA_VERSION = "lemma_version"
    SEMANTIC_DELTA = "semantic_delta"
    PROBE_IDENTITY = "probe_identity"
    RETENTION_PACKAGE = "retention_package"
    REACQUISITION_SCAFFOLD = "reacquisition_scaffold"
    RECOVERY_PROTOCOL = "recovery_protocol"
    EVIDENCE = "evidence"
    CHECKER_VERDICT = "checker_verdict"
    WARRANT_DECISION = "warrant_decision"
    EFFECT_REQUEST = "effect_request"
    EXTERNAL_RETURN = "external_return"
    RECONSTRUCTION = "reconstruction"
    PREDICTION_SEAL = "prediction_seal"


_RECORD_OWNER: dict[OwnedRecordType, MemoryOwner] = {
    OwnedRecordType.PROBE_EVENT: MemoryOwner.EPISODIC,
    OwnedRecordType.LEMMA_VERSION: MemoryOwner.SEMANTIC,
    OwnedRecordType.SEMANTIC_DELTA: MemoryOwner.SEMANTIC,
    OwnedRecordType.PROBE_IDENTITY: MemoryOwner.PROCEDURAL,
    OwnedRecordType.RETENTION_PACKAGE: MemoryOwner.RETENTION,
    OwnedRecordType.REACQUISITION_SCAFFOLD: MemoryOwner.RETENTION,
    OwnedRecordType.RECOVERY_PROTOCOL: MemoryOwner.RETENTION,
    OwnedRecordType.EVIDENCE: MemoryOwner.WARRANT,
    OwnedRecordType.CHECKER_VERDICT: MemoryOwner.WARRANT,
    OwnedRecordType.WARRANT_DECISION: MemoryOwner.WARRANT,
    OwnedRecordType.EFFECT_REQUEST: MemoryOwner.ACTION,
    OwnedRecordType.EXTERNAL_RETURN: MemoryOwner.ACTION,
    OwnedRecordType.RECONSTRUCTION: MemoryOwner.ACTION,
    OwnedRecordType.PREDICTION_SEAL: MemoryOwner.PREDICTION,
}


class OwnedMemoryRef(FrozenModel):
    """A typed reference that detects missing, replaced, or reinterpreted records."""

    schema_version: SchemaVersion = 1
    owner: MemoryOwner
    record_type: OwnedRecordType
    record_id: Identifier
    record_schema_version: PositiveInt
    content_fingerprint: Sha256Digest

    @model_validator(mode="after")
    def validate_owner(self) -> OwnedMemoryRef:
        if _RECORD_OWNER[self.record_type] is not self.owner:
            raise ValueError("owned memory record type does not belong to the declared owner")
        return self

    @property
    def key(self) -> str:
        return (
            f"{self.owner.value}:{self.record_type}:{self.record_id}:v{self.record_schema_version}"
        )


class RetrievalRankComponent(StrEnum):
    REFERENCE_MATCH = "reference_match_count"
    RECORD_TYPE_MATCH = "record_type_match_count"
    OWNER_MATCH = "owner_match_count"
    CUE_MATCH = "cue_match_count"
    TAG_MATCH = "tag_match_count"


DEFAULT_RANK_COMPONENTS = (
    RetrievalRankComponent.REFERENCE_MATCH,
    RetrievalRankComponent.RECORD_TYPE_MATCH,
    RetrievalRankComponent.OWNER_MATCH,
    RetrievalRankComponent.CUE_MATCH,
    RetrievalRankComponent.TAG_MATCH,
)


class StructuralRetrievalPolicy(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    version: Identifier
    max_results: Annotated[int, Field(ge=1, le=1000)] = 100
    rank_components: tuple[RetrievalRankComponent, ...] = DEFAULT_RANK_COMPONENTS
    accepted_record_types: tuple[OwnedRecordType, ...] = ()
    exact_scope: Literal[True] = True
    exact_binding: Literal[True] = True
    exact_horizon: Literal[True] = True
    reject_stale_references: Literal[True] = True

    @model_validator(mode="after")
    def validate_policy(self) -> StructuralRetrievalPolicy:
        if not self.rank_components:
            raise ValueError("retrieval policy requires at least one exact rank component")
        if len(set(self.rank_components)) != len(self.rank_components):
            raise ValueError("retrieval rank components must be unique")
        _require_canonical_ids(
            tuple(record_type.value for record_type in self.accepted_record_types),
            field_name="accepted retrieval record types",
        )
        return self


class RetrievalQuery(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    policy_id: Identifier
    policy_version: Identifier
    scope_fingerprint: Identifier
    binding_revision: Identifier
    protected_horizon_id: Identifier
    source_sequence: NonNegativeInt
    source_index_fingerprint: Sha256Digest
    owners: tuple[MemoryOwner, ...] = ()
    record_types: tuple[OwnedRecordType, ...] = ()
    reference_selectors: tuple[OwnedMemoryRef, ...] = ()
    cue_ids: tuple[Identifier, ...] = ()
    tag_ids: tuple[Identifier, ...] = ()
    limit: Annotated[int, Field(ge=1, le=1000)] = 20

    @model_validator(mode="after")
    def validate_query(self) -> RetrievalQuery:
        if not any(
            (
                self.owners,
                self.record_types,
                self.reference_selectors,
                self.cue_ids,
                self.tag_ids,
            )
        ):
            raise ValueError("retrieval query requires at least one structural selector")
        owner_values = tuple(owner.value for owner in self.owners)
        _require_canonical_ids(owner_values, field_name="retrieval owners")
        for field_name, values in (
            ("retrieval cue ids", self.cue_ids),
            ("retrieval tag ids", self.tag_ids),
        ):
            _require_canonical_ids(values, field_name=field_name)
        _require_canonical_ids(
            tuple(record_type.value for record_type in self.record_types),
            field_name="retrieval record types",
        )
        _require_canonical_ids(
            tuple(reference.key for reference in self.reference_selectors),
            field_name="retrieval reference selectors",
        )
        return self


class RetrievalRank(FrozenModel):
    schema_version: SchemaVersion = 1
    reference_match_count: NonNegativeInt = 0
    record_type_match_count: NonNegativeInt = 0
    owner_match_count: NonNegativeInt = 0
    cue_match_count: NonNegativeInt = 0
    tag_match_count: NonNegativeInt = 0

    def component(self, component: RetrievalRankComponent) -> int:
        return int(getattr(self, component.value))


class RetrievalHit(FrozenModel):
    schema_version: SchemaVersion = 1
    package_id: Identifier
    package_content_fingerprint: Sha256Digest
    rank: RetrievalRank
    matched_ref_keys: tuple[str, ...] = ()
    matched_cue_ids: tuple[Identifier, ...] = ()
    matched_tag_ids: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def validate_hit(self) -> RetrievalHit:
        for field_name, values in (
            ("matched retrieval refs", self.matched_ref_keys),
            ("matched retrieval cues", self.matched_cue_ids),
            ("matched retrieval tags", self.matched_tag_ids),
        ):
            _require_canonical_ids(values, field_name=field_name)
        if not any(
            (
                self.rank.reference_match_count,
                self.rank.record_type_match_count,
                self.rank.owner_match_count,
                self.rank.cue_match_count,
                self.rank.tag_match_count,
            )
        ):
            raise ValueError("retrieval hits require at least one structural match")
        return self


class RetrievalResult(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    query_id: Identifier
    policy_id: Identifier
    policy_version: Identifier
    source_sequence: NonNegativeInt
    source_index_fingerprint: Sha256Digest
    hits: tuple[RetrievalHit, ...]
    rejected_stale_package_ids: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def validate_result(self) -> RetrievalResult:
        hit_ids = tuple(hit.package_id for hit in self.hits)
        if len(set(hit_ids)) != len(hit_ids):
            raise ValueError("retrieval result package hits must be deduplicated")
        _require_canonical_ids(
            self.rejected_stale_package_ids,
            field_name="stale retrieval package ids",
        )
        if set(hit_ids) & set(self.rejected_stale_package_ids):
            raise ValueError("a stale package cannot also be returned as a hit")
        return self


class _ProvisionalRoute(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    scope_fingerprint: Identifier
    binding_revision: Identifier
    protected_horizon_id: Identifier
    source_refs: tuple[OwnedMemoryRef, ...]
    provenance_refs: tuple[Identifier, ...]

    @model_validator(mode="after")
    def validate_common_route(self) -> _ProvisionalRoute:
        if not self.source_refs:
            raise ValueError("provisional recovery routes require owned source references")
        ref_keys = tuple(reference.key for reference in self.source_refs)
        _require_canonical_ids(ref_keys, field_name="route source references")
        if not self.provenance_refs:
            raise ValueError("provisional recovery routes require provenance")
        _require_canonical_ids(self.provenance_refs, field_name="route provenance references")
        return self


class DirectUseRoute(_ProvisionalRoute):
    kind: Literal["direct_use"] = "direct_use"
    present_use_contract_id: Identifier


class ReconstructionRoute(_ProvisionalRoute):
    kind: Literal["reconstruction"] = "reconstruction"
    reconstruction_policy_id: Identifier


class ConsequenceEvaluationRoute(_ProvisionalRoute):
    kind: Literal["consequence_evaluation"] = "consequence_evaluation"
    consequence_evaluator_id: Identifier


class ReacquisitionRoute(_ProvisionalRoute):
    kind: Literal["reacquisition"] = "reacquisition"
    recovery_protocol_id: Identifier
    reacquisition_scaffold_id: Identifier


ProvisionalRecoveryRoute = Annotated[
    DirectUseRoute | ReconstructionRoute | ConsequenceEvaluationRoute | ReacquisitionRoute,
    Field(discriminator="kind"),
]


class ReacquisitionScaffold(FrozenModel):
    """A bounded recovery scaffold whose schema has no target-answer payload."""

    schema_version: SchemaVersion = 1
    id: Identifier
    scope_fingerprint: Identifier
    binding_revision: Identifier
    protected_horizon_id: Identifier
    cue_refs: tuple[OwnedMemoryRef, ...] = ()
    ordered_probe_ids: tuple[Identifier, ...] = ()
    boundary_refs: tuple[OwnedMemoryRef, ...] = ()
    failure_refs: tuple[OwnedMemoryRef, ...] = ()
    provenance_refs: tuple[Identifier, ...]

    @model_validator(mode="after")
    def validate_scaffold(self) -> ReacquisitionScaffold:
        if not any((self.cue_refs, self.ordered_probe_ids, self.boundary_refs, self.failure_refs)):
            raise ValueError("reacquisition scaffold cannot be structurally empty")
        for field_name, references in (
            ("scaffold cues", self.cue_refs),
            ("scaffold boundaries", self.boundary_refs),
            ("scaffold failures", self.failure_refs),
        ):
            _require_canonical_ids(
                tuple(reference.key for reference in references),
                field_name=field_name,
            )
        if len(set(self.ordered_probe_ids)) != len(self.ordered_probe_ids):
            raise ValueError("ordered scaffold probes must be unique")
        if not self.provenance_refs:
            raise ValueError("reacquisition scaffold requires provenance")
        _require_canonical_ids(self.provenance_refs, field_name="scaffold provenance references")
        return self


class CostAxis(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    unit_id: Identifier
    direction: Literal["lower_is_better"] = "lower_is_better"


class CostCoordinate(FrozenModel):
    schema_version: SchemaVersion = 1
    axis: CostAxis
    numerator: NonNegativeInt
    denominator: PositiveInt = 1

    @model_validator(mode="after")
    def require_reduced_fraction(self) -> CostCoordinate:
        if self.numerator == 0 and self.denominator != 1:
            raise ValueError("zero costs use canonical denominator one")
        if self.numerator != 0 and gcd(self.numerator, self.denominator) != 1:
            raise ValueError("exact costs must use reduced rational form")
        return self


class CostVector(FrozenModel):
    schema_version: SchemaVersion = 1
    coordinates: tuple[CostCoordinate, ...]

    @model_validator(mode="after")
    def validate_vector(self) -> CostVector:
        if not self.coordinates:
            raise ValueError("cost vectors require at least one named axis")
        axis_ids = tuple(coordinate.axis.id for coordinate in self.coordinates)
        _require_canonical_ids(axis_ids, field_name="cost-vector axes")
        return self

    @property
    def axis_signature(self) -> tuple[tuple[str, str, int], ...]:
        return tuple(
            (coordinate.axis.id, coordinate.axis.unit_id, coordinate.axis.schema_version)
            for coordinate in self.coordinates
        )


class RecoveryPins(FrozenModel):
    schema_version: SchemaVersion = 1
    scope_fingerprint: Identifier
    target_competence_id: Identifier
    finite_universe_hash: Sha256Digest
    binding_revision: Identifier
    protected_horizon_id: Identifier
    evaluator_id: Identifier
    evaluator_version: Identifier
    evidence_access_id: Identifier
    evidence_access_version: Identifier
    budget_id: Identifier
    budget_version: Identifier
    budget: CostVector
    recovery_protocol_id: Identifier
    recovery_protocol_version: Identifier
    comparison_policy_id: Identifier
    comparison_policy_version: Identifier


class RecoveryProtocol(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    version: Identifier
    scope_fingerprint: Identifier
    target_competence_id: Identifier
    finite_universe_hash: Sha256Digest
    binding_revision: Identifier
    protected_horizon_id: Identifier
    evaluator_id: Identifier
    evaluator_version: Identifier
    evidence_access_id: Identifier
    evidence_access_version: Identifier
    budget_id: Identifier
    budget_version: Identifier
    budget: CostVector
    comparison_policy_id: Identifier
    comparison_policy_version: Identifier
    cost_axes: tuple[CostAxis, ...]

    @model_validator(mode="after")
    def validate_protocol(self) -> RecoveryProtocol:
        if not self.cost_axes:
            raise ValueError("recovery protocol requires at least one declared cost axis")
        _require_canonical_ids(
            tuple(axis.id for axis in self.cost_axes),
            field_name="recovery protocol cost axes",
        )
        axis_signature = tuple(
            (axis.id, axis.unit_id, axis.schema_version) for axis in self.cost_axes
        )
        if self.budget.axis_signature != axis_signature:
            raise ValueError("recovery budget axes must exactly match protocol cost axes")
        return self

    @property
    def pins(self) -> RecoveryPins:
        return RecoveryPins(
            scope_fingerprint=self.scope_fingerprint,
            target_competence_id=self.target_competence_id,
            finite_universe_hash=self.finite_universe_hash,
            binding_revision=self.binding_revision,
            protected_horizon_id=self.protected_horizon_id,
            evaluator_id=self.evaluator_id,
            evaluator_version=self.evaluator_version,
            evidence_access_id=self.evidence_access_id,
            evidence_access_version=self.evidence_access_version,
            budget_id=self.budget_id,
            budget_version=self.budget_version,
            budget=self.budget,
            recovery_protocol_id=self.id,
            recovery_protocol_version=self.version,
            comparison_policy_id=self.comparison_policy_id,
            comparison_policy_version=self.comparison_policy_version,
        )


class RetentionPackage(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    scope_fingerprint: Identifier
    binding_revision: Identifier
    protected_horizon_id: Identifier
    owned_refs: tuple[OwnedMemoryRef, ...]
    cue_ids: tuple[Identifier, ...] = ()
    tag_ids: tuple[Identifier, ...] = ()
    direct_use_route_ids: tuple[Identifier, ...] = ()
    reconstruction_route_ids: tuple[Identifier, ...] = ()
    consequence_evaluation_route_ids: tuple[Identifier, ...] = ()
    reacquisition_route_ids: tuple[Identifier, ...] = ()
    scaffold_ids: tuple[Identifier, ...] = ()
    recovery_protocol_ids: tuple[Identifier, ...] = ()
    provenance_refs: tuple[Identifier, ...]

    @property
    def fingerprint(self) -> str:
        return content_fingerprint("rci.retention-package.v1", self)

    @model_validator(mode="after")
    def validate_package(self) -> RetentionPackage:
        if not self.owned_refs:
            raise ValueError("retention package requires owned typed references")
        _require_canonical_ids(
            tuple(reference.key for reference in self.owned_refs),
            field_name="retention package owned references",
        )
        route_groups = (
            self.direct_use_route_ids,
            self.reconstruction_route_ids,
            self.consequence_evaluation_route_ids,
            self.reacquisition_route_ids,
        )
        if not any(route_groups):
            raise ValueError("retention package requires at least one provisional route")
        all_route_ids: list[str] = []
        for field_name, values in (
            ("retention cues", self.cue_ids),
            ("retention tags", self.tag_ids),
            ("direct-use routes", self.direct_use_route_ids),
            ("reconstruction routes", self.reconstruction_route_ids),
            ("consequence-evaluation routes", self.consequence_evaluation_route_ids),
            ("reacquisition routes", self.reacquisition_route_ids),
            ("reacquisition scaffolds", self.scaffold_ids),
            ("recovery protocols", self.recovery_protocol_ids),
            ("retention provenance references", self.provenance_refs),
        ):
            _require_canonical_ids(values, field_name=field_name)
            if "routes" in field_name:
                all_route_ids.extend(values)
        if len(set(all_route_ids)) != len(all_route_ids):
            raise ValueError("provisional route kinds must remain separately identified")
        if not self.provenance_refs:
            raise ValueError("retention package requires provenance")
        return self


type _RegistrationRecord = (
    DirectUseRoute
    | ReconstructionRoute
    | ConsequenceEvaluationRoute
    | ReacquisitionRoute
    | ReacquisitionScaffold
    | RecoveryProtocol
)


class RetentionRegistration(FrozenModel):
    """Atomic registration payload while each contained record retains its own owner."""

    schema_version: SchemaVersion = 1
    package: RetentionPackage
    direct_use_routes: tuple[DirectUseRoute, ...] = ()
    reconstruction_routes: tuple[ReconstructionRoute, ...] = ()
    consequence_evaluation_routes: tuple[ConsequenceEvaluationRoute, ...] = ()
    reacquisition_routes: tuple[ReacquisitionRoute, ...] = ()
    scaffolds: tuple[ReacquisitionScaffold, ...] = ()
    recovery_protocols: tuple[RecoveryProtocol, ...] = ()

    @model_validator(mode="after")
    def validate_registration(self) -> RetentionRegistration:
        package = self.package
        collections: tuple[tuple[tuple[str, ...], tuple[_RegistrationRecord, ...], str], ...] = (
            (package.direct_use_route_ids, self.direct_use_routes, "direct-use routes"),
            (
                package.reconstruction_route_ids,
                self.reconstruction_routes,
                "reconstruction routes",
            ),
            (
                package.consequence_evaluation_route_ids,
                self.consequence_evaluation_routes,
                "consequence-evaluation routes",
            ),
            (
                package.reacquisition_route_ids,
                self.reacquisition_routes,
                "reacquisition routes",
            ),
            (package.scaffold_ids, self.scaffolds, "reacquisition scaffolds"),
            (package.recovery_protocol_ids, self.recovery_protocols, "recovery protocols"),
        )
        for expected_ids, records, label in collections:
            actual_ids = tuple(record.id for record in records)
            if actual_ids != expected_ids:
                raise ValueError(f"registered {label} must exactly match package references")
        pins = (
            package.scope_fingerprint,
            package.binding_revision,
            package.protected_horizon_id,
        )
        all_records: tuple[_RegistrationRecord, ...] = (
            *self.direct_use_routes,
            *self.reconstruction_routes,
            *self.consequence_evaluation_routes,
            *self.reacquisition_routes,
            *self.scaffolds,
            *self.recovery_protocols,
        )
        for record in all_records:
            record_pins = (
                record.scope_fingerprint,
                record.binding_revision,
                record.protected_horizon_id,
            )
            if record_pins != pins:
                raise ValueError("registered retention records require exact package pins")
        owned_keys = {reference.key for reference in package.owned_refs}
        for route in (
            *self.direct_use_routes,
            *self.reconstruction_routes,
            *self.consequence_evaluation_routes,
            *self.reacquisition_routes,
        ):
            if not {reference.key for reference in route.source_refs} <= owned_keys:
                raise ValueError("route sources must be among package-owned references")
        for scaffold in self.scaffolds:
            scaffold_refs = {
                reference.key
                for reference in (
                    *scaffold.cue_refs,
                    *scaffold.boundary_refs,
                    *scaffold.failure_refs,
                )
            }
            if not scaffold_refs <= owned_keys:
                raise ValueError("scaffold sources must be among package-owned references")
            procedural_record_ids = {
                reference.record_id
                for reference in package.owned_refs
                if reference.owner is MemoryOwner.PROCEDURAL
            }
            if not set(scaffold.ordered_probe_ids) <= procedural_record_ids:
                raise ValueError(
                    "ordered scaffold probes must resolve to package-owned procedural refs"
                )
        scaffold_by_id = {scaffold.id: scaffold for scaffold in self.scaffolds}
        protocol_by_id = {protocol.id: protocol for protocol in self.recovery_protocols}
        for route in self.reacquisition_routes:
            if route.reacquisition_scaffold_id not in scaffold_by_id:
                raise ValueError("reacquisition route references an unregistered scaffold")
            if route.recovery_protocol_id not in protocol_by_id:
                raise ValueError("reacquisition route references an unregistered protocol")
        return self


class MemoryReconstructionCandidate(FrozenModel):
    """Generated working detail kept separate from G1 return-bound reconstruction."""

    schema_version: SchemaVersion = 1
    id: Identifier
    rank: NonNegativeInt
    retention_package_ids: tuple[Identifier, ...]
    generated_working_structure: JsonValue
    protected_consequence_class_id: Identifier
    historical_fact_ids: tuple[Identifier, ...] = ()
    generated_detail_ids: tuple[Identifier, ...] = ()

    @field_validator("generated_working_structure")
    @classmethod
    def freeze_working_structure(cls, value: JsonValue) -> JsonValue:
        return freeze_json(value)

    @model_validator(mode="after")
    def validate_candidate(self) -> MemoryReconstructionCandidate:
        if not self.retention_package_ids:
            raise ValueError("memory reconstruction requires a retention package source")
        for field_name, values in (
            ("reconstruction package ids", self.retention_package_ids),
            ("reconstruction historical facts", self.historical_fact_ids),
            ("reconstruction generated details", self.generated_detail_ids),
        ):
            _require_canonical_ids(values, field_name=field_name)
        if set(self.historical_fact_ids) & set(self.generated_detail_ids):
            raise ValueError("generated reconstruction detail is not historical fact")
        return self


class MemoryReconstructionSet(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    cue_ids: tuple[Identifier, ...]
    scope_fingerprint: Identifier
    binding_revision: Identifier
    protected_horizon_id: Identifier
    candidates: tuple[MemoryReconstructionCandidate, ...]

    @model_validator(mode="after")
    def validate_set(self) -> MemoryReconstructionSet:
        _require_canonical_ids(self.cue_ids, field_name="reconstruction cues")
        order = tuple((candidate.rank, candidate.id) for candidate in self.candidates)
        if tuple(sorted(order)) != order:
            raise ValueError("memory reconstruction candidates require stable rank/id order")
        ids = tuple(candidate.id for candidate in self.candidates)
        if len(set(ids)) != len(ids):
            raise ValueError("memory reconstruction candidates must be deduplicated")
        return self

    @property
    def ambiguous(self) -> bool:
        return len(self.candidates) > 1


class RecoveryBranch(StrEnum):
    BASELINE = "baseline"
    RETAINED = "retained"


class ReacquisitionRequest(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    parent_inquiry_id: Identifier
    child_inquiry_id: Identifier
    branch: RecoveryBranch
    pins: RecoveryPins
    child_manifest_artifact: ArtifactRef
    child_inquiry_manifest_artifact: ArtifactRef
    child_context_digest: Sha256Digest
    child_policy_version: Identifier
    retention_package_id: Identifier | None = None
    scaffold_id: Identifier | None = None

    @model_validator(mode="after")
    def validate_request(self) -> ReacquisitionRequest:
        if self.parent_inquiry_id == self.child_inquiry_id:
            raise ValueError("reacquisition child inquiry must be distinct from its parent")
        retained_refs = (self.retention_package_id, self.scaffold_id)
        if self.branch is RecoveryBranch.BASELINE and any(retained_refs):
            raise ValueError("baseline reacquisition cannot use retained package or scaffold")
        if self.branch is RecoveryBranch.RETAINED and not all(retained_refs):
            raise ValueError("retained reacquisition requires package and scaffold")
        return self


class ReacquisitionChildManifest(FrozenModel):
    """Strict CAS payload binding a child inquiry to one parent recovery request."""

    schema_version: SchemaVersion = 1
    parent_inquiry_id: Identifier
    request_id: Identifier
    child_inquiry_id: Identifier
    pins: RecoveryPins
    context_digest: Sha256Digest
    policy_version: Identifier
    inquiry_manifest_artifact: ArtifactRef

    @model_validator(mode="after")
    def validate_manifest(self) -> ReacquisitionChildManifest:
        if self.parent_inquiry_id == self.child_inquiry_id:
            raise ValueError("reacquisition child manifest must identify a distinct child")
        return self


class ReacquisitionInquiryLink(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    request_id: Identifier
    parent_inquiry_id: Identifier
    child_inquiry_id: Identifier
    child_start_sequence: Literal[1] = 1
    child_start_event_id: Identifier
    child_start_event_digest: Sha256Digest
    child_prefix_sequence: PositiveInt
    child_prefix_digest: Sha256Digest
    child_manifest_artifact: ArtifactRef
    child_context_digest: Sha256Digest

    @model_validator(mode="after")
    def validate_link(self) -> ReacquisitionInquiryLink:
        if self.parent_inquiry_id == self.child_inquiry_id:
            raise ValueError("reacquisition link must name a distinct child inquiry")
        return self


class RecoveryObservation(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    branch: RecoveryBranch
    reacquisition_request_id: Identifier
    child_inquiry_id: Identifier
    child_prefix_sequence: PositiveInt
    child_prefix_digest: Sha256Digest
    retention_package_id: Identifier | None
    pins: RecoveryPins
    costs: CostVector
    logical_probe_ids: tuple[Identifier, ...] = ()
    effect_request_ids: tuple[Identifier, ...] = ()
    measurement_check: CheckReference
    competence_established: bool
    competence_check: CheckReference | None = None

    @model_validator(mode="after")
    def validate_observation(self) -> RecoveryObservation:
        if self.branch is RecoveryBranch.BASELINE and self.retention_package_id is not None:
            raise ValueError("baseline recovery observation cannot name retained material")
        if self.branch is RecoveryBranch.RETAINED and self.retention_package_id is None:
            raise ValueError("retained recovery observation requires a retention package")
        if self.competence_established and self.competence_check is None:
            raise ValueError("established competence requires an independent check reference")
        if not self.logical_probe_ids and not self.effect_request_ids:
            raise ValueError("reacquisition observations require measured probe or effect work")
        _require_canonical_ids(self.logical_probe_ids, field_name="measured logical probe ids")
        _require_canonical_ids(
            self.effect_request_ids,
            field_name="measured effect request ids",
        )
        if self.costs.axis_signature != self.pins.budget.axis_signature:
            raise ValueError("observed costs must use the exact recovery-budget axes")
        for observed, budget in zip(
            self.costs.coordinates,
            self.pins.budget.coordinates,
            strict=True,
        ):
            if observed.numerator * budget.denominator > budget.numerator * observed.denominator:
                raise ValueError("observed recovery cost exceeds the pinned budget")
        exact_count_axes = {
            "effects": len(self.effect_request_ids),
            "logical_probes": len(self.logical_probe_ids),
        }
        for coordinate in self.costs.coordinates:
            expected_count = exact_count_axes.get(coordinate.axis.id)
            if expected_count is not None and (
                coordinate.denominator != 1 or coordinate.numerator != expected_count
            ):
                raise ValueError(
                    f"{coordinate.axis.id} cost must equal its exact cited child-record count"
                )
        return self

    @property
    def measurement_proposition_id(self) -> str:
        """Fingerprint every measured fact while excluding its checker reference.

        The checker must bind to this value rather than the freely chosen record ID.
        Reusing a valid check after changing a cost, child prefix, measured probe, or
        effect therefore fails closed.
        """

        return content_fingerprint(
            "rci.recovery-observation-measurement.v1",
            self.model_dump(mode="json", exclude={"measurement_check"}),
        )


class RecoveryFrontierPoint(FrozenModel):
    schema_version: SchemaVersion = 1
    observation_id: Identifier
    costs: CostVector


class RecoveryFrontier(FrozenModel):
    schema_version: SchemaVersion = 1
    branch: RecoveryBranch
    pins: RecoveryPins
    source_observation_ids: tuple[Identifier, ...]
    points: tuple[RecoveryFrontierPoint, ...]

    @model_validator(mode="after")
    def validate_frontier(self) -> RecoveryFrontier:
        _require_canonical_ids(
            self.source_observation_ids,
            field_name="frontier source observations",
        )
        point_ids = tuple(point.observation_id for point in self.points)
        if len(set(point_ids)) != len(point_ids):
            raise ValueError("frontier points must be deduplicated")
        if not set(point_ids) <= set(self.source_observation_ids):
            raise ValueError("frontier points must refer to source observations")
        return self


class RecoveryComparisonOutcome(StrEnum):
    STRICT_ADVANTAGE = "strict_advantage"
    NO_ADVANTAGE = "no_advantage"
    INCOMPARABLE = "incomparable"


class FrontierCoverage(FrozenModel):
    schema_version: SchemaVersion = 1
    baseline_observation_id: Identifier
    retained_observation_id: Identifier
    strict: bool


class RecoveryComparison(FrozenModel):
    schema_version: SchemaVersion = 1
    id: Identifier
    baseline_frontier: RecoveryFrontier
    retained_frontier: RecoveryFrontier
    outcome: RecoveryComparisonOutcome
    coverage: tuple[FrontierCoverage, ...] = ()
    comparison_check: CheckReference
    standing: Literal["provisional_soft"] = "provisional_soft"

    @model_validator(mode="after")
    def validate_comparison_shape(self) -> RecoveryComparison:
        if self.baseline_frontier.branch is not RecoveryBranch.BASELINE:
            raise ValueError("comparison baseline frontier has the wrong branch")
        if self.retained_frontier.branch is not RecoveryBranch.RETAINED:
            raise ValueError("comparison retained frontier has the wrong branch")
        baseline_ids = {point.observation_id for point in self.baseline_frontier.points}
        retained_ids = {point.observation_id for point in self.retained_frontier.points}
        coverage_baseline_ids = [item.baseline_observation_id for item in self.coverage]
        if len(set(coverage_baseline_ids)) != len(coverage_baseline_ids):
            raise ValueError("each baseline frontier point may have one coverage witness")
        if any(
            item.baseline_observation_id not in baseline_ids
            or item.retained_observation_id not in retained_ids
            for item in self.coverage
        ):
            raise ValueError("comparison coverage must refer to its frontier points")
        # Local import avoids a model/algorithm import cycle while still making it
        # impossible to instantiate a record whose declared outcome contradicts the
        # exact integer-arithmetic checker.
        from rci.memory.checks import check_recovery_comparison

        valid, reason = check_recovery_comparison(self)
        if not valid:
            raise ValueError(reason)
        return self

    @property
    def comparison_proposition_id(self) -> str:
        """Fingerprint the checked arithmetic while excluding its check reference."""

        return content_fingerprint(
            "rci.recovery-comparison.v1",
            self.model_dump(mode="json", exclude={"comparison_check"}),
        )
