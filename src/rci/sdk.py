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

from pydantic import BaseModel, ConfigDict, ValidationError, model_validator

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
from rci.compression import (
    BindingCarrierManifest,
    CompressionApplication,
    CompressionContract,
    CompressionValidation,
    ExactCompressionLicense,
    PathResidue,
    RealizedHistoryDerivation,
    RecoveryLicense,
    RepresentationReopening,
    RepresentationSuccessorDecision,
    RetentionCapabilityLink,
)
from rci.core.commands import (
    AcceptEffectResult,
    AdmitClaim,
    DecideGoalAdmission,
    DecideMethodAdmission,
    DecideProjectSuccessor,
    DecideQuestionRepertoire,
    DecideRepresentationSuccessor,
    DomainCommand,
    GrantExactCompressionLicense,
    GrantRecoveryLicense,
    LinkReacquisitionInquiry,
    LinkRetentionCapability,
    OpenObligation,
    PlanEffectAttempt,
    RecordAttemptOutcome,
    RecordBacklogEffect,
    RecordCandidateEnvironment,
    RecordCapabilityFrontier,
    RecordCapabilityLimitation,
    RecordCapabilitySuccessorCandidate,
    RecordCompressionApplication,
    RecordCompressionValidation,
    RecordConsolidationCandidate,
    RecordConsolidationCheckpoint,
    RecordDecodeOutcome,
    RecordDevelopmentEvidence,
    RecordImplementationGoalCandidate,
    RecordIndependentReview,
    RecordLearnedProbeCandidate,
    RecordMemoryPatchCandidate,
    RecordMethodBindingCandidate,
    RecordObligationDisposition,
    RecordProbeAdmissionDecision,
    RecordProbeEvaluation,
    RecordProjectAnchor,
    RecordPromotionDecision,
    RecordQuestionContractCandidate,
    RecordRealizedHistoryDerivation,
    RecordReconsolidationLink,
    RecordRecoveryComparison,
    RecordRecoveryObservation,
    RecordRecursiveCycleCheckpoint,
    RecordRecursiveStopDisposition,
    RecordRepresentationGap,
    RecordSemanticFieldEvaluation,
    RecordStepPlan,
    RegisterBindingCarrierManifest,
    RegisterCompressionContract,
    RegisterRetentionPackage,
    ReopenRepresentation,
    RequestEffect,
    RequestReacquisition,
    RunRetrieval,
    SealImplementationGoal,
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
from rci.core.events import (
    CheckerVerdictRecorded,
    CognitivePlanRecorded,
    DomainEvent,
    EffectAttemptOutcomeRecorded,
    EffectAttemptStarted,
    EffectDecodeOutcomeRecorded,
    EffectNoAttemptDispositionRecorded,
    EffectRequested,
    EffectResultAccepted,
    EvidenceRecorded,
    ImplementationGoalSealed,
    InquiryStarted,
    MismatchRecorded,
    ObligationOpened,
    PredictionSealed,
    ProjectAnchorRecorded,
    StepPlanRecorded,
)
from rci.core.model import ArtifactRef, CapturedPayload, InquiryContext
from rci.core.replay import replay as replay_events
from rci.core.serialization import canonical_json_bytes, sha256_digest
from rci.core.state import InquiryState
from rci.core.transitions import decide, evolve
from rci.evaluation import (
    CapabilityConsequenceReport,
    CapabilityEvaluationBundle,
    CapabilityEvaluationProtocol,
    CapabilityTaskEnvelope,
    CognitiveHandoff,
    WeakReasonerFixture,
    build_capability_evaluation_bundle,
    build_resolution_invalid_bundle,
    capability_protocol_artifact,
    capability_result_artifact,
    capability_task_artifact,
    cognitive_handoff_artifact,
    failure_localization_frame_artifact,
)
from rci.evaluation.capability import CapabilityEvaluationEpisode
from rci.evaluation.fixtures import _build_weak_reasoner_fixture
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
from rci.persistence import ArtifactIntegrityError, ArtifactStore, SQLiteEventStore
from rci.project import (
    CandidateEnvironmentManifest,
    CapabilityFrontier,
    CapabilityLimitation,
    CapabilitySuccessorCandidate,
    DevelopmentEvidence,
    GoalAdmissionDecision,
    GoalSynthesisUnknown,
    ImplementationGoalCandidate,
    ImplementationGoalContract,
    IndependentReview,
    MethodAdmissionDecision,
    MethodBindingCandidate,
    ProjectAnchor,
    ProjectSuccessorDecision,
    PromotionDecision,
    QuestionContractCandidate,
    QuestionRepertoireDecision,
    RecursiveCycleCheckpoint,
    RecursiveStopDisposition,
    compile_implementation_goal_candidate,
)
from rci.questions import bind_answer, get_contract, render_question
from rci.questions.catalog import CATALOG_V0_3, CATALOG_V0_4, CORE_V1
from rci.questions.generated import (
    CompiledQuestionContract,
    GeneratedQuestionCompilationError,
    compile_admitted_question,
    generated_question_registry,
)
from rci.questions.models import QuestionContract
from rci.warrant import CheckerVerdict, CheckReference

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
    generated_compilation_id: str | None = None
    generated_candidate_id: str | None = None
    generated_decision_id: str | None = None
    generated_profile_id: str | None = None
    generated_comparison_policy_id: str | None = None

    @model_validator(mode="after")
    def validate_generated_pins(self) -> _QuestionEnvelope:
        pins = (
            self.generated_compilation_id,
            self.generated_candidate_id,
            self.generated_decision_id,
            self.generated_profile_id,
            self.generated_comparison_policy_id,
        )
        if any(value is not None for value in pins) and any(value is None for value in pins):
            raise ValueError("generated question envelope pins must be present together")
        return self


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

_GENERATED_CANDIDATE_ARGUMENT = "__rci_generated_question_candidate_id"
_GENERATED_DECISION_ARGUMENT = "__rci_generated_question_decision_id"
_GENERATED_COMPILATION_ARGUMENT = "__rci_generated_question_compilation_id"

_PROJECT_DOWNSTREAM_OBLIGATION_KIND: dict[str, ObligationKind] = {
    "theory": ObligationKind.CHARACTERIZE,
    "question": ObligationKind.CHARACTERIZE_RESIDUAL,
    "probe": ObligationKind.SAME_CLASS_VARIATION,
    "representation": ObligationKind.MINIMAL_BOUNDARY_CROSSING,
    "method": ObligationKind.CHARACTERIZE_RESIDUAL,
    "evidence": ObligationKind.LOCALIZE_CONFLICT,
    "implementation": ObligationKind.PROPOSE_FACTOR,
    "authority": ObligationKind.CHARACTERIZE_RESIDUAL,
}


def _stable_id(prefix: str, *parts: str) -> str:
    digest = sha256("\x00".join(parts).encode()).hexdigest()[:24]
    return f"{prefix}_{digest}"


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _artifact_refs(value: object) -> Iterable[ArtifactRef]:
    """Walk strict records without serializing away ArtifactRef identity."""

    if isinstance(value, ArtifactRef):
        yield value
    elif isinstance(value, BaseModel):
        for name in type(value).model_fields:
            yield from _artifact_refs(getattr(value, name))
    elif isinstance(value, (tuple, list)):
        for item in value:
            yield from _artifact_refs(item)


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
    def _text_argument(obligation: Obligation, name: str) -> str | None:
        value = next((item.value for item in obligation.args if item.name == name), None)
        return value if isinstance(value, str) else None

    def generated_question_registry(self, inquiry_id: str) -> tuple[CompiledQuestionContract, ...]:
        return generated_question_registry(self.inspect(inquiry_id))

    def open_generated_question(
        self,
        inquiry_id: str,
        *,
        candidate_id: str,
        bindings: dict[str, str],
    ) -> InquiryState:
        """Open one ordinary obligation from an exact compiled project question."""

        state = self.inspect(inquiry_id)
        compiled = compile_admitted_question(state, candidate_id)
        registered = next(
            (
                item
                for item in generated_question_registry(state)
                if item.candidate_id == candidate_id
            ),
            None,
        )
        if registered != compiled:
            raise GeneratedQuestionCompilationError(
                "generated question is not unique in the active confined registry"
            )
        render_question(compiled.contract, bindings)
        if bindings != {"limitation": compiled.limitation_id}:
            raise GeneratedQuestionCompilationError(
                "generated question bindings must name the exact owned limitation"
            )
        if state.context is None:  # pragma: no cover - compiler invariant
            raise RuntimeError("generated question requires a started inquiry")
        if (
            compiled.binding_revision != state.context.binding_revision
            or compiled.scope_fingerprint != state.context.scope_fingerprint
        ):
            raise GeneratedQuestionCompilationError(
                "generated question compilation is stale for the inquiry context"
            )
        argument_values = {
            **bindings,
            _GENERATED_CANDIDATE_ARGUMENT: compiled.candidate_id,
            _GENERATED_DECISION_ARGUMENT: compiled.decision_id,
            _GENERATED_COMPILATION_ARGUMENT: compiled.id,
        }
        args = tuple(
            BoundArgument(name=name, value=value) for name, value in sorted(argument_values.items())
        )
        obligation = Obligation(
            id=_stable_id(
                "obl",
                inquiry_id,
                compiled.id,
                canonical_json_bytes(bindings).decode(),
            ),
            kind=ObligationKind.SEPARATE_CONSEQUENCE_CLASSES,
            carrier_id=compiled.limitation_id,
            args=args,
            scope=self._scope_from_context(state.context),
            binding_revision=state.context.binding_revision,
            priority_vector=(200,),
        )
        return self.dispatch(
            OpenObligation(
                event_id=_stable_id("evt", inquiry_id, obligation.id, "generated-open"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                obligation=obligation,
            )
        )

    def _compiled_question_for_obligation(
        self,
        state: InquiryState,
        obligation: Obligation,
    ) -> CompiledQuestionContract | None:
        candidate_id = self._text_argument(obligation, _GENERATED_CANDIDATE_ARGUMENT)
        decision_id = self._text_argument(obligation, _GENERATED_DECISION_ARGUMENT)
        compilation_id = self._text_argument(obligation, _GENERATED_COMPILATION_ARGUMENT)
        marker_values = (candidate_id, decision_id, compilation_id)
        if all(value is None for value in marker_values):
            return None
        if any(value is None for value in marker_values):
            raise GeneratedQuestionCompilationError(
                "generated question obligation has incomplete admission pins"
            )
        assert candidate_id is not None
        compiled = compile_admitted_question(state, candidate_id)
        registered = next(
            (
                item
                for item in generated_question_registry(state)
                if item.candidate_id == candidate_id
            ),
            None,
        )
        if (
            registered != compiled
            or decision_id != compiled.decision_id
            or compilation_id != compiled.id
            or obligation.carrier_id != compiled.limitation_id
            or obligation.binding_revision != compiled.binding_revision
            or obligation.scope.fingerprint != compiled.scope_fingerprint
        ):
            raise GeneratedQuestionCompilationError(
                "generated question obligation differs from its exact compilation"
            )
        return compiled

    def _contract_for_obligation(
        self,
        state: InquiryState,
        obligation: Obligation,
    ) -> QuestionContract | None:
        marker_values = tuple(
            self._text_argument(obligation, name)
            for name in (
                _GENERATED_CANDIDATE_ARGUMENT,
                _GENERATED_DECISION_ARGUMENT,
                _GENERATED_COMPILATION_ARGUMENT,
            )
        )
        try:
            compiled = self._compiled_question_for_obligation(state, obligation)
        except GeneratedQuestionCompilationError:
            return None
        if compiled is not None:
            return compiled.contract
        if any(value is not None for value in marker_values):
            return None
        contract_id = _CONTRACT_BY_OBLIGATION_KIND.get(obligation.kind)
        if contract_id is None:
            return None
        contract = get_contract(contract_id)
        if contract.key not in CORE_V1.contract_keys:
            raise RuntimeError("only the admitted core-v1 profile may be scheduled")
        return contract

    @staticmethod
    def _bindings_for_contract(
        obligation: Obligation,
        contract: QuestionContract,
    ) -> dict[str, str]:
        values = {item.name: item.value for item in obligation.args}
        bindings: dict[str, str] = {}
        for role in contract.input_roles:
            value = values.get(role)
            if not isinstance(value, str):
                raise RuntimeError("question obligation lacks a typed text binding")
            bindings[role] = value
        return bindings

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
            contract = self._contract_for_obligation(state, obligation)
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
        state: InquiryState,
        step_plan: StepPlan,
        obligation: Obligation,
        contract: QuestionContract,
    ) -> tuple[EffectRequest, EffectAttemptPlan, str]:
        rendered = render_question(
            contract,
            self._bindings_for_contract(obligation, contract),
        )
        contract_ref = self.artifacts.put_bytes(
            canonical_json_bytes(contract),
            media_type="application/vnd.rci.question-contract+json",
            encoding="utf-8",
        )
        inquiry_context = state.context
        if inquiry_context is None:
            raise RuntimeError("manual request requires a started inquiry context")
        compiled = self._compiled_question_for_obligation(state, obligation)
        envelope = _QuestionEnvelope(
            obligation_id=obligation.id,
            obligation_fingerprint=obligation.fingerprint,
            contract_id=contract.id,
            contract_version=contract.version,
            catalog_manifest_digest=inquiry_context.catalog_manifest_digest,
            contract_artifact=contract_ref,
            rendered_question=rendered,
            generated_compilation_id=compiled.id if compiled is not None else None,
            generated_candidate_id=compiled.candidate_id if compiled is not None else None,
            generated_decision_id=compiled.decision_id if compiled is not None else None,
            generated_profile_id=compiled.profile_id if compiled is not None else None,
            generated_comparison_policy_id=(
                compiled.comparison_policy_id if compiled is not None else None
            ),
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
                and self._contract_for_obligation(state, obligation) is None
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
        contract = self._contract_for_obligation(state, obligation)
        if contract is None:  # pragma: no cover - scheduler projection invariant
            raise RuntimeError("step plan selected an inactive contract")
        request, plan, rendered = self._manual_request(
            inquiry_id,
            state=state,
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

    def _generated_downstream_obligation(
        self,
        *,
        state: InquiryState,
        source_obligation: Obligation,
        envelope: _QuestionEnvelope,
        answer: str | bytes | None,
        source_claim_id: str,
    ) -> Obligation | None:
        if envelope.generated_candidate_id is None:
            return None
        compiled = compile_admitted_question(state, envelope.generated_candidate_id)
        if (
            envelope.generated_compilation_id != compiled.id
            or envelope.generated_decision_id != compiled.decision_id
            or envelope.generated_profile_id != compiled.profile_id
            or envelope.generated_comparison_policy_id != compiled.comparison_policy_id
        ):
            raise GeneratedQuestionCompilationError(
                "generated question return differs from its persisted compilation"
            )
        matched = next(
            (
                item
                for item in compiled.possible_returns
                if isinstance(answer, str) and answer == item.return_class_id
            ),
            None,
        )
        return_class_id = matched.return_class_id if matched is not None else "unclassified"
        downstream_state_id = (
            matched.downstream_state_id
            if matched is not None
            else f"unclassified-return:{compiled.candidate_id}"
        )
        downstream_kind = (
            _PROJECT_DOWNSTREAM_OBLIGATION_KIND[matched.downstream_obligation_kind.value]
            if matched is not None
            else ObligationKind.CHARACTERIZE_RESIDUAL
        )
        limitation_kind = (
            matched.downstream_obligation_kind.value if matched is not None else "unknown"
        )
        argument_values = {
            "carrier": downstream_state_id,
            "downstream_limitation_kind": limitation_kind,
            "generated_return_class_id": return_class_id,
            "source_claim_id": source_claim_id,
            "source_question_candidate_id": compiled.candidate_id,
        }
        return Obligation(
            id=_stable_id(
                "obl",
                source_obligation.id,
                compiled.id,
                return_class_id,
                downstream_state_id,
            ),
            kind=downstream_kind,
            carrier_id=downstream_state_id,
            args=tuple(
                BoundArgument(name=name, value=value)
                for name, value in sorted(argument_values.items())
            ),
            scope=source_obligation.scope,
            binding_revision=source_obligation.binding_revision,
            parent_obligation_ids=(source_obligation.id,),
            priority_vector=(150,),
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
        contract = self._contract_for_obligation(state, obligation)
        if contract is None or contract != recorded_contract:
            raise RuntimeError("persisted question contract is not active for its obligation")
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
        downstream = self._generated_downstream_obligation(
            state=state,
            source_obligation=obligation,
            envelope=envelope,
            answer=answer,
            source_claim_id=claim.id,
        )
        commands: list[DomainCommand] = [
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
        ]
        if downstream is not None:
            commands.append(
                OpenObligation(
                    event_id=_stable_id("evt", downstream.id, "generated-downstream"),
                    inquiry_id=inquiry_id,
                    occurred_at=now,
                    obligation=downstream,
                )
            )
        return self._apply_batch(inquiry_id, tuple(commands))

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

    def register_binding_carriers(
        self, inquiry_id: str, manifest: BindingCarrierManifest
    ) -> InquiryState:
        return self.dispatch(
            RegisterBindingCarrierManifest(
                event_id=_stable_id("evt", inquiry_id, manifest.id, "carrier-manifest"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                manifest=manifest,
            )
        )

    def record_realized_history(
        self, inquiry_id: str, derivation: RealizedHistoryDerivation
    ) -> InquiryState:
        return self.dispatch(
            RecordRealizedHistoryDerivation(
                event_id=_stable_id("evt", inquiry_id, derivation.id, "history-derived"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                derivation=derivation,
            )
        )

    def register_compression_contract(
        self, inquiry_id: str, contract: CompressionContract
    ) -> InquiryState:
        return self.dispatch(
            RegisterCompressionContract(
                event_id=_stable_id("evt", inquiry_id, contract.id, "compression-contract"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                contract=contract,
            )
        )

    def record_compression_validation(
        self, inquiry_id: str, validation: CompressionValidation
    ) -> InquiryState:
        return self.dispatch(
            RecordCompressionValidation(
                event_id=_stable_id("evt", inquiry_id, validation.id, "compression-validation"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                validation=validation,
            )
        )

    def grant_exact_compression_license(
        self, inquiry_id: str, license_record: ExactCompressionLicense
    ) -> InquiryState:
        return self.dispatch(
            GrantExactCompressionLicense(
                event_id=_stable_id("evt", inquiry_id, license_record.id, "exact-license"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                license=license_record,
            )
        )

    def record_compression_application(
        self,
        inquiry_id: str,
        application: CompressionApplication,
        *,
        path_residues: tuple[PathResidue, ...] = (),
    ) -> InquiryState:
        return self.dispatch(
            RecordCompressionApplication(
                event_id=_stable_id("evt", inquiry_id, application.id, "compressed"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                application=application,
                path_residues=path_residues,
            )
        )

    def grant_recovery_license(
        self, inquiry_id: str, license_record: RecoveryLicense
    ) -> InquiryState:
        return self.dispatch(
            GrantRecoveryLicense(
                event_id=_stable_id("evt", inquiry_id, license_record.id, "recovery-license"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                license=license_record,
            )
        )

    def link_retention_capability(
        self, inquiry_id: str, link: RetentionCapabilityLink
    ) -> InquiryState:
        return self.dispatch(
            LinkRetentionCapability(
                event_id=_stable_id("evt", inquiry_id, link.id, "capability-linked"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                link=link,
            )
        )

    def decide_representation_successor(
        self, inquiry_id: str, decision: RepresentationSuccessorDecision
    ) -> InquiryState:
        return self.dispatch(
            DecideRepresentationSuccessor(
                event_id=_stable_id("evt", inquiry_id, decision.id, "successor-decided"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                decision=decision,
            )
        )

    def reopen_representation(
        self, inquiry_id: str, reopening: RepresentationReopening
    ) -> InquiryState:
        return self.dispatch(
            ReopenRepresentation(
                event_id=_stable_id("evt", inquiry_id, reopening.id, "representation-reopened"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                reopening=reopening,
            )
        )

    def record_project_anchor(self, inquiry_id: str, anchor: ProjectAnchor) -> InquiryState:
        return self.dispatch(
            RecordProjectAnchor(
                event_id=_stable_id("evt", inquiry_id, anchor.id, "project-anchor"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                anchor=anchor,
            )
        )

    def record_capability_limitation(
        self, inquiry_id: str, limitation: CapabilityLimitation
    ) -> InquiryState:
        return self.dispatch(
            RecordCapabilityLimitation(
                event_id=_stable_id("evt", inquiry_id, limitation.id, "capability-limitation"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                limitation=limitation,
            )
        )

    def record_question_contract_candidate(
        self, inquiry_id: str, candidate: QuestionContractCandidate
    ) -> InquiryState:
        return self.dispatch(
            RecordQuestionContractCandidate(
                event_id=_stable_id("evt", inquiry_id, candidate.id, "question-candidate"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                candidate=candidate,
            )
        )

    def decide_question_repertoire(
        self, inquiry_id: str, decision: QuestionRepertoireDecision
    ) -> InquiryState:
        return self.dispatch(
            DecideQuestionRepertoire(
                event_id=_stable_id("evt", inquiry_id, decision.id, "question-decision"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                decision=decision,
            )
        )

    def record_method_binding_candidate(
        self, inquiry_id: str, candidate: MethodBindingCandidate
    ) -> InquiryState:
        return self.dispatch(
            RecordMethodBindingCandidate(
                event_id=_stable_id("evt", inquiry_id, candidate.id, "method-candidate"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                candidate=candidate,
            )
        )

    def decide_method_admission(
        self, inquiry_id: str, decision: MethodAdmissionDecision
    ) -> InquiryState:
        return self.dispatch(
            DecideMethodAdmission(
                event_id=_stable_id("evt", inquiry_id, decision.id, "method-decision"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                decision=decision,
            )
        )

    def record_capability_successor_candidate(
        self, inquiry_id: str, candidate: CapabilitySuccessorCandidate
    ) -> InquiryState:
        return self.dispatch(
            RecordCapabilitySuccessorCandidate(
                event_id=_stable_id("evt", inquiry_id, candidate.id, "successor-candidate"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                candidate=candidate,
            )
        )

    def record_capability_frontier(
        self, inquiry_id: str, frontier: CapabilityFrontier
    ) -> InquiryState:
        return self.dispatch(
            RecordCapabilityFrontier(
                event_id=_stable_id("evt", inquiry_id, frontier.id, "capability-frontier"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                frontier=frontier,
            )
        )

    def derive_implementation_goal_candidate(
        self,
        inquiry_id: str,
        *,
        source_obligation_id: str,
        downstream_obligation_id: str,
        frontier_id: str,
    ) -> ImplementationGoalCandidate | GoalSynthesisUnknown:
        return compile_implementation_goal_candidate(
            self.inspect(inquiry_id),
            source_obligation_id=source_obligation_id,
            downstream_obligation_id=downstream_obligation_id,
            frontier_id=frontier_id,
        )

    def record_implementation_goal_candidate(
        self, inquiry_id: str, candidate: ImplementationGoalCandidate
    ) -> InquiryState:
        return self.dispatch(
            RecordImplementationGoalCandidate(
                event_id=_stable_id("evt", inquiry_id, candidate.id, "goal-candidate"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                candidate=candidate,
            )
        )

    def decide_goal_admission(
        self, inquiry_id: str, decision: GoalAdmissionDecision
    ) -> InquiryState:
        return self.dispatch(
            DecideGoalAdmission(
                event_id=_stable_id("evt", inquiry_id, decision.id, "goal-admission"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                decision=decision,
            )
        )

    def seal_admitted_implementation_goal(
        self, inquiry_id: str, *, candidate_id: str
    ) -> InquiryState:
        state = self.inspect(inquiry_id)
        candidate = next(
            (item for item in state.implementation_goal_candidates if item.id == candidate_id),
            None,
        )
        if candidate is None or not any(
            decision.candidate_id == candidate.id
            and decision.outcome.value == "admit"
            and decision.admitted_goal_id == candidate.goal.id
            for decision in state.goal_admission_decisions
        ):
            raise ValueError("implementation Goal candidate is not admitted")
        return self.seal_implementation_goal(inquiry_id, candidate.goal)

    def seal_implementation_goal(
        self, inquiry_id: str, goal: ImplementationGoalContract
    ) -> InquiryState:
        return self.dispatch(
            SealImplementationGoal(
                event_id=_stable_id("evt", inquiry_id, goal.id, "implementation-goal"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                goal=goal,
            )
        )

    def record_candidate_environment(
        self, inquiry_id: str, manifest: CandidateEnvironmentManifest
    ) -> InquiryState:
        return self.dispatch(
            RecordCandidateEnvironment(
                event_id=_stable_id("evt", inquiry_id, manifest.id, "candidate-environment"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                manifest=manifest,
            )
        )

    def record_development_evidence(
        self, inquiry_id: str, evidence: DevelopmentEvidence
    ) -> InquiryState:
        return self.dispatch(
            RecordDevelopmentEvidence(
                event_id=_stable_id("evt", inquiry_id, evidence.id, "development-evidence"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                evidence=evidence,
            )
        )

    def record_independent_review(self, inquiry_id: str, review: IndependentReview) -> InquiryState:
        return self.dispatch(
            RecordIndependentReview(
                event_id=_stable_id("evt", inquiry_id, review.id, "independent-review"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                review=review,
            )
        )

    def decide_project_successor(
        self, inquiry_id: str, decision: ProjectSuccessorDecision
    ) -> InquiryState:
        return self.dispatch(
            DecideProjectSuccessor(
                event_id=_stable_id("evt", inquiry_id, decision.id, "project-successor"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                decision=decision,
            )
        )

    def record_promotion_decision(
        self, inquiry_id: str, decision: PromotionDecision
    ) -> InquiryState:
        """Record an externally observed promotion fact; never perform Git mutation."""

        return self.dispatch(
            RecordPromotionDecision(
                event_id=_stable_id("evt", inquiry_id, decision.id, "promotion-decision"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                decision=decision,
            )
        )

    def record_recursive_cycle_checkpoint(
        self, inquiry_id: str, checkpoint: RecursiveCycleCheckpoint
    ) -> InquiryState:
        return self.dispatch(
            RecordRecursiveCycleCheckpoint(
                event_id=_stable_id("evt", inquiry_id, checkpoint.id, "cycle-checkpoint"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                checkpoint=checkpoint,
            )
        )

    def record_recursive_stop_disposition(
        self, inquiry_id: str, disposition: RecursiveStopDisposition
    ) -> InquiryState:
        return self.dispatch(
            RecordRecursiveStopDisposition(
                event_id=_stable_id("evt", inquiry_id, disposition.id, "recursive-stop"),
                inquiry_id=inquiry_id,
                occurred_at=self.clock(),
                disposition=disposition,
            )
        )

    def publish_capability_task(self, task: CapabilityTaskEnvelope) -> ArtifactRef:
        """Publish the actor-visible task without evaluator-only expected answers."""

        artifact = self.artifacts.put_bytes(
            canonical_json_bytes(task),
            media_type="application/vnd.rci.capability-task+json",
            encoding="utf-8",
        )
        if artifact != capability_task_artifact(task):
            raise ArtifactIntegrityError("published capability task metadata changed")
        return artifact

    def publish_capability_evaluation_protocol(
        self, protocol: CapabilityEvaluationProtocol
    ) -> ArtifactRef:
        """Publish the exact pre-return protocol bytes to CAS."""

        task = CapabilityTaskEnvelope.model_validate_json(
            self.artifacts.get_bytes(protocol.actor_task_artifact), strict=True
        )
        self.artifacts.verify(protocol.actor_task_artifact)
        if capability_task_artifact(task) != protocol.actor_task_artifact:
            raise ValueError("protocol actor-task artifact does not match its exact bytes")
        task_fields = (
            "anchor_id",
            "goal_id",
            "obligation_id",
            "task_id",
            "competence_id",
            "binding_revision",
            "scope_fingerprint",
            "protected_horizon_id",
            "operation_id",
            "actor_id",
            "actor_revision",
            "adapter_id",
            "route_definition_id",
            "route_definition_version",
            "context_artifact",
            "evidence_access_artifact",
            "budget_artifact",
            "assistance_artifact",
            "continuation_discriminator_id",
            "timeout_seconds",
        )
        if any(getattr(task, field) != getattr(protocol, field) for field in task_fields):
            raise ValueError("protocol and actor-visible task pins differ")

        if protocol.predecessor_handoff_artifact is not None:
            predecessor = CognitiveHandoff.model_validate_json(
                self.artifacts.get_bytes(protocol.predecessor_handoff_artifact), strict=True
            )
            self.artifacts.verify(protocol.predecessor_handoff_artifact)
            resolved_predecessor = self._evaluate_capability_request(
                predecessor.source_inquiry_id,
                predecessor.effect_request_id,
                through_sequence=predecessor.source_sequence,
            ).handoff
            if predecessor != resolved_predecessor:
                raise ValueError("predecessor handoff does not match its authoritative prefix")
            if (
                predecessor.anchor_id != protocol.anchor_id
                or predecessor.goal_id != protocol.goal_id
                or predecessor.project_head_sha != protocol.project_head_sha
                or predecessor.gate_digest != protocol.gate_digest
                or predecessor.protected_capability_ids != protocol.protected_capability_ids
            ):
                raise ValueError("successor protocol does not preserve its predecessor handoff")
            predecessor_protocol = CapabilityEvaluationProtocol.model_validate_json(
                self.artifacts.get_bytes(predecessor.protocol_artifact), strict=True
            )
            continuity_fields = (
                "anchor_fingerprint",
                "goal_fingerprint",
                "task_id",
                "competence_id",
                "operation_id",
                "effect_kind",
                "binding_revision",
                "scope_fingerprint",
                "protected_horizon_id",
                "context_artifact",
                "evidence_access_artifact",
                "budget_artifact",
                "timeout_seconds",
                "comparison_policy_id",
                "comparison_policy_version",
                "protected_capability_ids",
            )
            if any(
                getattr(predecessor_protocol, field) != getattr(protocol, field)
                for field in continuity_fields
            ):
                raise ValueError("successor protocol changes protected predecessor task pins")
            if predecessor_protocol.expectations != protocol.expectations:
                raise ValueError("successor protocol changes protected predecessor expectations")
            if protocol.continuation_discriminator_id != predecessor.next_discriminator_id:
                raise ValueError("successor protocol changes the sealed next discriminator")
            repeated_requirements: set[str] = set()
            if protocol.route_definition_id in predecessor.forbidden_route_ids_until_reopen:
                repeated_requirements.add(f"reopen-route:{protocol.route_definition_id}")
            if protocol.decoder_id in predecessor.forbidden_decoder_ids_until_reopen:
                repeated_requirements.add(f"reopen-decoder:{protocol.decoder_id}")
            if protocol.reopening_evidence_artifacts and not repeated_requirements:
                raise ValueError("reopening evidence has no failed route or decoder to reopen")
            if not repeated_requirements.issubset(set(predecessor.reopening_condition_ids)):
                raise ValueError("reopening target is not a sealed predecessor condition")
            source_state = self.inspect(predecessor.source_inquiry_id)
            source_stream = self.events.load_stream(predecessor.source_inquiry_id)
            covered_requirements: set[str] = set()
            for artifact, verdict_id in zip(
                protocol.reopening_evidence_artifacts,
                protocol.reopening_checker_verdict_ids,
                strict=True,
            ):
                self.artifacts.verify(artifact)
                evidence_matches = tuple(
                    item for item in source_state.evidence_records if item.artifact == artifact
                )
                verdict = source_state.checker_verdict_by_id(verdict_id)
                if len(evidence_matches) != 1 or verdict is None:
                    raise ValueError("reopening evidence is not uniquely owned and checked")
                evidence = evidence_matches[0]
                if (
                    verdict.evidence_id != evidence.id
                    or verdict.evidence_artifact != evidence.artifact
                    or verdict.proposition_id != evidence.proposition_id
                    or verdict.verdict is not CheckerVerdict.VALID
                    or verdict.certificate_artifact is None
                    or source_state.context is None
                    or verdict.checker_id not in source_state.context.discharge_mechanism_ids
                    or verdict.checker_id == predecessor_protocol.actor_id
                    or verdict.checker_id == protocol.actor_id
                    or evidence.proposition_id not in repeated_requirements
                ):
                    raise ValueError("reopening evidence lacks an exact authorized valid check")
                evidence_sequence = next(
                    (
                        stored.sequence
                        for stored in source_stream.events
                        if isinstance(stored.event, EvidenceRecorded)
                        and stored.event.evidence.id == evidence.id
                    ),
                    None,
                )
                verdict_sequence = next(
                    (
                        stored.sequence
                        for stored in source_stream.events
                        if isinstance(stored.event, CheckerVerdictRecorded)
                        and stored.event.checker_verdict.id == verdict.id
                    ),
                    None,
                )
                if (
                    evidence_sequence is None
                    or verdict_sequence is None
                    or evidence_sequence <= predecessor.source_sequence
                    or verdict_sequence <= predecessor.source_sequence
                ):
                    raise ValueError("reopening check must follow the exact predecessor handoff")
                covered_requirements.add(evidence.proposition_id)
            if covered_requirements != repeated_requirements:
                raise ValueError(
                    "successor protocol repeats a failed route without checked reopening"
                )
            if (
                protocol.route_definition_id not in predecessor.forbidden_route_ids_until_reopen
                and protocol.route_definition_id != predecessor.next_discriminator_route_id
            ):
                raise ValueError("successor protocol does not follow the sealed next discriminator")
        artifact = self.artifacts.put_bytes(
            canonical_json_bytes(protocol),
            media_type="application/vnd.rci.capability-evaluation+json",
            encoding="utf-8",
        )
        if artifact != capability_protocol_artifact(protocol):
            raise ArtifactIntegrityError("published capability protocol metadata changed")
        return artifact

    def _publish_capability_bundle(self, bundle: CapabilityEvaluationBundle) -> None:
        result_ref = self.artifacts.put_bytes(
            canonical_json_bytes(bundle.result),
            media_type="application/vnd.rci.capability-evaluation-result+json",
            encoding="utf-8",
        )
        if result_ref != capability_result_artifact(bundle.result):
            raise ArtifactIntegrityError("published capability result metadata changed")
        if bundle.localization_frame is not None:
            frame_ref = self.artifacts.put_bytes(
                canonical_json_bytes(bundle.localization_frame),
                media_type="application/vnd.rci.failure-localization-frame+json",
                encoding="utf-8",
            )
            if frame_ref != failure_localization_frame_artifact(bundle.localization_frame):
                raise ArtifactIntegrityError("published localization frame metadata changed")
        handoff_ref = self.artifacts.put_bytes(
            canonical_json_bytes(bundle.handoff),
            media_type="application/vnd.rci.cognitive-handoff+json",
            encoding="utf-8",
        )
        if handoff_ref != cognitive_handoff_artifact(bundle.handoff):
            raise ArtifactIntegrityError("published cognitive handoff metadata changed")

    def _evaluate_capability_request(
        self,
        inquiry_id: str,
        request_id: str,
        *,
        through_sequence: int | None = None,
    ) -> CapabilityEvaluationBundle:
        """Resolve one owned ledger lifecycle, verify CAS, then invoke the pure projector."""

        stream = self.events.load_stream(inquiry_id)
        selected_sequence = stream.version if through_sequence is None else through_sequence
        if selected_sequence < 1 or selected_sequence > stream.version:
            raise ValueError("capability evaluation prefix is outside the owned stream")
        selected_events = stream.events[:selected_sequence]
        state = replay_events(item.event for item in selected_events)
        request_state = state.request_by_id(request_id)
        if request_state is None:
            raise ValueError("capability evaluation request is not owned by the inquiry")
        cognitive_plans = tuple(
            item for item in state.cognitive_plans if item.effect_request_id == request_id
        )
        cognitive_plan = cognitive_plans[0] if len(cognitive_plans) == 1 else None
        predictions = tuple(
            item
            for item in state.predictions
            if cognitive_plan is not None and item.cognitive_plan_id == cognitive_plan.id
        )
        prediction = predictions[0] if len(predictions) == 1 else None
        if cognitive_plan is None or prediction is None:
            raise ValueError("capability request lacks one exact owned prediction commitment")
        try:
            actor_task_artifact = request_state.request.input_artifact
            actor_task = CapabilityTaskEnvelope.model_validate_json(
                self.artifacts.get_bytes(actor_task_artifact), strict=True
            )
            if actor_task_artifact != capability_task_artifact(actor_task):
                raise ValueError("request task artifact metadata does not match its bytes")
            predicted = prediction.predicted_consequence
            if not isinstance(predicted, dict):
                raise ValueError("prediction does not contain a protocol commitment")
            protocol_material = predicted.get("protocol_artifact")
            protocol_artifact = ArtifactRef.model_validate(protocol_material, strict=True)
            protocol = CapabilityEvaluationProtocol.model_validate_json(
                self.artifacts.get_bytes(protocol_artifact), strict=True
            )
            if protocol_artifact != capability_protocol_artifact(protocol):
                raise ValueError("prediction protocol artifact metadata does not match its bytes")
            if predicted.get("protocol_id") != protocol.id:
                raise ValueError("prediction protocol identity does not match its artifact")
        except (ArtifactIntegrityError, ValidationError, ValueError) as exc:
            raise ValueError("request does not have a valid sealed capability protocol") from exc

        anchor = next(
            (item for item in state.project_anchors if item.id == protocol.anchor_id), None
        )
        goal = next(
            (item for item in state.implementation_goals if item.id == protocol.goal_id), None
        )
        obligation = state.obligation_by_id(protocol.obligation_id)
        step_plan = state.step_plan_by_id(protocol.step_plan_id)
        resolution_issues: list[str] = []
        for value, issue in (
            (anchor, "anchor_not_owned"),
            (goal, "goal_not_owned"),
            (obligation, "obligation_not_owned"),
            (step_plan, "step_plan_not_owned"),
        ):
            if value is None:
                resolution_issues.append(issue)
        if resolution_issues:
            bundle = build_resolution_invalid_bundle(
                protocol=protocol,
                protocol_artifact=protocol_artifact,
                source_inquiry_id=inquiry_id,
                source_sequence=state.sequence,
                request_id=request_id,
                issue_codes=tuple(resolution_issues),
            )
            self._publish_capability_bundle(bundle)
            return bundle
        assert anchor is not None
        assert goal is not None
        assert obligation is not None
        assert step_plan is not None
        assert cognitive_plan is not None
        assert prediction is not None
        assert state.context is not None

        anchor_sequence = next(
            (
                stored.sequence
                for stored in selected_events
                if isinstance(stored.event, ProjectAnchorRecorded)
                and stored.event.anchor.id == anchor.id
            ),
            None,
        )
        goal_sequence = next(
            (
                stored.sequence
                for stored in selected_events
                if isinstance(stored.event, ImplementationGoalSealed)
                and stored.event.goal.id == goal.id
            ),
            None,
        )
        obligation_sequence = next(
            (
                stored.sequence
                for stored in selected_events
                if isinstance(stored.event, ObligationOpened)
                and stored.event.obligation.id == obligation.id
            ),
            None,
        )
        step_sequence = next(
            (
                stored.sequence
                for stored in selected_events
                if isinstance(stored.event, StepPlanRecorded)
                and stored.event.plan.id == step_plan.id
            ),
            None,
        )
        request_sequence = next(
            (
                stored.sequence
                for stored in selected_events
                if isinstance(stored.event, EffectRequested)
                and stored.event.request.id == request_id
            ),
            None,
        )
        cognitive_sequence = next(
            (
                stored.sequence
                for stored in selected_events
                if isinstance(stored.event, CognitivePlanRecorded)
                and stored.event.plan.id == cognitive_plan.id
            ),
            None,
        )
        prediction_sequence = next(
            (
                stored.sequence
                for stored in selected_events
                if isinstance(stored.event, PredictionSealed)
                and stored.event.prediction.id == prediction.id
            ),
            None,
        )
        terminal_sequences = tuple(
            stored.sequence
            for stored in selected_events
            if (
                isinstance(stored.event, EffectAttemptOutcomeRecorded)
                and stored.event.request_id == request_id
            )
            or (
                isinstance(stored.event, EffectNoAttemptDispositionRecorded)
                and stored.event.disposition.request_id == request_id
            )
        )
        required_sequences = (
            anchor_sequence,
            goal_sequence,
            obligation_sequence,
            step_sequence,
            request_sequence,
            cognitive_sequence,
            prediction_sequence,
        )
        if any(sequence is None for sequence in required_sequences):
            resolution_issues.append("antecedence_record_missing")
        else:
            assert anchor_sequence is not None
            assert goal_sequence is not None
            assert obligation_sequence is not None
            assert step_sequence is not None
            assert request_sequence is not None
            assert cognitive_sequence is not None
            assert prediction_sequence is not None
            if not (
                anchor_sequence < request_sequence
                and goal_sequence < request_sequence
                and obligation_sequence < step_sequence < request_sequence
            ):
                resolution_issues.append("authority_not_antecedent_to_request")
            if not request_sequence < cognitive_sequence < prediction_sequence:
                resolution_issues.append("prediction_plan_order_invalid")
            if terminal_sequences and prediction_sequence >= min(terminal_sequences):
                resolution_issues.append("prediction_not_antecedent_to_return")

            if protocol.assistance_artifact is not None:
                assistance_proposition = f"capability-assistance:{protocol.task_id}"
                assistance_evidence = tuple(
                    item
                    for item in state.evidence_records
                    if item.artifact == protocol.assistance_artifact
                    and item.proposition_id == assistance_proposition
                    and item.proposition_kind.value == "relation"
                    and item.scope_fingerprint == protocol.scope_fingerprint
                )
                assistance_verdicts = (
                    tuple(
                        item
                        for item in state.checker_verdicts
                        if len(assistance_evidence) == 1
                        and item.evidence_id == assistance_evidence[0].id
                        and item.evidence_artifact == assistance_evidence[0].artifact
                        and item.proposition_id == assistance_proposition
                    )
                    if assistance_evidence
                    else ()
                )
                attempt_ids = {attempt.plan.id for attempt in request_state.attempts}
                first_start_sequence = min(
                    (
                        stored.sequence
                        for stored in selected_events
                        if isinstance(stored.event, EffectAttemptStarted)
                        and stored.event.attempt_id in attempt_ids
                    ),
                    default=None,
                )
                if first_start_sequence is None:
                    pass
                elif len(assistance_evidence) != 1 or len(assistance_verdicts) != 1:
                    resolution_issues.append("assistance_not_uniquely_checked")
                else:
                    evidence = assistance_evidence[0]
                    assistance_verdict = assistance_verdicts[0]
                    evidence_sequence = next(
                        (
                            stored.sequence
                            for stored in selected_events
                            if isinstance(stored.event, EvidenceRecorded)
                            and stored.event.evidence.id == evidence.id
                        ),
                        None,
                    )
                    verdict_sequence = next(
                        (
                            stored.sequence
                            for stored in selected_events
                            if isinstance(stored.event, CheckerVerdictRecorded)
                            and stored.event.checker_verdict.id == assistance_verdict.id
                        ),
                        None,
                    )
                    if (
                        evidence_sequence is None
                        or verdict_sequence is None
                        or not evidence_sequence <= verdict_sequence < first_start_sequence
                        or assistance_verdict.verdict is not CheckerVerdict.VALID
                        or assistance_verdict.certificate_artifact is None
                        or assistance_verdict.checker_id
                        not in state.context.discharge_mechanism_ids
                        or assistance_verdict.checker_id == protocol.actor_id
                    ):
                        resolution_issues.append("assistance_not_independently_checked")

            prior_protocols: list[tuple[int, str, CapabilityEvaluationProtocol]] = []
            for prior_plan in state.cognitive_plans:
                if prior_plan.effect_request_id == request_id:
                    continue
                prior_prediction = next(
                    (item for item in state.predictions if item.cognitive_plan_id == prior_plan.id),
                    None,
                )
                if prior_prediction is None:
                    continue
                prior_sequence = next(
                    (
                        stored.sequence
                        for stored in selected_events
                        if isinstance(stored.event, PredictionSealed)
                        and stored.event.prediction.id == prior_prediction.id
                    ),
                    None,
                )
                if prior_sequence is None or prior_sequence >= request_sequence:
                    continue
                try:
                    prior_material = prior_prediction.predicted_consequence
                    if not isinstance(prior_material, dict):
                        continue
                    prior_ref = ArtifactRef.model_validate(
                        prior_material.get("protocol_artifact"), strict=True
                    )
                    prior_protocol = CapabilityEvaluationProtocol.model_validate_json(
                        self.artifacts.get_bytes(prior_ref), strict=True
                    )
                except (ArtifactIntegrityError, ValidationError, ValueError):
                    continue
                if (
                    prior_protocol.anchor_id == protocol.anchor_id
                    and prior_protocol.goal_id == protocol.goal_id
                    and prior_protocol.task_id == protocol.task_id
                    and prior_protocol.competence_id == protocol.competence_id
                    and prior_protocol.binding_revision == protocol.binding_revision
                    and prior_protocol.scope_fingerprint == protocol.scope_fingerprint
                    and prior_protocol.protected_horizon_id == protocol.protected_horizon_id
                ):
                    prior_protocols.append(
                        (prior_sequence, prior_plan.effect_request_id, prior_protocol)
                    )
            latest_prior = max(prior_protocols, default=None, key=lambda item: item[0])
            if latest_prior is None:
                if protocol.continuity_kind != "new_episode":
                    resolution_issues.append("continuity_predecessor_missing")
            elif protocol.continuity_kind != "continue":
                resolution_issues.append("continuity_predecessor_omitted")
            else:
                try:
                    assert protocol.predecessor_handoff_artifact is not None
                    predecessor = CognitiveHandoff.model_validate_json(
                        self.artifacts.get_bytes(protocol.predecessor_handoff_artifact),
                        strict=True,
                    )
                    if (
                        predecessor.source_inquiry_id != inquiry_id
                        or predecessor.effect_request_id != latest_prior[1]
                        or predecessor.source_sequence >= request_sequence
                    ):
                        raise ValueError("foreign predecessor")
                    resolved_predecessor = self._evaluate_capability_request(
                        inquiry_id,
                        predecessor.effect_request_id,
                        through_sequence=predecessor.source_sequence,
                    ).handoff
                    if predecessor != resolved_predecessor:
                        raise ValueError("stale predecessor")
                    prior_protocol = latest_prior[2]
                    continuity_fields = (
                        "anchor_fingerprint",
                        "goal_fingerprint",
                        "task_id",
                        "competence_id",
                        "operation_id",
                        "effect_kind",
                        "binding_revision",
                        "scope_fingerprint",
                        "protected_horizon_id",
                        "context_artifact",
                        "evidence_access_artifact",
                        "budget_artifact",
                        "timeout_seconds",
                        "comparison_policy_id",
                        "comparison_policy_version",
                        "protected_capability_ids",
                    )
                    if any(
                        getattr(prior_protocol, field) != getattr(protocol, field)
                        for field in continuity_fields
                    ):
                        raise ValueError("changed predecessor pins")
                    if prior_protocol.expectations != protocol.expectations:
                        raise ValueError("changed predecessor expectations")
                    if protocol.continuation_discriminator_id != predecessor.next_discriminator_id:
                        raise ValueError("changed predecessor discriminator")
                    repeated_requirements: set[str] = set()
                    if protocol.route_definition_id in predecessor.forbidden_route_ids_until_reopen:
                        repeated_requirements.add(f"reopen-route:{protocol.route_definition_id}")
                    if protocol.decoder_id in predecessor.forbidden_decoder_ids_until_reopen:
                        repeated_requirements.add(f"reopen-decoder:{protocol.decoder_id}")
                    if (
                        protocol.route_definition_id
                        not in predecessor.forbidden_route_ids_until_reopen
                        and protocol.route_definition_id != predecessor.next_discriminator_route_id
                    ):
                        raise ValueError("wrong discriminator")
                    if protocol.reopening_evidence_artifacts and not repeated_requirements:
                        raise ValueError("irrelevant reopening evidence")
                    if not repeated_requirements.issubset(set(predecessor.reopening_condition_ids)):
                        raise ValueError("unsealed reopening target")
                    covered: set[str] = set()
                    for artifact, verdict_id in zip(
                        protocol.reopening_evidence_artifacts,
                        protocol.reopening_checker_verdict_ids,
                        strict=True,
                    ):
                        evidence_matches = tuple(
                            item for item in state.evidence_records if item.artifact == artifact
                        )
                        verdict = state.checker_verdict_by_id(verdict_id)
                        if len(evidence_matches) != 1 or verdict is None:
                            raise ValueError("unowned reopening evidence")
                        evidence = evidence_matches[0]
                        evidence_sequence = next(
                            (
                                stored.sequence
                                for stored in selected_events
                                if isinstance(stored.event, EvidenceRecorded)
                                and stored.event.evidence.id == evidence.id
                            ),
                            None,
                        )
                        verdict_sequence = next(
                            (
                                stored.sequence
                                for stored in selected_events
                                if isinstance(stored.event, CheckerVerdictRecorded)
                                and stored.event.checker_verdict.id == verdict.id
                            ),
                            None,
                        )
                        if (
                            evidence_sequence is None
                            or verdict_sequence is None
                            or not predecessor.source_sequence
                            < evidence_sequence
                            <= verdict_sequence
                            < request_sequence
                            or verdict.evidence_id != evidence.id
                            or verdict.evidence_artifact != evidence.artifact
                            or verdict.proposition_id != evidence.proposition_id
                            or verdict.verdict is not CheckerVerdict.VALID
                            or verdict.certificate_artifact is None
                            or state.context is None
                            or verdict.checker_id not in state.context.discharge_mechanism_ids
                            or verdict.checker_id == prior_protocol.actor_id
                            or verdict.checker_id == protocol.actor_id
                            or evidence.proposition_id not in repeated_requirements
                        ):
                            raise ValueError("invalid reopening evidence")
                        covered.add(evidence.proposition_id)
                    if covered != repeated_requirements:
                        raise ValueError("reopening coverage mismatch")
                except (ArtifactIntegrityError, ValidationError, ValueError):
                    resolution_issues.append("continuity_invalid")

        accepted_id = request_state.accepted_decoded_outcome_id
        accepted = next(
            (item for item in request_state.decode_outcomes if item.id == accepted_id), None
        )
        report: CapabilityConsequenceReport | None = None
        checker_evidence = None
        checker_verdict = None
        try:
            all_refs = [
                *tuple(_artifact_refs(protocol)),
                *tuple(_artifact_refs(actor_task)),
                *tuple(_artifact_refs(request_state)),
                protocol_artifact,
                actor_task_artifact,
            ]
            sizes_by_digest: dict[str, set[int]] = {}
            for artifact in all_refs:
                sizes_by_digest.setdefault(artifact.digest, set()).add(artifact.size)
            if any(len(sizes) != 1 for sizes in sizes_by_digest.values()):
                raise ValueError("conflicting artifact sizes share one digest")
            for artifact in all_refs:
                self.artifacts.verify(artifact)
            accepted = next(
                (item for item in request_state.decode_outcomes if item.id == accepted_id), None
            )
            report = (
                CapabilityConsequenceReport.model_validate_json(
                    self.artifacts.get_bytes(accepted.result.semantic_artifact), strict=True
                )
                if isinstance(accepted, Decoded)
                else None
            )
            if report is not None:
                report_refs = tuple(_artifact_refs(report))
                report_sizes: dict[str, set[int]] = {}
                for artifact in report_refs:
                    report_sizes.setdefault(artifact.digest, set()).add(artifact.size)
                if any(len(sizes) != 1 for sizes in report_sizes.values()):
                    raise ValueError("report contains conflicting artifact sizes")
                for artifact in report_refs:
                    self.artifacts.verify(artifact)
        except (ArtifactIntegrityError, ValidationError, ValueError):
            bundle = build_resolution_invalid_bundle(
                protocol=protocol,
                protocol_artifact=protocol_artifact,
                source_inquiry_id=inquiry_id,
                source_sequence=state.sequence,
                request_id=request_id,
                issue_codes=("artifact_missing_tampered_or_malformed",),
            )
            self._publish_capability_bundle(bundle)
            return bundle

        if isinstance(accepted, Decoded) and report is not None:
            evidence_candidates = tuple(
                item
                for item in state.evidence_records
                if item.artifact == accepted.result.semantic_artifact
                and item.proposition_id == f"capability-report:{report.id}"
                and item.proposition_kind.value == "relation"
                and item.scope_fingerprint == protocol.scope_fingerprint
            )
            if len(evidence_candidates) == 1:
                checker_evidence = evidence_candidates[0]
                verdict_candidates = tuple(
                    item
                    for item in state.checker_verdicts
                    if item.evidence_id == checker_evidence.id
                    and item.checker_id == protocol.checker_id
                    and item.checker_version == protocol.checker_version
                )
                if len(verdict_candidates) == 1:
                    checker_verdict = verdict_candidates[0]
                elif verdict_candidates:
                    resolution_issues.append("checker_verdict_ambiguous")
            elif evidence_candidates:
                resolution_issues.append("checker_evidence_ambiguous")

        checker_sequence: int | None = None
        if (
            isinstance(accepted, Decoded)
            and checker_evidence is not None
            and checker_verdict is not None
        ):
            return_sequence = next(
                (
                    stored.sequence
                    for stored in selected_events
                    if isinstance(stored.event, EffectAttemptOutcomeRecorded)
                    and stored.event.request_id == request_id
                    and isinstance(stored.event.outcome, ReturnedOutcome)
                    and stored.event.outcome.external_return.id == accepted.external_return_id
                ),
                None,
            )
            decode_sequence = next(
                (
                    stored.sequence
                    for stored in selected_events
                    if isinstance(stored.event, EffectDecodeOutcomeRecorded)
                    and stored.event.request_id == request_id
                    and stored.event.outcome.id == accepted.id
                ),
                None,
            )
            acceptance_sequence = next(
                (
                    stored.sequence
                    for stored in selected_events
                    if isinstance(stored.event, EffectResultAccepted)
                    and stored.event.request_id == request_id
                    and stored.event.decoded_outcome_id == accepted.id
                ),
                None,
            )
            evidence_sequence = next(
                (
                    stored.sequence
                    for stored in selected_events
                    if isinstance(stored.event, EvidenceRecorded)
                    and stored.event.evidence.id == checker_evidence.id
                ),
                None,
            )
            checker_sequence = next(
                (
                    stored.sequence
                    for stored in selected_events
                    if isinstance(stored.event, CheckerVerdictRecorded)
                    and stored.event.checker_verdict.id == checker_verdict.id
                ),
                None,
            )
            semantic_sequences = (
                return_sequence,
                decode_sequence,
                acceptance_sequence,
                evidence_sequence,
                checker_sequence,
            )
            if any(sequence is None for sequence in semantic_sequences):
                resolution_issues.append("semantic_antecedence_record_missing")
            else:
                assert return_sequence is not None
                assert decode_sequence is not None
                assert acceptance_sequence is not None
                assert evidence_sequence is not None
                assert checker_sequence is not None
                if not (
                    return_sequence
                    < decode_sequence
                    <= acceptance_sequence
                    < evidence_sequence
                    < checker_sequence
                ):
                    resolution_issues.append("checker_not_subsequent_to_accepted_return")

        if resolution_issues:
            bundle = build_resolution_invalid_bundle(
                protocol=protocol,
                protocol_artifact=protocol_artifact,
                source_inquiry_id=inquiry_id,
                source_sequence=state.sequence,
                request_id=request_id,
                issue_codes=tuple(resolution_issues),
            )
            self._publish_capability_bundle(bundle)
            return bundle

        owned_mismatches = tuple(
            item for item in state.mismatches if item.prediction_id == prediction.id
        )
        classifications = tuple(item.classification for item in owned_mismatches)
        if len(set(classifications)) != len(classifications):
            bundle = build_resolution_invalid_bundle(
                protocol=protocol,
                protocol_artifact=protocol_artifact,
                source_inquiry_id=inquiry_id,
                source_sequence=state.sequence,
                request_id=request_id,
                issue_codes=("duplicate_mismatch_classification",),
            )
            self._publish_capability_bundle(bundle)
            return bundle
        if owned_mismatches:
            mismatch_sequences = tuple(
                next(
                    (
                        stored.sequence
                        for stored in selected_events
                        if isinstance(stored.event, MismatchRecorded)
                        and stored.event.mismatch.id == mismatch.id
                    ),
                    None,
                )
                for mismatch in owned_mismatches
            )
            if checker_sequence is None or any(
                sequence is None or sequence <= checker_sequence for sequence in mismatch_sequences
            ):
                bundle = build_resolution_invalid_bundle(
                    protocol=protocol,
                    protocol_artifact=protocol_artifact,
                    source_inquiry_id=inquiry_id,
                    source_sequence=state.sequence,
                    request_id=request_id,
                    issue_codes=("mismatch_not_subsequent_to_check",),
                )
                self._publish_capability_bundle(bundle)
                return bundle

        owned_refs = tuple(
            _artifact_refs(
                (
                    anchor,
                    state.context,
                    goal,
                    obligation,
                    step_plan,
                    cognitive_plan,
                    prediction,
                    checker_evidence,
                    checker_verdict,
                    owned_mismatches,
                )
            )
        )
        owned_sizes: dict[str, set[int]] = {}
        for artifact in owned_refs:
            owned_sizes.setdefault(artifact.digest, set()).add(artifact.size)
        if any(len(sizes) != 1 for sizes in owned_sizes.values()):
            bundle = build_resolution_invalid_bundle(
                protocol=protocol,
                protocol_artifact=protocol_artifact,
                source_inquiry_id=inquiry_id,
                source_sequence=state.sequence,
                request_id=request_id,
                issue_codes=("conflicting_owned_artifact_sizes",),
            )
            self._publish_capability_bundle(bundle)
            return bundle
        try:
            for artifact in owned_refs:
                self.artifacts.verify(artifact)
            episode = CapabilityEvaluationEpisode(
                source_inquiry_id=inquiry_id,
                source_sequence=state.sequence,
                protocol=protocol,
                protocol_artifact=protocol_artifact,
                actor_task=actor_task,
                actor_task_artifact=actor_task_artifact,
                inquiry_context=state.context,
                project_anchor=anchor,
                implementation_goal=goal,
                obligation=obligation,
                step_plan=step_plan,
                cognitive_plan=cognitive_plan,
                effect=request_state,
                prediction=prediction,
                checker_evidence=checker_evidence,
                checker_verdict=checker_verdict,
                mismatches=owned_mismatches,
            )
        except (ArtifactIntegrityError, ValidationError, ValueError):
            bundle = build_resolution_invalid_bundle(
                protocol=protocol,
                protocol_artifact=protocol_artifact,
                source_inquiry_id=inquiry_id,
                source_sequence=state.sequence,
                request_id=request_id,
                issue_codes=("owned_projection_invalid",),
            )
            self._publish_capability_bundle(bundle)
            return bundle
        bundle = build_capability_evaluation_bundle(
            protocol=protocol, episode=episode, report=report
        )
        self._publish_capability_bundle(bundle)
        return bundle

    def evaluate_capability_request(
        self, inquiry_id: str, request_id: str
    ) -> CapabilityEvaluationBundle:
        """Evaluate one request only from the inquiry's current authoritative ledger."""

        return self._evaluate_capability_request(inquiry_id, request_id)

    def capability_handoff(self, inquiry_id: str, request_id: str) -> CognitiveHandoff:
        """Return only the canonical context-reset handoff for one exact episode."""

        return self.evaluate_capability_request(inquiry_id, request_id).handoff

    def evaluate_weak_reasoner_fixture(
        self,
        *,
        baseline_sources: tuple[tuple[str, str], ...],
        assisted_sources: tuple[tuple[str, str], ...],
    ) -> WeakReasonerFixture:
        """Compare only canonical stream/request sources resolved by this SDK."""

        def resolve(
            sources: tuple[tuple[str, str], ...],
        ) -> tuple[
            tuple[InquiryState, ...],
            tuple[CapabilityEvaluationProtocol, ...],
            tuple[CapabilityEvaluationBundle, ...],
        ]:
            if len(set(sources)) != len(sources):
                raise ValueError("weak-reasoner sources must be unique")
            states: list[InquiryState] = []
            protocols: list[CapabilityEvaluationProtocol] = []
            bundles: list[CapabilityEvaluationBundle] = []
            for inquiry_id, request_id in sources:
                bundle = self.evaluate_capability_request(inquiry_id, request_id)
                protocol = CapabilityEvaluationProtocol.model_validate_json(
                    self.artifacts.get_bytes(bundle.handoff.protocol_artifact), strict=True
                )
                states.append(self.inspect(inquiry_id))
                protocols.append(protocol)
                bundles.append(bundle)
            return tuple(states), tuple(protocols), tuple(bundles)

        baseline_states, baseline_protocols, baseline_bundles = resolve(baseline_sources)
        assisted_states, assisted_protocols, assisted_bundles = resolve(assisted_sources)
        return _build_weak_reasoner_fixture(
            baseline_states=baseline_states,
            assisted_states=assisted_states,
            baseline_protocols=baseline_protocols,
            assisted_protocols=assisted_protocols,
            baseline_bundles=baseline_bundles,
            assisted_bundles=assisted_bundles,
        )

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
