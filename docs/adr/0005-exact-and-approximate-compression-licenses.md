# ADR-0005: Exact and approximate compression licenses

- Status: Accepted
- Date: 2026-08-22
- Requirements: RCI-047–RCI-056

## Context

The consequence-subspace note gives a useful exact linear quotient, while
practical compression methods are approximate and resource-dependent. Collapsing
the two would let empirical low loss or numerical rank thresholds authorize
irreversible forgetting.

## Decision

Compression has four immutable layers:
`CompressionContract`, independent `CompressionValidation`, policy
`CompressionLicense`, and `CompressionApplication`. Exact and approximate
licenses are tagged variants. Exactness is relative to a pinned protected
horizon, scope, query family, and binding; measured zero is not exact proof.

For finite-dimensional linear query family \(Q\), exact equivalence uses
\(V=\operatorname{span}Q\) and quotient
\(\mathbb R^d/V^\perp\cong V\). In the distributional form, the conclusion is
almost-sure unless support establishes universality. Reopening occurs when an old
null direction becomes visible:
\(\ker M_t\not\subseteq\ker M_{t+1}\); for positive-weight added probes this is a
strict kernel shrink. Linear rank establishes minimal linear dimension only.

Compression carries dependency residue, provenance, ancestry, debt, fallback,
and reopening predicates. Approximate bounds compose only through a pinned
checked policy.

## Consequences

- G3A can prove exact rational/finite cases without importing approximate
  numerical assumptions.
- G3B can evaluate bounded loss without upgrading it to exactness.
- Method catalogs and native adapters do not become core semantics.

## Verification

Use rational finite fixtures for quotient/kernel/rank/reopening laws and
counterexamples for the reversed kernel condition. Test discriminated licenses,
zero-loss non-promotion, residue preservation, and fail-closed bound
composition.
