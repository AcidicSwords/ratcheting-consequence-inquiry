# Active Goal G3A-L: Exact finite rational linear binding

- Status: active
- Authority: RCI v0.5, PLAN, ADR-0005, ADR-0011, ADR-0017
- Anchor: `71d32346c71a26cf82a36df7e50376759bc1873b`
- Token budget: none

## Sealed relation

Current: G3A-H provides generic carrier-explicit compression contracts, independent
validation stages, exact licensing, residue, reopening, and representation succession,
but RCI-051--RCI-054 have no executable exact linear binding.

Desired: a binding-specific, dependency-bounded exact rational implementation establishes
the finite universal, finite-support almost-sure scalar, and finite-support vector-output
linear consequence theorems; computes exact quotient/kernel/rank data; checks that data
independently; and detects the corrected kernel-shrink reopening condition.

Separator: exact finite fixtures must distinguish independent from redundant probes,
positive from zero/negative weights, universal from almost-sure scope, scalar from vector
outputs, correct from reversed kernel inclusion, recoverable from unrecoverable reopening,
and exact rationals from numerical approximations.

Preserve: every sealed event and snapshot schema, the replay-complete `InquiryState`, all
G3A-H carrier and authority distinctions, independent validation/license/application
stages, lawful `Unknown`, every predecessor gate, and the absence of source/Git,
promotion, model, control, or native-adapter authority.

## Scope

Implement strict, frozen, versioned exact-linear data records and pure operations for:

- canonical rational scalars, vectors, matrices, and positive finite weights;
- finite universal scalar probe families;
- finite-support almost-sure scalar query families using the uncentered second moment;
- finite-support almost-sure vector-output families using
  `G = sum(weight * A.T * A)`;
- exact rank, nullspace, row-space/quotient coordinates, consequence equivalence, and the
  minimum dimension among linear encoders only;
- an independent `fractions.Fraction` checker that does not call the SymPy analyzer;
- kernel reopening witnesses, with exact residue/recovery disposition and `Unknown` when
  neither route is licensed;
- a compatibility bridge that supplies exact property evidence to existing G3A-H
  `CompressionValidation` construction without warranting or licensing itself.

SymPy 1.14.0 is the pinned construction backend. Inputs are rationals only. No float,
numeric tolerance, approximate zero, eigenvalue cutoff, or empirical loss can enter the
exact path.

## Completion gate

Run every sealed predecessor command unchanged and add this focused command identically
to AGENTS, PLAN, CI, and verification evidence:

```text
uv run pytest -q tests/acceptance/test_g3a_linear_binding.py
```

Completion additionally requires base/all-extras Windows and Linux CI, Docker, exact-head
fresh semantic review from a context distinct from development, protected promotion, and
post-merge `main` CI. If the review is unavailable or invalid, preserve the candidate and
stop indeterminate rather than claiming the capability.

## Exclusions

No approximate compression or `ApproximateCompressionLicense`; NumPy; numerical rank;
arbitrary symbolic expressions; infinite-support measure theory; unrestricted bit or
nonlinear minimality; native compression adapters; candidate question grammar; event or
snapshot changes; raw opaque-memory system identification; CHC/PDR; control;
multi-backend warrant; model adapters; source/Git mutation; deployment; release; or
self-review/self-warrant/self-promotion.
