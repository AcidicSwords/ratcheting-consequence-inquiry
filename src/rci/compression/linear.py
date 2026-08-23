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
    RECOVERABLE = ReopeningOutcome.RECOVERABLE
    REACQUISITION_REQUIRED = ReopeningOutcome.REACQUISITION_REQUIRED
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
    representation_policy_id: Identifier
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
    representation_policy_id: str = "exact-rational-linear-v1",
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
            family_id=self.family_id,
            family_fingerprint=self.family_fingerprint,
            gram=self.gram_matrix,
        ):
            raise ValueError("exact linear analysis identity must be content-derived")
        return self

    @property
    def fingerprint(self) -> str:
        return content_fingerprint("rci.exact-linear-analysis.v1", self)


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
    path_residue_id: Identifier | None = None
    recovery_license_id: Identifier | None = None

    @model_validator(mode="after")
    def validate_reopening(self) -> LinearKernelReopening:
        if self.incumbent_horizon_id == self.expanded_horizon_id:
            raise ValueError("linear reopening requires a different protected horizon")
        if self.reopened != (self.witness is not None):
            raise ValueError("an exact linear reopening requires its kernel witness")
        if self.strict_kernel_shrink and not (self.reopened and self.positive_observation_addition):
            raise ValueError("strict kernel shrink requires a positive observation addition")
        if not self.reopened:
            if self.disposition is not LinearReopeningDisposition.NOT_REOPENED:
                raise ValueError("an unchanged quotient must have the not-reopened disposition")
            if self.path_residue_id is not None or self.recovery_license_id is not None:
                raise ValueError("an unchanged quotient cannot consume recovery material")
        elif self.disposition is LinearReopeningDisposition.RECOVERABLE:
            if self.path_residue_id is None or self.recovery_license_id is not None:
                raise ValueError("recoverable linear reopening requires only exact residue")
        elif self.disposition is LinearReopeningDisposition.REACQUISITION_REQUIRED:
            if self.recovery_license_id is None or self.path_residue_id is not None:
                raise ValueError("reacquisition reopening requires only a recovery licence")
        elif self.disposition is LinearReopeningDisposition.UNKNOWN:
            if self.path_residue_id is not None or self.recovery_license_id is not None:
                raise ValueError("Unknown linear reopening cannot claim recovery material")
        else:
            raise ValueError("a reopened quotient requires a recovery disposition")
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
    *, family_id: str, family_fingerprint: str, gram: ExactRationalMatrix
) -> str:
    material = {
        "family_id": family_id,
        "family_fingerprint": family_fingerprint,
        "gram_matrix": gram,
        "backend": "sympy-exact-rational@1.14.0",
    }
    return f"lin_{content_fingerprint('rci.exact-linear-analysis-fields.v1', material)[:24]}"


def _analysis_id(family: LinearQueryFamily, gram: ExactRationalMatrix) -> str:
    return _analysis_identity(
        family_id=family.id,
        family_fingerprint=family.fingerprint,
        gram=gram,
    )


def analyze_linear_query_family(family: LinearQueryFamily) -> ExactLinearAnalysis:
    """Construct exact candidate quotient data with SymPy rational matrices."""

    dimension = family.ambient_dimension
    gram = Matrix.zeros(dimension, dimension)
    for observation in family.observations:
        operator = _sympy_matrix(observation.operator)
        weight = Rational(observation.weight.numerator, observation.weight.denominator)
        gram += weight * operator.T * operator
    gram_record = _from_sympy_matrix(gram)
    rref, _ = gram.rref()
    quotient_rows = [rref.row(index).T for index in range(rref.rows) if any(rref.row(index))]
    return ExactLinearAnalysis(
        id=_analysis_id(family, gram_record),
        family_id=family.id,
        family_fingerprint=family.fingerprint,
        gram_matrix=gram_record,
        quotient_basis=_from_sympy_vectors(quotient_rows),
        kernel_basis=_from_sympy_vectors(gram.nullspace()),
        rank=int(gram.rank()),
        minimum_linear_encoder_dimension=int(gram.rank()),
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


def independently_check_linear_analysis(
    family: LinearQueryFamily, analysis: ExactLinearAnalysis
) -> ExactLinearCheck:
    """Recompute every exact claim without using the SymPy analyzer."""

    issues: set[str] = set()
    if analysis.family_id != family.id or analysis.family_fingerprint != family.fingerprint:
        issues.add("foreign_family")
    expected_gram = _fraction_gram(family)
    rref, pivots = _rref(expected_gram)
    expected_quotient = [row for row in rref if any(row)]
    expected_kernel = _fraction_nullspace(expected_gram)
    query_rows = [
        row for observation in family.observations for row in _fraction_rows(observation.operator)
    ]
    _, query_pivots = _rref(query_rows)
    query_kernel = _fraction_nullspace(query_rows)
    if analysis.gram_matrix != _exact_matrix(expected_gram):
        issues.add("gram_mismatch")
    if analysis.id != _analysis_id(family, _exact_matrix(expected_gram)):
        issues.add("analysis_id_mismatch")
    if analysis.rank != len(pivots):
        issues.add("rank_mismatch")
    if analysis.minimum_linear_encoder_dimension != len(pivots):
        issues.add("linear_minimum_mismatch")
    if analysis.quotient_basis != _exact_vectors(expected_quotient):
        issues.add("quotient_basis_mismatch")
    if analysis.kernel_basis != _exact_vectors(expected_kernel):
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
    material = {
        "family_id": family.id,
        "family_fingerprint": family.fingerprint,
        "analysis_id": analysis.id,
        "analysis_fingerprint": analysis.fingerprint,
        "properties": property_outcomes,
        "issues": tuple(sorted(issues)),
        "checker": "fraction-rref-v1",
    }
    return ExactLinearCheck(
        id=f"lck_{content_fingerprint('rci.exact-linear-check.v1', material)[:24]}",
        family_id=family.id,
        family_fingerprint=family.fingerprint,
        analysis_id=analysis.id,
        analysis_fingerprint=analysis.fingerprint,
        verdict=LinearCheckVerdict.INVALID if invalid else LinearCheckVerdict.VALID,
        property_outcomes=property_outcomes,
        issue_ids=tuple(sorted(issues)),
    )


def build_linear_validation_properties(
    check: ExactLinearCheck,
    *,
    compression_contract_id: str,
    check_reference: CheckReference,
    invalid_witness_artifact: ArtifactRef | None = None,
) -> tuple[ExactPropertyValidation, ...]:
    """Bridge checked binding evidence into the existing G3A-H property stages.

    The aggregate must still resolve ``check_reference`` and separately record the
    resulting ``CompressionValidation``.  This pure adapter grants no warrant or licence.
    """

    if check.verdict is LinearCheckVerdict.INVALID and invalid_witness_artifact is None:
        raise ValueError("invalid linear validation requires an exact counterexample artifact")
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
                check=check_reference,
                witness_artifact=(
                    invalid_witness_artifact if outcome is ValidationOutcome.INVALID else None
                ),
            )
        )
    return tuple(properties)


def encode_quotient(
    analysis: ExactLinearAnalysis, source: ExactRationalVector
) -> ExactRationalCoordinates:
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


def detect_linear_kernel_reopening(
    *,
    incumbent_family: LinearQueryFamily,
    incumbent: ExactLinearAnalysis,
    expanded_family: LinearQueryFamily,
    expanded: ExactLinearAnalysis,
    path_residue_id: str | None = None,
    recovery_license_id: str | None = None,
) -> LinearKernelReopening:
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
    if path_residue_id is not None and recovery_license_id is not None:
        raise ValueError("linear reopening chooses residue or reacquisition, not both")

    witness = next(
        (vector for vector in incumbent.kernel_basis if any(_matvec(expanded.gram_matrix, vector))),
        None,
    )
    old_by_id = {item.id: item for item in incumbent_family.observations}
    new_by_id = {item.id: item for item in expanded_family.observations}
    positive_addition = bool(set(new_by_id) - set(old_by_id)) and all(
        new_by_id.get(identity) == observation for identity, observation in old_by_id.items()
    )
    strict_shrink = positive_addition and witness is not None and expanded.rank > incumbent.rank
    if witness is None:
        disposition = LinearReopeningDisposition.NOT_REOPENED
    elif path_residue_id is not None:
        disposition = LinearReopeningDisposition.RECOVERABLE
    elif recovery_license_id is not None:
        disposition = LinearReopeningDisposition.REACQUISITION_REQUIRED
    else:
        disposition = LinearReopeningDisposition.UNKNOWN
    material = {
        "incumbent": incumbent.fingerprint,
        "expanded": expanded.fingerprint,
        "incumbent_horizon": incumbent_family.protected_horizon_id,
        "expanded_horizon": expanded_family.protected_horizon_id,
        "witness": witness,
        "positive_addition": positive_addition,
        "strict_shrink": strict_shrink,
        "disposition": disposition,
        "path_residue_id": path_residue_id,
        "recovery_license_id": recovery_license_id,
    }
    return LinearKernelReopening(
        id=f"lrp_{content_fingerprint('rci.linear-kernel-reopening.v1', material)[:24]}",
        incumbent_analysis_id=incumbent.id,
        expanded_analysis_id=expanded.id,
        incumbent_horizon_id=incumbent_family.protected_horizon_id,
        expanded_horizon_id=expanded_family.protected_horizon_id,
        reopened=witness is not None,
        witness=witness,
        positive_observation_addition=positive_addition,
        strict_kernel_shrink=strict_shrink,
        disposition=disposition,
        path_residue_id=path_residue_id,
        recovery_license_id=recovery_license_id,
    )
