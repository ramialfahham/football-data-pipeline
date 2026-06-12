# Review — governance/g3-role-reviewers — 2026-06-12

> Final review artifact (step 4 — Lock), after SEVEN blinded review rounds.
> Rounds 2–5 returned blocking findings — self-staging commit forms, bundled
> (`-qam`) and abbreviated (`--inc`) spellings, git global-option skips,
> compound-call restaging, quoted-pathspec and quotePath enumeration defects,
> per-section/preamble escalation pairing, risks-quota anchoring — each fixed,
> re-tested and re-staged, with the reviewers re-spawned cold against the new
> hash. Round 6 surfaced the two reserved §10 questions as a blocking
> escalation; the CPO answered both (recorded below); ruling 1 was implemented
> and round 7 verified implementation fidelity. 80/80 hook tests green.

diff_sha256: e5d37c9daccddec9948b2094fa19ffd8268ef342e095856764a404a750167100

## scope-auditor
VERDICT: PASS
risks_checked:
- Commit-form denial via allowlist inversion (git_discipline.py): shlex
  raw-token walk catches POSIX option bundling (`-qam`), long-option prefix
  abbreviations (`--inc`), git global options before `commit`, and quoted
  pathspecs; unbalanced quoting fails closed; pathspecs caught both as
  positional tokens and after `--`; flag-value tracking prevents a value
  being misread as a pathspec; the sole-command rule prevents index mutation
  after hash verification. Each bypass class is tested individually.
- Per-section ESCALATE/CPO-ANSWER pairing including the `_preamble`
  pseudo-section (git_discipline.py + check_task_artifacts.py mirror): an
  answer in one section cannot mask an unanswered escalation in another or in
  the preamble; verified against
  test_answer_elsewhere_does_not_mask_unanswered_escalation,
  test_preamble_escalation_not_masked, and the CI mirror test.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Ruling-1 fidelity: `.claude/agents/` added to PROTECTED_PREFIXES in
  task_contract_gate.py with the CPO-answer citation; backslash
  normalization precedes the prefix match so the Windows path form cannot
  slip past; test_agents_dir_is_protected covers it; doc sync present in
  working_agreement §2 and agent_guardrails.
- Ruling-2 fidelity: allowlist inversion, `--`/positional pathspec deny,
  shlex on the RAW command with unparseable quoting denied, exact
  `git commit` spelling, sole-command rule, NUL-split staged-path
  enumeration — all present and each exercised by a parametrized test
  (bundled, abbreviated, `-p`, global options, quoted pathspec, unclosed
  quote, non-ASCII path). No deviation from the confirmed package.
- Accidental-spelling sweep: quoted messages containing `&&`/`;`/newlines do
  not trip the sole-command deny (strip-then-split order); heredoc message
  pattern and double `-m` forms pass. Residual false positive: attached-value
  `-m"msg"` (no space) is over-denied in the fail-closed direction with the
  corrective spelling in the deny text — advisory.
- Fail-open (hook) vs fail-closed (CI) polarity verified per rule on both
  sides; untested fail-open branches remain an accepted follow-up.
- Re-run/interruption safety: all gate components read-only and idempotent;
  `--staged-hash` CLI side-effect-free.
- Cost/permissions on ci-validate.yml: no permissions widening, no new
  trigger; `fetch-depth: 0` negligible; base-ref fallback degrades to an
  empty diff on push-to-main, so the new step cannot brick main; additions
  stdlib-only.

## escalations
- question: Should `.claude/agents/**` (the reviewer agent definitions) be a
  PROTECTED path — editable only in a dedicated CPO-approved governance task
  with `protected_override`, like `.claude/hooks/` and the routing file — or
  remain contract-gated (editable inside any task whose contract lists them,
  caught at review time by the scope-auditor)?
  CPO ANSWER: Protect `.claude/agents/**` (blinded escalation, 2026-06-12).
  Implemented in task_contract_gate.py PROTECTED_PREFIXES with
  test_agents_dir_is_protected and doc sync; verified by round-7 reviewers.
- question: Confirm or narrow the commit-form deny package implemented as
  enforcement of the approved review gate: flag allowlist (`-m`/`--message`,
  `-F`/`--file`, `-q`, `-v`, `-S`/`--gpg-sign`, `-s`/`--signoff` only), exact
  `git commit` spelling (git global options denied), commit as the SOLE
  command in its shell call, shlex raw-token walk (unparseable quoting
  denied), NUL-split path enumeration — versus the plan's literal minimum
  (hash + verdict checks only, no form denies)?
  CPO ANSWER: Confirm the full deny package (blinded escalation, 2026-06-12).
  No narrowing; the package stands as the enforcement of the approved review
  gate.
