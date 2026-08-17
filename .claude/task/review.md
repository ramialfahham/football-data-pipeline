# Review — fix/75c-event-consistency-tests — 2026-08-17

diff_sha256: a0236b3c97114d9eeb33034321103fe3f045b2cd36d0200350cc4a78004f9d53

rounds: 2

<!--
HASH REBOUND 2026-08-17 after `gitlab/main` was merged into this branch to clear a conflict.
Was 20af9490d83e9ba7abdab975e9d195e59fb16bd60d6409ce814e3e8ca6e2b287.

The verdicts below still stand and this is NOT a new review round. What changed on the branch is
only the merge itself: `!59` (raw appends and never deletes) landed on main and touched the two
artifacts this branch also touches, so `active_work.md` and `escalations.log` conflicted.
Resolution, per file rather than wholesale:
  active_work.md   -> MAIN's (it is the newer handover), then its header corrected for the
                      merged state. In this branch's scope_paths, so editable.
  escalations.log  -> MAIN's, which is a strict SUPERSET (3287 lines vs 3235): it already
                      contains THIS branch's 2026-08-17 entry, carried over by !58, plus !59's.
                      Verified by grepping for both entries rather than assumed.
  contract.md      -> OURS. It describes THIS task and must not become !59's.
  review.md        -> OURS, hash rebound (this block).
No reviewed CODE changed: the only code on this branch is
`dbt_project/tests/assert_no_event_loss_since_cutoff.sql` and one `dbt_project.yml` var, and
neither appears in the merge. The hash moved because the base moved, not because the diff did.
-->


## scope-auditor
VERDICT: PASS
risks_checked:
- Diff file set vs `scope_paths`: the new singular test, `dbt_project.yml` (one var), `contract.md`, `escalations.log`. No model, no seed, no mart, no ingestion file — this adds an assertion and nothing else.
- The task was reduced, not expanded, against the plan the CPO approved: three designed tests became ONE, because two died against prod data. Both rejections are recorded with their measured reasons rather than dropped silently.
- `decisions_reserved` does not launder anything: the 5 damaged fixtures are explicitly NOT repaired here, and the "may a complete-but-smaller response supersede" question stays with the CPO (#896 rules it the other way today).
- The var is config-as-code and carries an explicit "never raise this to make a build green" warning, so the one way to abuse it is named in the file that holds it.
- Credential sweep of the diff: none.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- ROUND 1 FAILED and the finding was real: the scope CTE grouped `max(raw_ingested_at)` over `base_apif__fixture_events` itself, so a fixture losing ALL its events produced no CTE row and the inner join dropped it — the TOTAL-loss case, undetectable at any cutoff, forever. Measurement could not have caught it, because the known incident was PARTIAL for all 5 fixtures; it was found by reading the join.
- ROUND 2 FIX TRACED END TO END: `in_scope` now reads `fct_fixture`, independent of base. A fixture that loses every event keeps its `fct_fixture` header row, stays in scope, and all of its accumulated fact rows flag. The dependency on base surviving is gone.
- `fct_fixture` verified as the scope source rather than assumed: `fixture_sk` not_null+unique, `fixture_date` not_null, and upstream `loads/fixtures.py:185-197` refuses to write an empty fetch while 206-236 carry forward unrefreshed seasons — so the header row is genuinely always present.
- NEW BLIND SPOT NAMED AND ACCEPTED: a fixture kicking off before the cutoff but damaged after it is permanently out of scope. That is precisely the CPO's "scope it to new data" instruction, and it is disclosed in matching language in three places (test header, contract impact_map, escalations.log).
- Direction: the query is driven FROM the fact, so only fact>base can produce a row; incremental lag (base ahead) structurally cannot fail. Join keys are the models' declared, tested grains; no NULL-comparison hazard.
- Omitting `league_code` from the anti-join is safe — `fixture_sk`/`fixture_id` is globally unique in API-Football and both sides are int64.
- Var placement sits outside the `sync_dbt_vars.py`-generated block; `check_registry_var_sync.py` passes.
- Layer rules: a leaf singular test, no model/grain/materialisation change.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- MERGE CHECK only, not a fresh review of this branch's code. Routing required this reviewer
  because merging `gitlab/main` in stages main's `ingestion/**` and `docs/data_contract.md` paths;
  the question asked was solely whether the merge altered, reverted or damaged anything already
  reviewed and merged under `!59`.
- Confirmed via the worktree's `MERGE_MSG` and `AUTO_MERGE` that the conflicts were confined to
  `.claude/task/*` and `.claude/active_work.md`; no conflict marker or manual resolution touched
  `ingestion/`, `docs/`, `dbt_project/` or `scripts/`.
- Read the staged tree of `bigquery.py`, `loads/squads.py` and `loads/batch_fixtures.py`: all three
  delete helpers (`_delete_fixtures`, `delete_superseded_league_rows`,
  `_delete_superseded_player_rows`) are still ABSENT, present only as the dated
  "REMOVED 2026-08-17" comments. The merge did not resurrect them.
- `bigquery.py` still reads `"WRITE_APPEND" if append else "WRITE_TRUNCATE"` with WRITE_TRUNCATE
  reserved to single-current-state tables — matching `!59`, not reverted to unconditional truncate.
- `docs/data_contract.md` still carries the append-only write-mode table and the sentence "Since
  2026-08-17 nothing in ingestion deletes from raw", verbatim as reviewed.
- Cross-checked this branch's own `scope_paths`: nothing under `ingestion/` or `docs/`, corroborating
  that its real diff against main is the dbt test plus one var.

### analytics-engineer-reviewer — merge check (same reviewer, second pass)
- MERGE CHECK only, run when `gitlab/main` was merged in. Routing required this reviewer because
  the merge stages main's `dbt_project/**`; the question was whether it reverted any model or doc
  already reviewed under `!59`, and whether this branch's own dbt contribution survived. PASS.
- Read all four fixture-details staging model headers off the staged tree: every one says
  "APPEND-ONLY … a retry appends a second version rather than replacing the first", NOT the
  pre-`!59` "merge-on-write / deletes-on-retry" wording. No reversion.
- Read all five affected `stg_apif__generic.yml` descriptions: all say append-only, none asserts
  merge-on-write as current behaviour.
- `layering.md`'s only surviving "merge-on-write" is the past-tense item 8b reference, which is the
  documented exception; `data_contract.md` describes RAW_APIF_FIXTURE_DETAILS as append-only, one
  row per fetch.
- Read `assert_no_event_loss_since_cutoff.sql` in full — this branch's own contribution is intact
  byte-for-byte (kickoff-date scoping via `fct_fixture`, direction-only loss check, the stated
  inert-before-cutoff caveat). `event_loss_detector_from: '2026-08-19'` present exactly once.
- Grepped `dbt_project/`, `ingestion/`, `docs/` for conflict markers — none; the merge is fully
  resolved, not left mid-conflict.
- ⚠ STATED LIMIT, the reviewer's own: it has no Bash tool, so it could not run
  `git diff --cached gitlab/main`. It verified by reading the staged files on disk and
  cross-checking the merge's hunks in `review_input.patch` — a different route to the same
  conclusion, recorded rather than glossed.

## platform-reviewer
VERDICT: PASS
risks_checked:
- MERGE CHECK only. Routing required this reviewer because the merge stages main's `tests/**` and
  `scripts/**`; the question was whether it weakened or reverted any test already reviewed in `!59`.
- Confirmed `tests/test_raw_merge_on_write.py` in the staged tree is `!59`'s REWRITTEN version —
  it asserts `client.dml() == []` via `test_a_clean_run_appends_and_issues_no_dml` and
  `test_no_loader_module_carries_a_delete_helper`, NOT the pre-`!59` version that demanded the
  deletes happen. A wrong resolution here would have silently restored a test requiring the
  deleted behaviour; it did not.
- Swept every file under `tests/` for delete/merge residue and checked the seven hits individually:
  all read consistently with the append-only reversal; none demands a delete.
- `dbt_project.yml` carries exactly the one claimed var with its "never raise to make a build green"
  warning intact; the detector SQL matches what was already PASSed.
- Verified the `escalations.log` SUPERSET claim by locating BOTH entries rather than assuming it:
  this branch's at line 3129 and `!59`'s at line 3240.
- Grepped repo-wide for unresolved conflict markers — none.
- ⚠ STATED LIMIT, the reviewer's own: Read/Grep/Glob only, no shell, so it could not execute
  `git diff --cached` or recompute `--staged-hash` numerically; it substituted direct inspection of
  the staged working tree.
  ⭐ THAT GAP IS CLOSED BY EVIDENCE, not left open: the builder ran
  `python .claude/hooks/git_discipline.py --staged-hash` against the staged merge and it returned
  `a0236b3c97114d9eeb33034321103fe3f045b2cd36d0200350cc4a78004f9d53`, identical to the value
  recorded above, and `git diff --cached gitlab/main -- ingestion dbt_project scripts tests docs`
  returned only `assert_no_event_loss_since_cutoff.sql` and the `dbt_project.yml` var. Recorded
  here because "a reviewer could not run the check" is not the same as "the check passed".

## escalations
- question: May a COMPLETE provider response carrying strictly less data than what is stored supersede it?
  CPO ANSWER: NOT TAKEN — still open, and deliberately so. This test makes the loss VISIBLE; it does not decide who wins. #896 rules the ambiguous case the other way today (2026-08-03), so changing it reverses part of that ruling. Recorded in `escalations.log` and `decisions_reserved`.
