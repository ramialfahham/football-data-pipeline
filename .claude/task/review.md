# Review — fix/75-mr2-never-record-a-gap — 2026-08-17

diff_sha256: 39563ba4338c968174621e7fb31c7f9e61e396468f54c9da974fa096a2b4e580

rounds: 1

<!--
⚠ HASH BOUND THREE TIMES ON THIS BRANCH, and the sequence is the point:
  3d0296ad… the reviewed code diff, before main was merged in
  e51e5db9… the STAGED merge — what the local commit gate checks, and dead the instant the merge
            commit exists
  39563ba4… THIS value, computed after the merge was committed. It is what CI recomputes from
            `origin/main...HEAD`, and it is the only one that binds.
Confirmed rather than assumed: `check_task_artifacts.py` run bare against the committed merge
reported FAIL with "recomputed 39563ba4…", i.e. it named this number before it was written here.

A MERGE COMMIT MOVES ITS OWN MERGE-BASE, so a hash taken from the staged index binds nothing once
the merge is committed, and CI recomputing `origin/main...HEAD` gets a different number. That trap
reddened `!57`'s validate:governance earlier today. The rule is now in the handover: on a merge,
rebind AFTER committing, in a review.md-only follow-up (artifact-exempt).

WHY MAIN WAS MERGED IN: #69 (dim_country + dim_region) landed on main from another clone while
this branch was in review. Only task artifacts conflicted — contract.md, review.md,
review_input.patch — all resolved OURS, because each MR carries its own. No code conflict exists:
this branch touches only ingestion/ and tests/, #69 only dbt_project/.
-->


## scope-auditor
VERDICT: PASS
risks_checked:
- Traced the authority chain: the contract's "go ahead as recommended" resolves to the logged
  findings at `escalations.log:3257-3268`, and the four fixes in this diff are exactly the four
  named there. The two `decisions_reserved` deferrals (volume-delta threshold,
  `event_loss_detector_from`) are echoed at lines 3268/3288-3289 as MR3-owned, so nothing deferred
  is silently decided here.
- Every file in the diff is inside `scope_paths`. `tests/test_incomplete_fetch_no_supersede.py` is
  listed in scope but absent from the diff — checked the file directly rather than assuming: it is
  a pre-existing #896 test with no reason to change, not a smuggled omission.
- The mid-task amendment (`tests/test_player_squads_catchup.py`) is harness-only: the diff changes
  the mock's return value and adds a comment; no assertion moved.
- Independently grep-verified the 11 `load_json_to_bq` call sites rather than trusting the
  contract's count; 9 already explicit, and the diff adds `append=False` at exactly the two the
  contract names.
- The RECURRING COST declaration (a small increase in API calls, because wrongly-captured keys get
  re-fetched once) is bounded and is the direct consequence of the named fix, not an independent
  cost decision — declared, not smuggled.
- Credential sweep across the full patch: no hits.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- THE central risk, that the fix widens what "complete" means rather than withholding the write:
  read `http_client.py:83-107` and confirmed `result_is_complete` is untouched. Both directions are
  pinned — rate-limited body error withheld, empty-and-error-free still written — so the CPO ruling
  of 2026-08-03 survives intact.
- Read all three loaders in full and confirmed the `if not complete: continue` sits inside the
  per-entity loop and guards only that entity: a healthy sibling in the same batch is still
  written, which the tests assert on ids 11 and 8.
- Read `transfers.py:29-110`: the new `if not team_ids: return` is the first statement, before
  `complete = True` is initialised, so the empty-team path can no longer reach the write. It sits
  alongside, and does not tangle with, the pre-existing #896 discard-on-partial block.
- Verified every one of the 11 `load_json_to_bq` call sites individually. All pass `append`
  explicitly. `append` was ALREADY keyword-only (after `*`), so there is no positional-call risk
  anywhere and no caller can TypeError.
- Grepped the whole repo for readers of the three widened helpers: every call site unpacks
  `(rows, complete)`; none still assumes a bare list.
- Confirmed the response-parsing line in each helper is byte-identical before and after — only the
  already-tested `result_is_complete` primitive is newly wired in, matching the pattern the two
  sibling helpers have used since #896. No new parsing logic, so no new sample fixture is required.
- Checked the contract's deploy-order claim against the actual CI file: `.data_paths_prod`
  (`.gitlab-ci.yml:274-282`) excludes `ingestion/**`, so merging does not trigger a prod rebuild.
- No change to history window, fanout caps, cadence or env-var defaults anywhere in the diff.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Traced all 11 tests against the pre-fix hunks to answer the vacuity question directly. The six
  that fail on the tuple unpack are NOT vacuous: they call the REAL helpers with only
  `fetch_merged_paged` mocked, so a fix that restored the shape with the boolean wrong (hardcoded
  `True`) would still be caught by the explicit `assert complete is False` / `is True`.
- ⭐ CORRECTED THE BUILDER'S OWN EVIDENCE. `acceptance_evidence.md` claimed only THREE tests fail on
  an assertion pre-fix. Platform traced the loader hunks and showed the two player-entity tests do
  too, because they patch the helper inside the loader's namespace, so the pre-fix loader stores
  the tuple whole and records the entry. Re-run against `gitlab/main` to confirm rather than accept:
  `AssertionError: player 7's rate-limited empty payload was recorded ([7, 8])`. It is FIVE, and
  the document now says so and says it was corrected.
- Verified the `a[2]` positional payload capture against the real call sites in all three loaders —
  payload is index 2 in each — and that the `assert written` guard is present in both tests, so an
  empty capture cannot pass silently. (An earlier draft captured kwargs only and would have
  asserted over an empty list.)
- Confirmed `tests/test_player_squads_catchup.py`'s one-line change touches only the fake's return
  shape; no assertion in that file moved.
- Judged the `inspect`-based signature test the right level: Python enforces the required
  keyword-only constraint at call time regardless of the caller, so this is equivalent to and more
  robust than a `pytest.raises(TypeError)` call test, and it targets the named regression (a
  default reappearing).
- Confirmed the diff touches none of `scripts/`, `.claude/hooks/`, `.github/workflows/`,
  `.gitlab-ci.yml`, `*requirements*.txt` or `site_v2/**`, so the remaining platform hunt items have
  no surface here.
- Flagged one cosmetic defect, fixed before this lock: the test module docstring referenced
  `test_empty_but_clean_response_is_still_written`; the function is `..._is_still_complete`.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- MERGE CHECK only. Routing required this reviewer because merging `gitlab/main` in stages main's
  `dbt_project/**`; this branch declares no dbt path and contributes no dbt change. The question
  was solely whether the merge reverted or damaged #69's work, which landed on main from another
  clone while this branch was in review.
- Compared the on-disk content of every file #69 touched against that content as carried in the
  merge, byte for byte: `dim_country.sql` (34 lines), `dim_region.sql` (33), `seeds/countries.csv`
  (225 lines, all 224 rows afghanistan…zimbabwe), the `dim_country`/`dim_region` blocks in
  `core.yml` including their `not_null, unique` tests, both new exception bullets in
  `layering.md`, and the `countries` seed doc block in `seeds/schema.yml`. All identical — nothing
  silently reverted.
- Swept `dbt_project/` for conflict markers and merge-backup files (`.orig`, `.BACKUP`, `.LOCAL`,
  `.REMOTE`, `.BASE`): zero hits.
- Confirmed `contract.md`'s `scope_paths` declares no `dbt_project/` path, consistent with the
  claim that the merge should take main's side wholesale.
- ⚠ STATED LIMIT, the reviewer's own: Read/Grep/Glob only, no shell, so it could not run
  `git diff --cached gitlab/main -- dbt_project` and substituted direct content comparison against
  the merge's own hunks. Same conclusion by a different route.

## escalations
(none)
