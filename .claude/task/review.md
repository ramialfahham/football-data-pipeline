# Review — test/1-guard-path-doc-parity — 2026-08-07

diff_sha256: 051339f8e3bc483d9c62f4e419fe2df3d57cf6d9c09dbabc3f23f980209bb539

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round-1 finding (undeclared threshold: NEW MECHANISM cited only a quoted CPO instruction, with no
  `escalations.log` entry, against the `Path A — LOG IT` ruling at `escalations.log:112`): RESOLVED.
  The log now records the up-front instruction verbatim, cites the round-1 FAIL by name, and is
  APPENDED rather than rewritten. The cited authority at `:112` was re-read and matches the quoted
  text exactly.
- Scope: the diff touches only `.claude/task/contract.md`, `.claude/task/escalations.log` and
  `tests/test_governance_doc_parity.py`, all three declared in `scope_paths`. No file outside scope
  is edited.
- `impact_map` requirement (§2, A6): verified directly against `task_contract_gate.py:94`
  (`_STRUCTURAL_PREFIXES`) and `:95` (the export regex) — `tests/` and `.claude/task/**` match
  neither, so the contract's "none needed" is evidenced rather than asserted.
- Guard-invariant claim: confirmed against the changed-file list. `task_contract_gate.py` and
  `.claude/review_routing.json` do not appear in it; the new test only reads them.
- `decisions_reserved`: neither reserved item (extension to #19; a legitimate guard-set/routing-set
  divergence) is decided in this diff. Both correctly left open.
- The `KNOWN_INCOMPLETE` handling of the `platform-reviewer.md` gap: escalated with two named paths
  and a recommendation, and the CPO's answer is recorded in the log. A genuine §10 fork that was
  escalated, not smuggled.
- Credentials sweep across the full diff: nothing key-, token- or password-shaped.
- Recurring-cost claim ("no new job"): consistent with the diff. Tests only, no CI YAML, no new
  stage, no schedule change.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Re-run and interruption safety: the diff adds one file and touches no script, hook or workflow
  step. Every function in it is a read-only file/regex scan with no writes and no state, so running
  it twice or killing it mid-run leaves nothing behind.
- Whether the test's assertions are actually TRUE, rather than accepting the contract's claim: read
  `task_contract_gate.py:66-79` (4 prefixes + 5 files = 9) and the `paths` block of
  `.claude/review_routing.json`, then hand-verified `shared_guard_paths()` = 3,
  `cto_alone_guard_paths()` = 6 and `cto_routing_rows()` = 12 against the real JSON. All match the
  numbers the test pins.
- Every `COUNT_SITES` anchor, read against the live text in all seven files: each matches exactly
  once with the number the source predicts. This included two anchors straddling a line break, which
  a plain line-based grep initially missed for the same reason the test's own docstring names
  (Trap 1) — confirming `normalise()`'s whitespace collapse is load-bearing.
- The list-completeness axis: traced concrete runs through `_runs()`/`_path_tokens()` by hand — the
  full-nine lists in `TEMPLATE.md` and `cto-reviewer.md`, the six-item list in `platform-reviewer.md`,
  the shared three and the pre-split subset in `platform_reliability.md`, and the config-trio and
  hooks-wiring subsets — and all land on a set `_allowed_runs()` actually contains.
- The one `KNOWN_INCOMPLETE` entry: confirmed the "Your territory is" sentence in
  `platform-reviewer.md:13-14` really does omit `.gitlab-ci.yml` today, so the paired assertion pins
  a real, currently-true defect rather than a fabricated one.
- Coverage-sweep completeness: ran the equivalent `git grep` sweep independently and got the same 16
  files that `COVERED_FILES` (8) plus `SWEEP_EXEMPT` plus the two explicit carve-outs fully account
  for. No thirteenth site is silently uncovered.
- The cross-module import (`from test_governance_hooks import real_routing`): both files live in
  `tests/` with no `__init__.py` or conftest, so pytest's rootdir insertion resolves it whether the
  suite runs as `pytest tests/` or the file is targeted alone. No new import-mode risk beyond what
  `test_governance_hooks.py` already establishes.
- Guard mechanics, dependency hygiene, credentials, build and hosting: none apply. The diff touches
  no hook, workflow, `.gitlab-ci.yml`, `*requirements*.txt`, `package*.json` or site build file.

## escalations
- question: The new test found a TWELFTH restatement site — `.claude/agents/platform-reviewer.md`
  states that reviewer's territory and omits `.gitlab-ci.yml`, which routing does give it. Fix it
  here under a `protected_override` (turning a tests-only diff into a governance change needing an
  `impact_map` and `cto-reviewer` at opus), or record it, file it, and fix it in its own task?
  Builder recommended the second, because routing already summons the reviewer, so the enforcement
  is correct and only the wording is wrong.
  CPO ANSWER: "go ahead as recommended" (conversation, 2026-08-07) — record and file. Filed as
  GitLab #22. Recorded in `.claude/task/escalations.log` under the `2026-08-07
  test/1-guard-path-doc-parity` entry, and pinned in the test as a `KNOWN_INCOMPLETE` entry paired
  with `test_known_incomplete_lists_have_not_been_fixed`, which goes red the moment the prose is
  corrected.
