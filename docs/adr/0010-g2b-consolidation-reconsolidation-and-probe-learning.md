# ADR-0010: G2B consolidation, reconsolidation, and probe learning

- Status: Accepted
- Date: 2026-08-22
- Requirements: RCI-010, RCI-024, RCI-031, RCI-033, RCI-037,
  RCI-042--RCI-044, RCI-058

## Context

G2A made retrieval and measured reacquisition executable without allowing retrieved or
reconstructed material to become knowledge. The remaining RCI-058 work must explain how
episodes can propose generalizations, how challenged retained relations receive versioned
successors, how a bounded semantic field is evaluated, and how a failed probe basis can
propose a new procedural probe. None of those paths may bypass ordinary claim, attack,
checking, warrant, or immutable-history boundaries.

## Decision

G2B uses four separately owned pipelines:

1. `consolidation-interleave-v1` deterministically selects recent episodes together with
   available older exceptions and accepted counterexamples from an exact source prefix.
   A checkpoint is historical evidence; a consolidation candidate is an ordinary
   provisional generalization claim with an explicit candidate support boundary and
   challenge obligations. It is not a lemma or support route.
2. Reconsolidation begins from an owned mismatch and creates a `MemoryPatchCandidate`.
   A checked application appends a successor lemma, typed correction, and
   `ReconsolidationLink`. The predecessor and its provenance remain addressable, and every
   unresolved predecessor dependency is transported unless exact hard evidence discharges
   it.
3. `conservative-question-field-v1` derives a maximum 32-item semantic field from owned
   state. Open safety/warrant conflicts, counterexamples and exceptions, active support
   dependencies, and exact retrieval hits have fixed priority. Overflow remains
   undetermined. Only an active hard consequence-null warrant plus reopening condition may
   establish irrelevance. An evaluation is diagnostic evidence, not semantic authority.
4. A representation gap may create an inert `LearnedProbeCandidate` using the fixed
   `learned-recurrent-probe@1.0.0` contract. `finite-stratified-holdout-v1` evaluates exact
   additional consequence discrimination under a deterministic stratified split. Admission
   requires independent holdout, protected-behavior, and redundancy checks, completed
   attacks, and `g2b-probe-admission-v1`. Admission writes procedural memory only and does
   not create a lemma, licence, control certificate, or global scheduling permission.

The generic G1 `AdmitProbe` path remains available only to code-registered catalog probes.
Generated probes use the checked G2B admission event. AALpy, embeddings, learned automata,
compression, recovery licensing, self-cleaning, and control are outside G2B.

G2B adds new version-1 events and folded-state fields. Existing G1/G2A event classes remain
unchanged. The folded-state schema advances to v3 and incompatible snapshots rebuild from
the ledger; the SQLite table schema remains v2 unless a real table change becomes necessary.

## Consequences

- Episodic recurrence cannot self-promote into generalized knowledge.
- Recent-history bias is attacked by construction when older defeating material exists.
- Reconsolidation repairs by succession rather than rewriting history.
- Context pressure cannot silently convert unexplored structure into irrelevance.
- A learned probe has measurable protected value and an auditable admission boundary.
- RCI-058 can close without importing compression, control, or a machine-learning runtime.

## Verification

The G2B acceptance slice covers deterministic source selection, one-episode rejection,
older-counterexample inclusion, ordinary-claim/attack creation, dependency-preserving
versioned repair, conservative field coverage and overflow, representation-gap handling,
holdout and redundancy attacks, admission non-bypass, procedural-only admission, and sealed
G1/G2A replay compatibility.
