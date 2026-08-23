"""Blocking G3FO acceptance: exact failure observation without self-diagnosis."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from rci.cli import app
from rci.core.effects import (
    AttemptState,
    Decoded,
    EffectAttemptPlan,
    EffectRequest,
    EffectRequestState,
    ExternalReturn,
    MalformedDecode,
    NoAttemptDisposition,
    NoAttemptReason,
    PresentationUnknownOutcome,
    PresentationUnknownReason,
    ReturnedOutcome,
    RouteSnapshot,
    SuccessResult,
)
from rci.core.model import ArtifactRef, CapturedPayload
from rci.core.serialization import canonical_json_bytes, sha256_digest
from rci.evaluation import (
    CapabilityEvaluationEpisode,
    CapabilityEvaluationProtocol,
    ConsequenceObservation,
    DecodeIndeterminateObserved,
    EvaluationPassed,
    EvaluationProtocolInvalid,
    HandoffStatus,
    OperationalUnknownObserved,
    OperationalUnknownReason,
    ProtectedExpectation,
    ProtectedMismatchObserved,
    build_capability_consequence_report,
    build_capability_evaluation_protocol,
    capability_report_artifact,
    run_weak_reasoner_fixture,
)
from rci.probes import Mismatch, PredictionSeal
from rci.sdk import RCI
from rci.warrant import CheckerVerdict, CheckerVerdictRecord, PropositionKind

NOW = datetime(2026, 8, 22, tzinfo=UTC)
SCOPE = "1" * 64
GATE = "2" * 64
HEAD = "a" * 40
ACTOR = "scripted-weak-reasoner"
ACTOR_REVISION = "1"
ROUTE = "weak-reasoner-route"


def _stored(sdk: RCI, value: bytes, media_type: str = "application/octet-stream") -> ArtifactRef:
    return sdk.artifacts.put_bytes(value, media_type=media_type, encoding="utf-8")


def _protocol(
    sdk: RCI, consequence_ids: tuple[str, ...]
) -> tuple[CapabilityEvaluationProtocol, ArtifactRef]:
    expectations = tuple(
        ProtectedExpectation(
            consequence_id=consequence_id,
            expected_artifact=_stored(sdk, f"expected:{consequence_id}".encode()),
            attack_id=f"attack-{consequence_id}",
            downstream_question_id=f"question-{consequence_id}",
        )
        for consequence_id in sorted(consequence_ids)
    )
    protocol = build_capability_evaluation_protocol(
        anchor_id="anchor-g3fo",
        goal_id="goal-g3fo",
        obligation_id="obligation-evaluate-capability",
        step_plan_id="step-evaluate-capability",
        competence_id="competence-reason-over-finite-relations",
        project_head_sha=HEAD,
        gate_digest=GATE,
        binding_revision="capability-evaluation-binding-v1",
        scope_fingerprint=SCOPE,
        protected_horizon_id="g3fo-finite-horizon",
        operation_id="answer-finite-relation-task",
        effect_kind="capability-evaluation",
        actor_id=ACTOR,
        actor_revision=ACTOR_REVISION,
        adapter_id="scripted-reasoner-adapter",
        route_definition_id=ROUTE,
        route_definition_version="1",
        context_artifact=_stored(sdk, b"bounded task context"),
        evidence_access_artifact=_stored(sdk, b"finite evidence universe"),
        budget_artifact=_stored(sdk, b'{"attempts":1,"checks":2}'),
        timeout_seconds=30,
        comparison_policy_id="exact-artifact-equality",
        comparison_policy_version="1",
        decoder_id="capability-report-decoder",
        decoder_version="1",
        checker_id="deterministic-report-checker",
        checker_version="1",
        expectations=expectations,
        discriminator_route_ids=("counterexample-check-route",),
        protected_capability_ids=("g1-authority", "g3r-stage-separation"),
        stopping_condition_ids=("no-lawful-discriminator", "protocol-invalid"),
        reopening_condition_ids=("new-independent-evidence",),
    )
    return protocol, sdk.publish_capability_evaluation_protocol(protocol)


def _prediction(protocol: CapabilityEvaluationProtocol) -> PredictionSeal:
    return PredictionSeal(
        id="prediction-g3fo",
        cognitive_plan_id=protocol.step_plan_id,
        probe_or_action_id=protocol.operation_id,
        predicted_return_class="capability-consequence-report",
        predicted_consequence={
            "comparison_policy_id": protocol.comparison_policy_id,
            "comparison_policy_version": protocol.comparison_policy_version,
            "expectations": [
                {
                    "consequence_id": item.consequence_id,
                    "expected_artifact_digest": item.expected_artifact.digest,
                }
                for item in protocol.expectations
            ],
            "protocol_id": protocol.id,
        },
        acceptable_variation={
            "comparison_policy_id": protocol.comparison_policy_id,
            "comparison_policy_version": protocol.comparison_policy_version,
        },
        scope_fingerprint=SCOPE,
        basis_claim_ids=("task-contract",),
        sealed_sequence=1,
    )


def _request(
    protocol: CapabilityEvaluationProtocol, protocol_artifact: ArtifactRef
) -> EffectRequest:
    return EffectRequest(
        id="request-g3fo",
        step_plan_id=protocol.step_plan_id,
        effect_kind=protocol.effect_kind,
        adapter_id=protocol.adapter_id,
        input_artifact=protocol_artifact,
        timeout_seconds=protocol.timeout_seconds,
    )


def _semantic_episode(
    sdk: RCI,
    consequence_ids: tuple[str, ...],
    *,
    mismatched_ids: frozenset[str] = frozenset(),
    reverse_mismatches: bool = False,
) -> CapabilityEvaluationEpisode:
    protocol, protocol_artifact = _protocol(sdk, consequence_ids)
    request = _request(protocol, protocol_artifact)
    observations = []
    for expectation in protocol.expectations:
        actual = (
            _stored(sdk, f"wrong:{expectation.consequence_id}".encode())
            if expectation.consequence_id in mismatched_ids
            else expectation.expected_artifact
        )
        observations.append(
            ConsequenceObservation(
                consequence_id=expectation.consequence_id,
                actual_artifact=actual,
                evidence_artifacts=(
                    _stored(sdk, f"evidence:{expectation.consequence_id}".encode()),
                ),
            )
        )
    report = build_capability_consequence_report(
        protocol_id=protocol.id, observations=tuple(observations)
    )
    report_ref = sdk.artifacts.put_bytes(
        canonical_json_bytes(report),
        media_type="application/vnd.rci.capability-consequence-report+json",
        encoding="utf-8",
    )
    assert report_ref == capability_report_artifact(report)
    definition = _stored(sdk, b"route definition")
    environment = _stored(sdk, b"redacted environment")
    route = RouteSnapshot(
        id="route-snapshot-g3fo",
        definition_id=protocol.route_definition_id,
        definition_version=protocol.route_definition_version,
        definition_artifact=definition,
        backend_id="scripted-backend",
        adapter_id=protocol.adapter_id,
        adapter_version="1",
        endpoint_or_channel="in-process",
        transport="pure",
        execution_environment_artifact=environment,
        request_or_action_digest=sha256_digest(canonical_json_bytes(request)),
    )
    raw = _stored(sdk, b"model prose including: I am certainly correct")
    returned = ReturnedOutcome(
        attempt_id="attempt-g3fo",
        route_id=route.id,
        external_return=ExternalReturn(
            id="external-return-g3fo",
            attempt_id="attempt-g3fo",
            route_id=route.id,
            source_id=ACTOR,
            source_revision=ACTOR_REVISION,
            capture_boundary="scripted-stdout",
            capture_encoding="binary",
            captured_at=NOW,
            raw_payload=CapturedPayload(kind="bytes", artifact=raw),
        ),
    )
    attempt = AttemptState(
        plan=EffectAttemptPlan(
            id="attempt-g3fo",
            request_id=request.id,
            route=route,
        ),
        started=True,
        started_event_id="event-attempt-started",
        started_at=NOW,
        outcome=returned,
    )
    decoded = Decoded(
        id="decode-g3fo",
        external_return_id=returned.external_return.id,
        decoder_id=protocol.decoder_id,
        decoder_version=protocol.decoder_version,
        result=SuccessResult(
            id="canonical-result-g3fo",
            semantic_artifact=report_ref,
            operation_id=protocol.operation_id,
        ),
    )
    checker = CheckerVerdictRecord(
        id="checker-verdict-g3fo",
        evidence_id="report-evidence-g3fo",
        evidence_artifact=report_ref,
        proposition_id=f"capability-report:{report.id}",
        proposition_kind=PropositionKind.RELATION,
        scope_fingerprint=SCOPE,
        checker_id=protocol.checker_id,
        checker_version=protocol.checker_version,
        verdict=CheckerVerdict.VALID,
        verdict_artifact=_stored(sdk, b"valid report structure and exact comparison"),
        certificate_artifact=_stored(sdk, b"deterministic comparison certificate"),
    )
    prediction = _prediction(protocol)
    mismatches = [
        Mismatch(
            id=f"mismatch-{consequence_id}",
            prediction_id=prediction.id,
            external_return_id=returned.external_return.id,
            decode_outcome_id=decoded.id,
            difference_claim_id=f"difference-{consequence_id}",
            scope_fingerprint=SCOPE,
            protected_consequence_changed=True,
            classification=f"capability:{consequence_id}",
        )
        for consequence_id in sorted(mismatched_ids)
    ]
    if reverse_mismatches:
        mismatches.reverse()
    return CapabilityEvaluationEpisode(
        protocol=protocol,
        protocol_artifact=protocol_artifact,
        effect=EffectRequestState(
            request=request,
            attempts=(attempt,),
            decode_outcomes=(decoded,),
            accepted_decoded_outcome_id=decoded.id,
        ),
        prediction=prediction,
        checker_verdict=checker,
        mismatches=tuple(mismatches),
    )


def _malformed_episode(sdk: RCI) -> CapabilityEvaluationEpisode:
    protocol, protocol_artifact = _protocol(sdk, ("answer-valid",))
    request = _request(protocol, protocol_artifact)
    route = RouteSnapshot(
        id="route-snapshot-g3fo",
        definition_id=protocol.route_definition_id,
        definition_version=protocol.route_definition_version,
        definition_artifact=_stored(sdk, b"route definition"),
        backend_id="scripted-backend",
        adapter_id=protocol.adapter_id,
        adapter_version="1",
        endpoint_or_channel="in-process",
        transport="pure",
        execution_environment_artifact=_stored(sdk, b"redacted environment"),
        request_or_action_digest=sha256_digest(canonical_json_bytes(request)),
    )
    returned = ReturnedOutcome(
        attempt_id="attempt-g3fo",
        route_id=route.id,
        external_return=ExternalReturn(
            id="external-return-g3fo",
            attempt_id="attempt-g3fo",
            route_id=route.id,
            source_id=ACTOR,
            source_revision=ACTOR_REVISION,
            capture_boundary="scripted-stdout",
            capture_encoding="binary",
            captured_at=NOW,
            raw_payload=CapturedPayload(
                kind="bytes", artifact=_stored(sdk, b"not valid report json")
            ),
        ),
    )
    malformed = MalformedDecode(
        id="decode-malformed",
        external_return_id=returned.external_return.id,
        decoder_id=protocol.decoder_id,
        decoder_version=protocol.decoder_version,
        diagnostics=_stored(sdk, b"json syntax error"),
    )
    return CapabilityEvaluationEpisode(
        protocol=protocol,
        protocol_artifact=protocol_artifact,
        effect=EffectRequestState(
            request=request,
            attempts=(
                AttemptState(
                    plan=EffectAttemptPlan(id="attempt-g3fo", request_id=request.id, route=route),
                    started=True,
                    started_event_id="event-attempt-started",
                    started_at=NOW,
                    outcome=returned,
                ),
            ),
            decode_outcomes=(malformed,),
        ),
        prediction=_prediction(protocol),
    )


def _operational_episode(sdk: RCI, kind: str) -> CapabilityEvaluationEpisode:
    protocol, protocol_artifact = _protocol(sdk, ("answer-valid",))
    request = _request(protocol, protocol_artifact)
    if kind == "unsupported":
        effect = EffectRequestState(
            request=request,
            no_attempt_dispositions=(
                NoAttemptDisposition(
                    id="no-attempt-unsupported",
                    request_id=request.id,
                    step_plan_id=request.step_plan_id,
                    reason_kind=NoAttemptReason.UNSUPPORTED,
                    diagnostics=_stored(sdk, b"route unsupported"),
                ),
            ),
        )
    else:
        route = RouteSnapshot(
            id="route-snapshot-g3fo",
            definition_id=protocol.route_definition_id,
            definition_version=protocol.route_definition_version,
            definition_artifact=_stored(sdk, b"route definition"),
            backend_id="scripted-backend",
            adapter_id=protocol.adapter_id,
            adapter_version="1",
            endpoint_or_channel="in-process",
            transport="pure",
            execution_environment_artifact=_stored(sdk, b"redacted environment"),
            request_or_action_digest=sha256_digest(canonical_json_bytes(request)),
        )
        effect = EffectRequestState(
            request=request,
            attempts=(
                AttemptState(
                    plan=EffectAttemptPlan(id="attempt-g3fo", request_id=request.id, route=route),
                    started=True,
                    started_event_id="event-attempt-started",
                    started_at=NOW,
                    outcome=PresentationUnknownOutcome(
                        attempt_id="attempt-g3fo",
                        route_id=route.id,
                        reason_kind=PresentationUnknownReason.TIMEOUT,
                        diagnostics=_stored(sdk, b"deadline elapsed; presentation unknown"),
                    ),
                ),
            ),
        )
    return CapabilityEvaluationEpisode(
        protocol=protocol,
        protocol_artifact=protocol_artifact,
        effect=effect,
        prediction=_prediction(protocol),
    )


def test_six_consequential_outcomes_remain_distinct(tmp_path: Path) -> None:
    sdk = RCI(tmp_path)
    passed = sdk.evaluate_capability_episode(_semantic_episode(sdk, ("answer-valid",)))
    necessity = sdk.evaluate_capability_episode(
        _semantic_episode(
            sdk,
            ("false-necessity",),
            mismatched_ids=frozenset({"false-necessity"}),
        )
    )
    may_must = sdk.evaluate_capability_episode(
        _semantic_episode(
            sdk,
            ("may-must-collapse",),
            mismatched_ids=frozenset({"may-must-collapse"}),
        )
    )
    malformed = sdk.evaluate_capability_episode(_malformed_episode(sdk))
    timeout = sdk.evaluate_capability_episode(_operational_episode(sdk, "timeout"))
    unsupported = sdk.evaluate_capability_episode(_operational_episode(sdk, "unsupported"))

    assert isinstance(passed.result, EvaluationPassed)
    assert isinstance(necessity.result, ProtectedMismatchObserved)
    assert isinstance(may_must.result, ProtectedMismatchObserved)
    assert necessity.result.violations[0].consequence_id == "false-necessity"
    assert may_must.result.violations[0].consequence_id == "may-must-collapse"
    assert necessity.result.violations[0].attack_id != may_must.result.violations[0].attack_id
    assert necessity.limitation_candidate is not None
    assert may_must.limitation_candidate is not None
    assert isinstance(malformed.result, DecodeIndeterminateObserved)
    assert malformed.result.reason_kind == "malformed"
    assert malformed.limitation_candidate is None
    assert isinstance(timeout.result, OperationalUnknownObserved)
    assert timeout.result.reason_kind is OperationalUnknownReason.TIMEOUT
    assert isinstance(unsupported.result, OperationalUnknownObserved)
    assert unsupported.result.reason_kind is OperationalUnknownReason.NO_ATTEMPT_UNSUPPORTED
    assert timeout.limitation_candidate is unsupported.limitation_candidate is None


def test_root_cause_stays_unresolved_and_handoff_does_not_repeat_route(tmp_path: Path) -> None:
    sdk = RCI(tmp_path)
    episode = _semantic_episode(
        sdk,
        ("false-necessity",),
        mismatched_ids=frozenset({"false-necessity"}),
    )
    first = sdk.evaluate_capability_episode(episode)
    second = sdk.evaluate_capability_episode(episode)
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert first.localization_frame is not None
    assert first.localization_frame.selected_limitation_kind is None
    assert len(first.localization_frame.live_limitation_kinds) == 8
    assert first.handoff.status is HandoffStatus.CONTINUE
    assert ROUTE in first.handoff.forbidden_route_ids_until_reopen
    assert first.handoff.next_discriminator_route_id != ROUTE
    assert first.handoff.project_head_sha == HEAD
    assert first.handoff.gate_digest == GATE
    assert sdk.events.stream_version("unrelated") == 0


def test_protocol_mutation_foreign_budget_and_missing_artifact_fail_closed(
    tmp_path: Path,
) -> None:
    sdk = RCI(tmp_path)
    episode = _semantic_episode(sdk, ("answer-valid",))
    changed_request = episode.effect.request.model_copy(update={"timeout_seconds": 31})
    changed = episode.model_copy(
        update={"effect": episode.effect.model_copy(update={"request": changed_request})}
    )
    invalid = sdk.evaluate_capability_episode(changed)
    assert isinstance(invalid.result, EvaluationProtocolInvalid)
    assert "foreign_budget" in invalid.result.issue_codes
    assert invalid.limitation_candidate is None

    sdk.artifacts.path_for(episode.protocol.context_artifact).unlink()
    missing = sdk.evaluate_capability_episode(episode)
    assert isinstance(missing.result, EvaluationProtocolInvalid)
    assert missing.result.issue_codes == ("artifact_missing_tampered_or_malformed",)


def test_late_return_and_unaccepted_decode_fail_closed(tmp_path: Path) -> None:
    sdk = RCI(tmp_path)
    episode = _semantic_episode(sdk, ("answer-valid",))
    accepted = episode.effect.decode_outcomes[0]
    extra = accepted.model_copy(update={"id": "decode-late"})
    altered_effect = episode.effect.model_copy(update={"decode_outcomes": (accepted, extra)})
    invalid = sdk.evaluate_capability_episode(episode.model_copy(update={"effect": altered_effect}))
    assert isinstance(invalid.result, EvaluationProtocolInvalid)
    assert "unaccepted_decode_present" in invalid.result.issue_codes


def test_foreign_actor_and_route_fail_closed_without_blame(tmp_path: Path) -> None:
    sdk = RCI(tmp_path)
    episode = _semantic_episode(sdk, ("answer-valid",))
    attempt = episode.effect.attempts[0]
    assert isinstance(attempt.outcome, ReturnedOutcome)
    foreign_return = attempt.outcome.external_return.model_copy(
        update={"source_id": "different-actor"}
    )
    foreign_outcome = attempt.outcome.model_copy(update={"external_return": foreign_return})
    foreign_route = attempt.plan.route.model_copy(update={"definition_id": "foreign-route"})
    foreign_attempt = attempt.model_copy(
        update={
            "plan": attempt.plan.model_copy(update={"route": foreign_route}),
            "outcome": foreign_outcome,
        }
    )
    altered = episode.model_copy(
        update={"effect": episode.effect.model_copy(update={"attempts": (foreign_attempt,)})}
    )
    invalid = sdk.evaluate_capability_episode(altered)
    assert isinstance(invalid.result, EvaluationProtocolInvalid)
    assert {"foreign_actor", "foreign_route"} <= set(invalid.result.issue_codes)
    assert invalid.limitation_candidate is None


def test_mismatch_input_permutation_is_byte_stable(tmp_path: Path) -> None:
    sdk = RCI(tmp_path)
    consequence_ids = ("false-necessity", "may-must-collapse")
    forward = _semantic_episode(
        sdk,
        consequence_ids,
        mismatched_ids=frozenset(consequence_ids),
    )
    reverse = _semantic_episode(
        sdk,
        consequence_ids,
        mismatched_ids=frozenset(consequence_ids),
        reverse_mismatches=True,
    )
    assert canonical_json_bytes(sdk.evaluate_capability_episode(forward)) == canonical_json_bytes(
        sdk.evaluate_capability_episode(reverse)
    )


def test_exact_consequence_compares_captured_bytes_not_media_labels(tmp_path: Path) -> None:
    sdk = RCI(tmp_path)
    episode = _semantic_episode(sdk, ("answer-valid",))
    expected = episode.protocol.expectations[0].expected_artifact
    report = build_capability_consequence_report(
        protocol_id=episode.protocol.id,
        observations=(
            ConsequenceObservation(
                consequence_id="answer-valid",
                actual_artifact=expected.model_copy(
                    update={"media_type": "application/vnd.example.same-bytes"}
                ),
                evidence_artifacts=(_stored(sdk, b"same-byte comparison evidence"),),
            ),
        ),
    )
    report_ref = sdk.artifacts.put_bytes(
        canonical_json_bytes(report),
        media_type="application/vnd.rci.capability-consequence-report+json",
        encoding="utf-8",
    )
    decoded = episode.effect.decode_outcomes[0]
    assert isinstance(decoded, Decoded)
    altered_decode = decoded.model_copy(
        update={"result": decoded.result.model_copy(update={"semantic_artifact": report_ref})}
    )
    checker = episode.checker_verdict
    assert checker is not None
    altered_checker = checker.model_copy(
        update={
            "evidence_artifact": report_ref,
            "proposition_id": f"capability-report:{report.id}",
        }
    )
    altered = episode.model_copy(
        update={
            "effect": episode.effect.model_copy(update={"decode_outcomes": (altered_decode,)}),
            "checker_verdict": altered_checker,
        }
    )
    assert isinstance(sdk.evaluate_capability_episode(altered).result, EvaluationPassed)


def test_sdk_cli_parity_and_model_prose_is_inert(tmp_path: Path) -> None:
    sdk = RCI(tmp_path)
    episode = _semantic_episode(
        sdk,
        ("false-necessity",),
        mismatched_ids=frozenset({"false-necessity"}),
    )
    record = tmp_path / "episode.json"
    record.write_bytes(canonical_json_bytes(episode))
    runner = CliRunner()
    evaluated = runner.invoke(
        app,
        ["project", "evaluate", "--record", str(record), "--root", str(tmp_path)],
    )
    handed = runner.invoke(
        app,
        ["project", "handoff", "--record", str(record), "--root", str(tmp_path)],
    )
    assert evaluated.exit_code == 0, evaluated.output
    assert handed.exit_code == 0, handed.output
    assert json.loads(evaluated.stdout) == sdk.evaluate_capability_episode(episode).model_dump(
        mode="json"
    )
    assert json.loads(handed.stdout) == sdk.capability_handoff(episode).model_dump(mode="json")
    assert "model prose" not in evaluated.stdout


def test_bounded_weak_reasoner_improves_exact_conclusions_only() -> None:
    fixture = run_weak_reasoner_fixture(
        actor_manifest_digest="3" * 64,
        evidence_universe_digest="4" * 64,
        budget_digest="5" * 64,
    )
    assert [item.correct for item in fixture.baseline.conclusions] == [False, False]
    assert [item.correct for item in fixture.assisted.conclusions] == [True, True]
    assert fixture.baseline.actor_manifest_digest == fixture.assisted.actor_manifest_digest
    assert fixture.baseline.evidence_universe_digest == fixture.assisted.evidence_universe_digest
    assert fixture.baseline.budget_digest == fixture.assisted.budget_digest
    assert fixture.baseline.cost.attempts == fixture.assisted.cost.attempts == 2
    assert fixture.assisted.cost.checks == 2
