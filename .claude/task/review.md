# Review — chore/description-cleanup-core-base-intermediate — 2026-08-20

> MR4 of the description-drift programme, and the last content MR before the gate. Both required
> reviewers FAILed round 1 with one finding each. One was correct and is fixed; the other rested
> on a premise I disproved with evidence, and the reviewer withdrew it on seeing the file. Both
> PASSed on a narrow round-2 confirm.

diff_sha256: a893d644442094379c0bd509ce8a69dcc14a9d11fec09ff6c56f3ecd393803d8

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- All changed files are inside `scope_paths`; no `.sql`, test, config, column or model behaviour
  changed. Verified hunk by hunk that every one touches only a `description:` block.
- The file set matches the six-MR split's MR4 row in `escalations.log`. Nothing from MR5 (the gate
  script) or MR6 (`persist_docs`) leaked in, and the "partition key" instances in five docs and in
  `.claude/hooks/dbt_layer_gate.py` were correctly left alone as GitLab #79.
- ROUND 1 FAIL, WITHDRAWN ON EVIDENCE: the finding was that this diff destroyed two CPO rulings —
  base-prepares/dim-publishes, and the "only team name in the product" identity claim — because
  neither is in `escalations.log`. The search was right, the inference was not. Both are verbatim
  in `base_apif__teams_global.sql:1-10`, along with the collision-ladder rationale, and MR4 edits
  no `.sql` file at all. `engineering_standards.md` §1.2 makes a model's own header a legitimate
  home for its "why". The identity ruling is additionally already logged, as the 2026-08-19
  team-name entries.
- WHAT THE FINDING DID SURFACE, and it was worth having: the base-prepares/dim-publishes ruling
  had no home outside that one SQL comment, which is thin for an architectural ruling. It is now
  rescued into `escalations.log`, together with a note that this class of check must search the
  model file and not only the log. `decisions_reserved` was corrected to say where "elsewhere"
  includes, rather than claiming a bare ruling-by-ruling check.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- ROUND 1 FAIL, now fixed: `dim_date`'s description claimed the calendar ran July 2015 through
  December 2030. `dim_date.sql:6-9` builds a spine from 1900-01-01 to 2101-01-01 with no filter,
  so the claim was false — and false on main too; my rewrite had reworded it without checking,
  the exact failure this contract names as its one real risk. I found it independently while
  checking my own claims, minutes before the review landed. Now "one row per day from 1900
  through 2100", confirmed correct on round 2 including the exclusive end bound.
- The removed "explicit ref() per competition staging" claim: each of the three models reads ONE
  generic `stg_apif__*`, so the new text is true and the old text described a per-competition
  pattern the repo forbids and `check_layer_contract.py` blocks.
- `base_apif__teams`' union across teams, fixtures, standings, statistics, player stats and
  events matches its SQL. `base_apif__competition_seasons`' dedup claim matches its `qualify`.
- `base_apif__teams_global`: the slug ladder compressed from 2,441 chars to ~570 still matches the
  CASE ladder in the SQL — bare, country-anchored, id-suffixed, NULL beyond.
- `fct_fixture` final-time-goals-only, `fct_transfer`'s deliberate absence of relationship tests,
  `dim_team_competition_season_mapping`'s fixture-derived membership including scheduled fixtures,
  and `dim_country`/`dim_region`'s publishes-never-corrects claims all check out against SQL.
- All three bulk-replaced `fixture_sk` descriptions landed, and the incremental-vs-full-refresh
  text is true for each of the three facts it now sits on.
- Every `{{ doc() }}` reference still resolves, and no description contradicts a shared block or a
  sibling column in the same file.

## escalations
(none)
