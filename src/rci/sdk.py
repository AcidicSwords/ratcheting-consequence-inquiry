"""Small offline-first SDK over the event ledger.

The SDK owns clocks and deterministic identities at the effect boundary; reducers remain
pure. Manual answers travel through the same request/attempt/raw/decode/accept protocol
as other external returns and remain provisional L0 claims.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from rci.backlog.models import G1_APPLICABLE_EFFECT_KINDS, BacklogEffect
from rci.claims.models import (
    BoundArgument,
    Claim,
    Obligation,
    ObligationDisposition,
    ObligationKind,
    ObligationStatus,
    Provenance,
    Scope,
)
from rci.core.commands import (
    AcceptEffectResult,
    AdmitClaim,
    DomainCommand,
    LinkReacquisitionInquiry,
    OpenObligation,
    PlanEffectAttempt,
    RecordAttemptOutcome,
    RecordBacklogEffect,
    RecordConsolidationCandidate,
    RecordConsolidationCheckpoint,
    RecordDecodeOutcome,
    RecordLearnedProbeCandidate,
    RecordMemoryPatchCandidate,
    RecordObligationDisposition,
    RecordProbeAdmissionDecision,
    RecordProbeEvaluation,
    RecordReconsolidationLink,
    RecordRecoveryComparison,
    RecordRecoveryObservation,
    RecordRepresentationGap,
    RecordSemanticFieldEvaluation,
    RecordStepPlan,
    RegisterRetentionPackage,
    RequestEffect,
    RequestReacquisition,
    RunRetrieval,
    StartEffectAttempt,
    StartInquiry,
)
from rci.core.effects import (
    Decoded,
    EffectAttemptPlan,
    EffectRequest,
    ExternalReturn,
    ReturnedOutcome,
    RouteSnapshot,
    SuccessResult,
)
from rci.core.events import DomainEvent, InquiryStarted
from rci.core.model import ArtifactRef, CapturedPayload, InquiryContext
from rci.core.serialization import canonical_json_bytes, sha256_digest
from rci.core.state import InquiryState
from rci.core.transitions import decide, evolve
from rci.learning import (
    ConsolidationCandidate,
    ConsolidationCheckpoint,
    ConsolidationPolicy,
    LearnedProbeCandidate,
    MemoryPatchCandidate,
    ProbeAdmissionDecision,
    ProbeEvaluation,
    ReconsolidationLink,
    RepresentationGap,
    SemanticFieldEvaluation,
    SemanticFieldPolicy,
    derive_conservative_field,
    evaluate_conservative_field,
    select_consolidation_checkpoint,
    semantic_field_overflow_residual,
)
from rci.memory import (
    STRUCTURAL_EXACT_V1,
    MemoryOwner,
    OwnedMemoryRef,
    OwnedRecordType,
    ReacquisitionChildManifest,
    ReacquisitionInquiryLink,
    ReacquisitionRequest,
    RecoveryBranch,
    RecoveryComparison,
    RecoveryFrontier,
    RecoveryObservation,
    RetentionRegistration,
    RetrievalQuery,
    RetrievalResult,
    compare_recovery_frontiers,
    derive_recovery_frontier,
    structural_index_fingerprint,
)
from rci.orchestration import (
    AttemptKey,
    ObligationEntry,
    PlanStatus,
    StepPlan,
    plan_next,
)
from rci.persistence import ArtifactStore, SQLiteEventStore
from rci.questions import bind_answer, get_contract, render_question
from rci.questions.catalog import CATALOG_V0_3, CATALOG_V0_4, CORE_V1
from rci.questions.models import QuestionContract
from rci.warrant import CheckReference

Clock = Callable[[], datetime]


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class AnswerSubmissionError(RuntimeError):
    """A submitted answer cannot lawfully attach to the current inquiry state."""


class StepResult(_FrozenModel):
    inquiry_id: str
    status: Literal["needs_input", "satisfied", "active", "unknown"]
    sequence: int
    request_id: str | None = None
    prompt: str | None = None


class _QuestionEnvelope(_FrozenModel):
    schema_version: Literal[1] = 1
    obligation_id: str
    obligation_fingerprint: str
    contract_id: str
    contract_version: str
    catalog_manifest_digest: str
    contract_artifact: ArtifactRef
    rendered_question: str


_CONTRACT_BY_OBLIGATION_KIND: dict[ObligationKind, str] = {
    ObligationKind.CHARACTERIZE: "obligation-characterization",
    ObligationKind.SAME_CLASS_VARIATION: "same-class-variation",
    ObligationKind.MINIMAL_BOUNDARY_CROSSING: "minimal-boundary-crossing",
    ObligationKind.PROPOSE_FACTOR: "factor-proposal",
    ObligationKind.NECESSITY_COUNTEREXAMPLE: "necessity-counterexample",
    ObligationKind.SUFFICIENCY_COUNTEREXAMPLE: "sufficiency-counterexample",
    ObligationKind.LOCALIZE_CONFLICT: "conflict-localization",
    ObligationKind.CHARACTERIZE_RESIDUAL: "residual-characterization",
}


def _stable_id(prefix: str, *parts: str) -> str:
    digest = sha256("\x00".join(parts).encode()).hexdigest()[:24]
    return f"{prefix}_{digest}"


def _utc_now() -> datetime:
    return datetime.now(UTC)


class RCI:
    """Repository-local SDK with no network or provider dependency."""

    def __init__(self, root: str | Path = ".", *, clock: Clock = _utc_now) -> None:
        self.root = Path(root).resolve()
        runtime = self.root / ".rci"
        self.artifacts = ArtifactStore(runtime / "artifacts")
        self.events = SQLiteEventStore(
            runtime / "state.sqlite3",
            artifact_store=self.artifacts,
        )
        self.clock = clock

    def _apply_batch(
        self,
        inquiry_id: str,
        commands: Iterable[DomainCommand],
    ) -> InquiryState:
        state = self.events.rebuild_state(inquiry_id)
        initial_sequence = state.sequence
        pending: list[DomainEvent] = []
        for command in commands:
            new_events = decide(state, command)
            pending.extend(new_events)
            for event in new_events:
                state = evolve(state, event)
        if pending:
            self.events.append(inquiry_id, initial_sequence, pending)
        return state

    def dispatch(self, command: DomainCommand) -> InquiryState:
        """Apply one validated domain command through the pure reducer and ledger."""

        return self._apply_batch(command.inquiry_id, (command,))

    def dispatch_batch(
        self,
        inquiry_id: str,
        commands: Iterable[DomainCommand],
    ) -> InquiryState:
        """Atomically append the events decided from an ordered command batch."""

        return self._apply_batch(inquiry_id, commands)

    @staticmethod
    def _scope_from_context(context: InquiryContext) -> Scope:
        scope = Scope(
            id=context.scope_id,
            binding_revision=context.binding_revision,
            assumption_ids=context.assumption_ids,
            applicability_guard_id=context.guard_condition_id,
            finite_universe_hash=context.finite_universe_hash,
            closed_world=context.closed_world,
        )
        if scope.fingerprint != context.scope_fingerprint:
            raise ValueError("inquiry context scope fingerprint does not match its exact scope")
        return scope

    @staticmethod
    def default_context() -> InquiryContext:
        scope = Scope(id="default-scope", binding_revision="binding-v1")
        return InquiryContext(
            binding_revision=scope.binding_revision,
            carrier_schema_ids=("rci.opaque-carrier.v1",),
            relation_schema_ids=("rci.consequence-relation.v1",),
            consequence_profile_id="local-inquiry-consequences-v1",
            protected_horizon_id="inquiry-local-v1",
            admissible_operation_ids=("question.ask-v1", "answer.bind-l0-v1"),
            discharge_mechanism_ids=("manual-v1", "finite-exhaustive-v1"),
            scope_id=scope.id,
            scope_fingerprint=scope.fingerprint,
            assumption_ids=scope.assumption_ids,
            guard_condition_id=None,
            guard_ast=None,
            finite_universe_hash=scope.finite_universe_hash,
            closed_world=scope.closed_world,
            catalog_manifest_digest=CATALOG_V0_4.digest,
            scheduler_policy_version="deterministic-scheduler-v1",
            warrant_policy_version="g1-warrant-v1",
            provenance_refs=("sdk-default-binding-v1",),
        )

    def _inquiry_manifest_artifact(self, context: InquiryContext) -> ArtifactRef:
        catalog = next(
            (
                item
                for item in (CATALOG_V0_3, CATALOG_V0_4)
                if item.digest == context.catalog_manifest_digest
            ),
            None,
        )
        if catalog is None:
            raise ValueError("inquiry context names an unsupported question catalog digest")
        catalog_ref = self.artifacts.put_bytes(
            canonical_json_bytes(catalog),
            media_type="application/vnd.rci.question-catalog+json",
            encoding="utf-8",
        )
        manifest = canonical_json_bytes(
            {
                "schema_version": 1,
                "context": context.model_dump(mode="json"),
                "question_catalog_digest": catalog.digest,
                "question_catalog_artifact": catalog_ref.model_dump(mode="json"),
            }
        )
        manifest_ref = self.artifacts.put_bytes(
            manifest,
            media_type="application/vnd.rci.inquiry-manifest+json",
            encoding="utf-8",
        )
        return manifest_ref

    def _start_with_manifest(
        self,
        inquiry_id: str,
        *,
        context: InquiryContext,
        manifest_ref: ArtifactRef,
    ) -> InquiryState:
        self._scope_from_context(context)
        command = StartInquiry(
            event_id=_stable_id("evt", inquiry_id, "start", manifest_ref.digest),
            inquiry_id=inquiry_id,
            occurred_at=self.clock(),
            manifest_artifact=manifest_ref,
            policy_version=context.warrant_policy_version,
            context=context,
        )
        scope = self._scope_from_context(context)
        initial_obligation = Obligation(
            id=_stable_id(
                "obl",
                inquiry_id,
                "characterize",
                scope.fingerprint,
                context.consequence_profile_id,
            ),
            kind=ObligationKind.CHARACTERIZE,
            carrier_id=context.consequence_profile_id,
            args=(
                BoundArgument(
                    name="carrier",
                    value=context.consequence_profile_id,
                ),
            ),
            scope=scope,
            binding_revision=scope.binding_revision,
            priority_vector=(100,),
        )
        open_initial = OpenObligation(
            event_id=_stable_id("evt", initial_obligation.id, "opened"),
            inquiry_id=inquiry_id,
            occurred_at=command.occurred_at,
            obligation=initial_obligation,
        )
        return self._apply_batch(inquiry_id, (command, open_initial))

    def start(
        self,
        inquiry_id: str,
        *,
        context: InquiryContext | None = None,
    ) -> InquiryState:
        selected_context = context or self.default_context()
        return self._start_with_manifest(
            inquiry_id,
            context=selected_context,
            manifest_ref=self._inquiry_manifest_artifact(selected_context),
        )

    def inspect(self, inquiry_id: str) -> InquiryState:
        return self.events.rebuild_state(inquiry_id)

    def resume(self, inquiry_id: str) -> InquiryState:
        return self.inspect(inquiry_id)

    def replay(self, inquiry_id: str) -> InquiryState:
        return self.events.rebuild_state(inquiry_id, use_snapshot=False)

    def export(self, inquiry_id: str) -> bytes:
        return self.events.export_stream(inquiry_id)

    @staticmethod
    def _contract_for_obligation(obligation: Obligation) -> QuestionContract | None:
        contract_id = _CONTRACT_BY_OBLIGATION_KIND.get(obligation.kind)
        if contract_id is None:
            return None
        contract = get_contract(contract_id)
        if contract.key not in CORE_V1.contract_keys:
            raise RuntimeError("only the admitted core-v1 profile may be scheduled")
        return contract

    @staticmethod
    def _carrier_text(obligation: Obligation) -> str:
        carrier = next(
            (argument.value for argument in obligation.args if argument.name == "carrier"),
            obligation.carrier_id,
        )
        return carrier if isinstance(carrier, str) else obligation.carrier_id

    def _question_envelope_for_request(self, request: EffectRequest) -> _QuestionEnvelope:
        data = self.artifacts.get_bytes(request.input_artifact)
        envelope = _QuestionEnvelope.model_validate_json(data)
        contract = QuestionContract.model_validate_json(
            self.artifacts.get_bytes(envelope.contract_artifact),
            strict=True,
        )
        if contract.id != envelope.contract_id or contract.version != envelope.contract_version:
            raise RuntimeError("question envelope contract artifact does not match its identity")
        return envelope

    def _matches_last_accepted_answer(
        self,
        state: InquiryState,
        answer: str | bytes | None,
    ) -> bool:
        accepted = next(
            (
                item
                for item in reversed(state.effect_requests)
                if item.request.effect_kind == "semantic.manual_answer"
                and item.accepted_result is not None
            ),
            None,
        )
        if accepted is None or accepted.accepted_result is None:
            return False
        claim = Claim.model_validate_json(
            self.artifacts.get_bytes(accepted.accepted_result.semantic_artifact),
            strict=True,
        )
        if answer is None:
            return claim.payload is None
        if isinstance(answer, str):
            return claim.payload == answer
        return (
            isinstance(claim.payload, ArtifactRef)
            and claim.payload.digest == sha256(answer).hexdigest()
            and claim.payload.size == len(answer)
        )

    def _scheduler_entries(self, state: InquiryState) -> tuple[ObligationEntry, ...]:
        entries: list[ObligationEntry] = []
        for creation_sequence, obligation in enumerate(state.obligations, start=1):
            contract = self._contract_for_obligation(obligation)
            if contract is None:
                continue
            current_status = state.current_obligation_status(obligation.id)
            if current_status is None:  # pragma: no cover - aggregate invariant
                raise RuntimeError("scheduler encountered an unowned obligation")
            current = obligation.model_copy(update={"status": current_status})
            key = AttemptKey(
                obligation_fingerprint=obligation.fingerprint,
                contract_id=contract.id,
                contract_version=contract.version,
                binding_revision=obligation.binding_revision,
            )
            entries.append(
                ObligationEntry(
                    obligation=current,
                    attempt_key=key,
                    creation_sequence=creation_sequence,
                    dependency_depth=len(obligation.parent_obligation_ids),
                )
            )
        return tuple(entries)

    def _attempt_counts(self, state: InquiryState) -> Counter[AttemptKey]:
        counts: Counter[AttemptKey] = Counter()
        for request_state in state.effect_requests:
            request = request_state.request
            if request.effect_kind != "semantic.manual_answer":
                continue
            envelope = self._question_envelope_for_request(request)
            if (
                state.context is None
                or envelope.catalog_manifest_digest != state.context.catalog_manifest_digest
            ):
                raise RuntimeError("question request catalog differs from the inquiry context")
            key = AttemptKey(
                obligation_fingerprint=envelope.obligation_fingerprint,
                contract_id=envelope.contract_id,
                contract_version=envelope.contract_version,
                binding_revision=(
                    state.context.binding_revision
                    if state.context is not None
                    else "missing-binding"
                ),
            )
            counts[key] += len(request_state.attempts)
        return counts

    def _schedule(self, state: InquiryState) -> StepPlan:
        entries = self._scheduler_entries(state)
        completed = frozenset(
            obligation.id
            for obligation in state.obligations
            if state.current_obligation_status(obligation.id) is ObligationStatus.SATISFIED
        )
        if state.context is None:  # pragma: no cover - active-state invariant
            raise RuntimeError("active inquiry is missing its pinned context")
        return plan_next(
            entries,
            completed_obligation_ids=completed,
            attempt_counts=self._attempt_counts(state),
            # The constitutional budget counts every reducer transition, not only
            # semantic requests. The stream sequence is the replay-stable count,
            # and a ready manual step atomically records plan/request/plan/start.
            steps_used=state.sequence,
            ready_event_cost=4,
            policy_version=state.context.scheduler_policy_version,
        )

    def _manual_request(
        self,
        inquiry_id: str,
        *,
        step_plan: StepPlan,
        obligation: Obligation,
        contract: QuestionContract,
    ) -> tuple[EffectRequest, EffectAttemptPlan, str]:
        rendered = render_question(
            contract,
            {"carrier": self._carrier_text(obligation)},
        )
        contract_ref = self.artifacts.put_bytes(
            canonical_json_bytes(contract),
            media_type="application/vnd.rci.question-contract+json",
            encoding="utf-8",
        )
        inquiry_context = self.inspect(inquiry_id).context
        if inquiry_context is None:
            raise RuntimeError("manual request requires a started inquiry context")
        envelope = _QuestionEnvelope(
            obligation_id=obligation.id,
            obligation_fingerprint=obligation.fingerprint,
            contract_id=contract.id,
            contract_version=contract.version,
            catalog_manifest_digest=inquiry_context.catalog_manifest_digest,
            contract_artifact=contract_ref,
            rendered_question=rendered,
        )
        input_ref = self.artifacts.put_bytes(
            canonical_json_bytes(envelope),
            media_type="application/vnd.rci.question-invocation+json",
            encoding="utf-8",
        )
        route_definition = self.artifacts.put_bytes(
            b'{"adapter":"manual","version":"1.0.0"}',
            media_type="application/json",
            encoding="utf-8",
        )
        request_id = _stable_id("req", inquiry_id, step_plan.id)
        request = EffectRequest(
            id=request_id,
            step_plan_id=step_plan.id,
            effect_kind="semantic.manual_answer",
            adapter_id="manual",
            input_artifact=input_ref,
            timeout_seconds=60,
        )
        environment_ref = self.artifacts.put_bytes(
            canonical_json_bytes(
                {
                    "adapter": "manual",
                    "execution": "in-process",
                    "runtime": "rci",
                    "secrets_present": False,
                    "version": "1.0.0",
                }
            ),
            media_type="application/vnd.rci.execution-environment+json",
            encoding="utf-8",
        )
        route = RouteSnapshot(
            id=_stable_id("route", request_id, "manual"),
            definition_id="manual-route",
            definition_version="1.0.0",
            definition_artifact=route_definition,
            backend_id="human",
            adapter_id="manual",
            adapter_version="1.0.0",
            endpoint_or_channel="local-cli",
            transport="in-process",
            execution_environment_artifact=environment_ref,
            request_or_action_digest=sha256_digest(canonical_json_bytes(request)),
        )
        plan = EffectAttemptPlan(
            id=_stable_id("attempt", request_id, "1"),
            request_id=request_id,
            route=route,
        )
        return request, plan, rendered

    def step(self, inquiry_id: str) -> StepResult:
        state = self.inspect(inquiry_id)
        pending_manual = next(
            (
                request_state
                for request_state in state.effect_requests
                if request_state.request.effect_kind == "semantic.manual_answer"
                and request_state.accepted_decoded_outcome_id is None
                and any(
                    attempt.started and attempt.outcome is None
                    for attempt in request_state.attempts
                )
            ),
            None,
        )
        if pending_manual is not None:
            envelope = self._question_envelope_for_request(pending_manual.request)
            return StepResult(
                inquiry_id=inquiry_id,
                status="needs_input",
                sequence=state.sequence,
                request_id=pending_manual.request.id,
                prompt=envelope.rendered_question,
            )
        unresolved_return = any(
            request_state.request.effect_kind == "semantic.manual_answer"
            and request_state.accepted_decoded_outcome_id is None
            and any(
                attempt.outcome is not None and attempt.outcome.kind == "returned"
                for attempt in request_state.attempts
            )
            for request_state in state.effect_requests
        )
        if unresolved_return:
            return StepResult(
                inquiry_id=inquiry_id,
                status="active",
                sequence=state.sequence,
            )

        step_plan = self._schedule(state)
        if step_plan.status is PlanStatus.SATISFIED:
            unsupported_open = any(
                state.current_obligation_status(obligation.id) is ObligationStatus.OPEN
                and self._contract_for_obligation(obligation) is None
                for obligation in state.obligations
            )
            return StepResult(
                inquiry_id=inquiry_id,
                status="unknown" if unsupported_open else "satisfied",
                sequence=state.sequence,
            )
        if step_plan.status is PlanStatus.UNKNOWN:
            return StepResult(
                inquiry_id=inquiry_id,
                status="unknown",
                sequence=state.sequence,
            )
        if step_plan.selected_obligation_id is None:  # pragma: no cover - plan invariant
            raise RuntimeError("ready step plan omitted its selected obligation")
        obligation = state.obligation_by_id(step_plan.selected_obligation_id)
        if obligation is None:  # pragma: no cover - aggregate invariant
            raise RuntimeError("step plan selected an unknown obligation")
        contract = self._contract_for_obligation(obligation)
        if contract is None:  # pragma: no cover - scheduler projection invariant
            raise RuntimeError("step plan selected an inactive contract")
        request, plan, rendered = self._manual_request(
            inquiry_id,
            step_plan=step_plan,
            obligation=obligation,
            contract=contract,
        )
        now = self.clock()
        state = self._apply_batch(
            inquiry_id,
            (
                RecordStepPlan(
                    event_id=_stable_id("evt", step_plan.id, "recorded"),
                    inquiry_id=inquiry_id,
                    occurred_at=now,
                    plan=step_plan,
                ),
                RequestEffect(
                    event_id=_stable_id("evt", request.id, "requested"),
                    inquiry_id=inquiry_id,
                    occurred_at=now,
                    request=request,
                ),
                PlanEffectAttempt(
                    event_id=_stable_id("evt", plan.id, "planned"),
                    inquiry_id=inquiry_id,
                    occurred_at=now,
                    plan=plan,
                ),
                StartEffectAttempt(
                    event_id=_stable_id("evt", plan.id, "started"),
                    inquiry_id=inquiry_id,
                    occurred_at=now,
                    attempt_id=plan.id,
                ),
            ),
        )
        return StepResult(
            inquiry_id=inquiry_id,
            status="needs_input",
            sequence=state.sequence,
            request_id=request.id,
            prompt=rendered,
        )

    def run(self, inquiry_id: str, *, max_steps: int = 100) -> StepResult:
        if max_steps < 1 or max_steps > 100:
            raise ValueError("max_steps must be between 1 and the constitutional limit of 100")
        previous_sequence = -1
        for _ in range(max_steps):
            result = self.step(inquiry_id)
            if result.status != "active":
                return result
            if result.sequence <= previous_sequence:
                return result
            previous_sequence = result.sequence
        state = self.inspect(inquiry_id)
        return StepResult(
            inquiry_id=inquiry_id,
            status="unknown",
            sequence=state.sequence,
        )

    def submit_answer(self, inquiry_id: str, answer: str | bytes | None) -> InquiryState:
        state = self.inspect(inquiry_id)
        pending = next(
            (
                item
                for item in state.effect_requests
                if item.request.effect_kind == "semantic.manual_answer"
                and item.accepted_decoded_outcome_id is None
                and any(attempt.started and attempt.outcome is None for attempt in item.attempts)
            ),
            None,
        )
        if pending is None:
            step_result = self.step(inquiry_id)
            state = self.inspect(inquiry_id)
            if step_result.status != "needs_input":
                if self._matches_last_accepted_answer(state, answer):
                    return state
                raise AnswerSubmissionError(
                    f"inquiry has no pending manual answer request ({step_result.status})"
                )
            pending = next(
                (
                    item
                    for item in state.effect_requests
                    if item.request.effect_kind == "semantic.manual_answer"
                    and item.accepted_decoded_outcome_id is None
                    and any(
                        attempt.started and attempt.outcome is None for attempt in item.attempts
                    )
                ),
                None,
            )
            if pending is None:  # pragma: no cover - step/result invariant
                raise AnswerSubmissionError("step reported input without a pending request")
        if not pending.attempts:
            raise RuntimeError("manual request has no persisted attempt plan")
        attempt = pending.attempts[0].plan
        now = self.clock()
        raw_ref = None
        if answer is not None:
            data = answer if isinstance(answer, bytes) else answer.encode()
            raw_ref = self.artifacts.put_bytes(
                data,
                media_type=(
                    "application/octet-stream" if isinstance(answer, bytes) else "text/plain"
                ),
                encoding="binary" if isinstance(answer, bytes) else "utf-8",
            )
        captured = (
            CapturedPayload(kind="null")
            if raw_ref is None
            else CapturedPayload(kind="bytes", artifact=raw_ref)
        )
        external_return = ExternalReturn(
            id=_stable_id("return", pending.request.id, captured.model_dump_json()),
            attempt_id=attempt.id,
            route_id=attempt.route.id,
            source_id="manual-user",
            capture_boundary="manual-answer-submission",
            capture_encoding=(
                "native-null"
                if answer is None
                else ("binary" if isinstance(answer, bytes) else "utf-8")
            ),
            captured_at=now,
            raw_payload=captured,
        )
        inert_answer = raw_ref if isinstance(answer, bytes) else answer
        if state.context is None:  # pragma: no cover - active-state invariant
            raise RuntimeError("active inquiry is missing its pinned context")
        envelope = self._question_envelope_for_request(pending.request)
        if envelope.catalog_manifest_digest != state.context.catalog_manifest_digest:
            raise RuntimeError("manual request catalog differs from the inquiry context")
        obligation = state.obligation_by_id(envelope.obligation_id)
        if obligation is None or obligation.fingerprint != envelope.obligation_fingerprint:
            raise RuntimeError("manual request does not reference its exact obligation")
        recorded_contract = QuestionContract.model_validate_json(
            self.artifacts.get_bytes(envelope.contract_artifact),
            strict=True,
        )
        contract = recorded_contract
        claim = bind_answer(
            contract,
            answer=inert_answer,
            bound_args=obligation.args,
            scope=self._scope_from_context(state.context),
            provenance=Provenance(kind="manual_answer", source_id=external_return.id),
        )
        semantic_ref = self.artifacts.put_bytes(
            claim.model_dump_json().encode(),
            media_type="application/vnd.rci.claim+json",
            encoding="utf-8",
        )
        decoded = Decoded(
            id=_stable_id("decode", external_return.id, semantic_ref.digest),
            external_return_id=external_return.id,
            decoder_id="l0-claim-binder",
            decoder_version="1.0.0",
            result=SuccessResult(
                id=_stable_id("result", semantic_ref.digest),
                semantic_artifact=semantic_ref,
                operation_id="l0_claim",
            ),
        )
        return self._apply_batch(
            inquiry_id,
            (
                RecordAttemptOutcome(
                    event_id=_stable_id("evt", external_return.id, "captured"),
                    inquiry_id=inquiry_id,
                    occurred_at=now,
                    request_id=pending.request.id,
                    outcome=ReturnedOutcome(
                        attempt_id=attempt.id,
                        route_id=attempt.route.id,
                        external_return=external_return,
                    ),
                ),
                RecordDecodeOutcome(
                    event_id=_stable_id("evt", decoded.id, "decoded"),
                    inquiry_id=inquiry_id,
                    occurred_at=now,
                    request_id=pending.request.id,
                    outcome=decoded,
                ),
                AcceptEffectResult(
                    event_id=_stable_id("evt", decoded.id, "accepted"),
                    inquiry_id=inquiry_id,
                    occurred_at=now,
                    request_id=pending.request.id,
                    decoded_outcome_id=decoded.id,
                ),
                AdmitClaim(
                    event_id=_stable_id("evt", claim.id, "admitted"),
                    inquiry_id=inquiry_id,
                    occurred_at=now,
                    claim=claim,
                ),
                RecordObligationDisposition(
                    event_id=_stable_id("evt", obligation.id, decoded.id, "satisfied"),
                    inquiry_id=inquiry_id,
                    occurred_at=now,
                    disposition=ObligationDisposition(
                        id=_stable_id("disp", obligation.id, decoded.id, "satisfied"),
                        obligation_id=obligation.id,
                        status=ObligationStatus.SATISFIED,
                        reason="accepted answer bound as a provisional L0 claim",
                        evidence_refs=(decoded.id,),
                    ),
                ),
            ),
        )

    def consolidation_checkpoint(
        self,
        inquiry_id: str,
        *,
        checkpoint_id: str,
        policy: ConsolidationPolicy | None = None,
    ) -> ConsolidationCheckpoint:
        """Select and persist the exact deterministic consolidation source prefix."""

        state = self.inspect(inquiry_id)
        if state.context is None:
            raise RuntimeError("consolidation requires a started inquiry")
        selected_policy = policy or ConsolidationPolicy()
        checkpoint = select_consolidation_checkpoint(
            checkpoint_id=checkpoint_id,
            policy=selected_policy,
            source_sequence=state.sequence,
            scope_fingerprint=state.context.scope_fingerprint,
            binding_revision=state.context.binding_revision,
            protected_horizon_id=state.context.protected_horizon_id,
            probe_observations=state.probe_observations,
            claims=state.claims,
            conflicts=state.conflicts,
            mismatches=state.mismatches,
            accepted_counterexample_requests={
                item.request.id: item for item in state.effect_requests
            },
        )
        self.dispatch(
            RecordConsolidationCheckpoint(
                event_id=_stable_id("evt", inquiry_id, checkpoint.id, "consolidated"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                checkpoint=checkpoint,
            )
        )
        return checkpoint

    def record_consolidation_candidate(
        self, inquiry_id: str, candidate: ConsolidationCandidate
    ) -> InquiryState:
        return self.dispatch(
            RecordConsolidationCandidate(
                event_id=_stable_id("evt", inquiry_id, candidate.id, "candidate"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                candidate=candidate,
            )
        )

    def propose_consolidation(
        self,
        inquiry_id: str,
        *,
        claim: Claim,
        challenge_obligations: tuple[Obligation, ...],
        candidate: ConsolidationCandidate,
    ) -> InquiryState:
        """Atomically create only an ordinary claim, attacks, and a candidate boundary."""

        now = self.clock()
        commands: list[DomainCommand] = [
            AdmitClaim(
                event_id=_stable_id("evt", inquiry_id, claim.id, "consolidation-claim"),
                inquiry_id=inquiry_id,
                occurred_at=now,
                claim=claim,
            )
        ]
        commands.extend(
            OpenObligation(
                event_id=_stable_id("evt", inquiry_id, item.id, "consolidation-attack"),
                inquiry_id=inquiry_id,
                occurred_at=now,
                obligation=item,
            )
            for item in challenge_obligations
        )
        commands.append(
            RecordConsolidationCandidate(
                event_id=_stable_id("evt", inquiry_id, candidate.id, "candidate"),
                inquiry_id=inquiry_id,
                occurred_at=now,
                candidate=candidate,
            )
        )
        return self.dispatch_batch(inquiry_id, commands)

    def record_memory_patch(self, inquiry_id: str, candidate: MemoryPatchCandidate) -> InquiryState:
        return self.dispatch(
            RecordMemoryPatchCandidate(
                event_id=_stable_id("evt", inquiry_id, candidate.id, "memory-patch"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                candidate=candidate,
            )
        )

    def record_reconsolidation_link(
        self, inquiry_id: str, link: ReconsolidationLink
    ) -> InquiryState:
        return self.dispatch(
            RecordReconsolidationLink(
                event_id=_stable_id("evt", inquiry_id, link.id, "reconsolidated"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                link=link,
            )
        )

    def evaluate_semantic_field(
        self,
        inquiry_id: str,
        *,
        evaluation_id: str,
        probe_fingerprint: str,
        safety_structure_ids: tuple[str, ...] = (),
        exception_structure_ids: tuple[str, ...] = (),
        dependency_structure_ids: tuple[str, ...] = (),
        retrieval_structure_ids: tuple[str, ...] = (),
        policy: SemanticFieldPolicy | None = None,
    ) -> SemanticFieldEvaluation:
        """Derive and persist one bounded conservative field diagnostic."""

        state = self.inspect(inquiry_id)
        probe = next(
            (item for item in state.admitted_probes if item.fingerprint == probe_fingerprint),
            None,
        )
        if probe is None:
            raise ValueError("semantic-field evaluation requires an admitted probe")
        selected_policy = policy or SemanticFieldPolicy()
        field, required, overflow, source_index = derive_conservative_field(
            probe_identity=probe,
            source_sequence=state.sequence,
            policy=selected_policy,
            safety_structure_ids=safety_structure_ids,
            exception_structure_ids=exception_structure_ids,
            dependency_structure_ids=dependency_structure_ids,
            retrieval_structure_ids=retrieval_structure_ids,
        )
        evaluation = evaluate_conservative_field(
            evaluation_id=evaluation_id,
            field=field,
            policy=selected_policy,
            source_sequence=state.sequence,
            source_index_fingerprint=source_index,
            probe_fingerprint=probe_fingerprint,
            required_structure_ids=required,
            overflow_structure_ids=overflow,
        )
        if state.context is None:
            raise RuntimeError("semantic-field evaluation requires inquiry context")
        overflow_residual = semantic_field_overflow_residual(
            evaluation,
            self._scope_from_context(state.context),
        )
        self.dispatch(
            RecordSemanticFieldEvaluation(
                event_id=_stable_id("evt", inquiry_id, evaluation.id, "field-evaluated"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                evaluation=evaluation,
                overflow_residual=overflow_residual,
            )
        )
        return evaluation

    def record_representation_gap(self, inquiry_id: str, gap: RepresentationGap) -> InquiryState:
        return self.dispatch(
            RecordRepresentationGap(
                event_id=_stable_id("evt", inquiry_id, gap.id, "gap"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                gap=gap,
            )
        )

    def record_learned_probe_candidate(
        self, inquiry_id: str, candidate: LearnedProbeCandidate
    ) -> InquiryState:
        return self.dispatch(
            RecordLearnedProbeCandidate(
                event_id=_stable_id("evt", inquiry_id, candidate.id, "probe-candidate"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                candidate=candidate,
            )
        )

    def record_probe_evaluation(self, inquiry_id: str, evaluation: ProbeEvaluation) -> InquiryState:
        return self.dispatch(
            RecordProbeEvaluation(
                event_id=_stable_id("evt", inquiry_id, evaluation.id, "probe-evaluated"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                evaluation=evaluation,
            )
        )

    def record_probe_admission(
        self, inquiry_id: str, decision: ProbeAdmissionDecision
    ) -> InquiryState:
        return self.dispatch(
            RecordProbeAdmissionDecision(
                event_id=_stable_id("evt", inquiry_id, decision.id, "probe-admission"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                decision=decision,
            )
        )

    def register_retention_package(
        self,
        inquiry_id: str,
        registration: RetentionRegistration,
    ) -> InquiryState:
        """Register one atomic, provisional, non-compressive retention bundle."""

        return self.dispatch(
            RegisterRetentionPackage(
                event_id=_stable_id(
                    "evt",
                    inquiry_id,
                    registration.package.id,
                    registration.package.fingerprint,
                    "registered",
                ),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                registration=registration,
            )
        )

    def retrieve(
        self,
        inquiry_id: str,
        *,
        query_id: str,
        result_id: str,
        owners: tuple[MemoryOwner, ...] = (),
        record_types: tuple[OwnedRecordType, ...] = (),
        reference_selectors: tuple[OwnedMemoryRef, ...] = (),
        cue_ids: tuple[str, ...] = (),
        tag_ids: tuple[str, ...] = (),
        limit: int = 20,
    ) -> RetrievalResult:
        """Run one exact structural query over the current committed aggregate prefix."""

        state = self.inspect(inquiry_id)
        if state.context is None:
            raise RuntimeError("retrieval requires a started inquiry context")
        query = RetrievalQuery(
            id=query_id,
            policy_id=STRUCTURAL_EXACT_V1.id,
            policy_version=STRUCTURAL_EXACT_V1.version,
            scope_fingerprint=state.context.scope_fingerprint,
            binding_revision=state.context.binding_revision,
            protected_horizon_id=state.context.protected_horizon_id,
            source_sequence=state.sequence,
            source_index_fingerprint=structural_index_fingerprint(
                state.retention_packages,
                state.owned_memory_fingerprints,
            ),
            owners=owners,
            record_types=record_types,
            reference_selectors=reference_selectors,
            cue_ids=tuple(sorted(set(cue_ids))),
            tag_ids=tuple(sorted(set(tag_ids))),
            limit=limit,
        )
        updated = self.dispatch(
            RunRetrieval(
                event_id=_stable_id("evt", inquiry_id, query.id, result_id, "retrieved"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                result_id=result_id,
                query=query,
            )
        )
        result = next(item for item in updated.retrieval_results if item.id == result_id)
        return result

    def request_reacquisition(
        self,
        parent_inquiry_id: str,
        *,
        request_id: str,
        child_inquiry_id: str,
        branch: RecoveryBranch,
        recovery_protocol_id: str,
        retention_package_id: str | None = None,
        scaffold_id: str | None = None,
    ) -> InquiryState:
        """Persist the first saga prefix without starting or linking the child."""

        parent = self.inspect(parent_inquiry_id)
        if parent.context is None:
            raise RuntimeError("reacquisition requires a started parent inquiry")
        protocol = next(
            (item for item in parent.recovery_protocols if item.id == recovery_protocol_id),
            None,
        )
        if protocol is None:
            raise ValueError("reacquisition protocol is not owned by the parent inquiry")
        context_digest = sha256_digest(canonical_json_bytes(parent.context))
        base_manifest_ref = self._inquiry_manifest_artifact(parent.context)
        child_manifest = ReacquisitionChildManifest(
            parent_inquiry_id=parent_inquiry_id,
            request_id=request_id,
            child_inquiry_id=child_inquiry_id,
            pins=protocol.pins,
            context_digest=context_digest,
            policy_version=parent.context.warrant_policy_version,
            inquiry_manifest_artifact=base_manifest_ref,
        )
        child_manifest_ref = self.artifacts.put_bytes(
            canonical_json_bytes(child_manifest),
            media_type="application/vnd.rci.reacquisition-child-manifest+json",
            encoding="utf-8",
        )
        request = ReacquisitionRequest(
            id=request_id,
            parent_inquiry_id=parent_inquiry_id,
            child_inquiry_id=child_inquiry_id,
            branch=branch,
            pins=protocol.pins,
            child_manifest_artifact=child_manifest_ref,
            child_inquiry_manifest_artifact=base_manifest_ref,
            child_context_digest=context_digest,
            child_policy_version=parent.context.warrant_policy_version,
            retention_package_id=retention_package_id,
            scaffold_id=scaffold_id,
        )
        return self.dispatch(
            RequestReacquisition(
                event_id=_stable_id("evt", parent_inquiry_id, request.id, "requested"),
                inquiry_id=parent_inquiry_id,
                occurred_at=self.clock(),
                request=request,
            )
        )

    def start_reacquisition_child(
        self,
        parent_inquiry_id: str,
        request_id: str,
    ) -> InquiryState:
        """Create or idempotently resume the exact child stream pinned by a request."""

        parent = self.inspect(parent_inquiry_id)
        request = next(
            (item for item in parent.reacquisition_requests if item.id == request_id),
            None,
        )
        if request is None or parent.context is None:
            raise ValueError("reacquisition request is not owned by a started parent")
        manifest = ReacquisitionChildManifest.model_validate_json(
            self.artifacts.get_bytes(request.child_manifest_artifact),
            strict=True,
        )
        if manifest.context_digest != sha256_digest(canonical_json_bytes(parent.context)):
            raise ValueError("reacquisition manifest context differs from its parent")
        return self._start_with_manifest(
            request.child_inquiry_id,
            context=parent.context,
            manifest_ref=request.child_manifest_artifact,
        )

    def link_reacquisition_inquiry(
        self,
        parent_inquiry_id: str,
        request_id: str,
    ) -> InquiryState:
        """Persist the final link only after verifying the actual child prefix."""

        parent = self.inspect(parent_inquiry_id)
        request = next(
            (item for item in parent.reacquisition_requests if item.id == request_id),
            None,
        )
        if request is None:
            raise ValueError("reacquisition request is not owned by the parent")
        if any(item.request_id == request_id for item in parent.reacquisition_inquiry_links):
            return parent
        child = self.events.load_stream(request.child_inquiry_id)
        if not child.events:
            raise ValueError("reacquisition child stream has not started")
        start_event = child.events[0]
        inquiry_started = start_event.event
        if not isinstance(inquiry_started, InquiryStarted):
            raise ValueError("reacquisition child stream does not begin with InquiryStarted")
        link = ReacquisitionInquiryLink(
            id=_stable_id("reacq-link", parent_inquiry_id, request.id),
            request_id=request.id,
            parent_inquiry_id=parent_inquiry_id,
            child_inquiry_id=request.child_inquiry_id,
            child_start_event_id=inquiry_started.event_id,
            child_start_event_digest=start_event.event_digest,
            child_prefix_sequence=child.version,
            child_prefix_digest=self.events.stream_prefix_digest(request.child_inquiry_id),
            child_manifest_artifact=inquiry_started.manifest_artifact,
            child_context_digest=sha256_digest(canonical_json_bytes(inquiry_started.context)),
        )
        return self.dispatch(
            LinkReacquisitionInquiry(
                event_id=_stable_id("evt", parent_inquiry_id, link.id, "linked"),
                inquiry_id=parent_inquiry_id,
                occurred_at=self.clock(),
                link=link,
            )
        )

    def start_reacquisition(
        self,
        parent_inquiry_id: str,
        *,
        request_id: str,
        child_inquiry_id: str,
        branch: RecoveryBranch,
        recovery_protocol_id: str,
        retention_package_id: str | None = None,
        scaffold_id: str | None = None,
    ) -> InquiryState:
        """Resume the request-to-child-to-link saga through every durable prefix."""

        self.request_reacquisition(
            parent_inquiry_id,
            request_id=request_id,
            child_inquiry_id=child_inquiry_id,
            branch=branch,
            recovery_protocol_id=recovery_protocol_id,
            retention_package_id=retention_package_id,
            scaffold_id=scaffold_id,
        )
        self.start_reacquisition_child(parent_inquiry_id, request_id)
        return self.link_reacquisition_inquiry(parent_inquiry_id, request_id)

    def record_recovery_observation(
        self,
        parent_inquiry_id: str,
        observation: RecoveryObservation,
    ) -> InquiryState:
        """Record independently checked child recovery measurements."""

        return self.dispatch(
            RecordRecoveryObservation(
                event_id=_stable_id("evt", parent_inquiry_id, observation.id, "observed"),
                inquiry_id=parent_inquiry_id,
                occurred_at=self.clock(),
                observation=observation,
            )
        )

    def recovery_frontier(
        self,
        parent_inquiry_id: str,
        *,
        branch: RecoveryBranch,
        observation_ids: tuple[str, ...],
    ) -> RecoveryFrontier:
        state = self.inspect(parent_inquiry_id)
        by_id = {item.id: item for item in state.recovery_observations}
        try:
            observations = tuple(by_id[identifier] for identifier in observation_ids)
        except KeyError as error:
            raise ValueError("recovery frontier references an unknown observation") from error
        if not observations:
            raise ValueError("recovery frontier requires at least one observation")
        return derive_recovery_frontier(
            branch=branch,
            pins=observations[0].pins,
            observations=observations,
        )

    def compare_recovery(
        self,
        parent_inquiry_id: str,
        *,
        comparison_id: str,
        baseline_observation_ids: tuple[str, ...],
        retained_observation_ids: tuple[str, ...],
        comparison_check: CheckReference,
    ) -> RecoveryComparison:
        comparison = self.compare_recovery_frontiers_for_check(
            parent_inquiry_id,
            comparison_id=comparison_id,
            baseline_observation_ids=baseline_observation_ids,
            retained_observation_ids=retained_observation_ids,
            comparison_check=comparison_check,
        )
        self.dispatch(
            RecordRecoveryComparison(
                event_id=_stable_id("evt", parent_inquiry_id, comparison.id, "compared"),
                inquiry_id=parent_inquiry_id,
                occurred_at=self.clock(),
                comparison=comparison,
            )
        )
        return comparison

    def compare_recovery_frontiers_for_check(
        self,
        parent_inquiry_id: str,
        *,
        comparison_id: str,
        baseline_observation_ids: tuple[str, ...],
        retained_observation_ids: tuple[str, ...],
        comparison_check: CheckReference,
    ) -> RecoveryComparison:
        """Build the exact provisional comparison that an external checker must bind."""

        baseline = self.recovery_frontier(
            parent_inquiry_id,
            branch=RecoveryBranch.BASELINE,
            observation_ids=baseline_observation_ids,
        )
        retained = self.recovery_frontier(
            parent_inquiry_id,
            branch=RecoveryBranch.RETAINED,
            observation_ids=retained_observation_ids,
        )
        comparison = compare_recovery_frontiers(
            comparison_id=comparison_id,
            baseline=baseline,
            retained=retained,
            comparison_check=comparison_check,
        )
        return comparison

    def append_local_effects(
        self,
        inquiry_id: str,
        effects: Iterable[BacklogEffect],
    ) -> InquiryState:
        """Atomically append governed local backlog events without external-effect fiction."""

        state = self.inspect(inquiry_id)
        commands: list[DomainCommand] = []
        now = self.clock()
        for effect in effects:
            if not isinstance(effect, BacklogEffect):
                raise TypeError("local effect append accepts BacklogEffect records only")
            if effect.kind not in G1_APPLICABLE_EFFECT_KINDS:
                raise PermissionError(f"backlog effect {effect.kind} is not applicable in G1")
            commands.append(
                RecordBacklogEffect(
                    event_id=_stable_id("evt", effect.id, "recorded"),
                    inquiry_id=inquiry_id,
                    occurred_at=now,
                    effect=effect,
                )
            )
        if not commands:
            return state
        return self._apply_batch(inquiry_id, commands)
