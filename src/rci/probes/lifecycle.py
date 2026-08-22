"""Pure probe-trace and semantic-field transformations."""

from __future__ import annotations

from collections.abc import Iterable

from rci.claims.models import content_fingerprint
from rci.probes.models import (
    ComparabilityBridge,
    ProbeEvent,
    ProbeIdentity,
    ProbeTrace,
    RelevanceStatus,
    SemanticField,
    SemanticItem,
)


def compare_probe_events(
    left: ProbeEvent,
    right: ProbeEvent,
    *,
    bridge: ComparabilityBridge | None = None,
) -> bool:
    left_fingerprint = left.probe_identity.fingerprint
    right_fingerprint = right.probe_identity.fingerprint
    same_identity = left_fingerprint == right_fingerprint
    same_binding = left.binding_revision == right.binding_revision
    same_referents = left.bound_referents == right.bound_referents
    if same_identity and same_binding and same_referents:
        return True
    selected_bridge = bridge or right.comparability_bridge or left.comparability_bridge
    return selected_bridge is not None and selected_bridge.connects(
        left_fingerprint, right_fingerprint
    )


def append_probe_event(trace: ProbeTrace, event: ProbeEvent) -> ProbeTrace:
    if event.probe_identity.fingerprint != trace.probe_fingerprint:
        raise ValueError("event does not belong to this recurrent probe")
    if trace.events:
        previous = trace.events[-1]
        if event.sequence_index <= previous.sequence_index:
            raise ValueError("new probe event must follow the current trace tail")
        if not compare_probe_events(previous, event):
            raise ValueError("probe observations are not comparable without a bridge")
    return trace.model_copy(update={"events": (*trace.events, event)})


def build_semantic_field(
    *,
    probe_identity: ProbeIdentity,
    protected_horizon_id: str,
    items: Iterable[SemanticItem],
    same_probe_history_event_ids: Iterable[str] = (),
    cross_probe_trace_ids: Iterable[str] = (),
    retrieval_result_ids: Iterable[str] = (),
    method_contract_ids: Iterable[str] = (),
    reopening_condition_ids: Iterable[str] = (),
    authorized_irrelevance_warrant_ids: frozenset[str] = frozenset(),
) -> SemanticField:
    """Build a non-authoritative view from explicit, checked input references."""

    item_tuple = tuple(items)
    history_tuple = tuple(same_probe_history_event_ids)
    cross_probe_tuple = tuple(cross_probe_trace_ids)
    retrieval_tuple = tuple(retrieval_result_ids)
    method_tuple = tuple(method_contract_ids)
    reopening_tuple = tuple(reopening_condition_ids)
    requested_irrelevance = frozenset(
        item.irrelevance_warrant_id
        for item in item_tuple
        if item.relevance is RelevanceStatus.IRRELEVANT and item.irrelevance_warrant_id is not None
    )
    if not requested_irrelevance <= authorized_irrelevance_warrant_ids:
        raise ValueError("irrelevance requires an active checked consequence-null warrant")
    required_reopening = frozenset(
        item.reopening_condition_id
        for item in item_tuple
        if item.relevance is RelevanceStatus.IRRELEVANT and item.reopening_condition_id is not None
    )
    if not required_reopening <= frozenset(reopening_tuple):
        raise ValueError("irrelevance reopening conditions must be pinned by the field")
    material = {
        "probe": probe_identity.fingerprint,
        "horizon": protected_horizon_id,
        "items": [item.model_dump(mode="json") for item in item_tuple],
        "history": history_tuple,
        "cross_probe": cross_probe_tuple,
        "retrieval": retrieval_tuple,
        "methods": method_tuple,
        "reopening": reopening_tuple,
        "authorized_irrelevance_warrants": sorted(authorized_irrelevance_warrant_ids),
    }
    return SemanticField(
        id=f"field_{content_fingerprint('rci.semantic-field.v1', material)[:24]}",
        probe_fingerprint=probe_identity.fingerprint,
        protected_horizon_id=protected_horizon_id,
        items=item_tuple,
        same_probe_history_event_ids=history_tuple,
        cross_probe_trace_ids=cross_probe_tuple,
        retrieval_result_ids=retrieval_tuple,
        method_contract_ids=method_tuple,
        reopening_condition_ids=reopening_tuple,
    )


def reopen_semantic_item(item: SemanticItem, *, condition_id: str) -> SemanticItem:
    if item.relevance is not RelevanceStatus.IRRELEVANT:
        return item
    if item.reopening_condition_id != condition_id:
        return item
    return SemanticItem(
        structure_id=item.structure_id,
        relevance=RelevanceStatus.UNDETERMINED,
        reopening_condition_id=item.reopening_condition_id,
    )
