# Proposed Goal G3A-H: Exact history-state foundation

- Status: active after v0.4 governance merge
- Authority: RCI v0.4, PLAN, ADR-0011
- Token budget: none

## Target

Build and verify RCI v0.4 milestone G3A-H as defined by `PLAN.md`, ADR-0011,
and this Goal.

Follow root `AGENTS.md`. Treat `RCI_Project_Spec.tex` v0.4 as semantic
authority and maintain `docs/requirements-matrix.md` for RCI-001 through
RCI-071. Preserve the sealed G1, G2A, and G2B event schemas and semantics.

Implement only the exact history-state foundation of G3A:

- explicit binding-declared configuration, realized-history,
  prior-retained-state, and other carrier roles;
- a binding-specific typed partial realized-history derivation that never
  infers domain succession from ledger order;
- `CompressionContract`, independent `CompressionValidation`,
  `ExactCompressionLicense`, `CompressionApplication`, `RecoveryLicense`,
  `PathResidue`, route-capability linking, and a derived retained-state view;
- exact consequence factorization, separately claimed coarsest equivalence,
  continuation compatibility, deterministic recursive update where applicable,
  determination descent, and residue completeness;
- representation-successor decisions requiring predecessor preservation,
  typed gain, independent warrant, and explicit incomparability;
- generic reopening by exact factorization failure, with `Unknown` when no
  residue or licensed recovery route can restore the distinction;
- folded-state schema v4 with rebuild of v1-v3 snapshots and no mutation of
  existing event classes.

Implement the unary parity fixture as an unbounded unary-history carrier with a
finite two-state quotient checked by finite transition congruence and base/step
reasoning. Implement the order-sensitive fixture proving that equal
configuration and equal event counts do not imply equal protected future
consequence.

Do not replace `InquiryState`, infer history from ledger sequence, identify
`ProbeTrace` with realized history, identify `RetentionPackage` with certified
retained state, identify `MemoryPatchCandidate` with representation refinement,
collapse `PathResidue` into an open support dependency, or let validation,
license, or application promote itself.

Do not add SymPy, NumPy, approximate compression, native compression adapters,
CHC/PDR, controller synthesis, multi-backend evidence, UI, servers, deployment,
releases, or the opaque end-to-end benchmark. G3A-L and later Goals own those
capabilities.

## Completion gate

Run the sealed G1 gate and both sealed G2 focused commands, then:

```text
uv run pytest -q tests/acceptance/test_g3a_history_state.py
```

Completion requires every in-scope matrix row to have passing evidence,
archived G1/G2 streams to replay with unchanged semantics, all five protected
hosted Windows/Linux/extras/Docker checks, and successful post-merge `main` CI.

## Explicit exclusions

G3A-L linear geometry, G3B approximation, G3C native methods, G4 recursive
formal engines, G5 control, G6 multi-backend warrant, G7 opaque benchmark and
release hardening, UI, servers, deployment, tags, and releases.

