from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class EvaluationCase(_FrozenModel):
    id: str
    contradiction_localized: bool
    false_necessity_rejected: bool
    correction_opened: bool
    boundary_found: bool
    counterexample_preserved: bool
    warrant_lawful: bool
    order_stable: bool
    context_bounded: bool

    @model_validator(mode="after")
    def validate_id(self) -> EvaluationCase:
        if not self.id:
            raise ValueError("evaluation case id is required")
        return self


class EvaluationReport(_FrozenModel):
    case_count: int
    contradiction_rate: float
    false_necessity_rejection_rate: float
    correction_rate: float
    boundary_rate: float
    counterexample_rate: float
    lawful_warrant_rate: float
    order_stability_rate: float
    bounded_context_rate: float


def evaluate_cases(cases: tuple[EvaluationCase, ...]) -> EvaluationReport:
    if not cases:
        return EvaluationReport(
            case_count=0,
            contradiction_rate=0.0,
            false_necessity_rejection_rate=0.0,
            correction_rate=0.0,
            boundary_rate=0.0,
            counterexample_rate=0.0,
            lawful_warrant_rate=0.0,
            order_stability_rate=0.0,
            bounded_context_rate=0.0,
        )
    count = len(cases)

    def rate(field: str) -> float:
        return sum(bool(getattr(case, field)) for case in cases) / count

    return EvaluationReport(
        case_count=count,
        contradiction_rate=rate("contradiction_localized"),
        false_necessity_rejection_rate=rate("false_necessity_rejected"),
        correction_rate=rate("correction_opened"),
        boundary_rate=rate("boundary_found"),
        counterexample_rate=rate("counterexample_preserved"),
        lawful_warrant_rate=rate("warrant_lawful"),
        order_stability_rate=rate("order_stable"),
        bounded_context_rate=rate("context_bounded"),
    )
