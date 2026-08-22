"""Blocking G3G acceptance for confined implementation-Goal synthesis."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from rci.claims import ClaimRole
from rci.claims.models import content_fingerprint
from rci.cli import app
from rci.core.errors import IdentityConflictError, InvalidCommandError
from rci.project import (
    PREDECESSOR_GATE_COMMANDS,
    AdmissionOutcome,
    CandidateEnvironmentManifest,
    CapabilityLimitation,
    CapabilitySuccessorCandidate,
    ConsequentialReturn,
    DevelopmentEvidence,
    EvidenceKind,
    EvidenceOutcome,
    GoalAdmissionDecision,
    GoalSynthesisUnknown,
    ImplementationGoalCandidate,
    ImplementationGoalContract,
    IndependentReview,
    LimitationKind,
    ProjectAnchor,
    ProjectCost,
    ProjectGainKind,
    QuestionContractCandidate,
    QuestionRepertoireDecision,
    ReviewOutcome,
    SuccessorKind,
    derive_capability_frontier,
    goal_admission_evidence_ids,
)
from rci.questions import ContractMaturity, QuestionContract
from rci.sdk import RCI

BASE = "a" * 40
HEAD = "b" * 40
DIGEST = "c" * 64


def _gate_digest(commands: tuple[str, ...]) -> str:
    return content_fingerprint("rci.project-gate.v1", commands)


def _question_candidate(limitation: CapabilityLimitation) -> QuestionContractCandidate:
    return QuestionContractCandidate(
        id="question-candidate-goal-synthesis",
        limitation_id=limitation.id,
        contract=QuestionContract(
            id="project-next-capability",
            version="0.1.0",
            family="recursive-project",
            input_roles=("limitation",),
            output_claim_role=ClaimRole.CHARACTERIZATION,
            precondition_policy_id="owned-project-limitation-v1",
            render_template="Which successor does {limitation} require?",
            maturity=ContractMaturity.EXPERIMENTAL,
        ),
        typed_referent_ids=(limitation.id,),
        precondition_ids=("owned-limitation",),
        possible_returns=(
            ConsequentialReturn(
                return_class_id="goal-derivation-required",
                downstream_state_id="compile-confined-goal",
                downstream_obligation_kind=LimitationKind.IMPLEMENTATION,
            ),
            ConsequentialReturn(
                return_class_id="method-transport-required",
                downstream_state_id="bind-native-method",
                downstream_obligation_kind=LimitationKind.METHOD,
            ),
        ),
        comparison_policy_id="consequence-distinction-v1",
        downstream_consumer_ids=("frontier-builder",),
        falsifying_attack_ids=("same-successor-under-both-returns",),
    )


def _setup(root: Path, *, answer: str = "goal-derivation-required") -> tuple[RCI, str, str, str]:
    sdk = RCI(root)
    sdk.start("project-inquiry")
    anchor = ProjectAnchor(
        id="anchor-g3g",
        repository="AcidicSwords/ratcheting-consequence-inquiry",
        protected_branch="main",
        commit_sha=BASE,
        tree_digest=DIGEST,
        authority_digest="1" * 64,
        gate_digest=_gate_digest(PREDECESSOR_GATE_COMMANDS),
        clean=True,
    )
    sdk.record_project_anchor("project-inquiry", anchor)
    limitation = CapabilityLimitation(
        id="limitation-goal-synthesis",
        anchor_id=anchor.id,
        kind=LimitationKind.IMPLEMENTATION,
        current_capability="Route an admitted project return to an ordinary obligation.",
        missing_capability="Compile that exact return into an inert confined Goal candidate.",
        consequential_boundary=(
            "One return requires replayable Goal derivation while the alternate "
            "requires method transport."
        ),
        protected_consequence_ids=("manual-goal-bypass", "predecessor-gate", "runtime-no-exec"),
        observed_evidence=(sdk.artifacts.put_bytes(b"return-to-Goal join is manual"),),
        existing_question_contract_keys=("project-next-capability/0.1.0",),
    )
    sdk.record_capability_limitation("project-inquiry", limitation)

    predecessor = CapabilitySuccessorCandidate(
        id="successor-g3q-evidence",
        anchor_id=anchor.id,
        limitation_id=limitation.id,
        kind=SuccessorKind.QUESTION_REPERTOIRE,
        current_state="Question candidates are inert.",
        desired_state="One admitted question schedules lawfully.",
        preserved_capability_ids=("g1", "g2a", "g2b", "g3ah", "g3r"),
        gain_kinds=(ProjectGainKind.NEW_SEPARATOR,),
        discriminator_id="regenerative-question-acceptance",
        evidence_mechanism_ids=("acceptance",),
        estimated_costs=(ProjectCost(axis="implementation_steps", value=1),),
        reversible=True,
    )
    sdk.record_capability_successor_candidate("project-inquiry", predecessor)
    predecessor_frontier = derive_capability_frontier(
        frontier_id="frontier-g3q-evidence", candidates=(predecessor,)
    )
    sdk.record_capability_frontier("project-inquiry", predecessor_frontier)
    predecessor_goal = ImplementationGoalContract(
        id="goal-g3q-evidence",
        cycle_id="cycle-g3q-evidence",
        anchor_id=anchor.id,
        frontier_id=predecessor_frontier.id,
        candidate_id=predecessor.id,
        current=predecessor.current_state,
        desired=predecessor.desired_state,
        separator="The admitted question becomes schedulable.",
        expected_incumbent_return="No compiled question exists.",
        expected_candidate_return="One compiled question exists.",
        preserve_capability_ids=predecessor.preserved_capability_ids,
        acceptance_commands=("uv run pytest -q tests/acceptance/test_regenerative_questions.py",),
        allowed_mutation_roots=("src/rci/questions", "tests"),
        forbidden_authority_roots=("AGENTS.md", "PLAN.md"),
        assumption_ids=("existing-effect-protocol-sufficient",),
        incumbent_gate_digest=anchor.gate_digest,
        proposed_gate_digest="2" * 64,
        rollback_condition="A predecessor check fails.",
        reopening_condition="The confined question grammar is insufficient.",
    )
    sdk.seal_implementation_goal("project-inquiry", predecessor_goal)
    environment = CandidateEnvironmentManifest(
        id="environment-g3q-evidence",
        goal_id=predecessor_goal.id,
        developer_id="g3q-developer",
        base_commit_sha=BASE,
        candidate_branch="codex/g3q",
        worktree_path=".rci/workspaces/g3q",
        initial_tree_digest=DIGEST,
        toolchain_artifact=sdk.artifacts.put_bytes(b"python=3.12"),
        toolchain_digest="3" * 64,
    )
    sdk.record_candidate_environment("project-inquiry", environment)
    evidence = DevelopmentEvidence(
        id="evidence-g3q",
        goal_id=predecessor_goal.id,
        candidate_environment_id=environment.id,
        kind=EvidenceKind.TEST,
        command_or_method=predecessor_goal.acceptance_commands[0],
        outcome=EvidenceOutcome.PASS,
        observed_return=sdk.artifacts.put_bytes(b"7 passed"),
        base_commit_sha=BASE,
        candidate_commit_sha=HEAD,
        gate_digest=predecessor_goal.proposed_gate_digest,
    )
    sdk.record_development_evidence("project-inquiry", evidence)
    sdk.record_independent_review(
        "project-inquiry",
        IndependentReview(
            id="review-g3q",
            goal_id=predecessor_goal.id,
            candidate_environment_id=environment.id,
            reviewer_id="independent-reviewer",
            reviewer_context_digest="4" * 64,
            reviewed_commit_sha=HEAD,
            evidence_ids=(evidence.id,),
            outcome=ReviewOutcome.VALID,
            findings_artifact=sdk.artifacts.put_bytes(b"valid"),
        ),
    )
    question = _question_candidate(limitation)
    sdk.record_question_contract_candidate("project-inquiry", question)
    sdk.decide_question_repertoire(
        "project-inquiry",
        QuestionRepertoireDecision(
            id="decision-question-g3g",
            candidate_id=question.id,
            outcome=AdmissionOutcome.ADMIT,
            controller_policy_version="recursive-question-policy-v1",
            evidence_ids=(evidence.id,),
            admitted_profile_id="recursive-project-v1",
        ),
    )

    successor = CapabilitySuccessorCandidate(
        id="successor-g3g",
        anchor_id=anchor.id,
        limitation_id=limitation.id,
        kind=SuccessorKind.GOAL_DECOMPOSITION,
        current_state=limitation.current_capability,
        desired_state=limitation.missing_capability,
        preserved_capability_ids=("g1", "g2a", "g2b", "g3ah", "g3q", "g3r"),
        gain_kinds=(ProjectGainKind.EXECUTABLE_RELATION,),
        discriminator_id="goal-synthesis-acceptance",
        evidence_mechanism_ids=("acceptance", "hosted-ci", "independent-review"),
        estimated_costs=(ProjectCost(axis="missing_executable_seams", value=1),),
        reversible=True,
    )
    sdk.record_capability_successor_candidate("project-inquiry", successor)
    frontier = derive_capability_frontier(frontier_id="frontier-g3g", candidates=(successor,))
    sdk.record_capability_frontier("project-inquiry", frontier)

    opened = sdk.open_generated_question(
        "project-inquiry", candidate_id=question.id, bindings={"limitation": limitation.id}
    )
    source = opened.obligations[-1]
    sdk.step("project-inquiry")
    final = sdk.submit_answer("project-inquiry", answer)
    downstream = next(
        item for item in final.obligations if item.parent_obligation_ids == (source.id,)
    )
    return sdk, source.id, downstream.id, frontier.id


def test_exact_return_compiles_admits_and_seals_without_authority_collapse(
    tmp_path: Path,
) -> None:
    sdk, source_id, downstream_id, frontier_id = _setup(tmp_path)
    derived = sdk.derive_implementation_goal_candidate(
        "project-inquiry",
        source_obligation_id=source_id,
        downstream_obligation_id=downstream_id,
        frontier_id=frontier_id,
    )
    assert isinstance(derived, ImplementationGoalCandidate)
    assert derived == sdk.derive_implementation_goal_candidate(
        "project-inquiry",
        source_obligation_id=source_id,
        downstream_obligation_id=downstream_id,
        frontier_id=frontier_id,
    )
    assert derived.goal.incumbent_gate_digest == _gate_digest(PREDECESSOR_GATE_COMMANDS)
    assert set(PREDECESSOR_GATE_COMMANDS) < set(derived.goal.acceptance_commands)
    assert derived.goal.allowed_mutation_roots == tuple(sorted(derived.goal.allowed_mutation_roots))
    assert all("return" not in root for root in derived.goal.allowed_mutation_roots)

    sdk.record_implementation_goal_candidate("project-inquiry", derived)
    with pytest.raises(InvalidCommandError, match="admission"):
        sdk.seal_implementation_goal("project-inquiry", derived.goal)
    decision = GoalAdmissionDecision(
        id="goal-admission-g3g",
        candidate_id=derived.id,
        candidate_fingerprint=content_fingerprint("rci.implementation-goal-candidate.v1", derived),
        outcome=AdmissionOutcome.ADMIT,
        evidence_record_ids=goal_admission_evidence_ids(derived),
        admitted_goal_id=derived.goal.id,
    )
    sdk.decide_goal_admission("project-inquiry", decision)
    final = sdk.seal_admitted_implementation_goal("project-inquiry", candidate_id=derived.id)
    assert final.implementation_goals[-1] == derived.goal
    assert all(item.goal_id != derived.goal.id for item in final.candidate_environments)
    assert final.development_evidence[-1].goal_id != derived.goal.id
    assert final.promotion_decisions == ()
    exported = sdk.export("project-inquiry")
    assert sdk.replay("project-inquiry") == final
    assert sdk.export("project-inquiry") == exported


def test_alternate_return_and_tampering_remain_inert(tmp_path: Path) -> None:
    sdk, source_id, downstream_id, frontier_id = _setup(tmp_path / "goal")
    unknown = sdk.derive_implementation_goal_candidate(
        "project-inquiry",
        source_obligation_id=source_id,
        downstream_obligation_id="missing-downstream",
        frontier_id=frontier_id,
    )
    assert isinstance(unknown, GoalSynthesisUnknown)

    method_sdk, method_source, method_downstream, method_frontier = _setup(
        tmp_path / "method", answer="method-transport-required"
    )
    method_result = method_sdk.derive_implementation_goal_candidate(
        "project-inquiry",
        source_obligation_id=method_source,
        downstream_obligation_id=method_downstream,
        frontier_id=method_frontier,
    )
    assert isinstance(method_result, GoalSynthesisUnknown)
    assert method_result.reason == "return-class-not-goal-derivation"

    injection_sdk, injection_source, injection_downstream, injection_frontier = _setup(
        tmp_path / "injection",
        answer="goal-derivation-required; powershell -Command injected",
    )
    injection_result = injection_sdk.derive_implementation_goal_candidate(
        "project-inquiry",
        source_obligation_id=injection_source,
        downstream_obligation_id=injection_downstream,
        frontier_id=injection_frontier,
    )
    assert isinstance(injection_result, GoalSynthesisUnknown)

    derived = sdk.derive_implementation_goal_candidate(
        "project-inquiry",
        source_obligation_id=source_id,
        downstream_obligation_id=downstream_id,
        frontier_id=frontier_id,
    )
    assert isinstance(derived, ImplementationGoalCandidate)
    with pytest.raises(InvalidCommandError, match="pure deterministic compilation"):
        sdk.record_implementation_goal_candidate(
            "project-inquiry",
            derived.model_copy(
                update={
                    "goal": derived.goal.model_copy(
                        update={"acceptance_commands": ("powershell -Command injected",)}
                    )
                }
            ),
        )


def test_one_total_decision_and_canonical_cli_sdk_parity(tmp_path: Path) -> None:
    sdk, source_id, downstream_id, frontier_id = _setup(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "project",
            "goal-candidate",
            "project-inquiry",
            "--source-obligation-id",
            source_id,
            "--downstream-obligation-id",
            downstream_id,
            "--frontier-id",
            frontier_id,
            "--root",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    candidate = ImplementationGoalCandidate.model_validate_json(result.stdout, strict=True)
    assert candidate == sdk.inspect("project-inquiry").implementation_goal_candidates[-1]
    decision = GoalAdmissionDecision(
        id="goal-admission-cli",
        candidate_id=candidate.id,
        candidate_fingerprint=content_fingerprint(
            "rci.implementation-goal-candidate.v1", candidate
        ),
        outcome=AdmissionOutcome.ADMIT,
        evidence_record_ids=goal_admission_evidence_ids(candidate),
        admitted_goal_id=candidate.goal.id,
    )
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(decision.model_dump_json())
    decided = runner.invoke(
        app,
        [
            "project",
            "goal-decision",
            "project-inquiry",
            "--record",
            str(decision_path),
            "--root",
            str(tmp_path),
        ],
    )
    assert decided.exit_code == 0, decided.output
    with pytest.raises(IdentityConflictError, match="one total"):
        sdk.decide_goal_admission(
            "project-inquiry", decision.model_copy(update={"id": "different-decision"})
        )
    sealed = runner.invoke(
        app,
        [
            "project",
            "goal-seal-admitted",
            "project-inquiry",
            "--candidate-id",
            candidate.id,
            "--root",
            str(tmp_path),
        ],
    )
    assert sealed.exit_code == 0, sealed.output
    assert json.loads(sealed.stdout)["id"] == candidate.goal.id
