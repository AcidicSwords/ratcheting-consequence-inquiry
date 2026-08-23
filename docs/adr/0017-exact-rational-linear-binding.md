# ADR-0017: Exact rational linear binding

- Status: Accepted for active G3A-L
- Date: 2026-08-22
- Requirements: RCI-051--RCI-054, RCI-059

## Context

G3A-H already implements carrier-explicit exact compression contracts and keeps their
validation, warrant, licence, and application stages separate. RCI-051--RCI-054 and
ADR-0005 additionally define a concrete finite-dimensional linear binding, but no code
currently realizes it. The post-G3FO frontier did not establish question-frame blindness,
so the candidate grammar remains deferred. The exact linear binding is the smallest
already-authorized successor with a finite independent discriminator and a mature native
mathematical implementation.

## Decision

Implement G3A-L as an additive pure binding under `rci.compression`. SymPy 1.14.0 constructs
exact rational matrices, ranks, row spaces, and nullspaces. A separate standard-library
`fractions.Fraction` elimination/checking path verifies the canonical result and does not
call the SymPy analyzer. Neither path grants a compression licence or warrant.

The binding accepts only finite, explicitly typed rational data:

- universal scalar probes use a stacked exact matrix `A`;
- finite-support scalar distributions use the uncentered second moment
  `M = sum(weight * q * q.T)`;
- finite-support vector outputs use `G = sum(weight * A.T * A)`;
- every finite-support weight is strictly positive and exactly normalized;
- the quotient is represented by exact row-space coordinates, while the kernel remains
  the authoritative collapsed subspace;
- reported minimum dimension is explicitly limited to linear encoders;
- almost-sure conclusions stay almost-sure unless a separate support theorem establishes
  universality;
- reopening is `ker(old) not-subset-of ker(new)`, and positive added probes may establish
  strict kernel shrink. The pure binding returns an exact witness with `Unknown`; only the
  existing aggregate-owned G3A-H transition may resolve retained residue or a licensed
  reacquisition route.

Rational construction rejects floats, symbolic free variables, approximate zeros, and
numeric tolerances. The backend's generated result is evidence for an independent check,
not its own check. The compatibility bridge targets existing G3A-H validation records and
does not mutate any sealed event schema.

## Consequences

- SymPy becomes a direct dependency only because G3A-L exercises its exact matrix API.
- Base tests remain offline and deterministic after dependency synchronization.
- RCI-051--RCI-054 can gain executable evidence without turning the linear theorem into a
  universal model of raw memory or nonlinear state.
- G3B approximation, G3C native adapters, and the compositional grammar remain separate
  future Goals.

## Verification

Use exact rational fixtures for redundant/independent scalar probes, weighted finite
support, vector outputs, row-space quotient coordinates, correct and reversed reopening,
and residue/recovery/Unknown disposition. Differential property tests compare SymPy
construction with the independent Fraction checker. Mutation tests reject zero/negative
weights, floats, malformed shapes, false minimality scope, and unsupported universality.
