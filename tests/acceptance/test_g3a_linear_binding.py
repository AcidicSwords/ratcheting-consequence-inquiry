from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from rci.cli import app
from rci.compression import (
    CarrierContract,
    CarrierRole,
    CompressionContract,
    CompressionValidation,
    ExactClaimKind,
    ExactLinearAnalysis,
    ExactPropertyValidation,
    ExactRational,
    ExactRationalCoordinates,
    ExactRationalMatrix,
    ExactRationalVector,
    LinearAnalysisStanding,
    LinearCheckVerdict,
    LinearEquivalenceScope,
    LinearOutputKind,
    LinearQueryFamily,
    LinearReopeningDisposition,
    ValidationOutcome,
    ValidationProperty,
    WeightedLinearObservation,
    analyze_linear_query_family,
    build_linear_property_check_records,
    build_linear_query_family,
    build_linear_validation_properties,
    detect_linear_kernel_reopening,
    encode_quotient,
    independently_check_linear_analysis,
    linear_property_check_payloads,
    linear_target_carrier_schema_id,
    protected_consequences_equal,
)
from rci.core import RecordCheckerVerdict, RecordEvidence
from rci.core.errors import InvalidCommandError
from rci.core.model import ArtifactRef
from rci.core.serialization import canonical_json_bytes
from rci.sdk import RCI
from rci.warrant.models import CheckReference, EvidenceKind

SCOPE = "a" * 64
DIGEST = "b" * 64
NOW = datetime(2026, 8, 23, tzinfo=UTC)


def _r(numerator: int, denominator: int = 1) -> ExactRational:
    return ExactRational(numerator=numerator, denominator=denominator)


def _matrix(rows: tuple[tuple[int | tuple[int, int], ...], ...]) -> ExactRationalMatrix:
    return ExactRationalMatrix(
        rows=tuple(
            tuple(_r(*value) if isinstance(value, tuple) else _r(value) for value in row)
            for row in rows
        )
    )


def _observation(
    identity: str,
    rows: tuple[tuple[int | tuple[int, int], ...], ...],
    *,
    weight: tuple[int, int] = (1, 1),
) -> WeightedLinearObservation:
    return WeightedLinearObservation(
        id=identity,
        operator=_matrix(rows),
        weight=_r(*weight),
    )


def _family(
    observations: tuple[WeightedLinearObservation, ...],
    *,
    horizon: str = "linear-horizon-v1",
    output: LinearOutputKind = LinearOutputKind.SCALAR,
    scope: LinearEquivalenceScope = LinearEquivalenceScope.UNIVERSAL_FINITE_FAMILY,
    carrier: str = "history-vector-carrier-v1",
) -> LinearQueryFamily:
    return build_linear_query_family(
        binding_revision="linear-binding-v1",
        source_carrier_id=carrier,
        scope_fingerprint=SCOPE,
        protected_horizon_id=horizon,
        output_kind=output,
        equivalence_scope=scope,
        observations=observations,
    )


def test_exact_universal_quotient_is_permutation_stable_and_linear_only() -> None:
    observations = (
        _observation("probe-x", ((1, 0, 0),)),
        _observation("probe-y", ((0, 1, 0),)),
        _observation("probe-xy-redundant", ((1, 1, 0),), weight=(2, 1)),
    )
    family = _family(observations)
    permuted = _family(tuple(reversed(observations)))
    assert family == permuted

    analysis = analyze_linear_query_family(family)
    assert analysis.rank == 2
    assert analysis.minimum_linear_encoder_dimension == 2
    assert analysis.minimality_scope == "linear_encoders_only"
    assert analysis.standing is LinearAnalysisStanding.CANDIDATE_UNLICENSED
    assert analysis.kernel_basis == (ExactRationalVector(values=(_r(0), _r(0), _r(1))),)
    assert analysis.quotient_basis == (
        ExactRationalVector(values=(_r(1), _r(0), _r(0))),
        ExactRationalVector(values=(_r(0), _r(1), _r(0))),
    )
    assert encode_quotient(
        analysis, ExactRationalVector(values=(_r(2), _r(3), _r(99)))
    ) == ExactRationalCoordinates(values=(_r(2), _r(3)))
    with pytest.raises(ValueError, match="intact analysis record"):
        encode_quotient(
            analysis.model_copy(
                update={
                    "quotient_basis": (
                        ExactRationalVector(values=(_r(0), _r(0), _r(1))),
                        ExactRationalVector(values=(_r(0), _r(1), _r(0))),
                    )
                }
            ),
            ExactRationalVector(values=(_r(2), _r(3), _r(99))),
        )
    assert protected_consequences_equal(
        family,
        ExactRationalVector(values=(_r(2), _r(3), _r(0))),
        ExactRationalVector(values=(_r(2), _r(3), _r(99))),
    )
    assert not protected_consequences_equal(
        family,
        ExactRationalVector(values=(_r(2), _r(3), _r(0))),
        ExactRationalVector(values=(_r(3), _r(3), _r(0))),
    )


def test_finite_support_scalar_analysis_is_uncentered_and_almost_sure_only() -> None:
    family = _family(
        (
            _observation("support-x", ((1, 0),), weight=(1, 4)),
            _observation("support-y", ((0, 1),), weight=(3, 4)),
        ),
        scope=LinearEquivalenceScope.FINITE_SUPPORT_ALMOST_SURE,
    )
    analysis = analyze_linear_query_family(family)
    assert family.gram_semantics == "weighted_operator_gram"
    assert family.distribution_moment_semantics == "uncentered_second_moment"
    assert analysis.equivalence_scope is LinearEquivalenceScope.FINITE_SUPPORT_ALMOST_SURE
    assert analysis.gram_matrix == _matrix((((1, 4), 0), (0, (3, 4))))
    assert analysis.rank == 2
    assert not hasattr(analysis, "universal_equivalence")


def test_vector_output_uses_exact_weighted_gram_operator() -> None:
    family = _family(
        (
            _observation(
                "vector-left",
                ((1, 0, 0), (0, 1, 0)),
                weight=(1, 2),
            ),
            _observation(
                "vector-right",
                ((0, 1, 0), (0, 0, 1)),
                weight=(1, 2),
            ),
        ),
        output=LinearOutputKind.VECTOR,
        scope=LinearEquivalenceScope.FINITE_SUPPORT_ALMOST_SURE,
    )
    analysis = analyze_linear_query_family(family)
    assert analysis.gram_matrix == _matrix((((1, 2), 0, 0), (0, 1, 0), (0, 0, (1, 2))))
    assert analysis.rank == 3
    assert analysis.kernel_basis == ()


def test_exact_input_contract_rejects_approximation_and_invalid_support() -> None:
    tiny_exact = _family(
        (
            WeightedLinearObservation(
                id="tiny-exact",
                operator=ExactRationalMatrix(
                    rows=((ExactRational(numerator=1, denominator=10**12),),)
                ),
            ),
        )
    )
    assert analyze_linear_query_family(tiny_exact).rank == 1
    with pytest.raises(ValidationError, match="reduced"):
        ExactRational(numerator=2, denominator=4)
    with pytest.raises(ValidationError):
        ExactRational.model_validate({"numerator": 0.1, "denominator": 1})
    with pytest.raises(ValidationError, match="strictly positive"):
        WeightedLinearObservation(
            id="zero-weight",
            operator=_matrix(((1, 0),)),
            weight=_r(0),
        )
    with pytest.raises(ValidationError, match="sum exactly to one"):
        _family(
            (
                _observation("a", ((1, 0),), weight=(1, 3)),
                _observation("b", ((0, 1),), weight=(1, 3)),
            ),
            scope=LinearEquivalenceScope.FINITE_SUPPORT_ALMOST_SURE,
        )
    with pytest.raises(ValidationError, match="scalar"):
        _family((_observation("not-scalar", ((1, 0), (0, 1))),))
    with pytest.raises(ValidationError, match="finite-support almost-sure"):
        _family(
            (_observation("universal-vector", ((1, 0), (0, 1))),),
            output=LinearOutputKind.VECTOR,
        )
    with pytest.raises(ValidationError, match="exact-rational-linear-v1"):
        build_linear_query_family(
            binding_revision="binding-v1",
            source_carrier_id="carrier-v1",
            scope_fingerprint=SCOPE,
            protected_horizon_id="horizon-v1",
            output_kind=LinearOutputKind.SCALAR,
            equivalence_scope=LinearEquivalenceScope.UNIVERSAL_FINITE_FAMILY,
            observations=(_observation("unknown-policy", ((1, 0),)),),
            representation_policy_id="unknown-linear-policy",  # type: ignore[arg-type]
        )


def test_public_analyzer_revalidates_the_exact_query_family_boundary() -> None:
    family = _family((_observation("x", ((1, 0),)),))
    with pytest.raises(ValueError, match="intact query family"):
        analyze_linear_query_family(family.model_copy(update={"schema_version": 2}))
    invalid_vector_family = family.model_copy(update={"output_kind": LinearOutputKind.VECTOR})
    with pytest.raises(ValueError, match="intact query family"):
        analyze_linear_query_family(invalid_vector_family)
    with pytest.raises(ValueError, match="intact query family"):
        independently_check_linear_analysis(
            invalid_vector_family,
            analyze_linear_query_family(family),
        )
    with pytest.raises(ValueError, match="intact query family"):
        analyze_linear_query_family(
            family.model_copy(update={"representation_policy_id": "unknown-linear-policy"})
        )


def test_zero_probe_has_a_lawful_zero_dimensional_linear_quotient() -> None:
    family = _family((_observation("zero", ((0, 0),)),))
    analysis = analyze_linear_query_family(family)
    check = independently_check_linear_analysis(family, analysis)
    assert analysis.rank == 0
    assert analysis.quotient_basis == ()
    assert encode_quotient(
        analysis, ExactRationalVector(values=(_r(7), _r(-3)))
    ) == ExactRationalCoordinates(values=())
    assert check.verdict is LinearCheckVerdict.VALID


def test_fraction_checker_rejects_tampered_sympy_candidate_and_bridges_stages() -> None:
    family = _family((_observation("x", ((1, 0),)),))
    analysis = analyze_linear_query_family(family)
    check = independently_check_linear_analysis(family, analysis)
    assert check.verdict is LinearCheckVerdict.VALID
    assert dict(check.property_outcomes)[ValidationProperty.CONSEQUENCE_FACTORIZATION] is (
        ValidationOutcome.VALID
    )

    compression_contract = CompressionContract(
        id="compression-contract",
        carrier_manifest_id="carrier-manifest-v1",
        source_carrier_id=family.source_carrier_id,
        target_carrier=CarrierContract(
            id="linear-retained-carrier",
            role=CarrierRole.OTHER_DECLARED,
            schema_id=linear_target_carrier_schema_id(analysis),
            binding_revision=family.binding_revision,
        ),
        binding_revision=family.binding_revision,
        scope_fingerprint=family.scope_fingerprint,
        protected_horizon_id=family.protected_horizon_id,
        continuation_operation_ids=(),
        consequence_query_ids=tuple(item.id for item in family.observations),
        equality_semantics_id=family.equality_semantics_id,
        recovery_semantics_ids=(),
        claim_kinds=(
            ExactClaimKind.COARSEST_EXACT_QUOTIENT,
            ExactClaimKind.CONSEQUENCE_SUFFICIENT,
        ),
        representation_policy_id=family.representation_policy_id,
        provenance_refs=tuple(sorted((family.id, analysis.id))),
    )
    property_check_records = tuple(
        (
            property_kind,
            *build_linear_property_check_records(
                family,
                analysis,
                check,
                compression_contract,
                property_kind,
            ),
        )
        for property_kind in (
            ValidationProperty.CONSEQUENCE_FACTORIZATION,
            ValidationProperty.EXACT_EQUIVALENCE,
        )
    )
    supplemental_properties = (
        ExactPropertyValidation(
            property=ValidationProperty.RESIDUE_COMPLETENESS,
            outcome=ValidationOutcome.VALID,
            proposition_id="compression-property:compression-contract:residue_completeness",
            check=CheckReference(
                evidence_id="linear-residue-evidence",
                checker_verdict_id="linear-residue-check",
            ),
        ),
    )
    properties = build_linear_validation_properties(
        check,
        family=family,
        analysis=analysis,
        compression_contract=compression_contract,
        property_check_records=property_check_records,
        supplemental_properties=supplemental_properties,
    )
    validation = CompressionValidation(
        id="linear-validation",
        contract_id="compression-contract",
        contract_fingerprint=DIGEST,
        properties=properties,
        validator_id="fraction-rref-v1",
        validator_version="1",
        validation_artifact=ArtifactRef(digest=DIGEST, size=1),
    )
    assert validation.valid
    assert len(validation.properties) == len(ValidationProperty)
    claimed_checks = tuple(
        item.check for item in validation.properties if item.outcome is ValidationOutcome.VALID
    )
    assert len(claimed_checks) == 3
    assert len(set(claimed_checks)) == 3
    assert (
        next(
            item
            for item in validation.properties
            if item.property is ValidationProperty.RESIDUE_COMPLETENESS
        ).outcome
        is ValidationOutcome.VALID
    )
    with pytest.raises(ValueError, match="required exact property"):
        build_linear_validation_properties(
            check,
            family=family,
            analysis=analysis,
            compression_contract=compression_contract,
            property_check_records=property_check_records,
            supplemental_properties=(),
        )

    substituted_identity = analysis.model_dump(mode="python")
    substituted_identity["id"] = "lin_substituted"
    with pytest.raises(ValidationError, match="content-derived"):
        ExactLinearAnalysis.model_validate(substituted_identity)
    substituted_basis = analysis.model_dump(mode="python")
    substituted_basis["quotient_basis"] = (ExactRationalVector(values=(_r(0), _r(1))),)
    with pytest.raises(ValidationError, match="content-derived"):
        ExactLinearAnalysis.model_validate(substituted_basis)

    tampered = analysis.model_copy(update={"gram_matrix": _matrix(((2, 0), (0, 0)))})
    invalid = independently_check_linear_analysis(family, tampered)
    assert invalid.verdict is LinearCheckVerdict.INVALID
    assert "gram_mismatch" in invalid.issue_ids
    identity_check = independently_check_linear_analysis(
        family, analysis.model_copy(update={"id": "lin_substituted"})
    )
    assert identity_check.verdict is LinearCheckVerdict.INVALID
    assert "analysis_id_mismatch" in identity_check.issue_ids
    scope_check = independently_check_linear_analysis(
        family, analysis.model_copy(update={"minimality_scope": "unrestricted"})
    )
    assert scope_check.verdict is LinearCheckVerdict.INVALID
    assert "minimality_scope_mismatch" in scope_check.issue_ids
    fixed_pin_mutations = (
        ("schema_version", 2, "schema_version_mismatch"),
        ("construction_backend_id", "foreign-backend", "construction_backend_mismatch"),
        ("construction_backend_version", "999", "construction_backend_version_mismatch"),
        ("standing", "licensed", "standing_mismatch"),
    )
    for field, value, issue in fixed_pin_mutations:
        pin_check = independently_check_linear_analysis(
            family, analysis.model_copy(update={field: value})
        )
        assert pin_check.verdict is LinearCheckVerdict.INVALID
        assert issue in pin_check.issue_ids
        assert "analysis_id_mismatch" in pin_check.issue_ids
    with pytest.raises(ValueError, match="intact candidate check"):
        build_linear_validation_properties(
            check.model_copy(update={"id": "lck_substituted"}),
            family=family,
            analysis=analysis,
            compression_contract=compression_contract,
            property_check_records=property_check_records,
            supplemental_properties=supplemental_properties,
        )
    with pytest.raises(ValueError, match="intact candidate check"):
        build_linear_validation_properties(
            check.model_copy(update={"verdict": LinearCheckVerdict.INVALID}),
            family=family,
            analysis=analysis,
            compression_contract=compression_contract,
            property_check_records=property_check_records,
            supplemental_properties=supplemental_properties,
            invalid_witness_artifact=ArtifactRef(digest=DIGEST, size=1),
        )
    with pytest.raises(ValueError, match="each claimed"):
        build_linear_validation_properties(
            check,
            family=family,
            analysis=analysis,
            compression_contract=compression_contract,
            property_check_records=property_check_records[:1],
            supplemental_properties=supplemental_properties,
        )
    for substituted_records in (
        (
            property_check_records[0],
            (
                ValidationProperty.EXACT_EQUIVALENCE,
                property_check_records[0][1],
                property_check_records[0][2],
            ),
        ),
        (
            property_check_records[0],
            (
                ValidationProperty.EXACT_EQUIVALENCE,
                property_check_records[1][1],
                property_check_records[1][2].model_copy(
                    update={"checker_id": "construction-backend"}
                ),
            ),
        ),
        (
            property_check_records[0],
            (
                ValidationProperty.EXACT_EQUIVALENCE,
                property_check_records[1][1].model_copy(
                    update={"artifact": ArtifactRef(digest="f" * 64, size=1)}
                ),
                property_check_records[1][2],
            ),
        ),
    ):
        with pytest.raises(ValueError, match="exact Fraction-check projection"):
            build_linear_validation_properties(
                check,
                family=family,
                analysis=analysis,
                compression_contract=compression_contract,
                property_check_records=substituted_records,
                supplemental_properties=supplemental_properties,
            )
    foreign_target = compression_contract.target_carrier.model_copy(
        update={"binding_revision": "foreign-binding"}
    )
    foreign_contracts = (
        (
            compression_contract.model_copy(
                update={
                    "binding_revision": "foreign-binding",
                    "target_carrier": foreign_target,
                }
            ),
            "binding",
        ),
        (
            compression_contract.model_copy(update={"source_carrier_id": "foreign-source-carrier"}),
            "source_carrier",
        ),
        (
            compression_contract.model_copy(
                update={
                    "target_carrier": compression_contract.target_carrier.model_copy(
                        update={"schema_id": "constant-state-v1"}
                    )
                }
            ),
            "target_carrier_schema",
        ),
        (compression_contract.model_copy(update={"scope_fingerprint": "d" * 64}), "scope"),
        (
            compression_contract.model_copy(update={"protected_horizon_id": "foreign-horizon"}),
            "horizon",
        ),
        (
            compression_contract.model_copy(update={"consequence_query_ids": ("foreign-query",)}),
            "consequence_queries",
        ),
        (
            compression_contract.model_copy(
                update={"equality_semantics_id": "foreign-equality-semantics"}
            ),
            "equality_semantics",
        ),
        (
            compression_contract.model_copy(
                update={"representation_policy_id": "foreign-linear-policy"}
            ),
            "representation_policy",
        ),
        (
            compression_contract.model_copy(update={"provenance_refs": ("foreign-family",)}),
            "family_provenance",
        ),
        (
            compression_contract.model_copy(update={"provenance_refs": (family.id,)}),
            "analysis_provenance",
        ),
    )
    for foreign_contract, mismatch in foreign_contracts:
        with pytest.raises(ValueError, match=mismatch):
            build_linear_validation_properties(
                check,
                family=family,
                analysis=analysis,
                compression_contract=foreign_contract,
                property_check_records=property_check_records,
                supplemental_properties=supplemental_properties,
            )
    with pytest.raises(ValueError, match="exact family analysis"):
        build_linear_validation_properties(
            invalid,
            family=family,
            analysis=analysis,
            compression_contract=compression_contract,
            property_check_records=property_check_records,
            supplemental_properties=supplemental_properties,
        )


def test_aggregate_rejects_same_id_substitution_of_linear_check_records(
    tmp_path: Path,
) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)
    inquiry_id = "linear-record-binding"
    state = sdk.start(inquiry_id)
    assert state.context is not None
    family = build_linear_query_family(
        binding_revision=state.context.binding_revision,
        source_carrier_id="history-vector-carrier-v1",
        scope_fingerprint=state.context.scope_fingerprint,
        protected_horizon_id=state.context.protected_horizon_id,
        output_kind=LinearOutputKind.SCALAR,
        equivalence_scope=LinearEquivalenceScope.UNIVERSAL_FINITE_FAMILY,
        observations=(_observation("aggregate-x", ((1, 0),)),),
    )
    analysis = analyze_linear_query_family(family)
    check = independently_check_linear_analysis(family, analysis)
    contract = CompressionContract(
        id="aggregate-linear-contract",
        carrier_manifest_id="aggregate-carrier-manifest",
        source_carrier_id=family.source_carrier_id,
        target_carrier=CarrierContract(
            id="aggregate-linear-target",
            role=CarrierRole.OTHER_DECLARED,
            schema_id=linear_target_carrier_schema_id(analysis),
            binding_revision=family.binding_revision,
        ),
        binding_revision=family.binding_revision,
        scope_fingerprint=family.scope_fingerprint,
        protected_horizon_id=family.protected_horizon_id,
        continuation_operation_ids=(),
        consequence_query_ids=tuple(item.id for item in family.observations),
        equality_semantics_id=family.equality_semantics_id,
        recovery_semantics_ids=(),
        claim_kinds=(ExactClaimKind.CONSEQUENCE_SUFFICIENT,),
        representation_policy_id=family.representation_policy_id,
        provenance_refs=tuple(sorted((family.id, analysis.id))),
    )
    evidence, verdict = build_linear_property_check_records(
        family,
        analysis,
        check,
        contract,
        ValidationProperty.CONSEQUENCE_FACTORIZATION,
    )
    evidence_payload, verdict_payload = linear_property_check_payloads(
        family,
        analysis,
        check,
        contract,
        ValidationProperty.CONSEQUENCE_FACTORIZATION,
    )
    assert (
        sdk.artifacts.put_bytes(
            evidence_payload,
            media_type="application/json",
            encoding="utf-8",
        )
        == evidence.artifact
    )
    assert (
        sdk.artifacts.put_bytes(
            verdict_payload,
            media_type="application/json",
            encoding="utf-8",
        )
        == verdict.verdict_artifact
    )
    foreign_artifact = sdk.artifacts.put_bytes(
        b"foreign linear property evidence",
        media_type="application/json",
        encoding="utf-8",
    )
    with pytest.raises(InvalidCommandError, match="identity does not match its artifact"):
        sdk.dispatch(
            RecordEvidence(
                event_id="record-foreign-linear-evidence",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                evidence=evidence.model_copy(update={"artifact": foreign_artifact}),
            )
        )
    with pytest.raises(InvalidCommandError, match="identity does not match its artifact"):
        sdk.dispatch(
            RecordEvidence(
                event_id="record-retyped-linear-evidence",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                evidence=evidence.model_copy(update={"kind": EvidenceKind.OBSERVATION}),
            )
        )

    sdk.dispatch(
        RecordEvidence(
            event_id="record-linear-evidence",
            inquiry_id=inquiry_id,
            occurred_at=NOW,
            evidence=evidence,
        )
    )
    foreign_verdict_artifact = sdk.artifacts.put_bytes(
        b"foreign linear property verdict",
        media_type="application/json",
        encoding="utf-8",
    )
    with pytest.raises(InvalidCommandError, match="identity does not match its checked record"):
        sdk.dispatch(
            RecordCheckerVerdict(
                event_id="record-foreign-linear-verdict",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                checker_verdict=verdict.model_copy(
                    update={"verdict_artifact": foreign_verdict_artifact}
                ),
            )
        )
    with pytest.raises(InvalidCommandError, match="identity does not match its checked record"):
        sdk.dispatch(
            RecordCheckerVerdict(
                event_id="record-recertified-linear-verdict",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                checker_verdict=verdict.model_copy(
                    update={"certificate_artifact": foreign_verdict_artifact}
                ),
            )
        )

    accepted = sdk.dispatch(
        RecordCheckerVerdict(
            event_id="record-linear-verdict",
            inquiry_id=inquiry_id,
            occurred_at=NOW,
            checker_verdict=verdict,
        )
    )
    assert accepted.evidence_by_id(evidence.id) == evidence
    assert accepted.checker_verdict_by_id(verdict.id) == verdict


def test_positive_probe_addition_opens_exact_unknown_for_owned_g3a_resolution() -> None:
    x = _observation("probe-x", ((1, 0, 0),))
    y = _observation("probe-y", ((0, 1, 0),))
    old_family = _family((x,), horizon="horizon-x")
    expanded_family = _family((x, y), horizon="horizon-xy")
    old = analyze_linear_query_family(old_family)
    expanded = analyze_linear_query_family(expanded_family)

    unknown = detect_linear_kernel_reopening(
        incumbent_family=old_family,
        incumbent=old,
        expanded_family=expanded_family,
        expanded=expanded,
    )
    assert unknown.reopened
    assert unknown.witness == ExactRationalVector(values=(_r(0), _r(1), _r(0)))
    assert unknown.positive_observation_addition
    assert unknown.strict_kernel_shrink
    assert unknown.disposition is LinearReopeningDisposition.UNKNOWN
    assert not hasattr(unknown, "path_residue_id")
    assert not hasattr(unknown, "recovery_license_id")
    substituted_reopening = unknown.model_dump(mode="python")
    substituted_reopening["id"] = "lrp_substituted"
    with pytest.raises(ValidationError, match="content-derived"):
        type(unknown).model_validate(substituted_reopening)


def test_normalized_support_extension_computes_strict_kernel_shrink_from_subspaces() -> None:
    old_family = _family(
        (_observation("probe-x", ((1, 0),)),),
        scope=LinearEquivalenceScope.FINITE_SUPPORT_ALMOST_SURE,
        horizon="horizon-x-support",
    )
    expanded_family = _family(
        (
            _observation("probe-x", ((1, 0),), weight=(1, 2)),
            _observation("probe-y", ((0, 1),), weight=(1, 2)),
        ),
        scope=LinearEquivalenceScope.FINITE_SUPPORT_ALMOST_SURE,
        horizon="horizon-xy-support",
    )
    result = detect_linear_kernel_reopening(
        incumbent_family=old_family,
        incumbent=analyze_linear_query_family(old_family),
        expanded_family=expanded_family,
        expanded=analyze_linear_query_family(expanded_family),
    )
    assert result.reopened
    assert result.positive_observation_addition
    assert result.strict_kernel_shrink

    crosscut_family = _family(
        (_observation("probe-y", ((0, 1),)),),
        scope=LinearEquivalenceScope.FINITE_SUPPORT_ALMOST_SURE,
        horizon="horizon-y-support",
    )
    crosscut = detect_linear_kernel_reopening(
        incumbent_family=old_family,
        incumbent=analyze_linear_query_family(old_family),
        expanded_family=crosscut_family,
        expanded=analyze_linear_query_family(crosscut_family),
    )
    assert crosscut.reopened
    assert not crosscut.positive_observation_addition
    assert not crosscut.strict_kernel_shrink


def test_reversed_kernel_inclusion_does_not_fabricate_reopening() -> None:
    x = _observation("probe-x", ((1, 0, 0),))
    y = _observation("probe-y", ((0, 1, 0),))
    incumbent_family = _family((x, y), horizon="horizon-xy")
    weakened_family = _family((x,), horizon="horizon-x")
    result = detect_linear_kernel_reopening(
        incumbent_family=incumbent_family,
        incumbent=analyze_linear_query_family(incumbent_family),
        expanded_family=weakened_family,
        expanded=analyze_linear_query_family(weakened_family),
    )
    assert not result.reopened
    assert result.witness is None
    assert result.disposition is LinearReopeningDisposition.NOT_REOPENED
    assert not result.positive_observation_addition


def test_reopening_rejects_foreign_carriers_and_equivalence_semantics() -> None:
    x = _observation("probe-x", ((1, 0),))
    old_family = _family((x,), horizon="old")
    foreign = _family((x,), horizon="new", carrier="foreign-carrier")
    with pytest.raises(ValueError, match="one binding"):
        detect_linear_kernel_reopening(
            incumbent_family=old_family,
            incumbent=analyze_linear_query_family(old_family),
            expanded_family=foreign,
            expanded=analyze_linear_query_family(foreign),
        )


def test_linear_binding_adds_no_event_snapshot_or_authority_surface() -> None:
    import rci.core.events as events
    from rci.core.state import InquiryState

    assert not any("Linear" in name for name in events.__dict__)
    assert not any("linear" in name.lower() for name in InquiryState.model_fields)
    analysis = analyze_linear_query_family(_family((_observation("x", ((1, 0),)),)))
    assert analysis.standing is LinearAnalysisStanding.CANDIDATE_UNLICENSED
    assert not hasattr(analysis, "warrant_decision_id")
    assert not hasattr(analysis, "license_id")


def test_sdk_and_cli_return_the_same_canonical_inert_analysis(tmp_path: Path) -> None:
    family = _family((_observation("probe-x", ((1, 0),)),))
    analysis, check = RCI.analyze_exact_linear(family)
    family_file = tmp_path / "family.json"
    family_file.write_bytes(canonical_json_bytes(family))
    result = CliRunner().invoke(
        app,
        ["compression", "linear-analyze", "--family", str(family_file)],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload == {
        "analysis": analysis.model_dump(mode="json"),
        "check": check.model_dump(mode="json"),
        "family": family.model_dump(mode="json"),
    }
