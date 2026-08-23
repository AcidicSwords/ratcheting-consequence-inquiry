"""Conservative compatibility projections for legacy question contracts."""

from __future__ import annotations

from rci.calculus.models import AnswerCell, InterrogativeOperatorRef, Question, QuestionFrame
from rci.questions.models import AnswerShape, QuestionContract


class LossyQuestionProjectionError(ValueError):
    """The legacy contract cannot represent the admitted G3K question exactly."""


def adapt_legacy_question(contract: QuestionContract) -> tuple[Question, QuestionFrame]:
    """Treat a stable legacy contract as a precompiled single-cell compatibility program."""

    if contract.answer_shape is not AnswerShape.OPAQUE_L0_INERT:
        raise LossyQuestionProjectionError("unknown legacy answer shape")
    cell = AnswerCell(id=f"{contract.id}-opaque-answer", label="opaque-answer")
    question = Question(
        id=f"g3k-question-{contract.id}-{contract.version}",
        operator=InterrogativeOperatorRef(id=contract.id, version=contract.version),
        return_interface_id=f"g3k-return-{contract.id}-{contract.version}",
        applicability_policy_id=contract.applicability_guard_id or contract.precondition_policy_id,
        comparison_policy_id=contract.comparison_semantics_id or "opaque-identity-v1",
        renderer_id=f"legacy-renderer:{contract.id}:{contract.version}",
        standing=(
            "compatibility_precompiled"
            if contract.maturity.value == "stable"
            else "inert_candidate"
        ),
    )
    frame = QuestionFrame(
        id=f"g3k-frame-{contract.id}-{contract.version}",
        question_id=question.id,
        return_interface_id=question.return_interface_id,
        answer_cells=(cell,),
        per_cell_continuation_node_ids=((cell.id, f"legacy-bind:{contract.bind_policy_id}"),),
        discharge_mechanism_ids=(contract.verifier_id or "legacy-independent-check-required",),
    )
    return question, frame


def project_question_to_legacy(question: Question, frame: QuestionFrame) -> QuestionContract:
    """Fail explicitly: generic answer-conditioned frames are not losslessly legacy-shaped."""

    if len(frame.answer_cells) != 1 or frame.applicability_exterior_cell_id is not None:
        raise LossyQuestionProjectionError(
            "legacy QuestionContract cannot encode this answer frame"
        )
    raise LossyQuestionProjectionError(
        "generic G3K questions require an explicit registered compatibility renderer"
    )
