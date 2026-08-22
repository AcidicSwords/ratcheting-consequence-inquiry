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
nonblocking; the hosted `docker` job remains the required container evidence.
The first hosted G2A PR workflow is pending and will be recorded after it passes.
