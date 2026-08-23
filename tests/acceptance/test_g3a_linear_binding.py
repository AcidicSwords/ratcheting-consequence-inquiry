from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from rci.cli import app
from rci.compression import (
    CompressionValidation,
    ExactLinearAnalysis,
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
    build_linear_query_family,
    build_linear_validation_properties,
    detect_linear_kernel_reopening,
    encode_quotient,
    independently_check_linear_analysis,
    protected_consequences_equal,
)
from rci.core.model import ArtifactRef
from rci.core.serialization import canonical_json_bytes
from rci.sdk import RCI
from rci.warrant.models import CheckReference

SCOPE = "a" * 64
DIGEST = "b" * 64


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

    check_ref = CheckReference(evidence_id="linear-evidence", checker_verdict_id="fraction-check")
    properties = build_linear_validation_properties(
        check,
        compression_contract_id="compression-contract",
        check_reference=check_ref,
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
    assert (
        next(
            item
            for item in validation.properties
            if item.property is ValidationProperty.RESIDUE_COMPLETENESS
        ).outcome
        is ValidationOutcome.NOT_CLAIMED
    )

    tampered_payload = analysis.model_dump(mode="python")
    tampered_payload["gram_matrix"] = _matrix(((2, 0), (0, 0)))
    tampered = ExactLinearAnalysis.model_validate(tampered_payload)
    invalid = independently_check_linear_analysis(family, tampered)
    assert invalid.verdict is LinearCheckVerdict.INVALID
    assert "gram_mismatch" in invalid.issue_ids
    with pytest.raises(ValueError, match="counterexample"):
        build_linear_validation_properties(
            invalid,
            compression_contract_id="compression-contract",
            check_reference=check_ref,
        )


def test_positive_probe_addition_reopens_exact_kernel_with_typed_disposition() -> None:
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

    recoverable = detect_linear_kernel_reopening(
        incumbent_family=old_family,
        incumbent=old,
        expanded_family=expanded_family,
        expanded=expanded,
        path_residue_id="path-residue-y",
    )
    assert recoverable.disposition is LinearReopeningDisposition.RECOVERABLE
    assert recoverable.path_residue_id == "path-residue-y"

    reacquire = detect_linear_kernel_reopening(
        incumbent_family=old_family,
        incumbent=old,
        expanded_family=expanded_family,
        expanded=expanded,
        recovery_license_id="recovery-license-y",
    )
    assert reacquire.disposition is LinearReopeningDisposition.REACQUISITION_REQUIRED


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
