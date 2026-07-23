# Review — feat/player-career-minutes — 2026-07-23

diff_sha256: 1a3712586afddd48573f65fe869b730a2d92342003f4d6fe108abd2711df9596

rounds: 3

> Round count note (honest, for the audit trail): this branch ran three earlier rounds against TWO
> now-superseded scopes — first adding a `minutes_per_appearance` ratio (analytics-engineer FAIL: an
> uncatalogued rate), then adding a `metric_catalogue` row (football-analytics-expert FAIL: the
> denominator counts matchday selections). The CPO re-scoped the task after that second FAIL was
> verified against production, and the contract was rewritten. The count above is for the CURRENT
> scope (the appearance-definition fix): round 1 full review, round 2 delta, round 3 confirmation.
> `football-analytics-expert-reviewer` is NOT in the required set for this diff — its trigger path
> `dbt_project/seeds/metric_catalogue.csv` was reverted and is absent — but its FAIL is what found the
> defect this PR now fixes, and the metric it objected to is deferred to the PR that consumes it.

## scope-auditor
VERDICT: PASS
risks_checked:
- Serial amendment vs uncontrolled drift: five amendments are recorded, each naming its authority
  (CPO "Then it is wrong" / "Players are part of the squad even with zero appearances" / the two
  reversals). Verified the diff stays inside the amended `scope_paths` with no undeclared file, and
  that the additions are one defect class rather than an open-ended refactor.
- Contract honesty about its own false claim: the impact_map previously asserted "Neither is read by
  scripts/export_site_data.py (checked)". Verified the contract now states plainly that this was FALSE
  and not independently verified, and records the true code path — it does not launder the error.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The three round-2 findings are genuinely fixed: `int_player_season_position.yml` and
  `int_player_profile__yoy.sql` no longer carry the pre-fix "appearances-with-stats" phrasing, and the
  contract's export claim is corrected. The export path was re-verified independently
  (`export_site_data.py:688` selects `mart_player_profile`; `_strip_identity` drops only bio fields;
  the yoy appearance fields do reach `players/{id}.json`).
- No new SQL defect crept in: each of the four fixed writers shows a single coherent hunk implementing
  `countif(coalesce(minutes_played, 0) > 0)` or the `where coalesce(minutes_played, 0) > 0` leg filter,
  with no extraneous or conflicting edits.
- (Earlier rounds, carried) `starts` correctly needed no change — `is_starter` is stored as
  `coalesce(minutes_played,0) > 0 and not coalesce(is_substitute,false)`, so the new
  `starts + substitute_appearances = appearances` test holds by construction. Confirmed empirically on
  production: 0 violations across 170,533 club-seasons.
- (Earlier rounds, carried) The `appearances >= 1` -> `>= 0` change is a legitimate narrowing, not a
  loosened guard: the old expression asserted the premise the CPO overturned, and 26,530 production
  rows never satisfied it.

## escalations
- question: `minutes_per_appearance` — a display-support mart column, or a catalogue-governed metric?
  CPO ANSWER: catalogue it (AskUserQuestion 2026-07-23, "Catalogue it now"). Subsequently DEFERRED out
  of this PR by the answer below, to land with the Squad tab on the corrected denominator.
- question: the ratio's denominator counts matchday selections, not appearances (verified on
  production). Ship the ratio anyway, drop it, or fix the count?
  CPO ANSWER: "Ship minutes only, fix apps next" (AskUserQuestion 2026-07-23), then, on being shown
  that appearances counts squad selections: "Then it is wrong" — fix the definition.
- question: should never-played squad members be dropped from the career log or kept?
  CPO ANSWER: "Players are part of the squad even with zero appearances" (2026-07-23) — kept, counted
  as 0. Nothing is deleted.
