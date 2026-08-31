# Task contract — rename the four player goalkeeping metrics (step 4, MR 6)

objective: >
  **STEP 4 of the metric catalogue naming programme, MR 6 of seven.** The `goalkeeping` family of
  the player catalogue:

      saves                 →  saves_player
      save_pct              →  saves_player_pct
      goals_against         →  goals_against_player
      shots_on_goal_against →  shots_on_goal_against_player

  `!125` shipped `shooting`, `!127` `discipline`, `!128` `defending`, `!129` `passing`, `!130`
  `duels`. Remaining after this one: `goals` (10).

  ⛔⛔ **THE RULE IS UNCHANGED AND IS STILL THE WHOLE DESIGN: A REFERENCE FOLLOWS ITS SOURCE.**

  ⭐⭐ **THE LARGEST AND MOST ENTANGLED BATCH OF STEP 4: 676 tokens across 76 files and 50 distinct
  maximal tokens** (`!130`: 537 / 46 / 25). **210 renamed, 466 protected** — the first batch where
  protections outnumber renames more than two to one, because almost the whole team tree shares
  these stems.

  ⛔⛔ **ROUND 1 FAILED 5–0 ON TWO REAL DEFECTS, BOTH MINE, BOTH THE SAME CLASS: A SCOPE COARSER THAN
  THE ENTITY IT HAD TO RESOLVE.** Counts moved 217/459 → **210/466**. See `decisions_taken` §11.

refs: >
  **`.claude/task/escalations.log`, the block "THE METRIC CATALOGUE NAMING PROGRAMME"**, its table
  "⛔ PLAYER, 35 REMAINING" — all four renames appear in it verbatim.
  ⭐ Cited by CONTENT, never by line number and never a plan file.
  ⭐ `saves_player_pct` is **RULING 5's shape** — `_player` before a trailing `_pct`.
  ⚠ Group membership verified FROM THE SEED: `player`/`goalkeeping` is **5 rows** — these four plus
  `saves_per90`, which does not change because `_per90` already means player.

  ⭐ **TWO STANDING CPO RULINGS, applied unchanged:** **"re-point them"** (45 references here, **18
  of them TEAM-side**) and **"yes"** (provider and per-match surfaces keep the provider name — ten
  provider `.sql` files excluded, 31 tokens).

  ⚠ **NO NEW CPO RULING WAS NEEDED OR TAKEN.** Every target name is already in the record. Two FORM
  decisions were taken under "the transformation layer decides the FORM, the CPO decides the NAME"
  and are recorded in `decisions_taken` §5 and §6.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/macros/player_benchmark_metrics.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_competition_benchmarks.sql
  - dbt_project/models/4_intermediate/shared/int_player_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_player_momentum.sql
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/mart_player_season_record.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_metric_direction_lower_is_better_agree.sql
  - docs/wireframes/01_fixture_page.md
  - docs/wireframes/03_player_profile.md
  - docs/wireframes/10_home.md
  - docs/wireframes/12_player_stats.md
  - docs/wireframes/99_gaps_register.md
  - docs/wireframes/metrics_display.md
  - scripts/sync_metric_docs_blocks.py
  - scripts/declare_missing_columns.py
  - site_v2/src/components/fixture/PlayerRow.astro
  - site_v2/src/lib/types.ts
  - tests/test_declare_missing_columns.py
  - tests/test_sync_metric_docs_blocks.py
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/active_work.md

# ⚠ This list is the EXACT changed set — reconciled against `git diff --name-only` in both
# directions. The 34 swept files come from the classifier's DRY RUN (files with zero renames are
# never opened); `metric_columns.md` is regenerated; four files are rewritten BY HAND (see
# decisions_taken §6); six are review paperwork.
#
# ⭐⭐ NOTE THE TWO `site_v2/` ENTRIES, AND THAT THEY ARE NOT THE ONES `!129` HAD. This is the first
# batch to change a RENDERING COMPONENT. See decisions_taken §1 — it is also the one part of this
# MR that NO automated gate covers.
#
# ⚠ SWEPT BUT NOT CHANGED — 42 files the classifier read and decided, every token PROTECTED:
#  · the entire TEAM tree, including seven models no batch has touched before
#    (mart_head_to_head, int_team_profile__streaks, mart_team_fixtures, mart_team_season,
#    int_team_momentum_window, mart_team_momentum_window, mart_matchday_insights)
#  · ⭐ TEN FRONTEND FILES: i18n/strings.ts, lib/metricRows.ts, both page specs, and six components
#    (HeadToHead, RecentMatch, DeservedHero, MetricSeasonRow, TeamFixtureRow, YearOverYear).
#    `metrics.saves_pct.label` and `metrics.goals_against_per_match.label` are BOTH among the 12
#    rows that actually render.
#  · ⭐ FOUR FILES WHERE `saves` IS AN ORDINARY ENGLISH VERB — see decisions_taken §4.
#
# ⚠ NOT IN SCOPE, each for a stated reason:
#  · `.claude/task/review_input.patch` — regenerated review paperwork, hash-excluded by design.
#  · `site_v2/src/data/**` and `site/**` — the committed sample and the frozen MVP tree.
#  · the ten provider `.sql` files (31 tokens) — the CPO's "yes" ruling.
#  · `ingestion/api_football/bigquery.py` — its one token is the English verb, and ingestion is
#    outside the rename's remit entirely.

protected_override: >
  none. No guard, threshold, schedule or exemption is loosened. ⚠ `fct_fixture_player_stats` is the
  only `incremental` model carrying any of these names and its columns are NOT renamed — only its
  `doc()` pointers move — so no `--full-refresh` is implied.

impact_map: >
  ⭐ **RUN ON THIS BRANCH BEFORE THE FIRST EDIT, AND PASTED VERBATIM.**

      $ dbt ls --resource-type model --select int_player_season__metrics+ \
          int_player_club_season__metrics+ int_player_competition_benchmarks+ \
          int_player_momentum__metrics+ int_player_season_position__metrics+ \
          int_player_season_record+ mart_leaderboards+ mart_player_momentum+ \
          mart_player_profile+ mart_player_season_record+

      football_data_pipeline.4_intermediate.domestic_league.team_season.int_player_season__metrics
      football_data_pipeline.4_intermediate.shared.int_player_club_season__metrics
      football_data_pipeline.4_intermediate.shared.int_player_competition_benchmarks
      football_data_pipeline.4_intermediate.shared.int_player_momentum__metrics
      football_data_pipeline.4_intermediate.shared.int_player_profile__yoy
      football_data_pipeline.4_intermediate.shared.int_player_season_position__metrics
      football_data_pipeline.4_intermediate.shared.int_player_season_record
      football_data_pipeline.5_marts.shared.mart_leaderboards
      football_data_pipeline.5_marts.shared.mart_player_career
      football_data_pipeline.5_marts.shared.mart_player_competition_benchmarks
      football_data_pipeline.5_marts.shared.mart_player_momentum
      football_data_pipeline.5_marts.shared.mart_player_profile
      football_data_pipeline.5_marts.shared.mart_player_season_record

  **13 models.** Ten change by direct SQL edit (the nine player models above plus
  `int_player_competition_benchmarks`, whose only token is a comment); `mart_player_competition_benchmarks`
  changes only through `player_benchmark_metrics()`. ⚠ **TWO ARE AN OVER-COUNT**:
  `int_player_profile__yoy` and `mart_player_career` carry **0** of the four names — re-verified by
  grep for this batch, not carried from `!130`.

  Downstream of the marts: `scripts/export_site_data.py` (1 literal) and
  `tests/test_export_site_data.py` (1 fixture literal) — and, for the first time,
  **two `site_v2/src/` source files**.

acceptance_criteria:
  - ⛔⛔ **THE `PlayerRow.astro` → `types.ts` → `mart_player_momentum` CHAIN IS VERIFIED BY READING, BECAUSE NOTHING ELSE COVERS IT.** Every link is confirmed by hand: the mart emits the renamed column, `shape_top_players` passes it through a DROP-list so the payload key follows automatically, `TopPlayer` declares it, and the component reads it. This is stated as the one unguarded part of the MR, not as a passing check.
  - ⛔ **CRITERION 1 IS A CONFIRMATION, NOT A DISCRIMINATING CHECK** — the `!129`/`!130` finding, declared up front rather than discovered in review. The GK line renders on **0 of 67** built pages, so the dist comparison cannot catch a mis-scope in `PlayerRow.astro`. What the dist comparison does prove is that the twelve rendered rows are unchanged, including the two protected team labels `"% Save percentage"` and `"Ø Goals against"`.
  - ⭐ **Exactly two `site_v2/` files change and exactly four tokens move in them**; the other ten swept frontend files are byte-identical. No name is HALF-renamed — each new name appears everywhere the old one did, and every surviving old name is a provider read, a TEAM column, or an English word.
  - `sync_metric_docs_blocks.py --check` and `check_description_hygiene.py` both pass AND are each watched going RED.
  - Every dotted AND bare column reference resolves against the relation it actually reads; the yml-vs-projection check reports zero mismatches **and is mutation-tested in BOTH its strong and its known-weak form**, so the bound found on `!130` is re-stated rather than re-discovered.
  - ⛔ The three 22-name TEAM `accepted_values` lists are byte-identical, each keeping all **three** of its hits (`goals_against_per_match`, `shots_on_goal_against_per_match`, `saves_pct`).

decisions_taken: >
  All four names come from the record, verbatim. No name in this batch was proposed by me.

  ⭐⭐ **ONE QUESTION, ASKED OF EVERY OCCURRENCE: DID THE RELATION THIS READS FROM RENAME THE
  COLUMN?** 676 tokens classified once, each decision printed with its resolved entity —
  **217 renamed, 459 protected** across 76 files. 2,228 tokens repo-wide: 1,521 untouched (the
  sample, `.claude/**`, `site/**`, `docs/audits/**`, the regenerated `metric_columns.md`), 31 in
  provider `.sql`.

  ⭐⭐ **§1. THE FIRST RENDERING-COMPONENT CHANGE OF STEP 4 — AND THE ONE PART OF THIS MR NO GATE
  COVERS.** `site_v2/src/components/fixture/PlayerRow.astro:37` renders the goalkeeper line:

      <b>{player.saves ?? 0}</b> {t(lang, "saves")} · <b>{percent(player.save_pct, lang)}</b>

  **Three tokens, two decisions, one line.** `player.saves` / `player.save_pct` are payload fields
  and move; `t(lang, "saves")` is a UI WORD KEY (`strings.ts` `saves: "saves" / "Paraden" /
  "torjuntaa"`) and stays. Nothing in this programme has put a renaming and a protected token on the
  same line before, so the decision is made by ROLE — the characters preceding the token — never by
  the file.

  ⛔ **Everything that would normally catch a mistake here is absent, and each was checked rather
  than assumed:**
    · `shape_top_players` uses a **DROP-list** (`_TOPPLAYER_DROP`), not a keep-list, so the renamed
      mart column reaches the payload with **no export edit** — and no export test notices.
    · `site_v2/package.json` has **NO typecheck**: `build` is bare `astro build`, `prebuild` is
      `npm test && check-page-specs.mjs`. A stale `player.saves` against a renamed `TopPlayer`
      compiles silently.
    · **No test anywhere references `PlayerRow`, `TopPlayer` or `top_players`.**
    · **The GK line renders on 0 of 67 built pages** — measured over `dist` with comments stripped.
  A mis-scope would therefore ship a goalkeeper line reading `0` and a blank percentage with every
  gate green. The chain is verified by reading it end to end, and that is said plainly rather than
  dressed up as a passing check.

  ⭐ `lib/types.ts` moves **2 of its 11** occurrences — `TopPlayer.saves` / `TopPlayer.save_pct`.
  The other nine are `FormMatch`, `RecentMeeting`, `HeadToHead`, `TeamFixture`, `TeamSeason`: team
  scorelines and team metrics. Resolved by the enclosing `export interface`, the TypeScript analogue
  of `yml_model_at()`; an unlisted interface ABORTS.

  ⭐⭐ **§2. TWO BLOCK-PAIR COLLAPSES AT ONCE — SIMULATED, NOT PREDICTED.** `_blocks()` splits a
  metric into `__team`/`__player` only where its rows disagree. **Both** `saves` and `goals_against`
  stop being ambiguous, so both pairs collapse. Run against the real generator with the renamed seed
  held in memory, before any code:

      172 → 167 blocks   (11 removed, 6 added)
      REMOVED  saves__player · saves__team · goals_against__player · goals_against__team ·
               save_pct · shots_on_goal_against ·
               goals_against_{this_season,prev_season,delta_yoy,sum_season}__player ·
               last_meeting_goals_against__player
      ADDED    saves · saves_player · saves_player_pct · goals_against ·
               goals_against_player · shots_on_goal_against_player

    · **18 TEAM-side `doc()` re-points** (`saves__team` 6 + `goals_against__team` 12) caused by a
      player rename, against five on `!130`. No sweep finds these from the player side.
    · **Five deleted orphans, each verified at 0 references**, including
      `last_meeting_goals_against__player` — a PREFIX-affix orphan, a shape `!130` did not have.
    · **45 `doc()` references re-point in total.**

  ⭐ **§3. THE SEED'S TWO ENTITIES DISAGREE ON THE PROVIDER COLUMN, AND BOTH STILL PROTECT.** Team
  `saves` computes `sum(goalkeeper_saves)`; player `saves` computes `sum(saves)`. Player
  `shots_on_goal_against` is `sum(saves + goals_against)` while team
  `shots_on_goal_against_per_match` is `sum(opponent_shots_on_goal)`. Different provider columns, same
  rule: all 16 seed formula occurrences protect and only the four `metric_id`s move.
  `player_benchmark_metrics.sql` is the mirror case and its `num`/`den` DO move.

  ⭐⭐ **§4. `saves` IS AN ORDINARY ENGLISH WORD — a trap class no previous stem had.** All PROTECT,
  and each is a printed decision rather than an invisible exclusion:

      ingestion/api_football/bigquery.py      "the extra call costs 13 KB and saves gigabytes"
      dbt_project/docs/engineering_standards.md   "what the macro saves"
      tests/test_governance_hooks.py          "`changes:` filter saves neither"
      docs/ui_design_brief.md  ×3             "GK: saves, goals conceded, save %"  (plain prose)

  And `goals_saves` is the PROVIDER's own field name for keeper saves, normalised to the leg column
  `saves` — protected, and it sits beside `save_pct`, which moves.

  ⭐ **§5. A FORM DECISION: `player_profile_saves_lte_faced` renames with its metric**, to
  `player_profile_saves_player_lte_faced`, and its expression `saves <= shots_on_goal_against` moves
  with it. A test name embedding a metric id has moved in every batch since `!125`; this is the
  first that is not an `*_in_range` name, which is why it is recorded rather than assumed.

  ⭐ **§6. A SECOND FORM DECISION, AND IT IS THE `!130` §3 PROBLEM AT SCALE.** Four files use
  `goals_against` as the worked EXAMPLE of a dual-entity id, and the rename falsifies all four:
  `scripts/sync_metric_docs_blocks.py`, `scripts/declare_missing_columns.py`,
  `tests/test_declare_missing_columns.py`, `tests/test_sync_metric_docs_blocks.py`.
  ⚠ The generator's is the sharpest: `_derived()`'s docstring argues the entity suffix is mandatory
  BECAUSE "the catalogue holds exactly one [row for `goals_against`], for a PLAYER … Every column of
  that name lives on a TEAM model." **After this MR the single row is the TEAM's**, so the entity
  matches and the specific hazard that paragraph describes is gone.
  **Decision: rewrite each to state the RULE without asserting a now-false fact, marking the example
  historical.** No name is chosen and no mechanism changes. ⛔ **NOTHING IS DELETED** — `_derived()`
  still suffixes by entity and the guard still protects a future collision. The synthetic
  `__team`/`__player` FIXTURES in those tests also stay: they exercise a mechanism that still exists.
  The classifier PROTECTS all 13 tokens in these files and prints "prose the rename FALSIFIES", so
  the rewrite is a visible separate edit rather than a substitution hidden in a 217-token diff.

  ⭐ **§7. A DEFECT IN MY OWN TOOL, FOUND BY READING THE PRINTED REASONS RATHER THAN THE COUNTS.**
  `mart_player_season_record.sql:13` says, inside a `{# … #}` docstring, "…computed here via
  safe_divide. save_pct is only meaningful for goalkeepers." That `.` is SENTENCE PUNCTUATION, but
  `sql_shape()` saw `safe_divide.` before the token and reported "dotted", labelling the occurrence
  **"RENAME read — safe_divide. reads a metric relation that renamed it"**. The DECISION was right;
  the REASON was a lie — the exact class `!127` fixed for bare reads and `!129` for aliases. The
  comment test already existed but lived INSIDE `bare_decision()`, reachable only after `sql_shape`
  returned "bare", so prose could never reach it. Hoisted ahead of shape analysis; the jinja-comment
  count went 11 → 13 and the false reason is gone.

  ⭐ **§8. #96 INVERTS FROM `!130`.** All six `accepted_values` lists contain a swept token again,
  but only **3 entries move across 3 lists** (`save_pct` in the 14-name board list and in both
  18-name player lists), while the three 22-name TEAM lists carry **three** protected hits each
  (`goals_against_per_match`, `shots_on_goal_against_per_match`, `saves_pct`) — up from two.

  ⭐ **§9. EIGHT SINGULAR TESTS, SPLIT FOUR AND FOUR.** Player rename: `std_player_`,
  `player_profile_`, `mart_leaderboards_save_pct_in_range`, plus `player_profile_saves_lte_faced`.
  Team protect: `momentum_team_`, `std_team_`, `mmi_home_`, `mmi_away_saves_pct_in_range`.

  ⛔⛔ **§10. A PREDICTION I WROTE INTO THIS CONTRACT AND THEN DISPROVED — AND THE REASON MATTERS
  MORE THAN THE NUMBER.** I predicted the hygiene gate's "means more than one thing" list would drop
  **4 → 3** as `goals_against` became unambiguous. Measured: it **stays at 4**, and the entry merely
  changes shape:

      before   goals_against: goals_against__player, goals_against__team
      after    goals_against: goals_against, goals_against_player

  `_ambiguous_names()` groups by COLUMN NAME and reports any name whose columns reference more than
  one block. Columns literally named `goals_against` still split two ways after the rename — the
  TEAM surfaces point at `goals_against`, while the PLAYER PROVIDER surfaces
  (`fct_fixture_player_stats`, `int_legs__player_match`, `mart_player_fixture_stats`) keep the
  provider column NAME under the "yes" ruling but had their `doc()` re-pointed to
  `goals_against_player` under the "re-point them" ruling.

  ⭐ **THE TWO STANDING RULINGS INTERACT, AND THE CONSEQUENCE IS GENERAL: a metric rename can never
  disambiguate a column name that the PROVIDER also uses.** `duels_won_pct` resolved on `!130` only
  because it is a computed rate with no provider column of that name; `goals_against` and `saves`
  are provider fields, so they cannot. That corrects an expectation `!130`'s own contract recorded —
  that the naming programme frees some of #87's 49 blank columns. **It does not: the blank count is
  unchanged at 49**, and #87 is untouched by this programme rather than partly solved by it.

  ⛔⛔ **§11. ROUND 1 FAILED 5–0. TWO REAL DEFECTS, BOTH MINE, AND BOTH THE SAME UNDERLYING MISTAKE:
  A SCOPE COARSER THAN THE ENTITY IT HAD TO RESOLVE.** All five reviewers returned FAIL; four found
  the first defect independently and three the second.

  **(a) THE TEAM SCORELINE PAIR, 6 SITES — and the worst of them would have shipped a silent data
  loss.** `goals_for` / `goals_against` is the TEAM per-fixture scoreline from
  `int_legs__team_match`, reaching `mart_team_fixtures`, `mart_head_to_head` and
  `mart_team_momentum_window` — none of which this MR renames. I scoped `export_site_data.py`,
  `tests/test_export_site_data.py`, `01_fixture_page.md` and `03_player_profile.md` as PLAYER files,
  so all six occurrences were renamed.
  `export_site_data.py:166`'s `_TEAM_FIXTURE_FIELDS` is a KEEP-list applied to `mart_team_fixtures`
  rows via `{k: row.get(k) …}`. Renamed, it would have emitted `goals_against_player: null` for every
  team's `next_fixture` and every `recent_results` entry, **forever, with no crash**, while
  `TeamFixtureRow.astro:23` still read `fx.goals_against` — a field the export had stopped emitting.
  ⚠ **And the test was mutated to match the bug**: `test_export_site_data.py:367`'s fixture dict key
  was renamed in lockstep, so `pytest` stayed green. That is the "verify the test fails" trap in its
  purest form — the sweep edited the test and the code together, so the test could not disagree.
  ⭐ **THE FIX IS A FACT ABOUT THE DOMAIN, NOT AN EXEMPTION LIST.** There is no player `goals_for` —
  a player does not score or concede "for" in the scoreline sense — so wherever the pair appears,
  `goals_against` is the team field. Implemented as `in_team_scoreline()`, scoped to the PARAGRAPH in
  markdown and the enclosing statement elsewhere (a line-scoped test on a construct that wraps is how
  `!128` round 1 failed). Measured against the round-1 diff: it separates **all 6 wrong renames from
  all 60 correct ones, exactly.**
  ⚠ A consequence worth recording: once the six were protected, `export_site_data.py` and
  `tests/test_export_site_data.py` dropped to ZERO renames — so the no-op-write guard never reopened
  them and they kept their round-1 text on disk. **A file that falls to zero renames must be restored
  from base explicitly.** Both were, and both left `scope_paths`.

  **(b) THE SEED'S `interpretation` COLUMN — a blocklist that silently swept everything not on it.**
  `SEED_REFERENCE_FIELDS` listed five columns to PROTECT; the seed has fifteen. `interpretation` was
  not among them, so `saves_per90`'s prose became "More **saves_player** per 90 is better…" — an
  internal identifier injected into reader-facing text (`seeds/schema.yml` calls it the seed of the
  site's good/bad reading and auto-narrative), on a row this contract states three times does not
  change.
  ⭐ **THE FIX IS THE SHAPE, NOT THE ENTRY.** Adding `interpretation` would have left the next added
  column exposed identically. It is now an ALLOWLIST — `SEED_RENAMEABLE_FIELDS = {"metric_id"}` — so
  a new seed column is protected by default. Verified: **zero non-`metric_id` seed fields differ from
  base**, across every row.

  ⚠ Both defects were invisible to every gate: `dbt parse`, the hygiene gate, the yml-vs-projection
  check, the resolver, `pytest`, `npm test` and the two site builds were all green with both defects
  present — the dist comparison because it builds from the frozen sample, which this MR correctly
  does not touch. **The reviewers were the only thing between these and production.**

  ⚠ Verified alongside it, mechanically: all **45** `doc()` re-points preserve their entity —
  `saves__team`→`saves` ×6, `saves__player`→`saves_player` ×12, `goals_against__team`→`goals_against`
  ×12, `goals_against__player`→`goals_against_player` ×8, `save_pct`→`saves_player_pct` ×6,
  `shots_on_goal_against`→`shots_on_goal_against_player` ×1. **Zero crossovers.**

decisions_reserved:
  - none NEW on naming. Every target name is in the record; the two judgements taken (§5, §6) choose
    no name.
  - ⭐ **CARRIED: the column-reference resolver as a committed CI gate.** `!129` argued against it;
    `!130` added that it covers dotted references only. Still not proposed.
  - ⭐ **CARRIED from `!130`: the `__team`/`__player` block split loses its last live instance at the
    end of step 4.** This MR removes two of the three remaining dual-entity ids; only `goals`,
    `goals_open_play` and `goals_penalty` are left, and MR 7 takes them. Nothing is proposed and
    nothing is removed — but §6 shows the cost is now concrete: four files documented the mechanism
    with an example that no longer exists.
  - ⚠ CARRIED FORWARD: **#96**, ten reproductions.
  - ⚠ CARRIED FORWARD: `_LEADERBOARD_METRICS` / `_LB_KEEP` pinned by NO test. ⭐ This MR shows the
    OTHER export path is unpinned too: `shape_top_players`' DROP-list means `TopPlayer` fields reach
    the frontend with no test between the mart and the component.
  - ⚠ CARRIED FORWARD: **#99**, the export's literal `goals`/`assists` read keys — MR 7's.
  - ⚠ CARRIED FORWARD: **#87** — the "means more than one thing" list drops 4 → 3 here. Filling the
    freed columns is #87 and is deliberately NOT done.
  - ⚠ CARRIED FORWARD: **#98**; the doc-block inheritance trap.

done_when:
  - `sync_metric_docs_blocks.py --check` passes after regeneration at **167** blocks, reconciled term by term against the simulation in `decisions_taken` §2 — 11 removed, 6 added, the −5 being the deleted `goals_against_*__player` orphans.
  - `check_description_hygiene.py`, `check_layer_contract.py` pass, `dbt parse` is clean, and the description count is measured against base (**1604 both sides** — the "re-point them" ruling, a seventh measurement). ⛔ **CORRECTED AFTER MEASUREMENT: the "means more than one thing" list STAYS AT 4.** I predicted 4 → 3 and that was wrong — see `decisions_taken` §10.
  - The `PlayerRow.astro` → `types.ts` → `mart_player_momentum` chain is read end to end and the absence of any gate over it is stated in the evidence.
  - The resolver reports zero broken references; the yml-vs-projection check reports zero mismatches and is mutation-tested in both its strong and its known-weak form.
  - `python -m pytest -q` matches the `9ee88a4` baseline.
  - `sqlfluff lint` on every changed model, FROM THE REPO ROOT, UNPIPED, proved byte-identical to a re-lint of the stashed base.
  - `npm test` green, the mutations watched going RED, and the site built TWICE at 12 rows / 7 headings in all three locales with `"% Save percentage"` and `"Ø Goals against"` intact.
  - All six `accepted_values` lists read by eye, compared base-vs-branch **in file order with a length assertion**: 3 entries move, the three team lists byte-identical.
  - ⚠ `check_ui_i18n_metrics.py` is run because it is a real CI gate, but it is **NOT evidence** — it validates only the frozen `site/**` tree this branch never touches.
