# Review — fix/retire-team-dribbles-pct-510 — 2026-06-22

> #510 — retire the TEAM dribbles_success_pct metric end-to-end (executing the 2026-06-11 display
> ruling; CPO directed (A)). Two team surfaces (momentum + season-record); player metric untouched.
> Round 2 after an analytics-engineer FAIL surfaced three stale doc references (now fixed; two files
> added to scope via a recorded amendment). Required reviewers: scope-auditor + analytics-engineer
> (dbt_project/**) + football-analytics-expert (metric_catalogue.csv).

diff_sha256: f6ba94234e80c34cb79f542e6b276f0128bb5265529e5eb316df61733779b4b3

## scope-auditor
VERDICT: PASS
risks_checked:
- Downstream transparency after column removal: mart_matchday_insights (the sole downstream
  consumer of mart_momentum__team) projects explicit columns, never dribbles_success_pct, so the
  removal is transparent — no downstream model breaks or needs changes.
- Complete retirement across team surfaces + valid amendment: team dribbles_success_pct removed from
  the catalogue, both team marts, both team int models, both range tests, and all stale docs; the
  "TWO team surfaces" claim is correct; the two amended-in files (test + macro) are comment-only,
  non-structural, with the amendment recording authority (the reviewer FAIL + standing doc-sync rule).
  Executes the 2026-06-11 ruling — no new §10 metric decision; no retained metric's value changes.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- mart_matchday_insights downstream transparency: it `select *`s mart_momentum__team into CTEs but
  its final SELECT is a fully-enumerated explicit column list that never named dribbles_success_pct —
  the retired column is invisible to it without any change, consistent with the impact_map.
- SELECT-list integrity + completeness: the final SELECTs of mart_momentum__team, mart_season_record__team,
  int_momentum__team, int_season_record__team all terminate cleanly on duels_won_pct (no dangling
  comma); the three prior stale-doc findings (schema.yml metric_id desc, the unique-by-entity test
  comment, the team-benchmark macro comment) are resolved; grep confirms no stale TEAM
  dribbles_success_pct remains (player refs + the int_player_season_ratios test legitimately retain it).

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Football-validity of the asymmetric drop (team dribbles retired, team duels retained): duels_won_pct
  is a bilateral provider-standardised contest with clear team-level meaning and broad coverage;
  team dribbles_success_pct is a noisy individual-skill aggregate with thin coverage, already
  "defined but not displayed" in the 2026-06-11 contract. The distinction is football-coherent.
- Surgical precision: the diff removes exactly the one CSV row (dribbles_success_pct,team); the player
  rows (dribbles_success, dribbles_attempts, dribbles_success_pct,player) are intact and unmodified.

## escalations
(none)
