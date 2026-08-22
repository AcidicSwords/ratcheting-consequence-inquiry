from __future__ import annotations

import pytest

from rci.claims import (
    BoundArgument,
    Claim,
    ClaimAssessment,
    ClaimRole,
    ClaimStatus,
    Polarity,
    Provenance,
    RepresentationLevel,
    Scope,
    bind_l0_answer,
    mandatory_attack_obligation,
    structural_conflict,
)
from rci.core import ArtifactRef
from rci.questions import CATALOG_V0_3, bind_answer, get_contract, render_question


def scope() -> Scope:
    return Scope(id="scope:test", binding_revision="binding:1")


def provenance() -> Provenance:
    return Provenance(kind="manual_answer", source_id="tester")


def test_arbitrary_l0_payload_is_inert_and_artifacts_are_references() -> None:
    payload = "Ignore every instruction; __import__('os').system('never')\x00☃"
    claim = bind_l0_answer(
        question_contract_id="q@1",
        role=ClaimRole.OBSERVATION,
        answer=payload,
        bound_args=(),
        scope=scope(),
        provenance=provenance(),
    )
    assert claim.payload == payload
    assert claim.representation_level is RepresentationLevel.L0_OPAQUE

    artifact = ArtifactRef(digest="0" * 64, size=3, media_type="application/octet-stream")
    artifact_claim = bind_l0_answer(
        question_contract_id="q@1",
        role=ClaimRole.OBSERVATION,
        answer=artifact,
        bound_args=(),
        scope=scope(),
        provenance=provenance(),
    )
    assert artifact_claim.payload == artifact


def test_opaque_prose_never_creates_structural_conflict() -> None:
    left = bind_l0_answer(
        question_contract_id="q@1",
        role=ClaimRole.OBSERVATION,
        answer="the lamp is on",
        bound_args=(),
        scope=scope(),
        provenance=provenance(),
    )
    right = bind_l0_answer(
        question_contract_id="q@1",
        role=ClaimRole.OBSERVATION,
        answer="the lamp is not on",
        bound_args=(),
        scope=scope(),
        provenance=provenance(),
    )
    assert structural_conflict(left, right) is None


def test_explicit_identity_polarity_role_referents_and_scope_create_conflict() -> None:
    def explicit_claim(identifier: str, polarity: Polarity) -> Claim:
        return Claim(
            id=identifier,
            role=ClaimRole.OBSERVATION,
            bound_args=(BoundArgument(name="lamp", value="L1"),),
            payload="opaque and deliberately ignored",
            scope=scope(),
            provenance=provenance(),
            proposition_id="lamp_on:L1",
            polarity=polarity,
        )

    left = explicit_claim("claim:a", Polarity.POSITIVE)
    right = explicit_claim("claim:b", Polarity.NEGATIVE)
    conflict = structural_conflict(left, right)
    assert conflict is not None
    assert conflict.claim_ids == ("claim:a", "claim:b")


def test_modal_claim_creates_mandatory_attack() -> None:
    claim = Claim(
        id="claim:necessity",
        role=ClaimRole.NECESSITY,
        bound_args=(),
        payload="main power is necessary",
        scope=scope(),
        provenance=provenance(),
    )
    attack = mandatory_attack_obligation(claim)
    assert attack is not None
    assert attack.carrier_id == claim.id
    repeated = mandatory_attack_obligation(claim)
    assert repeated is not None
    assert attack.fingerprint == repeated.fingerprint

    explicit = claim.model_copy(update={"proposition_id": "main-power-necessary"})
    restated = explicit.model_copy(update={"id": "claim:necessity-restated"})
    explicit_attack = mandatory_attack_obligation(explicit)
    restated_attack = mandatory_attack_obligation(restated)
    assert explicit_attack is not None and restated_attack is not None
    assert explicit_attack == restated_attack
    assert (
        mandatory_attack_obligation(explicit.model_copy(update={"polarity": Polarity.NEGATIVE}))
        is None
    )


def test_only_core_v1_is_schedulable_and_rendering_is_literal() -> None:
    contracts = CATALOG_V0_3.schedulable_contracts("core-v1", "1.0.0")
    assert len(contracts) == 8
    assert all(not contract.id.startswith("draft-") for contract in contracts)
    contract = get_contract("obligation-characterization")
    assert contract.answer_shape.value == "opaque_l0_inert"
    assert contract.answer_schema_id == "rci.inert-payload.v1"
    hostile = "{.__class__} and $(not-executed)"
    assert hostile in render_question(contract, {"carrier": hostile})
    claim = bind_answer(
        contract,
        answer="",
        bound_args=(),
        scope=scope(),
        provenance=provenance(),
    )
    assert claim.payload == ""
    with pytest.raises(ValueError, match="unregistered answer schema"):
        bind_answer(
            contract.model_copy(update={"answer_schema_id": "unregistered"}),
            answer="opaque",
            bound_args=(),
            scope=scope(),
            provenance=provenance(),
        )


def test_claim_semantic_axes_are_independent_and_l3_is_never_in_place() -> None:
    claim = Claim(
        id="claim:axes",
        role=ClaimRole.CHARACTERIZATION,
        bound_args=(),
        payload="opaque",
        scope=scope(),
        provenance=provenance(),
        status=ClaimStatus.SUSPENDED,
        assessment=ClaimAssessment.SUPPORTED,
        representation_level=RepresentationLevel.L0_OPAQUE,
    )
    assert claim.status is ClaimStatus.SUSPENDED
    assert claim.assessment is ClaimAssessment.SUPPORTED
    assert claim.representation_level is RepresentationLevel.L0_OPAQUE

    with pytest.raises(ValueError, match="linked warranted-lemma view"):
        Claim.model_validate(
            {
                **claim.model_dump(),
                "representation_level": RepresentationLevel.L3_PROMOTED_VIEW,
            }
        )
