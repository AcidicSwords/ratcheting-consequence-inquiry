"""Pure deterministic G2B policies."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from math import ceil

from rci.claims.models import (
    Claim,
    ClaimAssessment,
    Conflict,
    Obligation,
    ObligationStatus,
    Provenance,
    Residual,
    Scope,
    content_fingerprint,
)
from rci.core.effects import CounterexampleResult
from rci.core.serialization import canonical_json_bytes, sha256_digest
from rci.learning.models import (
    ConsolidationCheckpoint,
    ConsolidationPolicy,
    ConsolidationSource,
    ConsolidationSourceRole,
    ConsolidationStatus,
    ProbeEvaluation,
    ProbeEvaluationProtocol,
    ProbeSample,
    SemanticFieldEvaluation,
    SemanticFieldEvaluationStatus,
    SemanticFieldPolicy,
)
from rci.memory.models import MemoryOwner, OwnedMemoryRef, OwnedRecordType
from rci.memory.references import make_owned_memory_ref
from rci.probes.lifecycle import build_semantic_field
from rci.probes.models import (
    Mismatch,
    ProbeEvent,
    ProbeIdentity,
    RelevanceStatus,
    SemanticField,
    SemanticItem,
)
from rci.warrant.models import CheckReference


def _source_index_fingerprint(references: Iterable[OwnedMemoryRef], sequence: int) -> str:
    keys = sorted(reference.key for reference in references)
    return sha256_digest((f"{sequence}\n" + "\n".join(keys)).encode())


def select_consolidation_checkpoint(
    *,
    checkpoint_id: str,
    policy: ConsolidationPolicy,
    source_sequence: int,
    scope_fingerprint: str,
    binding_revision: str,
    protected_horizon_id: str,
    probe_observations: Iterable[ProbeEvent],
    claims: Iterable[Claim],
    conflicts: Iterable[Conflict],
    mismatches: Iterable[Mismatch],
    accepted_counterexample_requests: Mapping[str, object],
) -> ConsolidationCheckpoint:
    observations = tuple(
        item
        for item in probe_observations
        if item.probe_identity.scope_fingerprint == scope_fingerprint
        and item.binding_revision == binding_revision
        and item.probe_identity.protected_horizon_id == protected_horizon_id
    )
    observations = tuple(sorted(observations, key=lambda item: (item.sequence_index, item.id)))
    recent = observations[-policy.recent_limit :]
    recent_ids = {item.id for item in recent}
    claims_by_id = {claim.id: claim for claim in claims}
    conflicted_claim_ids = {claim_id for conflict in conflicts for claim_id in conflict.claim_ids}
    mismatched_returns = {item.external_return_id for item in mismatches}

    def is_exception(item: ProbeEvent) -> bool:
        associated = tuple(
            claims_by_id[claim_id]
            for claim_id in item.interpretation_claim_ids
            if claim_id in claims_by_id
        )
        return bool(set(item.external_return_ids) & mismatched_returns) or any(
            claim.id in conflicted_claim_ids
            or claim.assessment in {ClaimAssessment.CONTESTED, ClaimAssessment.REFUTED}
            for claim in associated
        )

    older_exceptions = tuple(
        item for item in observations if item.id not in recent_ids and is_exception(item)
    )[-policy.exception_limit :]

    sources: list[ConsolidationSource] = []
    for role, selected in (
        (ConsolidationSourceRole.RECENT_EPISODE, reversed(recent)),
        (ConsolidationSourceRole.OLDER_EXCEPTION, reversed(older_exceptions)),
    ):
        for observation in selected:
            sources.append(
                ConsolidationSource(
                    role=role,
                    reference=make_owned_memory_ref(
                        owner=MemoryOwner.EPISODIC,
                        record_type=OwnedRecordType.PROBE_EVENT,
                        record_id=observation.id,
                        record_schema_version=1,
                        record=observation,
                    ),
                    semantic_sequence=observation.sequence_index,
                )
            )
    for request_id, request in sorted(accepted_counterexample_requests.items())[
        : policy.counterexample_limit
    ]:
        result = getattr(request, "accepted_result", None)
        if not isinstance(result, CounterexampleResult):
            continue
        request_record = getattr(request, "request", None)
        if request_record is None:
            continue
        sources.append(
            ConsolidationSource(
                role=ConsolidationSourceRole.COUNTEREXAMPLE,
                reference=make_owned_memory_ref(
                    owner=MemoryOwner.ACTION,
                    record_type=OwnedRecordType.EFFECT_REQUEST,
                    record_id=request_id,
                    record_schema_version=request_record.schema_version,
                    record=request_record,
                ),
                semantic_sequence=source_sequence,
            )
        )
    unique: list[ConsolidationSource] = []
    seen: set[str] = set()
    for source in sources:
        if source.reference.key not in seen:
            unique.append(source)
            seen.add(source.reference.key)
    episode_count = sum(
        item.role
        in {ConsolidationSourceRole.RECENT_EPISODE, ConsolidationSourceRole.OLDER_EXCEPTION}
        for item in unique
    )
    status = (
        ConsolidationStatus.READY
        if episode_count >= policy.minimum_distinct_episodes
        else ConsolidationStatus.INSUFFICIENT_DIVERSITY
    )
    return ConsolidationCheckpoint(
        id=checkpoint_id,
        policy=policy,
        source_sequence=source_sequence,
        source_index_fingerprint=_source_index_fingerprint(
            (item.reference for item in unique), source_sequence
        ),
        scope_fingerprint=scope_fingerprint,
        binding_revision=binding_revision,
        protected_horizon_id=protected_horizon_id,
        sources=tuple(unique),
        status=status,
    )


def derive_conservative_field(
    *,
    probe_identity: ProbeIdentity,
    source_sequence: int,
    policy: SemanticFieldPolicy,
    safety_structure_ids: Iterable[str],
    exception_structure_ids: Iterable[str],
    dependency_structure_ids: Iterable[str],
    retrieval_structure_ids: Iterable[str],
) -> tuple[SemanticField, tuple[str, ...], tuple[str, ...], str]:
    groups = (
        tuple(sorted(set(safety_structure_ids))),
        tuple(sorted(set(exception_structure_ids))),
        tuple(sorted(set(dependency_structure_ids))),
        tuple(sorted(set(retrieval_structure_ids))),
    )
    ordered: list[str] = []
    for group in groups:
        for item in group:
            if item not in ordered:
                ordered.append(item)
    required = tuple(sorted(set(groups[0]) | set(groups[1]) | set(groups[2])))
    included = tuple(ordered[: policy.maximum_items])
    overflow = tuple(sorted(ordered[policy.maximum_items :]))
    field = build_semantic_field(
        probe_identity=probe_identity,
        protected_horizon_id=probe_identity.protected_horizon_id,
        items=tuple(
            SemanticItem(structure_id=item, relevance=RelevanceStatus.ACTIVE) for item in included
        ),
        retrieval_result_ids=tuple(sorted(set(retrieval_structure_ids))),
    )
    index = sha256_digest((f"{source_sequence}\n" + "\n".join(ordered)).encode())
    return field, required, overflow, index


def evaluate_conservative_field(
    *,
    evaluation_id: str,
    field: SemanticField,
    policy: SemanticFieldPolicy,
    source_sequence: int,
    source_index_fingerprint: str,
    probe_fingerprint: str,
    required_structure_ids: Iterable[str],
    overflow_structure_ids: Iterable[str],
) -> SemanticFieldEvaluation:
    items = field.items
    included = tuple(sorted(item.structure_id for item in items))
    irrelevant = tuple(
        sorted(item.structure_id for item in items if item.relevance is RelevanceStatus.IRRELEVANT)
    )
    required = tuple(sorted(set(required_structure_ids)))
    overflow = tuple(sorted(set(overflow_structure_ids)))
    status = (
        SemanticFieldEvaluationStatus.INCOMPLETE
        if set(required) - set(included) or overflow
        else SemanticFieldEvaluationStatus.VALID
    )
    field_fingerprint = sha256_digest(field.model_dump_json().encode())
    return SemanticFieldEvaluation(
        id=evaluation_id,
        policy=policy,
        field_id=field.id,
        field_fingerprint=field_fingerprint,
        field=field,
        source_sequence=source_sequence,
        source_index_fingerprint=source_index_fingerprint,
        probe_fingerprint=probe_fingerprint,
        required_structure_ids=required,
        included_structure_ids=included,
        overflow_structure_ids=overflow,
        irrelevant_structure_ids=irrelevant,
        status=status,
    )


def semantic_field_overflow_residual(
    evaluation: SemanticFieldEvaluation,
    scope: Scope,
) -> Residual | None:
    """Create the exact ordinary residual for structures omitted by the field bound."""

    if not evaluation.overflow_structure_ids:
        return None
    identity = content_fingerprint(
        "rci.semantic-field-overflow-residual.v1",
        {
            "evaluation_id": evaluation.id,
            "overflow": evaluation.overflow_structure_ids,
            "scope": scope.fingerprint,
        },
    )
    return Residual(
        id=f"residual_{identity[:24]}",
        carrier_id=evaluation.field_id,
        payload={
            "kind": "semantic_field_overflow",
            "structure_ids": list(evaluation.overflow_structure_ids),
        },
        scope=scope,
        provenance=Provenance(kind="derived_policy", source_id=evaluation.id),
    )


def _pair_gain(samples: tuple[ProbeSample, ...]) -> int:
    gain = 0
    for index, left in enumerate(samples):
        for right in samples[index + 1 :]:
            if (
                left.protected_consequence_class_id != right.protected_consequence_class_id
                and left.existing_basis_class_id == right.existing_basis_class_id
                and left.candidate_value_id != right.candidate_value_id
            ):
                gain += 1
    return gain


def stratified_probe_split(
    samples: Iterable[ProbeSample], protocol: ProbeEvaluationProtocol
) -> tuple[tuple[ProbeSample, ...], tuple[ProbeSample, ...]]:
    by_class: dict[str, list[ProbeSample]] = defaultdict(list)
    for sample in samples:
        by_class[sample.protected_consequence_class_id].append(sample)
    training: list[ProbeSample] = []
    holdout: list[ProbeSample] = []
    for class_id in sorted(by_class):
        group = sorted(by_class[class_id], key=lambda item: (item.fingerprint, item.observation_id))
        if len(group) < 2:
            raise ValueError("each consequence class requires training and holdout samples")
        holdout_count = max(1, ceil(len(group) / protocol.holdout_denominator))
        if holdout_count >= len(group):
            raise ValueError("holdout split must leave a training sample in each class")
        training.extend(group[:-holdout_count])
        holdout.extend(group[-holdout_count:])
    return tuple(training), tuple(holdout)


def build_probe_evaluation(
    *,
    evaluation_id: str,
    candidate_probe_id: str,
    samples: Iterable[ProbeSample],
    protocol: ProbeEvaluationProtocol,
    redundancy_check: CheckReference,
    protected_behavior_check: CheckReference,
) -> ProbeEvaluation:
    sample_tuple = tuple(samples)
    training, holdout = stratified_probe_split(sample_tuple, protocol)
    index = sha256_digest("\n".join(sorted(sample.fingerprint for sample in sample_tuple)).encode())
    training_ids = tuple(sorted(item.observation_id for item in training))
    holdout_ids = tuple(sorted(item.observation_id for item in holdout))
    training_gain = _pair_gain(training)
    holdout_gain = _pair_gain(holdout)
    evaluation_proposition_id = probe_evaluation_proposition_id(
        candidate_probe_id=candidate_probe_id,
        protocol=protocol,
        samples=sample_tuple,
        training_observation_ids=training_ids,
        holdout_observation_ids=holdout_ids,
        training_discrimination_gain=training_gain,
        holdout_discrimination_gain=holdout_gain,
        protected_error_count=0,
    )
    return ProbeEvaluation(
        id=evaluation_id,
        candidate_probe_id=candidate_probe_id,
        protocol=protocol,
        sample_index_fingerprint=index,
        samples=tuple(sorted(sample_tuple, key=lambda item: item.observation_id)),
        training_observation_ids=training_ids,
        holdout_observation_ids=holdout_ids,
        training_discrimination_gain=training_gain,
        holdout_discrimination_gain=holdout_gain,
        protected_error_count=0,
        redundancy_check=redundancy_check,
        protected_behavior_check=protected_behavior_check,
        evaluation_proposition_id=evaluation_proposition_id,
    )


def probe_evaluation_proposition_id(
    *,
    candidate_probe_id: str,
    protocol: ProbeEvaluationProtocol,
    samples: tuple[ProbeSample, ...],
    training_observation_ids: tuple[str, ...],
    holdout_observation_ids: tuple[str, ...],
    training_discrimination_gain: int,
    holdout_discrimination_gain: int,
    protected_error_count: int,
) -> str:
    """Fingerprint the exact proof material checked for a probe evaluation."""

    digest = sha256_digest(
        canonical_json_bytes(
            {
                "candidate_probe_id": candidate_probe_id,
                "holdout_discrimination_gain": holdout_discrimination_gain,
                "holdout_observation_ids": holdout_observation_ids,
                "protected_error_count": protected_error_count,
                "protocol": protocol.model_dump(mode="json"),
                "samples": tuple(
                    item.model_dump(mode="json")
                    for item in sorted(samples, key=lambda item: item.observation_id)
                ),
                "training_discrimination_gain": training_discrimination_gain,
                "training_observation_ids": training_observation_ids,
            }
        )
    )
    return f"probe-evaluation:{digest}"


def unresolved_obligation_ids(obligations: Iterable[Obligation]) -> frozenset[str]:
    return frozenset(
        item.id for item in obligations if item.status is not ObligationStatus.SATISFIED
    )
