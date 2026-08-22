from rci.evaluation import evaluate_cases


def test_empty_evaluation_is_deterministic() -> None:
    assert evaluate_cases(()).model_dump() == {
        "case_count": 0,
        "contradiction_rate": 0.0,
        "false_necessity_rejection_rate": 0.0,
        "correction_rate": 0.0,
        "boundary_rate": 0.0,
        "counterexample_rate": 0.0,
        "lawful_warrant_rate": 0.0,
        "order_stability_rate": 0.0,
        "bounded_context_rate": 0.0,
    }
