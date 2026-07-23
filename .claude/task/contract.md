# Task contract — fix the appearance definition, and add minutes to the career mart

> Written on a CLEAN tree (branch `feat/player-career-minutes` off main after #810 merged).
> Amended three times, each on a clean tree, each with the CPO authority recorded — see `amendments:`.

objective: >
  Fix a VERIFIED data defect: `appearances` counts matchday SELECTIONS, not time on the pitch, because
  the finished-match player-stat rows it counts include unused substitutes. An appearance now requires
  the player to have taken the pitch (`minutes_played > 0`). CPO ruling 2026-07-23, verbatim:
  "Then it is wrong". Zero-minute squad members are KEPT as rows with `appearances = 0` — CPO: "Players
  are part of the squad even with zero appearances" — so no row is deleted; only the count is corrected.
  Also carries `minutes` up into `mart_player_career` (the original PR1 scope), since both are
  prerequisites for the team page Squad tab and touch the same models.

refs: >
  Measured against production BigQuery 2026-07-23 (evidence, not inference):
  - 383,416 of 1,677,854 `fct_fixture_player_stats` rows have null minutes; 382,942 of those are
    0-minute unused substitutes.
  - 87,739 of 170,533 career club-seasons (51.4%) carry an inflated appearance count; 26,530 record a
    player who never took the pitch; mean mins/app 44.9 as-built vs 60.5 corrected.
  - `mart_player_career`'s own docstring claimed it was "distinct from dim_player_team_season_mapping
    (roster membership incl. never-played members)" — the data disproves it, so this is a bug against
    stated intent, not a deliberate definition.
  Verified this session, and it bounds the blast radius:
  - Every qualification floor downstream (benchmarks, leaderboards) keys on `minutes >= 270`, NOT on
    appearances — so those surfaces are insulated from this change.
  - `starts` is ALREADY correct: `is_starter` is derived as `coalesce(minutes_played,0) > 0 and not
    is_substitute`, so it already requires pitch time. Only `appearances` and `substitute_appearances`
    are wrong.
  - `int_player_season__metrics` re-aggregates by SUMMING the club-season base, so fixing the base
    fixes it with no edit there.
  - Team-side `games_in_window` (`int_team_momentum__metrics`) is a count of TEAM legs and is NOT
    affected — a team always plays its own match.

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_player_club_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/4_intermediate/shared/int_player_profile__yoy.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/5_marts/shared/mart_player_career.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - .claude/active_work.md

impact_map: >
  writers: FOUR intermediate models each compute a player participation count from raw legs, and all
    four carry the same defect (fix the CLASS, not one instance). The fourth,
    `int_player_season_record` (`row_number()` over unfiltered legs as `match_number`/`games_played`),
    was MISSED by my first grep sweep and caught by the analytics-engineer reviewer — recorded here
    because the sweep claim in an earlier revision of this contract was false as written. Its
    consumers `mart_player_season_record.games_played` and `int_player_profile__yoy`
    (`appearances_cutoff`/`appearances_prev`/`appearances_prev_full` -> `mart_player_profile`) would
    otherwise have carried a selection-based "appearances" beside the corrected one in the same row.
    CORRECTION (2026-07-23, second analytics-engineer FAIL): an earlier revision of this contract said
    "Neither is read by scripts/export_site_data.py (checked)". That was FALSE and the "(checked)" was
    not mine to claim — I restated a reviewer's aside as my own verification. Verified now, by reading
    the code: `export_site_data.py:688` does `select * from mart_player_profile`, and `_strip_identity`
    (`:588-597`) drops only team/player bio fields, so the yoy appearance fields DO flow into
    `seasons_out` (`:417-424`) and into `players/{id}.json`. `mart_player_season_record.games_played`
    genuinely is unread. No player JSON is committed yet, so nothing wrong has shipped — but the export
    would have emitted an inconsistent "appearances" pair on its next run. The
    four:
    `int_player_club_season__metrics` (`count(*) as appearances` + `countif(is_substitute) as
    substitute_appearances`), `int_player_season_position__metrics` (`count(*) as appearances`), and
    `int_player_momentum__metrics` (`count(*) as games_in_window`, documented as "the player's
    appearance count within the side's window"). `minutes` additionally flows up into
    `mart_player_career`.
  examined_and_EXCLUDED (the sweep is only honest if the misses are named): every model reading
    `int_legs__player_match` / `fct_fixture_player_stats` was enumerated and each counting or
    sequencing construct in it judged. Four deliberately NOT changed, because none is an appearance
    count: `int_legs__team_from_players.players_with_stats` (a stat-COVERAGE count — we genuinely do
    hold stat rows for benched players, and their zeros sum harmlessly); `int_player_season__team`
    (picks a club by MOST RECENT leg — for "which club is he at", squad membership is the right
    signal, not pitch time); `mart_player_profile`'s modal-position pick (`order by count(*) desc`
    over position_code — a listed attribute, not a participation count); and the `row_number()` dedups
    in `base_apif__fixture_players` / `dim_player_team_season_mapping`. Team-side
    `int_team_momentum__metrics.games_in_window` counts TEAM legs and cannot carry this defect.
    `int_player_profile__contribution` was checked and NOT changed: it only SUMS goals/assists over
    legs (no participation count — verified, no count/row_number construct in it), so bench rows
    contribute 0 and its value is unaffected; it still reads unfiltered legs, so its
    "appearances-with-stats" wording remains accurate for what it actually does.
  documentation_sweep: the prose was swept with grep across the whole dbt project for every stale
    appearance phrasing, not spot-fixed at the sites the reviewer named — because two consecutive
    reviews failed on exactly that. Corrected: `mart_player_career` (SQL header + shared.yml model,
    appearances and minutes descriptions + the gate-test comment), `int_player_club_season.yml`
    (model + appearances), `int_season_record.yml` (model + games_played), `int_momentum.yml`
    (games_in_window), `int_player_season_position.yml` (appearances),
    `int_player_profile__yoy.sql` (its match_number description) and
    `int_team_season.yml` (int_player_season__metrics' "appearances = finished player-stat rows").
  downstream: dbt CLI is broken locally (documented in active_work.md), so lineage is traced by grep,
    the standing fallback. `int_player_club_season__metrics` -> `int_player_season__metrics` (sums it,
    so it inherits the fix) and -> `mart_player_career` (a LEAF mart: zero
    `ref('mart_player_career')` hits in models). `int_player_season_position__metrics` ->
    `int_player_competition_benchmarks` / `mart_player_competition_benchmarks` / `mart_leaderboards`,
    all of which gate on `minutes >= 270` and so do not change their qualifying population.
    `int_player_momentum__metrics` -> `mart_player_momentum` (carries `games_in_window` as a displayed
    count; it is NOT a rate denominator there — the ratios divide by their own atoms, verified).
    Consumption: `scripts/export_site_data.py` reads these marts by explicit column name and is NOT
    edited here.
  layer_rules: intermediate + marts. `check_layer_contract.py` passes (staging genericity untouched).
    No `league_code` hardcoding; the fix is competition-agnostic. Appearance counting is a playing-time
    DIMENSION (exempt in `assert_no_uncatalogued_season_metric`), so no metric_catalogue row is
    involved and no metric-governance question arises.
  deploy_order: all affected models are full rebuilds (`table`), so `ci-data-build` recomputes them on
    merge with no incremental-rename trap and no NULLed history. Numbers CHANGE on rebuild by design.
  blast_radius: REAL and intended — this corrects wrong numbers. `appearances` falls wherever bench
    selections were counted (51.4% of career club-seasons); 26,530 career rows go to `appearances = 0`
    but are RETAINED per the CPO. `substitute_appearances` falls to genuine sub appearances.
    `games_in_window` falls to games actually played. Benchmarks/leaderboards keep their populations
    (minutes-gated). Nothing is renamed or dropped. Nothing is live to users (the MVP is retired), so
    there is no user-facing regression risk.

decisions_taken: >
  (1) An appearance REQUIRES pitch time (`minutes_played > 0`) — CPO 2026-07-23 ("Then it is wrong").
  (2) Zero-minute squad members are KEPT as rows with `appearances = 0`, never deleted — CPO 2026-07-23
      ("Players are part of the squad even with zero appearances").
  (3) Consequently the `player_career_row_is_appearance_gated` test changes from `appearances >= 1` to
      `appearances >= 0`. This is NOT loosening a guard to make a change pass: the old expression
      encoded the very premise the CPO just overturned (that the mart excludes never-played members).
      It is narrowed to what still holds and its comment records why.
  (4) `substitute_appearances` gets the same fix (`is_substitute AND minutes > 0`); `starts` needs none
      (`is_starter` already requires minutes > 0). The invariant `starts + substitute_appearances =
      appearances` then holds and is added as a DQ test.
  (5) Fixing all three counts in one PR rather than one, because they are one defect class and leaving
      a known instance is the repeat failure mode this repo has been bitten by.
  (6) `minutes` is carried into `mart_player_career` (original PR1 scope): a playing-time dimension,
      not a catalogue metric, and unaffected by the defect (a 0-minute row adds 0 to the sum).

decisions_reserved:
  - `minutes_per_appearance` and its `metric_catalogue` row stay DEFERRED. The analytics-engineer
    reviewer ruled it catalogue-governed; the football-analytics-expert's proposed `neutral` direction
    is still open. It belongs in the PR that consumes it (the Squad tab), on the corrected denominator.
  - Whether the Squad tab lists zero-appearance squad members or only those with an appearance is a
    DISPLAY decision for the Squad-tab PR, not settled here. The warehouse now supports either.
  - PR2 (export + frontend + sample re-export) is a later increment and waits on this deploying.

done_when:
  - `appearances` = `countif(coalesce(minutes_played, 0) > 0)` and `substitute_appearances` =
    `countif(is_substitute and coalesce(minutes_played, 0) > 0)` in the club-season base;
    `appearances` likewise in the position model; `games_in_window` likewise in player momentum.
  - `mart_player_career` selects `minutes`; the appearance-gate test reads `>= 0` with its comment
    updated; every stale "distinct from roster membership" claim is gone from BOTH the SQL docstring
    and the schema YAML (swept with grep, not spot-fixed).
  - New DQ test: `starts + substitute_appearances = appearances` on the club-season base.
  - `python scripts/check_layer_contract.py` passes; YAML parses.
  - `ci-data-build` GREEN: dbt build succeeds and all DQ tests pass (dbt + SQLFluff do not run locally
    — CI is the gate).
  - ONE commit, pushed with an explicit refspec, PR opened. The CPO merges.

amendments:
  - 2026-07-23: + dbt_project/seeds/metric_catalogue.csv — authority: CPO Path A (AskUserQuestion)
    after the analytics-engineer FAILED round 1 ruling minutes_per_appearance catalogue-governed.
    SUPERSEDED below.
  - 2026-07-23: - dbt_project/seeds/metric_catalogue.csv (reverted) and - minutes_per_appearance —
    authority: CPO (AskUserQuestion, "Ship minutes only, fix apps next") after the
    football-analytics-expert FAILED round 2 finding the denominator counts matchday selections,
    verified against production BigQuery before acting.
  - 2026-07-23: + the three intermediate models and their YAMLs — authority: CPO ruling "Then it is
    wrong" (appearances) and "Players are part of the squad even with zero appearances" (keep the
    rows), plus "whatever is reasonable" on branch choice; content: fix the appearance definition
    across all three counts and keep the `minutes` column in the same PR. Amended on a clean tree.
  - 2026-07-23: + int_player_profile__yoy.sql — authority: the same CPO ruling ("Then it is wrong"),
    documentation only; content: its docstring described match_number as "the running count of the
    player's finished appearances-with-stats", the pre-fix definition. Found by the second
    analytics-engineer FAIL, together with a stale `appearances` description in
    int_player_season_position.yml (already in scope) and the false export claim corrected in the
    impact_map above. Amended on a clean tree.
  - 2026-07-23: + int_player_season_record.sql + int_season_record.yml — authority: the same CPO
    ruling ("Then it is wrong"), applied to a FOURTH instance of the identical defect that the
    analytics-engineer reviewer found after my sweep missed it; content: filter the builder's legs to
    played legs so `match_number`/`games_played` count matches actually played, matching the model's
    own documented intent ("one row per match the player appeared in"). Amended on a clean tree.
