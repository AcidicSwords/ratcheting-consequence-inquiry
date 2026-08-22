import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier

import pytest

from rci.claims import BoundArgument, Obligation, ObligationKind, Scope
from rci.core import (
    AcceptEffectResult,
    AttemptKey,
    CapturedPayload,
    Decoded,
    DomainCommand,
    DomainEvent,
    EffectAttemptPlan,
    EffectRequest,
    ExternalReturn,
    InquiryContext,
    InquiryState,
    OpenObligation,
    PlanEffectAttempt,
    PlanReason,
    PlanStatus,
    RecordAttemptOutcome,
    RecordDecodeOutcome,
    RecordStepPlan,
    RequestEffect,
    ReturnedOutcome,
    RouteSnapshot,
    StartEffectAttempt,
    StartInquiry,
    SuccessResult,
    TransformEvidence,
    UnknownResult,
    build_step_plan,
    decide,
    evolve,
    initial_state,
)
from rci.core.errors import InvalidTransitionError
from rci.core.events import EffectAttemptPlanned, EffectRequested, EffectResultAccepted
from rci.core.model import ArtifactRef
from rci.persistence import (
    DATABASE_SCHEMA_VERSION,
    FOLDED_STATE_SCHEMA_VERSION,
    ArtifactIntegrityError,
    ArtifactStore,
    DuplicateEventError,
    OptimisticConcurrencyError,
    SQLiteEventStore,
    UnsupportedSchemaVersionError,
)

BASE_TIME = datetime(2026, 1, 1, tzinfo=UTC)


def build_history(
    artifacts: ArtifactStore,
) -> tuple[tuple[DomainEvent, ...], tuple[InquiryState, ...], ArtifactRef]:
    input_artifact = artifacts.put_bytes(b"effect input")
    definition_artifact = artifacts.put_bytes(b"route definition")
    environment_artifact = artifacts.put_bytes(b"python=3.12")
    transform_input = artifacts.put_bytes(b"untransformed")
    transform_output = artifacts.put_bytes(b"transformed")
    raw_return = artifacts.put_bytes(b'{"answer":null}', media_type="application/json")
    semantic = artifacts.put_bytes(b'{"kind":"unknown"}', media_type="application/json")
    manifest = artifacts.put_bytes(b'{"schema":"rci.inquiry-manifest.v1"}')
    scope = Scope(id="scope-1", binding_revision="binding-1")
    obligation = Obligation(
        id="obligation-1",
        kind=ObligationKind.CHARACTERIZE,
        carrier_id="carrier-1",
        args=(BoundArgument(name="target", value="carrier-1"),),
        scope=scope,
        binding_revision=scope.binding_revision,
    )
    step_plan = build_step_plan(
        input_fingerprint="3" * 64,
        policy_version="scheduler-1",
        status=PlanStatus.READY,
        selected_obligation_id=obligation.id,
        selected_attempt_key=AttemptKey(
            obligation_fingerprint=obligation.fingerprint,
            contract_id="contract-1",
            contract_version="1",
            binding_revision=obligation.binding_revision,
        ),
        reason=PlanReason.DETERMINISTIC_PRIORITY,
        remaining_budget=99,
    )

    route = RouteSnapshot(
        id="route-1",
        definition_id="route-definition-1",
        definition_version="1.0",
        definition_artifact=definition_artifact,
        backend_id="backend-1",
        adapter_id="adapter-1",
        adapter_version="1.0",
        execution_environment_artifact=environment_artifact,
        request_or_action_digest="e" * 64,
        transform_evidence=(
            TransformEvidence(
                id="transform-1",
                version="1.0",
                input_artifact=transform_input,
                output_artifact=transform_output,
            ),
        ),
    )
    request = EffectRequest(
        id="request-1",
        step_plan_id=step_plan.id,
        effect_kind="probe",
        adapter_id="adapter-1",
        input_artifact=input_artifact,
    )
    plan = EffectAttemptPlan(id="attempt-1", request_id=request.id, route=route)
    returned = ReturnedOutcome(
        attempt_id=plan.id,
        route_id=route.id,
        external_return=ExternalReturn(
            id="return-1",
            attempt_id=plan.id,
            route_id=route.id,
            capture_boundary="test-backend-return",
            capture_encoding="binary",
            captured_at=BASE_TIME,
            raw_payload=CapturedPayload(kind="bytes", artifact=raw_return),
        ),
    )
    decoded = Decoded(
        id="decode-1",
        external_return_id="return-1",
        decoder_id="decoder-1",
        decoder_version="1.0",
        result=UnknownResult(
            id="result-1",
            semantic_artifact=semantic,
            reason_kind="backend_unknown",
        ),
    )
    commands = (
        StartInquiry(
            event_id="event-start",
            inquiry_id="inquiry-1",
            occurred_at=BASE_TIME,
            manifest_artifact=manifest,
            policy_version="policy-1",
            context=InquiryContext(
                binding_revision="binding-1",
                carrier_schema_ids=("carrier-1",),
                relation_schema_ids=("relation-1",),
                consequence_profile_id="consequence-1",
                protected_horizon_id="horizon-1",
                scope_id="scope-1",
                scope_fingerprint=scope.fingerprint,
                catalog_manifest_digest=manifest.digest,
                scheduler_policy_version="scheduler-1",
                warrant_policy_version="warrant-1",
                provenance_refs=("test",),
            ),
        ),
        OpenObligation(
            event_id="event-obligation",
            inquiry_id="inquiry-1",
            occurred_at=BASE_TIME + timedelta(milliseconds=1),
            obligation=obligation,
        ),
        RecordStepPlan(
            event_id="event-step-plan",
            inquiry_id="inquiry-1",
            occurred_at=BASE_TIME + timedelta(milliseconds=2),
            plan=step_plan,
        ),
        RequestEffect(
            event_id="event-request",
            inquiry_id="inquiry-1",
            occurred_at=BASE_TIME + timedelta(seconds=1),
            request=request,
        ),
        PlanEffectAttempt(
            event_id="event-plan",
            inquiry_id="inquiry-1",
            occurred_at=BASE_TIME + timedelta(seconds=2),
            plan=plan,
        ),
        StartEffectAttempt(
            event_id="event-start-attempt",
            inquiry_id="inquiry-1",
            occurred_at=BASE_TIME + timedelta(seconds=3),
            attempt_id=plan.id,
        ),
        RecordAttemptOutcome(
            event_id="event-return",
            inquiry_id="inquiry-1",
            occurred_at=BASE_TIME + timedelta(seconds=4),
            request_id=request.id,
            outcome=returned,
        ),
        RecordDecodeOutcome(
            event_id="event-decode",
            inquiry_id="inquiry-1",
            occurred_at=BASE_TIME + timedelta(seconds=5),
            request_id=request.id,
            outcome=decoded,
        ),
        AcceptEffectResult(
            event_id="event-accept",
            inquiry_id="inquiry-1",
            occurred_at=BASE_TIME + timedelta(seconds=6),
            request_id=request.id,
            decoded_outcome_id=decoded.id,
        ),
    )
    state = initial_state()
    events: list[DomainEvent] = []
    states: list[InquiryState] = []
    for command in commands:
        decided = decide(state, command)
        events.extend(decided)
        for event in decided:
            state = evolve(state, event)
            states.append(state)
    return tuple(events), tuple(states), raw_return


def test_wal_occ_replay_and_deterministic_export(tmp_path: Path) -> None:
    artifacts = ArtifactStore(tmp_path / "artifacts")
    events, states, _ = build_history(artifacts)
    store = SQLiteEventStore(tmp_path / "state.sqlite3", artifact_store=artifacts)

    assert store.journal_mode() == "wal"
    assert store.append("inquiry-1", 0, events) == len(events)
    assert store.append("inquiry-1", len(events), ()) == len(events)
    assert store.rebuild_state("inquiry-1") == states[-1]
    assert store.rebuild_state("inquiry-1", use_snapshot=False) == states[-1]
    assert store.export_stream("inquiry-1") == store.export_stream("inquiry-1")

    second_writer = SQLiteEventStore(tmp_path / "state.sqlite3", artifact_store=artifacts)
    with pytest.raises(OptimisticConcurrencyError):
        second_writer.append("inquiry-1", 0, ())


def test_two_writers_race_from_the_same_expected_sequence(tmp_path: Path) -> None:
    artifacts = ArtifactStore(tmp_path / "artifacts")
    events, _, _ = build_history(artifacts)
    database = tmp_path / "state.sqlite3"
    writers = (
        SQLiteEventStore(database, artifact_store=artifacts),
        SQLiteEventStore(database, artifact_store=artifacts),
    )
    starts = (
        events[0],
        events[0].model_copy(update={"event_id": "event-start-racing-writer"}),
    )
    barrier = Barrier(2)

    def race(index: int) -> int | str:
        barrier.wait()
        try:
            return writers[index].append("inquiry-1", 0, (starts[index],))
        except OptimisticConcurrencyError:
            return "typed_conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(race, range(2)))

    assert sorted(results, key=str) == [1, "typed_conflict"]
    committed = writers[0].load_stream("inquiry-1")
    assert committed.version == 1
    assert committed.events[0].event.event_id in {event.event_id for event in starts}


def test_append_folds_lifecycle_before_inserting_any_rows(tmp_path: Path) -> None:
    artifacts = ArtifactStore(tmp_path / "artifacts")
    events, _, _ = build_history(artifacts)
    store = SQLiteEventStore(tmp_path / "state.sqlite3", artifact_store=artifacts)

    with pytest.raises(InvalidTransitionError, match="active aggregate"):
        store.append("inquiry-1", 0, (events[1],))
    assert store.stream_version("inquiry-1") == 0

    store.append("inquiry-1", 0, (events[0],))
    with pytest.raises(InvalidTransitionError, match="unknown request"):
        store.append("inquiry-1", 1, (events[4],))
    assert store.stream_version("inquiry-1") == 1
    assert store.rebuild_state("inquiry-1").sequence == 1


def test_published_artifact_survives_a_rejected_event_as_recoverable_orphan(
    tmp_path: Path,
) -> None:
    artifacts = ArtifactStore(tmp_path / "artifacts")
    events, _, _ = build_history(artifacts)
    orphan = artifacts.put_bytes(b"published-before-failed-append")
    request_event = events[3]
    assert isinstance(request_event, EffectRequested)
    orphan_request = request_event.request.model_copy(update={"input_artifact": orphan})
    orphan_event = request_event.model_copy(update={"request": orphan_request})
    database = tmp_path / "state.sqlite3"
    store = SQLiteEventStore(database, artifact_store=artifacts)

    with pytest.raises(InvalidTransitionError):
        store.append("inquiry-1", 0, (orphan_event,))

    reopened_artifacts = ArtifactStore(tmp_path / "artifacts")
    reopened_store = SQLiteEventStore(database, artifact_store=reopened_artifacts)
    assert reopened_artifacts.get_bytes(orphan) == b"published-before-failed-append"
    assert reopened_store.stream_version("inquiry-1") == 0
    assert orphan.digest.encode() not in reopened_store.export_stream("inquiry-1")


def test_snapshot_and_projection_are_rebuildable(tmp_path: Path) -> None:
    artifacts = ArtifactStore(tmp_path / "artifacts")
    events, states, _ = build_history(artifacts)
    store = SQLiteEventStore(tmp_path / "state.sqlite3", artifact_store=artifacts)

    split = 3
    store.append("inquiry-1", 0, events[:split])
    snapshot = store.save_snapshot("inquiry-1", states[split - 1])
    assert snapshot.sequence == split
    assert snapshot.fold_schema_version == FOLDED_STATE_SCHEMA_VERSION
    assert snapshot.source_event_digest == store.stream_prefix_digest(
        "inquiry-1", through_sequence=split
    )
    store.append("inquiry-1", split, events[split:])
    assert store.rebuild_state("inquiry-1") == states[-1]

    def append_kind(current: tuple[str, ...], event: DomainEvent) -> tuple[str, ...]:
        return (*current, event.kind)

    initial_kinds: tuple[str, ...] = ()
    kinds = store.rebuild_projection(
        "inquiry-1",
        initial=initial_kinds,
        apply=append_kind,
    )
    payload = "\n".join(kinds).encode()
    checkpoint = store.save_projection_checkpoint(
        "event-kinds",
        "1.0.0",
        "inquiry-1",
        len(events),
        payload,
    )
    assert (
        store.load_latest_projection_checkpoint("event-kinds", "1.0.0", "inquiry-1") == checkpoint
    )
    assert store.load_latest_projection_checkpoint("event-kinds", "2.0.0", "inquiry-1") is None


def test_stream_prefix_digest_is_ordered_bounded_and_stable(tmp_path: Path) -> None:
    artifacts = ArtifactStore(tmp_path / "artifacts")
    events, _, _ = build_history(artifacts)
    store = SQLiteEventStore(tmp_path / "state.sqlite3", artifact_store=artifacts)
    store.append("inquiry-1", 0, events)

    first = store.stream_prefix_digest("inquiry-1", through_sequence=1)
    complete = store.stream_prefix_digest("inquiry-1")
    assert first == store.stream_prefix_digest("inquiry-1", through_sequence=1)
    assert complete == store.stream_prefix_digest("inquiry-1", through_sequence=len(events))
    assert first != complete
    with pytest.raises(ValueError, match="outside the event stream"):
        store.stream_prefix_digest("inquiry-1", through_sequence=len(events) + 1)


def test_v1_snapshot_is_discarded_and_rebuilt_without_changing_ledger_or_projection(
    tmp_path: Path,
) -> None:
    artifacts = ArtifactStore(tmp_path / "artifacts")
    events, states, _ = build_history(artifacts)
    database = tmp_path / "state.sqlite3"
    store = SQLiteEventStore(database, artifact_store=artifacts)
    store.append("inquiry-1", 0, events)
    original_export = store.export_stream("inquiry-1")
    snapshot = store.save_snapshot("inquiry-1", states[-1])
    checkpoint = store.save_projection_checkpoint(
        "event-kinds",
        "1.0.0",
        "inquiry-1",
        len(events),
        b"g1-projection",
    )

    # Recreate the exact G1 snapshot shape while leaving the authoritative ledger
    # and the separately versioned projection checkpoint untouched.
    with sqlite3.connect(database) as connection:
        connection.execute("DROP TRIGGER snapshots_forbid_update")
        connection.execute("ALTER TABLE snapshots RENAME TO snapshots_v2")
        connection.execute(
            """
            CREATE TABLE snapshots (
                stream_id TEXT NOT NULL,
                sequence INTEGER NOT NULL CHECK (sequence >= 1),
                state_bytes BLOB NOT NULL,
                state_digest TEXT NOT NULL,
                PRIMARY KEY (stream_id, sequence),
                FOREIGN KEY (stream_id) REFERENCES streams(stream_id)
            )
            """
        )
        connection.execute(
            """
            INSERT INTO snapshots(stream_id, sequence, state_bytes, state_digest)
            SELECT stream_id, sequence, state_bytes, state_digest FROM snapshots_v2
            """
        )
        connection.execute("DROP TABLE snapshots_v2")
        connection.execute(
            """
            CREATE TRIGGER snapshots_forbid_update
            BEFORE UPDATE ON snapshots
            BEGIN
                SELECT RAISE(ABORT, 'snapshots are immutable');
            END
            """
        )
        connection.execute("PRAGMA user_version = 1")

    reopened = SQLiteEventStore(database, artifact_store=artifacts)
    assert DATABASE_SCHEMA_VERSION == 2
    assert reopened.export_stream("inquiry-1") == original_export
    assert reopened.load_latest_snapshot("inquiry-1") is None
    assert reopened.rebuild_state("inquiry-1") == states[-1]
    assert (
        reopened.load_latest_projection_checkpoint("event-kinds", "1.0.0", "inquiry-1")
        == checkpoint
    )

    rebuilt_snapshot = reopened.save_snapshot("inquiry-1", states[-1])
    assert rebuilt_snapshot.fold_schema_version == FOLDED_STATE_SCHEMA_VERSION
    assert rebuilt_snapshot.source_event_digest == snapshot.source_event_digest


def test_g2a_fold_v2_snapshot_is_rebuilt_as_v3_without_changing_events(
    tmp_path: Path,
) -> None:
    artifacts = ArtifactStore(tmp_path / "artifacts")
    events, states, _ = build_history(artifacts)
    database = tmp_path / "state.sqlite3"
    store = SQLiteEventStore(database, artifact_store=artifacts)
    store.append("inquiry-1", 0, events)
    original_export = store.export_stream("inquiry-1")
    store.save_snapshot("inquiry-1", states[-1])

    with sqlite3.connect(database) as connection:
        connection.execute("DROP TRIGGER snapshots_forbid_update")
        connection.execute(
            "UPDATE snapshots SET fold_schema_version = ? WHERE stream_id = ?",
            ("rci.inquiry-state.v2", "inquiry-1"),
        )
        connection.execute(
            """
            CREATE TRIGGER snapshots_forbid_update
            BEFORE UPDATE ON snapshots
            BEGIN
                SELECT RAISE(ABORT, 'snapshots are immutable');
            END
            """
        )

    reopened = SQLiteEventStore(database, artifact_store=artifacts)
    assert reopened.load_latest_snapshot("inquiry-1") is None
    assert reopened.rebuild_state("inquiry-1") == states[-1]
    assert reopened.export_stream("inquiry-1") == original_export
    rebuilt = reopened.save_snapshot("inquiry-1", states[-1])
    assert rebuilt.fold_schema_version == "rci.inquiry-state.v3"


def test_failed_batch_rolls_back_and_resume_is_consistent(tmp_path: Path) -> None:
    artifacts = ArtifactStore(tmp_path / "artifacts")
    events, states, _ = build_history(artifacts)
    database = tmp_path / "state.sqlite3"
    store = SQLiteEventStore(database, artifact_store=artifacts)
    store.append("inquiry-1", 0, events[:1])

    duplicate = events[2].model_copy(update={"event_id": events[0].event_id})
    with pytest.raises(DuplicateEventError):
        store.append("inquiry-1", 1, (events[1], duplicate))

    reopened = SQLiteEventStore(database, artifact_store=artifacts)
    assert reopened.stream_version("inquiry-1") == 1
    assert reopened.rebuild_state("inquiry-1") == states[0]


def test_late_competing_return_is_durable_but_cannot_replace_first_acceptance(
    tmp_path: Path,
) -> None:
    artifacts = ArtifactStore(tmp_path / "artifacts")
    base_events, _, _ = build_history(artifacts)
    request_event = base_events[3]
    first_plan_event = base_events[4]
    assert isinstance(request_event, EffectRequested)
    assert isinstance(first_plan_event, EffectAttemptPlanned)
    request = request_event.request
    first_plan = first_plan_event.plan
    second_plan = EffectAttemptPlan(
        id="attempt-late",
        request_id=request.id,
        route=first_plan.route.model_copy(update={"id": "route-late"}),
    )
    first_raw = artifacts.put_bytes(b"first", media_type="application/octet-stream")
    late_raw = artifacts.put_bytes(b"late", media_type="application/octet-stream")
    first_semantic = artifacts.put_bytes(b'{"winner":"first"}')
    late_semantic = artifacts.put_bytes(b'{"winner":"late"}')
    first_return = ReturnedOutcome(
        attempt_id=first_plan.id,
        route_id=first_plan.route.id,
        external_return=ExternalReturn(
            id="return-first",
            attempt_id=first_plan.id,
            route_id=first_plan.route.id,
            capture_boundary="test-backend-return",
            capture_encoding="binary",
            captured_at=BASE_TIME,
            raw_payload=CapturedPayload(kind="bytes", artifact=first_raw),
        ),
    )
    late_return = ReturnedOutcome(
        attempt_id=second_plan.id,
        route_id=second_plan.route.id,
        external_return=ExternalReturn(
            id="return-late",
            attempt_id=second_plan.id,
            route_id=second_plan.route.id,
            capture_boundary="test-backend-return",
            capture_encoding="binary",
            captured_at=BASE_TIME,
            raw_payload=CapturedPayload(kind="bytes", artifact=late_raw),
        ),
    )
    first_decode = Decoded(
        id="decode-first",
        external_return_id=first_return.external_return.id,
        decoder_id="decoder-1",
        decoder_version="1.0",
        result=SuccessResult(
            id="result-first",
            semantic_artifact=first_semantic,
            operation_id="test_result",
        ),
    )
    late_decode = Decoded(
        id="decode-late",
        external_return_id=late_return.external_return.id,
        decoder_id="decoder-1",
        decoder_version="1.0",
        result=SuccessResult(
            id="result-late",
            semantic_artifact=late_semantic,
            operation_id="test_result",
        ),
    )

    prefix = base_events[:4]
    state = initial_state()
    for event in prefix:
        state = evolve(state, event)

    def fold_commands(
        current: InquiryState,
        commands: tuple[DomainCommand, ...],
    ) -> tuple[InquiryState, tuple[DomainEvent, ...]]:
        generated: list[DomainEvent] = []
        for command in commands:
            command_events = decide(current, command)
            generated.extend(command_events)
            for event in command_events:
                current = evolve(current, event)
        return current, tuple(generated)

    first_commands: tuple[DomainCommand, ...] = (
        PlanEffectAttempt(
            event_id="event-plan-first",
            inquiry_id="inquiry-1",
            occurred_at=BASE_TIME + timedelta(seconds=2),
            plan=first_plan,
        ),
        PlanEffectAttempt(
            event_id="event-plan-late",
            inquiry_id="inquiry-1",
            occurred_at=BASE_TIME + timedelta(seconds=3),
            plan=second_plan,
        ),
        StartEffectAttempt(
            event_id="event-start-first",
            inquiry_id="inquiry-1",
            occurred_at=BASE_TIME + timedelta(seconds=4),
            attempt_id=first_plan.id,
        ),
        StartEffectAttempt(
            event_id="event-start-late",
            inquiry_id="inquiry-1",
            occurred_at=BASE_TIME + timedelta(seconds=5),
            attempt_id=second_plan.id,
        ),
        RecordAttemptOutcome(
            event_id="event-return-first",
            inquiry_id="inquiry-1",
            occurred_at=BASE_TIME + timedelta(seconds=6),
            request_id=request.id,
            outcome=first_return,
        ),
        RecordDecodeOutcome(
            event_id="event-decode-first",
            inquiry_id="inquiry-1",
            occurred_at=BASE_TIME + timedelta(seconds=7),
            request_id=request.id,
            outcome=first_decode,
        ),
        AcceptEffectResult(
            event_id="event-accept-first",
            inquiry_id="inquiry-1",
            occurred_at=BASE_TIME + timedelta(seconds=8),
            request_id=request.id,
            decoded_outcome_id=first_decode.id,
        ),
    )
    state, first_events = fold_commands(state, first_commands)
    state_after_first = state
    late_commands: tuple[DomainCommand, ...] = (
        RecordAttemptOutcome(
            event_id="event-return-late",
            inquiry_id="inquiry-1",
            occurred_at=BASE_TIME + timedelta(seconds=9),
            request_id=request.id,
            outcome=late_return,
        ),
        RecordDecodeOutcome(
            event_id="event-decode-late",
            inquiry_id="inquiry-1",
            occurred_at=BASE_TIME + timedelta(seconds=10),
            request_id=request.id,
            outcome=late_decode,
        ),
    )
    state, late_events = fold_commands(state, late_commands)

    store = SQLiteEventStore(tmp_path / "state.sqlite3", artifact_store=artifacts)
    first_version = store.append("inquiry-1", 0, (*prefix, *first_events))
    assert store.rebuild_state("inquiry-1") == state_after_first
    late_version = store.append("inquiry-1", first_version, late_events)
    assert store.rebuild_state("inquiry-1") == state

    persisted = state.request_by_id(request.id)
    assert persisted is not None
    assert persisted.accepted_decoded_outcome_id == first_decode.id
    assert isinstance(persisted.attempts[1].outcome, ReturnedOutcome)
    assert persisted.attempts[1].outcome.external_return.id == late_return.external_return.id
    assert any(outcome.id == late_decode.id for outcome in persisted.decode_outcomes)

    forged_replacement = EffectResultAccepted(
        event_id="event-accept-late",
        inquiry_id="inquiry-1",
        occurred_at=BASE_TIME + timedelta(seconds=11),
        request_id=request.id,
        decoded_outcome_id=late_decode.id,
    )
    with pytest.raises(InvalidTransitionError, match="already accepted"):
        store.append("inquiry-1", late_version, (forged_replacement,))
    assert store.stream_version("inquiry-1") == late_version
    assert store.rebuild_state("inquiry-1") == state


def test_dangling_route_artifact_is_rejected_before_commit(tmp_path: Path) -> None:
    artifacts = ArtifactStore(tmp_path / "artifacts")
    events, _, _ = build_history(artifacts)
    store = SQLiteEventStore(tmp_path / "state.sqlite3", artifact_store=artifacts)
    store.append("inquiry-1", 0, events[:4])

    plan_event = events[4]
    assert isinstance(plan_event, EffectAttemptPlanned)
    missing = ArtifactRef(digest="f" * 64, size=99)
    broken_route = plan_event.plan.route.model_copy(update={"definition_artifact": missing})
    broken_plan = plan_event.plan.model_copy(update={"route": broken_route})
    broken_event = plan_event.model_copy(update={"plan": broken_plan})

    with pytest.raises(ArtifactIntegrityError):
        store.append("inquiry-1", 4, (broken_event,))
    assert store.stream_version("inquiry-1") == 4


def test_artifact_tampering_blocks_replay(tmp_path: Path) -> None:
    artifacts = ArtifactStore(tmp_path / "artifacts")
    events, _, raw_return = build_history(artifacts)
    store = SQLiteEventStore(tmp_path / "state.sqlite3", artifact_store=artifacts)
    store.append("inquiry-1", 0, events)

    artifacts.path_for(raw_return).write_bytes(b"altered after commit")
    with pytest.raises(ArtifactIntegrityError):
        store.rebuild_state("inquiry-1")


def test_event_rows_are_append_only(tmp_path: Path) -> None:
    artifacts = ArtifactStore(tmp_path / "artifacts")
    events, _, _ = build_history(artifacts)
    database = tmp_path / "state.sqlite3"
    store = SQLiteEventStore(database, artifact_store=artifacts)
    store.append("inquiry-1", 0, events[:1])

    with sqlite3.connect(database) as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute("DELETE FROM events WHERE stream_id = ?", ("inquiry-1",))


def test_unknown_future_database_schema_fails_closed(tmp_path: Path) -> None:
    database = tmp_path / "future.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA user_version = 999")
    with pytest.raises(UnsupportedSchemaVersionError):
        SQLiteEventStore(database)
