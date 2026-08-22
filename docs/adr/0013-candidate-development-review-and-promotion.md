# ADR-0013: Candidate development, independent review, and protected promotion

- Status: accepted for G3R
- Date: 2026-08-22
- Requirements: RCI-076 through RCI-078

## Decision

An implementation candidate is developed from an exact clean anchor in an isolated
branch/worktree described by `CandidateEnvironmentManifest`. The Goal is sealed first
and pins current/desired behavior, separator, expected returns, preserved capabilities,
acceptance commands, assumptions, allowed mutation roots, forbidden authority roots,
incumbent/proposed gate digests, rollback, and reopening.

The RCI runtime records this proof chain but does not execute Git or write source:

```text
Goal sealed -> candidate environment -> development evidence
-> fresh exact-head independent review -> successor decision
-> externally observed protected promotion
```

The reviewer identity/context must differ from the developer, see the exact candidate
head and evidence, and return `Valid`, `Invalid`, or `Indeterminate`. Only `Valid` plus
passing exact-head evidence can support replacement. CI and review are independent
returns, not self-warrant. Merge is preauthorized by the user only after the sealed
conditions pass; force push, branch deletion, credentials, releases, deployments, and
permission expansion remain outside autonomous authority.

The user delegates bounded development intent, not a claim to technical infallibility
and not irreversible account authority. Within that bound the agent may choose
architecture and implementation by the recorded frontier and evidence instead of asking
the user to adjudicate details they cannot meaningfully verify. The user retains
revocation and account control. The candidate still cannot count the developer's own
confidence as review, rewrite the Goal after a return, or bypass protected checks.

This matches platform mechanisms that make long-running coding work inspectable—
repository instructions, isolated worktrees, permissions, persistent Goals, and scored
improvement loops—without treating a platform feature as project warrant:
<https://learn.chatgpt.com/use-cases>.

CI changes use dual-gate replacement: add the successor while the incumbent remains;
pass both on PR and protected main; require both; remove the incumbent only in a later
reviewed cleanup after the successor passes independently again.

## Continuity and stopping

Append-only cycle checkpoints and `docs/recursion/cycles/` reports make handoff durable.
Recurrence stops on no consequential residue, no discriminator, three repetitions of
the same blocker, invalid/indeterminate/stale evidence, or required authority expansion.
It returns `Unknown` rather than relaxing the Goal.
