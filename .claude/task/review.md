# Review — feat/team-board-order — 2026-09-09

diff_sha256: e0d6206d6cd88e07b691a0c3d568024a344a3bd2cc3e4330ce23cf304fad82b5

rounds: 2

Round 1: `scope-auditor` PASS, `analytics-engineer-reviewer` FAIL. Round 2: both PASS.

The FAIL was worth the round. The new test's `is_current_season` guard was cardinality-only, which
is the shape this repo had ALREADY strengthened on the player mart's sibling
(`assert_one_current_season_per_league.sql`), whose header records the two mutations that shape
passes green. Copying a guard's shape without reading what it had learned is the defect. Fixed by
checking cardinality, recency and row completeness, and mutation-proven three ways.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 — verified the CPO ruling the contract leans on exists VERBATIM in `escalations.log`: the
  2026-09-09 entry rejecting `season_games_played` with "will not work most of the time", and the
  disposition "yes, let's a separate issue to build something smarter at some later point" (filed as
  #114). The contract represents it as "no criterion, fall to a meaningless `team_sk`" and does not
  strengthen it into something he did not say. Ruling 1 is also present and correctly cited. No
  instance of the repo's recorded "asserted ruling not in the log" failure class.
- Round 1 — every changed file is in `scope_paths`; nothing outside it.
- Round 1 — `decisions_reserved` (#114's real tie-break, and whether the block's rows link to team
  pages) are neither decided nor smuggled in: `team_sk` is used only as a documented, explicitly
  meaningless stabiliser, and no linking logic appears anywhere in the patch.
- Round 1 — impact_map is evidenced with real `dbt ls --select mart_team_leaderboards+` output
  (22 nodes, ZERO downstream models), not asserted from memory.
- Round 1 — both CTO thresholds declared and checked against the actual SQL: only window functions
  inside a model that already ranks, plus one singular test. No new mart, macro, dependency or gate.
- Round 1 — credential sweep across the whole diff: nothing.
- Round 2 delta — the strengthened invariant KEEPS the original cardinality predicate verbatim as
  its first OR-branch and only ADDS two more, so any row-set that failed before still fails now.
  Monotonic strengthening, not a rewrite that trades away prior coverage. Checked because "never
  loosen a guard" is the standing item and a rewrite is exactly where a guard silently narrows.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL — the `is_current_season` guard was cardinality-only, regressing to a shape already
  strengthened on the sibling test, on the identical column in the mirror mart. Named both mutations
  it would pass green.
- Round 2 — equivalence to the sibling, checked aggregate by aggregate: same three conditions
  (cardinality, recency against the max season, full-row flagging), same OR combination, only
  restructured from CTE-plus-WHERE into a HAVING on the same grouping grain. No weaker substitution,
  no dropped branch. Equivalent in force.
- Round 2 — both named mutations re-derived against the new SQL rather than taken from the report:
  the ascending ORDER BY leaves cardinality at 1 but trips the recency branch; the `row_number()`
  reversion leaves cardinality and recency intact but trips `flagged_rows != season_rows`. Both are
  now structurally impossible to pass green.
- Window generality: every window partitions on `league_code` / `season_api_year` / `metric_key`
  with no per-competition literal anywhere in the model.
- `board_leader_order`'s CASE front-sort proven equivalent to a filtered-CTE-then-join: a
  `league_leader_order = 1` row necessarily carries `board_rank = 1`, so it always survives
  `where board_rank <= 10`, and non-leaders sorted to the tail cannot shift a leader's position.
- `is_current_season` against that same filter, given windows evaluate after WHERE: the surviving
  season set is identical to the unfiltered one, because a league-season's rank-1 team is never cut
  by a top-10 filter.
- Invariants 1-3 each check the OUTPUT independently of the window that produced it — counts,
  NULL-consistency, `lead()` adjacency — rather than re-deriving the same `row_number()`, so none is
  a tautology.
- Catalogue governance: the three columns are ordering and filtering scaffolding, not metrics, and
  match the un-catalogued precedent merged for the player mart in `!164` / `!165`.
- `rank` (i.e. `board_rank`) is untouched — the diff adds only a trailing comma to its existing
  `dense_rank()` definition.

## escalations
(none)

The tie-break question was put to the CPO and ANSWERED before the model was written — the
2026-09-09 entry in `escalations.log`. What is deliberately not answered is in `decisions_reserved`,
and a better tie-break is #114 at LOW priority.
