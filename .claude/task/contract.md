# Task contract — correct the gaps register against the reduced home-page design

objective: >
  `docs/wireframes/99_gaps_register.md` entries GAP-24..GAP-29 were written against the NINE-board
  Top players / Top teams design. That design was REDUCED to FOUR single-metric boards per block on
  2026-08-10 (the CPO's set, in his order, recorded verbatim in `design-mocks/gen_top_players.py`'s
  header and reflected in the rendered mocks). The register was never updated, so three of its six
  entries describe warehouse work for boards that no longer exist — including GAP-26, which the
  register still flags as "the highest-risk of the six". Reading the register today produces a
  materially wrong picture of what the home page needs. Void what the reduction killed, keep what
  survived, and register the two gaps the reduced design newly exposes.
refs: GitLab #40 (Top players) + #41 (Top teams) — the stated design authority; the 2026-08-10
  reduction recorded in `design-mocks/gen_top_players.py`; `.claude/active_work.md`'s
  "HOME PAGE: authority is #40 + #41 ... truth is FOUR boards of ONE metric, top 7".

scope_paths:
  - docs/wireframes/99_gaps_register.md
  - .claude/active_work.md

impact_map: >
  writers: none. This is a documentation correction only — no dbt model, no seed, no export, no
    site file changes. Nothing reads this register at build time; it is read by humans and by me
    when scoping home-page work.

  downstream: the register is an INPUT to scoping decisions, not to code. Correcting it changes
    what the next session believes is required for the Top players / Top teams blocks. That is the
    point: the stale version caused me to report "9 rankings, 4 missing" and to raise a
    goals-conceded ranking alarm for a board deleted eight days earlier, both this session.

  layer_rules: not applicable — no layer is touched. The corrections were derived by READING the
    warehouse (`mart_leaderboards.sql`, `int_team_season__metrics_cumulative.sql`) and the
    generators, and every claim below is a grep result, not a recollection.

  verification performed BEFORE writing (each a command, not a memory):
    - `mart_leaderboards` count_boards list read in full: goals, scorer_points, shots_on_goal,
      dribbles_success, passes_total, passes_key, duels_won, defensive_actions, cards_total.
      `grep -c "'assists'"` = 0 -> assists is a COLUMN on the mart but NOT a ranked board.
    - `grep -c "team_sk"` on `mart_leaderboards.sql` = 0 -> GAP-27 (no club per row) still live.
    - `grep -n "partition by"` -> `partition by league_code, season_api_year` -> the mart ranks
      WITHIN one league; the design ranks ACROSS seven pooled leagues. Distinct from GAP-28's pool
      MEMBERSHIP question, so it needs its own entry.
    - all four Top-teams metrics (`goals_per_match`, `shots_on_goal_per_match`,
      `passes_per_match`, `duels_per_match`) confirmed present in
      `int_team_season__metrics_cumulative.sql` -> GAP-29's "already carries them" claim holds.
    - no team-side leaderboard mart exists: `find dbt_project/models/5_marts -iname "*leaderboard*"`
      returns `mart_leaderboards.sql` only.

  blast_radius: one documentation file plus the handover. No behaviour change anywhere.

decisions_taken: >
  VOID vs REWRITE. GAP-24/25/26 are struck through and marked void rather than rewritten in place,
  and the two live gaps the reduced design exposes get NEW ids (GAP-30, GAP-31). Rewriting an id's
  content in place would silently change what an external reference to "GAP-24" means; the register
  already has a withdrawal convention (GAP-04, struck through + **withdrawn** + the reason) and this
  follows it exactly rather than inventing a second one.

  NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - Whether the four voided/new gaps become GitLab issues is the CPO's, unchanged by this task —
    the register's own header already says accepted gaps become their own issues and that gap fixes
    never ship inside blueprint PRs.
  - The pass-accuracy defect that GAP-25 mentioned in passing is NOT resolved by voiding GAP-25;
    `gen_top_players.py` records it as re-filed separately. Not touched here.
  - Whether the register needs a periodic reconciliation mechanism (this is the second time a
    design change left it stale) — a process question, raised in the handover, not decided here.

done_when:
  - GAP-24, GAP-25, GAP-26 struck through and marked void, each naming the 2026-08-10 reduction as
    the cause and stating what specifically no longer exists.
  - GAP-27, GAP-28, GAP-29 confirmed still live, with their text reconciled to the four-board
    design where it referenced the nine-board one.
  - GAP-30 (assists is not a ranked board) and GAP-31 (pooled-vs-per-league rank grain) added.
  - `.claude/active_work.md` records that the register was stale and is now corrected, under the
    16,000-character cap.
