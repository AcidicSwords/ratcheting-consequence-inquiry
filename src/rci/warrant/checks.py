"""Fail-closed resolution of recorded evidence/check pairs."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from rci.warrant.models import (
    CheckerVerdict,
    CheckerVerdictRecord,
    CheckReference,
    Evidence,
    PropositionKind,
)


def evidence_index(records: Iterable[Evidence]) -> Mapping[str, Evidence]:
    return {record.id: record for record in records}


def checker_verdict_index(
    records: Iterable[CheckerVerdictRecord],
) -> Mapping[str, CheckerVerdictRecord]:
    return {record.id: record for record in records}


def validate_checked_evidence(
    evidence: Evidence,
    checker_verdict: CheckerVerdictRecord,
    *,
    proposition_id: str,
    proposition_kind: PropositionKind,
    scope_fingerprint: str,
    authorized_checker_ids: Iterable[str],
) -> tuple[bool, str]:
    """Validate exact ownership and policy pins without inferring checker authority."""

    if checker_verdict.evidence_id != evidence.id:
        return False, "checker verdict references different evidence"
    if checker_verdict.evidence_artifact != evidence.artifact:
        return False, "checker verdict does not pin the exact evidence artifact"
    if evidence.proposition_id != proposition_id:
        return False, "evidence proposition does not match exactly"
    if checker_verdict.proposition_id != proposition_id:
        return False, "checker verdict proposition does not match exactly"
    if evidence.proposition_kind is not proposition_kind:
        return False, "evidence proposition kind does not match exactly"
    if checker_verdict.proposition_kind is not proposition_kind:
        return False, "checker verdict proposition kind does not match exactly"
    if evidence.scope_fingerprint != scope_fingerprint:
        return False, "evidence scope does not match exactly"
    if checker_verdict.scope_fingerprint != scope_fingerprint:
        return False, "checker verdict scope does not match exactly"
    if checker_verdict.checker_id not in frozenset(authorized_checker_ids):
        return False, "checker identity is not authorized by the inquiry binding"
    if checker_verdict.verdict is not CheckerVerdict.VALID:
        return False, "independent checker did not validate the evidence"
    if checker_verdict.certificate_artifact is None:
        return False, "valid checker verdict lacks an exact certificate artifact"
    return True, "independently checked exact evidence"


def resolve_check_reference(
    reference: CheckReference,
    *,
    evidence_by_id: Mapping[str, Evidence],
    checker_verdict_by_id: Mapping[str, CheckerVerdictRecord],
    proposition_id: str,
    proposition_kind: PropositionKind,
    scope_fingerprint: str,
    authorized_checker_ids: Iterable[str],
) -> tuple[bool, str]:
    evidence = evidence_by_id.get(reference.evidence_id)
    checker_verdict = checker_verdict_by_id.get(reference.checker_verdict_id)
    if evidence is None:
        return False, "check reference does not resolve to owned evidence"
    if checker_verdict is None:
        return False, "check reference does not resolve to an owned checker verdict"
    if checker_verdict.evidence_id != reference.evidence_id:
        return False, "check reference evidence and checker verdict do not align"
    return validate_checked_evidence(
        evidence,
        checker_verdict,
        proposition_id=proposition_id,
        proposition_kind=proposition_kind,
        scope_fingerprint=scope_fingerprint,
        authorized_checker_ids=authorized_checker_ids,
    )
