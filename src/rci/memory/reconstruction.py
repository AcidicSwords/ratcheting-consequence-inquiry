"""Pure assembly of provisional, possibly ambiguous memory reconstructions."""

from __future__ import annotations

from collections.abc import Iterable

from rci.memory.models import MemoryReconstructionCandidate, MemoryReconstructionSet


class ReconstructionConflictError(ValueError):
    """One candidate identity was reused for different generated content."""


def build_memory_reconstruction_set(
    *,
    reconstruction_set_id: str,
    cue_ids: tuple[str, ...],
    scope_fingerprint: str,
    binding_revision: str,
    protected_horizon_id: str,
    candidates: Iterable[MemoryReconstructionCandidate],
) -> MemoryReconstructionSet:
    """Deduplicate exact candidates and preserve ambiguity in stable rank/ID order."""

    by_id: dict[str, MemoryReconstructionCandidate] = {}
    for candidate in candidates:
        prior = by_id.get(candidate.id)
        if prior is not None and prior != candidate:
            raise ReconstructionConflictError(
                f"memory reconstruction candidate {candidate.id!r} has conflicting contents"
            )
        by_id[candidate.id] = candidate
    ordered = tuple(sorted(by_id.values(), key=lambda candidate: (candidate.rank, candidate.id)))
    return MemoryReconstructionSet(
        id=reconstruction_set_id,
        cue_ids=cue_ids,
        scope_fingerprint=scope_fingerprint,
        binding_revision=binding_revision,
        protected_horizon_id=protected_horizon_id,
        candidates=ordered,
    )
