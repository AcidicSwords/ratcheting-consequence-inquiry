"""Blocking G3R acceptance: project succession is evidence-bound, never self-authorizing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from rci.claims import ClaimRole
from rci.cli import app
from rci.core.errors import IdentityConflictError, InvalidCommandError
from rci.project import (
    AdmissionOutcome,
    CandidateEnvironmentManifest,
    CapabilityLimitation,
    CapabilitySuccessorCandidate,
    CheckConclusion,
    ConsequentialReturn,
    CyclePhase,
    DevelopmentEvidence,
    EvidenceKind,
    EvidenceOutcome,
    ImplementationGoalContract,
    IndependentReview,
    LimitationKind,
    MethodAdmissionDecision,
    MethodBindingCandidate,
    ProjectAnchor,
    ProjectCost,
    ProjectDisposition,
    ProjectGainKind,
    ProjectSuccessorDecision,
    PromotionDecision,
    PromotionOutcome,
    QuestionContractCandidate,
    QuestionRepertoireDecision,
    RecursiveCycleCheckpoint,
    RecursiveStopDisposition,
    ReviewOutcome,
    StopReason,
    SuccessorKind,
    derive_capability_frontier,
)
from rci.questions import ContractMaturity, QuestionContract
from rci.sdk import RCI

BASE = "a" * 40
HEAD = "b" * 40
DIGEST = "1" * 64
GATE = "2" * 64
PROPOSED_GATE = "3" * 64


def _setup(sdk: RCI) -> tuple[ProjectAnchor, CapabilityLimitation]:
    sdk.start("project-inquiry")
    observation = sdk.artifacts.put_bytes(
        b"scheduler cannot derive a new question operator",
        media_type="text/plain",
        encoding="utf-8",
    )
    anchor = ProjectAnchor(
        id="anchor-main-g3ah",
        repository="AcidicSwords/ratcheting-consequence-inquiry",
        protected_branch="main",
        commit_sha=BASE,
        tree_digest=DIGEST,
        authority_digest="4" * 64,
        gate_digest=GATE,
        clean=True,
    )
    sdk.record_project_anchor("project-inquiry", anchor)
    limitation = CapabilityLimitation(
        id="limitation-self-selector",
        anchor_id=anchor.id,
        kind=LimitationKind.QUESTION,
        current_capability="Select among admitted contracts and a fixed learned-probe shape.",
        missing_capability="Derive and evaluate the smallest lawful question operator.",
        consequential_boundary=(
            "A missing operator can leave distinct roadmap successors "
            "observationally indistinguishable."
        ),
        protected_consequence_ids=("next-goal-quality", "sealed-predecessor-behavior"),
        observed_evidence=(observation,),
        existing_question_contract_keys=("learned-recurrent-probe/1.0.0",),
    )
    sdk.record_capability_limitation("project-inquiry", limitation)
    return anchor, limitation


def _candidate(
    anchor: ProjectAnchor,
    limitation: CapabilityLimitation,
    *,
    identity: str,
    kind: SuccessorKind,
    gain: ProjectGainKind,
    cost: int | None,
    discriminator: str | None,
) -> CapabilitySuccessorCandidate:
    return CapabilitySuccessorCandidate(
        id=identity,
        anchor_id=anchor.id,
        limitation_id=limitation.id,
        kind=kind,
        current_state="Roadmap choice is supplied manually.",
        desired_state="Roadmap choice is derived from a checked consequential boundary.",
        preserved_capability_ids=("g1", "g2a", "g2b", "g3ah"),
        gain_kinds=(gain,),
        discriminator_id=discriminator,
        evidence_mechanism_ids=("acceptance", "fresh-review", "hosted-ci"),
        estimated_costs=(ProjectCost(axis="missing_executable_seams", value=cost),),
        reversible=True,
    )


def _question_candidate(limitation: CapabilityLimitation) -> QuestionContractCandidate:
    contract = QuestionContract(
        id="project-missing-capability",
        version="0.1.0",
        family="recursive-project",
        input_roles=("limitation",),
        output_claim_role=ClaimRole.CHARACTERIZATION,
        precondition_policy_id="owned-project-limitation-v1",
        render_template="What return distinguishes {limitation}?",
        maturity=ContractMaturity.EXPERIMENTAL,
    )
    return QuestionContractCandidate(
        id="question-candidate-1",
        limitation_id=limitation.id,
        contract=contract,
        typed_referent_ids=(limitation.id,),
        precondition_ids=("owned-limitation",),
        possible_returns=(
            ConsequentialReturn(
                return_class_id="roadmap-required",
                downstream_state_id="select-roadmap",
                downstream_obligation_kind=LimitationKind.IMPLEMENTATION,
            ),
            ConsequentialReturn(
                return_class_id="selector-required",
                downstream_state_id="build-selector",
                downstream_obligation_kind=LimitationKind.QUESTION,
            ),
        ),
        comparison_policy_id="consequence-distinction-v1",
        downstream_consumer_ids=("frontier-builder",),
        falsifying_attack_ids=("same-outcome-attack",),
    )


def test_frontier_is_permutation_stable_and_prefers_smallest_reversible_discriminator(
    tmp_path: Path,
) -> None:
    sdk = RCI(tmp_path)
    anchor, limitation = _setup(sdk)
    linear = _candidate(
        anchor,
        limitation,
        identity="candidate-g3al",
        kind=SuccessorKind.REPRESENTATION,
        gain=ProjectGainKind.EXECUTABLE_RELATION,
        cost=8,
        discriminator="discriminator-linear-dependency",
    )
    selector = _candidate(
        anchor,
        limitation,
        identity="candidate-question-selector",
        kind=SuccessorKind.QUESTION_REPERTOIRE,
        gain=ProjectGainKind.NEW_SEPARATOR,
        cost=3,
        discriminator="discriminator-goal-quality",
    )
    left = derive_capability_frontier(frontier_id="frontier-1", candidates=(linear, selector))
    right = derive_capability_frontier(frontier_id="frontier-1", candidates=(selector, linear))
    assert left == right
    assert left.nondominated_candidate_ids == ("candidate-g3al", "candidate-question-selector")
    assert left.selected_discriminator_candidate_id == selector.id

    for item in (linear, selector):
        sdk.record_capability_successor_candidate("project-inquiry", item)
    sdk.record_capability_frontier("project-inquiry", left)
    with pytest.raises(InvalidCommandError):
        sdk.record_capability_frontier(
            "project-inquiry",
            left.model_copy(
                update={
                    "id": "frontier-forged",
                    "selected_discriminator_candidate_id": linear.id,
                }
            ),
        )


def test_repository_dogfood_keeps_six_successors_on_frontier_and_selects_question_basis(
    tmp_path: Path,
) -> None:
    sdk = RCI(tmp_path)
    anchor, limitation = _setup(sdk)
    specifications = (
        (
            "candidate-g3al-linear",
            SuccessorKind.REPRESENTATION,
            ProjectGainKind.EXECUTABLE_RELATION,
            4,
            "linear-binding-dependency-test",
        ),
        (
            "candidate-regenerative-question",
            SuccessorKind.QUESTION_REPERTOIRE,
            ProjectGainKind.NEW_SEPARATOR,
            1,
            "generated-contract-scheduler-test",
        ),
        (
            "candidate-native-method-binding",
            SuccessorKind.METHOD_REPERTOIRE,
            ProjectGainKind.NEW_METHOD,
            2,
            "native-assumption-transport-test",
        ),
        (
            "candidate-autonomous-goal-synthesis",
            SuccessorKind.GOAL_DECOMPOSITION,
            ProjectGainKind.INDEPENDENT_CHECKABILITY,
            3,
            "goal-sealing-quality-test",
        ),
        (
            "candidate-isolated-development-actuator",
            SuccessorKind.IMPLEMENTATION,
            ProjectGainKind.DEVELOPMENT_RECOVERY,
            4,
            "candidate-worktree-authority-test",
        ),
        (
            "candidate-g4-recursive-formal",
            SuccessorKind.METHOD_REPERTOIRE,
            ProjectGainKind.SCOPE_EXTENSION,
            5,
            "recursive-invariant-obligation-test",
        ),
    )
    candidates = tuple(
        _candidate(
            anchor,
            limitation,
            identity=identity,
            kind=kind,
            gain=gain,
            cost=cost,
            discriminator=discriminator,
        )
        for identity, kind, gain, cost, discriminator in specifications
    )
    frontier = derive_capability_frontier(
        frontier_id="frontier-g3r-roadmap-v1", candidates=reversed(candidates)
    )

    assert frontier.nondominated_candidate_ids == tuple(sorted(item.id for item in candidates))
    assert frontier.selected_discriminator_candidate_id == "candidate-regenerative-question"
    assert len(frontier.incomparable_pairs) == 15

    for candidate in candidates:
        sdk.record_capability_successor_candidate("project-inquiry", candidate)
    state = sdk.record_capability_frontier("project-inquiry", frontier)
    assert state.capability_frontiers == (frontier,)


def test_project_cli_exposes_complete_recording_surface_and_canonical_inspection(
    tmp_path: Path,
) -> None:
    sdk = RCI(tmp_path)
    anchor, _ = _setup(sdk)
    runner = CliRunner()
    help_result = runner.invoke(app, ["project", "--help"])
    assert help_result.exit_code == 0
    for command in (
        "anchor",
        "limitation",
        "question-candidate",
        "question-decision",
        "method-candidate",
        "method-decision",
        "frontier",
        "goal",
        "candidate",
        "evidence",
        "review",
        "successor",
        "promote",
        "checkpoint",
        "stop",
        "inspect",
    ):
        assert command in help_result.stdout

    first = runner.invoke(
        app,
        ["project", "inspect", "project-inquiry", "--root", str(tmp_path)],
    )
    second = runner.invoke(
        app,
        ["project", "inspect", "project-inquiry", "--root", str(tmp_path)],
    )
    assert first.exit_code == second.exit_code == 0
    assert first.stdout == second.stdout
    payload = json.loads(first.stdout)
    assert payload["project_anchors"] == [anchor.model_dump(mode="json")]


def test_cycle_continuity_is_monotone_and_stops_without_fabricating_progress(
    tmp_path: Path,
) -> None:
    sdk = RCI(tmp_path)
    anchor, limitation = _setup(sdk)
    report = sdk.artifacts.put_bytes(b"anchored", media_type="text/plain", encoding="utf-8")
    anchored = RecursiveCycleCheckpoint(
        id="checkpoint-anchored",
        cycle_id="cycle-g3r",
        phase=CyclePhase.ANCHORED,
        predecessor_id=None,
        record_ids=(anchor.id,),
        report_artifact=report,
    )
    first = sdk.record_recursive_cycle_checkpoint("project-inquiry", anchored)
    assert first.recursive_cycle_checkpoints == (anchored,)
    assert sdk.record_recursive_cycle_checkpoint("project-inquiry", anchored) == first

    limitation_checkpoint = RecursiveCycleCheckpoint(
        id="checkpoint-limitation",
        cycle_id="cycle-g3r",
        phase=CyclePhase.LIMITATION_RECORDED,
        predecessor_id=anchored.id,
        record_ids=(limitation.id,),
        report_artifact=sdk.artifacts.put_bytes(b"limitation recorded"),
    )
    sdk.record_recursive_cycle_checkpoint("project-inquiry", limitation_checkpoint)
    with pytest.raises(InvalidCommandError, match="advance monotonically"):
        sdk.record_recursive_cycle_checkpoint(
            "project-inquiry",
            RecursiveCycleCheckpoint(
                id="checkpoint-backward",
                cycle_id="cycle-g3r",
                phase=CyclePhase.ANCHORED,
                predecessor_id=limitation_checkpoint.id,
                record_ids=(anchor.id,),
                report_artifact=report,
            ),
        )

    stopped = RecursiveStopDisposition(
        id="stop-no-discriminator",
        cycle_id="cycle-g3r",
        reason=StopReason.NO_DISCRIMINATOR,
        consequential_residual_ids=(limitation.id,),
        evidence_artifact=sdk.artifacts.put_bytes(b"no lawful discriminator"),
    )
    final = sdk.record_recursive_stop_disposition("project-inquiry", stopped)
    assert final.recursive_stop_dispositions == (stopped,)
    assert final.sequence == sdk.replay("project-inquiry").sequence


def test_generated_question_is_inert_and_requires_distinct_consequential_returns(
    tmp_path: Path,
) -> None:
    sdk = RCI(tmp_path)
    _, limitation = _setup(sdk)
    candidate = _question_candidate(limitation)
    state = sdk.record_question_contract_candidate("project-inquiry", candidate)
    assert state.question_contract_candidates == (candidate,)
    assert all(
        probe.question_contract_key != candidate.contract.key for probe in state.admitted_probes
    )
    with pytest.raises(InvalidCommandError, match="owned development evidence"):
        sdk.decide_question_repertoire(
            "project-inquiry",
            QuestionRepertoireDecision(
                id="question-decision-forged",
                candidate_id=candidate.id,
                outcome=AdmissionOutcome.ADMIT,
                controller_policy_version="recursive-question-policy-v1",
                evidence_ids=("unowned-success-claim",),
                admitted_profile_id="recursive-project-v1",
            ),
        )
    wrong_family = candidate.model_copy(
        update={
            "id": "question-candidate-wrong-family",
            "contract": candidate.contract.model_copy(update={"family": "ordinary-inquiry"}),
        }
    )
    sdk.record_question_contract_candidate("project-inquiry", wrong_family)
    with pytest.raises(InvalidCommandError, match="confined to recursive-project"):
        sdk.decide_question_repertoire(
            "project-inquiry",
            QuestionRepertoireDecision(
                id="question-decision-wrong-family",
                candidate_id=wrong_family.id,
                outcome=AdmissionOutcome.ADMIT,
                controller_policy_version="recursive-question-policy-v1",
                evidence_ids=("unowned-success-claim",),
                admitted_profile_id="recursive-project-v1",
            ),
        )

    with pytest.raises(ValueError, match="two consequentially distinct"):
        QuestionContractCandidate(
            id="question-candidate-invalid",
            limitation_id=limitation.id,
            contract=candidate.contract,
            typed_referent_ids=(limitation.id,),
            precondition_ids=("owned-limitation",),
            possible_returns=(
                candidate.possible_returns[0],
                candidate.possible_returns[1].model_copy(
                    update={"downstream_state_id": "select-roadmap"}
                ),
            ),
            comparison_policy_id="consequence-distinction-v1",
            downstream_consumer_ids=("frontier-builder",),
            falsifying_attack_ids=("same-outcome-attack",),
        )


def test_sealed_goal_candidate_review_and_promotion_are_separate_exact_head_stages(
    tmp_path: Path,
) -> None:
    sdk = RCI(tmp_path)
    anchor, limitation = _setup(sdk)
    candidate = _candidate(
        anchor,
        limitation,
        identity="candidate-g3r",
        kind=SuccessorKind.IMPLEMENTATION,
        gain=ProjectGainKind.INDEPENDENT_CHECKABILITY,
        cost=5,
        discriminator="recursive-acceptance",
    )
    sdk.record_capability_successor_candidate("project-inquiry", candidate)
    frontier = derive_capability_frontier(frontier_id="frontier-g3r", candidates=(candidate,))
    sdk.record_capability_frontier("project-inquiry", frontier)
    goal = ImplementationGoalContract(
        id="goal-g3r",
        cycle_id="cycle-1",
        anchor_id=anchor.id,
        frontier_id=frontier.id,
        candidate_id=candidate.id,
        current="Development intent is transient.",
        desired="Development intent and evidence form a replayable proof chain.",
        separator="The focused recursive acceptance fails before and passes after the candidate.",
        expected_incumbent_return="No project-domain record exists.",
        expected_candidate_return="The full chain replays without source or Git effects.",
        preserve_capability_ids=candidate.preserved_capability_ids,
        acceptance_commands=(
            "uv run pytest -q tests/acceptance/test_recursive_project_inquiry.py",
        ),
        allowed_mutation_roots=("src/rci/project", "tests/acceptance"),
        forbidden_authority_roots=(".github", "AGENTS.md", "PLAN.md", "RCI_Project_Spec.tex"),
        assumption_ids=("git-worktree-available", "hosted-ci-available"),
        incumbent_gate_digest=GATE,
        proposed_gate_digest=PROPOSED_GATE,
        rollback_condition="Any protected predecessor check regresses.",
        reopening_condition="A future candidate cannot be distinguished by the admitted basis.",
    )
    sdk.seal_implementation_goal("project-inquiry", goal)
    with pytest.raises(ValueError, match="repository-relative"):
        ImplementationGoalContract.model_validate(
            {
                **goal.model_dump(mode="python"),
                "id": "goal-path-escape",
                "allowed_mutation_roots": ("src/../AGENTS.md",),
            },
            strict=True,
        )
    with pytest.raises(IdentityConflictError, match="immutable"):
        sdk.seal_implementation_goal(
            "project-inquiry", goal.model_copy(update={"desired": "Move the target after return."})
        )

    toolchain = sdk.artifacts.put_bytes(b"python=3.12\nuv=0.9.18")
    environment = CandidateEnvironmentManifest(
        id="environment-g3r",
        goal_id=goal.id,
        developer_id="codex-developer-context",
        base_commit_sha=BASE,
        candidate_branch="codex/g3r",
        worktree_path=".rci/workspaces/cycle-1",
        initial_tree_digest=DIGEST,
        toolchain_artifact=toolchain,
        toolchain_digest="5" * 64,
    )
    sdk.record_candidate_environment("project-inquiry", environment)
    observed = sdk.artifacts.put_bytes(b"1 passed")
    evidence = DevelopmentEvidence(
        id="evidence-focused-g3r",
        goal_id=goal.id,
        candidate_environment_id=environment.id,
        kind=EvidenceKind.TEST,
        command_or_method=goal.acceptance_commands[0],
        outcome=EvidenceOutcome.PASS,
        observed_return=observed,
        base_commit_sha=BASE,
        candidate_commit_sha=HEAD,
        gate_digest=PROPOSED_GATE,
    )
    sdk.record_development_evidence("project-inquiry", evidence)
    findings = sdk.artifacts.put_bytes(b"no blocking finding")
    with pytest.raises(InvalidCommandError, match="independent"):
        sdk.record_independent_review(
            "project-inquiry",
            IndependentReview(
                id="review-self",
                goal_id=goal.id,
                candidate_environment_id=environment.id,
                reviewer_id=environment.developer_id,
                reviewer_context_digest="6" * 64,
                reviewed_commit_sha=HEAD,
                evidence_ids=(evidence.id,),
                outcome=ReviewOutcome.VALID,
                findings_artifact=findings,
            ),
        )
    review = IndependentReview(
        id="review-fresh",
        goal_id=goal.id,
        candidate_environment_id=environment.id,
        reviewer_id="codex-fresh-reviewer-context",
        reviewer_context_digest="6" * 64,
        reviewed_commit_sha=HEAD,
        evidence_ids=(evidence.id,),
        outcome=ReviewOutcome.VALID,
        findings_artifact=findings,
    )
    sdk.record_independent_review("project-inquiry", review)
    question_candidate = _question_candidate(limitation)
    sdk.record_question_contract_candidate("project-inquiry", question_candidate)
    admitted = QuestionRepertoireDecision(
        id="question-decision-reviewed",
        candidate_id=question_candidate.id,
        outcome=AdmissionOutcome.ADMIT,
        controller_policy_version="recursive-question-policy-v1",
        evidence_ids=(evidence.id,),
        admitted_profile_id="recursive-project-v1",
    )
    admission_state = sdk.decide_question_repertoire("project-inquiry", admitted)
    assert admission_state.question_repertoire_decisions == (admitted,)
    method_candidate = MethodBindingCandidate(
        id="method-candidate-cegar",
        limitation_id=limitation.id,
        relation_id="failed-candidate-refinement",
        native_field="counterexample-guided abstraction refinement",
        method_id="cegar-v1",
        primary_source_urls=("https://web.stanford.edu/class/cs357/cegar.pdf",),
        source_artifacts=(findings,),
        assumption_ids=("finite-checkable-abstraction",),
        applicability_check_ids=("counterexample-check",),
        license_id="research-paper-reference",
        adapter_required=False,
    )
    sdk.record_method_binding_candidate("project-inquiry", method_candidate)
    method_decision = MethodAdmissionDecision(
        id="method-decision-reviewed",
        candidate_id=method_candidate.id,
        outcome=AdmissionOutcome.ADMIT,
        method_policy_version="project-method-policy-v1",
        evidence_ids=(evidence.id,),
    )
    method_state = sdk.decide_method_admission("project-inquiry", method_decision)
    assert method_state.method_admission_decisions == (method_decision,)

    unreviewed = evidence.model_copy(
        update={
            "id": "evidence-unreviewed",
            "observed_return": sdk.artifacts.put_bytes(b"unreviewed pass"),
        }
    )
    sdk.record_development_evidence("project-inquiry", unreviewed)
    with pytest.raises(InvalidCommandError, match="exactly the reviewed evidence"):
        sdk.decide_project_successor(
            "project-inquiry",
            ProjectSuccessorDecision(
                id="successor-forged-evidence",
                goal_id=goal.id,
                candidate_id=candidate.id,
                candidate_environment_id=environment.id,
                review_id=review.id,
                evidence_ids=(unreviewed.id,),
                disposition=ProjectDisposition.REPLACE,
                preserved_capability_ids=candidate.preserved_capability_ids,
                gain_kinds=candidate.gain_kinds,
                reason="A pass the reviewer never saw must remain unusable.",
            ),
        )
    successor = ProjectSuccessorDecision(
        id="successor-g3r",
        goal_id=goal.id,
        candidate_id=candidate.id,
        candidate_environment_id=environment.id,
        review_id=review.id,
        evidence_ids=(evidence.id,),
        disposition=ProjectDisposition.REPLACE,
        preserved_capability_ids=candidate.preserved_capability_ids,
        gain_kinds=candidate.gain_kinds,
        reason="The sealed discriminator passed with a fresh valid review.",
    )
    sdk.decide_project_successor("project-inquiry", successor)
    promotion = PromotionDecision(
        id="promotion-g3r",
        successor_decision_id=successor.id,
        candidate_commit_sha=HEAD,
        pull_request_url="https://github.com/AcidicSwords/ratcheting-consequence-inquiry/pull/4",
        required_checks=(
            CheckConclusion(context="base (ubuntu-latest)", conclusion="success"),
            CheckConclusion(context="recursive (ubuntu-latest)", conclusion="success"),
        ),
        outcome=PromotionOutcome.MERGED,
        merged_commit_sha="c" * 40,
    )
    final = sdk.record_promotion_decision("project-inquiry", promotion)
    assert final.promotion_decisions == (promotion,)
    assert sdk.replay("project-inquiry") == final
    assert not hasattr(sdk, "merge")


def test_valid_review_cannot_bless_failing_evidence(tmp_path: Path) -> None:
    sdk = RCI(tmp_path)
    anchor, limitation = _setup(sdk)
    candidate = _candidate(
        anchor,
        limitation,
        identity="candidate-failing",
        kind=SuccessorKind.IMPLEMENTATION,
        gain=ProjectGainKind.REPAIRED_FAILURE,
        cost=1,
        discriminator="failing-check",
    )
    sdk.record_capability_successor_candidate("project-inquiry", candidate)
    frontier = derive_capability_frontier(frontier_id="frontier-failing", candidates=(candidate,))
    sdk.record_capability_frontier("project-inquiry", frontier)
    goal = ImplementationGoalContract(
        id="goal-failing",
        cycle_id="cycle-failing",
        anchor_id=anchor.id,
        frontier_id=frontier.id,
        candidate_id=candidate.id,
        current="Failing boundary.",
        desired="Passing boundary.",
        separator="Exact failing test.",
        expected_incumbent_return="failure",
        expected_candidate_return="success",
        preserve_capability_ids=candidate.preserved_capability_ids,
        acceptance_commands=("uv run pytest -q failing.py",),
        allowed_mutation_roots=("src/rci/project",),
        forbidden_authority_roots=("AGENTS.md",),
        assumption_ids=("fixture",),
        incumbent_gate_digest=GATE,
        proposed_gate_digest=PROPOSED_GATE,
        rollback_condition="Regression.",
        reopening_condition="Counterexample.",
    )
    sdk.seal_implementation_goal("project-inquiry", goal)
    toolchain = sdk.artifacts.put_bytes(b"toolchain")
    environment = CandidateEnvironmentManifest(
        id="env-failing",
        goal_id=goal.id,
        developer_id="developer",
        base_commit_sha=BASE,
        candidate_branch="codex/failing",
        worktree_path=".rci/workspaces/failing",
        initial_tree_digest=DIGEST,
        toolchain_artifact=toolchain,
        toolchain_digest="7" * 64,
    )
    sdk.record_candidate_environment("project-inquiry", environment)
    evidence = DevelopmentEvidence(
        id="failed-evidence",
        goal_id=goal.id,
        candidate_environment_id=environment.id,
        kind=EvidenceKind.TEST,
        command_or_method=goal.acceptance_commands[0],
        outcome=EvidenceOutcome.FAIL,
        observed_return=sdk.artifacts.put_bytes(b"FAILED"),
        base_commit_sha=BASE,
        candidate_commit_sha=HEAD,
        gate_digest=PROPOSED_GATE,
    )
    sdk.record_development_evidence("project-inquiry", evidence)
    with pytest.raises(InvalidCommandError, match="cannot bless"):
        sdk.record_independent_review(
            "project-inquiry",
            IndependentReview(
                id="review-invalid-blessing",
                goal_id=goal.id,
                candidate_environment_id=environment.id,
                reviewer_id="fresh-reviewer",
                reviewer_context_digest="8" * 64,
                reviewed_commit_sha=HEAD,
                evidence_ids=(evidence.id,),
                outcome=ReviewOutcome.VALID,
                findings_artifact=sdk.artifacts.put_bytes(b"incorrectly valid"),
            ),
        )
