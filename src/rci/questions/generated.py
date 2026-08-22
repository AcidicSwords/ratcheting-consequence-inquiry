"""Derived, data-only compilation of admitted G3Q question contracts.

The compiler creates no writable registry and grants no authority.  It joins immutable
project records already owned by the aggregate and emits a rebuildable view only when
the exact active policy, binding, scope, and safe question surface agree.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Protocol, cast

from pydantic import model_validator

from rci.claims.models import content_fingerprint
from rci.core.model import FrozenModel, Identifier, Sha256Digest
from rci.project.models import (
    AdmissionOutcome,
    ConsequentialReturn,
    GitCommitSha,
    QuestionContractCandidate,
    QuestionRepertoireDecision,
)
from rci.questions.catalog import CATALOG_V0_4
from rci.questions.models import (
    AnswerShape,
    ContractMaturity,
    QuestionContract,
    render_question,
)

if TYPE_CHECKING:
    from rci.core.state import InquiryState


class _ProjectRecord(Protocol):
    id: str


GENERATED_QUESTION_PROFILE_ID = "recursive-project-v1"
GENERATED_QUESTION_POLICY_VERSION = "recursive-question-policy-v1"
GENERATED_QUESTION_COMPILER_VERSION = "generated-question-compiler-v1"
GENERATED_QUESTION_PRECONDITION_POLICY = "owned-project-limitation-v1"
GENERATED_QUESTION_COMPARISON_POLICY = "consequence-distinction-v1"
GENERATED_QUESTION_CONSUMERS = frozenset({"frontier-builder"})


class GeneratedQuestionCompilationError(ValueError):
    """An admitted candidate cannot enter the confined executable projection."""


class CompiledReferent(FrozenModel):
    record_type: Identifier
    record_id: Identifier


class CompiledQuestionContract(FrozenModel):
    """Rebuildable executable view over one exact admitted candidate."""

    schema_version: Literal[1] = 1
    id: Identifier
    compiler_version: Literal["generated-question-compiler-v1"] = "generated-question-compiler-v1"
    profile_id: Literal["recursive-project-v1"] = "recursive-project-v1"
    candidate_id: Identifier
    candidate_fingerprint: Sha256Digest
    decision_id: Identifier
    decision_fingerprint: Sha256Digest
    limitation_id: Identifier
    anchor_id: Identifier
    anchor_commit_sha: GitCommitSha
    binding_revision: Identifier
    scope_fingerprint: Sha256Digest
    protected_horizon_id: Identifier
    comparison_policy_id: Identifier
    controller_policy_version: Literal["recursive-question-policy-v1"] = (
        "recursive-question-policy-v1"
    )
    contract: QuestionContract
    referents: tuple[CompiledReferent, ...]
    possible_returns: tuple[ConsequentialReturn, ...]
    downstream_consumer_ids: tuple[Identifier, ...]

    @model_validator(mode="after")
    def validate_compilation(self) -> CompiledQuestionContract:
        if tuple(sorted(self.referents, key=lambda item: (item.record_type, item.record_id))) != (
            self.referents
        ):
            raise ValueError("compiled referents must be canonically ordered")
        if tuple(sorted(self.possible_returns, key=lambda item: item.return_class_id)) != (
            self.possible_returns
        ):
            raise ValueError("compiled return classes must be canonically ordered")
        return self


def _project_referent_index(state: InquiryState) -> dict[str, tuple[str, ...]]:
    collections = {
        "project_anchor": state.project_anchors,
        "capability_limitation": state.capability_limitations,
        "question_contract_candidate": state.question_contract_candidates,
        "question_repertoire_decision": state.question_repertoire_decisions,
        "method_binding_candidate": state.method_binding_candidates,
        "method_admission_decision": state.method_admission_decisions,
        "capability_successor_candidate": state.capability_successor_candidates,
        "capability_frontier": state.capability_frontiers,
        "implementation_goal": state.implementation_goals,
        "candidate_environment": state.candidate_environments,
        "development_evidence": state.development_evidence,
        "independent_review": state.independent_reviews,
        "project_successor_decision": state.project_successor_decisions,
        "promotion_decision": state.promotion_decisions,
        "recursive_cycle_checkpoint": state.recursive_cycle_checkpoints,
        "recursive_stop_disposition": state.recursive_stop_dispositions,
    }
    index: dict[str, list[str]] = {}
    for record_type, records in collections.items():
        for record in records:
            record_id = cast(_ProjectRecord, record).id
            index.setdefault(record_id, []).append(record_type)
    return {record_id: tuple(sorted(record_types)) for record_id, record_types in index.items()}


def _compile_referents(
    state: InquiryState,
    candidate: QuestionContractCandidate,
) -> tuple[CompiledReferent, ...]:
    if candidate.limitation_id not in candidate.typed_referent_ids:
        raise GeneratedQuestionCompilationError(
            "generated question must explicitly reference its exact limitation"
        )
    index = _project_referent_index(state)
    compiled: list[CompiledReferent] = []
    for record_id in candidate.typed_referent_ids:
        record_types = index.get(record_id, ())
        if len(record_types) != 1:
            raise GeneratedQuestionCompilationError(
                "generated question referents must resolve to one exact owned project record"
            )
        compiled.append(CompiledReferent(record_type=record_types[0], record_id=record_id))
    return tuple(sorted(compiled, key=lambda item: (item.record_type, item.record_id)))


def _validate_safe_contract(candidate: QuestionContractCandidate) -> None:
    contract = candidate.contract
    if contract.family != "recursive-project":
        raise GeneratedQuestionCompilationError(
            "generated question is outside the recursive-project family"
        )
    if contract.maturity not in {ContractMaturity.DRAFT, ContractMaturity.EXPERIMENTAL}:
        raise GeneratedQuestionCompilationError(
            "generated question must remain draft or experimental"
        )
    if contract.input_roles != ("limitation",):
        raise GeneratedQuestionCompilationError(
            "generated question compiler v1 accepts only the exact limitation input role"
        )
    if contract.key in {item.key for item in CATALOG_V0_4.contracts}:
        raise GeneratedQuestionCompilationError(
            "generated question cannot shadow a sealed catalog contract"
        )
    if (
        contract.precondition_policy_id != GENERATED_QUESTION_PRECONDITION_POLICY
        or contract.answer_shape is not AnswerShape.OPAQUE_L0_INERT
        or contract.answer_schema_id != "rci.inert-payload.v1"
        or contract.bind_policy_id != "bind-l0-v1"
        or contract.update_rule_id != "append-provisional-claim-v1"
        or contract.reifier_id is not None
        or contract.verifier_id is not None
        or contract.recurrent_probe
        or contract.next_obligation_rule_ids
    ):
        raise GeneratedQuestionCompilationError(
            "generated question requests an unimplemented or authority-bearing contract seam"
        )
    try:
        render_question(contract, {role: role for role in contract.input_roles})
    except ValueError as exc:
        raise GeneratedQuestionCompilationError(
            "generated question template and typed input roles do not match"
        ) from exc
    if candidate.precondition_ids != ("owned-limitation",):
        raise GeneratedQuestionCompilationError(
            "generated question has an unknown precondition policy input"
        )
    if candidate.comparison_policy_id != GENERATED_QUESTION_COMPARISON_POLICY:
        raise GeneratedQuestionCompilationError("generated question comparison policy is stale")
    if not set(candidate.downstream_consumer_ids) <= GENERATED_QUESTION_CONSUMERS:
        raise GeneratedQuestionCompilationError(
            "generated question names an unimplemented downstream consumer"
        )
    return_ids = tuple(item.return_class_id for item in candidate.possible_returns)
    if len(return_ids) != len(set(return_ids)):
        raise GeneratedQuestionCompilationError("generated return-class identities must be unique")


def _active_decision(
    state: InquiryState,
    candidate_id: str,
) -> QuestionRepertoireDecision:
    decisions = tuple(
        item for item in state.question_repertoire_decisions if item.candidate_id == candidate_id
    )
    if len(decisions) != 1 or (
        decisions[0].outcome is not AdmissionOutcome.ADMIT
        or decisions[0].admitted_profile_id != GENERATED_QUESTION_PROFILE_ID
        or decisions[0].controller_policy_version != GENERATED_QUESTION_POLICY_VERSION
    ):
        raise GeneratedQuestionCompilationError(
            "generated question requires one exact active admission decision"
        )
    return decisions[0]


def compile_admitted_question(
    state: InquiryState,
    candidate_id: str,
) -> CompiledQuestionContract:
    """Compile one exact admitted candidate without mutating aggregate authority."""

    if state.context is None:
        raise GeneratedQuestionCompilationError("generated question requires a started inquiry")
    candidate = next(
        (item for item in state.question_contract_candidates if item.id == candidate_id),
        None,
    )
    if candidate is None:
        raise GeneratedQuestionCompilationError("generated question candidate is not owned")
    decision = _active_decision(state, candidate.id)
    limitation = next(
        (item for item in state.capability_limitations if item.id == candidate.limitation_id),
        None,
    )
    if limitation is None:
        raise GeneratedQuestionCompilationError("generated question limitation is not owned")
    anchor = next(
        (item for item in state.project_anchors if item.id == limitation.anchor_id),
        None,
    )
    if anchor is None or not anchor.clean:
        raise GeneratedQuestionCompilationError("generated question requires its clean anchor")
    _validate_safe_contract(candidate)
    referents = _compile_referents(state, candidate)
    returns = tuple(sorted(candidate.possible_returns, key=lambda item: item.return_class_id))
    candidate_fingerprint = content_fingerprint("rci.question-candidate.v1", candidate)
    decision_fingerprint = content_fingerprint("rci.question-decision.v1", decision)
    compilation_material = {
        "candidate_fingerprint": candidate_fingerprint,
        "decision_fingerprint": decision_fingerprint,
        "anchor_commit_sha": anchor.commit_sha,
        "binding_revision": state.context.binding_revision,
        "scope_fingerprint": state.context.scope_fingerprint,
        "protected_horizon_id": state.context.protected_horizon_id,
        "comparison_policy_id": candidate.comparison_policy_id,
        "compiler_version": GENERATED_QUESTION_COMPILER_VERSION,
    }
    compilation_fingerprint = content_fingerprint("rci.generated-question.v1", compilation_material)
    return CompiledQuestionContract(
        id=f"compiled-question-{compilation_fingerprint[:24]}",
        candidate_id=candidate.id,
        candidate_fingerprint=candidate_fingerprint,
        decision_id=decision.id,
        decision_fingerprint=decision_fingerprint,
        limitation_id=limitation.id,
        anchor_id=anchor.id,
        anchor_commit_sha=anchor.commit_sha,
        binding_revision=state.context.binding_revision,
        scope_fingerprint=state.context.scope_fingerprint,
        protected_horizon_id=state.context.protected_horizon_id,
        comparison_policy_id=candidate.comparison_policy_id,
        contract=candidate.contract,
        referents=referents,
        possible_returns=returns,
        downstream_consumer_ids=candidate.downstream_consumer_ids,
    )


def generated_question_registry(state: InquiryState) -> tuple[CompiledQuestionContract, ...]:
    """Return the deterministic confined registry projection for the active policy."""

    active_candidate_ids = sorted(
        {
            item.candidate_id
            for item in state.question_repertoire_decisions
            if item.outcome is AdmissionOutcome.ADMIT
            and item.admitted_profile_id == GENERATED_QUESTION_PROFILE_ID
            and item.controller_policy_version == GENERATED_QUESTION_POLICY_VERSION
        }
    )
    candidates: list[CompiledQuestionContract] = []
    for candidate_id in active_candidate_ids:
        try:
            candidates.append(compile_admitted_question(state, candidate_id))
        except GeneratedQuestionCompilationError:
            continue
    key_counts: dict[str, int] = {}
    for item in candidates:
        key_counts[item.contract.key] = key_counts.get(item.contract.key, 0) + 1
    return tuple(item for item in candidates if key_counts[item.contract.key] == 1)
