"""Blocking G3K-E acceptance for typed effects, arrangements, and checked succession."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from rci.calculus import (
    CalculusValidationError,
    LossyQuestionProjectionError,
    adapt_legacy_question,
    build_question_partition,
    compose_relation_extensions,
    crossing_is_involutive,
    frame_observation_proposition_id,
    interpret_node,
    project_question_to_legacy,
    question_is_productive,
    select_continuation,
    validate_arrangement_composition,
    validate_program,
)
from rci.calculus.models import (
    AnswerCell,
    ArrangementCandidate,
    ArrangementProgramAdmission,
    CompletionProfile,
    ContinuationEdge,
    CrossArrangement,
    EffectNode,
    EffectRef,
    EffectSignature,
    FrameObservation,
    FrameObservationKind,
    IdentityArrangement,
    InteractionContinuation,
    InteractionFrameObservation,
    InteractionOccurrence,
    InteractionProgram,
    PersistenceWitness,
    PrimitiveArrangement,
    ProgramActionKind,
    QuestionFrame,
    RealizedInteractionPair,
    RealizedSuccession,
    RelationExtension,
    ReturnInterface,
    SequentialArrangement,
    StopNode,
    TraceFragmentRef,
)
from rci.core import ArtifactRef, Decoded, RecordCheckerVerdict, RecordEvidence
from rci.core.errors import InvalidCommandError
from rci.questions.catalog import CATALOG_V0_4, CORE_V1
from rci.sdk import RCI
from rci.warrant import (
    CheckerVerdict,
    CheckerVerdictRecord,
    CheckReference,
    Evidence,
    EvidenceKind,
    PropositionKind,
)

NOW = datetime(2026, 8, 23, tzinfo=UTC)


def _program(*, request_input_artifact: ArtifactRef | None = None) -> InteractionProgram:
    cells = (
        AnswerCell(id="answer-yes", label="yes"),
        AnswerCell(id="answer-no", label="no"),
    )
    return_interface = ReturnInterface(id="binary-return", answer_cells=cells)
    signature = EffectSignature(
        id="ask-signature",
        input_interface_id="question-input",
        return_interface_id=return_interface.id,
        operation_id="semantic.manual_answer",
    )
    effect = EffectRef(
        id="ask-effect",
        signature_id=signature.id,
        request_input_artifact=(
            request_input_artifact
            or ArtifactRef(
                digest="0" * 64,
                size=0,
                media_type="application/octet-stream",
                encoding="binary",
            )
        ),
    )
    frame = QuestionFrame(
        id="binary-frame",
        question_id="binary-question",
        return_interface_id=return_interface.id,
        answer_cells=cells,
        per_cell_continuation_node_ids=(
            ("answer-yes", "yes-node"),
            ("answer-no", "no-node"),
        ),
        discharge_mechanism_ids=("finite-exhaustive-v1",),
    )
    return InteractionProgram(
        id="binary-question-program",
        entry_node_id="ask-node",
        nodes=(
            EffectNode(
                id="ask-node",
                effect_id=effect.id,
                return_interface_id=return_interface.id,
                frame_id=frame.id,
            ),
            StopNode(id="yes-node", outcome="stop"),
            StopNode(id="no-node", outcome="unknown"),
        ),
        continuation_edges=(
            ContinuationEdge(
                id="edge-yes",
                source_node_id="ask-node",
                answer_cell_id="answer-yes",
                target_node_id="yes-node",
            ),
            ContinuationEdge(
                id="edge-no",
                source_node_id="ask-node",
                answer_cell_id="answer-no",
                target_node_id="no-node",
            ),
        ),
        effect_signatures=(signature,),
        effects=(effect,),
        return_interfaces=(return_interface,),
        question_frames=(frame,),
    )


def _record_check(
    sdk: RCI,
    inquiry_id: str,
    proposition_id: str,
    suffix: str,
    *,
    evidence_artifact: ArtifactRef | None = None,
    checker_id: str = "finite-exhaustive-v1",
) -> CheckReference:
    state = sdk.inspect(inquiry_id)
    assert state.context is not None
    artifact = evidence_artifact or sdk.artifacts.put_bytes(
        suffix.encode(), media_type="text/plain", encoding="utf-8"
    )
    certificate = sdk.artifacts.put_bytes(
        f"certificate:{suffix}".encode(), media_type="text/plain", encoding="utf-8"
    )
    evidence = Evidence(
        id=f"evidence:{suffix}",
        kind=EvidenceKind.INDEPENDENT_WITNESS,
        proposition_id=proposition_id,
        proposition_kind=PropositionKind.RELATION,
        scope_fingerprint=state.context.scope_fingerprint,
        artifact=artifact,
    )
    verdict = CheckerVerdictRecord(
        id=f"verdict:{suffix}",
        evidence_id=evidence.id,
        evidence_artifact=artifact,
        proposition_id=proposition_id,
        proposition_kind=PropositionKind.RELATION,
        scope_fingerprint=state.context.scope_fingerprint,
        checker_id=checker_id,
        checker_version="1",
        verdict=CheckerVerdict.VALID,
        verdict_artifact=certificate,
        certificate_artifact=certificate,
    )
    sdk.dispatch(
        RecordEvidence(
            event_id=f"event:evidence:{suffix}",
            inquiry_id=inquiry_id,
            occurred_at=NOW,
            evidence=evidence,
        )
    )
    sdk.dispatch(
        RecordCheckerVerdict(
            event_id=f"event:verdict:{suffix}",
            inquiry_id=inquiry_id,
            occurred_at=NOW,
            checker_verdict=verdict,
        )
    )
    return CheckReference(evidence_id=evidence.id, checker_verdict_id=verdict.id)


def test_arrangement_composition_is_typed_and_not_realized_succession() -> None:
    first = PrimitiveArrangement(
        id="alpha", input_interface_id="i", output_interface_id="middle", binding_primitive_id="a"
    )
    second = PrimitiveArrangement(
        id="beta", input_interface_id="middle", output_interface_id="o", binding_primitive_id="b"
    )
    composed = SequentialArrangement(
        id="beta-after-alpha",
        input_interface_id="i",
        output_interface_id="o",
        first_arrangement_id=first.id,
        second_arrangement_id=second.id,
        hidden_interface_id="middle",
    )
    validate_arrangement_composition(composed, arrangements=(first, second))
    with pytest.raises(CalculusValidationError, match="hidden interface"):
        validate_arrangement_composition(
            composed.model_copy(update={"hidden_interface_id": "foreign"}),
            arrangements=(first, second),
        )

    pair = RealizedInteractionPair(
        id="realized-1",
        represented_effect_id="ask-effect",
        external_return_id="external-return-1",
        return_interface_id="binary-return",
        answer_cell_id="answer-yes",
    )
    succession = RealizedSuccession(
        id="trace-1", binding_revision="binding-v1", realized_pair_ids=(pair.id,)
    )
    assert succession.realized_pair_ids == ("realized-1",)
    assert composed.first_arrangement_id == "alpha"
    assert not hasattr(succession, "first_arrangement_id")


def test_binary_crossing_is_involutive_and_keeps_succession_order_distinct() -> None:
    swap = CrossArrangement(
        id="boolean-not",
        input_interface_id="binary",
        output_interface_id="binary",
        source_arrangement_id="predicate",
        permutation=(1, 0),
    )
    assert crossing_is_involutive(swap)
    assert tuple(swap.permutation[index] for index in swap.permutation) == (0, 1)
    left = RealizedSuccession(
        id="left", binding_revision="b", realized_pair_ids=("pair-a", "pair-b")
    )
    right = RealizedSuccession(
        id="right", binding_revision="b", realized_pair_ids=("pair-b", "pair-a")
    )
    assert left != right


def test_answer_conditioned_program_keeps_alternatives_unactualized() -> None:
    program = _program()
    validate_program(program)
    action = interpret_node(program, program.entry_node_id)
    assert action.kind is ProgramActionKind.REQUEST_EXISTING_EFFECT
    checked_yes = FrameObservation(
        id="observation-yes",
        frame_id="frame",
        kind=FrameObservationKind.COMPLETE,
        live_answer_cell_ids=("answer-yes",),
        decode_outcome_id="decode",
        check=CheckReference(evidence_id="e", checker_verdict_id="v"),
    )
    assert select_continuation(program, node_id="ask-node", observation=checked_yes) == "yes-node"
    assert interpret_node(program, "no-node").kind is ProgramActionKind.UNKNOWN
    assert {edge.target_node_id for edge in program.continuation_edges} == {
        "yes-node",
        "no-node",
    }


def test_program_cycles_require_a_fresh_effect_boundary() -> None:
    program = _program()
    guarded = program.model_copy(
        update={
            "continuation_edges": tuple(
                edge.model_copy(update={"target_node_id": "ask-node"})
                for edge in program.continuation_edges
            ),
            "question_frames": tuple(
                frame.model_copy(
                    update={
                        "per_cell_continuation_node_ids": tuple(
                            (cell_id, "ask-node")
                            for cell_id, _target in frame.per_cell_continuation_node_ids
                        )
                    }
                )
                for frame in program.question_frames
            ),
        }
    )
    validate_program(guarded)
    epsilon = program.model_copy(
        update={
            "continuation_edges": (
                *program.continuation_edges,
                ContinuationEdge(
                    id="epsilon",
                    source_node_id="yes-node",
                    answer_cell_id="answer-yes",
                    target_node_id="yes-node",
                ),
            )
        }
    )
    with pytest.raises(CalculusValidationError, match="only effect nodes"):
        validate_program(epsilon)


def test_partial_exterior_and_indeterminate_are_not_complete_answer_siblings() -> None:
    check = CheckReference(evidence_id="e", checker_verdict_id="v")
    partial = FrameObservation(
        id="partial",
        frame_id="frame",
        kind=FrameObservationKind.PARTIAL,
        live_answer_cell_ids=("answer-yes", "answer-no"),
        decode_outcome_id="decoded",
        check=check,
    )
    exterior = FrameObservation(
        id="exterior",
        frame_id="frame",
        kind=FrameObservationKind.EXTERIOR,
        decode_outcome_id="decoded-exterior",
        check=check,
    )
    indeterminate = FrameObservation(
        id="indeterminate",
        frame_id="frame",
        kind=FrameObservationKind.INDETERMINATE,
        decode_outcome_id="malformed",
    )
    assert select_continuation(_program(), node_id="ask-node", observation=partial) is None
    assert not exterior.live_answer_cell_ids
    assert not indeterminate.live_answer_cell_ids

    program = _program()
    exterior_program = program.model_copy(
        update={
            "nodes": (*program.nodes, StopNode(id="exterior-node", outcome="unknown")),
            "continuation_edges": (
                *program.continuation_edges,
                ContinuationEdge(
                    id="edge-exterior",
                    source_node_id="ask-node",
                    answer_cell_id="not-applicable",
                    target_node_id="exterior-node",
                ),
            ),
            "return_interfaces": tuple(
                item.model_copy(update={"applicability_exterior_cell_id": "not-applicable"})
                for item in program.return_interfaces
            ),
            "question_frames": tuple(
                item.model_copy(
                    update={
                        "applicability_exterior_cell_id": "not-applicable",
                        "exterior_continuation_node_id": "exterior-node",
                    }
                )
                for item in program.question_frames
            ),
        }
    )
    checked_exterior = exterior.model_copy(update={"frame_id": "binary-frame"})
    assert (
        select_continuation(
            exterior_program,
            node_id="ask-node",
            observation=checked_exterior,
        )
        == "exterior-node"
    )


def test_finite_relation_join_hides_exact_port_and_partition_is_permutation_stable() -> None:
    left = RelationExtension(
        id="left-relation",
        relation_signature_id="left-signature",
        port_ids=("source", "middle"),
        rows=(("s1", "m1"), ("s2", "m2")),
    )
    right = RelationExtension(
        id="right-relation",
        relation_signature_id="right-signature",
        port_ids=("middle", "target"),
        rows=(("m1", "t1"), ("m2", "t2")),
    )
    composition = compose_relation_extensions(
        left,
        right,
        hidden_port_id="middle",
        composition_id="joined",
        reopening_key_id="reopen-middle",
    )
    assert composition.extension.port_ids == ("source", "target")
    assert composition.extension.rows == (("s1", "t1"), ("s2", "t2"))
    assert composition.hidden_port_id == "middle"
    with pytest.raises(CalculusValidationError, match="shared hidden port"):
        compose_relation_extensions(
            left,
            right,
            hidden_port_id="foreign",
            composition_id="invalid",
            reopening_key_id="reopen",
        )

    profile = CompletionProfile(
        id="profile",
        question_frame_id="frame",
        completion_ids=("c1", "c2", "c3"),
        cell_by_completion=(("c3", "no"), ("c1", "yes"), ("c2", "yes")),
    )
    permuted = profile.model_copy(
        update={"cell_by_completion": tuple(reversed(profile.cell_by_completion))}
    )
    assert build_question_partition(profile) == build_question_partition(permuted)
    assert question_is_productive(build_question_partition(profile))
    single = CompletionProfile(
        id="single",
        question_frame_id="frame",
        completion_ids=("c1", "c2"),
        cell_by_completion=(("c1", "same"), ("c2", "same")),
    )
    assert not question_is_productive(build_question_partition(single))
    assert single.closed_registry_check is None


def test_all_core_v1_questions_are_losslessly_readable_as_precompiled_frames() -> None:
    contracts = {item.key: item for item in CATALOG_V0_4.contracts}
    compiled = [adapt_legacy_question(contracts[key]) for key in CORE_V1.contract_keys]
    assert len(compiled) == 8
    assert [pair[0].operator.id for pair in compiled] == [
        contracts[key].id for key in CORE_V1.contract_keys
    ]
    assert all(len(frame.answer_cells) == 1 for _, frame in compiled)
    multi = QuestionFrame(
        id="multi",
        question_id=compiled[0][0].id,
        return_interface_id="binary",
        answer_cells=(AnswerCell(id="a", label="a"), AnswerCell(id="b", label="b")),
        per_cell_continuation_node_ids=(("a", "left"), ("b", "right")),
        discharge_mechanism_ids=("checker",),
    )
    with pytest.raises(LossyQuestionProjectionError):
        project_question_to_legacy(compiled[0][0], multi)


def test_piecewise_recognition_is_candidate_only_and_failure_creates_residue() -> None:
    fragment = TraceFragmentRef(
        id="fragment-1", source_inquiry_id="inquiry", realized_pair_ids=("pair-1",)
    )
    arrangement = IdentityArrangement(
        id="recognized-id", input_interface_id="i", output_interface_id="i"
    )
    candidate = ArrangementCandidate(
        id="candidate", arrangement=arrangement, fragment_ids=(fragment.id,)
    )
    assert candidate.status == "inert_candidate"
    broken = PersistenceWitness(
        id="broken",
        predecessor_arrangement_id=arrangement.id,
        successor_arrangement_id="successor",
        succession_fragment_id="later-fragment",
        protected_horizon_id="horizon",
        commutes=False,
        check=CheckReference(evidence_id="e", checker_verdict_id="v"),
        residue_id="reopen-recognized-id",
    )
    assert broken.residue_id is not None


def test_program_lifecycle_is_owned_checked_replayable_and_cannot_self_admit(
    tmp_path: Path,
) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)
    sdk.start("inquiry")
    step = sdk.step("inquiry")
    assert step.request_id is not None
    requested = next(
        item
        for item in sdk.inspect("inquiry").effect_requests
        if item.request.id == step.request_id
    )
    program = _program(request_input_artifact=requested.request.input_artifact)
    sdk.record_arrangement_program_candidate("inquiry", program)
    forged = ArrangementProgramAdmission(
        id="admission",
        program_id=program.id,
        outcome="admit",
        policy_version="g3k-program-policy-v1",
        check=CheckReference(evidence_id="missing", checker_verdict_id="missing"),
    )
    with pytest.raises(InvalidCommandError, match="does not resolve"):
        sdk.decide_arrangement_program_admission("inquiry", forged)
    check = _record_check(
        sdk,
        "inquiry",
        f"admit-arrangement-program:{program.id}",
        "program-admission",
    )
    sdk.decide_arrangement_program_admission("inquiry", forged.model_copy(update={"check": check}))

    wrong_input_artifact = sdk.artifacts.put_bytes(
        b"foreign-input",
        media_type="application/octet-stream",
        encoding="binary",
    )
    wrong_input_program = program.model_copy(
        update={
            "id": "wrong-input-program",
            "effects": tuple(
                item.model_copy(update={"request_input_artifact": wrong_input_artifact})
                for item in program.effects
            ),
        }
    )
    sdk.record_arrangement_program_candidate("inquiry", wrong_input_program)
    wrong_input_check = _record_check(
        sdk,
        "inquiry",
        f"admit-arrangement-program:{wrong_input_program.id}",
        "wrong-input-program-admission",
    )
    sdk.decide_arrangement_program_admission(
        "inquiry",
        ArrangementProgramAdmission(
            id="wrong-input-admission",
            program_id=wrong_input_program.id,
            outcome="admit",
            check=wrong_input_check,
        ),
    )
    state = sdk.inspect("inquiry")
    with pytest.raises(InvalidCommandError, match="exact represented operation and input"):
        sdk.open_interaction_occurrence(
            "inquiry",
            InteractionOccurrence(
                id="wrong-input-occurrence",
                execution_id="wrong-input-execution",
                program_id=wrong_input_program.id,
                node_id="ask-node",
                effect_id="ask-effect",
                effect_request_id=step.request_id,
                source_sequence=state.sequence,
            ),
        )

    skipped_node_program = program.model_copy(
        update={
            "id": "skipped-node-program",
            "nodes": (
                *program.nodes,
                EffectNode(
                    id="second-ask-node",
                    effect_id="ask-effect",
                    return_interface_id="binary-return",
                    frame_id="binary-frame",
                ),
            ),
            "continuation_edges": (
                *program.continuation_edges,
                ContinuationEdge(
                    id="second-edge-yes",
                    source_node_id="second-ask-node",
                    answer_cell_id="answer-yes",
                    target_node_id="yes-node",
                ),
                ContinuationEdge(
                    id="second-edge-no",
                    source_node_id="second-ask-node",
                    answer_cell_id="answer-no",
                    target_node_id="no-node",
                ),
            ),
        }
    )
    sdk.record_arrangement_program_candidate("inquiry", skipped_node_program)
    skipped_node_check = _record_check(
        sdk,
        "inquiry",
        f"admit-arrangement-program:{skipped_node_program.id}",
        "skipped-node-program-admission",
    )
    sdk.decide_arrangement_program_admission(
        "inquiry",
        ArrangementProgramAdmission(
            id="skipped-node-admission",
            program_id=skipped_node_program.id,
            outcome="admit",
            check=skipped_node_check,
        ),
    )
    state = sdk.inspect("inquiry")
    with pytest.raises(InvalidCommandError, match="program entry node"):
        sdk.open_interaction_occurrence(
            "inquiry",
            InteractionOccurrence(
                id="skipped-node-occurrence",
                execution_id="skipped-node-execution",
                program_id=skipped_node_program.id,
                node_id="second-ask-node",
                effect_id="ask-effect",
                effect_request_id=step.request_id,
                source_sequence=state.sequence,
            ),
        )

    prefix = sdk.inspect("inquiry")
    occurrence = InteractionOccurrence(
        id="occurrence",
        execution_id="execution",
        program_id=program.id,
        node_id="ask-node",
        effect_id="ask-effect",
        effect_request_id=step.request_id,
        source_sequence=prefix.sequence,
    )
    sdk.open_interaction_occurrence("inquiry", occurrence)
    predicted_semantic_artifact = sdk.artifacts.put_bytes(
        b"yes", media_type="text/plain", encoding="utf-8"
    )
    premature_check = _record_check(
        sdk,
        "inquiry",
        "observe-frame:premature-frame",
        "premature-frame",
        evidence_artifact=predicted_semantic_artifact,
    )
    final = sdk.submit_answer("inquiry", "yes")
    request = next(item for item in final.effect_requests if item.request.id == step.request_id)
    assert request.accepted_decoded_outcome_id is not None
    accepted = next(
        item for item in request.decode_outcomes if item.id == request.accepted_decoded_outcome_id
    )
    assert isinstance(accepted, Decoded)
    premature = InteractionFrameObservation(
        id="premature-owned-frame",
        occurrence_id=occurrence.id,
        observation=FrameObservation(
            id="premature-frame",
            frame_id="binary-frame",
            kind=FrameObservationKind.COMPLETE,
            live_answer_cell_ids=("answer-yes",),
            decode_outcome_id=request.accepted_decoded_outcome_id,
            check=premature_check,
        ),
    )
    with pytest.raises(InvalidCommandError, match=r"does not match|must follow"):
        sdk.record_interaction_frame_observation("inquiry", premature)
    wrong_frame = InteractionFrameObservation(
        id="wrong-owned-frame",
        occurrence_id=occurrence.id,
        observation=FrameObservation(
            id="wrong-frame-observation",
            frame_id="caller-authored-frame",
            kind=FrameObservationKind.COMPLETE,
            live_answer_cell_ids=("answer-yes",),
            decode_outcome_id=request.accepted_decoded_outcome_id,
            check=CheckReference(evidence_id="wrong-frame", checker_verdict_id="wrong-frame"),
        ),
    )
    with pytest.raises(InvalidCommandError, match="exact owned frame"):
        sdk.record_interaction_frame_observation("inquiry", wrong_frame)
    unauthorized_draft = FrameObservation(
        id="wrong-checker-frame",
        frame_id="binary-frame",
        kind=FrameObservationKind.COMPLETE,
        live_answer_cell_ids=("answer-yes",),
        decode_outcome_id=request.accepted_decoded_outcome_id,
        check=CheckReference(evidence_id="pending", checker_verdict_id="pending"),
    )
    wrong_checker = _record_check(
        sdk,
        "inquiry",
        frame_observation_proposition_id(unauthorized_draft),
        "wrong-checker-frame",
        evidence_artifact=accepted.result.semantic_artifact,
        checker_id="manual-v1",
    )
    unauthorized_discharge = InteractionFrameObservation(
        id="unauthorized-discharge-frame",
        occurrence_id=occurrence.id,
        observation=unauthorized_draft.model_copy(update={"check": wrong_checker}),
    )
    with pytest.raises(InvalidCommandError, match="not authorized by the exact owned frame"):
        sdk.record_interaction_frame_observation("inquiry", unauthorized_discharge)
    observation_draft = FrameObservation(
        id="frame-yes",
        frame_id="binary-frame",
        kind=FrameObservationKind.COMPLETE,
        live_answer_cell_ids=("answer-yes",),
        decode_outcome_id=request.accepted_decoded_outcome_id,
        check=CheckReference(evidence_id="pending", checker_verdict_id="pending"),
    )
    frame_check = _record_check(
        sdk,
        "inquiry",
        frame_observation_proposition_id(observation_draft),
        "frame-yes",
        evidence_artifact=accepted.result.semantic_artifact,
    )
    classification_substitution = InteractionFrameObservation(
        id="substituted-frame-classification",
        occurrence_id=occurrence.id,
        observation=observation_draft.model_copy(
            update={
                "live_answer_cell_ids": ("answer-no",),
                "check": frame_check,
            }
        ),
    )
    with pytest.raises(InvalidCommandError, match="proposition does not match"):
        sdk.record_interaction_frame_observation("inquiry", classification_substitution)
    observation = InteractionFrameObservation(
        id="owned-frame-yes",
        occurrence_id=occurrence.id,
        observation=observation_draft.model_copy(update={"check": frame_check}),
    )
    sdk.record_interaction_frame_observation("inquiry", observation)
    continuation = InteractionContinuation(
        id="selected-yes",
        occurrence_id=occurrence.id,
        observation_id=observation.id,
        selected_answer_cell_id="answer-yes",
        successor_node_id="yes-node",
    )
    sdk.select_interaction_continuation("inquiry", continuation)
    replayed = sdk.replay("inquiry")
    assert replayed.interaction_continuations == (continuation,)
    assert sdk.export("inquiry") == sdk.export("inquiry")
