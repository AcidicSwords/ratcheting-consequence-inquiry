"""Pure confined compilation from an admitted project return to an inert Goal candidate."""

from __future__ import annotations

from hashlib import sha256
from typing import TYPE_CHECKING, Literal

from rci.claims.models import (
    ClaimStatus,
    Obligation,
    RepresentationLevel,
    content_fingerprint,
)
from rci.core.effects import Decoded, SuccessResult
from rci.core.model import FrozenModel, Identifier
from rci.project.models import ImplementationGoalCandidate, ImplementationGoalContract
from rci.questions.generated import compile_admitted_question

if TYPE_CHECKING:
    from rci.core.state import InquiryState


GOAL_COMPILER_VERSION = "implementation-goal-compiler-v1"
GOAL_ADMISSION_POLICY_VERSION = "goal-admission-policy-v1"
GOAL_ACCEPTANCE_REGISTRY_VERSION = "project-gate-registry-v1"
GOAL_MUTATION_REGISTRY_VERSION = "project-mutation-registry-v1"

PREDECESSOR_GATE_COMMANDS = (
    "uv lock --check",
    "uv sync --dev",
    'uv run python -c "import rci"',
    'uv run pytest -q -m "not optional"',
    "uv sync --all-extras --dev",
    "uv run ruff format --check .",
    "uv run ruff check .",
    "uv run mypy src/rci tests",
    "uv run pytest -q",
    "uv run pytest -q tests/acceptance",
    "uv run pytest -q tests/acceptance/test_g2a_retrieval_recovery.py",
    "uv run pytest -q tests/acceptance/test_g2b_consolidation_plasticity.py",
    "uv run pytest -q tests/acceptance/test_g3a_history_state.py",
    "uv run pytest -q tests/acceptance/test_recursive_project_inquiry.py",
    "uv run pytest -q tests/acceptance/test_regenerative_questions.py",
    "uv run rci --help",
    "uv build",
)
GOAL_SYNTHESIS_COMMAND = "uv run pytest -q tests/acceptance/test_goal_synthesis.py"
PROPOSED_GATE_COMMANDS = (*PREDECESSOR_GATE_COMMANDS, GOAL_SYNTHESIS_COMMAND)

ALLOWED_MUTATION_ROOTS = (
    "src/rci/cli",
    "src/rci/core",
    "src/rci/project",
    "src/rci/sdk.py",
    "tests",
)
FORBIDDEN_AUTHORITY_ROOTS = (
    ".git",
    ".github",
    ".rci/config.toml",
    "AGENTS.md",
    "PLAN.md",
    "RCI_Project_Spec.tex",
    "docs/adr",
    "docs/goals",
    "docs/requirements-matrix.md",
)
GOAL_ASSUMPTIONS = (
    "existing-effect-protocol-sufficient",
    "generated-return-is-provisional",
    "manual-goal-bypass-remains-external",
    "registry-confined-goal-shape-sufficient",
)


class GoalSynthesisUnknown(FrozenModel):
    """Derived fail-closed result; it is never appended as authority."""

    kind: Literal["unknown"] = "unknown"
    reason: Identifier


class GoalSynthesisError(ValueError):
    """The requested exact source chain is not a lawful compiler input."""


def _argument(obligation: Obligation, name: str) -> str | None:
    values = tuple(item.value for item in obligation.args if item.name == name)
    if len(values) != 1 or not isinstance(values[0], str):
        return None
    return values[0]


def _fingerprint(namespace: str, value: object) -> str:
    return content_fingerprint(namespace, value)


def _gate_digest(commands: tuple[str, ...]) -> str:
    return _fingerprint("rci.project-gate.v1", commands)


def goal_admission_evidence_ids(candidate: ImplementationGoalCandidate) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                candidate.question_candidate_id,
                candidate.question_decision_id,
                candidate.source_obligation_id,
                candidate.accepted_decode_id,
                candidate.source_claim_id,
                candidate.downstream_obligation_id,
                candidate.anchor_id,
                candidate.limitation_id,
                candidate.frontier_id,
                candidate.selected_candidate_id,
            }
        )
    )


def compile_implementation_goal_candidate(
    state: InquiryState,
    *,
    source_obligation_id: str,
    downstream_obligation_id: str,
    frontier_id: str,
) -> ImplementationGoalCandidate | GoalSynthesisUnknown:
    """Compile one exact source chain or return a typed, inert Unknown result."""

    if state.context is None:
        return GoalSynthesisUnknown(reason="inquiry-not-started")
    source = state.obligation_by_id(source_obligation_id)
    downstream = state.obligation_by_id(downstream_obligation_id)
    frontier = next((item for item in state.capability_frontiers if item.id == frontier_id), None)
    if source is None or downstream is None or frontier is None:
        return GoalSynthesisUnknown(reason="source-record-not-owned")
    if downstream.parent_obligation_ids != (source.id,):
        return GoalSynthesisUnknown(reason="downstream-parent-mismatch")
    return_class = _argument(downstream, "generated_return_class_id")
    if return_class != "goal-derivation-required":
        return GoalSynthesisUnknown(reason="return-class-not-goal-derivation")
    question_candidate_id = _argument(source, "__rci_generated_question_candidate_id")
    if (
        question_candidate_id is None
        or _argument(downstream, "source_question_candidate_id") != question_candidate_id
    ):
        return GoalSynthesisUnknown(reason="question-source-mismatch")
    try:
        compiled = compile_admitted_question(state, question_candidate_id)
    except ValueError:
        return GoalSynthesisUnknown(reason="question-compilation-not-active")
    if (
        _argument(source, "__rci_generated_question_decision_id") != compiled.decision_id
        or _argument(source, "__rci_generated_question_compilation_id") != compiled.id
        or source.carrier_id != compiled.limitation_id
        or source.binding_revision != compiled.binding_revision
        or source.scope.fingerprint != compiled.scope_fingerprint
        or downstream.binding_revision != compiled.binding_revision
        or downstream.scope.fingerprint != compiled.scope_fingerprint
    ):
        return GoalSynthesisUnknown(reason="question-context-mismatch")
    matching_return = tuple(
        item
        for item in compiled.possible_returns
        if item.return_class_id == return_class
        and item.downstream_state_id == downstream.carrier_id
    )
    if len(matching_return) != 1:
        return GoalSynthesisUnknown(reason="return-mapping-ambiguous")

    plans = {item.id: item for item in state.step_plans}
    requests = tuple(
        item
        for item in state.effect_requests
        if (plan := plans.get(item.request.step_plan_id)) is not None
        and plan.selected_obligation_id == source.id
        and item.accepted_decoded_outcome_id is not None
    )
    if len(requests) != 1:
        return GoalSynthesisUnknown(reason="accepted-return-not-unique")
    request_state = requests[0]
    decoded = next(
        (
            item
            for item in request_state.decode_outcomes
            if item.id == request_state.accepted_decoded_outcome_id
        ),
        None,
    )
    if not isinstance(decoded, Decoded) or not isinstance(decoded.result, SuccessResult):
        return GoalSynthesisUnknown(reason="accepted-return-not-success")

    source_claim_id = _argument(downstream, "source_claim_id")
    claims = tuple(item for item in state.claims if item.id == source_claim_id)
    if len(claims) != 1:
        return GoalSynthesisUnknown(reason="source-claim-not-unique")
    claim = claims[0]
    if (
        claim.status is not ClaimStatus.PROVISIONAL
        or claim.representation_level is not RepresentationLevel.L0_OPAQUE
        or claim.provenance.source_id != decoded.external_return_id
        or sha256(claim.model_dump_json().encode()).hexdigest()
        != decoded.result.semantic_artifact.digest
    ):
        return GoalSynthesisUnknown(reason="source-claim-decode-mismatch")

    limitation = next(
        (item for item in state.capability_limitations if item.id == compiled.limitation_id), None
    )
    anchor = (
        None
        if limitation is None
        else next((item for item in state.project_anchors if item.id == limitation.anchor_id), None)
    )
    selected = (
        None
        if frontier.selected_discriminator_candidate_id is None
        else next(
            (
                item
                for item in state.capability_successor_candidates
                if item.id == frontier.selected_discriminator_candidate_id
            ),
            None,
        )
    )
    if (
        limitation is None
        or anchor is None
        or selected is None
        or frontier.status != "ready"
        or frontier.anchor_id != anchor.id
        or frontier.limitation_id != limitation.id
        or selected.anchor_id != anchor.id
        or selected.limitation_id != limitation.id
        or selected.discriminator_id != "goal-synthesis-acceptance"
        or anchor.gate_digest != _gate_digest(PREDECESSOR_GATE_COMMANDS)
    ):
        return GoalSynthesisUnknown(reason="frontier-profile-not-applicable")

    goal_material = {
        "compiled_question_id": compiled.id,
        "accepted_decode_id": decoded.id,
        "source_claim_id": claim.id,
        "downstream_obligation_id": downstream.id,
        "anchor_id": anchor.id,
        "limitation_id": limitation.id,
        "frontier_id": frontier.id,
        "selected_candidate_id": selected.id,
        "compiler_version": GOAL_COMPILER_VERSION,
        "acceptance_registry_version": GOAL_ACCEPTANCE_REGISTRY_VERSION,
        "mutation_registry_version": GOAL_MUTATION_REGISTRY_VERSION,
    }
    goal_material_fingerprint = _fingerprint("rci.implementation-goal-material.v1", goal_material)
    goal = ImplementationGoalContract(
        id=f"goal:{goal_material_fingerprint}",
        cycle_id=f"cycle:{goal_material_fingerprint}",
        anchor_id=anchor.id,
        frontier_id=frontier.id,
        candidate_id=selected.id,
        current=selected.current_state,
        desired=selected.desired_state,
        separator=limitation.consequential_boundary,
        expected_incumbent_return="No replayable implementation-Goal candidate is derivable.",
        expected_candidate_return=(
            "One exact admitted return compiles to an inert, controller-admissible Goal candidate."
        ),
        preserve_capability_ids=selected.preserved_capability_ids,
        acceptance_commands=tuple(sorted(PROPOSED_GATE_COMMANDS)),
        allowed_mutation_roots=tuple(sorted(ALLOWED_MUTATION_ROOTS)),
        forbidden_authority_roots=tuple(sorted(FORBIDDEN_AUTHORITY_ROOTS)),
        assumption_ids=tuple(sorted(GOAL_ASSUMPTIONS)),
        incumbent_gate_digest=_gate_digest(PREDECESSOR_GATE_COMMANDS),
        proposed_gate_digest=_gate_digest(PROPOSED_GATE_COMMANDS),
        rollback_condition="Any protected predecessor command fails or authority expands.",
        reopening_condition=(
            "A lawful return requires a Goal shape, check, or mutation root outside the registries."
        ),
    )
    candidate_material = {
        **goal_material,
        "goal_fingerprint": _fingerprint("rci.implementation-goal.v1", goal),
        "binding_revision": state.context.binding_revision,
        "scope_fingerprint": state.context.scope_fingerprint,
        "protected_horizon_id": state.context.protected_horizon_id,
    }
    candidate_fingerprint = _fingerprint("rci.implementation-goal-candidate.v1", candidate_material)
    question_candidate = next(
        item for item in state.question_contract_candidates if item.id == compiled.candidate_id
    )
    question_decision = next(
        item for item in state.question_repertoire_decisions if item.id == compiled.decision_id
    )
    return ImplementationGoalCandidate(
        id=f"goal-candidate:{candidate_fingerprint}",
        question_candidate_id=question_candidate.id,
        question_candidate_fingerprint=_fingerprint(
            "rci.question-candidate.v1", question_candidate
        ),
        question_decision_id=question_decision.id,
        question_decision_fingerprint=_fingerprint("rci.question-decision.v1", question_decision),
        compiled_question_id=compiled.id,
        compiled_question_fingerprint=_fingerprint("rci.compiled-question.v1", compiled),
        source_obligation_id=source.id,
        source_obligation_fingerprint=source.fingerprint,
        effect_request_id=request_state.request.id,
        accepted_decode_id=decoded.id,
        accepted_decode_fingerprint=_fingerprint("rci.decode-outcome.v1", decoded),
        source_claim_id=claim.id,
        source_claim_fingerprint=_fingerprint("rci.claim.v1", claim),
        downstream_obligation_id=downstream.id,
        downstream_obligation_fingerprint=downstream.fingerprint,
        matched_return_class_id="goal-derivation-required",
        anchor_id=anchor.id,
        anchor_fingerprint=_fingerprint("rci.project-anchor.v1", anchor),
        limitation_id=limitation.id,
        limitation_fingerprint=_fingerprint("rci.capability-limitation.v1", limitation),
        frontier_id=frontier.id,
        frontier_fingerprint=_fingerprint("rci.capability-frontier.v1", frontier),
        selected_candidate_id=selected.id,
        selected_candidate_fingerprint=_fingerprint("rci.capability-successor.v1", selected),
        binding_revision=state.context.binding_revision,
        scope_fingerprint=state.context.scope_fingerprint,
        protected_horizon_id=state.context.protected_horizon_id,
        goal=goal,
        goal_fingerprint=_fingerprint("rci.implementation-goal.v1", goal),
    )


__all__ = [
    "GOAL_ACCEPTANCE_REGISTRY_VERSION",
    "GOAL_ADMISSION_POLICY_VERSION",
    "GOAL_COMPILER_VERSION",
    "GOAL_MUTATION_REGISTRY_VERSION",
    "GOAL_SYNTHESIS_COMMAND",
    "PREDECESSOR_GATE_COMMANDS",
    "PROPOSED_GATE_COMMANDS",
    "GoalSynthesisError",
    "GoalSynthesisUnknown",
    "compile_implementation_goal_candidate",
    "goal_admission_evidence_ids",
]
