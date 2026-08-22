"""Strict G3A-H records for exact history-state representations.

The event-folded :class:`InquiryState` is deliberately absent from the carrier-role
enum.  These records describe derived representation contracts; they never replace
the replay-complete aggregate.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import model_validator

from rci.core.model import ArtifactRef, FrozenModel, Identifier, Sha256Digest
from rci.warrant.models import CheckReference


class CarrierRole(StrEnum):
    CONFIGURATION = "configuration"
    REALIZED_HISTORY = "realized_history"
    PRIOR_RETAINED_STATE = "prior_retained_state"
    OTHER_DECLARED = "other_declared"


class HistoryDerivationStatus(StrEnum):
    DERIVED = "derived"
    NOT_DEFINED = "not_defined"
    INCOMPLETE = "incomplete"
    FAILED = "failed"


class ExactClaimKind(StrEnum):
    CONSEQUENCE_SUFFICIENT = "consequence_sufficient"
    COARSEST_EXACT_QUOTIENT = "coarsest_exact_quotient"
    EXECUTABLE_RETAINED_STATE = "executable_retained_state"


class ValidationProperty(StrEnum):
    CONSEQUENCE_FACTORIZATION = "consequence_factorization"
    EXACT_EQUIVALENCE = "exact_equivalence"
    CONTINUATION_COMPATIBILITY = "continuation_compatibility"
    RECURSIVE_UPDATE = "recursive_update"
    DETERMINATION_DESCENT = "determination_descent"
    RESIDUE_COMPLETENESS = "residue_completeness"


class ValidationOutcome(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    NOT_CLAIMED = "not_claimed"


class RepresentationGainKind(StrEnum):
    BREAKER = "breaker"
    SEPARATOR = "separator"
    QUOTIENT = "quotient"
    SCOPE = "scope"
    COMPOSITION = "composition"
    RECOVERY = "recovery"
    WARRANT = "warrant"


class SuccessorDisposition(StrEnum):
    REPLACE = "replace"
    KEEP = "keep"
    INCOMPARABLE = "incomparable"
    REJECT = "reject"


class ReopeningOutcome(StrEnum):
    RECOVERABLE = "recoverable"
    REACQUISITION_REQUIRED = "reacquisition_required"
    UNKNOWN = "unknown"


def _canonical(values: tuple[str, ...], label: str) -> None:
    if len(set(values)) != len(values) or tuple(sorted(values)) != values:
        raise ValueError(f"{label} must be unique and canonically ordered")


class CarrierContract(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    role: CarrierRole
    schema_id: Identifier
    binding_revision: Identifier


class BindingCarrierManifest(FrozenModel):
    """Versioned binding declaration; it does not mutate sealed InquiryStarted."""

    schema_version: Literal[1] = 1
    id: Identifier
    binding_revision: Identifier
    configuration_carrier: CarrierContract
    realized_history_carrier: CarrierContract
    other_carriers: tuple[CarrierContract, ...] = ()
    history_derivation_policy_id: Identifier
    configuration_projection_policy_id: Identifier
    manifest_artifact: ArtifactRef
    provenance_refs: tuple[Identifier, ...]

    @model_validator(mode="after")
    def validate_manifest(self) -> BindingCarrierManifest:
        if self.configuration_carrier.role is not CarrierRole.CONFIGURATION:
            raise ValueError("configuration carrier must declare the configuration role")
        if self.realized_history_carrier.role is not CarrierRole.REALIZED_HISTORY:
            raise ValueError("history carrier must declare the realized-history role")
        carriers = (self.configuration_carrier, self.realized_history_carrier, *self.other_carriers)
        if any(item.binding_revision != self.binding_revision for item in carriers):
            raise ValueError("all carrier contracts must pin the manifest binding revision")
        if any(
            item.role in {CarrierRole.CONFIGURATION, CarrierRole.REALIZED_HISTORY}
            for item in self.other_carriers
        ):
            raise ValueError("configuration and realized-history roles have one explicit owner")
        ids = tuple(item.id for item in carriers)
        if len(set(ids)) != len(ids):
            raise ValueError("carrier contract identities must be unique")
        if not self.provenance_refs:
            raise ValueError("carrier manifests require provenance")
        _canonical(self.provenance_refs, "carrier-manifest provenance")
        return self


class RealizedHistoryDerivation(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    carrier_manifest_id: Identifier
    source_ledger_sequence: int
    source_prefix_digest: Sha256Digest
    status: HistoryDerivationStatus
    history_artifact: ArtifactRef | None = None
    realized_extension_ids: tuple[Identifier, ...] = ()
    derivation_check: CheckReference | None = None
    diagnostics_artifact: ArtifactRef | None = None

    @model_validator(mode="after")
    def validate_derivation(self) -> RealizedHistoryDerivation:
        if self.source_ledger_sequence < 1:
            raise ValueError("history derivation requires a committed ledger prefix")
        if (self.status is HistoryDerivationStatus.DERIVED) != (self.history_artifact is not None):
            raise ValueError("only a derived history may carry a history artifact")
        if self.status is HistoryDerivationStatus.DERIVED and not self.realized_extension_ids:
            raise ValueError("derived history must identify binding-defined realized extensions")
        if (self.status is HistoryDerivationStatus.DERIVED) != (self.derivation_check is not None):
            raise ValueError("only a derived history requires an independent derivation check")
        if len(set(self.realized_extension_ids)) != len(self.realized_extension_ids):
            raise ValueError("realized extensions must be unique and ordered by binding semantics")
        return self


class CompressionContract(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    carrier_manifest_id: Identifier
    source_carrier_id: Identifier
    target_carrier: CarrierContract
    binding_revision: Identifier
    scope_fingerprint: Sha256Digest
    protected_horizon_id: Identifier
    continuation_operation_ids: tuple[Identifier, ...]
    consequence_query_ids: tuple[Identifier, ...]
    equality_semantics_id: Identifier
    recovery_semantics_ids: tuple[Identifier, ...]
    claim_kinds: tuple[ExactClaimKind, ...]
    representation_policy_id: Identifier
    provenance_refs: tuple[Identifier, ...]

    @model_validator(mode="after")
    def validate_contract(self) -> CompressionContract:
        if self.target_carrier.role not in {
            CarrierRole.PRIOR_RETAINED_STATE,
            CarrierRole.OTHER_DECLARED,
        }:
            raise ValueError("compression target must explicitly declare a retained/other role")
        if self.target_carrier.binding_revision != self.binding_revision:
            raise ValueError("target carrier binding must match the compression contract")
        if not self.consequence_query_ids or not self.claim_kinds or not self.provenance_refs:
            raise ValueError("exact compression contracts require queries, claims, and provenance")
        for values, label in (
            (self.continuation_operation_ids, "continuation operations"),
            (self.consequence_query_ids, "consequence queries"),
            (self.recovery_semantics_ids, "recovery semantics"),
            (tuple(item.value for item in self.claim_kinds), "exact claim kinds"),
            (self.provenance_refs, "compression provenance"),
        ):
            _canonical(values, label)
        executable = ExactClaimKind.EXECUTABLE_RETAINED_STATE in self.claim_kinds
        if executable and not self.continuation_operation_ids:
            raise ValueError("executable retained state requires an admitted continuation family")
        return self


class ExactPropertyValidation(FrozenModel):
    property: ValidationProperty
    outcome: ValidationOutcome
    proposition_id: Identifier | None = None
    check: CheckReference | None = None
    witness_artifact: ArtifactRef | None = None

    @model_validator(mode="after")
    def validate_property(self) -> ExactPropertyValidation:
        checked = self.outcome is not ValidationOutcome.NOT_CLAIMED
        if checked != (self.proposition_id is not None and self.check is not None):
            raise ValueError("claimed validation properties require an exact independent check")
        if self.outcome is ValidationOutcome.INVALID and self.witness_artifact is None:
            raise ValueError("invalid validation requires a counterexample artifact")
        return self


class CompressionValidation(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    contract_id: Identifier
    contract_fingerprint: Sha256Digest
    properties: tuple[ExactPropertyValidation, ...]
    validator_id: Identifier
    validator_version: Identifier
    validation_artifact: ArtifactRef

    @model_validator(mode="after")
    def validate_validation(self) -> CompressionValidation:
        names = tuple(item.property for item in self.properties)
        if len(names) != len(set(names)):
            raise ValueError("each validation property may appear exactly once")
        if set(names) != set(ValidationProperty):
            raise ValueError("compression validation must disposition every exact property")
        return self

    @property
    def valid(self) -> bool:
        return all(item.outcome is not ValidationOutcome.INVALID for item in self.properties)


class ExactCompressionLicense(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    contract_id: Identifier
    validation_id: Identifier
    warrant_decision_id: Identifier
    policy_version: Identifier
    granted_capability_ids: tuple[Identifier, ...]
    predecessor_license_id: Identifier | None = None

    @model_validator(mode="after")
    def validate_license(self) -> ExactCompressionLicense:
        if not self.granted_capability_ids:
            raise ValueError("exact licenses require at least one explicit capability")
        _canonical(self.granted_capability_ids, "licensed capabilities")
        if self.predecessor_license_id == self.id:
            raise ValueError("a compression license cannot succeed itself")
        return self


class PathResidue(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    contract_id: Identifier
    source_history_derivation_id: Identifier
    residue_artifact: ArtifactRef
    distinction_ids: tuple[Identifier, ...]
    recovery_route_ids: tuple[Identifier, ...] = ()
    provenance_refs: tuple[Identifier, ...]

    @model_validator(mode="after")
    def validate_residue(self) -> PathResidue:
        if not self.distinction_ids or not self.provenance_refs:
            raise ValueError("path residue requires distinctions and provenance")
        for values, label in (
            (self.distinction_ids, "path distinctions"),
            (self.recovery_route_ids, "path recovery routes"),
            (self.provenance_refs, "path-residue provenance"),
        ):
            _canonical(values, label)
        return self


class CompressionApplication(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    license_id: Identifier
    source_history_derivation_id: Identifier
    source_artifact: ArtifactRef
    retained_state_artifact: ArtifactRef
    retained_state_fingerprint: Sha256Digest
    path_residue_ids: tuple[Identifier, ...] = ()
    applied_representation_id: Identifier
    provenance_refs: tuple[Identifier, ...]

    @model_validator(mode="after")
    def validate_application(self) -> CompressionApplication:
        for values, label in (
            (self.path_residue_ids, "application path residues"),
            (self.provenance_refs, "application provenance"),
        ):
            _canonical(values, label)
        if not self.provenance_refs:
            raise ValueError("compression applications require provenance")
        return self


class RecoveryLicense(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    compression_application_id: Identifier
    retention_package_id: Identifier
    route_id: Identifier
    recovery_semantics_id: Identifier
    warrant_decision_id: Identifier
    policy_version: Identifier


class RetentionCapabilityLink(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    retention_package_id: Identifier
    route_id: Identifier
    compression_application_id: Identifier
    recovery_license_id: Identifier


class RepresentationSuccessorDecision(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    incumbent_license_id: Identifier
    candidate_license_id: Identifier
    disposition: SuccessorDisposition
    preserved_capability_ids: tuple[Identifier, ...]
    explicitly_disposed_capability_ids: tuple[Identifier, ...] = ()
    gain_kinds: tuple[RepresentationGainKind, ...] = ()
    warrant_decision_id: Identifier | None = None
    reason: str

    @model_validator(mode="after")
    def validate_successor(self) -> RepresentationSuccessorDecision:
        for values, label in (
            (self.preserved_capability_ids, "preserved capabilities"),
            (self.explicitly_disposed_capability_ids, "disposed capabilities"),
            (tuple(item.value for item in self.gain_kinds), "representation gains"),
        ):
            _canonical(values, label)
        if self.disposition is SuccessorDisposition.REPLACE:
            if not self.gain_kinds or self.warrant_decision_id is None:
                raise ValueError("replacement requires typed gain and independent warrant")
        elif self.warrant_decision_id is not None:
            raise ValueError("only a replacement disposition may carry replacement warrant")
        return self


class RepresentationReopening(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    license_id: Identifier
    prior_horizon_id: Identifier
    expanded_horizon_id: Identifier
    factorization_failure_check: CheckReference
    counterexample_artifact: ArtifactRef
    outcome: ReopeningOutcome
    path_residue_id: Identifier | None = None
    recovery_license_id: Identifier | None = None

    @model_validator(mode="after")
    def validate_reopening(self) -> RepresentationReopening:
        if self.prior_horizon_id == self.expanded_horizon_id:
            raise ValueError("reopening requires a materially different protected horizon")
        if self.outcome is ReopeningOutcome.RECOVERABLE and self.path_residue_id is None:
            raise ValueError("recoverable reopening requires exact path residue")
        if (
            self.outcome is ReopeningOutcome.REACQUISITION_REQUIRED
            and self.recovery_license_id is None
        ):
            raise ValueError("reacquisition reopening requires a recovery license")
        if self.outcome is ReopeningOutcome.UNKNOWN and (
            self.path_residue_id is not None or self.recovery_license_id is not None
        ):
            raise ValueError("Unknown reopening cannot claim unavailable recovery material")
        return self


class RetainedStateView(FrozenModel):
    """Derived join; never an independently writable authority."""

    compression_application_id: Identifier
    contract_id: Identifier
    license_id: Identifier
    source_carrier_id: Identifier
    target_carrier_id: Identifier
    retained_state_artifact: ArtifactRef
    capability_ids: tuple[Identifier, ...]
    standing: Literal["licensed"] = "licensed"
