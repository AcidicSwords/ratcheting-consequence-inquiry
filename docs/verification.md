# RCI verification record

This is an append-oriented evidence log. Record commands, environment, exit
status, and material returns. A planned, skipped, unavailable, or failed check is
not passing evidence.

## G0 governance normalization — 2026-08-22

Environment: Windows PowerShell, repository
`C:\Users\Justin\Documents\Inquiry_Calculus_Wrapper`.

### Archived-source integrity

Command:

```powershell
$ErrorActionPreference='Stop'
$rx='^\| [^|]+ \| [^|]+ \| \x60(?<path>docs/spec/sources/[^\x60]+)\x60 \| (?<bytes>\d+) \| \x60(?<hash>[0-9a-f]{64})\x60 \|'
$rows=Get-Content -LiteralPath 'docs\source-manifest.md' | ForEach-Object {
  if($_ -match $rx){
    [pscustomobject]@{
      Path=$Matches.path
      Bytes=[int64]$Matches.bytes
      Hash=$Matches.hash
    }
  }
}
if($rows.Count -ne 10){throw "Expected 10 manifest rows, found $($rows.Count)"}
foreach($row in $rows){
  $item=Get-Item -LiteralPath $row.Path
  $hash=(Get-FileHash -LiteralPath $row.Path -Algorithm SHA256).Hash.ToLowerInvariant()
  if($item.Length -ne $row.Bytes -or $hash -ne $row.Hash){
    throw "Mismatch: $($row.Path)"
  }
}
"PASS: $($rows.Count) manifest archive rows match byte counts and SHA-256 digests."
```

Exit: `0`

Return:

```text
PASS: 10 manifest archive rows match byte counts and SHA-256 digests.
```

The two additive source originals were also compared directly to their archive
digests. Exit `0`:

```text
PASS: 10 archived files match expected byte counts and SHA-256 digests; both additive originals equal their archives.
```

### Requirement and ADR coverage

Command:

```powershell
$ErrorActionPreference='Stop'
$spec = Get-Content -Raw -LiteralPath 'RCI_Project_Spec.tex'
$matrix = Get-Content -Raw -LiteralPath 'docs\requirements-matrix.md'
$specIds = [regex]::Matches($spec, '\\paragraph\{(RCI-\d{3})\s+---') |
  ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique
$matrixIds = [regex]::Matches(
  $matrix, '^\| (RCI-\d{3}) \|',
  [System.Text.RegularExpressions.RegexOptions]::Multiline
) | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique
$expected = 1..68 | ForEach-Object { 'RCI-{0:d3}' -f $_ }
if(($expected | Where-Object { $_ -notin $specIds }) -or
   ($expected | Where-Object { $_ -notin $matrixIds }) -or
   $specIds.Count -ne 68 -or $matrixIds.Count -ne 68){
  throw 'Requirement coverage failure'
}
$adrCount = (Get-ChildItem -LiteralPath 'docs\adr' -Filter '*.md' -File).Count
if($adrCount -ne 8){throw "Expected 8 ADRs, found $adrCount"}
'PASS: specification and matrix each contain exactly RCI-001 through RCI-068; 8 ADRs present.'
```

Exit: `0`

Return:

```text
PASS: specification and matrix each contain exactly RCI-001 through RCI-068; 8 ADRs present.
```

### G1 command parity

Command:

```powershell
$ErrorActionPreference='Stop'
$expected = @(
  'uv lock --check',
  'uv sync --dev',
  'uv run python -c "import rci"',
  'uv run pytest -q -m "not optional"',
  'uv sync --all-extras --dev',
  'uv run ruff format --check .',
  'uv run ruff check .',
  'uv run mypy src/rci tests',
  'uv run pytest -q',
  'uv run pytest -q tests/acceptance',
  'uv run rci --help',
  'uv build'
)
foreach ($path in @('AGENTS.md','PLAN.md','docs\goals\G1.md')) {
  $lines = Get-Content -LiteralPath $path
  $start = [Array]::IndexOf($lines, $expected[0])
  if ($start -lt 0) { throw "$path lacks first gate command" }
  for ($i=0; $i -lt $expected.Count; $i++) {
    if ($lines[$start+$i] -ne $expected[$i]) {
      throw "$path gate differs at command $($i+1)"
    }
  }
}
'PASS: AGENTS.md, PLAN.md, and docs/goals/G1.md contain the identical 12-command G1 gate.'
```

Exit: `0`

Return:

```text
PASS: AGENTS.md, PLAN.md, and docs/goals/G1.md contain the identical 12-command G1 gate.
```

### Phase-boundary checks

Assertions checked that recovery execution is assigned to G2/G3, the opaque
controlled-memory benchmark is assigned to G7, and G1 explicitly excludes both
and requests no token budget.

Exit: `0`

Return:

```text
PASS: recovery execution is gated to G2/G3; opaque benchmark to G7; G1 explicitly excludes both and requests no token budget.
```

### Root instruction discovery and size

Recursive discovery found exactly one `AGENTS.md` at the repository root, size
13,244 bytes.

Exit: `0`

Return:

```text
PASS: one root AGENTS.md is discoverable and is below 32 KiB.
```

### Normative LaTeX source

A structural check counted balanced unescaped braces and validated nested
`\begin{...}`/`\end{...}` ordering.

Exit: `0`

Return:

```text
PASS: LaTeX source has balanced unescaped braces (211 pairs) and nested begin/end environments.
```

`pdflatex` availability check:

```text
UNAVAILABLE: pdflatex is not installed; the normative LaTeX source was not compiled locally.
```

This limitation remains visible; structural balance is not a substitute for a
successful LaTeX compilation.

### Live-document structure

Archived source bytes were excluded from this content check. The live
governance documents contain no generation placeholders, and every Markdown
code fence is balanced.

Exit: `0`

Return:

```text
PASS: live governance documents contain no placeholders and have balanced Markdown code fences.
```

## G1 completion gate — 2026-08-22

Environment: native Windows PowerShell, Python 3.12 through `uv`, repository
`C:\Users\Justin\Documents\Inquiry_Calculus_Wrapper`. The commands below were
run sequentially in the exact order frozen in `AGENTS.md`, `PLAN.md`, and
`docs/goals/G1.md`. Every command exited `0`.

### Frozen native gate

```text
> uv lock --check
Resolved 40 packages in 0.90ms

> uv sync --dev
Resolved 40 packages in 0.88ms
Uninstalled 12 packages in 179ms
 - anyio==4.14.2
 - certifi==2026.7.22
 - distro==1.9.0
 - h11==0.16.0
 - httpcore==1.0.9
 - httpx==0.28.1
 - idna==3.19
 - jiter==0.16.0
 - openai==2.54.0
 - sniffio==1.3.1
 - tqdm==4.70.0
 - z3-solver==4.16.0.0

> uv run python -c "import rci"
[no stdout]

> uv run pytest -q -m "not optional"
.........................s.............................................. [ 51%]
....................................................................     [100%]
139 passed, 1 skipped, 4 deselected in 3.42s

> uv sync --all-extras --dev
Resolved 40 packages in 1ms
Installed 12 packages in 512ms
 + anyio==4.14.2
 + certifi==2026.7.22
 + distro==1.9.0
 + h11==0.16.0
 + httpcore==1.0.9
 + httpx==0.28.1
 + idna==3.19
 + jiter==0.16.0
 + openai==2.54.0
 + sniffio==1.3.1
 + tqdm==4.70.0
 + z3-solver==4.16.0.0

> uv run ruff format --check .
112 files already formatted

> uv run ruff check .
All checks passed!

> uv run mypy src/rci tests
Success: no issues found in 88 source files

> uv run pytest -q
.............................s.......................................... [ 50%]
........................................................................ [100%]
143 passed, 1 skipped in 3.70s

> uv run pytest -q tests/acceptance
............                                                             [100%]
12 passed in 1.46s

> uv run rci --help
Usage: rci [OPTIONS] COMMAND [ARGS]...

Ratcheting Consequence Inquiry

+- Options -------------------------------------------------------------------+
| --install-completion          Install completion for the current shell.     |
| --show-completion             Show completion for the current shell, to     |
|                               copy it or customize the installation.        |
| --help                        Show this message and exit.                    |
+-----------------------------------------------------------------------------+
+- Commands ------------------------------------------------------------------+
| start      Start or idempotently reopen an inquiry.                         |
| step       Advance one deterministic orchestration step.                    |
| run        Run until input, satisfaction, Unknown, or the bounded step      |
|            limit.                                                           |
| resume                                                                      |
| inspect                                                                     |
| answer                                                                      |
| replay                                                                      |
| export                                                                      |
| contracts  Question contract catalog                                        |
| eval       Offline evaluation                                               |
| db         Local event database                                             |
| backlog    Governed backlog reconciliation                                  |
+-----------------------------------------------------------------------------+

> uv build
Building source distribution...
Building wheel from source distribution...
Successfully built dist\ratcheting_consequence_inquiry-0.3.1.tar.gz
Successfully built dist\ratcheting_consequence_inquiry-0.3.1-py3-none-any.whl
```

### Skip qualification

An additional `uv run pytest -q -rs` run exited `0` with `143 passed, 1
skipped`. The sole skip was
`tests/security/test_workspace_digest.py::test_workspace_digest_fails_closed_on_a_link_outside_root`:
this Windows host denied the test fixture's attempt to create a file symlink
with `WinError 1314`. The implementation's link/reparse-point rejection and its
non-symlink bounds tests ran; the same adversarial symlink case remains in the
suite for the native Linux CI lane and for Windows hosts with symlink privilege.
The skip is environmental evidence, not a local passing assertion.

### Blocking G1 evidence

The passing suite directly exercises:

- strict inert L0 payloads, deep snapshot immutability, explicit structural
  conflict only, mandatory attacks, and immutable correction succession;
- pure reducers, canonical event serialization, fail-closed schemas/upcasting,
  replay/export identity, WAL/OCC races, pre-commit folding, snapshots,
  projections, CAS tamper/dangling/orphan behavior, and exact raw-value
  distinctions;
- replay-owned step plans, exact attempt keys, the 100-event boundary, three
  attempts, typed no-attempt/presentation/capture/return/decode stages,
  first-result acceptance, and durable rejection of a late competing return;
- separately owned evidence, independent checker verdict, warrant decision,
  and promotion stages; checked environment realizability; exact closed-world
  scope; route-specific dependencies; hard-cycle and ancestry-cycle rejection;
  byte-identical SQLite rollback; guard/support/nogood invalidation and
  reopening; and exact scope/binding/universe/policy theory selection;
- recurrent probe identity and comparability, fresh-observation isolation,
  prediction-before-return, actual mismatch only, and separation of raw
  episode, decode, reconstruction, semantic delta, and active theory;
- exhaustive finite interpretation, malformed reification, optional bounded
  Z3 differential checks, independently rechecked SAT witnesses, and
  solver-trusted/non-promotable Z3-only UNSAT;
- the predetermined eight-state circuit conclusions, route bypass and
  may-versus-must distinction, SDK/CLI lifecycle parity, deterministic backlog
  shadow trace, checked-evidence gate, allowlisted manual effects, proposal-only
  close, recurrence history, ambient network denial, and bounded isolated
  evidence execution.

The requirements matrix identifies later G2--G7 work as deferred rather than
claiming it through placeholders. Docker, credentials, live OpenAI, GPU, and
later research services were not needed for this gate.

Supplementary Docker discovery found client `29.7.2`, but the local Docker
Desktop Linux daemon was stopped (`npipe:////./pipe/dockerDesktopLinuxEngine`
was absent). No local container-build result is therefore claimed. This is
nonblocking by the G1 contract; the digest-pinned Dockerfile and isolated Linux
workflow remain checked-in CI inputs, while the native Windows/Linux gate above
is canonical.

### Post-gate governance audit

Read-only closeout checks exited `0` and returned:

```text
PASS: 68 requirement IDs align; 10 source archives match; 8 ADRs; AGENTS.md=13244 bytes.
PASS: all 9 extant external source drafts still byte-match their immutable archives.
PASS: frozen 12-command gate is identical in AGENTS.md, PLAN.md, and G1 goal artifact.
PASS: live Markdown fences balanced; TeX environments 4/4; no stale G1 or superseded lifecycle terms.
PASS: 68-row closeout, zero open G1 statuses, gate parity, tracked human policy, and ignored runtime state.
```

The original v0.1 file is represented by its immutable archive because its root
path is now the normalized v0.3.1 authority. Every other source attachment or
download remained byte-identical at closeout.

## Hosted G1 verification

The public G1 history starts with baseline commit
[`c282712a1ca9e3c166457a0a8beb7d8ee353ea31`](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/commit/c282712a1ca9e3c166457a0a8beb7d8ee353ea31).
Hosted consoles exposed a presentation-sensitive acceptance assertion, fixed in
ordinary follow-up commits without rewriting the baseline. The first fully passing
hosted head is
[`76a411f3b6f552d3b0ef2539f04fe42dcd6867fc`](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/commit/76a411f3b6f552d3b0ef2539f04fe42dcd6867fc).

[GitHub Actions run 32566650112](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32566650112)
completed successfully on 2026-08-22 with these unique required job conclusions:

| Required check | Job ID | Conclusion |
|---|---:|---|
| `base (ubuntu-latest)` | [97016126204](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32566650112/job/97016126204) | `success` |
| `base (windows-latest)` | [97016126227](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32566650112/job/97016126227) | `success` |
| `extras (ubuntu-latest)` | [97016126259](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32566650112/job/97016126259) | `success` |
| `extras (windows-latest)` | [97016126223](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32566650112/job/97016126223) | `success` |
| `docker` | [97016126104](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32566650112/job/97016126104) | `success` |

The Docker job built the pinned image and ran it with networking disabled, a
read-only root filesystem, all Linux capabilities dropped, and
`no-new-privileges`. The four native jobs independently exercised both dependency
profiles on hosted Windows and Linux.

## G2A governance activation — 2026-08-22

G2A and G2B were introduced as internal gates under stable requirement RCI-058.
ADR-0009 makes G2A recovery routes provisional and unlicensed and retains
`RecoveryLicense` enforcement for G3A. No stable requirement was added or
renumbered, and the frozen G1 gate remains unchanged.

Read-only document audits exited `0` and returned:

```text
PASS: G1 gate parity in AGENTS, PLAN, G1, and G2A.
PASS: focused G2A command parity in AGENTS, PLAN, G2A, CI, and verification.
PASS: RCI-001 through RCI-068 remain exact; G2A/G2B split appears in every live architecture authority.
PASS: ADR-0009 and architecture stage provisional G2A routes before G3 licensing.
PASS: AGENTS.md=15635 bytes; live Markdown fences and git diff check pass.
```

The focused G2A command is frozen as:

```text
uv run pytest -q tests/acceptance/test_g2a_retrieval_recovery.py
```

## G2A local implementation verification — 2026-08-22

The complete frozen G1 gate and focused G2A command were rerun from branch
`goal/g2a-retrieval-recovery` after the G2A implementation. Exact local returns:

```text
uv lock --check
PASS (exit 0): Resolved 40 packages.

uv sync --dev
PASS (exit 0): base/dev environment synchronized; optional OpenAI/Z3 packages absent.

uv run python -c "import rci"
PASS (exit 0).

uv run pytest -q -m "not optional"
PASS (exit 0): 161 passed, 1 skipped, 4 deselected.

uv sync --all-extras --dev
PASS (exit 0): 40 locked packages resolved; OpenAI 2.54.0 and z3-solver 4.16.0.0 installed.

uv run ruff format --check .
PASS (exit 0): 124 files already formatted.

uv run ruff check .
PASS (exit 0): All checks passed.

uv run mypy src/rci tests
PASS (exit 0): 98 source files checked with no issues.

uv run pytest -q
PASS (exit 0): 165 passed, 1 skipped.

uv run pytest -q tests/acceptance
PASS (exit 0): 15 passed.

uv run pytest -q tests/acceptance/test_g2a_retrieval_recovery.py
PASS (exit 0): 3 passed.

uv run rci --help
PASS (exit 0): lifecycle, contracts, eval, db, backlog, memory, and recovery groups present.

uv build
PASS (exit 0): source archive and universal wheel built for version 0.3.1.
```

The focused evidence covers deterministic retrieval and CLI parity, exact route
separation, a baseline/retained circuit pair with one effect each and a strict
three-probe versus two-probe Pareto improvement, independently checked soft
comparison, resumable request/child/link prefixes, same-batch saga rejection,
wrong-context child rejection, unfinished-child rejection, and mutation-bound
measurement/comparison checks. Unit and replay suites additionally cover
permutation stability, exact scope/binding/horizon isolation, bounds, stale refs,
ambiguous reconstruction, generated-detail containment, eventual-success-only,
incomparable/evaluator-mismatched frontiers, and the archived 11-event G1 vertical
slice with byte-identical export and unchanged G1 projection digest.

The local Docker client was version 29.7.2, but the Docker Desktop Linux daemon
was stopped, so no local image result is claimed. Docker is supplementary and
nonblocking. The hosted verification below supplies the required container
evidence.

## G2A hosted PR verification — 2026-08-22

Commit [`1dea7d1`](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/commit/1dea7d17466d0ec26b3907a72315279424f9dbab)
was verified in [pull request 1](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/pull/1).
The canonical pull-request workflow was
[run 32573442799](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32573442799),
which completed successfully with these five unique job names:

| Required job | Hosted job | Conclusion |
|---|---|---|
| `base (ubuntu-latest)` | [97032207945](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32573442799/job/97032207945) | `success` |
| `base (windows-latest)` | [97032207898](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32573442799/job/97032207898) | `success` |
| `extras (ubuntu-latest)` | [97032207926](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32573442799/job/97032207926) | `success` |
| `extras (windows-latest)` | [97032207805](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32573442799/job/97032207805) | `success` |
| `docker` | [97032207935](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32573442799/job/97032207935) | `success` |

The Docker job built and executed the pinned image under the repository's
network-disabled, read-only, capability-dropped policy. The four native jobs
proved the base and optional dependency profiles on both hosted Windows and
Linux. The branch remained subject to the protected-`main` pull-request and
required-check boundary; no release, deployment, or authority expansion was
performed.

## G2B governance activation — 2026-08-22

G2A is sealed at merged `main` commit `5d4d637`. ADR-0010 and
`docs/goals/G2B.md` define the remaining RCI-058 boundary: deterministic consolidation,
versioned reconsolidation, conservative semantic-field evaluation, and checked learned-
probe admission.

The focused G2B command is frozen as:

```text
uv run pytest -q tests/acceptance/test_g2b_consolidation_plasticity.py
```

## G2B local verification — 2026-08-22

The complete native G2B gate passed locally on Windows after the implementation. Exact
returns were:

- `uv lock --check`: exit 0; 40 locked packages resolved.
- `uv sync --dev`: exit 0; base development environment synchronized.
- `uv run python -c "import rci"`: exit 0.
- `uv run pytest -q -m "not optional"`: 166 passed, 1 skipped, 4 deselected.
- `uv sync --all-extras --dev`: exit 0; OpenAI and pinned Z3 extras synchronized.
- `uv run ruff format --check .`: 131 files already formatted.
- `uv run ruff check .`: all checks passed.
- `uv run mypy src/rci tests`: success across 103 source files.
- `uv run pytest -q`: 170 passed, 1 skipped.
- `uv run pytest -q tests/acceptance`: 16 passed.
- `uv run pytest -q tests/acceptance/test_g2a_retrieval_recovery.py`: 3 passed.
- `uv run pytest -q tests/acceptance/test_g2b_consolidation_plasticity.py`: 1 passed.
- `uv run rci --help`: exit 0 and lists `memory`, `field`, and `probes` groups.
- `uv build`: exit 0; sdist and wheel built.

The sole skip remains the already disclosed native-Windows symlink privilege case
(`WinError 1314`); Linux CI retains that adversarial path. The G2B acceptance proves an
older circuit exception is interleaved with recent episodes, consolidation creates only
an ordinary claim and open attacks, field overflow creates an ordinary residual, a
tampered holdout score is rejected, generic learned-probe admission is rejected, and the
checked controller path admits the backup-power separator without creating a lemma or
licence. Frozen G1 replay remains byte-identical, existing G2A acceptance remains green,
and the G1/G2A event class definitions were not changed; G2B adds only new version-1
event kinds and folded-state schema v3.

## G2B hosted pull-request verification — 2026-08-22

Implementation commit `1154d67e7081db49aa206eea5f639dce2f963c48` was pushed in
[pull request 2](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/pull/2).
The protected [pull-request workflow](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32576659315)
completed successfully with all five unique jobs:

- [`base (ubuntu-latest)`](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32576659315/job/97039887350): success;
- [`base (windows-latest)`](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32576659315/job/97039887391): success;
- [`extras (ubuntu-latest)`](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32576659315/job/97039887397): success;
- [`extras (windows-latest)`](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32576659315/job/97039887364): success;
- [`docker`](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32576659315/job/97039887392): success.

The independent [branch-push workflow](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32576657003)
also completed all five jobs successfully. The documentation commit and its protected
checks must pass before merge; the post-merge `main` run remains the final G2B gate.

### G2B post-merge completion

Protected PR #2 merged linearly. Commit
`a5ac134981494cd126261117828140e7151eaf39` passed post-merge workflow
`32576841848`; all unique required jobs concluded `success`:

- `base (ubuntu-latest)`;
- `base (windows-latest)`;
- `extras (ubuntu-latest)`;
- `extras (windows-latest)`;
- `docker`.

G2B and RCI-058 are sealed and verified at that anchor.

## RCI v0.4 governance normalization — 2026-08-22

RCI v0.4 adopts ADR-0011 and distinguishes the replay-complete aggregate fold
from binding-derived realized history, configuration projection, and a G3
consequence-sufficient retained state. Requirements RCI-001–RCI-068 retain their
stable identifiers and RCI-069–RCI-071 add aggregate/state separation,
continuation compatibility, and representation succession.

The package metadata advances to 0.4.0 without a release or tag. All G1/G2 event
classes remain schema version 1. Their canonical JSON-schema hashes at
`a5ac134981494cd126261117828140e7151eaf39` are frozen in
`tests/fixtures/compat/g2b-event-schema-manifest.json` and checked on every run.

The parity fixture wording is corrected: `{a}*` is an unbounded history carrier
with a finite two-state quotient. G3A-H must prove it through finite transition
congruence/base-step reasoning rather than bounded sampling. SymPy remains
deferred to G3A-L.

Local governance and regression returns:

- authority check: exactly RCI-001 through RCI-071 in both spec and matrix;
- v0.4 source SHA-256:
  `30a3c167f6ecf0e14b8c16273addcafa9bdf304bd4e761c0429e1d5c4516a955`;
- root AGENTS size: 17,550 bytes;
- `uv lock --check`, base/all-extras synchronization, import/version check,
  Ruff, mypy over 104 source files, CLI help, and build: exit 0;
- non-optional pytest: 167 passed, 1 skipped, 4 deselected;
- full pytest: 171 passed, 1 skipped;
- acceptance: 16 passed;
- archived G1 plus sealed G2 schema compatibility: 2 passed;
- G2A/G2B focused acceptance: 4 passed;
- package build: 0.4.0 sdist and universal wheel.

The sole skip remains the documented native-Windows symlink privilege case. No
G3A-H runtime claim is made by this normalization alone. Hosted PR and post-merge
returns are recorded after the protected workflow completes.

## G3A-H local implementation verification — 2026-08-22

The bounded exact history-state implementation adds only new version-1 event kinds and
advances the rebuildable folded-state schema to v4. Sealed G1/G2 event JSON schemas are
unchanged. A frozen G2B stream extension at the `a5ac134` anchor now joins the archived
G1 corpus; both replay and export identically with all G3 collections empty.

Exact local returns after the implementation stabilized:

- `uv lock --check`: exit 0; 40 locked packages resolved;
- `uv sync --dev`: exit 0; base environment synchronized;
- `uv run python -c "import rci"`: exit 0; package version 0.4.0;
- `uv run pytest -q -m "not optional"`: 172 passed, 1 skipped, 4 deselected;
- `uv sync --all-extras --dev`: exit 0; optional OpenAI/Z3 extras synchronized;
- `uv run ruff format --check .`: 140 files formatted;
- `uv run ruff check .`: all checks passed;
- `uv run mypy src/rci tests`: success across 109 source files;
- `uv run pytest -q`: 176 passed, 1 skipped;
- `uv run pytest -q tests/acceptance`: 18 passed;
- G2A/G2B focused acceptance: 4 passed;
- `uv run pytest -q tests/acceptance/test_g3a_history_state.py`: 2 passed;
- `uv run rci --help`: exit 0 and lists the `compression` group;
- `uv build`: exit 0; version 0.4.0 sdist and universal wheel built.

The sole skip remains the disclosed Windows symlink-privilege fixture. The G3A-H
acceptance proves an unbounded unary-history carrier through finite base/transition
congruence, exact factorization and recursive update; rejects the reopened singleton
quotient; rejects count as an order-sensitive state; distinguishes present-answer
sufficiency from continuation compatibility; independently checks realized-history
derivation; rejects a forged prefix digest without a ledger write; keeps package,
validation, licence, application, and capability stages separate; records exact path
residue; derives a licensed retained-state view; rejects predecessor capability loss;
records a warranted strict successor; and reopens by checked factorization failure.

## G3A-H hosted pull-request verification — 2026-08-22

Pull request [#4](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/pull/4)
verified implementation commit
`5a3297b9da975628c4dbd1ae0130267f1b1a5e0b`. The protected pull-request run
[32581474989](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32581474989)
completed successfully with all five unique required jobs:

- `base (ubuntu-latest)`: success, job `97051397357`;
- `base (windows-latest)`: success, job `97051397302`;
- `extras (ubuntu-latest)`: success, job `97051397328`;
- `extras (windows-latest)`: success, job `97051397190`;
- `docker`: success, job `97051397283`.

The branch push run
[32581472468](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32581472468)
also completed all five jobs successfully at the same commit. The pull-request jobs ran
the frozen G1 gate and the focused G2A, G2B, and G3A-H commands on both native operating
systems; the Docker job built and executed the pinned network-disabled, read-only image.

## G3A-H protected-main verification — 2026-08-22

Pull request #4 was merged with linear history. Its two commits were rewritten on
protected `main` as implementation commit
`5969a0ab48e35ab865932479409d75338b3f6d85` and evidence commit
`f03b774f2f29b162a3fc828893a541a6f9049866`.

Post-merge run
[32581710548](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32581710548)
completed successfully at `f03b774f2f29b162a3fc828893a541a6f9049866` with all five
required jobs:

- `base (ubuntu-latest)`: success, job `97051969823`;
- `base (windows-latest)`: success, job `97051970006`;
- `extras (ubuntu-latest)`: success, job `97051969989`;
- `extras (windows-latest)`: success, job `97051969921`;
- `docker`: success, job `97051970073`.

This seals the bounded G3A-H implementation. G3A-L, G3B, G3C, and all later milestones
remain deferred and unclaimed.

## G3R local candidate verification — 2026-08-22

RCI v0.5 adds RCI-072–RCI-078 and the bounded recursive-project binding in ADR-0012 and
ADR-0013. All predecessor event classes remain version 1 and retain their frozen schema
manifest. New G3R event kinds are version 1; folded state advances to v5 and rebuilds
v1–v4 snapshots from the ledger. The runtime records candidate-development evidence but
still has no source-writing, arbitrary-command, Git, merge, push, credential, policy,
release, deployment, or authority-expansion port.

The checked six-candidate roadmap frontier remains a partial order. It selects
regenerative question-contract synthesis only as the smallest reversible discriminator;
G3A-L, native-method binding, autonomous Goal synthesis, isolated candidate actuation,
and G4 remain nondominated. At this local-candidate stage, `docs/goals/G3Q.md` was
sealed next but remained inactive pending the hosted boundary recorded below.

Exact local returns after the self-warrant audit and hardening pass:

- requirements parity: exactly RCI-001 through RCI-078 in the spec and matrix;
- recursive source archive: 2,613 bytes, SHA-256
  `2ef54c70faeca5e4091f96e081a35ce12e990d4719453bcd175b2ba2cd696c8b`;
- root `AGENTS.md`: 20,642 bytes, below 32 KiB;
- `uv lock --check`: exit 0, 40 packages resolved;
- `uv sync --dev`: exit 0;
- `uv run python -c "import rci"`: exit 0, package version 0.5.0;
- `uv run pytest -q -m "not optional"`: 183 passed, 1 skipped, 4 deselected;
- `uv sync --all-extras --dev`: exit 0;
- `uv run ruff format --check .`: 152 files formatted;
- `uv run ruff check .`: all checks passed;
- `uv run mypy src/rci tests`: success across 114 source files;
- `uv run pytest -q`: 187 passed, 1 skipped;
- `uv run pytest -q tests/acceptance`: 25 passed;
- `uv run rci --help`: exit 0 and lists the `project` group;
- `uv build`: exit 0; 0.5.0 sdist and universal wheel built;
- `uv run pytest -q tests/acceptance/test_recursive_project_inquiry.py`: 7 passed;
- archived G1/G2 schema, replay, and v1–v4 snapshot rebuild focus: 5 passed,
  15 deselected.

The focused acceptance proves permutation-stable partial-order selection, all-six
nondominated roadmap dogfooding, inert generated questions, two consequential return
classes, unowned-evidence rejection, exact reviewed question/method admission, immutable
Goals, exact anchor/candidate pins, self-review rejection, failing-evidence rejection,
unreviewed-evidence substitution rejection, separate successor/promotion records,
effect-free replay, and a deterministic canonical-JSON CLI inspection surface.

The sole skip remains the disclosed native-Windows symlink-privilege fixture.

## G3R hosted verification and protected promotion — 2026-08-22

The exact candidate head was
`15971d7293ad2008aded614ec0843083f02c8780`. Pull request
[#6](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/pull/6) preserved the
sealed Goal and merged by protected linear rebase as
`6b0f2f793130d91bddaf1a2cffa9be87fd8b4e6d`.

Fresh review used two detached, read-only exact-head contexts with repository editing and
Git mutation denied. GitHub Copilot CLI review session
`0ea60e53-7c1a-4035-a48f-39f74b5e6a11` returned `Valid` for candidate
`66008fc183d79b15261c994a45327f0cecdde982`; after the hosted-check naming fix, session
`bc13b7df-70bb-4d2c-ad65-4ac274410662` independently returned `Valid` for exact head
`15971d7293ad2008aded614ec0843083f02c8780`, with zero file changes. The preserved review
summary is [PR comment 5381694084](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/pull/6#issuecomment-5381694084).
A separately requested hosted Codex review returned a usage-limit notice; it is recorded
as indeterminate and contributes no warrant.

Both the exact-head push
[run 32587865627](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32587865627)
and pull-request
[run 32587866957](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32587866957)
passed all six unique jobs:

- `base (ubuntu-latest)`: PR job `97066894736`, success;
- `base (windows-latest)`: PR job `97066894750`, success;
- `extras (ubuntu-latest)`: PR job `97066894681`, success;
- `extras (windows-latest)`: PR job `97066894737`, success;
- `docker`: PR job `97066894717`, success;
- `recursive (ubuntu-latest)`: PR job `97066894753`, success.

Protected-main post-merge
[run 32588028074](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32588028074)
at exact SHA `6b0f2f793130d91bddaf1a2cffa9be87fd8b4e6d` also passed:

- `base (ubuntu-latest)`: job `97067271271`, success;
- `base (windows-latest)`: job `97067271291`, success;
- `extras (ubuntu-latest)`: job `97067271319`, success;
- `extras (windows-latest)`: job `97067271214`, success;
- `docker`: job `97067271241`, success;
- `recursive (ubuntu-latest)`: job `97067271103`, success.

`main` protection requires pull requests with zero mandatory approvals, current strict
status from all six checks, linear history, owner enforcement, and blocks force pushes
and deletion. This completes the G3R boundary. G3Q is now the active bounded Goal; its
implementation was not begun during G3R.

## G3Q local candidate verification — 2026-08-22

The candidate starts from exact protected-main anchor
`b20935c712e3bd0a3d16aa5445c40c5297eb77c7` on branch
`codex/g3q-regenerative-questions`. It reuses the sealed
`QuestionContractCandidate`/`QuestionRepertoireDecision` records and ordinary
obligation/effect/claim events. `CompiledQuestionContract` is a deterministic derived
view, so no event class, folded-state field, snapshot schema, or dependency changed.

The compiler admits only the exact `recursive-project-v1` policy and pins the clean
anchor, candidate and decision fingerprints, compiler and controller policies, binding,
scope, protected horizon, comparison policy, typed owned referents, and allowlisted
consumer. The SDK and canonical-JSON CLI can inspect the projection and open an ordinary
question obligation. Returned payloads remain provisional; a declared exact return
class opens its typed ordinary downstream obligation, while any other payload—including
prompt-injection text—opens an unclassified residual. Neither route creates warrant,
promotion, procedural knowledge, source authority, or Git authority.

Exact local returns:

- requirements parity: 78 unique IDs in both spec and matrix;
- root `AGENTS.md`: 21,296 bytes, below 32 KiB;
- `uv lock --check`: exit 0, 40 packages resolved;
- `uv sync --dev`: exit 0;
- `uv run python -c "import rci; print(rci.__version__)"`: exit 0, `0.5.0`;
- `uv run pytest -q -m "not optional"`: 190 passed, 1 skipped, 4 deselected;
- `uv sync --all-extras --dev`: exit 0;
- `uv run ruff format --check .`: 154 files formatted;
- `uv run ruff check .`: all checks passed;
- `uv run mypy src/rci tests`: success across 116 source files;
- `uv run pytest -q`: 194 passed, 1 skipped;
- `uv run pytest -q tests/acceptance`: 32 passed on the serial exact rerun;
- `uv run rci --help`: exit 0 and lists the `project` group;
- `uv build`: exit 0; 0.5.0 sdist and universal wheel built;
- `uv run pytest -q tests/acceptance/test_regenerative_questions.py`: 7 passed.

The focused acceptance proves deterministic registry order, exact context isolation,
owned-but-unadmitted and foreign candidate inertness, stale-policy and malformed-policy
rejection, exact binding validation, two-return downstream divergence, prompt-injection
containment, built-in scheduler non-regression, replay/export identity, CLI/SDK parity,
and absence of self-warrant. One overlapping diagnostic invocation encountered a
Windows file lock because an earlier yielded pytest subprocess still owned the shared
`.pytest-tmp` SQLite file; it is not counted as evidence. After the process exited, the
same canonical acceptance command passed serially with 32 tests.

At this local-candidate checkpoint, hosted CI, exact-head independent review, protected
promotion, and post-merge evidence remained pending. The following section records their
later exact returns and supersedes that provisional disposition.

## G3Q hosted verification and protected promotion — 2026-08-22

The exact candidate commit was
`fbb9a19649c6e60e9d1a0e636c424170b83a86ca`. Pull request
[#8](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/pull/8) retained exact
base `b20935c712e3bd0a3d16aa5445c40c5297eb77c7` and merged by protected linear rebase as
`433a24ba31c14db95fb71d9ca1440e4d24c707d5`.
GitHub [Rebase-and-Merge](https://docs.github.com/en/pull-requests/reference/pull-request-merges#rebase-and-merge-your-commits)
rewrites the commit SHA even when the head is already based on the base commit. The PR API
records `fbb9a196...` as `headRefOid` and `433a24ba...` as
`mergeCommit`; both commits have parent `b20935c...`, exact tree
`bef9daa39beb0f702054ab48e5abfc60964c5cc1`, and an empty pairwise diff. The promoted
content is therefore exact even though the candidate commit is intentionally not an
ancestor of the rewritten protected-main commit.

The requested hosted Codex review returned a usage-limit notice in
[PR comment 5381876187](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/pull/8#issuecomment-5381876187).
It is `Indeterminate` and contributes no warrant. A separate fresh, read-only GitHub
Copilot CLI review evaluated the exact committed diff
`b20935c712e3bd0a3d16aa5445c40c5297eb77c7..fbb9a19649c6e60e9d1a0e636c424170b83a86ca`,
reported no actionable findings across authority escalation, admission conflict and
staleness, context mismatch, scheduler suppression, replay, stage separation, CLI/SDK
parity, and regressions, and made no file change. Its preserved summary is
[PR comment 5381903569](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/pull/8#issuecomment-5381903569).

The exact-head pull-request
[run 32590137359](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32590137359)
passed all seven unique jobs:

- `base (ubuntu-latest)`: job `97072562639`, success;
- `base (windows-latest)`: job `97072562539`, success;
- `extras (ubuntu-latest)`: job `97072562502`, success;
- `extras (windows-latest)`: job `97072562528`, success;
- `docker`: job `97072562438`, success;
- `recursive (ubuntu-latest)`: job `97072562544`, success;
- `regenerative (ubuntu-latest)`: job `97072562576`, success.

Protected-main post-merge
[run 32590581711](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32590581711)
at exact SHA `433a24ba31c14db95fb71d9ca1440e4d24c707d5` also passed:

- `base (ubuntu-latest)`: job `97073668634`, success;
- `base (windows-latest)`: job `97073668630`, success;
- `extras (ubuntu-latest)`: job `97073668622`, success;
- `extras (windows-latest)`: job `97073668599`, success;
- `docker`: job `97073668611`, success;
- `recursive (ubuntu-latest)`: job `97073668633`, success;
- `regenerative (ubuntu-latest)`: job `97073668524`, success.

Before merge, a protection read-back exposed that only the predecessor six checks were
required. The status-check subresource was corrected and read back again. Protected
`main` now requires pull requests with zero mandatory approvals, current strict status
from all seven GitHub Actions checks with app ID `15368`, linear history, owner
enforcement, and blocks force pushes and deletion. This seals G3Q without granting RCI or
the development agent runtime merge authority.

## Post-G3Q recursive frontier selection — 2026-08-22

The selection cycle begins from clean protected-main anchor
`4d89bb776181dd0b7885b0e0dd1042426d0456ca` on documentation-only branch
`codex/post-g3q-frontier`. It changes no runtime code, dependency, event class, snapshot,
effect port, Git authority, or protected check. The immutable reasoning record is
`docs/recursion/cycles/post-g3q-frontier.md`; ADR-0014 records the selected confined
Goal-synthesis boundary, and `docs/goals/G3G.md` is deliberately non-active until a
protected promoted anchor replaces its placeholder.

The existing strict models accepted one inert `QuestionContractCandidate` with exact
owned anchor/limitation/frontier referents, two distinct returns
(`goal-derivation-required` and `method-transport-required`), one exact comparison policy,
one consumer, and three falsifying attacks. This did not admit or schedule the candidate.

The existing `derive_capability_frontier` implementation was then run over G3G, G3A-L,
native-method binding, isolated candidate actuation, and G4 in original and reversed
order. Exact model equality held. All five candidates remain nondominated and all ten
pairs remain incomparable because their typed gains differ. Under two explicitly bounded
inventory axes—missing executable seams and new authority-risk boundaries—G3G is the
componentwise cost-minimal reversible candidate with a discriminator. The result selected
which discriminator to run first; it did not create a universal roadmap ranking.

The selection consulted primary/native sources for narrow transported relations:

- van Lamsweerde and Letier on goal refinement and obstacle analysis:
  <https://www.cs.ucf.edu/~turgut/heng_than.pdf>;
- Jackson and Zave on separating desired environment requirements from implementable
  machine specifications:
  <https://www.researchgate.net/publication/221553733_Deriving_Specifications_from_Requirements_An_Example>;
- Solar-Lezama on the bounded candidate/validator/counterexample recurrence and lawful
  no-solution behavior, without treating Goal compilation as program synthesis:
  <https://people.csail.mit.edu/asolar/papers/thesis.pdf>;
- Rice on typed algorithm-selection spaces rather than a universal scalar method score:
  <https://dblp.org/rec/journals/ac/Rice76>.

Exact local returns after the governance edits:

- `uv lock --check`: exit 0, 40 packages resolved;
- `uv sync --dev`: exit 0;
- `uv run python -c "import rci; print(rci.__version__)"`: exit 0, `0.5.0`;
- `uv run pytest -q -m "not optional"`: 190 passed, 1 skipped, 4 deselected;
- `uv sync --all-extras --dev`: exit 0;
- `uv run ruff format --check .`: 158 files already formatted;
- `uv run ruff check .`: all checks passed;
- `uv run mypy src/rci tests`: success across 116 source files;
- `uv run pytest -q`: 194 passed, 1 skipped;
- `uv run pytest -q tests/acceptance`: 32 passed;
- `uv run rci --help`: exit 0 and lists the `project` group;
- `uv build`: exit 0; 0.5.0 sdist and universal wheel built;
- `uv run pytest -q tests/acceptance/test_recursive_project_inquiry.py`: 7 passed;
- `uv run pytest -q tests/acceptance/test_regenerative_questions.py`: 7 passed;
- requirement parity: 78 unique stable IDs in both specification and matrix;
- root `AGENTS.md`: 22,302 bytes, below 32 KiB;
- ADR inventory: 14, including pending implementation decision ADR-0014.

At this local checkpoint, exact-head review, protected promotion, and post-merge checks
remained pending. The following section records their later exact returns and supersedes
that provisional disposition.

## Post-G3Q selection hosted verification and protected promotion — 2026-08-22

The exact candidate was `faf5c8b5f5a54b1598e8af03b71cf8f39c36d054` from base
`4d89bb776181dd0b7885b0e0dd1042426d0456ca`. Pull request
[#10](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/pull/10) merged by
protected linear rebase as `60ff25635f94fb004e6419a09293c5e0fc023074`.
Both commits have exact parent `4d89bb776181dd0b7885b0e0dd1042426d0456ca`, exact tree
`9dc374a47c8d58f5edea3dd8cd937287f1cfa2c5`, and an empty pairwise diff.

Hosted Codex quota, GitHub Copilot pull-request-review nonavailability, exhausted Copilot
CLI quota, and an invalid configured OpenAI API credential were preserved as independent
`Indeterminate` returns. A fresh stateless local `qwen3.5:9b` context reviewed the exact
base/head, ADR-0013 contract, immutable cycle report, and complete committed patch. Its
JSON-schema-constrained return pinned both exact commits, reported `Valid` with no
findings, and made no repository change. The prompt contained 27,059 tokens and the
bounded return 297 tokens. The full summary and limitations are preserved in
[PR comment 5382180753](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/pull/10#issuecomment-5382180753).

Exact-head pull-request
[run 32592149739](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32592149739)
passed:

- `base (ubuntu-latest)`: job `97077535928`, success;
- `base (windows-latest)`: job `97077535749`, success;
- `extras (ubuntu-latest)`: job `97077535889`, success;
- `extras (windows-latest)`: job `97077535862`, success;
- `docker`: job `97077535895`, success;
- `recursive (ubuntu-latest)`: job `97077535870`, success;
- `regenerative (ubuntu-latest)`: job `97077535839`, success.

Protected-main post-merge
[run 32593669603](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32593669603)
at exact SHA `60ff25635f94fb004e6419a09293c5e0fc023074` passed:

- `base (ubuntu-latest)`: job `97081242554`, success;
- `base (windows-latest)`: job `97081242524`, success;
- `extras (ubuntu-latest)`: job `97081242487`, success;
- `extras (windows-latest)`: job `97081242527`, success;
- `docker`: job `97081242441`, success;
- `recursive (ubuntu-latest)`: job `97081242394`, success;
- `regenerative (ubuntu-latest)`: job `97081242472`, success.

The protection read-back required all seven strict current checks with linear history and
owner enforcement and denied force pushes and deletion. This seals the selection only:
G3G is the next no-budget Goal at exact anchor
`60ff25635f94fb004e6419a09293c5e0fc023074`, but no G3G implementation was performed.

## Active G3G local verification

G3G preserves `60ff25635f94fb004e6419a09293c5e0fc023074` as its selection
anchor and begins implementation from protected development anchor
`defeb5c2dad32b86cc1861d4f3c35522a3f0497f`.

Focused command:

```text
uv run pytest -q tests/acceptance/test_goal_synthesis.py
```

Local results on the G3G candidate worktree:

- `uv lock --check`: passed, 40 packages resolved;
- `uv sync --dev`: passed;
- `uv run python -c "import rci"`: passed;
- `uv run pytest -q -m "not optional"`: 194 passed, one intentional platform
  skip, four optional tests deselected;
- `uv sync --all-extras --dev`: passed;
- `uv run ruff format --check .`: 160 files formatted;
- `uv run ruff check .`: passed;
- `uv run mypy src/rci tests`: 118 source files passed;
- `uv run pytest -q`: 198 passed, one intentional platform skip;
- `uv run pytest -q tests/acceptance`: 35 passed;
- `uv run rci --help`: passed and exposed no execution authority;
- `uv build`: source distribution and wheel built successfully;
- `uv run pytest -q tests/acceptance/test_goal_synthesis.py`: 3 passed.

The folded-state schema advanced from v5 to v6. Versions v1 through v5 are discarded
as derived snapshots and rebuilt from the unchanged authoritative event ledger. At this
checkpoint hosted exact-head conclusions remained pending; the following section records
their later returns and supersedes that provisional disposition.

## G3G hosted verification and protected promotion — 2026-08-22

The exact implementation candidate was
`ebdcee241fb9d8306df5ebe316e506ed7d9a202b` from protected development anchor
`defeb5c2dad32b86cc1861d4f3c35522a3f0497f`. Pull request
[#12](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/pull/12) merged by
protected linear rebase as `5f48d397030b6a063fdca19e51b70a824096e564`. The immutable
selection anchor remains `60ff25635f94fb004e6419a09293c5e0fc023074`.

Two fresh stateless local `qwen3.5:9b` review attempts failed the requested JSON-only
review contract, misclassified the task as test generation, and emitted invented code.
Both returns are preserved as `Indeterminate`; neither changed the repository or counts
as review evidence. The deterministic compiler/reducer recomputation, adversarial tests,
and hosted CI remain the standing evidence.

Exact pull-request
[run 32596264093](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32596264093)
passed:

- `base (ubuntu-latest)`: job `97087630940`, success;
- `base (windows-latest)`: job `97087631047`, success;
- `extras (ubuntu-latest)`: job `97087631068`, success;
- `extras (windows-latest)`: job `97087631091`, success;
- `docker`: job `97087631074`, success;
- `recursive (ubuntu-latest)`: job `97087631067`, success;
- `regenerative (ubuntu-latest)`: job `97087631081`, success;
- `goal-synthesis (ubuntu-latest)`: job `97087631070`, success.

Protected-main post-merge
[run 32596365612](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32596365612)
at exact SHA `5f48d397030b6a063fdca19e51b70a824096e564` passed:

- `base (ubuntu-latest)`: job `97087894060`, success;
- `base (windows-latest)`: job `97087894034`, success;
- `extras (ubuntu-latest)`: job `97087894043`, success;
- `extras (windows-latest)`: job `97087893954`, success;
- `docker`: job `97087894012`, success;
- `recursive (ubuntu-latest)`: job `97087893901`, success;
- `regenerative (ubuntu-latest)`: job `97087894070`, success;
- `goal-synthesis (ubuntu-latest)`: job `97087894005`, success.

Branch-protection read-back requires all eight strict current checks, including the new
goal-synthesis context, with linear history and owner enforcement; force pushes and
deletion remain blocked. G3G is sealed. No later frontier member is selected or active.

## G3V stopped-indeterminate disposition — 2026-08-22

G3V began from protected-main anchor
`b6069c0a58a669eed21005bada407eff1828071a`. Its implementation commit was
`21855a932a45b8d38118dca3447697bf7ab2c1eb`; the final documentation head was
`a425f4b0dfa5b2c52a67df87d460f25e4e825518` on pull request
[#14](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/pull/14).

The candidate's recorded local returns were:

- focused bounded-review acceptance: 6 passed;
- non-optional suite: 200 passed, one intentional platform skip, four deselected;
- full suite: 204 passed, one intentional platform skip;
- acceptance suite: 41 passed;
- mypy: 120 source files passed;
- Ruff format/check and build: passed.

Hosted candidate [run
32600257888](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32600257888)
reported success for all nine candidate contexts:

- `base (ubuntu-latest)`: job `97097350801`;
- `base (windows-latest)`: job `97097350757`;
- `extras (ubuntu-latest)`: job `97097350765`;
- `extras (windows-latest)`: job `97097350769`;
- `docker`: job `97097350664`;
- `recursive (ubuntu-latest)`: job `97097350777`;
- `regenerative (ubuntu-latest)`: job `97097350791`;
- `goal-synthesis (ubuntu-latest)`: job `97097350774`;
- `review-equivalence (ubuntu-latest)`: job `97097350763`.

Fresh exact-head semantic review from a context distinct from the developer was
unavailable. That return is `Unknown`. Because G3R requires it and G3V explicitly forbids
its bounded profile from substituting for it, no `IndependentReview`, successor
decision, or promotion was lawful. PR #14 was closed without merge and its branch was
retained. The executable candidate is not part of protected main; RCI-079 remains
unverified and may be reopened only through a new Goal.

## G3FO stopped-indeterminate disposition and grammar reconciliation — 2026-08-23

G3FO began from protected-main anchor
`ed6f5922815a29b856786660e76d62b68eeae26a`. PR #16 preserved four candidate heads:

- `f6ba64c7adfe87ff27dea9e590f7a95343cff791`: invalid; evaluation trusted a
  caller-authored lifecycle, comparison policy was decorative, permutation changed a
  result, stage outcomes collapsed, handoff was not resolvable, and the weak fixture was
  self-authored;
- `f0592800e983b9a5655f82f381a34cae38288032`: invalid; authority could be appended
  after return, reopening was self-authorizable, decode/check stages still collapsed,
  and fixture pins were forgeable;
- `ee32c3fad87dab177c372bbd7ba4cb089167b2ce`: invalid; pre-return checks could validate
  later returns, late rejected evidence superseded accepted standing, continuation pins
  were incomplete, and duplicate tasks collapsed;
- `b3cb06363ac5b8cd60c9bfbda5c3fbdd7dca72fb`: repaired final candidate; review
  conclusion unavailable.

The final candidate added explicit authority regressions for pre-return project/evidence
antecedence, independently checked assistance, lawful delivery retry, accepted-evidence
dominance, pending/decode/check/operational separation, exact raw/decode/check handoff
references, task/expectation/operation/effect/discriminator continuity, independently
checked route/decoder reopening, closed neutral task mapping, and owned branch comparison.

The complete local gate passed at the exact final head:

- `uv lock --check`: passed;
- `uv sync --dev`: passed;
- `uv run python -c "import rci"`: passed;
- `uv run pytest -q -m "not optional"`: 215 passed, one documented skip, four
  deselected;
- `uv sync --all-extras --dev`: passed;
- `uv run ruff format --check .`: 170 files formatted;
- `uv run ruff check .`: passed;
- `uv run mypy src/rci tests`: 121 source files passed;
- `uv run pytest -q`: 219 passed, one documented skip;
- `uv run pytest -q tests/acceptance`: 56 passed;
- every sealed predecessor focused command passed with counts 3, 1, 2, 7, 7, and 3;
- `uv run pytest -q tests/acceptance/test_capability_failure_observation.py`: 21
  passed;
- `uv run rci --help` and `uv build`: passed; sdist and wheel built.

Hosted exact-head run
[`32619654627`](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32619654627)
passed all nine jobs: base on Ubuntu/Windows; extras on Ubuntu/Windows; recursive,
regenerative, goal-synthesis, and failure-observation on Ubuntu; and Docker.

Fresh review remained a blocking relation. The hosted Codex reviewer reported exhausted
code-review quota on PR #16. A GitHub Copilot review request produced no reviewer or
review, and the installed local Codex executable was inaccessible. These are unavailable
review returns, not semantic validation. In accordance with the presealed boundary,
G3FO was stopped indeterminate, PR #16 was closed without merge, and its branch was
retained. No G3FO source, CI requirement, evaluator, handoff, or claimed weak-reasoner
improvement entered protected main.

Three candidate source documents are preserved byte-for-byte:

- operator-first calculus: 104223 bytes, SHA-256
  `fc821f187f6c1a608135d698f704d9e59892e1776276a52002d13b44190f2858`;
- canonical regenerative calculus: 48267 bytes, SHA-256
  `3f8e6647a692787402657e0fa4e4c13c01a0449ee2cf057c450737915f48ce82`;
- proposed compositional grammar: 28181 bytes, SHA-256
  `5585c5bfb6e9e31ce72dac173ba1b9a7de008fec08d254a59f0c0931d15f0860`.

ADR-0016 records their candidate correspondences and rejected collapses. Requirement
parity remains exactly RCI-001--RCI-079; no new stable requirement or v0.6 authority was
allocated. The post-G3FO frontier is `Unknown`: the preserved reviews demonstrated
authority/lifecycle/implementation defects, not two verified failures requiring a shared
dependent-question frame. G3Q-F therefore remains a candidate and no successor Goal is
active.

The documentation-only stop/reconciliation tree then passed the unchanged protected
gate locally: source integrity 15/15, requirement parity 79/79, ADR count 16, 194
non-optional tests plus one documented skip and four deselected, 198 full tests plus the
same skip, 35 acceptance tests, all six predecessor focused gates, Ruff, mypy over 118
source files, import, CLI help, and build. It adds no G3FO code or focused CI check.

The stop/reconciliation record was promoted linearly through
[PR #17](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/pull/17) as
protected-main commit `66da91aa56b3949845032f0c428ab331bdc7ec55`. Post-merge hosted
[run `32620214741`](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/runs/32620214741)
passed base and extras on Ubuntu/Windows, recursive, regenerative, goal-synthesis, and
Docker. This verifies the stop record and source reconciliation; it does not validate or
promote the unmerged G3FO implementation.
