# Review — feat/rank-in-the-warehouse — 2026-09-09

diff_sha256: 20a9ee291d599f40d97070821b699310a8638c124c5a2fe63b6b2f50b477561b

rounds: 2

Round 1: both reviewers PASSED. Round 2 was NOT forced by a FAIL — `analytics-engineer-reviewer`
flagged a coverage gap without failing it, and a flagged trade-off is still a trade-off in this
repo, so the gap was closed and the delta re-reviewed rather than the pass banked.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 — verified both CPO rulings quoted in `contract.md` (RULING 1 and RULING 2, 2026-09-09)
  appear VERBATIM in `.claude/task/escalations.log` as added by this same diff, including the "yes,
  that's the rule" line and the fewer-minutes reasoning. No attribution without citation.
- Round 1 — every touched file (`mart_leaderboards.sql`, `shared.yml`, the new singular test,
  `layering.md`, `contract.md`, `escalations.log`) is listed in `scope_paths`; nothing outside it.
- Round 1 — `decisions_reserved` genuinely leaves the cross-league ordering, `mart_team_leaderboards`
  and `competitionOrder.mjs` open rather than smuggling them in as decided.
- Round 1 — the impact_map is evidenced with actual `dbt ls --select mart_leaderboards+` output
  (27 nodes, zero downstream models), not asserted from memory; A6 satisfied.
- Round 1 — the new singular test adds a stricter invariant rather than narrowing an existing one;
  checked specifically for a coverage-cut dodge.
- Round 1 — scanned the whole diff for credential-shaped content and for an undeclared NEW MECHANISM
  or RECURRING COST threshold; none found, and both thresholds are declared in `decisions_taken`.
- Round 2 delta — the added `wrong_leader` clause is additive only: the two pre-existing conditions
  are untouched and still OR'd, so this is a strict widening of the detection surface and not a
  loosened guard. Verified line by line rather than accepted from the brief.
- Round 2 delta — the reworded `layering.md` sentence claims no authority beyond what round 1
  already checked against `escalations.log`; the rule content itself is unchanged.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 — window-function generality: both `dense_rank()` and the new `row_number()` partition on
  `(league_code, season_api_year)` with no per-competition branching and no hardcoded league
  identifier; checked against every board in `count_boards` and `rate_boards`.
- Round 1 — the `rank` consumer contract is genuinely untouched: `board_rank as rank` and
  `where board_rank <= 10` are unchanged and the `rank` description is byte-identical. Also
  confirmed the `league_leader_order = 1` row can never fall outside the top-10 cut, because it
  shares the same primary sort key as `board_rank`.
- Round 1 — the new test is not tautological: its second invariant recomputes `max(sort_value)` and
  `min(minutes)` from raw rows instead of re-deriving the model's own window expression, so dropping
  the `minutes` leg makes it fire. It can fail for the reason it exists.
- Round 1 — catalogue governance: `assert_no_uncatalogued_season_metric` scopes only to the three
  `int_*` canonical models (confirmed via its `depends_on` refs), so an ordinal column on a mart
  needs no catalogue row.
- Round 1 — independently grepped `dbt_project/` for `mart_leaderboards`: the only real
  `ref('mart_leaderboards')` calls are two tests; every other hit is prose. The "LEAF, zero
  downstream models" claim in the impact map is corroborated, not taken on trust.
- Round 1 — `layering.md` internal consistency: the "Allowed in the frontend" list contains no
  sorting allowance that would contradict the new unconditional ban, and no other section permits
  page-side ordering.
- Round 2 delta — traced the new third clause through the `leaders`/`best` CTEs.
  `fewest_minutes_at_best` is `min(minutes)` over rows sharing the leader's own `sort_value`,
  computed independently of the `is not null` gate the first two clauses use, so it fires exactly on
  the nulls-first regression and stays correctly silent both for an untied leader with unknown
  minutes and for a wholly-NULL tie group. No false positive or negative found.
- Round 2 delta — the `layering.md` pointer now resolves forward to the section's own test sentence
  rather than to a bullet that had itself been rewritten; the round-1 ambiguity is gone and no new
  one is introduced.
- Round 2 delta — confirmed no model SQL, seed, `dbt_project.yml` or export file moved, so round 1's
  impact-map and consumption-layer conclusions still stand unmodified.

## escalations
(none)

The two §10 questions this branch rests on were put to the CPO and ANSWERED before any code was
written — they are rulings recorded in `escalations.log`, not open escalations. The questions this
branch deliberately does NOT answer are in `contract.md`'s `decisions_reserved`.
