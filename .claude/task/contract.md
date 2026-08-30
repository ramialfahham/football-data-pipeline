# Task contract — rename the five player defending metrics (step 4, MR 3)

objective: >
  **STEP 4 of the metric catalogue naming programme, MR 3 of seven.** The `defending` family of the
  player catalogue:

      tackles_total          →  tackles_player
      tackles_interceptions  →  interceptions_player
      tackles_blocks         →  blocks_player
      defensive_actions      →  defensive_actions_player
      dribbles_past          →  dribbles_past_player          (PLAYER entity only)

  `!125` shipped `shooting`, `!127` shipped `discipline` (five reviewers PASS at round 1, full
  pipeline green including `data:build:mr`). Remaining after this one: `passing` (5) · `duels` (6) ·
  `goalkeeping` (4) · `goals` (7).

  ⛔⛔ **THE RULE, UNCHANGED AND STILL THE WHOLE DESIGN: A REFERENCE FOLLOWS ITS SOURCE.** Shape only
  tells you WHAT is being read. These player names are also provider stat words — `tackles_total` is
  the same identifier from `stg_apif__fixture_players` through base, core and `int_legs__player_match`.

  ⛔⛔ **AND THIS IS THE BATCH WHERE THE TEAM AND PLAYER NAMESPACES ACTUALLY MEET.** RULING 5's own
  reasoning named `int_legs__team_from_players` as the model where seven TEAM metrics are aggregated
  FROM player data — "tackles, interceptions, blocks, defensive actions, duels, duels won, key
  passes". **Four of these five are on that list.** `int_legs__team_from_players.sql:29-31` reads

      sum(tackles_total) as tackles,  sum(tackles_blocks) as blocks,
      sum(tackles_interceptions) as interceptions

  — player column names in, TEAM column names out. It is excluded outright as a provider `.sql`
  under the "yes" ruling, which is correct and load-bearing: its reads point at
  `int_legs__player_match`, which does not rename. Renaming them there would produce a model that
  cannot execute, and it is the single most dangerous line in the batch.
  ⭐ The team seed formulas are safe BY CONSTRUCTION and it is worth stating why rather than trusting
  it: `defensive_actions_per_match` reads `sum(tackles + interceptions + blocks)` from that model,
  whose columns are `tackles` / `interceptions` / `blocks` — **different tokens**, so no stem
  reaches them.

refs: >
  **`.claude/task/escalations.log`, the block "THE METRIC CATALOGUE NAMING PROGRAMME"**, its table
  "⛔ PLAYER, 35 REMAINING" — all five renames appear in it verbatim.
  ⭐ Cited by CONTENT, never by line number and never a plan file.
  ⭐ The shape is **RULING 5**, verbatim: "suffix only for the player metrics", with its reasoning
  that seven team metrics are aggregated from player data via `int_legs__team_from_players` — which
  is exactly why this batch needs a real `PROTECT_TOKENS` set where MR 2 needed none.
  ⚠ Group membership was verified FROM THE SEED, not assumed from the table: `player`/`defending` is
  **9 rows** — these five plus `tackles_per90`, `interceptions_per90`, `blocks_per90`,
  `defensive_actions_per90`, which are four of the twelve UNCHANGED `_per90` names.

  ⭐ **TWO STANDING CPO RULINGS GOVERN, applied unchanged and quoted with what they answered:**
  1. **"re-point them"** — references to a renamed doc block move, wherever they sit. **59 of the 72
     doc references move; 13 do not**, because their blocks are not renamed
     (`defensive_actions_per_match*`, `defensive_actions_per90`). Measured proof: the description
     count holds at **1604**, exactly the base.
  2. **"yes"** — the per-match / provider surfaces keep the provider name and are out of the edit set
     entirely: `mart_player_match_log`, `mart_player_fixture_stats`, `mart_team_fixture_stats`,
     `int_legs__*` (including `int_legs__team_from_players`), `3_core`, `2_base`, `1_staging`.

  ⭐ **THE DERIVED FORMS FOLLOW THEIR METRIC, and the precedent is landed and readable rather than
  argued.** `defensive_actions` carries four player yoy forms plus their `__player` block names.
  `!125` did exactly this for `shots_on_goal`: `int_player_profile__yoy.sql:80` now reads
  `shots_on as shots_on_goal_player_this_season`. So
  `defensive_actions_this_season → defensive_actions_player_this_season`, and so on.

  Branched from main **`a3fb952`**, clean tree. `glab mr list`: no open merge requests.

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
  - dbt_project/models/4_intermediate/shared/int_player_profile.yml
  - dbt_project/models/4_intermediate/shared/int_player_profile__yoy.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
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
# ⚠ SWEPT BUT NOT CHANGED — 16 files the classifier read and decided, every token PROTECTED. They
# are deliberately IN the sweep rather than skipped, so a decision is printed for each:
#  · the six TEAM models carrying `defensive_actions_per_match*`: int_team_profile__yoy,
#    mart_team_profile, mart_team_season_record, mart_team_momentum,
#    int_team_season__metrics_cumulative, int_team_competition_benchmark_metrics_long
#  · int_team_profile.yml and int_competition_benchmarks.yml — team columns and the player
#    benchmark list, which holds `defensive_actions_per90`
#  · dbt_project/macros/player_benchmark_metrics.sql — `defensive_actions_per90` only
#  · docs/wireframes/12_player_stats.md (`defensive_actions_per90`), 14_team_stats.md (team)
#  · ⭐ THE FIVE FRONTEND FILES: site_v2/src/i18n/strings.ts, lib/metricRows.ts,
#    components/team/TeamPerformance.astro, specs/competition/matches/fixture.spec.json,
#    specs/teams/team.spec.json — every token is `defensive_actions_per_match`, a RENDERED row.
#
# ⚠ NOT IN SCOPE, each for a stated reason:
#  · the PROVIDER / per-match surfaces — the CPO's "yes". `core.yml` and `int_legs.yml` ARE in
#    scope, but ONLY to re-point a `doc()`; no column on them moves.
#  · site_v2/src/data/** — the declared transient. `teams/33.json` alone holds 121 occurrences.
#  · site/** — the frozen MVP tree.

protected_override: >
  none required. No file in scope_paths is a protected command-class file.

impact_map: >
  writers: the five metrics are computed in `int_player_club_season__metrics` and
    `int_player_season_position__metrics` (the two per-fixture bases), re-summed in
    `int_player_season__metrics`, windowed in `int_player_momentum__metrics` and
    `int_player_season_record`, and `defensive_actions` is additionally COMPOSED in
    `int_player_profile__yoy` from `int_player_season_record`'s three tackle columns.
    `mart_player_profile`, `mart_leaderboards`, `mart_player_momentum` and
    `mart_player_season_record` consume them.

  downstream: `dbt ls --select int_player_club_season__metrics+ int_player_season__metrics+
    int_player_momentum__metrics+ int_player_season_record+ int_player_season_position__metrics+
    int_player_profile__yoy+ --resource-type model`, verbatim output — **13 models**:
      4_intermediate.shared.int_player_club_season__metrics
      4_intermediate.shared.int_player_competition_benchmarks
      4_intermediate.shared.int_player_momentum__metrics
      4_intermediate.shared.int_player_profile__yoy
      4_intermediate.domestic_league.team_season.int_player_season__metrics
      4_intermediate.shared.int_player_season_position__metrics
      4_intermediate.shared.int_player_season_record
      5_marts.shared.mart_leaderboards
      5_marts.shared.mart_player_career
      5_marts.shared.mart_player_competition_benchmarks
      5_marts.shared.mart_player_momentum
      5_marts.shared.mart_player_profile
      5_marts.shared.mart_player_season_record

    ⛔⛔ **AND A CORRECTION TO THIS CONTRACT'S OWN CLAIM, WHICH IS WORSE THAN THE FINDING THAT
    PROMPTED IT.** `scope-auditor` FAILed round 2 because this field described the command without
    pasting its output. The truthful correction is larger: the earlier wording said the command was
    **"run on this branch BEFORE the first edit"**, and **it was not run for MR 3 at all.** That
    sentence was carried over from `!127`'s contract — where the command *was* run — and never
    executed here. The reviewer caught missing evidence; the actual fault was **asserting a step I
    had skipped**. The list above is the real output, run after the finding.
    ⭐ THE RULE, and the record already carries its sibling ("don't claim a record says what it
    doesn't"): **a contract sentence saying "I ran X" is a claim of fact and must be true when
    written, not when convenient.** Reusing a prior contract as a template silently imports its
    claims along with its structure.
    ⚠ **What running it actually changed**, so this is not merely a formatting fix: the real lineage
    is **13 models, not the 10** the previous batch's list held. Three of the thirteen —
    `int_player_competition_benchmarks`, `mart_player_competition_benchmarks`, `mart_player_career`
    — carry none of the five names, which is the over-count the caveat below predicted; had the
    number gone the other way it would have pointed at a model this contract does not cover.
    ⚠ **THE LINEAGE IS EVIDENCE, NOT THE FILE LIST** — it under-counts every yml, `core.yml`,
    `int_legs.yml`, the wireframes and the export, and over-counts the three named above.
    ⭐ Audited the rest of this contract for the same defect after the finding:
    `deploy_order`'s "no touched model is incremental" was re-derived rather than re-asserted — all
    ten changed `.sql` models declare `materialized='table'` or `'view'`, none `'incremental'`.

  layer_rules: `check_layer_contract.py`. Coupled guards:
      · ⭐ **`shared.yml:1756`** — the 14-name `mart_leaderboards.metric_key` `accepted_values` list.
        **`defensive_actions` → `defensive_actions_player`**, in lockstep with `mart_leaderboards.sql`'s
        `count_boards` and the export's `_LEADERBOARD_METRICS`. `_LB_KEEP` additionally holds
        `tackles_total`, `tackles_interceptions`, `tackles_blocks`.
      · ⭐ **`int_competition_benchmarks.yml:105` and `shared.yml:2186`** — the two 18-name PLAYER
        lists both contain **`defensive_actions_per90`, which must NOT move.** These two are
        checked as PROTECTIONS, not as changes: a mis-scope breaks them. That is #96 in reverse and
        it is new this batch.
      · the three 22-name TEAM lists contain none of the five.
    ⛔ #96: no offline gate enforces any of them — SEVEN consecutive reproductions. Checked by eye.

  deploy_order: none needed. No touched model is incremental.

  blast_radius: five metric columns plus four derived yoy forms rename across the player per-fixture
    bases, season, position, momentum, season-record, yoy and mart models; one `metric_key` VALUE
    changes on the leaderboard boards. **No number changes** — every formula, floor and null policy
    is byte-identical, and the catalogue's own formulas still read the leg columns they always did.

acceptance_criteria:
  - Every player metric name the BUILT site renders reads the same words after the rename as before, in all three locales, measured structurally from the markup of the pages under `site_v2/dist/` and compared element-for-element against the same pages built from the base commit — never by substring. ⭐ **This batch is the first where that is a REAL check rather than a confirmed prediction**: `defensive_actions_per_match` is one of the 12 rendered rows and is a PROTECTED token, so a mis-scope removes a rendered label.
  - No `site_v2/src` source file outside the generated sample changes at all, and no name is HALF-renamed — each new name appears everywhere the old one did in the models, ymls, seed, export and wireframes that this MR moves, and every surviving old name is an upstream READ of a provider relation, pinned by count per file.
  - `sync_metric_docs_blocks.py --check` and `check_description_hygiene.py` both pass AND are each watched going RED — the first on a stale `metric_id` in the seed, the second on a deliberately dangling `doc()`.
  - ⭐ Every dotted AND bare column reference to a renamed name resolves against the relation it actually reads, checked statically and watched going RED against a reproduction of the `!125` round-2 defect.

decisions_taken: >
  All five names come from the record; both governing rulings are quoted with what they answered.
  The derived-form targets follow `!125`'s landed precedent rather than a new decision.

  ⭐⭐ **ONE QUESTION, ASKED OF EVERY OCCURRENCE: DID THE RELATION THIS READS FROM RENAME THE
  COLUMN?** 367 tokens classified once, each decision printed — **247 renamed, 120 protected**,
  reconciling exactly against `git grep` in both directions. 1,464 tokens repo-wide: 1,062 untouched
  (the sample, `.claude/**`, `site/**`, the regenerated `metric_columns.md`), 35 in provider `.sql`.

  **FOUR self-aliasing `sum(X) … as X` sites this batch, and only ONE moves its inner read:**

      int_player_club_season__metrics.sql       ← per_fixture ← fct_fixture_player_stats   KEEP
      int_player_season_position__metrics.sql   ← per_fixture ← fct_fixture_player_stats   KEEP
      int_player_season_record.sql              ← player_legs = int_legs__player_match     KEEP
      int_player_season__metrics.sql            ← club_season = int_player_club_season__metrics
                                                  a METRIC relation this MR renames         MOVES

  ⚠ `int_player_season_position__metrics` is NEW to the sweep and is the second file to need a
  `PROVIDER_DOTTED` entry (`s` = `fct_fixture_player_stats`).

  ⛔ **A DEFECT I INTRODUCED AND CAUGHT ON THE FIRST DRY RUN, recorded because the class is the
  point.** I set out to improve the classifier's printed REASON — MR 2 labelled every
  non-self-aliasing bare read "this model's own column", which is false at
  `int_player_profile__yoy.sql:50`, where `tackles_total + tackles_interceptions + tackles_blocks as
  defensive_actions` reads `ref('int_player_season_record')`. My first version of that improvement
  swallowed the `alias` case, so the four aliases in `int_player_season_record.sql` came out labelled
  **"bare read of int_legs__player_match, which renames it"** — a sentence false twice over: it is a
  WRITE, and that relation does not rename. The decisions were right throughout (247/120 before and
  after the fix, unchanged), but **a decision list a reviewer checks INSTEAD of the diff must not
  lie**, and I had just reintroduced exactly that. Fixed by handling `alias` explicitly and naming
  the renaming relations, so the label can only claim a source that actually moves.

  ⛔⛔ **AND A FALSE POSITIVE IN THE RESOLVER ITSELF, FOUND ON THE UNMODIFIED TREE.** Run against
  `main` before a single edit, `check_column_refs.py` reported
  `int_player_profile__yoy.sql:82` as a BROKEN reference: `defensive_actions` read inside CTE `cur`,
  whose chain resolves to `int_player_season_record`, which does not emit it. **The column is born
  in the chain** — `std` creates it by expression at line 50. No earlier batch exercised this,
  because none had a metric COMPUTED inside a CTE from renamed inputs.
  ⭐ Fixed: a name created by an `as <name>` alias in the same model is exempted — and **exempted
  into the "unresolved, reported" list, never silently**, so the count of what the tool did not
  check stays visible. The fix was then proved not to have blunted it: reproducing the `!125`
  round-2 defect still turns it RED with the exact diagnosis.
  ⭐ THE RULE: **a check that cries wolf gets ignored, which makes it the same defect as one that
  gives false confidence.** The record already carries the second half; this is the first.

  ⛔ **THE BUILT-PAGE PREDICTION, before any code — and it is a REAL check this time.**
  `defensive_actions_per_match` is one of the **12 rendered metric rows** (`metricRows.ts:98`,
  `strings.ts:630/669/708`, `TeamPerformance.astro:61`, both page specs). Those five occurrences are
  PROTECTED tokens, so **if any were mis-scoped a rendered label would disappear** and the
  element-for-element comparison would catch it. Unlike `!125` and `!127`, an unchanged build here
  is evidence, not only a confirmed prediction. Predicted: **12 rows / 7 headings, EN+DE+FI,
  ADDED none / REMOVED none**, and zero changed files under `site_v2/src`.

  ⛔⛔ **THE ROUND-1 DEFECT, AND THE JUDGEMENT THAT SHOULD HAVE BEEN HERE FROM THE START.**
  `bi-analyst-reviewer` FAILed round 1 on `docs/wireframes/03_player_profile.md:127-128`. That file
  documents **two surfaces**, and this contract recorded a judgement for neither:
    · lines 96-106 — the season-stats bundle and its unbundled-atomics line, sourced from
      `mart_player_profile` / `mart_player_season_record`, which DO rename. **4 tokens move.**
    · lines 126-129 — the MATCH LOG expanded-row list, sourced from `mart_player_match_log`, a
      provider surface the "yes" ruling keeps unrenamed. **2 tokens must NOT move**, and round 1
      moved them, leaving the wireframe naming two fields that exist nowhere in the export.
  ⚠ `!127` recorded exactly this split for the same file and the same table. This contract had no
  entry for the match-log section at all, so the rename shipped with no judgement recorded — which
  is why the reviewer could fairly call it a reversal of precedent rather than a considered call.

  ⛔ **WHY THE GUARD MISSED IT, because the cause is more useful than the fix.** The provider-prose
  guard keys on line CONTENT — the mark "may show the full per-match line" — but tested it against
  **the token's own line**. In `!125` the affected token sat on the same line as the mark, so it
  worked by luck. Here the list wraps: the mark is on line 126, the tokens on 127-128.
  ⭐ **THE CLASS: a line-scoped test on a construct that spans lines.** The repo already records it
  for grep ("a line-based grep misses a phrase straddling a line break"); this is the same defect in
  prose. The mark now governs its whole PARAGRAPH, up to the first blank line.
  ⭐ Round 2 numbers: **245 renamed / 122 protected** (was 247/120) — those two tokens, and nothing
  else, moved from one column to the other. The fix was applied by RE-RUNNING the classifier, so
  what ships is its output rather than a hand-edit.
  ⚠ The verification suite changed with it: `03_player_profile.md` is now pinned by an EXACT COUNT
  of 2 protected, not whitelisted. A whole-file exemption would let a future half-rename through
  silently — and this is the second time in this programme that a whole-file question proved wrong
  for a file that only PARTLY moves, the first being MR 2's models.

  ⚠ **A GATE IN `done_when` IS NOT DISCRIMINATING FOR THIS CHANGE, raised by `platform-reviewer` and
  recorded rather than quietly dropped.** `check_ui_i18n_metrics.py` validates only `site/**` — the
  retired, frozen legacy tree this branch never touches — so its exit 0 "passes identically whether
  or not the rename happened". It is still a real CI gate and is still run, but it is **not
  evidence** for this MR and is no longer presented as such. The discriminating check for the UI
  risk is the before/after structural `dist` comparison. Same class as every other vacuous-check
  finding in the record, turned this time on my own evidence list.

  THRESHOLD DECLARATIONS. NEW MECHANISM: none in the shipped tree — the resolver remains a scratchpad
  tool. RECURRING COST: none. NEW DEPENDENCY: none.

decisions_reserved:
  - none NEW on naming: all five are ruled, and the derived forms follow `!125`'s landed precedent.
  - ⭐ **CARRIED, STILL UNANSWERED: should the column-reference resolver become a committed CI gate?**
    Evidence now spans three MRs. New this batch, and it cuts both ways: the resolver had a
    FALSE-POSITIVE class nobody had hit before, so committing it would have turned `main` red on a
    correct tree. That is an argument for hardening it before adopting it, not against adopting it.
  - ⚠ CARRIED FORWARD: **#96**, now SEVEN reproductions. Three of the six lists are in play this
    batch — one changes, two must be protected.
  - ⚠ CARRIED FORWARD: `_LEADERBOARD_METRICS` / `_LB_KEEP` pinned by NO test. `platform-reviewer`
    independently confirmed this on `!127` and confirmed the values were nonetheless correct. This
    MR moves four more of those literals.
  - ⚠ CARRIED FORWARD: **#99**, the export's literal `goals`/`assists` read keys — MR 7's.
  - ⚠ CARRIED FORWARD: **#98** English group headings on DE/FI; the doc-block inheritance trap.

done_when:
  - `sync_metric_docs_blocks.py --check` passes after regeneration, with the block count reconciled.
  - `check_description_hygiene.py`, `check_layer_contract.py`, `check_ui_i18n_metrics.py` pass, `dbt parse` is clean, and the description count reads **1604** — identical to the base.
  - The resolver reports zero broken references, and was watched going RED on a reproduction of the `!125` round-2 defect AFTER its false-positive fix, proving the fix did not blunt it.
  - `python -m pytest -q` matches the `a3fb952` baseline.
  - `sqlfluff lint` on every changed model, FROM THE REPO ROOT, UNPIPED, proved byte-identical to a re-lint of the stashed base.
  - `npm test` green, the two mutations watched going RED, and the site built TWICE at 12 rows / 7 headings, unchanged in all three locales.
  - All six `accepted_values` lists read by eye: the one that changes named, and `defensive_actions_per90` asserted still present in both player lists.
