"""Immutable v0.3 question catalog and the bounded ``core-v1`` profile."""

from __future__ import annotations

from rci.claims.models import ClaimRole
from rci.questions.models import (
    ContractMaturity,
    QuestionCatalog,
    QuestionContract,
    QuestionProfile,
)


def _contract(
    contract_id: str,
    family: str,
    role: ClaimRole,
    template: str,
    *,
    maturity: ContractMaturity = ContractMaturity.DRAFT,
    next_rules: tuple[str, ...] = (),
) -> QuestionContract:
    return QuestionContract(
        id=contract_id,
        version="1.0.0",
        family=family,
        input_roles=("carrier",),
        output_claim_role=role,
        precondition_policy_id="carrier-present-v1",
        render_template=template,
        next_obligation_rule_ids=next_rules,
        maturity=maturity,
    )


_CORE_CONTRACTS = (
    _contract(
        "obligation-characterization",
        "present-obligation",
        ClaimRole.CHARACTERIZATION,
        "What exact relation must be established for {carrier}?",
        maturity=ContractMaturity.STABLE,
    ),
    _contract(
        "same-class-variation",
        "stretch-positive",
        ClaimRole.VARIATION,
        "What variation of {carrier} preserves the protected consequence?",
        maturity=ContractMaturity.STABLE,
    ),
    _contract(
        "minimal-boundary-crossing",
        "squeeze-positive-to-negative",
        ClaimRole.BOUNDARY,
        "What smallest change to {carrier} crosses the protected boundary?",
        maturity=ContractMaturity.STABLE,
    ),
    _contract(
        "factor-proposal",
        "factor",
        ClaimRole.FACTOR,
        "Which factor best explains the consequential variation in {carrier}?",
        maturity=ContractMaturity.STABLE,
    ),
    _contract(
        "necessity-counterexample",
        "necessity",
        ClaimRole.NECESSITY,
        "Can the consequence hold without {carrier}?",
        maturity=ContractMaturity.STABLE,
        next_rules=("retain-counterexample-or-record-unknown-v1",),
    ),
    _contract(
        "sufficiency-counterexample",
        "sufficiency",
        ClaimRole.SUFFICIENCY,
        "Can {carrier} hold while the consequence fails?",
        maturity=ContractMaturity.STABLE,
        next_rules=("retain-counterexample-or-record-unknown-v1",),
    ),
    _contract(
        "conflict-localization",
        "contradiction-repair",
        ClaimRole.LOCALIZATION,
        "Where is the smallest explicit conflict involving {carrier}?",
        maturity=ContractMaturity.STABLE,
    ),
    _contract(
        "residual-characterization",
        "residual",
        ClaimRole.RESIDUAL,
        "What consequential uncertainty remains for {carrier}?",
        maturity=ContractMaturity.STABLE,
    ),
)


# Catalog families from v0.3 Parts XXV/XXVI remain discoverable but inactive. They
# are metadata, not promises that later-phase semantics already exist.
_DRAFT_FAMILIES: tuple[tuple[str, str, ClaimRole], ...] = (
    ("binding", "binding", ClaimRole.CHARACTERIZATION),
    ("consequence", "consequence", ClaimRole.CHARACTERIZATION),
    ("distinction", "distinction", ClaimRole.BOUNDARY),
    ("equivalence", "equivalence", ClaimRole.GENERALIZATION),
    ("second-distinction", "second-distinction-tetrad", ClaimRole.BOUNDARY),
    ("arrangement", "arrangement", ClaimRole.PATTERN),
    ("succession", "succession", ClaimRole.PATTERN),
    ("stretch-negative", "stretch-negative", ClaimRole.VARIATION),
    ("squeeze-negative-positive", "squeeze-negative-to-positive", ClaimRole.BOUNDARY),
    ("extreme-reversal", "extreme-reversal", ClaimRole.VARIATION),
    ("problem-reconstruction", "problem-non-problem", ClaimRole.CHARACTERIZATION),
    ("abstraction", "abstraction", ClaimRole.GENERALIZATION),
    ("description-control", "description-control", ClaimRole.PREREQUISITE),
    ("actualization", "actualization", ClaimRole.ACTUALIZATION),
    ("prerequisite", "prerequisite", ClaimRole.PREREQUISITE),
    ("discharge-selection", "discharge-selection", ClaimRole.CHARACTERIZATION),
    ("warrant", "warrant", ClaimRole.CHARACTERIZATION),
    ("success-localization", "success-localization", ClaimRole.LOCALIZATION),
    ("failure-localization", "failure-localization", ClaimRole.LOCALIZATION),
    ("generalization", "generalization", ClaimRole.GENERALIZATION),
    ("conditional-learning", "conditional-learning", ClaimRole.GENERALIZATION),
    ("reopening", "reopening", ClaimRole.RESIDUAL),
    ("compression", "compression", ClaimRole.RESIDUAL),
    ("intermediate-lawfulness", "intermediate-lawfulness", ClaimRole.INVARIANT),
    ("question-selection", "question-selection", ClaimRole.CHARACTERIZATION),
    ("progress", "progress", ClaimRole.CHARACTERIZATION),
    ("stopping", "stopping", ClaimRole.CHARACTERIZATION),
    ("recurrent-perception", "recurrent-perceptual", ClaimRole.PATTERN),
)

_DRAFT_CONTRACTS = tuple(
    _contract(
        f"draft-{contract_id}",
        family,
        role,
        "What does the {family} relation reveal about {carrier}?".replace("{family}", family),
    )
    for contract_id, family, role in _DRAFT_FAMILIES
)

CORE_V1 = QuestionProfile(
    id="core-v1",
    version="1.0.0",
    contract_keys=tuple(contract.key for contract in _CORE_CONTRACTS),
)

CATALOG_V0_3 = QuestionCatalog(
    id="rci-question-catalog",
    version="0.3.0",
    contracts=_CORE_CONTRACTS + _DRAFT_CONTRACTS,
    profiles=(CORE_V1,),
)

LEARNED_RECURRENT_PROBE = QuestionContract(
    id="learned-recurrent-probe",
    version="1.0.0",
    family="learned-recurrent-perceptual",
    input_roles=("carrier",),
    output_claim_role=ClaimRole.PATTERN,
    precondition_policy_id="admitted-learned-probe-v1",
    render_template="What protected distinction does the admitted probe reveal for {carrier}?",
    next_obligation_rule_ids=("retain-provisional-pattern-or-record-unknown-v1",),
    maturity=ContractMaturity.STABLE,
    recurrent_probe=True,
    comparison_semantics_id="candidate-bound-exact-v1",
    canonical_probe_rendering="learned-recurrent-probe-v1",
    applicability_guard_id="always",
    history_policy_id="fresh-before-history-v1",
)

G2B_COGNITIVE_V1 = QuestionProfile(
    id="g2b-cognitive-v1",
    version="1.0.0",
    contract_keys=(LEARNED_RECURRENT_PROBE.key,),
)

CATALOG_V0_4 = QuestionCatalog(
    id="rci-question-catalog",
    version="0.4.0",
    contracts=(*CATALOG_V0_3.contracts, LEARNED_RECURRENT_PROBE),
    profiles=(*CATALOG_V0_3.profiles, G2B_COGNITIVE_V1),
)


def get_contract(contract_id: str, version: str = "1.0.0") -> QuestionContract:
    for contract in CATALOG_V0_4.contracts:
        if contract.id == contract_id and contract.version == version:
            return contract
    raise KeyError(f"unknown question contract {contract_id}@{version}")
