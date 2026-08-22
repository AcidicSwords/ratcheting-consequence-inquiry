"""Pure constructors and structural inference for inquiry claims."""

from __future__ import annotations

from typing import Final

from rci.claims.models import (
    BoundArgument,
    Claim,
    ClaimRole,
    Conflict,
    ConflictKind,
    InertPayload,
    Obligation,
    ObligationKind,
    Polarity,
    Provenance,
    RepresentationLevel,
    Scope,
    content_fingerprint,
)

_ATTACK_BY_ROLE: Final[dict[ClaimRole, ObligationKind]] = {
    ClaimRole.NECESSITY: ObligationKind.NECESSITY_COUNTEREXAMPLE,
    ClaimRole.SUFFICIENCY: ObligationKind.SUFFICIENCY_COUNTEREXAMPLE,
    ClaimRole.PREREQUISITE: ObligationKind.PREREQUISITE_BYPASS,
}


def bind_l0_answer(
    *,
    question_contract_id: str,
    role: ClaimRole,
    answer: InertPayload,
    bound_args: tuple[BoundArgument, ...],
    scope: Scope,
    provenance: Provenance,
    claim_id: str | None = None,
) -> Claim:
    """Bind any JSON answer as inert L0 data without asserting its truth."""

    material = {
        "contract": question_contract_id,
        "role": role,
        "answer": answer,
        "bound_args": [item.model_dump(mode="json") for item in bound_args],
        "scope": scope.fingerprint,
        "provenance": provenance.model_dump(mode="json"),
    }
    stable_id = claim_id or f"clm_{content_fingerprint('rci.claim.l0.v1', material)[:24]}"
    return Claim(
        id=stable_id,
        role=role,
        bound_args=bound_args,
        payload=answer,
        scope=scope,
        provenance=provenance,
        representation_level=RepresentationLevel.L0_OPAQUE,
    )


def structural_conflict(left: Claim, right: Claim) -> Conflict | None:
    """Detect only explicit same-proposition opposite-polarity conflict at L0."""

    left_key = left.structural_key
    right_key = right.structural_key
    if left_key is None or left_key != right_key:
        return None
    if {left.polarity, right.polarity} != {Polarity.POSITIVE, Polarity.NEGATIVE}:
        return None
    first_id, second_id = sorted((left.id, right.id))
    claim_ids = (first_id, second_id)
    conflict_id = f"cnf_{content_fingerprint('rci.conflict.v1', claim_ids)[:24]}"
    return Conflict(
        id=conflict_id,
        claim_ids=claim_ids,
        kind=ConflictKind.STRUCTURAL_POLARITY,
        scope=left.scope,
        proposition_id=left.proposition_id,
    )


def conflict_obligation(conflict: Conflict) -> Obligation:
    args = (
        BoundArgument(name="left_claim_id", value=conflict.claim_ids[0]),
        BoundArgument(name="right_claim_id", value=conflict.claim_ids[1]),
    )
    obligation_id = f"obl_{content_fingerprint('rci.obligation.conflict.v1', conflict.id)[:24]}"
    return Obligation(
        id=obligation_id,
        kind=ObligationKind.LOCALIZE_CONFLICT,
        carrier_id=conflict.id,
        args=args,
        scope=conflict.scope,
        binding_revision=conflict.scope.binding_revision,
        priority_vector=(100,),
    )


def mandatory_attack_obligation(claim: Claim) -> Obligation | None:
    """Create the mandatory falsification pressure for modal/control claims."""

    kind = _ATTACK_BY_ROLE.get(claim.role)
    if kind is None or claim.polarity is Polarity.NEGATIVE:
        return None
    carrier_id = claim.proposition_id or claim.id
    argument_name = "proposition_id" if claim.proposition_id is not None else "claim_id"
    args = (BoundArgument(name=argument_name, value=carrier_id),)
    material = {
        "carrier": carrier_id,
        "kind": kind,
        "scope": claim.scope.fingerprint,
    }
    obligation_id = f"obl_{content_fingerprint('rci.obligation.attack.v1', material)[:24]}"
    return Obligation(
        id=obligation_id,
        kind=kind,
        carrier_id=carrier_id,
        args=args,
        scope=claim.scope,
        binding_revision=claim.scope.binding_revision,
        priority_vector=(90,),
    )
