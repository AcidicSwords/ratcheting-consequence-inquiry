# ADR-0008: Optional adapters and dogfooding authority

- Status: Accepted
- Date: 2026-08-22
- Requirements: RCI-041, RCI-056, RCI-061–RCI-064

## Context

OpenAI, Z3, native research code, Docker, and repository dogfooding can improve
RCI, but each introduces nondeterminism, availability, licensing, or authority
risk. They must not become hidden dependencies of the deterministic core.

## Decision

OpenAI and Z3 are optional extras behind versioned ports. Base installation,
replay, examples, and blocking tests are credential-free and network-silent.
The OpenAI adapter uses explicitly configured Responses API models, locally
compiled stateless context, no model tools, bounded output, `store=False`, and
preserved raw L0 responses. Optional adapter absence is typed unsupported.

Native compression/system-identification adapters arrive only in their gated
Goals. Docker execution uses a digest-pinned allowlist, no network, nonroot,
read-only filesystem, dropped capabilities, bounded resources, explicit
argument arrays, and captured temporary mounts. It receives no credentials,
Docker socket, ledger/CAS authority, or live source tree.

`.rci/config.toml` is human-owned policy. Backlog reconciliation is dry-run by
default. G1 manual apply may append only create, exact-dedupe, rank, and block;
close remains proposal-only. Evidence runners cannot write source, mutate Git,
edit policy, package, deploy, release, or expand authority.

## Consequences

- Optional backends cannot block or silently alter offline conclusions.
- Adapter output enters the ordinary return/decode/check/warrant pipeline.
- RCI can dogfood evidence without authorizing its own code or policy.

## Verification

Separate base and all-extras CI jobs. Assert no network in blocking tests,
fail-closed optional imports, adapter output non-self-warrant, sandbox argument
and mount policy, golden shadow reconciliation, no workspace mutation, and
proposal-only close.
