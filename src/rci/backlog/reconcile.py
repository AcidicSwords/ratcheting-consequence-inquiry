"""Pure deterministic reconciliation and an explicitly bounded apply projection."""

from __future__ import annotations

from collections.abc import Iterable
from hashlib import sha256

from pydantic import BaseModel, ConfigDict, model_validator

from rci.backlog.models import (
    CHECKED_EVIDENCE_STATUSES,
    G1_APPLICABLE_EFFECT_KINDS,
    BacklogEffect,
    BacklogEffectKind,
    BacklogFinding,
    BacklogItem,
    EvidenceStatus,
)


class BacklogPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    allowed_apply_effects: frozenset[BacklogEffectKind] = G1_APPLICABLE_EFFECT_KINDS
    proposal_only_effects: frozenset[BacklogEffectKind] = frozenset({BacklogEffectKind.CLOSE})

    @model_validator(mode="after")
    def validate_policy(self) -> BacklogPolicy:
        if self.allowed_apply_effects & self.proposal_only_effects:
            raise ValueError("an effect cannot be both applicable and proposal-only")
        unauthorized = self.allowed_apply_effects - G1_APPLICABLE_EFFECT_KINDS
        if unauthorized:
            names = ", ".join(sorted(effect.value for effect in unauthorized))
            raise ValueError(f"G1 policy cannot authorize apply effects: {names}")
        if BacklogEffectKind.CLOSE not in self.proposal_only_effects:
            raise ValueError("G1 requires close to remain proposal-only")
        return self


def _effect_id(kind: BacklogEffectKind, finding: BacklogFinding, target: str) -> str:
    if finding.evidence_digest is None:
        raise ValueError("applicable backlog effects require checked evidence")
    material = f"{kind}\x00{finding.id}\x00{target}\x00{finding.evidence_digest}".encode()
    return f"bfx_{sha256(material).hexdigest()[:24]}"


def _effect(
    kind: BacklogEffectKind,
    finding: BacklogFinding,
    target: str,
    reason: str,
    *,
    rank: int | None = None,
) -> BacklogEffect:
    if finding.evidence_digest is None:
        raise ValueError("applicable backlog effects require checked evidence")
    return BacklogEffect(
        id=_effect_id(kind, finding, target),
        kind=kind,
        finding_id=finding.id,
        target_item_id=target,
        fingerprint=finding.fingerprint,
        title=finding.title,
        protected_consequence=finding.protected_consequence,
        source=finding.source,
        recurrence_of=finding.recurrence_of,
        rank=rank,
        evidence_digest=finding.evidence_digest,
        workspace_digest=finding.workspace_digest,
        reason=reason,
    )


def reconcile(
    items: Iterable[BacklogItem], findings: Iterable[BacklogFinding]
) -> tuple[BacklogEffect, ...]:
    """Return a stable shadow trace without mutating input or workspace state."""

    item_tuple = tuple(items)
    existing = {item.fingerprint: item for item in item_tuple if not item.closed}
    closed = {item.fingerprint: item for item in item_tuple if item.closed}
    effects: list[BacklogEffect] = []
    for finding in sorted(findings, key=lambda value: (-value.priority, value.id)):
        if finding.evidence_status not in CHECKED_EVIDENCE_STATUSES:
            continue
        matched = existing.get(finding.fingerprint)
        prior_closed = closed.get(finding.fingerprint)
        effective_finding = finding
        if matched is None and prior_closed is not None and finding.recurrence_of is None:
            effective_finding = finding.model_copy(update={"recurrence_of": prior_closed.id})
        target = (
            matched.id
            if matched is not None
            else (
                f"item_{finding.fingerprint[:16]}_{finding.id[-7:]}"
                if effective_finding.recurrence_of is not None
                else f"item_{finding.fingerprint[:24]}"
            )
        )
        if matched is None:
            effects.append(
                _effect(
                    BacklogEffectKind.CREATE,
                    effective_finding,
                    target,
                    "linked recurrence" if prior_closed is not None else "new exact fingerprint",
                )
            )
        else:
            effects.append(
                _effect(
                    BacklogEffectKind.DEDUPE,
                    finding,
                    target,
                    "exact fingerprint match",
                )
            )

        effects.append(
            _effect(
                BacklogEffectKind.RANK,
                finding,
                target,
                "deterministic checked-evidence priority",
                rank=finding.priority,
            )
        )
        if finding.evidence_status is EvidenceStatus.CHECKED_BLOCKED:
            effects.append(
                _effect(BacklogEffectKind.BLOCK, finding, target, "checked prerequisite is open")
            )
        elif finding.evidence_status is EvidenceStatus.CHECKED_CLOSABLE:
            effects.append(
                _effect(
                    BacklogEffectKind.CLOSE,
                    finding,
                    target,
                    "fresh checked closure evidence; proposal-only in G1",
                )
            )
        existing.setdefault(
            finding.fingerprint,
            BacklogItem(
                id=target,
                fingerprint=finding.fingerprint,
                title=finding.title,
                protected_consequence=finding.protected_consequence,
                source=finding.source,
                rank=finding.priority,
                recurrence_of=effective_finding.recurrence_of,
            ),
        )
    return tuple(effects)


def apply_effects(
    items: Iterable[BacklogItem],
    effects: Iterable[BacklogEffect],
    *,
    policy: BacklogPolicy,
) -> tuple[BacklogItem, ...]:
    """Apply only policy-authorized local projection effects.

    Persistence is performed by the caller after appending the same effects atomically.
    This function exposes no filesystem, Git, subprocess, network, or policy mutation.
    """

    by_id = {item.id: item for item in items}
    for effect in effects:
        if effect.kind not in policy.allowed_apply_effects:
            raise PermissionError(f"effect {effect.kind} is not authorized for G1 apply")
        item = by_id.get(effect.target_item_id)
        if effect.kind is BacklogEffectKind.CREATE:
            if item is None:
                by_id[effect.target_item_id] = BacklogItem(
                    id=effect.target_item_id,
                    fingerprint=effect.fingerprint,
                    title=effect.title,
                    protected_consequence=effect.protected_consequence,
                    source=effect.source,
                    rank=0,
                    recurrence_of=effect.recurrence_of,
                )
            elif item.fingerprint != effect.fingerprint:
                raise ValueError("create effect target identity has different content")
        elif item is None:
            raise ValueError("non-create effect targets an unknown item")
        elif item.fingerprint != effect.fingerprint:
            raise ValueError("effect fingerprint does not match its target item")
        elif effect.kind is BacklogEffectKind.RANK:
            by_id[item.id] = item.model_copy(update={"rank": effect.rank or 0})
        elif effect.kind is BacklogEffectKind.BLOCK:
            by_id[item.id] = item.model_copy(update={"blocked": True})
        elif effect.kind is BacklogEffectKind.DEDUPE:
            # The single existing exact-fingerprint occurrence is already authoritative.
            continue
        else:  # pragma: no cover - model and constitutional policy make this unreachable
            raise RuntimeError(f"unhandled authorized backlog effect: {effect.kind}")
    return tuple(sorted(by_id.values(), key=lambda item: (-item.rank, item.id)))
