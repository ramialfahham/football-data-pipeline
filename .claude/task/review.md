# Review — fix/75-raw-append-only — 2026-08-17

diff_sha256: b385360a3e53df9d7c0000589240e81d0f93d6a5ca2c98ed078e79268a46cbbf

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1: diffed the file list against `scope_paths` (no out-of-scope file); verified both CPO
  rulings quoted in `decisions_taken` against the 2026-08-17 entries in `escalations.log` — the
  verbatim quotes, the cost-stated-before-ruling process and the "supersedes part A" claim all
  match, no fabricated authority; checked the RECURRING COST declaration is present with the
  figure the CPO approved; confirmed the NEW MECHANISM claim ("this DELETES mechanisms; it adds
  none") against the diff; confirmed `decisions_reserved` items are flagged-but-untouched, in
  particular that the protected `.claude/agents/data-engineer-reviewer.md` does not appear in the
  diff; scanned for credential-shaped strings and widened permissions, none found.
- Round 2 (delta, after two contract amendments added eight files): diffed all eight hunk-by-hunk —
  every hunk touches only a docstring, comment, or an assertion-message string literal; no changed
  control flow, no changed assertion condition, no test added or removed. Cross-checked the claimed
  authority against `escalations.log`: the ruling reads "raw stops deleting old rows EVERYWHERE,
  not only for fixture details", so citing it for files beyond the reviewer's three named examples
  is an honest reading, not a stretch — the ruling's own scope is global. Re-diffed all 24 blocks
  in the patch against `scope_paths`; all matched, none outside.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAILED: three module docstrings (`standings.py:6-8`, `teams.py:6-8`, `transfers.py:8-10`)
  still read "MERGE-ON-WRITE since #33 item 8b … deletes this league's older rows" while the
  function body edited by the same diff said the delete was removed. Named as the "correction that
  did not replace everywhere" failure class, in the same three files that used to house the deleted
  helpers. Resolved in round 2 and content-verified against the current loader code, which passes
  `append=True` on every raw write and issues no DML.
- Round 2: re-ran the repo-wide grep for `merge-on-write|merge on write|delete-on-retry` across
  `*.py`/`*.md` INDEPENDENTLY rather than trusting the builder's sweep — every remaining hit is
  past-tense/historical or in the excluded/protected files named in `done_when`; none asserts
  current behaviour.
- `grep -rn "delete from|DELETE FROM" ingestion/` run directly against the working tree: zero hits,
  matching the `done_when` claim.
- Checked the rewritten `test_raw_merge_on_write.py` asserts absence of DML via a keyword class
  match (`delete|update|merge|truncate`) rather than a name pin, so a delete reintroduced under any
  name is caught; and that `test_no_loader_module_carries_a_delete_helper` walks the real module
  namespace rather than grepping source text.
- Verified the NEW claims introduced by the reworded comments rather than assuming them: the
  `transfers.py` empty-`team_ids` description checked against `transfers.py:29-96` (loop never
  runs, `complete` stays True — accurate, and correctly deferred to MR2 rather than silently left
  as a live gap); `completeness.py:283,331` checked against the surrounding snapshot-read logic,
  still accurate under append-only.
- Base models consuming the now-multi-row raw tables all dedup `partition by <entity key> order by
  raw_ingested_at desc`; the "no SQL changes needed" claim holds and no downstream reader assumes
  one row per key.
- Confirmed the #896 completeness guard is unweakened in all five loaders.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAILED on the same stale-docstring class, found independently, plus two findings the
  other reviewer did not raise: the `ingested_at` docstrings in `bigquery.py:162-166` and
  `:227-229` still justified the parameter by a delete boundary that no longer exists anywhere
  (`grep -rn "ingested_at=" ingestion/` returns zero call sites), and — the one that matters most —
  `contract.md`'s own `done_when` verification grep was scoped to `docs/` and `dbt_project/` and
  never `ingestion/`, so it passed green while four in-scope files said the opposite of the change.
  All three resolved in round 2; the corrected grep was re-run by the reviewer directly and its
  result set matched.
- Test-coverage hunt (the reason for the routing): every "no delete" assertion goes through a client
  double recording raw SQL rather than monkeypatching a removed helper by name, so a reintroduction
  under a different name or as inline SQL is still caught. Traced each of the three removed call
  sites to confirm any reintroduction must travel through `client.query(...)`.
- Vacuous-test hunt: none found. `test_the_fixture_write_is_an_append` exercises the real
  `_insert_fixture_rows` and asserts its actual hardcoded `write_disposition`;
  `test_every_raw_write_is_an_append` asserts the flag that genuinely gates WRITE_APPEND vs
  WRITE_TRUNCATE in `bigquery.py:195`.
- Guarantee-retention hunt: the three removed parametrized cases pinned properties of a mechanism
  that no longer exists (delete scoping, delete boundary, delete failure handling) and are
  legitimately retired; `test_a_failed_delete_still_extends_team_ids` was RE-POINTED, not dropped,
  onto the path that still exists (an incomplete/discarded snapshot), and the live guarantee was
  verified against `teams.py:91-96`.
- Round 2 delta remit: diffed `tests/test_refetch_cadence.py` and
  `tests/test_incomplete_snapshot_not_written.py` hunk-by-hunk — every changed line is inside a
  docstring, a comment, or an assert's failure-message string; the assert CONDITIONS are
  byte-identical before and after. Changing a test's prose is a cheap place to hide a loosened
  guard, and none was loosened.
- Checked the RED-first evidence in `acceptance_evidence.md` against the code and confirmed the old
  delete functions would produce exactly the pasted failure text.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Tested the central claim ("no dbt change is needed") against the actual SQL rather than the
  comments: read all four fixture-detail staging models plus `stg_apif__players` and confirmed each
  is a `select *`/faithful unnest with no `qualify` and no dedup; read the three whole-league
  staging models and confirmed each carries
  `qualify row_number() over (partition by league_code order by ingested_at desc) = 1`, which picks
  the newest row regardless of how many older versions now survive.
- Read the consuming base models and confirmed each dedups on the correct entity key with
  `raw_ingested_at desc`: `base_apif__fixture_events.sql:22-28`,
  `base_apif__fixture_players.sql:92-96`, `base_apif__fixture_statistics.sql:64-70`,
  `base_apif__player_team_season.sql:21-24`. Confirmed `stg_apif__lineups` has no base consumer,
  matching the new header warning.
- Hunted for anything assuming one row per key: no `unique` test exists at the sub-league grain in
  `stg_apif__generic.yml` (only `not_null`); the singular DQ tests check emptiness, not uniqueness;
  `assert_event_team_in_fixture_participants` operates on the post-dedup core layer. Nothing was
  broken or silently invalidated.
- Confirmed the four staging `.sql` diffs and the yml diff touch comments/descriptions only — no
  `select`, `qualify`, `where` or column list changed — matching the "no SQL changes" claim.
- (Round 1 verdict; its surface is unchanged by the two amendments, which added only ingestion,
  tests and a diagnostics script.)

## escalations
(none)

<!--
Round 1: 2 PASS, 2 FAIL. Both FAILs were the same defect found independently — stale module
docstrings contradicting the code beneath them. Fixing only the three files the reviewers NAMED
would have been fixing the instance; the repo-wide sweep that followed found six more, three of
them outside scope, which is why there are two contract amendments. The most consequential single
find was platform's: the contract's own verification grep was scoped narrower than its own
sentence, which is the #904 class this project keeps paying for.
-->
