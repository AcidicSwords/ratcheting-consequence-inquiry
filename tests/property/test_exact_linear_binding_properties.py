from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from rci.compression import (
    ExactRational,
    ExactRationalMatrix,
    LinearCheckVerdict,
    LinearEquivalenceScope,
    LinearOutputKind,
    WeightedLinearObservation,
    analyze_linear_query_family,
    build_linear_query_family,
    independently_check_linear_analysis,
)


@settings(max_examples=40, deadline=None)
@given(
    rows=st.lists(
        st.lists(st.integers(min_value=-4, max_value=4), min_size=1, max_size=4),
        min_size=1,
        max_size=5,
    ).filter(lambda values: len({len(row) for row in values}) == 1)
)
def test_sympy_analysis_matches_independent_fraction_elimination(rows: list[list[int]]) -> None:
    observations = tuple(
        WeightedLinearObservation(
            id=f"probe-{index:02d}",
            operator=ExactRationalMatrix(
                rows=(tuple(ExactRational(numerator=value) for value in row),)
            ),
        )
        for index, row in enumerate(rows)
    )
    family = build_linear_query_family(
        binding_revision="property-binding-v1",
        source_carrier_id="property-vector-carrier-v1",
        scope_fingerprint="c" * 64,
        protected_horizon_id="property-horizon-v1",
        output_kind=LinearOutputKind.SCALAR,
        equivalence_scope=LinearEquivalenceScope.UNIVERSAL_FINITE_FAMILY,
        observations=observations,
    )
    analysis = analyze_linear_query_family(family)
    assert independently_check_linear_analysis(family, analysis).verdict is (
        LinearCheckVerdict.VALID
    )
