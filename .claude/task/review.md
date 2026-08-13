# Review — fix/65-ci-worktree-prune — 2026-08-13

diff_sha256: b1b3a6465a8b8ae1ef070c1ccfc41ef76b7dbb9b7191980278c71232f0c46fcb

rounds: 1

Three routed reviewers, blinded (patch + `contract.md` + `escalations.log`; no builder narrative).
Routing per `.claude/review_routing.json`: scope-auditor (always), plus cto-reviewer and
platform-reviewer for `.gitlab-ci.yml`, which is a PROTECTED file. All three PASS at round 1.

⚠ Two things the reviewers established that the builder had NOT: that `.github/workflows/` runs on
`ubuntu-latest` (ephemeral), so leaving the twin line unedited is diagnostically correct and not
merely policy-correct; and that `test:python` runs on every non-scheduled pipeline, so the new guard
fails closed on every future MR rather than only locally. Both are recorded below in the reviewer's
own territory rather than restated as builder claims.

## scope-auditor
VERDICT: PASS
risks_checked:
- `protected_override` authority is real and correctly ORDERED: `.gitlab-ci.yml` confirmed present
  in `PROTECTED_FILES` (`task_contract_gate.py:77`), and the 2026-08-13 `escalations.log` entry
  recording the CPO's "yes" plus the premise interrogation ("Does it conflict with the other
  worktree?") is appended BEFORE `contract.md` cites it.
- Narrowness of the override checked against the file, not the claim: `git worktree` appears only in
  `data:build:mr`; no `rules:`/`changes:` anchor, no other job, no resource group and nothing under
  `.github/workflows/` is touched.
- `scope_paths` matches the diffed file set EXACTLY — four files, none undeclared.
- The `.claude/active_work.md` exclusion (`decisions_taken` 6) judged as a documented decision
  rather than a handover-discipline violation: it gives a concrete reason (main's copy is stale,
  the live copy is on `!33`, editing it would manufacture a conflict) and states how to reverse it.
- No new mechanism and no recurring cost: `git worktree prune` is a stateless local git metadata
  operation, adding no job, schedule, service or BigQuery object; the added test pins a CLASS rather
  than a line number.

## cto-reviewer
VERDICT: PASS
risks_checked:
- The gate's own requirements are satisfied for a protected path: `_is_structural`
  (`task_contract_gate.py:193-208`) makes `impact_map` mandatory alongside a non-placeholder
  `protected_override`, and the contract carries both.
- The escalation entry was compared against the two prior protected-path entries (#61, #63) and
  matches their shape — ask, premise check, ruling, explicit narrowing — rather than being an
  outlier written to fit.
- NO GUARD INVARIANT IS WEAKENED. `prune` removes only registrations whose directory is gone, so a
  genuine live collision still fails loudly; `add -f`, which would have silently overridden one, was
  explicitly rejected. No test, lint or DQ step is skipped, reordered or narrowed.
- The instrument was challenged: does this paper over a runner misconfiguration that should be fixed
  at the runner instead? Judged reasonable — reconfiguring a shared self-hosted runner's workspace
  strategy is a materially larger and riskier change, and the contract defers it explicitly rather
  than smuggling it in.
- ⭐ THE GUARD FAILS CLOSED GOING FORWARD, verified rather than assumed: `test:python`
  (`.gitlab-ci.yml:430-437`) runs `pytest tests/` on every non-scheduled pipeline, so dropping the
  prune line reddens every future MR and main pipeline.
- Recurring cost: none. No trigger, schedule, BigQuery scan or network call added;
  `.data_paths_mr`/`.data_paths_prod` untouched, so WHICH changes cause a build is unchanged.
- The still-red pipeline was tested against the "verify by running" standard and judged DISCLOSURE
  rather than evasion: #66 is named separately in both `done_when` and the escalation, with the
  reason, instead of a false green being claimed.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Placement traced through the real script order (`.gitlab-ci.yml:517-577`): prune and add are
  adjacent, nothing runs between them, and `resource_group: ci-data-build-write-ci` plus the absence
  of any other worktree-using job means no concurrent job can re-register the stale entry in the
  gap.
- The diagnosis was tested against the config rather than taken on trust: `GIT_STRATEGY` and
  `GIT_CLEAN_FLAGS` are unset (so nothing in-repo overrides the runner default that would falsify
  "the project dir persists"), `GIT_DEPTH` affects fetch depth only, and `cache:` covers
  `.cache/pip`/`.npm` and never `/tmp` or `.git/worktrees`. ⚠ Nothing in the file CONTRADICTS the
  diagnosis and nothing in it CONFIRMS the diagnosis — it rests on the two cited job logs, which is
  outside what the diff can show.
- ⚠ A STATE THE FIX DOES NOT CLEAR, stated rather than glossed: `/tmp/main-src` existing with stale
  CONTENT while still registered. `prune` only clears registrations whose directory is gone, so that
  case would fail with "already exists". It is consistent with `decisions_taken` 2 (fail loudly on a
  genuine collision) and is NOT a regression — the behaviour is identical before and after.
- The new test is real, not decoration: `_script_lines_by_job` was traced against the actual YAML
  merge structure (`<<: [*python, *gcp_job]` inside `.data_build_base`, then `<<: *data_build_base`)
  — PyYAML resolves merge keys before the alias is reused, so the job's own `script:` is captured
  intact and in execution order. Removing the prune line was traced through the assertion: `add_at`
  found, `prune_at` None, job flagged, test fails.
- No false positives: every job without `git worktree add` is skipped by the `continue` and never
  reaches the assertion.
- ⚠ LATENT LIMITATION OF THE GUARD, disclosed rather than left to be discovered: `extends:`,
  `!reference` and `include:` are grepped and none is used in this file today, so the test sees
  everything. A template whose `script:` lived in an `include:`-ed file WOULD be invisible to it.
  Not triggered by anything in this repo now; recorded so the next person adding an `include:` knows.
- ⭐ Leaving `.github/workflows/ci-data-build.yml:191` unedited is DIAGNOSTICALLY correct, not just
  policy-correct: that workflow declares `runs-on: ubuntu-latest`, i.e. ephemeral GitHub-hosted
  runners, where a persisted project directory cannot occur. The dormant-workflow README already
  carries a pre-reactivation audit section, so a future re-arm does not depend on silence here.
- Re-run and interruption safety: prune is idempotent, and a job dying after a successful `add`
  leaves a registration that self-heals on the next run through the same prune.
- Nothing else engaged: no secrets, no permission widening, no dependency/lockfile/site-build/hosting
  file touched, and `git worktree` logic exists in neither `git_discipline.py` nor
  `check_task_artifacts.py`.

## Verification (LOCAL — CI evidence is the pipeline on this MR)

- ⭐ The new test was SEEN RED before it was trusted green. Against the unfixed `.gitlab-ci.yml` it
  failed naming the real offender: `data:build:mr: git worktree add at script index 76, prune
  absent`. After the fix, green.
- ⭐ BOTH of its failure branches were proved live, because one of them ("prune present but AFTER the
  add") could otherwise have been dead code. Driven over four synthetic configs: prune absent →
  flagged; prune after the add → flagged; prune before the add → clean; prune in a DIFFERENT job →
  flagged. The last case is what stops a prune elsewhere in the file from satisfying the check.
- ⭐ The MECHANISM was run against real git, not read off the manual (`scratchpad/wt_repro.py`):
  unfixed `add` exits 128 reproducing CI's error text, `prune` then `add` exits 0, and a repeat prune
  with nothing stale is a no-op that still leaves `add` working.
- `git worktree prune --dry-run -v` on this machine removes NONE of the three registered worktrees,
  which is the evidence behind the CPO's "does it conflict with the other worktree?" question.
- `pytest tests/` — 799 passed, 1 skipped, 15 subtests passed. `dbt parse` clean.
- Offline gates all PASS: `check_layer_contract`, `check_registry_var_sync`,
  `check_competition_type_seed`, `check_copy_gate`, `check_ui_i18n_metrics`, and all five JSON
  manifests parse.
- `sqlfluff lint` NOT run and NOT claimed: this diff contains zero `.sql` files, so it would have
  been uninformative.

⚠ **This is LOCAL evidence and is never CI evidence.** The pipeline on this MR is the CI evidence.
It is EXPECTED to go past the worktree step and then FAIL further down on **#66** — prod data has
not been rebuilt since 08-09, so `assert_event_team_in_fixture_participants` still returns its 10
rows through `--defer --favor-state`. That is a different defect and not evidence this fix failed.
Read the log, not the colour.
