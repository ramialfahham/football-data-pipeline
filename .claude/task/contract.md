# Task contract — an awarded match is a RESULT without a STAT LINE

objective: >
  Count `AWD` (technical loss) and `WO` (walkover) as played matches for RESULTS — points, W/D/L,
  goals, games played — while leaving every statistical rate untouched, because those matches have no
  stat line and never will. Normalise `status_short` casing at staging so matching on the code is
  safe at all.

refs: >
  Not an issue — found while diagnosing the freshness guard that has been failing the nightly.
  ⭐ **THE DECISION IS THE CPO'S**, taken on measured evidence put to him: 24 past fixtures carry
  `AWD`/`WO`, 23 of them with a score, and NONE of them counts anywhere today because every
  downstream model filters `status_short in ('FT','AET','PEN')`. Recorded in
  `.claude/task/escalations.log`, entry
  `2026-09-06 — feat/awarded-and-walkover-count-as-played — AWARDED MATCHES COUNT AS PLAYED`.
  ⛔ **AND HE APPROVED A SECOND, LARGER CHANGE AFTER MY FIRST PLAN WAS SHOWN TO BE WRONG.** The plan
  I put to him — "add AWD/WO to the played filter" — would have NULLED every statistical metric for
  ~16 team-seasons and withheld an entire competition's deserved-vs-actual read. That is in the same
  escalation entry, with the measurement. He answered "same MR".
  ⚠ The casing standardisation is his too, unprompted: *"another input to standardize"*, on being
  shown `Canc`/`CANC`, `Abd`, `WalkOver`/`Walkover`.

scope_paths:
  - .claude/task/contract.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log
  - dbt_project/models/1_staging/api_football/stg_apif__fixtures_next.sql
  - dbt_project/models/1_staging/api_football/sources.yml
  - dbt_project/models/1_staging/api_football/staging.yml
  - dbt_project/models/4_intermediate/shared/int_legs__team_match.sql
  - dbt_project/models/4_intermediate/shared/int_team_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum_window.sql
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics_cumulative.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/5_marts/shared/mart_team_momentum.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_awarded_matches_do_not_null_team_stats.sql
  - dbt_project/tests/assert_momentum_awarded_matches_do_not_null_team_stats.sql

impact_map: >
  ⛔ **THIS IS THE MAP THAT MATTERS, because my first plan was wrong precisely for missing it.**
  The statistical rates are gated ALL-OR-NOTHING: `when games_with_team_stats < games_played then
  null`. One played match without a stat line nulls EVERY rate for that team's whole season. An
  awarded match has no stat line by nature, so counting it as played — the change the CPO asked for —
  would silently destroy the stats it was never meant to touch.
  MEASURED, on prod, before writing a line: Toulouse and FC Nantes (L1 2025) both sit at
  33 played / 33 with stats today, so both have working metrics and everything to lose. Same for
  Flamengo and Independiente Medellín (LIBER 2026), Senegal and Morocco (AFCON 2025), plus UEL 2021,
  BPL 2022 and CAFCL 2020 — ~16 team-seasons.
  ⛔ And it CASCADES: `int_team_season__deserved_vs_actual` withholds the read unless EVERY team in a
  league-season has a computable shots-on-target figure, so two nulled teams would withhold the
  entire **Ligue 1 2025** deserved-vs-actual read — all 18 teams.
  THE FIX: gate on `games_expecting_team_stats` (played minus awarded/walkover) instead of
  `games_played`. An awarded match is then not "missing" data; it is a match that could never have
  had any.
  gate census, two-sided and counted rather than estimated: **35 sites in 2 files** —
  `int_team_season__metrics_cumulative.sql` 25 (`< games_played`), `mart_team_momentum.sql` 10
  (`< games_in_window`). Both surfaces are changed; fixing one and not the other would leave the
  season figures and the form figures disagreeing about the same match.
  NOT gated and therefore NOT touched: `games_with_player_stats`. Player-derived metrics use their
  own denominators under the player-null-is-zero ruling, so no gate reads it.
  writers: no ingestion change. The staging edit is a cast of an existing field, not a new read.
  consumers NOT edited, deliberately: `mart_team_fixture_stats` and every player-side filter. Those
  are STAT surfaces — an awarded match has no stat line, so adding it would add empty rows for
  nobody. The change is confined to the RESULT path.
  ⚠ `int_legs__team_match` already carries `and goals_home is not null and goals_away is not null`,
  so the ONE walkover with no score (CAFCL 2020, fixture 649441) is excluded with no extra guard.
  blast_radius: 24 fixtures, 12 (competition, season) groups, of which 3 are in a 2025+ season and
  exactly ONE is in an elite competition (L1 2025). Season figures move for the teams involved:
  games played +1, so per-match averages shift. That is the intended effect.

acceptance_criteria:
  - `status_short` is UPPERCASE for every row after the staging change, measured on prod: the
    `Canc` / `Abd` variants are gone and the `accepted_values` warning that has fired in every build
    goes to zero.
  - `AWD` and `WO` fixtures contribute to results: for a named affected team, `season_games_played`
    increases by exactly 1 and points/W-D-L move by the awarded outcome. Measured, not asserted.
  - ⭐ **No statistical metric that works today becomes NULL.** Compared team-season by team-season
    over the whole warehouse — not sampled, and not just for the affected teams.
    ⛔ **AGAINST A CONTROLLED BASELINE, NOT THE LIVE TABLE.** The live intermediate tables are a day
    older than the `fct_fixture` they derive from whenever the nightly fails, which it did on
    2026-09-07; and the momentum chain filters on `current_date()`, so its live mart is a moving
    target regardless. Both were measured naively first and both produced large phantom differences
    in competitions holding no awarded fixture at all. The comparison that counts is main's chain and
    this one composed into ONE query over identical inputs.
  - The Ligue 1 2025 deserved-vs-actual read still exists after the change. This is the cascade my
    first plan would have broken, so it is checked explicitly rather than inferred.
  - `games_expecting_team_stats` equals `season_games_played` for every team-season with no awarded
    or walkover match, and is exactly 1 lower for each such match. Measured.
  - A new test fails when the gate is reverted to `games_played`. Watched RED under that mutation —
    the mutation is the whole reason this column exists.
  - `dbt parse` exits 0 and SQLFluff passes under the templater CI uses, exit codes read BARE and
    UNREDIRECTED (a redirect makes SQLFluff exit 1 on success on this machine — see the evidence).
  - `check_description_hygiene.py`, `check_layer_contract.py`, `sync_metric_docs_blocks.py --check`
    and `pytest tests/` all pass.

decisions_taken: >
  ⭐ **THE CASING FIX GOES IN STAGING, and that is the layer contract, not a preference.** Staging is
  raw cleanup; normalising a provider field's casing is exactly that. Doing it downstream would leave
  every other consumer matching on raw strings.
  ⭐ **`upper()` YIELDS THE CANONICAL CODES, so this is a repair rather than a re-coding.**
  API-Football's own codes are uppercase (`CANC`, `ABD`, `WO`); the lowercase spellings are provider
  noise. The `accepted_values` list already enumerates the uppercase set, which is why it warns.
  ⭐ **GATE ON "COULD THIS MATCH HAVE HAD STATS", NOT "DID IT".** The existing gate conflates a
  missing stat line with an impossible one. `games_expecting_team_stats` separates them, and it is
  the minimum change that lets a result count without a phantom coverage gap.
  ⚠ NAME: `games_expecting_team_stats` follows the file's existing `games_played` /
  `games_with_team_stats` pattern. Flagged rather than escalated — it is an internal warehouse column
  no consumer reads, and the form follows a convention already set in the same file.
  THRESHOLD DECLARATIONS: no new mechanism, no new dependency, no recurring cost. No guard loosened —
  the coverage gate is made MORE precise, and one test is added to pin it.

decisions_reserved:
  - **The freshness guard.** `assert_fct_fixture_no_stale_live` uses a 3-hour wall-clock window
    against a once-daily ingest and has failed the nightly 9 of the last 29 nights. Diagnosed, a fix
    designed (measure from the last observation, not the wall clock — which clears 3 of today's 4
    flagged rows), NOT built here. Its own MR.
  - **Whether an interrupted match should ever count.** The Utrecht fixture that started this is
    `INT`, has a partial score, and counts nowhere — leaving FC Utrecht a game short of its league.
    `INT`/`ABD`/`PST`/`CANC` produced no result, so excluding them is correct; what is unresolved is
    that we cannot tell "not finished yet" from "never will be".
  - **The handover** still says `is_current_season` reached prod via the nightly; it was
    `data:build:main` on the !153 merge. Not fixed here.

done_when:
  - `.venv/Scripts/dbt.exe parse` exits 0.
  - SQLFluff passes on every changed model, exit code read bare and unredirected.
  - The compiled models run against prod read-only; old-vs-new compared team-season by team-season.
  - The new test measured on prod: green as built, RED under the reverted gate.
  - `python -m pytest tests/ -q` passes.

rounds_cap_override: >
  CPO, 2026-09-08: **"go ahead, add the not_null tests"**, given after round 3 was brought to him with
  the finding, my partial acceptance and the reason for the part I declined.
  ⚠ What the four rounds were spent on, because the cap exists to separate LOOPING from FIXING.
  Nothing was re-argued and no verdict was disputed:
    round 1  FAIL — a correctness bug: the sotd gate moved, its divisor did not (15 team-seasons)
    round 2  FAIL — the SAME class in finishing_efficiency_pct (up to +60%), plus missing descriptions
    round 3  FAIL — no third instance found; a missing not_null on the new denominator
    round 4  the two-line fix
  ⭐ Rounds 1 and 2 each found a real defect that would have shipped a wrong number to a live elite
  competition, and neither pointed at the other — their victims are disjoint, because Ligue 1's
  awarded match is a 0-0. Round 3's clean ratio sweep is what closed the class.

amendments:
  - **2026-09-06: `int_team_momentum_window.sql` added to `scope_paths`.** Not new work and not a
    wider decision — the model I had listed, `int_team_momentum__metrics.sql`, does not read the legs
    directly. It reads `int_team_momentum_window`, which projects columns EXPLICITLY rather than
    `select *`, so `is_awarded_result` reaches the form-window aggregation only if that model carries
    it through. Without the edit the new counter is silently always equal to `games_in_window` and the
    form-window half of this change does nothing.
    ⭐ Caught by the contract gate on the edit itself, not by me: I traced the season chain to its
    source and assumed the momentum chain had the same shape. Authority is the CPO's "same MR" on the
    enlarged gate change, which explicitly covered both surfaces — this is a link in the surface he
    approved, not an addition to it.
  - ⭐ **2026-09-07: the 0-0 "Technical loss" — my recommendation was WRONG and no exclusion rule was
    added.** Verifying on prod I found the one awarded fixture that is not 3-0: FC Nantes vs Toulouse
    FC, L1 2025 matchday 34, `AWD` with goals 0-0, which under this change credits BOTH teams a draw
    (their 23→24 and 44→45). I recommended excluding awarded matches that record no winner, arguing a
    technical loss must have one and that inventing a point in an elite league is exactly the silent
    wrong number the DQ rules exist to stop. **The CPO checked the actual match**: *"As simple Google
    search says it was a 0:0"*. It finished 0-0, both teams earned that point, and counting it as a
    draw is correct. Recorded in `escalations.log`, entry
    `2026-09-07 — feat/awarded-and-walkover-count-as-played — THE 0-0 TECHNICAL LOSS`.
    ⚠ The lesson is the logged `feedback_verify_real_world_identity`: I inferred what the data MUST
    say from what a status label MEANS, and never checked what happened. One search settled it, and
    the objection had already cost a design detour.
  - ⛔ **2026-09-07: a CORRECTNESS BUG I introduced, found by `analytics-engineer-reviewer`.**
    `int_team_season__metrics_cumulative.sql`'s `shots_on_goal_difference_per_match` had its GATE
    moved to `games_expecting_team_stats` and its DIVISOR left on `games_played`. Those were equal
    while the gate demanded full coverage; once awarded matches count as played they diverge by
    exactly the number of awarded matches, so a numerator spanning the stat-covered games was divided
    by one more game and quietly diluted.
    ⚠ **It is the worst possible one to get wrong**: this is the regression input to
    `int_team_season__deserved_vs_actual`, so a diluted value moves an entire league-season's
    deserved-points fit — including the Ligue 1 2025 case this MR is built around — rather than one
    cell. Nothing tested it, and the sibling `int_team_momentum__metrics` docstring states the very
    rule it broke ("we never divide a full-window numerator by a partial-window denominator").
    Fixed to `least(games_with_sot_stats, games_with_opp_sot_stats)` — the games BOTH sides of the
    subtraction cover, byte-identical to the old behaviour wherever the old gate passed.
    ⭐ Two-sided check of the other divisors: four still use `games_played`
    (`points_capture_pct`, `clean_sheets_pct`, `goals_per_match`, `goals_against_per_match`) and all
    four are CORRECT — they are scoreline metrics, and an awarded match really is a played game with
    a real scoreline. One moved, four stay.
  - ⛔ **2026-09-07: the test this contract PROMISED and I never wrote**, also from
    `analytics-engineer-reviewer`. `acceptance_criteria` says "A new test fails when the gate is
    reverted to `games_played`. Watched RED under that mutation — the mutation is the whole reason
    this column exists." No such test existed: a plain reversion at any of the 35 sites would have
    passed CI. Two singular tests added, one per surface, and `games_expecting_team_stats` is now
    projected out of `mart_team_momentum` because without it no test on that surface can tell a
    correct gate from a reverted one. Declaring a criterion and not meeting it is worse than not
    declaring it — the contract asserted coverage that did not exist.
  - ⛔ **2026-09-07, round 2: A SECOND CORRECTNESS BUG OF THE SAME CLASS, and the model documented
    the invariant I broke.** `analytics-engineer-reviewer` FAILed again on `finishing_efficiency_pct`
    — open-play goals over shots-on-target. The goal sums are UNGATED window totals and now include
    an awarded match's goals; `shots_on_goal` is a null-skipping sum that never can. So a 3-0
    technical win adds three real goals with no shot behind them. Measured by re-introducing it:

        LIBER 2025 team 154   correct 0.1724   bugged 0.2759     (+60%)
        LIBER 2026 team 127   correct 0.2241   bugged 0.2759
        BPL   2022 team 266   correct 0.2667   bugged 0.3
        WCQAS 2026 team 12    correct 0.4706   bugged 0.5

    ⛔ Both builders CARRIED A COMMENT stating the property my change invalidated — "finishing is NULL
    unless the window is fully shot-covered, so no coverage-restricted goals sum is needed" — and I
    changed what the gate compares against without reading either. The fix is the pattern sitting
    three lines below it in the same file: a coverage-restricted sum,
    `goals_open_play_in_sot_games`, exactly as `goals_against_in_save_games` already does for
    `saves_pct`. Both comments are now corrected rather than left contradicting the code.
    ⚠ Ligue 1 does NOT appear above, correctly: its awarded match is the 0-0, so there are no phantom
    goals to add. The two bugs have disjoint victims, which is why finding the first did not surface
    the second.
  - ⛔ **2026-09-07, round 2: the new columns had NO descriptions**, also from the reviewer.
    `dbt_project/docs/engineering_standards.md:82` requires a `description` on business-facing
    columns in core, intermediate and marts; `is_awarded_result` and `games_expecting_team_stats` had
    none, and `check_description_hygiene.py` polices model-level coverage only, so CI was silent.
    Four schema files added to `scope_paths` for it. ⚠ `scope-auditor` had checked this at round 1 and
    called it consistent with existing convention — which it was; the convention itself violates the
    standard. A precedent is not a permission.
  - ⭐ **2026-09-08, round 3 → 4: a `not_null` on the new denominator, and HALF the finding declined.**
    `analytics-engineer-reviewer`'s ratio sweep came back CLEAN — every rate in both builders and both
    consumers enumerated, no third instance of the same-window class, and the round-2 fixes confirmed
    including that the window-function references resolve to leg columns rather than sibling aliases.
    Its finding: `games_expecting_team_stats` carried no `not_null` test in the two intermediate
    schema files though its siblings and the mart copy do. Reasoning exact — every gate reads
    `x < games_expecting_team_stats`, and a NULL there is not FALSE; the comparison yields NULL, the
    CASE falls to its ELSE, and an UNGATED RATE is served instead of an honest NULL. Added.
    ⚠ Severity stated rather than inflated: it cannot be NULL today, since a `countif` / `sum(case …)`
    never is. The test guards a future change to how it is derived.
    ⛔ **The same finding asked for `not_null` on `goals_open_play_in_sot_games` too, and that was
    DECLINED.** It is a coverage-RESTRICTED sum: with no shots-on-target data it sums nothing and is
    legitimately NULL, which is what makes `finishing_efficiency_pct` null out honestly. Measured on
    prod over the 118,180 season-record rows: `games_expecting_team_stats` 0 nulls,
    `goals_open_play_in_sot_games` **18,301** — the requested test would have gone red on 15% of rows
    immediately. Its precedent sibling `goals_against_in_save_games` is untested for the same reason.
    A reviewer finding is accepted on its reasoning, not its authorship.
  - ⛔ **2026-09-08, round 4: I DOCUMENTED AND TESTED A COLUMN THE MODEL DOES NOT EMIT.**
    `analytics-engineer-reviewer` PASSed round 4 but named an asymmetry: `is_awarded_result` carried
    no `not_null` while the reasoning used to justify one on `games_expecting_team_stats` applied
    equally. Adding it revealed that `int_team_season_record` USES the flag internally — inside its
    `legs` CTE, to derive the counter — and never projects it. So the `is_awarded_result` entry I had
    added to `int_season_record.yml` at round 2 described a column that does not exist, and the new
    test would have failed only when it reached BigQuery. Entry removed; the test stands on the two
    models that genuinely emit it (`int_legs__team_match`, `int_team_momentum_window`), where it is
    measured non-null across all 118,180 legs.
    ⚠ **`dbt parse` is happy with a documented phantom column, and so is every offline gate.** The
    handover names a checker for exactly this class, `check_yml_vs_projection` — there is no such
    script in `scripts/` today, and `declare_missing_columns.py` covers only the reverse direction.
    Found because a verification query failed, not by any guard.
    ⭐ Raised with the CPO, who asked whether a consistent end-to-end test strategy exists at all.
    It does not — `engineering_standards.md` §3 states per-layer minimums but no rule for when a NULL
    is a defect versus the honest answer, no severity principle, and no projection check. Filed as
    **GitLab #109** at his instruction, deliberately NOT attempted here.
  - ⚠ **2026-09-07: the verification METHOD changed, not the scope.** `acceptance_criteria` now
    requires a CONTROLLED baseline rather than a diff against the live tables, because both live
    surfaces move on their own — the intermediate layer is stale whenever the nightly fails (it did,
    2026-09-07 05:11), and the momentum window filters on `current_date()`. Measured naively first,
    both produced large phantom differences in competitions holding no awarded fixture, and the
    numbers I reported from them were wrong. No path was added or removed.
