# Review — feat/description-hygiene-gate — 2026-08-20

> MR5 of six: the gate that makes the description standard stick, plus the last of the content
> sweep it needed to be green on day one. Four reviewers, since two PROTECTED paths are edited.
> Round 1: cto-reviewer PASS, analytics-engineer-reviewer PASS, platform-reviewer FAIL (3),
> scope-auditor FAIL (3). All six findings addressed; four were code defects and are fixed, two
> were about the contract describing the work inaccurately and the contract is corrected.

diff_sha256: ddd995ff4e543aaa06bf4c573920a84fc8985b1e69e235945cef67dad57bab72

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is inside `scope_paths` as amended. No MR6 work (`persist_docs`,
  `dbt docs generate`) present. The "partition key" instances in five docs and in
  `.claude/hooks/dbt_layer_gate.py` were left untouched for GitLab #79, as reserved.
- The `protected_override` cites a CPO approval recorded in `escalations.log` BEFORE the branch
  touched either protected file, and each protected edit is exactly the one line it authorises.
- ROUND 1 FAIL, and the finding was right about the thing that mattered. `decisions_reserved` said
  fixing a gate survivor was "in scope only as far as making the gate green"; the ten-file sweep
  went further, applying §2 in full. The reviewer was correct that the contract's own limit did
  not describe the work.
  RESOLVED BY CORRECTING THE CONTRACT, not by narrowing the work, and the reasoning is recorded in
  the bullet itself: the gate's rules are deliberately narrower than §2 — they match only what a
  machine can decide without taste. `mart_team_season composes …` and `ratios live in
  mart_team_season_record` are §2-banned downstream-consumer claims that no regex here catches.
  Deleting only the flagged token would have left those standing inside a description the sweep
  had just edited, and left the ten files inconsistent with the five MR3/MR4 rewrote.
  ONE flagged change was NOT §2-driven and is restored: "Complement to int_team_momentum__metrics"
  is a sibling cross-reference, not a downstream claim, and dropping it cost something for nothing.
  analytics-engineer-reviewer independently checked all ten files against their SQL and found no
  false claim, so the rewrites themselves are sound.

## cto-reviewer
VERDICT: PASS
risks_checked:
- The `protected_override` citation is real and specific, not self-certifying: the escalations
  entry exists, carries the CPO's verbatim "do both", and narrows itself to exactly two edits.
- Both protected edits match that scope — one script line in `validate:governance`, one tuple
  entry in `FAST_GATES`, each with the per-entry comment both files already use. No second hunk.
- The hook's fail-OPEN harness and CI's fail-CLOSED behaviour are both unchanged; the new gate
  rides the existing mechanisms rather than altering them.
- No new dependency: `PyYAML>=6.0` is already in `requirements.txt` and ten scripts import it.
- No new CI job, schedule or cadence, so no recurring cost.
- No other protected path appears in the diff.

## platform-reviewer
VERDICT: PASS
risks_checked:
- ROUND 1 FAIL 1, fixed: the decision-language rule matched bare `\bruled\b|\bruling\b`. In a
  FOOTBALL repo that fires on "goal ruled out for offside" or "match ruled void" — legitimate
  description prose — and it broke the gate's own stated design rule of matching annotation forms
  rather than ordinary verbs. Both alternations are removed; `\bCPO\b` already catches every real
  instance, because a ruling worth logging is attributed. Two new tests pin BOTH directions:
  football prose passes, "The CPO ruled …" still fails.
- ROUND 1 FAIL 2, fixed: `read_text` sat inside a `try` that caught only `yaml.YAMLError`, so a
  non-UTF-8 `.yml` raised an uncaught `UnicodeDecodeError` and escaped as a raw traceback — still
  a non-zero exit, but naming no file. Now catches `(yaml.YAMLError, UnicodeDecodeError, OSError)`,
  with a test feeding real cp1252 bytes and asserting the file is named.
- ROUND 1 FAIL 3, fixed: `validate-local/SKILL.md` still said "Five of these also run at turn end"
  after a sixth was added, and the pinning test asserts set equality over the marked block only,
  not prose counts. Corrected to six, with a note in the file saying the count is unpinned so the
  next person to add a gate knows to change it.
- Not vacuous: every banned class drives `main()` against a synthetic offender and asserts exit 1,
  each paired with a same-fixture-without-offender green assertion. The floor test restores the
  REAL `MIN_DESCRIPTIONS` rather than the relaxed test value.
- CI fails closed (plain `script:` step, no `|| true`); the hook fails open, unchanged.
- Performance: walks a small set of `.yml` files, skips `target/` and `dbt_packages/` by exact
  path segment, and runs before `dbt deps` in CI so those directories do not yet exist.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- All ten rewritten files checked against their models' SQL. No rewritten description makes a claim
  the SQL contradicts, and no grain, sign-convention or coverage claim was altered to something
  false — the specific hunt that caught a real defect in each of the two previous MRs.
- Verified individually: the deserved-vs-actual least-squares method, sign convention and coverage
  gate; the byte-identity claims in both directions between the cumulative and whole-season models;
  match-history-not-roster membership; the season-cap / recency / uncapped-tournament window rules;
  in-position per-90s; `appearances` as `countif(minutes > 0)`; and the qualifier-window and
  finishing-efficiency columns on the matchday mart.
- `stg_apif__lineups`: the dropped "NO consumer today" claim was verified still true by grep, and
  dropping rather than restating it is what §2 requires.
- No `{{ doc() }}` reference broken; no description contradicts a sibling in its own file.

## escalations
(none)
