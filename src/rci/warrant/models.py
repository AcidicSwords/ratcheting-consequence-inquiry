"""Immutable support, evidence, and warranted-lemma records."""

from __future__ import annotations

from enum import StrEnum

from pydantic import model_validator

from rci.claims.models import FrozenModel, Scope
from rci.core.model import ArtifactRef


class CheckerVerdict(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    INDETERMINATE = "indeterminate"
    TIMEOUT = "timeout"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


class WarrantClass(StrEnum):
    NONE = "none"
    SOFT = "soft"
    SOLVER_TRUSTED = "solver_trusted"
    HARD = "hard"


class SupportStanding(StrEnum):
    """Current applicability of an immutable support or nogood record."""

    STANDING = "standing"
    WITHDRAWN = "withdrawn"


class EvidenceKind(StrEnum):
    MODEL_OUTPUT = "model_output"
    REIFICATION = "reification"
    HEURISTIC = "heuristic"
    RETRIEVAL = "retrieval"
    OBSERVATION = "observation"
    INDEPENDENT_WITNESS = "independent_witness"
    EXHAUSTIVE_UNSAT = "exhaustive_unsat"
    Z3_UNSAT = "z3_unsat"


class PropositionKind(StrEnum):
    EXISTENTIAL = "existential"
    UNIVERSAL = "universal"
    RELATION = "relation"


class Applicability(FrozenModel):
    condition_id: str
    required_context_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_applicability(self) -> Applicability:
        if not self.condition_id:
            raise ValueError("applicability condition identity is required")
        if len(set(self.required_context_ids)) != len(self.required_context_ids):
            raise ValueError("applicability context ids must be unique")
        return self


class CheckReference(FrozenModel):
    """A non-authoritative pointer to an aggregate-owned checker record."""

    evidence_id: str
    checker_verdict_id: str

    @model_validator(mode="after")
    def validate_reference(self) -> CheckReference:
        if not self.evidence_id or not self.checker_verdict_id:
            raise ValueError("check references require evidence and checker-verdict identities")
        return self


class SupportEnvironment(FrozenModel):
    """A declared assumption environment with independently checked realizability."""

    id: str
    scope_fingerprint: str
    binding_revision: str
    assumption_ids: tuple[str, ...]
    finite_universe_hash: str | None
    realizability_check: CheckReference

    @model_validator(mode="after")
    def validate_environment(self) -> SupportEnvironment:
        if not self.id or not self.scope_fingerprint or not self.binding_revision:
            raise ValueError("support environment identity, scope, and binding are required")
        if len(set(self.assumption_ids)) != len(self.assumption_ids):
            raise ValueError("support assumptions must be unique")
        if tuple(sorted(self.assumption_ids)) != self.assumption_ids:
            raise ValueError("support assumptions must use canonical order")
        return self

    @property
    def assumptions(self) -> frozenset[str]:
        return frozenset(self.assumption_ids)


class Nogood(FrozenModel):
    id: str
    scope_fingerprint: str
    binding_revision: str
    finite_universe_hash: str | None
    policy_version: str
    incompatible_assumption_ids: tuple[str, ...]
    check: CheckReference
    warrant_decision_id: str
    reason: str

    @model_validator(mode="after")
    def validate_nogood(self) -> Nogood:
        if (
            any(
                not value
                for value in (
                    self.id,
                    self.scope_fingerprint,
                    self.binding_revision,
                    self.policy_version,
                    self.warrant_decision_id,
                )
            )
            or not self.incompatible_assumption_ids
        ):
            raise ValueError(
                "nogoods require identity, scope, binding, policy, warrant, and assumptions"
            )
        if not self.reason:
            raise ValueError("nogoods require a reason")
        if len(set(self.incompatible_assumption_ids)) != len(self.incompatible_assumption_ids):
            raise ValueError("nogood assumptions must be unique")
        if tuple(sorted(self.incompatible_assumption_ids)) != self.incompatible_assumption_ids:
            raise ValueError("nogood assumptions must use canonical order")
        return self


class SupportRouteStandingChange(FrozenModel):
    """Append-only standing history for one immutable support route."""

    id: str
    support_route_id: str
    standing: SupportStanding
    reason: str
    predecessor_id: str | None = None

    @model_validator(mode="after")
    def validate_change(self) -> SupportRouteStandingChange:
        if not self.id or not self.support_route_id or not self.reason:
            raise ValueError("support-route standing changes require identity, route, and reason")
        if self.id == self.predecessor_id:
            raise ValueError("a standing change cannot succeed itself")
        return self


class NogoodStandingChange(FrozenModel):
    """Append-only standing history for one immutable warranted nogood."""

    id: str
    nogood_id: str
    standing: SupportStanding
    reason: str
    predecessor_id: str | None = None

    @model_validator(mode="after")
    def validate_change(self) -> NogoodStandingChange:
        if not self.id or not self.nogood_id or not self.reason:
            raise ValueError("nogood standing changes require identity, nogood, and reason")
        if self.id == self.predecessor_id:
            raise ValueError("a standing change cannot succeed itself")
        return self


class SupportRoute(FrozenModel):
    """One exposed route by which a conclusion may stand."""

    id: str
    conclusion_id: str
    environment: SupportEnvironment
    required_dependency_ids: tuple[str, ...]
    open_dependency_ids: tuple[str, ...]
    certificate_check: CheckReference
    warrant_refs: tuple[str, ...] = ()
    justification_refs: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_route(self) -> SupportRoute:
        if not self.id or not self.conclusion_id:
            raise ValueError("support route and conclusion identity are required")
        for collection in (
            self.required_dependency_ids,
            self.open_dependency_ids,
            self.warrant_refs,
            self.justification_refs,
            self.provenance_refs,
        ):
            if len(set(collection)) != len(collection):
                raise ValueError("support-route reference collections must be unique")
        if tuple(sorted(self.required_dependency_ids)) != self.required_dependency_ids:
            raise ValueError("required dependencies must use canonical order")
        if tuple(sorted(self.open_dependency_ids)) != self.open_dependency_ids:
            raise ValueError("open dependencies must use canonical order")
        if not set(self.open_dependency_ids) <= set(self.required_dependency_ids):
            raise ValueError("open dependencies must be a subset of required dependencies")
        return self


class Evidence(FrozenModel):
    """Inert evidence material; it carries no checker or warrant authority."""

    id: str
    kind: EvidenceKind
    proposition_id: str
    proposition_kind: PropositionKind
    scope_fingerprint: str
    artifact: ArtifactRef
    closed_finite_universe: bool = False
    finite_universe_hash: str | None = None

    @model_validator(mode="after")
    def validate_evidence(self) -> Evidence:
        if not self.id or not self.proposition_id or not self.scope_fingerprint:
            raise ValueError("evidence identity, proposition, and scope are required")
        if self.closed_finite_universe and self.finite_universe_hash is None:
            raise ValueError("closed-finite evidence requires an exact universe hash")
        return self


class CheckerVerdictRecord(FrozenModel):
    """An immutable independent check over one exact recorded evidence artifact."""

    id: str
    evidence_id: str
    evidence_artifact: ArtifactRef
    proposition_id: str
    proposition_kind: PropositionKind
    scope_fingerprint: str
    checker_id: str
    checker_version: str
    verdict: CheckerVerdict
    verdict_artifact: ArtifactRef
    certificate_artifact: ArtifactRef | None = None

    @model_validator(mode="after")
    def validate_verdict(self) -> CheckerVerdictRecord:
        if any(
            not value
            for value in (
                self.id,
                self.evidence_id,
                self.proposition_id,
                self.scope_fingerprint,
                self.checker_id,
                self.checker_version,
            )
        ):
            raise ValueError(
                "checker verdict identity, evidence, proposition, scope, and checker are required"
            )
        if self.verdict is CheckerVerdict.VALID and self.certificate_artifact is None:
            raise ValueError("valid checker verdicts require an exact certificate artifact")
        return self


class LemmaVersion(FrozenModel):
    """Authoritative immutable semantic/version object, independent of support state."""

    id: str
    relation_id: str
    proposition_kind: PropositionKind
    scope: Scope
    applicability: Applicability
    source_claim_ids: tuple[str, ...]
    predecessor_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_version(self) -> LemmaVersion:
        if not self.id or not self.relation_id:
            raise ValueError("lemma version and relation identity are required")
        if self.id in self.predecessor_refs:
            raise ValueError("a lemma version cannot succeed itself")
        if len(set(self.predecessor_refs)) != len(self.predecessor_refs):
            raise ValueError("predecessor references must be unique")
        if len(set(self.source_claim_ids)) != len(self.source_claim_ids):
            raise ValueError("source claim references must be unique")
        return self


class LemmaSupport(FrozenModel):
    """Authoritative support/warrant state referring to one semantic lemma version."""

    lemma_version_id: str
    policy_version: str
    support_routes: tuple[SupportRoute, ...]
    historical_support_routes: tuple[SupportRoute, ...] = ()
    warrant_class: WarrantClass
    certificate_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]

    @model_validator(mode="after")
    def validate_support(self) -> LemmaSupport:
        if not self.policy_version:
            raise ValueError("lemma support requires an exact warrant-policy version")
        if not self.support_routes:
            raise ValueError("lemma support requires at least one route")
        route_ids = [route.id for route in self.all_support_routes]
        if len(set(route_ids)) != len(route_ids):
            raise ValueError("support route identities must be unique")
        if any(route.conclusion_id != self.lemma_version_id for route in self.all_support_routes):
            raise ValueError("every support route must name its lemma conclusion")
        environments = [route.environment.assumptions for route in self.support_routes]
        for index, left in enumerate(environments):
            for right in environments[index + 1 :]:
                if left < right or right < left:
                    raise ValueError("support environments must form a minimal antichain")
        if any(
            not any(
                current.environment.assumptions <= historical.environment.assumptions
                for current in self.support_routes
            )
            for historical in self.historical_support_routes
        ):
            raise ValueError("historical support routes must be initially dominated or equivalent")
        for collection in (self.certificate_refs, self.provenance_refs):
            if len(set(collection)) != len(collection):
                raise ValueError("lemma support references must be unique")
        return self

    @property
    def all_support_routes(self) -> tuple[SupportRoute, ...]:
        return (*self.support_routes, *self.historical_support_routes)


class WarrantedLemma(FrozenModel):
    """A joined read model; its two authoritative owners remain explicit."""

    version: LemmaVersion
    support: LemmaSupport

    @model_validator(mode="after")
    def validate_join(self) -> WarrantedLemma:
        if self.version.id != self.support.lemma_version_id:
            raise ValueError("lemma version and support owner do not refer to one object")
        for route in self.support.all_support_routes:
            if (
                route.environment.scope_fingerprint != self.version.scope.fingerprint
                or route.environment.binding_revision != self.version.scope.binding_revision
                or route.environment.finite_universe_hash != self.version.scope.finite_universe_hash
            ):
                raise ValueError(
                    "support routes must remain inside the lemma's exact scope/binding/universe"
                )
        return self

    @property
    def id(self) -> str:
        return self.version.id


class WarrantDecisionRecord(FrozenModel):
    """Persistable policy decision kept separate from checking and promotion."""

    id: str
    evidence_id: str
    checker_verdict_id: str
    proposition_id: str
    proposition_kind: PropositionKind
    scope_fingerprint: str
    warrant_class: WarrantClass
    reason: str
    policy_version: str

    @model_validator(mode="after")
    def validate_decision(self) -> WarrantDecisionRecord:
        if any(
            not value
            for value in (
                self.id,
                self.evidence_id,
                self.checker_verdict_id,
                self.proposition_id,
                self.scope_fingerprint,
                self.reason,
                self.policy_version,
            )
        ):
            raise ValueError("warrant decision identity, scope, reason, and policy are required")
        return self


class PromotionLink(FrozenModel):
    """The immutable link creating an L3 view without mutating source claims."""

    id: str
    lemma_version_id: str
    source_claim_ids: tuple[str, ...]
    warrant_decision_id: str

    @model_validator(mode="after")
    def validate_link(self) -> PromotionLink:
        if not self.id or not self.lemma_version_id or not self.warrant_decision_id:
            raise ValueError("promotion link identity, lemma, and decision are required")
        if not self.source_claim_ids:
            raise ValueError("promotion must preserve at least one source claim")
        if len(set(self.source_claim_ids)) != len(self.source_claim_ids):
            raise ValueError("promotion source claim references must be unique")
        return self


class ActiveLemmaView(FrozenModel):
    """Regenerable working view, never a second semantic truth store."""

    lemma_version_id: str
    relation_id: str
    standing_support_route_id: str
    standing_support_route_ids: tuple[str, ...]
    scope_fingerprint: str
    binding_revision: str
    finite_universe_hash: str | None
    policy_version: str

    @model_validator(mode="after")
    def validate_routes(self) -> ActiveLemmaView:
        if not self.standing_support_route_ids:
            raise ValueError("active lemma views require at least one standing minimal route")
        if self.standing_support_route_id != self.standing_support_route_ids[0]:
            raise ValueError("the primary standing route must be the first minimal route")
        if len(set(self.standing_support_route_ids)) != len(self.standing_support_route_ids):
            raise ValueError("active minimal support route identities must be unique")
        return self


class TheorySelector(FrozenModel):
    """Exact non-authoritative pins used to derive a current theory view."""

    scope_fingerprint: str
    binding_revision: str
    finite_universe_hash: str | None
    policy_version: str
    current_assumption_ids: tuple[str, ...] = ()
    current_context_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_selector(self) -> TheorySelector:
        if not self.scope_fingerprint or not self.binding_revision or not self.policy_version:
            raise ValueError("theory selection requires exact scope, binding, and policy pins")
        for collection in (self.current_assumption_ids, self.current_context_ids):
            if len(set(collection)) != len(collection):
                raise ValueError("theory selector collections must be unique")
            if tuple(sorted(collection)) != collection:
                raise ValueError("theory selector collections must use canonical order")
        return self
