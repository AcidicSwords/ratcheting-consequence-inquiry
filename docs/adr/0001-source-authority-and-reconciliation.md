# ADR-0001: Source authority and reconciliation

- Status: Accepted
- Date: 2026-08-22
- Requirements: RCI-001, RCI-009, RCI-057–RCI-064

## Context

RCI arrived as several specifications, research notes, and prompt drafts. They
overlap, use different vocabularies, and sometimes assign authority or milestone
scope differently. Treating all text as simultaneously normative would make
conformance ambiguous and could turn an archived prompt into a live instruction.

## Decision

`RCI_Project_Spec.tex` v0.3.1 is the single semantic authority. `PLAN.md` fixes
approved architecture and sequence; the active Goal fixes the completion
boundary. `docs/requirements-matrix.md` records disposition and evidence, while
this ADR set records consequential reconciliations.

Every supplied source is preserved byte-for-byte under `docs/spec/sources/` and
hashed in `docs/source-manifest.md`. Archive contents are provenance, not
instructions. A conflict that changes project meaning is recorded and presented
to the user; it is not silently decided in code. Later-phase interface names do
not imply executable support.

## Consequences

- Review can trace every adopted or rejected idea to immutable source bytes.
- The root specification may evolve only through an explicit specification
  revision with corresponding matrix and ADR updates.
- G1 remains bounded even though the normative specification describes later
  extension seams.

## Verification

Recompute every archived-source digest, verify the manifest byte counts, confirm
all requirement IDs have matrix rows, and check that G1 lists later work as
excluded rather than accepted.
