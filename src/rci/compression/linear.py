"""Exact finite rational linear-consequence binding for G3A-L.

SymPy constructs candidate exact linear data.  The independent checker below uses only
``fractions.Fraction`` and never calls the SymPy construction path.  Neither result is a
warrant or a compression licence.
"""

from __future__ import annotations

from enum import StrEnum
from fractions import Fraction
from math import gcd
from typing import Literal

from pydantic import model_validator
from sympy import Matrix, Rational  # type: ignore[import-untyped]

from rci.claims.models import content_fingerprint
from rci.compression.models import (
    ExactPropertyValidation,
    ReopeningOutcome,
    ValidationOutcome,
    ValidationProperty,
)
from rci.core.model import ArtifactRef, FrozenModel, Identifier, Sha256Digest
from rci.warrant.models import CheckReference


class LinearEquivalenceScope(StrEnum):
    UNIVERSAL_FINITE_FAMILY = "universal_finite_family"
    FINITE_SUPPORT_ALMOST_SURE = "finite_support_almost_sure"


class LinearOutputKind(StrEnum):
    SCALAR = "scalar"
    VECTOR = "vector"


class LinearAnalysisStanding(StrEnum):
    CANDIDATE_UNLICENSED = "candidate_unlicensed"


class LinearCheckVerdict(StrEnum):
    VALID = "valid"
    INVALID = "invalid"


class LinearReopeningDisposition(StrEnum):
    NOT_REOPENED = "not_reopened"
    UNKNOWN = ReopeningOutcome.UNKNOWN


class ExactRational(FrozenModel):
    numerator: int
    denominator: int = 1

    @model_validator(mode="after")
    def validate_canonical(self) -> ExactRational:
        if self.denominator <= 0:
            raise ValueError("exact rational denominators must be positive")
        if gcd(abs(self.numerator), self.denominator) != 1:
            raise ValueError("exact rationals must be reduced")
        if self.numerator == 0 and self.denominator != 1:
            raise ValueError("zero has the unique canonical denominator one")
        return self

    @classmethod
    def from_fraction(cls, value: Fraction) -> ExactRational:
        return cls(numerator=value.numerator, denominator=value.denominator)

    def as_fraction(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)


ZERO = ExactRational(numerator=0)
ONE = ExactRational(numerator=1)


class ExactRationalVector(FrozenModel):
    values: tuple[ExactRational, ...]

    @model_validator(mode="after")
    def validate_vector(self) -> ExactRationalVector:
        if not self.values:
            raise ValueError("exact rational vectors cannot be empty")
        return self


class ExactRationalCoordinates(FrozenModel):
    """Quotient coordinates; the exact zero-dimensional quotient is the empty tuple."""

    values: tuple[ExactRational, ...]


class ExactRationalMatrix(FrozenModel):
    rows: tuple[tuple[ExactRational, ...], ...]

    @model_validator(mode="after")
    def validate_matrix(self) -> ExactRationalMatrix:
        if not self.rows or not self.rows[0]:
            raise ValueError("exact rational matrices cannot be empty")
        width = len(self.rows[0])
        if any(len(row) != width for row in self.rows):
            raise ValueError("exact rational matrices must be rectangular")
        return self

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def column_count(self) -> int:
        return len(self.rows[0])


class WeightedLinearObservation(FrozenModel):
    id: Identifier
    operator: ExactRationalMatrix
    weight: ExactRational = ONE

    @model_validator(mode="after")
    def validate_weight(self) -> WeightedLinearObservation:
        if self.weight.as_fraction() <= 0:
            raise ValueError("finite linear observation weights must be strictly positive")
        return self


def _family_material(
    *,
    binding_revision: str,
    source_carrier_id: str,
    scope_fingerprint: str,
    protected_horizon_id: str,
    output_kind: LinearOutputKind,
    equivalence_scope: LinearEquivalenceScope,
    observations: tuple[WeightedLinearObservation, ...],
    representation_policy_id: str,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "binding_revision": binding_revision,
        "source_carrier_id": source_carrier_id,
        "scope_fingerprint": scope_fingerprint,
        "protected_horizon_id": protected_horizon_id,
        "output_kind": output_kind,
        "equivalence_scope": equivalence_scope,
        "observations": observations,
        "representation_policy_id": representation_policy_id,
        "gram_semantics": "weighted_operator_gram",
        "distribution_moment_semantics": (
            "uncentered_second_moment"
            if equivalence_scope is LinearEquivalenceScope.FINITE_SUPPORT_ALMOST_SURE
            else None
        ),
    }


class LinearQueryFamily(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    binding_revision: Identifier
    source_carrier_id: Identifier
    scope_fingerprint: Sha256Digest
    protected_horizon_id: Identifier
    output_kind: LinearOutputKind
    equivalence_scope: LinearEquivalenceScope
    observations: tuple[WeightedLinearObservation, ...]
    representation_policy_id: Literal["exact-rational-linear-v1"]
    gram_semantics: Literal["weighted_operator_gram"] = "weighted_operator_gram"
    distribution_moment_semantics: Literal["uncentered_second_moment"] | None = None

    @model_validator(mode="after")
    def validate_family(self) -> LinearQueryFamily:
        if not self.observations:
            raise ValueError("linear query families require at least one observation")
        ids = tuple(item.id for item in self.observations)
        if len(set(ids)) != len(ids) or ids != tuple(sorted(ids)):
            raise ValueError("linear observations must have unique canonical identities")
        dimension = self.observations[0].operator.column_count
        if any(item.operator.column_count != dimension for item in self.observations):
            raise ValueError("all linear observations must share one source dimension")
        if self.output_kind is LinearOutputKind.SCALAR and any(
            item.operator.row_count != 1 for item in self.observations
        ):
            raise ValueError("scalar linear observations must have exactly one output row")
        if (
            self.output_kind is LinearOutputKind.VECTOR
            and self.equivalence_scope is LinearEquivalenceScope.UNIVERSAL_FINITE_FAMILY
        ):
            raise ValueError("G3A-L vector-output families are finite-support almost-sure only")
        weights = tuple(item.weight.as_fraction() for item in self.observations)
        distributional = self.equivalence_scope is LinearEquivalenceScope.FINITE_SUPPORT_ALMOST_SURE
        if distributional and sum(weights, Fraction()) != 1:
            raise ValueError("finite-support almost-sure weights must sum exactly to one")
        if distributional != (self.distribution_moment_semantics is not None):
            raise ValueError("only distributional families use uncentered second-moment semantics")
        expected_id = _family_id(
            **_family_material(
                binding_revision=self.binding_revision,
                source_carrier_id=self.source_carrier_id,
                scope_fingerprint=self.scope_fingerprint,
                protected_horizon_id=self.protected_horizon_id,
                output_kind=self.output_kind,
                equivalence_scope=self.equivalence_scope,
                observations=self.observations,
                representation_policy_id=self.representation_policy_id,
            )
        )
        if self.id != expected_id:
            raise ValueError("linear query family identity must be content-derived")
        return self

    @property
    def ambient_dimension(self) -> int:
        return self.observations[0].operator.column_count

    @property
    def fingerprint(self) -> str:
        return content_fingerprint("rci.linear-query-family.v1", self)


def _family_id(**fields: object) -> str:
    return f"lqf_{content_fingerprint('rci.linear-query-family-fields.v1', fields)[:24]}"


def build_linear_query_family(
    *,
    binding_revision: str,
    source_carrier_id: str,
    scope_fingerprint: str,
    protected_horizon_id: str,
    output_kind: LinearOutputKind,
    equivalence_scope: LinearEquivalenceScope,
    observations: tuple[WeightedLinearObservation, ...],
    representation_policy_id: Literal["exact-rational-linear-v1"] = "exact-rational-linear-v1",
) -> LinearQueryFamily:
    ordered = tuple(sorted(observations, key=lambda item: item.id))
    fields = _family_material(
        binding_revision=binding_revision,
        source_carrier_id=source_carrier_id,
        scope_fingerprint=scope_fingerprint,
        protected_horizon_id=protected_horizon_id,
        output_kind=output_kind,
        equivalence_scope=equivalence_scope,
        observations=ordered,
        representation_policy_id=representation_policy_id,
    )
    return LinearQueryFamily(
        id=_family_id(**fields),
        binding_revision=binding_revision,
        source_carrier_id=source_carrier_id,
        scope_fingerprint=scope_fingerprint,
        protected_horizon_id=protected_horizon_id,
        output_kind=output_kind,
        equivalence_scope=equivalence_scope,
        observations=ordered,
        representation_policy_id=representation_policy_id,
        distribution_moment_semantics=(
            "uncentered_second_moment"
            if equivalence_scope is LinearEquivalenceScope.FINITE_SUPPORT_ALMOST_SURE
            else None
        ),
    )


class ExactLinearAnalysis(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    family_id: Identifier
    family_fingerprint: Sha256Digest
    gram_matrix: ExactRationalMatrix
    quotient_basis: tuple[ExactRationalVector, ...]
    kernel_basis: tuple[ExactRationalVector, ...]
    rank: int
    minimum_linear_encoder_dimension: int
    minimality_scope: Literal["linear_encoders_only"] = "linear_encoders_only"
    equivalence_scope: LinearEquivalenceScope
    construction_backend_id: Literal["sympy-exact-rational"] = "sympy-exact-rational"
    construction_backend_version: Literal["1.14.0"] = "1.14.0"
    standing: LinearAnalysisStanding = LinearAnalysisStanding.CANDIDATE_UNLICENSED

    @model_validator(mode="after")
    def validate_analysis(self) -> ExactLinearAnalysis:
        if self.rank < 0 or self.rank > self.gram_matrix.column_count:
            raise ValueError("linear rank must fit the declared ambient dimension")
        if self.minimum_linear_encoder_dimension != self.rank:
            raise ValueError("minimum linear encoder dimension is the exact rank")
        if len(self.quotient_basis) != self.rank:
            raise ValueError("quotient basis cardinality must equal exact rank")
        if len(self.kernel_basis) != self.gram_matrix.column_count - self.rank:
            raise ValueError("kernel basis cardinality must equal exact nullity")
        width = self.gram_matrix.column_count
        if any(
            len(vector.values) != width for vector in (*self.quotient_basis, *self.kernel_basis)
        ):
            raise ValueError("linear basis vectors must inhabit the source carrier")
        if self.id != _analysis_identity(
            schema_version=self.schema_version,
            family_id=self.family_id,
            family_fingerprint=self.family_fingerprint,
            gram=self.gram_matrix,
            quotient_basis=self.quotient_basis,
            kernel_basis=self.kernel_basis,
            rank=self.rank,
            minimum_linear_encoder_dimension=self.minimum_linear_encoder_dimension,
            minimality_scope=self.minimality_scope,
            equivalence_scope=self.equivalence_scope,
            construction_backend_id=self.construction_backend_id,
            construction_backend_version=self.construction_backend_version,
            standing=self.standing,
        ):
            raise ValueError("exact linear analysis identity must be content-derived")
        return self

    @property
    def fingerprint(self) -> str:
        return content_fingerprint(
            "rci.exact-linear-analysis.v1",
            self.model_dump(mode="json", warnings=False),
        )


class ExactLinearCheck(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    family_id: Identifier
    family_fingerprint: Sha256Digest
    analysis_id: Identifier
    analysis_fingerprint: Sha256Digest
    verdict: LinearCheckVerdict
    property_outcomes: tuple[tuple[ValidationProperty, ValidationOutcome], ...]
    issue_ids: tuple[Identifier, ...] = ()
    checker_id: Literal["fraction-rref-v1"] = "fraction-rref-v1"
    standing: Literal["candidate_check_evidence"] = "candidate_check_evidence"

    @model_validator(mode="after")
    def validate_check(self) -> ExactLinearCheck:
        properties = tuple(item[0] for item in self.property_outcomes)
        if properties != tuple(sorted(properties, key=lambda item: item.value)):
            raise ValueError("linear property outcomes must be canonically ordered")
        if len(set(properties)) != len(properties):
            raise ValueError("linear property outcomes must be unique")
        invalid = any(outcome is ValidationOutcome.INVALID for _, outcome in self.property_outcomes)
        if (self.verdict is LinearCheckVerdict.INVALID) != invalid:
            raise ValueError("linear check verdict must match its property outcomes")
        if invalid != bool(self.issue_ids):
            raise ValueError("invalid linear checks require canonical issues")
        if tuple(sorted(set(self.issue_ids))) != self.issue_ids:
            raise ValueError("linear check issues must be unique and canonical")
        if set(properties) != set(ValidationProperty):
            raise ValueError("linear checks must disposition every exact validation property")
        if self.id != _linear_check_id(
            family_id=self.family_id,
            family_fingerprint=self.family_fingerprint,
            analysis_id=self.analysis_id,
            analysis_fingerprint=self.analysis_fingerprint,
            property_outcomes=self.property_outcomes,
            issue_ids=self.issue_ids,
            checker_id=self.checker_id,
            standing=self.standing,
        ):
            raise ValueError("exact linear check identity must be content-derived")
        return self


class LinearKernelReopening(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    incumbent_analysis_id: Identifier
    expanded_analysis_id: Identifier
    incumbent_horizon_id: Identifier
    expanded_horizon_id: Identifier
    reopened: bool
    witness: ExactRationalVector | None = None
    positive_observation_addition: bool
    strict_kernel_shrink: bool
    disposition: LinearReopeningDisposition

    @model_validator(mode="after")
    def validate_reopening(self) -> LinearKernelReopening:
        if self.incumbent_horizon_id == self.expanded_horizon_id:
            raise ValueError("linear reopening requires a different protected horizon")
        if self.reopened != (self.witness is not None):
            raise ValueError("an exact linear reopening requires its kernel witness")
        if self.strict_kernel_shrink and not self.reopened:
            raise ValueError("strict kernel shrink requires an exact reopening witness")
        if not self.reopened:
            if self.disposition is not LinearReopeningDisposition.NOT_REOPENED:
                raise ValueError("an unchanged quotient must have the not-reopened disposition")
        elif self.disposition is not LinearReopeningDisposition.UNKNOWN:
            raise ValueError(
                "pure linear reopening remains Unknown until aggregate-owned recovery resolution"
            )
        if self.id != _linear_reopening_id(
            incumbent_analysis_id=self.incumbent_analysis_id,
            expanded_analysis_id=self.expanded_analysis_id,
            incumbent_horizon_id=self.incumbent_horizon_id,
            expanded_horizon_id=self.expanded_horizon_id,
            witness=self.witness,
            positive_observation_addition=self.positive_observation_addition,
            strict_kernel_shrink=self.strict_kernel_shrink,
            disposition=self.disposition,
        ):
            raise ValueError("linear kernel reopening identity must be content-derived")
        return self


def _fraction_rows(matrix: ExactRationalMatrix) -> list[list[Fraction]]:
    return [[value.as_fraction() for value in row] for row in matrix.rows]


def _exact_matrix(rows: list[list[Fraction]]) -> ExactRationalMatrix:
    return ExactRationalMatrix(
        rows=tuple(tuple(ExactRational.from_fraction(value) for value in row) for row in rows)
    )


def _exact_vectors(rows: list[list[Fraction]]) -> tuple[ExactRationalVector, ...]:
    return tuple(
        ExactRationalVector(values=tuple(ExactRational.from_fraction(value) for value in row))
        for row in rows
    )


def _sympy_matrix(matrix: ExactRationalMatrix) -> Matrix:
    return Matrix(
        [[Rational(value.numerator, value.denominator) for value in row] for row in matrix.rows]
    )


def _from_sympy_matrix(matrix: Matrix) -> ExactRationalMatrix:
    return ExactRationalMatrix(
        rows=tuple(
            tuple(
                ExactRational(numerator=int(value.p), denominator=int(value.q))
                for value in matrix.row(row_index)
            )
            for row_index in range(matrix.rows)
        )
    )


def _from_sympy_vectors(vectors: list[Matrix]) -> tuple[ExactRationalVector, ...]:
    return tuple(
        ExactRationalVector(
            values=tuple(
                ExactRational(numerator=int(value.p), denominator=int(value.q)) for value in vector
            )
        )
        for vector in vectors
    )


def _analysis_identity(
    *,
    schema_version: int,
    family_id: str,
    family_fingerprint: str,
    gram: ExactRationalMatrix,
    quotient_basis: tuple[ExactRationalVector, ...],
    kernel_basis: tuple[ExactRationalVector, ...],
    rank: int,
    minimum_linear_encoder_dimension: int,
    minimality_scope: str,
    equivalence_scope: LinearEquivalenceScope,
    construction_backend_id: str,
    construction_backend_version: str,
    standing: LinearAnalysisStanding,
) -> str:
    material = {
        "schema_version": schema_version,
        "family_id": family_id,
        "family_fingerprint": family_fingerprint,
        "gram_matrix": gram,
        "quotient_basis": quotient_basis,
        "kernel_basis": kernel_basis,
        "rank": rank,
        "minimum_linear_encoder_dimension": minimum_linear_encoder_dimension,
        "minimality_scope": minimality_scope,
        "equivalence_scope": equivalence_scope,
        "construction_backend_id": construction_backend_id,
        "construction_backend_version": construction_backend_version,
        "standing": standing,
    }
    return f"lin_{content_fingerprint('rci.exact-linear-analysis-fields.v1', material)[:24]}"


def _analysis_id(
    family: LinearQueryFamily,
    *,
    gram: ExactRationalMatrix,
    quotient_basis: tuple[ExactRationalVector, ...],
    kernel_basis: tuple[ExactRationalVector, ...],
    rank: int,
) -> str:
    return _analysis_identity(
        schema_version=1,
        family_id=family.id,
        family_fingerprint=family.fingerprint,
        gram=gram,
        quotient_basis=quotient_basis,
        kernel_basis=kernel_basis,
        rank=rank,
        minimum_linear_encoder_dimension=rank,
        minimality_scope="linear_encoders_only",
        equivalence_scope=family.equivalence_scope,
        construction_backend_id="sympy-exact-rational",
        construction_backend_version="1.14.0",
        standing=LinearAnalysisStanding.CANDIDATE_UNLICENSED,
    )


def _require_intact_family(family: LinearQueryFamily) -> None:
    try:
        validated = LinearQueryFamily.model_validate(
            family.model_dump(mode="python", warnings=False)
        )
    except ValueError as exc:
        raise ValueError("exact linear operations require an intact query family") from exc
    if validated != family:
        raise ValueError("exact linear operations require an intact query family")


def analyze_linear_query_family(family: LinearQueryFamily) -> ExactLinearAnalysis:
    """Construct exact candidate quotient data with SymPy rational matrices."""

    _require_intact_family(family)
    dimension = family.ambient_dimension
    gram = Matrix.zeros(dimension, dimension)
    for observation in family.observations:
        operator = _sympy_matrix(observation.operator)
        weight = Rational(observation.weight.numerator, observation.weight.denominator)
        gram += weight * operator.T * operator
    gram_record = _from_sympy_matrix(gram)
    rref, _ = gram.rref()
    quotient_rows = [rref.row(index).T for index in range(rref.rows) if any(rref.row(index))]
    quotient_basis = _from_sympy_vectors(quotient_rows)
    kernel_basis = _from_sympy_vectors(gram.nullspace())
    rank = int(gram.rank())
    return ExactLinearAnalysis(
        id=_analysis_id(
            family,
            gram=gram_record,
            quotient_basis=quotient_basis,
            kernel_basis=kernel_basis,
            rank=rank,
        ),
        family_id=family.id,
        family_fingerprint=family.fingerprint,
        gram_matrix=gram_record,
        quotient_basis=quotient_basis,
        kernel_basis=kernel_basis,
        rank=rank,
        minimum_linear_encoder_dimension=rank,
        equivalence_scope=family.equivalence_scope,
    )


def _rref(rows: list[list[Fraction]]) -> tuple[list[list[Fraction]], tuple[int, ...]]:
    work = [row[:] for row in rows]
    row_count = len(work)
    column_count = len(work[0])
    pivot_row = 0
    pivots: list[int] = []
    for column in range(column_count):
        selected = next(
            (index for index in range(pivot_row, row_count) if work[index][column]), None
        )
        if selected is None:
            continue
        work[pivot_row], work[selected] = work[selected], work[pivot_row]
        divisor = work[pivot_row][column]
        work[pivot_row] = [value / divisor for value in work[pivot_row]]
        for index in range(row_count):
            if index == pivot_row:
                continue
            factor = work[index][column]
            if factor:
                work[index] = [
                    value - factor * pivot
                    for value, pivot in zip(work[index], work[pivot_row], strict=True)
                ]
        pivots.append(column)
        pivot_row += 1
        if pivot_row == row_count:
            break
    return work, tuple(pivots)


def _fraction_gram(family: LinearQueryFamily) -> list[list[Fraction]]:
    dimension = family.ambient_dimension
    gram = [[Fraction() for _ in range(dimension)] for _ in range(dimension)]
    for observation in family.observations:
        weight = observation.weight.as_fraction()
        for row in _fraction_rows(observation.operator):
            for left in range(dimension):
                for right in range(dimension):
                    gram[left][right] += weight * row[left] * row[right]
    return gram


def _fraction_nullspace(rows: list[list[Fraction]]) -> list[list[Fraction]]:
    rref, pivots = _rref(rows)
    column_count = len(rows[0])
    free = [column for column in range(column_count) if column not in pivots]
    basis: list[list[Fraction]] = []
    for free_column in free:
        vector = [Fraction() for _ in range(column_count)]
        vector[free_column] = Fraction(1)
        for row_index, pivot_column in enumerate(pivots):
            vector[pivot_column] = -rref[row_index][free_column]
        basis.append(vector)
    return basis


def _linear_check_id(
    *,
    family_id: str,
    family_fingerprint: str,
    analysis_id: str,
    analysis_fingerprint: str,
    property_outcomes: tuple[tuple[ValidationProperty, ValidationOutcome], ...],
    issue_ids: tuple[str, ...],
    checker_id: str,
    standing: str,
) -> str:
    material = {
        "schema_version": 1,
        "family_id": family_id,
        "family_fingerprint": family_fingerprint,
        "analysis_id": analysis_id,
        "analysis_fingerprint": analysis_fingerprint,
        "properties": property_outcomes,
        "issues": issue_ids,
        "checker": checker_id,
        "standing": standing,
    }
    return f"lck_{content_fingerprint('rci.exact-linear-check.v1', material)[:24]}"


def independently_check_linear_analysis(
    family: LinearQueryFamily, analysis: ExactLinearAnalysis
) -> ExactLinearCheck:
    """Recompute every exact claim without using the SymPy analyzer."""

    _require_intact_family(family)
    issues: set[str] = set()
    if analysis.family_id != family.id or analysis.family_fingerprint != family.fingerprint:
        issues.add("foreign_family")
    expected_gram = _fraction_gram(family)
    rref, pivots = _rref(expected_gram)
    expected_quotient = [row for row in rref if any(row)]
    expected_kernel = _fraction_nullspace(expected_gram)
    expected_gram_record = _exact_matrix(expected_gram)
    expected_quotient_record = _exact_vectors(expected_quotient)
    expected_kernel_record = _exact_vectors(expected_kernel)
    expected_analysis_id = _analysis_id(
        family,
        gram=expected_gram_record,
        quotient_basis=expected_quotient_record,
        kernel_basis=expected_kernel_record,
        rank=len(pivots),
    )
    candidate_analysis_id = _analysis_identity(
        schema_version=analysis.schema_version,
        family_id=analysis.family_id,
        family_fingerprint=analysis.family_fingerprint,
        gram=analysis.gram_matrix,
        quotient_basis=analysis.quotient_basis,
        kernel_basis=analysis.kernel_basis,
        rank=analysis.rank,
        minimum_linear_encoder_dimension=analysis.minimum_linear_encoder_dimension,
        minimality_scope=analysis.minimality_scope,
        equivalence_scope=analysis.equivalence_scope,
        construction_backend_id=analysis.construction_backend_id,
        construction_backend_version=analysis.construction_backend_version,
        standing=analysis.standing,
    )
    query_rows = [
        row for observation in family.observations for row in _fraction_rows(observation.operator)
    ]
    _, query_pivots = _rref(query_rows)
    query_kernel = _fraction_nullspace(query_rows)
    if analysis.schema_version != 1:
        issues.add("schema_version_mismatch")
    if analysis.construction_backend_id != "sympy-exact-rational":
        issues.add("construction_backend_mismatch")
    if analysis.construction_backend_version != "1.14.0":
        issues.add("construction_backend_version_mismatch")
    if analysis.standing != LinearAnalysisStanding.CANDIDATE_UNLICENSED:
        issues.add("standing_mismatch")
    if analysis.gram_matrix != expected_gram_record:
        issues.add("gram_mismatch")
    if analysis.id != expected_analysis_id or analysis.id != candidate_analysis_id:
        issues.add("analysis_id_mismatch")
    if analysis.rank != len(pivots):
        issues.add("rank_mismatch")
    if analysis.minimum_linear_encoder_dimension != len(pivots):
        issues.add("linear_minimum_mismatch")
    if analysis.minimality_scope != "linear_encoders_only":
        issues.add("minimality_scope_mismatch")
    if analysis.quotient_basis != expected_quotient_record:
        issues.add("quotient_basis_mismatch")
    if analysis.kernel_basis != expected_kernel_record:
        issues.add("kernel_basis_mismatch")
    if len(query_pivots) != len(pivots):
        issues.add("query_rank_mismatch")
    if _exact_vectors(query_kernel) != _exact_vectors(expected_kernel):
        issues.add("query_kernel_mismatch")
    if analysis.equivalence_scope is not family.equivalence_scope:
        issues.add("equivalence_scope_mismatch")

    invalid = bool(issues)
    property_outcomes = tuple(
        sorted(
            (
                (
                    ValidationProperty.CONSEQUENCE_FACTORIZATION,
                    ValidationOutcome.INVALID if invalid else ValidationOutcome.VALID,
                ),
                (ValidationProperty.CONTINUATION_COMPATIBILITY, ValidationOutcome.NOT_CLAIMED),
                (ValidationProperty.DETERMINATION_DESCENT, ValidationOutcome.NOT_CLAIMED),
                (
                    ValidationProperty.EXACT_EQUIVALENCE,
                    ValidationOutcome.INVALID if invalid else ValidationOutcome.VALID,
                ),
                (ValidationProperty.RECURSIVE_UPDATE, ValidationOutcome.NOT_CLAIMED),
                (ValidationProperty.RESIDUE_COMPLETENESS, ValidationOutcome.NOT_CLAIMED),
            ),
            key=lambda item: item[0].value,
        )
    )
    issue_ids = tuple(sorted(issues))
    check_id = _linear_check_id(
        family_id=family.id,
        family_fingerprint=family.fingerprint,
        analysis_id=analysis.id,
        analysis_fingerprint=analysis.fingerprint,
        property_outcomes=property_outcomes,
        issue_ids=issue_ids,
        checker_id="fraction-rref-v1",
        standing="candidate_check_evidence",
    )
    return ExactLinearCheck(
        id=check_id,
        family_id=family.id,
        family_fingerprint=family.fingerprint,
        analysis_id=analysis.id,
        analysis_fingerprint=analysis.fingerprint,
        verdict=LinearCheckVerdict.INVALID if invalid else LinearCheckVerdict.VALID,
        property_outcomes=property_outcomes,
        issue_ids=issue_ids,
    )


def build_linear_validation_properties(
    check: ExactLinearCheck,
    *,
    compression_contract_id: str,
    property_check_references: tuple[tuple[ValidationProperty, CheckReference], ...],
    invalid_witness_artifact: ArtifactRef | None = None,
) -> tuple[ExactPropertyValidation, ...]:
    """Bridge checked binding evidence into the existing G3A-H property stages.

    The aggregate must still resolve ``check_reference`` and separately record the
    resulting ``CompressionValidation``.  This pure adapter grants no warrant or licence.
    """

    if (
        check.schema_version != 1
        or check.checker_id != "fraction-rref-v1"
        or check.standing != "candidate_check_evidence"
        or check.id
        != _linear_check_id(
            family_id=check.family_id,
            family_fingerprint=check.family_fingerprint,
            analysis_id=check.analysis_id,
            analysis_fingerprint=check.analysis_fingerprint,
            property_outcomes=check.property_outcomes,
            issue_ids=check.issue_ids,
            checker_id=check.checker_id,
            standing=check.standing,
        )
    ):
        raise ValueError("linear validation requires an intact candidate check record")
    if check.verdict is LinearCheckVerdict.INVALID and invalid_witness_artifact is None:
        raise ValueError("invalid linear validation requires an exact counterexample artifact")
    referenced_properties = tuple(item[0] for item in property_check_references)
    if referenced_properties != tuple(
        sorted(referenced_properties, key=lambda item: item.value)
    ) or len(set(referenced_properties)) != len(referenced_properties):
        raise ValueError("linear property check references must be unique and canonical")
    claimed_properties = {
        property_kind
        for property_kind, outcome in check.property_outcomes
        if outcome is not ValidationOutcome.NOT_CLAIMED
    }
    if set(referenced_properties) != claimed_properties:
        raise ValueError("each claimed linear property requires its own exact check reference")
    checks_by_property = dict(property_check_references)
    properties: list[ExactPropertyValidation] = []
    for property_kind, outcome in check.property_outcomes:
        if outcome is ValidationOutcome.NOT_CLAIMED:
            properties.append(ExactPropertyValidation(property=property_kind, outcome=outcome))
            continue
        properties.append(
            ExactPropertyValidation(
                property=property_kind,
                outcome=outcome,
                proposition_id=(
                    f"compression-property:{compression_contract_id}:{property_kind.value}"
                ),
                check=checks_by_property[property_kind],
                witness_artifact=(
                    invalid_witness_artifact if outcome is ValidationOutcome.INVALID else None
                ),
            )
        )
    return tuple(properties)


def _require_intact_analysis(analysis: ExactLinearAnalysis) -> None:
    try:
        validated = ExactLinearAnalysis.model_validate(
            analysis.model_dump(mode="python", warnings=False)
        )
    except ValueError as exc:
        raise ValueError("exact linear operations require an intact analysis record") from exc
    if validated != analysis:
        raise ValueError("exact linear operations require an intact analysis record")


def encode_quotient(
    analysis: ExactLinearAnalysis, source: ExactRationalVector
) -> ExactRationalCoordinates:
    _require_intact_analysis(analysis)
    if len(source.values) != analysis.gram_matrix.column_count:
        raise ValueError("source vector does not inhabit the analyzed carrier")
    source_values = [value.as_fraction() for value in source.values]
    coordinates = tuple(
        ExactRational.from_fraction(
            sum(
                (
                    coefficient.as_fraction() * value
                    for coefficient, value in zip(basis.values, source_values, strict=True)
                ),
                Fraction(),
            )
        )
        for basis in analysis.quotient_basis
    )
    return ExactRationalCoordinates(values=coordinates)


def protected_consequences_equal(
    family: LinearQueryFamily,
    left: ExactRationalVector,
    right: ExactRationalVector,
) -> bool:
    _require_intact_family(family)
    if (
        len(left.values) != family.ambient_dimension
        or len(right.values) != family.ambient_dimension
    ):
        raise ValueError("comparison vectors must inhabit the query-family carrier")
    delta = [
        left_value.as_fraction() - right_value.as_fraction()
        for left_value, right_value in zip(left.values, right.values, strict=True)
    ]
    return all(
        sum(
            (coefficient * value for coefficient, value in zip(row, delta, strict=True)),
            Fraction(),
        )
        == 0
        for observation in family.observations
        for row in _fraction_rows(observation.operator)
    )


def _matvec(matrix: ExactRationalMatrix, vector: ExactRationalVector) -> tuple[Fraction, ...]:
    return tuple(
        sum(
            (
                coefficient.as_fraction() * value.as_fraction()
                for coefficient, value in zip(row, vector.values, strict=True)
            ),
            Fraction(),
        )
        for row in matrix.rows
    )


def _linear_reopening_id(
    *,
    incumbent_analysis_id: str,
    expanded_analysis_id: str,
    incumbent_horizon_id: str,
    expanded_horizon_id: str,
    witness: ExactRationalVector | None,
    positive_observation_addition: bool,
    strict_kernel_shrink: bool,
    disposition: LinearReopeningDisposition,
) -> str:
    material = {
        "schema_version": 1,
        "incumbent_analysis_id": incumbent_analysis_id,
        "expanded_analysis_id": expanded_analysis_id,
        "incumbent_horizon_id": incumbent_horizon_id,
        "expanded_horizon_id": expanded_horizon_id,
        "witness": witness,
        "positive_observation_addition": positive_observation_addition,
        "strict_kernel_shrink": strict_kernel_shrink,
        "disposition": disposition,
    }
    return f"lrp_{content_fingerprint('rci.linear-kernel-reopening.v1', material)[:24]}"


def detect_linear_kernel_reopening(
    *,
    incumbent_family: LinearQueryFamily,
    incumbent: ExactLinearAnalysis,
    expanded_family: LinearQueryFamily,
    expanded: ExactLinearAnalysis,
) -> LinearKernelReopening:
    _require_intact_family(incumbent_family)
    _require_intact_family(expanded_family)
    if (
        incumbent_family.binding_revision != expanded_family.binding_revision
        or incumbent_family.source_carrier_id != expanded_family.source_carrier_id
        or incumbent_family.scope_fingerprint != expanded_family.scope_fingerprint
        or incumbent_family.ambient_dimension != expanded_family.ambient_dimension
        or incumbent_family.output_kind is not expanded_family.output_kind
        or incumbent_family.equivalence_scope is not expanded_family.equivalence_scope
    ):
        raise ValueError(
            "linear reopening requires one binding, carrier, scope, dimension, and semantics"
        )
    if (
        incumbent.family_id != incumbent_family.id
        or incumbent.family_fingerprint != incumbent_family.fingerprint
        or expanded.family_id != expanded_family.id
        or expanded.family_fingerprint != expanded_family.fingerprint
    ):
        raise ValueError("linear reopening analyses must belong to their exact query families")
    if (
        independently_check_linear_analysis(incumbent_family, incumbent).verdict
        is not LinearCheckVerdict.VALID
        or independently_check_linear_analysis(expanded_family, expanded).verdict
        is not LinearCheckVerdict.VALID
    ):
        raise ValueError("linear reopening requires independently valid exact analyses")
    witness = next(
        (vector for vector in incumbent.kernel_basis if any(_matvec(expanded.gram_matrix, vector))),
        None,
    )
    old_by_id = {item.id: item for item in incumbent_family.observations}
    new_by_id = {item.id: item for item in expanded_family.observations}
    positive_addition = bool(set(new_by_id) - set(old_by_id)) and all(
        (new_observation := new_by_id.get(identity)) is not None
        and new_observation.operator == observation.operator
        for identity, observation in old_by_id.items()
    )
    expanded_kernel_within_incumbent = all(
        not any(_matvec(incumbent.gram_matrix, vector)) for vector in expanded.kernel_basis
    )
    strict_shrink = (
        witness is not None and expanded_kernel_within_incumbent and expanded.rank > incumbent.rank
    )
    disposition = (
        LinearReopeningDisposition.NOT_REOPENED
        if witness is None
        else LinearReopeningDisposition.UNKNOWN
    )
    reopening_id = _linear_reopening_id(
        incumbent_analysis_id=incumbent.id,
        expanded_analysis_id=expanded.id,
        incumbent_horizon_id=incumbent_family.protected_horizon_id,
        expanded_horizon_id=expanded_family.protected_horizon_id,
        witness=witness,
        positive_observation_addition=positive_addition,
        strict_kernel_shrink=strict_shrink,
        disposition=disposition,
    )
    return LinearKernelReopening(
        id=reopening_id,
        incumbent_analysis_id=incumbent.id,
        expanded_analysis_id=expanded.id,
        incumbent_horizon_id=incumbent_family.protected_horizon_id,
        expanded_horizon_id=expanded_family.protected_horizon_id,
        reopened=witness is not None,
        witness=witness,
        positive_observation_addition=positive_addition,
        strict_kernel_shrink=strict_shrink,
        disposition=disposition,
    )
