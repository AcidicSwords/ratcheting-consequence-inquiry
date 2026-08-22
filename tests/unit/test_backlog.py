from pathlib import Path

import pytest

from rci.backlog import (
    BacklogEffectKind,
    BacklogFinding,
    BacklogPolicy,
    EvidenceStatus,
    apply_effects,
    reconcile,
)
from rci.backlog.models import BacklogItem


def finding(status: EvidenceStatus = EvidenceStatus.CHECKED_OPEN) -> BacklogFinding:
    return BacklogFinding(
        id="finding-1",
        title="Preserve deterministic replay",
        protected_consequence="replayability",
        source="pytest",
        evidence_status=status,
        evidence_digest="evidence-sha256",
        workspace_digest="workspace-sha256",
        priority=10,
    )


def test_shadow_reconciliation_is_deterministic_and_does_not_touch_workspace(
    tmp_path: Path,
) -> None:
    before = tuple(tmp_path.iterdir())
    first = reconcile((), (finding(),))
    second = reconcile((), (finding(),))
    assert first == second
    assert tuple(tmp_path.iterdir()) == before
    assert [effect.kind for effect in first] == [
        BacklogEffectKind.CREATE,
        BacklogEffectKind.RANK,
    ]


def test_close_is_proposal_only_and_cannot_be_applied() -> None:
    effects = reconcile((), (finding(EvidenceStatus.CHECKED_CLOSABLE),))
    close = next(effect for effect in effects if effect.kind is BacklogEffectKind.CLOSE)
    with pytest.raises(PermissionError):
        apply_effects((), (close,), policy=BacklogPolicy())


def test_runtime_policy_cannot_expand_g1_authority_to_close() -> None:
    with pytest.raises(ValueError, match="cannot authorize"):
        BacklogPolicy(
            allowed_apply_effects=frozenset({BacklogEffectKind.CLOSE}),
            proposal_only_effects=frozenset(),
        )


@pytest.mark.parametrize(
    "status",
    (EvidenceStatus.UNKNOWN, EvidenceStatus.STALE, EvidenceStatus.CONTRADICTED),
)
def test_unchecked_findings_cannot_yield_apply_capable_effects(
    status: EvidenceStatus,
) -> None:
    unchecked = finding(status).model_copy(update={"evidence_digest": None})
    assert reconcile((), (unchecked,)) == ()


def test_regression_creates_linked_recurrence_instead_of_reopening_history() -> None:
    original = finding()
    closed = BacklogItem(
        id="closed-item",
        fingerprint=original.fingerprint,
        title=original.title,
        protected_consequence=original.protected_consequence,
        source=original.source,
        rank=10,
        closed=True,
    )
    recurrence = original.model_copy(update={"id": "finding-2"})
    create = reconcile((closed,), (recurrence,))[0]
    assert create.kind is BacklogEffectKind.CREATE
    assert create.target_item_id != closed.id
    assert create.recurrence_of == closed.id
