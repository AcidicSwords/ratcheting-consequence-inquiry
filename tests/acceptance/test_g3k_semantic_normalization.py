"""G3K-S evidence that the incumbent question surface lacks two required relations."""

from pathlib import Path
from runpy import run_path

import pytest

from rci.questions.generated import (
    GeneratedQuestionCompilationError,
    compile_admitted_question,
)

_G3Q_HELPERS = run_path(str(Path(__file__).with_name("test_regenerative_questions.py")))
_generated_downstream = _G3Q_HELPERS["_generated_downstream"]
_question_candidate = _G3Q_HELPERS["_question_candidate"]
_setup_admission = _G3Q_HELPERS["_setup_admission"]


def test_owned_generated_question_cannot_encode_answer_conditioned_continuation(
    tmp_path: Path,
) -> None:
    _, limitation, candidate = _setup_admission(tmp_path / "seed")
    conditioned = _question_candidate(
        limitation,
        candidate_id="answer-conditioned-candidate",
        contract_id="answer-conditioned-question",
    ).model_copy(
        update={
            "contract": candidate.contract.model_copy(
                update={
                    "id": "answer-conditioned-question",
                    "next_obligation_rule_ids": ("branch-by-checked-answer-v1",),
                }
            )
        }
    )
    sdk, _, conditioned = _setup_admission(tmp_path / "conditioned", question_candidate=conditioned)
    with pytest.raises(
        GeneratedQuestionCompilationError,
        match="unimplemented or authority-bearing contract seam",
    ):
        compile_admitted_question(sdk.inspect("project-inquiry"), conditioned.id)


def test_owned_partial_answer_cannot_preserve_multiple_live_answer_cells(
    tmp_path: Path,
) -> None:
    sdk, _, candidate = _setup_admission(tmp_path / "partial")
    opened = sdk.open_generated_question(
        "project-inquiry",
        candidate_id=candidate.id,
        bindings={"limitation": candidate.limitation_id},
    )
    source = opened.obligations[-1]
    sdk.step("project-inquiry")
    partial = "roadmap-required|selector-required"
    final = sdk.submit_answer("project-inquiry", partial)
    downstream = _generated_downstream(final, source.id)
    return_class = next(
        item.value for item in downstream.args if item.name == "generated_return_class_id"
    )
    assert return_class == "unclassified"
    assert downstream.carrier_id == f"unclassified-return:{candidate.id}"
    assert not hasattr(downstream, "live_answer_cell_ids")
