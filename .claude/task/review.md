# Review — chore/33-item15-drop-injuries — 2026-08-13

diff_sha256: 2f31a1c3938b751bacf70496c171d0b4ca6ab351f4642ae8e2421e2ac0480dde

rounds: 3

<!--
Round 1: all three PASS on the removal itself. platform-reviewer additionally FLAGGED, outside
         its own territory and therefore not as a FAIL, that `docs/data_contract.md:36` still
         said "Eleven tables" after a row was removed. scope-auditor had passed that same line
         as "still correct".
Round 2: the count was REMOVED rather than corrected (CLAUDE.md gives that instruction for this
         exact class). scope-auditor PASS, and accepted the correction to its own round-1
         reading. data-engineer-reviewer FAIL: the SAME stale count survived at line 3 of the
         same file, under the OPPOSITE counting convention, so the document now contradicted
         itself two lines from the top.
Round 3: both instances closed, whole file swept, and the documented set recounted against what
         the loaders actually write. All three PASS.

Worth keeping: the round-2 FAIL was "you fixed the instance, not the class" applied INSIDE a
single file. The first fix was itself the defect it was fixing.
-->

## scope-auditor
VERDICT: PASS
risks_checked:
- CPO authority verified in `.claude/task/escalations.log` independently of `contract.md` — the
  question put ("drop `/injuries` as a second task?") and the answer ("yes") are both in the
  committed log, as is the 2026-08-13 premise check.
- The `readers: NONE` claim checked directly rather than accepted: `sources.yml` has no injuries
  entry, and the only `injur` hits under `dbt_project/models/**` are `has_coverage_injuries`,
  parsed from the `/leagues` coverage flag and untouched by this diff.
- Every `diff --git` header maps onto an entry in `scope_paths`; no file outside the allowlist.
- Dangling-reference sweep across `ingestion/**` and `scripts/**`: no surviving import of
  `load_injuries` and no reference to `RAW_APIF_INJURIES` outside the deliberately-updated drop
  script; the runner's docstring phase list and import list dropped the step consistently.
- Test deletion judged against the "guard loosened" threshold: `TestLoadInjuries` went with its
  subject, `TestLoadCoaches` is preserved verbatim, and the surviving envelope-stability guard in
  `test_incomplete_fetch_no_supersede.py` lost only a docstring mention, not an assertion.
- The physical table drop is confirmed NOT in this diff, matching `decisions_reserved`.
- Classified the round-2 count removal against §10: no table, write mode, partition, cluster or
  merge key changes, so a builder-level doc-hygiene call, consistent with the precedent CLAUDE.md
  already sets — not a fresh unilateral pattern.
- ⚠ Its round-1 reading of the "Eleven tables" line as "still correct" was wrong and it accepted
  the correction at round 2. Recorded because a reviewer PASS is not evidence a claim is true.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- ⚠ THE CRITICAL SAFETY CHECK: `has_coverage_injuries` is parsed at `stg_apif__leagues.sql:88`
  from `$.coverage.injuries` (the `/leagues` payload), used in `base_apif__leagues.sql:23,62`,
  `dim_competition_season.sql:25` and declared in `core.yml:143-144`. None of those files appears
  in the patch, so the column is untouched and `dim_competition_season` cannot break.
- Sole-writer claim verified by grepping all of `ingestion/api_football` — `load_injuries` was the
  only writer of `RAW_APIF_INJURIES` and was called from exactly one site.
- `run_cheap_phases` read in full after the change: import, phase log and call cleanly removed, no
  orphaned variable, no unused import, try/except and the following coaches phase unaffected, and
  the module docstring's phase list matches the code exactly.
- Hidden dependents ruled out by reading `completeness.py` (`FANOUT_ENTITIES`, `PER_TEAM_ENTITIES`,
  `PER_TEAM_GATED`, the snapshot table), `orchestrator.py`, `quota.py`, `settings.py`,
  `bigquery.py` and `.gitlab-ci.yml` — no completeness gate, quota accounting or scheduler config
  depends on the removed phase.
- The `http_client.py` "four -> three" comment edit verified by ENUMERATING the loaders that copy
  the envelope wholesale: `standings.py` and `fixtures.py` via `_merge_merged_paged`, plus
  `teams.py`'s manual comprehension. Three, and `coaches.py` was never in that set because it
  builds its payload from explicit named keys.
- ⚠ FAILED round 2: the stale count at `docs/data_contract.md:3` survived the round-2 fix under
  the opposite convention to the one the new caveat described, leaving the document
  self-contradicting. Re-verified at round 3 that both instances are closed, the whole file is
  free of number-words adjacent to "table", and the documented set matches reality — an
  independent recount of `raw_table(...)` call sites gives 11 entities, exactly the 10 rows plus
  `RAW_APIF_LEAGUES`.

## platform-reviewer
VERDICT: PASS
risks_checked:
- `tests/test_coaches.py` compared BYTE-FOR-BYTE against the `TestLoadCoaches` block in the
  deleted file at `main` — all 9 methods and both helpers identical; no assertion, mock target or
  fixture value changed, and nothing in the survivors referenced the deleted class or shared state
  with it. The file was reconstructed rather than edited, so this was the check that mattered.
- Test-count arithmetic confirmed by enumerating `TestLoadInjuries`' 9 methods: 798 − 9 = 789,
  matching the run exactly. Nothing else was lost.
- `scripts/drop_injuries_raw_tables.py` matching logic confirmed byte-identical (docstring only).
  Verified `"RAW_APIF_INJURIES"` satisfies both `startswith("RAW_APIF_")` and
  `endswith("_INJURIES")`, so the docstring's claim that one pattern covers both the retired
  per-competition naming and the unified table is true. Dry-run path never calls `delete_table`;
  a second run finds nothing and exits 0; per-table failures are collected and the script exits 1
  on any error, so it fails closed rather than reporting false success.
- Confirmed no dependency file, CI config, hook or `site_v2` path appears anywhere in the diff,
  and no credential-shaped content beyond a pre-existing mock header value.
- Flagged (outside its territory, hence not a FAIL) the stale "Eleven tables" line that
  data-engineer-reviewer then FAILed on — the flag was correct and is what started round 2.

## escalations
(none — the CPO ruling "yes" (2026-08-12) and the 2026-08-13 premise check are both recorded in
`.claude/task/escalations.log` and were verified there by `scope-auditor`. No question was put to
the CPO during the review cycle.)
