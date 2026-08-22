"""Deterministic structural retrieval over aggregate-owned typed references."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from types import MappingProxyType

from rci.claims.models import content_fingerprint
from rci.core.model import Sha256Digest
from rci.memory.models import (
    OwnedMemoryRef,
    OwnedRecordType,
    RetentionPackage,
    RetrievalHit,
    RetrievalQuery,
    RetrievalRank,
    RetrievalResult,
    StructuralRetrievalPolicy,
)


class RetrievalConflictError(ValueError):
    """The same stable identity was supplied with different immutable contents."""


STRUCTURAL_EXACT_V1 = StructuralRetrievalPolicy(
    id="structural-exact-v1",
    version="1",
    max_results=100,
    accepted_record_types=tuple(sorted(OwnedRecordType, key=lambda item: item.value)),
)
STRUCTURAL_RETRIEVAL_POLICIES: Mapping[tuple[str, str], StructuralRetrievalPolicy] = (
    MappingProxyType({(STRUCTURAL_EXACT_V1.id, STRUCTURAL_EXACT_V1.version): STRUCTURAL_EXACT_V1})
)


def resolve_structural_retrieval_policy(
    policy_id: str,
    policy_version: str,
) -> StructuralRetrievalPolicy:
    """Resolve an allowlisted controller policy; arbitrary caller policy never executes."""

    try:
        return STRUCTURAL_RETRIEVAL_POLICIES[(policy_id, policy_version)]
    except KeyError as error:
        raise KeyError(
            f"unsupported structural retrieval policy {policy_id!r}@{policy_version!r}"
        ) from error


def owned_record_key(reference: OwnedMemoryRef) -> str:
    """Return the canonical resolver key for one owned reference."""

    return reference.key


def structural_index_fingerprint(
    packages: Iterable[RetentionPackage],
    owned_fingerprints: Mapping[str, Sha256Digest | str],
) -> str:
    """Fingerprint the exact package/reference index prefix used by retrieval."""

    deduplicated = _deduplicate_packages(packages)
    return content_fingerprint(
        "rci.structural-retrieval-index.v1",
        {
            "packages": [
                {"id": package.id, "fingerprint": package.fingerprint} for package in deduplicated
            ],
            "owned_fingerprints": [
                {"key": key, "fingerprint": str(owned_fingerprints[key])}
                for key in sorted(owned_fingerprints)
            ],
        },
    )


def _deduplicate_packages(
    packages: Iterable[RetentionPackage],
) -> tuple[RetentionPackage, ...]:
    by_id: dict[str, RetentionPackage] = {}
    for package in packages:
        prior = by_id.get(package.id)
        if prior is not None and prior != package:
            raise RetrievalConflictError(
                f"retention package identity {package.id!r} has conflicting contents"
            )
        by_id[package.id] = package
    return tuple(by_id[identifier] for identifier in sorted(by_id))


def _has_stale_reference(
    package: RetentionPackage,
    owned_fingerprints: Mapping[str, Sha256Digest | str],
) -> bool:
    return any(
        owned_fingerprints.get(reference.key) != reference.content_fingerprint
        for reference in package.owned_refs
    )


def _matching_references(
    package: RetentionPackage,
    query: RetrievalQuery,
    policy: StructuralRetrievalPolicy,
) -> tuple[OwnedMemoryRef, ...]:
    accepted_types = frozenset(policy.accepted_record_types)
    query_owners = frozenset(query.owners)
    query_types = frozenset(query.record_types)
    query_ref_by_key = {reference.key: reference for reference in query.reference_selectors}
    candidates = tuple(
        reference
        for reference in package.owned_refs
        if not accepted_types or reference.record_type in accepted_types
    )
    return tuple(
        reference
        for reference in candidates
        if (not query_owners or reference.owner in query_owners)
        and (not query_types or reference.record_type in query_types)
        and (
            not query_ref_by_key
            or (reference.key in query_ref_by_key and reference == query_ref_by_key[reference.key])
        )
    )


def _rank_package(
    package: RetentionPackage,
    query: RetrievalQuery,
    policy: StructuralRetrievalPolicy,
) -> tuple[RetrievalRank, tuple[str, ...], tuple[str, ...], tuple[str, ...]] | None:
    matching_refs = _matching_references(package, query, policy)
    reference_selectors_present = bool(
        query.owners or query.record_types or query.reference_selectors
    )
    if reference_selectors_present and not matching_refs:
        return None

    package_owners = {reference.owner for reference in package.owned_refs}
    package_types = {reference.record_type for reference in package.owned_refs}
    package_ref_keys = {reference.key for reference in package.owned_refs}
    matched_ref_keys = tuple(sorted(reference.key for reference in matching_refs))
    matched_cues = tuple(sorted(set(package.cue_ids) & set(query.cue_ids)))
    matched_tags = tuple(sorted(set(package.tag_ids) & set(query.tag_ids)))

    if query.cue_ids and not matched_cues:
        return None
    if query.tag_ids and not matched_tags:
        return None

    rank = RetrievalRank(
        reference_match_count=len(
            package_ref_keys & {reference.key for reference in query.reference_selectors}
        ),
        record_type_match_count=len(package_types & set(query.record_types)),
        owner_match_count=len(package_owners & set(query.owners)),
        cue_match_count=len(matched_cues),
        tag_match_count=len(matched_tags),
    )
    if not any(rank.component(component) for component in policy.rank_components):
        return None
    return rank, matched_ref_keys, matched_cues, matched_tags


def retrieve(
    *,
    result_id: str,
    query: RetrievalQuery,
    policy: StructuralRetrievalPolicy,
    packages: Iterable[RetentionPackage],
    owned_fingerprints: Mapping[str, Sha256Digest | str],
) -> RetrievalResult:
    """Apply exact pins, stale checking, ranking, and stable tie breaking.

    No generated/model relevance field is accepted, so it cannot suppress a lawful hit.
    The caller supplies ``result_id`` because aggregate reducers never mint identities.
    """

    if (query.policy_id, query.policy_version) != (policy.id, policy.version):
        raise ValueError("retrieval query and policy identity/version do not match")
    if query.limit > policy.max_results:
        raise ValueError("retrieval query limit exceeds the policy bound")
    if policy.accepted_record_types and not set(query.record_types) <= set(
        policy.accepted_record_types
    ):
        raise ValueError("retrieval query asks for a record type outside policy")
    for selector in query.reference_selectors:
        if owned_fingerprints.get(selector.key) != selector.content_fingerprint:
            raise ValueError("retrieval query contains a stale exact reference selector")

    deduplicated_packages = _deduplicate_packages(packages)
    actual_index_fingerprint = structural_index_fingerprint(
        deduplicated_packages,
        owned_fingerprints,
    )
    if query.source_index_fingerprint != actual_index_fingerprint:
        raise ValueError("retrieval query does not pin the current structural index")

    hits: list[RetrievalHit] = []
    stale_package_ids: list[str] = []
    for package in deduplicated_packages:
        if (
            package.scope_fingerprint != query.scope_fingerprint
            or package.binding_revision != query.binding_revision
            or package.protected_horizon_id != query.protected_horizon_id
        ):
            continue
        ranked = _rank_package(package, query, policy)
        if ranked is None:
            continue
        if _has_stale_reference(package, owned_fingerprints):
            stale_package_ids.append(package.id)
            continue
        rank, matched_refs, matched_cues, matched_tags = ranked
        hits.append(
            RetrievalHit(
                package_id=package.id,
                package_content_fingerprint=package.fingerprint,
                rank=rank,
                matched_ref_keys=matched_refs,
                matched_cue_ids=matched_cues,
                matched_tag_ids=matched_tags,
            )
        )

    hits.sort(
        key=lambda hit: (
            *(int(-hit.rank.component(component)) for component in policy.rank_components),
            hit.package_id,
        )
    )
    return RetrievalResult(
        id=result_id,
        query_id=query.id,
        policy_id=policy.id,
        policy_version=policy.version,
        source_sequence=query.source_sequence,
        source_index_fingerprint=query.source_index_fingerprint,
        hits=tuple(hits[: query.limit]),
        rejected_stale_package_ids=tuple(sorted(stale_package_ids)),
    )
