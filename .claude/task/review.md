# Review — fix/530b-player-catalogue-integrity — 2026-07-02

> G3 Lock artifact. #530(b): fix the player catalogue-integrity gap. Adds an event-derived `goals_penalty`
> atom to int_legs__player_match; completes the two player metric_catalogue rows (finishing_efficiency:
> base/num/denom + direction=higher_better; duels_won_pct: direction=higher_better); syncs the seed's own
> schema.yml deferred-rows prose. Season model untouched (Option Y). Required set (routing): scope-auditor
> (always) + analytics-engineer (dbt_project/**) + football-analytics-expert (metric_catalogue.csv).
>
> Round 1 (hash e339d31) — scope-auditor PASS, football-analytics PASS, analytics-engineer FAIL: the seed's
> own dbt_project/seeds/schema.yml still listed finishing_efficiency among "the deferred player rows pending
> the penalty atom" — SSoT self-contradiction after the CSV row was completed.
> Round 2 (hash 959cfc07) — added schema.yml to scope + dropped finishing_efficiency from the
> deferred enumeration (kept goals_penalty/goals_open_play, still blank) + corrected the now-stale
> "pending the atom" phrasing. CODE (leg + CSV) byte-identical to round 1. All three reviewers PASS.
> Round 3 (hash 08375bb5, THIS lock) — ci-data-build round-2 failed a SQLFluff **ST06** rule: the new
> `coalesce(...) as goals_penalty` sat among the simple `ps.*` columns; ST06 wants calculations AFTER
> simple targets. Moved it to the trailing calculated-columns block (before round_order) — still an output
> column, catalogue formula still resolves, semantics identical. CSV/schema.yml/contract byte-identical to
> round 2. All three reviewers re-confirmed PASS (resolvability guard is name-based, not positional).

diff_sha256: 08375bb5c920f0299e7ee85672841e40ee7a5608e9e0132e7ece2dc430d2efd8

## scope-auditor
VERDICT: PASS
risks_checked:
- Penalty-atom resolvability in metric_catalogue — goals_penalty added to int_legs__player_match from the
  same event derivation as the team leg; assert_metric_catalogue_expr_resolvable now includes
  finishing_efficiency,player (was skipped with blank base_relation) and resolves `sum(goals_total -
  goals_penalty)` + `sum(shots_on)` to real leg columns. Left join on (fixture_sk, player_sk) is
  cardinality-preserving; coalesce(...,0) null-safe. Held.
- schema.yml/CSV consistency round-trip — the 3rd amendment added schema.yml to scope; the description now
  records finishing_efficiency as done + goals_penalty/goals_open_play still pending (verified against the
  live CSV blanks). CSV rows well-formed (14 fields); direction=higher_better on both; interpretation blank
  (v1.x player exemption, schema.yml). Doc + code synchronized; no §10 decision; formula pure. Held.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Doc/data SSoT drift (the round-1 defect) — re-verified schema.yml base_relation description
  (lines 108-110) against the live CSV: finishing_efficiency (row 15) fully filled + no longer in the
  deferred enumeration; goals_penalty/goals_open_play (rows 31-32) genuinely still blank and the only two
  listed; the "Blank for the deferred rows above" refs now resolve to those two. No stale reference remains.
  Fully resolved.
- Join fan-out on the new leg column — the events CTE groups by (fixture_sk, player_sk) before the left
  join, so it cannot multiply rows; the leg's unique_combination_of_columns([fixture_sk, player_sk]) grain
  test still holds. Derivation parity with the season model's own CTE confirmed (same event filter/grain/
  coalesce); Option Y (season model untouched) → finishing value unchanged. Held.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- finishing_efficiency (player) — open-play conversion `(goals − penalty goals)/shots on target` is
  football-valid; goals_total already excludes own goals (provider convention → only penalties subtracted,
  vs the team row's penalties+own-goals — a real accounting asymmetry, not a copy-paste gap); higher_better
  correct; the >100% edge is honestly nulled ([0,1]), cap stays model-side. Held.
- duels_won_pct (player) direction + schema.yml prose — higher_better matches the team row for the identical
  formula (a duel win-rate is a genuine quality signal, no style-vs-quality caveat needed); the schema.yml
  edit is pure bookkeeping (verified against the live CSV blanks/fills), no formula/direction/football claim
  embedded. Held.

## escalations
(none) — completes two player catalogue rows to match the already-computed formula + the CPO direction
ruling (both higher_better, 2026-07-02); no new metric invented; exprs pure (cap stays model-side). The
season-model single-source repoint + the remaining #530(b) rows (goals_penalty, goals_open_play) are
flagged follow-ups, reserved.
