"""Cognitive lifecycle validation over the authoritative core effect records."""

from __future__ import annotations

from enum import StrEnum

from pydantic import JsonValue, model_validator

from rci.claims.models import (
    BoundArgument,
    FrozenModel,
    Obligation,
    ObligationKind,
    Scope,
    content_fingerprint,
)
from rci.core.effects import (
    AttemptOutcome,
    CancelledOutcome,
    CaptureFailedOutcome,
    DecodeOutcome,
    EffectAttemptPlan,
    NoAttemptDisposition,
    NotPresentedOutcome,
    PresentationUnknownOutcome,
    ReturnedOutcome,
)
from rci.probes.models import (
    CognitiveAttemptPlan,
    PredictionSeal,
    Reconstruction,
    ReconstructionSet,
    SemanticDelta,
    WarrantedChange,
)
from rci.warrant.models import SupportRoute


class LifecycleVerdict(StrEnum):
    VALID = "valid"
    INVALID = "invalid"


class LifecycleCheck(FrozenModel):
    verdict: LifecycleVerdict
    violations: tuple[str, ...]

    @model_validator(mode="after")
    def validate_check(self) -> LifecycleCheck:
        if self.verdict is LifecycleVerdict.VALID and self.violations:
            raise ValueError("valid lifecycle checks cannot carry violations")
        if self.verdict is LifecycleVerdict.INVALID and not self.violations:
            raise ValueError("invalid lifecycle checks require violations")
        return self


def validate_cognitive_lifecycle(
    *,
    plan: CognitiveAttemptPlan,
    effect_plan: EffectAttemptPlan | None,
    outcome: AttemptOutcome | None,
    no_attempt: NoAttemptDisposition | None = None,
    seal: PredictionSeal | None = None,
    attempt_sequence: int | None = None,
    decode_outcomes: tuple[DecodeOutcome, ...] = (),
    reconstruction: Reconstruction | None = None,
    delta: SemanticDelta | None = None,
) -> LifecycleCheck:
    """Validate links/order without duplicating route, return, or decode authority."""

    violations: list[str] = []
    if seal is not None:
        if seal.cognitive_plan_id != plan.id or seal.probe_or_action_id != plan.probe_or_action_id:
            violations.append("prediction_plan_mismatch")
        if seal.sealed_sequence < plan.planned_sequence:
            violations.append("prediction_precedes_plan")
        if attempt_sequence is not None and seal.sealed_sequence >= attempt_sequence:
            violations.append("prediction_not_sealed_before_attempt")
    if no_attempt is not None:
        if no_attempt.request_id != plan.effect_request_id:
            violations.append("no_attempt_request_mismatch")
        if any(item is not None for item in (effect_plan, outcome, reconstruction, delta)):
            violations.append("no_attempt_has_downstream_objects")
        if decode_outcomes:
            violations.append("no_attempt_has_decode_outcomes")
        if plan.effect_attempt_plan_id is not None:
            violations.append("no_attempt_references_effect_attempt")
    else:
        if effect_plan is None:
            violations.append("missing_effect_attempt_plan")
        else:
            if plan.effect_attempt_plan_id != effect_plan.id:
                violations.append("effect_attempt_plan_mismatch")
            if effect_plan.request_id != plan.effect_request_id:
                violations.append("effect_request_mismatch")
        if outcome is None:
            violations.append("missing_attempt_outcome")
    returned = outcome if isinstance(outcome, ReturnedOutcome) else None
    if isinstance(
        outcome,
        (
            NotPresentedOutcome,
            CaptureFailedOutcome,
            PresentationUnknownOutcome,
            CancelledOutcome,
        ),
    ):
        if effect_plan is not None and outcome.route_id != effect_plan.route.id:
            violations.append("attempt_outcome_route_mismatch")
        if decode_outcomes or reconstruction is not None or delta is not None:
            violations.append("non_returned_outcome_has_return_pipeline")
    if returned is not None:
        if effect_plan is not None:
            if returned.attempt_id != effect_plan.id:
                violations.append("returned_attempt_mismatch")
            if returned.route_id != effect_plan.route.id:
                violations.append("returned_route_mismatch")
        if any(
            decoded.external_return_id != returned.external_return.id for decoded in decode_outcomes
        ):
            violations.append("decode_external_return_mismatch")
        if reconstruction is not None:
            if reconstruction.external_return_id != returned.external_return.id:
                violations.append("reconstruction_return_mismatch")
            if set(reconstruction.decode_outcome_ids) != {
                decoded.id for decoded in decode_outcomes
            }:
                violations.append("reconstruction_decode_set_mismatch")
        elif delta is not None:
            violations.append("semantic_delta_without_reconstruction")
        if delta is not None and reconstruction is not None:
            if delta.reconstruction_id != reconstruction.id:
                violations.append("semantic_delta_reconstruction_mismatch")
            if delta.committed_sequence <= reconstruction.reconstructed_sequence:
                violations.append("semantic_delta_not_after_reconstruction")
    elif outcome is not None and not isinstance(
        outcome,
        (
            NotPresentedOutcome,
            CaptureFailedOutcome,
            PresentationUnknownOutcome,
            CancelledOutcome,
        ),
    ):
        violations.append("unsupported_attempt_outcome")
    if len({decoded.id for decoded in decode_outcomes}) != len(decode_outcomes):
        violations.append("duplicate_decode_outcome_id")
    unique = tuple(dict.fromkeys(violations))
    return LifecycleCheck(
        verdict=LifecycleVerdict.INVALID if unique else LifecycleVerdict.VALID,
        violations=unique,
    )


def open_dependency_obligations(
    *,
    lemma_id: str,
    support_routes: tuple[SupportRoute, ...],
    scope: Scope,
) -> tuple[Obligation, ...]:
    """Expose every unresolved dependency once, even across alternate routes."""

    route_ids_by_dependency: dict[str, set[str]] = {}
    for route in support_routes:
        for dependency_id in route.open_dependency_ids:
            route_ids_by_dependency.setdefault(dependency_id, set()).add(route.id)
    obligations: list[Obligation] = []
    for dependency_id, route_ids in sorted(route_ids_by_dependency.items()):
        route_ids_json: JsonValue = list(sorted(route_ids))
        material = {
            "lemma": lemma_id,
            "dependency": dependency_id,
            "scope": scope.fingerprint,
        }
        obligations.append(
            Obligation(
                id=f"obl_{content_fingerprint('rci.open-dependency.v1', material)[:24]}",
                kind=ObligationKind.DISCHARGE_OPEN_DEPENDENCY,
                carrier_id=lemma_id,
                args=(
                    BoundArgument(name="dependency_id", value=dependency_id),
                    BoundArgument(name="support_route_ids", value=route_ids_json),
                ),
                scope=scope,
                binding_revision=scope.binding_revision,
                priority_vector=(100,),
            )
        )
    return tuple(obligations)


def ambiguity_obligation(
    reconstruction_set: ReconstructionSet,
    *,
    scope: Scope,
) -> Obligation | None:
    if reconstruction_set.resolved or not reconstruction_set.candidates:
        return None
    classes = tuple(sorted(reconstruction_set.consequence_class_ids))
    classes_json: JsonValue = list(classes)
    material = {
        "cue": reconstruction_set.cue_id,
        "horizon": reconstruction_set.protected_horizon_id,
        "classes": classes,
        "scope": scope.fingerprint,
    }
    return Obligation(
        id=f"obl_{content_fingerprint('rci.reconstruction-ambiguity.v1', material)[:24]}",
        kind=ObligationKind.DISCRIMINATE_RECONSTRUCTION,
        carrier_id=reconstruction_set.cue_id,
        args=(BoundArgument(name="consequence_class_ids", value=classes_json),),
        scope=scope,
        binding_revision=scope.binding_revision,
        priority_vector=(95,),
    )


def create_semantic_delta(
    *,
    delta_id: str,
    reconstruction: Reconstruction,
    warranted_changes: tuple[WarrantedChange, ...],
    reopened_structure_ids: tuple[str, ...] = (),
    retired_structure_ids: tuple[str, ...] = (),
    committed_sequence: int,
) -> SemanticDelta:
    """Commit only changes that name their independent warrant lemma."""

    if any(not change.warrant_lemma_id for change in warranted_changes):
        raise ValueError("every semantic change requires a warrant lemma")
    if committed_sequence <= reconstruction.reconstructed_sequence:
        raise ValueError("semantic commit must follow reconstruction")
    return SemanticDelta(
        id=delta_id,
        reconstruction_id=reconstruction.id,
        warranted_changes=warranted_changes,
        reopened_structure_ids=reopened_structure_ids,
        retired_structure_ids=retired_structure_ids,
        committed_sequence=committed_sequence,
    )
