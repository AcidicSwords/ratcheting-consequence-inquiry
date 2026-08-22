"""Immutable backlog records. They grant no workspace capability."""

from __future__ import annotations

import json
from enum import StrEnum
from hashlib import sha256

from pydantic import BaseModel, ConfigDict, model_validator


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


def backlog_fingerprint(title: str, protected_consequence: str, source: str) -> str:
    material = json.dumps(
        [title.strip(), protected_consequence.strip(), source.strip()],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode()
    return sha256(material).hexdigest()


class EvidenceStatus(StrEnum):
    CHECKED_OPEN = "checked_open"
    CHECKED_BLOCKED = "checked_blocked"
    CHECKED_CLOSABLE = "checked_closable"
    STALE = "stale"
    UNKNOWN = "unknown"
    CONTRADICTED = "contradicted"


CHECKED_EVIDENCE_STATUSES = frozenset(
    {
        EvidenceStatus.CHECKED_OPEN,
        EvidenceStatus.CHECKED_BLOCKED,
        EvidenceStatus.CHECKED_CLOSABLE,
    }
)


class BacklogEffectKind(StrEnum):
    CREATE = "create"
    DEDUPE = "dedupe"
    RANK = "rank"
    BLOCK = "block"
    CLOSE = "close"


G1_APPLICABLE_EFFECT_KINDS = frozenset(
    {
        BacklogEffectKind.CREATE,
        BacklogEffectKind.DEDUPE,
        BacklogEffectKind.RANK,
        BacklogEffectKind.BLOCK,
    }
)


class BacklogFinding(FrozenModel):
    id: str
    title: str
    protected_consequence: str
    source: str
    evidence_status: EvidenceStatus
    evidence_digest: str | None = None
    workspace_digest: str
    priority: int = 0
    recurrence_of: str | None = None

    @model_validator(mode="after")
    def validate_finding(self) -> BacklogFinding:
        required = (
            self.id,
            self.title,
            self.protected_consequence,
            self.source,
            self.workspace_digest,
        )
        if not all(required):
            raise ValueError("finding identity and evidence fields are required")
        if self.evidence_status in CHECKED_EVIDENCE_STATUSES and not self.evidence_digest:
            raise ValueError("checked findings require an exact evidence digest")
        return self

    @property
    def fingerprint(self) -> str:
        return backlog_fingerprint(self.title, self.protected_consequence, self.source)


class BacklogItem(FrozenModel):
    id: str
    fingerprint: str
    title: str
    protected_consequence: str
    source: str
    rank: int
    blocked: bool = False
    closed: bool = False
    recurrence_of: str | None = None


class BacklogEffect(FrozenModel):
    id: str
    kind: BacklogEffectKind
    finding_id: str
    target_item_id: str
    fingerprint: str
    title: str
    protected_consequence: str
    source: str
    recurrence_of: str | None = None
    rank: int | None = None
    evidence_digest: str
    workspace_digest: str
    reason: str
