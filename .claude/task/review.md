# Review — feat/board-leader-order — 2026-09-09

diff_sha256: 2d3e0b4d3c6bd8d69ed1a24c56374d53c93bed4412a0ba584f22dfd552a4ad66

rounds: 2

Round 1: both reviewers PASSED. Round 2 was not forced by a FAIL — `scope-auditor` flagged, without
failing, that the contract's RECURRING COST paragraph still described a self-join the shipped SQL
does not contain. A flagged trade-off is still a trade-off, and a contract that misdescribes its own
change is wrong even when it overstates rather than hides. Corrected and re-reviewed as a delta;
`analytics-engineer-reviewer`'s round-1 pass stands because the delta touched no SQL.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 — verified both 2026-09-09 CPO rulings against `escalations.log` verbatim: "All ranking
  and ordering lives in the warehouse. The page renders the order it is served", and the
  fewer-minutes tie-break with the `player_sk` fallback. Both match the contract's quotes exactly;
  no fabricated authority.
- Round 1 — checked the contract's admission that two EARLIER contracts were wrong ("the cross-league
  order could not live in the mart") against the removed text in the diff. The prior claim is quoted
  accurately and the correction is sound: restricting a total order to a subset preserves relative
  order. The admission narrows scope back to implementing an existing unconditional ruling rather
  than covering a new unauthorised decision.
- Round 1 — `decisions_reserved` (the `player_sk` last resort, `mart_team_leaderboards` parity,
  `competitionOrder.mjs`) are each untouched in the diff; nothing reserved is silently decided.
- Round 1 — every changed file is in `scope_paths`. `layering.md` needed no edit because MR A
  already carries the rule wording.
- Round 1 — impact_map is evidenced with a real `dbt ls --select mart_leaderboards+` run against
  THIS checkout (29 nodes, 0 downstream models), not carried over from MR A, and the prod comparison
  of rendered league order is measured rather than asserted.
- Round 1 — no credentials anywhere in the diff; the CTO thresholds are declared and hold against
  the actual SQL.
- Round 2 delta — compared the corrected paragraph against the shipped SQL and confirmed no
  self-join exists (one `ranked` CTE feeding the final select, two window functions), so the
  correction is accurate and agrees with the file's own inline comment about the abandoned form. The
  NEW MECHANISM and RECURRING COST conclusions are unchanged; no new authority is invoked.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Window generality: `board_leader_order` partitions by `metric_key` alone and `league_leader_order`
  by `(league_code, season_api_year)`. Neither references a league or competition literal — generic
  across every `league_code`.
- Equivalence of the shipped form to the obvious one, worked by hand: sorting leaders to the front of
  the window (`case when league_leader_order = 1 then 0 else 1 end` first) and discarding the
  non-leaders' numbers with a CASE assigns leaders exactly the integers a leaders-only filtered CTE
  would. Non-leaders sitting after them in the same partition cannot perturb their relative order or
  their values. Confirmed equivalent, not a defect.
- NULL and uniqueness are STRUCTURAL, not merely asserted: `where board_rank <= 10` filters before
  the window runs, and a league leader always carries `board_rank = 1`, so no leader is ever excluded
  from the partition; `row_number()` cannot repeat a value within it.
- The new test is falsifiable and not a tautology: its third invariant walks consecutive pairs with
  `lead()` and asserts the later row is not strictly better on the ruled keys, rather than
  re-deriving `row_number()` with the same ORDER BY — which would pass for any ordering.
- `rank` and `league_leader_order` are byte-for-byte unchanged; read the full `ranked` CTE and the
  outer select across the diff hunk boundaries to confirm it.
- Catalogue governance: `assert_no_uncatalogued_season_metric` scopes to the three canonical `int_*`
  models, not this mart, and `board_leader_order` derives no value — it orders already-catalogued
  ones. Consistent with the existing precedent for `rank` and `league_leader_order`.
- Description hygiene: the new column's description is well within BigQuery's 1,024-character limit,
  which matters because `persist_docs` is on and a breach fails the prod build.
- Scope: no `scripts/export_*.py` or `site_v2` file is in this patch, so the consumption-layer
  trigger is not engaged — the export change is #40 MR B's.

## escalations
(none)

The two §10 questions this work rests on were ruled on before any of it was written and are recorded
in `escalations.log`. What this MR deliberately does NOT answer is in `decisions_reserved`.
