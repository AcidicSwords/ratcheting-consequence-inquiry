# Ratcheting Consequence Inquiry v0.4 — captured semantic source

**Capture:** supplied directly by the user in the Codex task on 2026-08-22  
**Alignment anchor:** `a5ac134981494cd126261117828140e7151eaf39`  
**Disposition:** semantic successor source normalized into `RCI_Project_Spec.tex`

This repository copy captures the complete semantic delta that was supplied in
conversation. It is provenance, not a second live instruction source. The root
TeX specification is the normalized authority.

## Decisive distinction

The authoritative aggregate fold and the protected retained-state quotient are
different maps:

```text
Phi_agg : E_B* -> Sigma_B^agg
q_H     : Hist_B -> S_H
Phi_agg != q_H
```

`InquiryState` is `Sigma^agg`: the replay-complete fold of the immutable event
ledger. `S_H` is a G3 representation that retains exactly or approximately what
a declared protected future consequence horizon needs from realized history.
No G1/G2 object is silently redefined as `S_H`.

## Repository-aligned symbols

- `E_B` is the versioned event vocabulary and an event prefix is authoritative
  immutable history.
- `Phi_agg` is repeated pure `evolve`; its result is `InquiryState`.
- `rho_B` is a binding-specific partial derivation of realized interaction
  history from authoritative evidence.
- `p_B` projects realized history to a binding-defined configuration carrier.
- `H` is the protected future experiment/consequence horizon.
- `q_H` maps realized history into a consequence-sufficient retained carrier.
- `ProbeTrace` is one comparable observational subtrace, not universal history.
- `RetentionPackage` is a package of typed references and provisional routes,
  not a sufficiency proof or licensed state.
- `RepresentationGap` witnesses an unavailable distinction but does not choose
  the missing representation.
- `PredictionSeal` is a sealed prospective consequence commitment.
- `Mismatch` is a typed comparison with an actual captured return.
- support and warrant remain owned by the existing warrant subsystem.

Ledger order is not domain succession unless a binding establishes that fact.
Claims, verdicts, semantic-field evaluations, and learned-probe candidates can
advance ledger sequence without extending realized domain history. No universal
`Occurrence` type is introduced.

Two histories may have the same configuration while differing under a protected
future consequence. Consequently a configuration projection and a history
quotient are separate contracts even when their codomains happen to be
isomorphic.

## Exact retained state

For every protected experiment `e in H`, a binding supplies `Con_e(h)` and its
typed equality semantics. Exact protected equivalence is:

```text
h ==_H h' iff Con_e(h) == Con_e(h') for every e in H
```

A working relation based on currently admitted discriminators is weaker and
cannot become exact merely because no current probe separates the histories.

`q : Hist_B -> S` is consequence sufficient when equal represented values imply
exact protected equivalence. Equivalently, every protected consequence factors
through `q`. Calling a representation the exact coarsest quotient additionally
requires the reverse implication and an independent minimality/isomorphism
argument. Existence of the set quotient gives no automatic finite,
computability, linearity, realizability, or bit-optimality result.

The authoritative recurrence and consequence-state recurrence are distinct:

```text
Sigma[n+1] = evolve(Sigma[n], event[n+1])
q(h . u)   = U(q(h), u)
evolve != U
```

The second equation applies only to binding-defined realized extensions. A
retained representation claimed executable under an admitted continuation must
also prove that equal represented states have identical represented successor
sets for every operation in scope. Present-answer sufficiency does not imply
recursive-state sufficiency.

Determination languages are carrier-relative. A history determination descends
to retained state exactly when it is saturated under `q`, equivalently when it
is an inverse image of a retained-state determination.

## Filtering, refinement, and ratchet

Updating `s` under fixed `q`, refining `q`, extending `H`, and rebinding `B` are
different transitions. A G2B `MemoryPatchCandidate` repairs a semantic lemma; it
is not a representation refinement.

A representation successor must preserve every still-valid protected
predecessor competence, establish at least one typed strict gain, and possess
standing independent warrant. Invalidated predecessor claims require exact
warranted disposition. Mere tradeoffs remain incomparable. New model output,
new notation, or regenerated objections are not gain.

Reopening occurs whenever a new protected consequence cannot factor through an
incumbent representation: there exist inputs identified by the old `q` that the
new consequence separates. If the distinction is absent from representation
residue, provenance/ancestry, and licensed recovery routes, the result is
`Unknown`; no reconstruction is fabricated.

Representation/path residue and epistemic open dependency remain different.

## G3 exact contract

Every exact compression contract identifies source and target carriers, carrier
roles, binding, scope, horizon, continuation family, consequence/query family,
equality semantics, and recovery semantics. Source roles include configuration,
realized history, prior retained state, and another explicitly declared carrier.

Validation separately establishes every claimed property:

1. protected consequence factorization;
2. reverse equivalence/minimality when a coarsest quotient is claimed;
3. continuation compatibility for history-state execution;
4. deterministic recursive update where applicable;
5. determination descent where claimed;
6. residue and recovery completeness.

The lifecycle remains:

```text
CompressionContract
  -> independent CompressionValidation
  -> policy CompressionLicense
  -> CompressionApplication
```

Only a compression application joined to a standing route-specific recovery
license may expose a G2 retention package as a protected retained capability.
The package alone never does so.

## Exact fixtures

The first fixture uses the unbounded unary-history carrier `{a}*`, a singleton
configuration projection, parity as protected consequence, and the finite
retained state `{even, odd}` with toggle update. Exactness is established through
a finite transition congruence and base/step argument, not bounded sampling.
A smaller parity-insensitive horizon lawfully permits a singleton quotient;
adding parity reopens it.

The second fixture distinguishes `ab` from `ba`. They have the same configuration
and event counts but a declared protected continuation separates them. Count is
therefore not a sufficient history state.

## Permanent no-collapse rules

- `InquiryState` is not realized history or retained consequence state.
- `ProbeTrace` is not realized history.
- `RetentionPackage` is not `S_H` and does not imply licensed retention.
- `MemoryPatchCandidate` is not `q` refinement.
- same configuration does not imply same future behavior.
- same immediate output does not imply same trajectory behavior.
- availability does not imply warrantable selection.
- retrospective improvement does not imply prospective knowability.
- generated separators are not admitted probes.
- admitted probes are not licensed state representations.
- failed recall does not prove absence of retained learning.
- zero empirical loss or numerical near-zero does not prove exactness.

## Requirement delta

RCI-002, 008, 023, 024, 047–050, 054, 059, 065–068 are strengthened without
renumbering. RCI-069 requires aggregate/retained-state separation. RCI-070
requires continuation compatibility for executable retained state. RCI-071
requires warranted preservation-and-gain succession or explicit
incomparability.

Sealed G1, G2A, and G2B event classes retain their existing meaning. G3 adds new
version-1 event kinds and may advance only rebuildable folded-state, snapshot,
and projection schemas. The ledger/CAS remains the sole durable authority.

