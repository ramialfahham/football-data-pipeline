# Task contract — rename the five player discipline metrics (step 4, MR 2)

objective: >
  **STEP 4 of the metric catalogue naming programme, MR 2 of seven.** The `discipline` family of the
  player catalogue — the seed holds exactly five `entity=player, metric_group=discipline` rows and
  these are all five:

      cards_yellow       →  cards_yellow_player
      cards_red          →  cards_red_player
      cards_total        →  cards_player
      offsides           →  offsides_player
      penalty_committed  →  penalty_committed_player          (PLAYER entity only)

  Step 3 closed with `!123` (twelve team renames, merged, live in prod). Step 4 is the other half —
  35 player renames split into seven MRs on the seed's own `metric_group`, the same key step 3 used.
  `!125` shipped `shooting`. Remaining after this one: `defending` (5) · `passing` (5) · `duels` (6)
  · `goalkeeping` (4) · `goals` (7).

  ⛔⛔ **THE RULE THIS BATCH TURNS ON, inherited from `!125` where it cost three rounds and two full
  reverts: A REFERENCE FOLLOWS ITS SOURCE.** Shape only tells you WHAT is being read; the SOURCE
  decides whether it moves. All five names are also PROVIDER STAT WORDS — `cards_yellow` is the same
  identifier from `stg_apif__fixture_players.sql` through base, core and `int_legs__player_match` —
  so one word does two jobs and a rename must move only one of them.

  ⭐⭐ **AND THIS BATCH IS THE SHARPEST INSTANCE OF IT SO FAR: THREE `sum(X) … as X` SELF-ALIASING
  SITES, WITH TWO OPPOSITE ANSWERS.** Identical shape, different source:

      int_player_club_season__metrics.sql:135-139   ← per_fixture ← fct_fixture_player_stats
                                                      PROVIDER → the inner read is PROTECTED
      int_player_season_record.sql:63-67            ← player_legs = ref('int_legs__player_match')
                                                      PROVIDER → the inner read is PROTECTED
      int_player_season__metrics.sql:58-62          ← club_season = ref('int_player_club_season__metrics')
                                                      A METRIC RELATION THIS MR RENAMES → IT MOVES

  The third is the exact shape four reviewers found independently at `!125` round 2. Both answers
  are visible side by side in the code `!125` landed, which is why they are quoted here rather than
  argued: `int_player_season_record.sql:50` reads `sum(shots_total) over w as shots_player` (inner
  read KEPT), while `int_player_season__metrics.sql:45` reads `sum(shots_player) as shots_player`
  (both halves MOVED).

refs: >
  **`.claude/task/escalations.log`, the block "THE METRIC CATALOGUE NAMING PROGRAMME"**, its table
  "⛔ PLAYER, 35 REMAINING" — all five renames appear in it verbatim, as
  `penalty_committed → penalty_committed_player`, `cards_yellow → cards_yellow_player`,
  `cards_red → cards_red_player`, `cards_total → cards_player`, `offsides → offsides_player`.
  ⭐ Cited by CONTENT, never by line number and never a plan file — three MRs in this programme were
  FAILed for exactly that.
  ⭐ The shape is **RULING 5**, verbatim: "suffix only for the player metrics", with its form
  "duels_won_player_pct not duels_won_pct_player". Not load-bearing here: none of the five takes a
  trailing `_pct`. All five satisfy **THE RULED PATTERN**, `noun [_qualifier] [_against] [_player]
  [_form]`, cited up front because batch D burned three rounds hunting a per-name quote the pattern
  had already settled.

  ⭐ **TWO CPO RULINGS GOVERN THIS MR, both quoted with what they answered:**
  1. **"re-point them"** — doc references on columns that BORROW a player metric's block are
     re-pointed, not blanked. He was shown: that the published text is entity-neutral and stays
     correct while the block NAME is internal jinja no consumer sees; that blanking is permitted by
     `check_description_hygiene.py:322` but deletes correct published descriptions; and a third
     option (adding TEAM catalogue rows) named as HIS and not taken. **48 doc references move here.**
     Measured proof it was the right call: the description count holds at **1604**, exactly the base.
  2. **"yes"**, answering whether the per-match / provider surfaces keep the provider name and are
     not renamed at all, because they carry raw per-match stats rather than metrics. So
     `mart_player_match_log`, `mart_player_fixture_stats`, `mart_team_fixture_stats`, `int_legs__*`,
     `3_core`, `2_base` and `1_staging` are **out of the edit set entirely** — 38 occurrences in
     nine `.sql` files, none touched.

  ⚠ Two of the borrowing columns are TEAM columns: `fct_fixture_team_stats.offsides` and
  `mart_team_fixture_stats.offsides`. `offsides` is one of the seven blocks the ruling enumerated.

  Branched from main **`3e5b25b`**, clean tree. `glab mr list`: no open merge requests.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_player_momentum.sql
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/mart_player_season_record.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - docs/wireframes/01_fixture_page.md
  - docs/wireframes/03_player_profile.md
  - docs/wireframes/10_home.md
  - docs/wireframes/99_gaps_register.md
  - docs/wireframes/metrics_display.md
  - scripts/export_site_data.py
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/active_work.md

# ⚠ This list is the EXACT changed set — reconciled against `git diff --name-only` in both
# directions, nothing extra either way.
#
# ⚠ NOT IN SCOPE, each for a stated reason:
#  · the PROVIDER / per-match surfaces named in `refs` — the CPO's "yes". `core.yml` and
#    `int_legs.yml` ARE in scope, but ONLY to re-point a `doc()` reference; no column on them moves,
#    and neither does any column on `mart_player_fixture_stats`, `mart_player_match_log` or
#    `mart_team_fixture_stats` in `shared.yml`.
#  · site_v2/src/** — see the built-page prediction in `decisions_taken`. The keys DO appear in the
#    committed fixture sample, and that is the declared transient; NO `.astro`, `.ts` or spec file
#    references any of the five. Verified by grep over `site_v2/src` excluding `src/data/`.
#  · site/** — the frozen MVP tree contains none of the five names at all.
#  · `docs/ui_design_brief.md` — two PROSE mentions of the English word "offsides" in sentences whose
#    every sibling is deliberately not an identifier ("cards (Y/R)", "penalties (won/committed)").
#  · `dbt_project/tests/assert_metric_direction_lower_is_better_agree.sql` — a `{# #}` comment
#    recording a DATED fact about the catalogue as it stood on 2026-07-21.
#  Both of the last two are declared judgement calls, argued in `decisions_taken`.

protected_override: >
  none required. No file in scope_paths is a protected command-class file.

impact_map: >
  writers: the five metrics are computed in `int_player_club_season__metrics` (per-club atoms),
    re-summed in `int_player_season__metrics` (which also derives `cards_player` as
    `cards_yellow_player + cards_red_player`), and independently windowed in
    `int_player_momentum__metrics` and `int_player_season_record`. `mart_player_profile`,
    `mart_leaderboards`, `mart_player_momentum` and `mart_player_season_record` consume them.

  downstream: `dbt ls --select int_player_club_season__metrics+ int_player_season__metrics+
    int_player_momentum__metrics+ int_player_season_record+ --resource-type model`, run on this
    branch BEFORE the first edit:
      4_intermediate.shared.int_player_club_season__metrics
      4_intermediate.shared.int_player_momentum__metrics
      4_intermediate.shared.int_player_profile__yoy
      4_intermediate.domestic_league.team_season.int_player_season__metrics
      4_intermediate.shared.int_player_season_record
      5_marts.shared.mart_leaderboards
      5_marts.shared.mart_player_career
      5_marts.shared.mart_player_momentum
      5_marts.shared.mart_player_profile
      5_marts.shared.mart_player_season_record
    ⚠ **THE LINEAGE IS EVIDENCE, NOT THE FILE LIST.** It over-counts — `int_player_profile__yoy` and
    `mart_player_career` carry none of the five names (no yoy or career form of a discipline metric
    exists) — and it under-counts: every yml, `core.yml`, `int_legs.yml`, five wireframes and
    `export_site_data.py` are edited and absent from it.

  layer_rules: `check_layer_contract.py`. Coupled guards:
      · ⭐ **`shared.yml:1756` — the 14-name `mart_leaderboards.metric_key` `accepted_values` list.
        `cards_total` is IN it, so the list moves with the mart or `data:build:mr` goes red.** This
        is the ONLY one of the six metric-key lists that changes: the three 22-name TEAM lists
        (`int_competition_benchmarks.yml:27,66`, `shared.yml:2080`) and the two 18-name PLAYER
        benchmark lists (`int_competition_benchmarks.yml:105`, `shared.yml:2186`) contain none of
        the five, checked name by name.
      · no `*_in_range` singular test names any of the five — the discipline metrics have no range
        test, unlike `finishing_efficiency` in `!125`.
    ⛔ #96: no offline gate enforces those lists — SIX consecutive reproductions. Checked by eye.

  deploy_order: none needed. No touched model is incremental.

  blast_radius: five metric columns rename across the player club-season, season, momentum, season-
    record and mart models; one `metric_key` VALUE changes on the leaderboard boards
    (`cards_total` → `cards_player`) together with its `accepted_values` entry and the export's two
    literal key tuples. **No number changes** — every formula, floor and null policy is
    byte-identical, and the catalogue's own formulas still read the leg columns they always did.

acceptance_criteria:
  - Every player metric name the BUILT site renders reads the same words after the rename as before, in all three locales, measured structurally from the markup of the pages under `site_v2/dist/` and compared element-for-element against the same pages built from the base commit — never by substring.
  - No `site_v2/src` source file outside the generated sample, and no built page, contains any of the five names as a standalone key, by whole-token grep; and no name is HALF-renamed — each new name appears everywhere the old one did in the models, ymls, seed, export and wireframes that this MR moves.
  - `sync_metric_docs_blocks.py --check` and `check_description_hygiene.py` both pass AND are each watched going RED — the first on a stale `metric_id` in the seed, the second on a deliberately dangling `doc()`. These replace the `npm test` label guard used for MRs B–F, which reaches NONE of the 35 player metrics: measured, `asked = rowKeys ∪ heroKeys` is 17 + 3 keys and every one is a team `metrics.*` key.
  - ⭐ Every dotted AND bare column reference to a renamed name resolves against the relation it actually reads, checked statically and watched going RED — on this batch, against BOTH shapes, because this batch contains both a bare read that must move and two that must not.

decisions_taken: >
  All five names come from the record; both governing rulings are quoted with what they answered in
  `refs`. The four acceptance criteria are carried from `!125`, whose criterion 3 replaced the
  expired B–F guard; criterion 4 is strengthened, because this batch exercises both bare shapes.

  ⭐⭐ **ONE QUESTION, ASKED OF EVERY OCCURRENCE: DID THE RELATION THIS READS FROM RENAME THE
  COLUMN?** 216 tokens were classified once and the decision printed for each — **169 renamed, 47
  protected**, reconciling exactly against `git grep` in both directions:
    · **alias** (`… as X`) — the metric being written. Always moves. 17 sites.
    · **dotted** (`s.cards_yellow`) — follows its source. Every one enumerated and its alias
      resolved to a relation: **19 read a metric relation and move** (`mart_player_profile` `a`,
      `mart_player_season_record` `sf`, `mart_player_momentum` `b`, `mart_leaderboards` `s`),
      **8 read a provider relation and do not** (`int_player_club_season__metrics` `s` =
      `fct_fixture_player_stats`, `int_player_momentum__metrics` `p` = `int_legs__player_match`).
    · **bare** — follows its source too. 22 are this model's own column and move; 4 are the inner
      read of a self-aliasing aggregate over a METRIC relation and move; **8 are the inner read of a
      self-aliasing aggregate over a PROVIDER relation and are protected.**
    · **prose** — a mention documenting a PROVIDER surface is a reference, not the metric.
      3 protected in files that otherwise move.
    · **seed** — `base_relation` / `numerator_expr` / `denominator_expr` are references, never the
      metric's own name. 6 protected; the five `metric_id` values move.

  ⭐ **THE FOURTH SURFACE THE RECORD SAID TO EXPECT, found here: `label_i18n_key`.** Row 50's key is
  `playerMetrics.offsides.label`, so a stem matches INSIDE a dotted i18n key. It does NOT move, and
  `!125`'s own diff is the proof rather than an argument: `playerMetrics.shots.label` stayed while
  `shots_total → shots_player`. The other four rows settle it independently — their keys
  (`playerMetrics.cards.yellow`, `.cards.red`, `.cards.label`, `.penalties.committed`) contain no
  stem at all, so these keys never tracked the metric_id in the first place.

  ⛔ **THE BUILT-PAGE PREDICTION, made before any code was written — AND IT IS NOT `!125`'s.** That
  MR could say the names never reached the payload. **These four do.** `site_v2/src/data/fixtures/*.json`
  carry `offsides`, `penalty_committed`, `cards_yellow` and `cards_red` under `top_players[]`, ten
  per fixture across 19 files, and that payload is built from **`mart_player_momentum`**
  (`export_site_data.py:871`) — a player METRIC mart this MR renames, not from
  `mart_player_fixture_stats`. `shape_top_players` filters with a DROP list (`_TOPPLAYER_DROP`,
  which names none of the five), so a renamed mart column flows straight through into a payload key.
  Three consequences, stated in full rather than reduced to "no change":
    1. **Today the built pages are byte-identical.** `site_v2/src/data/**` is the declared transient
       and is not swept, and NO `.astro` / `.ts` / spec file references any of the five. The four
       are carried-but-unrendered atoms — `01_fixture_page.md:196` calls them "available in the
       payload for an expanded row"; `03_player_profile.md:106` says they "stay unrendered". Row
       count HOLDS AT 12 where `!123` left it, headings at 7, in all three locales.
    2. **At the sample roll-forward those four payload keys change.** Nothing reads them, so nothing
       breaks — but it is a real payload change and is declared here, not discovered later.
    3. `cards_total` reaches only the leaderboards payload, which is not committed under
       `site_v2/src/data/` and has no page today.
  ⭐ **And because the payload's SOURCE renames, `01_fixture_page.md:198-199` renames with it.** That
  inverts the naive reading: `!125` classified the same file as team-side prose to protect, and it
  was right to — its only stem there was the TEAM `shots_on_goal_pct` at line 151. Same file,
  different source, different answer. This is the rule working, not an exception to it.

  ⛔ **TWO PROSE JUDGEMENT CALLS, DECLARED RATHER THAN BURIED**, each printed by the classifier with
  its reason:
    1. **`03_player_profile.md:119` does NOT move, while `:100` and `:106` do.** Line 119 is a row
       of the MATCH LOG table, whose payload is `mart_player_match_log` — excluded by the "yes"
       ruling; its neighbours in that same table are `goals_total`, `goals_saves`, `minutes_played`,
       `is_substitute`, all provider names. Lines 100 and 106 are the season-stats bundle and its
       unrendered atomics, a different surface nineteen lines above. One file, two sources.
       ⚠ This is the same class as the prose defect `bi-analyst-reviewer` FAILed `!125` round 2 on,
       in the same file, and it is keyed on LINE CONTENT rather than a line number so it cannot
       decay.
    2. **`metrics_display.md:271` and `docs/ui_design_brief.md:98,166` do NOT move.** All three are
       English prose, not key lists: their siblings are deliberately non-identifiers ("dribbled
       past", "penalties won/committed", "goals conceded", "cards (Y/R)"). Renaming `offsides` alone
       would leave it the only identifier in a prose list — worse, not better. `metrics_display.md:264`,
       the player metric-row contract's Atomics column, DOES move.
    3. **`assert_metric_direction_lower_is_better_agree.sql:9` does NOT move.** Its `{# #}` comment
       records a DATED fact — "by 2026-07-21 four rows contradicted each other (`cards_yellow`,
       `cards_red`, `cards_total`, `shots_on_goal_against`)" — about the catalogue as it stood on
       that date. Dated log → append, never rewrite. ⚠ The counter-argument is real and is recorded
       rather than hidden: a reader who greps the live seed for `cards_yellow` will not find it. It
       is a one-line fix in either direction if a reviewer reads it the other way.

  ⚠ `docs/ui_design_brief.md` is NEW to this sweep and was found by the classifier ABORTING on it
  rather than by a search. That abort-on-unlisted rule is why an English word colliding with a
  metric id could not be swept silently.

  ⚠ **A NO-OP WRITE IS STILL A WRITE.** 22 of the 24 swept files were opened; the two with zero
  renames were not. The contract gate watches the file system, not the diff.

  THRESHOLD DECLARATIONS. NEW MECHANISM: none in the shipped tree — the reference resolver remains a
  scratchpad verification tool, not a committed gate. Whether it should BECOME one is carried in
  `decisions_reserved`, unanswered. RECURRING COST: none. NEW DEPENDENCY: none.

decisions_reserved:
  - none NEW on naming: all five are ruled and quoted.
  - ⭐ **CARRIED, STILL UNANSWERED: should the column-reference resolver become a committed CI gate?**
    A NEW MECHANISM and therefore the CPO's/CTO's call. Five batches remain with the same exposure.
    Evidence added by THIS MR: it was watched going red on both shapes before being trusted, and
    this batch contains three identically-shaped bare reads with two opposite correct answers — the
    precise discrimination no offline gate in the repo performs.
  - ⚠ CARRIED FORWARD: **#96**, now SIX consecutive reproductions. All six `accepted_values` lists
    were checked by eye; exactly one changes (`shared.yml:1756`).
  - ⚠ CARRIED FORWARD: `_LEADERBOARD_METRICS` / `_LB_KEEP` (`export_site_data.py:48,53`) are pinned
    by NO test — `tests/test_export_site_data.py` exercises `shape_leaderboards` with synthetic keys
    only. This MR moves three of those literals, so a stale key would ship silently. Pre-existing
    and systemic across every batch, not introduced here.
  - ⚠ CARRIED FORWARD: **#99**, the export's literal `goals`/`assists` read keys — MR 7's; verified
    none of these five has the same problem.
  - ⚠ CARRIED FORWARD: **#98**, English group headings on DE/FI. Untouched.
  - ⚠ CARRIED FORWARD: the latent inheritance trap the doc re-pointing leaves — a `_player`-named
    block feeding team columns. Two more join it here (`fct_fixture_team_stats.offsides`,
    `mart_team_fixture_stats.offsides`). Filed rather than guarded; a guard is a new mechanism.

done_when:
  - `sync_metric_docs_blocks.py --check` passes after regeneration, with five bare blocks for these names and the block count unchanged.
  - `check_description_hygiene.py`, `check_layer_contract.py`, `check_ui_i18n_metrics.py` pass, `dbt parse` is clean with zero dangling `doc()`, and the description count reads **1604** — identical to the base, which is the "re-point them" ruling measured.
  - The static column-reference resolver reports zero broken references, and was watched going RED on BOTH a dotted and a bare reproduction before it was trusted.
  - `python -m pytest -q` matches the `3e5b25b` baseline.
  - `sqlfluff lint` on every changed model, FROM THE REPO ROOT, UNPIPED, exit code read bare; any FAIL proved pre-existing by re-linting the file unmodified and diffing.
  - `npm test` green, the two label-independent mutations watched going RED, and the built site measured structurally at 12 rows / 7 headings, unchanged in all three locales.
  - All six `accepted_values` metric-key lists read by eye, with the one that changes named.
