# Task contract — rename the five player passing metrics (step 4, MR 4)

objective: >
  **STEP 4 of the metric catalogue naming programme, MR 4 of seven.** The `passing` family of the
  player catalogue:

      passes_total       →  passes_player
      passes_accurate    →  passes_accurate_player
      passes_key         →  passes_key_player
      pass_accuracy_pct  →  passes_accuracy_player_pct
      key_passes_per90   →  passes_key_per90              (PLAYER entity only)

  `!125` shipped `shooting`, `!127` `discipline`, `!128` `defending`. Remaining after this one:
  `duels` (6) · `goalkeeping` (4) · `goals` (7).

  ⛔⛔ **THE RULE IS UNCHANGED AND IS STILL THE WHOLE DESIGN: A REFERENCE FOLLOWS ITS SOURCE.**
  Shape only tells you WHAT is being read. **This is the largest and most exposed batch of step 4**:
  426 tokens across 48 files, and three surfaces no previous batch had.

  ⚠ **`key_passes_per90 → passes_key_per90` is the ONLY `_per90` name in the entire programme that
  renames** — it is the entry the record's own "13 unchanged, not 14" correction is about, and it
  sits in BOTH 18-name player `accepted_values` lists.

refs: >
  **`.claude/task/escalations.log`, the block "THE METRIC CATALOGUE NAMING PROGRAMME"**, its table
  "⛔ PLAYER, 35 REMAINING" — all five renames appear in it verbatim.
  ⭐ Cited by CONTENT, never by line number and never a plan file.
  ⭐ `passes_accuracy_player_pct` is **RULING 5's shape** (`_player` before a trailing `_pct`)
  applied to **item 6 of "THE SIX"** — `pass_accuracy_pct → passes_accuracy_player_pct`, singular
  corrected to plural where the family is plural. Both are in the record.
  ⚠ Group membership verified FROM THE SEED, not assumed: `player`/`passing` is **6 rows** — these
  five plus `passes_per90`, which does not change.

  ⭐ **TWO STANDING CPO RULINGS, applied unchanged:** **"re-point them"** (references to a renamed
  doc block move wherever they sit — the description count must hold at 1604) and **"yes"** (the
  per-match / provider surfaces keep the provider name and are out of the edit set entirely).

  ⭐⭐ **AND ONE NEW CPO RULING, TAKEN DURING PLANNING AND RECORDED WITH WHAT IT ANSWERED.** The four
  derived yoy columns `key_passes_this_season` / `_prev_season` / `_prev_season_full` /
  `_delta_yoy` — 20 occurrences across 4 files, none a catalogue row — **rename with the metric** to
  `passes_key_player_*`. What he was shown before answering:
    · that they are unreachable by the token sweep, because they use the OLD `key_passes` noun order
      and contain none of the five stems;
    · that renaming them also REVERSES that noun order, which RULING 6 settled for the metric_id but
      never for these derived columns — which is why it was put to him rather than decided;
    · that `!125` and `!128` both moved derived forms with their metric
      (`shots_on_goal_this_season → shots_on_goal_player_this_season`);
    · the two alternatives with their costs — defer to a later MR (leaves a metric whose own yoy
      columns contradict its name), or leave permanently (the ruled pattern stops describing the
      tree).
  His answer: **rename them with the metric.**

  Branched from main **`1cf0d40`**, clean tree. `glab mr list`: no open merge requests.

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
  - docs/wireframes/12_player_stats.md
  - docs/wireframes/99_gaps_register.md
  - docs/wireframes/metrics_display.md
  - scripts/export_site_data.py
  - site_v2/src/lib/types.ts
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/active_work.md

# ⚠ This list is the EXACT changed set — reconciled against `git diff --name-only` in both
# directions, nothing extra either way.
#
# ⭐⭐ NOTE `site_v2/src/lib/types.ts`. MRs 1-3 each asserted an EMPTY `site_v2/` diff. **THAT CLAIM
# IS FALSE HERE AND IS NOT CARRIED FORWARD** — see decisions_taken.
#
# ⚠ SWEPT BUT NOT CHANGED — 17 files the classifier read and decided, every token PROTECTED, kept
# IN the sweep so a decision is printed for each rather than being an invisible exclusion:
#  · ten TEAM models carrying `passes_key_per_match*`, bare `key_passes`, or the `_sum_season` pair:
#    int_team_season__metrics_cumulative, int_team_momentum__metrics, int_team_momentum_window,
#    int_team_profile__yoy, int_team_season_record, int_team_competition_benchmark_metrics_long,
#    mart_team_momentum, mart_team_profile, mart_team_season_record, mart_team_season_insights
#  · int_team_profile.yml and domestic_league.yml — team column declarations
#  · docs/wireframes/14_team_stats.md — the team Passing row
#  · ⭐ FOUR FRONTEND FILES: site_v2/src/i18n/strings.ts, lib/metricRows.ts,
#    specs/competition/matches/fixture.spec.json, specs/teams/team.spec.json — every token is
#    `passes_key_per_match`, a row DECLARED in `metricRows.ts` but NOT among the 12 that render —
#    see the correction in `decisions_taken`.
#
# ⚠ NOT IN SCOPE, each for a stated reason:
#  · the PROVIDER / per-match surfaces — the CPO's "yes". `core.yml` and `int_legs.yml` ARE in
#    scope, but ONLY to re-point a `doc()`; no column on them moves.
#  · site_v2/src/data/** — the declared transient.
#  · site/** — the frozen MVP tree, which holds `pass_accuracy_recent`, the retired MVP's live_id.

protected_override: >
  none required. No file in scope_paths is a protected command-class file.

impact_map: >
  writers: the five metrics are computed in `int_player_club_season__metrics` and
    `int_player_season_position__metrics` (the two per-fixture bases), re-summed in
    `int_player_season__metrics`, windowed in `int_player_momentum__metrics` and
    `int_player_season_record`, and the key-passes yoy forms are derived in
    `int_player_profile__yoy`. `player_benchmark_metrics.sql` carries `pass_accuracy_pct` and
    `key_passes_per90` as board keys AND column names. `mart_player_profile`, `mart_leaderboards`,
    `mart_player_momentum` and `mart_player_season_record` consume them.

  downstream: `dbt ls --select int_player_club_season__metrics+ int_player_season__metrics+
    int_player_momentum__metrics+ int_player_season_record+ int_player_season_position__metrics+
    int_player_profile__yoy+ int_player_competition_benchmarks+ --resource-type model`,
    **run on this branch, verbatim output — 13 models**:
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
    ⚠ **THE LINEAGE IS EVIDENCE, NOT THE FILE LIST** — it under-counts every yml, `core.yml`,
    `int_legs.yml`, six wireframes, the export and `types.ts`; `mart_player_career` carries none of
    the five names.
    ⭐ **RE-RUN FOR THIS BRANCH, NOT COPIED.** `!128` FAILed review round 2 because this field
    claimed a command had been run when the sentence had been carried over from `!127`'s contract.
    Every factual claim in this contract was re-derived.

  layer_rules: `check_layer_contract.py`. Coupled guards:
      · ⭐ **#96 AT ITS WIDEST YET — THREE of the six lists change, seven entries in total.**
        `shared.yml`'s 14-name board list moves `passes_total`, `passes_key`, `pass_accuracy_pct`;
        and **both** 18-name PLAYER lists (`int_competition_benchmarks.yml:105`, `shared.yml:2186`)
        move `key_passes_per90` and `pass_accuracy_pct` while `passes_per90` must NOT move. **This
        is the first batch in which either 18-name list changes at all** — `!128` had to protect
        them. The three 22-name TEAM lists are untouched: `passes_accuracy_pct` does not contain
        `pass_accuracy_pct` (`passes_` ≠ `pass_`), and `passes_key_per_match` is protected.
      · ⭐ **FOUR SINGULAR RANGE TESTS RENAME** — a surface `!127` and `!128` explicitly had none of:
        `int_player_season_pass_accuracy_pct_in_range` (`int_team_season.yml:432`),
        `std_player_…` (`shared.yml:987`), `player_profile_…` (`shared.yml:1270`),
        `mart_leaderboards_…` (`shared.yml:1734`). Step 3's batch D **deliberately protected all four
        as "step-4 names"**; the record says so. Precedent for moving them is `!125`.
    ⛔ #96: no offline gate enforces any list — EIGHT consecutive reproductions. Checked by eye.

  deploy_order: none needed. **Re-derived, not asserted:** of the ten changed `.sql` models, eight
    declare `materialized='table'` and two (`mart_leaderboards`, `mart_player_season_record`)
    `'view'`. None is incremental.

  blast_radius: five metric columns plus four derived yoy forms and four singular test names rename
    across the player per-fixture bases, season, position, momentum, season-record, yoy, benchmark
    and mart models; three `metric_key` VALUES change on the leaderboard boards and two on each
    player benchmark list; one frontend TYPE declaration moves. **No number changes** — every
    formula, floor and null policy is byte-identical.

acceptance_criteria:
  - Every player metric name the BUILT site renders reads the same words after the rename as before, in all three locales, measured structurally from the markup under `site_v2/dist/` and compared element-for-element against the same pages built from the base commit — never by substring. ⚠ **UNLIKE `!128`, THIS IS A CONFIRMED PREDICTION, NOT A DISCRIMINATING CHECK — see `decisions_taken`.** The discriminating guard for the protected team row is `npm test`'s label binding, asserted separately.
  - ⭐ **`site_v2/src/lib/types.ts` is the ONLY frontend file that changes**, and it changes exactly one token; the other four swept frontend files are byte-identical. No name is HALF-renamed — each new name appears everywhere the old one did in the models, ymls, seed, macro, export, wireframes and type that this MR moves, and every surviving old name is an upstream READ of a provider relation or a TEAM column, pinned by count per file.
  - `sync_metric_docs_blocks.py --check` and `check_description_hygiene.py` both pass AND are each watched going RED — the first on a stale `metric_id` in the seed, the second on a deliberately dangling `doc()`.
  - ⭐ Every dotted AND bare column reference to a renamed name resolves against the relation it actually reads, checked statically and watched going RED against a reproduction of the `!125` round-2 defect.

decisions_taken: >
  All five names come from the record; the derived-form targets come from the new CPO ruling quoted
  in `refs` with what it answered; the four range-test names follow `!125`'s landed precedent.

  ⭐⭐ **ONE QUESTION, ASKED OF EVERY OCCURRENCE: DID THE RELATION THIS READS FROM RENAME THE
  COLUMN?** 426 tokens classified once, each decision printed — **272 renamed, 154 protected**,
  reconciling exactly against `git grep` in both directions. 1,655 tokens repo-wide: 1,197 untouched
  (the sample, `.claude/**`, `site/**`, the regenerated `metric_columns.md`), 32 in provider `.sql`.

  ⭐⭐ **THE FIFTH SURFACE, AND THE RECORD SAID TO EXPECT ONE: THE SEED'S `description` FIELD.**
  `!127` found `label_i18n_key` as the fourth. Three descriptions gloss their own FORMULA in prose
  and name the PROVIDER column:
      passes_accurate    "Derived as SUM(passes_total × passes_accuracy_percent / 100)"
      pass_accuracy_pct  "Null when passes_total is zero"
      passes_accuracy_pct (TEAM)  "Null when passes_total is zero"
  All three name a leg column that does not rename — the same read-vs-write distinction as a dotted
  SQL reference, in prose. ⛔ **And it is not cosmetic: `+persist_docs` publishes these descriptions
  to BigQuery**, so renaming them would ship a published description naming a column that exists
  nowhere. `description` is now a seed REFERENCE field.
  ⚠ THE LIMIT, stated rather than implied: that protects the field wholesale, and a description
  naming its own metric_id would need the opposite treatment. None does — checked across all five
  renamed rows — and all three occurrences are printed for a reviewer to check individually.

  ⭐⭐ **THE FRONTEND CHANGES FOR THE FIRST TIME IN STEP 4, AND THE OLD CLAIM IS RETIRED RATHER THAN
  REPEATED.** `site_v2/src/lib/types.ts:53` declares `passes_key?: number | null` on the `TopPlayer`
  interface. `top_players[]` is built from `mart_player_momentum` (`export_site_data.py:871`), which
  renames that column, so the type must move or it declares a field the payload will stop carrying.
  Its neighbours there (`goals_total`, `goals_assists`, `saves`, `shots_on`) are leg names that pass
  through unrenamed; this one is a metric column. **No component reads it**, so the built pages still
  do not change — but MRs 1-3 all asserted an empty `site_v2/` diff, and repeating that here would
  have been precisely the template-carries-claims defect that cost `!128` two review rounds.

  ⛔⛔ **ROUND 1 FAILED ON EXACTLY THIS, AND THE HEURISTIC IS NOW GONE RATHER THAN PATCHED.**
  `analytics-engineer-reviewer` FAILed round 1: three models shipped
  `round(passes_player * passes_accuracy_percent / 100)` — a nested aggregate over a SIBLING ALIAS,
  against CTEs that only carry `passes_total`. They could not have compiled.
      int_player_club_season__metrics.sql:125 · int_player_season_position__metrics.sql:106
      int_player_season_record.sql:54
  **The cause is the mistake this programme already logged once.** The classifier decided "is this
  an upstream read?" by asking whether the LINE ends with `as <the same token>`:
      sum(passes_total) as passes_player                     -> recognised, protected
      sum(round(passes_total * …)) as passes_accurate_player -> NOT recognised, renamed
  The second is just as much an upstream read — the metric is COMPUTED FROM the provider column —
  but its alias is a different word. `!125`'s round-2 lesson was, verbatim, that for bare reads I
  asked "does the alias match the inner name" instead of "did the source relation rename this
  column". This is that mistake in a new shape.
  ⭐ **THE FIX DELETES THE HEURISTIC.** Every bare read is now decided by resolving its scope's
  SOURCE: a source CTE that WRITES the token emits the new name (aliases always move) → RENAME; a
  chain reaching a provider relation → PROTECT; a chain reaching a renaming relation → RENAME;
  anything else ABORTS rather than guesses. That abort fired twice on the first run and both were
  real gaps in my model of the file — a jinja macro with no query scope, and tokens inside `{# #}`
  comments — each now handled explicitly rather than by falling through.
  ⚠ Counts moved **275/151 → 267/159** at round 2.

  ⛔⛔ **ROUND 2 THEN FAILED TOO — 3 PASS / 2 FAIL — ON A FOURTH SITE OF THE SAME CLASS**, found
  independently by `analytics-engineer-reviewer` and `bi-analyst-reviewer`.
  `mart_player_season_record.sql:168-170,187`: the `matched` CTE was correctly updated to read
  `sf.passes_key_player` / `sf.passes_accurate_player` / `sf.passes_player`, but the model's own
  FINAL SELECT still projected the OLD bare names, which no longer exist in that chain — and its
  own `shared.yml` entry already declared the new ones. Another model that could not compile.
  ⛔ **THE CAUSE, and it is a THIRD root under the same rule:** `matched` is
  `from sides as s inner join season_final as sf`, and the renamed columns come from the JOINED
  side. My scope resolution followed only `FROM`, chased `sides`, and answered from the wrong
  branch. **Neither the classifier nor the resolver follows joins**, so both agreed the tree was
  clean — twice.
  ⭐ Fixed by resolving across the WHOLE source set: every `ref()`, every `from` AND every `join`,
  walked transitively; RENAME if any terminal is a renaming relation, PROTECT only if every
  terminal is a provider relation, ABORT otherwise. Two further aborts fired immediately and were
  real gaps, not noise — window clauses (`w as (…)`) parsing as CTEs, which had been hiding the
  final select of `int_player_season_record.sql` from resolution entirely. Counts settled at
  **272/154**, and the fix is the classifier's own output, not a hand-edit.

  ⭐⭐ **AND A CHECK THAT DOES NOT DEPEND ON ANY OF THAT.** Four failures across two rounds all came
  from my own source-resolution logic, so before spending the last round I built one that cannot
  fail the same way: **for every model, do the columns its yml declares actually appear in its FINAL
  SELECT projection?** That is precisely the mismatch `bi-analyst-reviewer` used to find the round-2
  site — `shared.yml` declared `passes_key_player` while the SQL said `passes_key` — and it is
  independent of CTE chains, joins and aliases.
  ⚠ It also shows why the existing yml guard was too weak: it asked whether the new name appears
  ANYWHERE in the file, and `passes_key_player` did — inside a CTE. The new check looks only at the
  final projection.
  ⭐ Result: **10 models checked, exactly one mismatch — the site the reviewers found, and no
  fifth.** That is what made a third round worth spending rather than a guess.
  ⭐ **The same check was then run against the ALREADY-MERGED `!125`/`!127`/`!128` names as an audit
  of shipped work: 9 models, zero mismatches.** The merged batches are sound.

  **FOUR self-aliasing `sum(X) … as X` sites, and only ONE moves its inner read** — unchanged from
  `!128`: `int_player_club_season__metrics` and `int_player_season_position__metrics` (← per_fixture
  ← `fct_fixture_player_stats`) and `int_player_season_record` (← `int_legs__player_match`) all KEEP
  the inner read; `int_player_season__metrics` (← `club_season` = `int_player_club_season__metrics`,
  a metric relation this MR renames) MOVES it.

  ⛔ **THE TEAM/PLAYER JUNCTION, AND THIS TIME A STEM REACHES IT DIRECTLY.**
  `int_legs__team_from_players.sql:28` reads `sum(passes_key) as key_passes` — player name in, TEAM
  name out. RULING 5 named key passes among the seven team metrics aggregated from player data. It
  is excluded as provider `.sql`, and that exclusion is **load-bearing**: renaming there ships a
  model that cannot execute. `int_legs__team_match.sql:120-121` additionally carries
  `own.passes_total` / `own.passes_accurate`, TEAM leg columns sharing the player metric names —
  also provider-excluded.
  ⭐ **Bare `key_passes` is SWEPT but never moves.** Step 3's batch D justified leaving it
  structurally and left the rule that comes with it: *on a rename whose stem is shared, print the
  classification, not just the diff — a reviewer can check a decision list, they cannot check an
  exclusion you kept in your head.* 14 printed PROTECT decisions instead of 14 invisible ones.

  ⛔⛔ **A CLAIM I CARRIED FROM `!128` AND THEN DISPROVED BY MEASURING IT. RECORDED AS A MISS.**
  While planning I wrote that `passes_key_per_match` is "one of the 12 RENDERED rows", so criterion
  1 would be a real check the way it was on `!128`. **Both halves are wrong.** Measured from the
  built pages: `metricRows.ts` declares **16** rows, of which **12** render, and the twelve EN
  labels are `% Duels won · % Save percentage · Clean sheets · Ø Corners · Ø Corners against ·
  Ø Defensive actions… · Ø Duels · Ø Goals · Ø Goals against · Ø Passes · Ø Shots ·
  Ø Shots on target`. **"Ø Key passes" is not among them** — whole-token grep finds it on **zero**
  built pages. It is one of the rows the committed sample cannot feed.
  ⭐ So for THIS batch the built-page comparison **confirms a prediction, as on `!125` and `!127`;
  it does not discriminate.** `!128` was the exception, because `defensive_actions_per_match`
  genuinely renders.
  ⭐ **WHAT DOES DISCRIMINATE for this row, verified rather than assumed:**
  `site_v2/scripts/check-metric-labels.test.mjs` extracts every `labelKey` from `metricRows.ts` and
  asserts in BOTH directions, in all three locales, that each is defined in `strings.ts` and that no
  defined label goes unasked. Rename one side of `metrics.passes_key_per_match.label` without the
  other and `npm test` goes red. ⚠ `!125` measured that this guard's covered set is entirely TEAM
  `metrics.*` keys, reaching none of the 35 player metrics — which is precisely why it is
  load-bearing HERE, where the thing at risk is a team row.
  ⭐ THE LESSON, the same one that cost `!128` two review rounds: **a claim that was true of the
  previous branch is not evidence about this one.** I caught this only by running the measurement
  the claim asserted instead of restating it.
  ⚠ **AND THE ARITHMETIC INSIDE THAT CORRECTION WAS ITSELF WRONG**, caught by
  `bi-analyst-reviewer` and `platform-reviewer` independently: `metricRows.ts` declares **16** rows,
  not 17. The 17 came from counting `field:` string occurrences, which double-counts the nested
  `team:` override on the `clean_sheets` row. The substantive conclusion is unchanged and was
  re-derived by both: 16 − 4 rows the sample cannot feed = **12 rendered**, and "Ø Key passes" is
  not among them.

  ⛔⛔ **AND THE RESOLVER COULD NOT HAVE CAUGHT THE ROUND-1 DEFECT AT ALL — a bigger blind spot than
  two batches of green results suggested.** Tested by reintroducing the defect: **exit 0**. Three
  separate gaps, each found by experiment rather than reasoning:
    · `check_bare` walked only CTE bodies, so a read in a model's FINAL SELECT was never scanned —
      and that is where `int_player_season_record.sql:54` lives;
    · `window w as (…)` clauses parsed as CTEs, which pushed the synthesised final-select scope past
      the end of the file even after it was added;
    · a CTE that JOINS two relations resolved to only one of them, which then reported
      `int_team_season_record.sql:141` broken — **a false positive on a file this branch never
      touches**, the cries-wolf class for a third time.
  All three are now closed and each was verified by watching the real defect go RED and the
  untouched file go GREEN. ⚠ The `created` exemption added on `!128` was also made SCOPE-AWARE: a
  name aliased in the SAME select as the read is not exempt, because SQL cannot see a sibling alias.
  ⭐⭐ **THE RULE THIS LEAVES: a fix that removes a false positive can install a false negative, and
  only re-proving the ORIGINAL defect still goes red will tell you.** That has now happened twice in
  two batches, which is the strongest argument yet that the resolver must be HARDENED before it is
  ever considered as a committed gate.

  ⚠ **THE SUBSTRING HAZARD RUNS THE OTHER WAY HERE**, and step 3 recorded it: a careless sweep of
  `pass_accuracy_pct` turns the team's `passes_accuracy_pct` into `passes_accuracy_pct_pct`.
  Maximal-token matching prevents it; the protected-count guard proves it.

  ⚠⚠ **THE DOC-BLOCK COUNT RISES 173 → 175, AND MY PREDICTION OF A FALL WAS WRONG. RECORDED AS A
  MISS RATHER THAN QUIETLY RESTATED.** I predicted 171, reasoning only about orphans. The measured
  delta is −2 +4:
    · **−2, as predicted:** `passes_total_sum_season__player` and
      `passes_accurate_sum_season__player` stop being emitted. They existed only because `_derived()`
      decomposes a TEAM column onto a player-only stem, and they were referenced by nothing — the
      same shape `!125` predicted for `shots_on_goal_sum_season__player`.
    · **+4, NOT predicted, and it is a direct consequence of the new CPO ruling:**
      `passes_key_player_this_season__player` and its three siblings. The four yoy columns were
      previously `key_passes_*`, which decomposes onto `key_passes` — **not a player metric_id** —
      so the generator emitted no block and those four columns were undocumented. Renamed to
      `passes_key_player_*` they decompose onto a real player metric, so blocks now exist.
  ⚠⚠ **AND I OVERSTATED THAT ONCE BEFORE CHECKING IT, so the corrected version is the one that
  stands.** My first wording called this "a documentation side effect that is an improvement —
  four columns that carried no description can now carry one." **Measured: all four new blocks are
  ORPHANS** — `git grep "doc('passes_key_player_this_season__player')"` and its three siblings
  return **zero references**, exactly like the two that disappeared (checked at the base: also
  zero). Nothing gained a description. The honest statement is narrower: **two orphan blocks are
  replaced by four orphan blocks.**
  ⭐ It does NOT move the description count — measured at **1604, identical to the base** — because
  the four yml column entries still carry no `description:` line of their own. "Docs blocks
  resolved" moves 235 → 237.
  ⚠ Wiring descriptions onto those four columns would be scope creep on a rename, and blank
  descriptions are already tracked as **#82**. Flagged, not folded in.
  ⭐ THE LESSON, and it is the same one `!128` cost two rounds for: **I reasoned about the half of
  the mechanism I had seen before (orphans disappearing) and not about the half this batch
  introduced (a rename making a previously-undocumentable column documentable).** A predicted number
  is a claim; when it misses, the miss is the finding.

  THRESHOLD DECLARATIONS. NEW MECHANISM: none in the shipped tree — the resolver remains a scratchpad
  tool. RECURRING COST: none. NEW DEPENDENCY: none.

decisions_reserved:
  - none NEW on naming beyond the ruling quoted in `refs`, which was taken before any code was
    written and is recorded with what it answered.
  - ⭐ **CARRIED: should the column-reference resolver become a committed CI gate?** `!128` changed
    the shape of this question rather than only adding evidence: the resolver had a false-positive
    class that fired on a correct `main`, so the honest form is now **"harden, then commit?"**
  - ⚠ CARRIED FORWARD: **#96**, now EIGHT reproductions and the widest exposure yet — three lists,
    seven entries.
  - ⚠ CARRIED FORWARD: `_LEADERBOARD_METRICS` / `_LB_KEEP` pinned by NO test, independently
    confirmed by `platform-reviewer` on `!127` and `!128`. This MR moves four more of those literals.
  - ⚠ CARRIED FORWARD: **#99**, the export's literal `goals`/`assists` read keys — MR 7's.
  - ⚠ CARRIED FORWARD: **#98**; the doc-block inheritance trap; and the `03_player_profile.md`
    two-names-one-stat documentation gap `bi-analyst-reviewer` ruled acceptable on `!128`.

done_when:
  - `sync_metric_docs_blocks.py --check` passes after regeneration, with the block-count delta **measured and reconciled term by term**: 173 → 175, being −2 orphans (predicted) and +4 newly-documentable yoy columns (NOT predicted — see `decisions_taken`).
  - `check_description_hygiene.py`, `check_layer_contract.py` pass, `dbt parse` is clean, and the description count reads **1604** — identical to the base.
  - The resolver reports zero broken references, and was watched going RED on a reproduction of the `!125` round-2 defect.
  - `python -m pytest -q` matches the `1cf0d40` baseline.
  - `sqlfluff lint` on every changed model, FROM THE REPO ROOT, UNPIPED, proved byte-identical to a re-lint of the stashed base.
  - `npm test` green, the two mutations watched going RED, and the site built TWICE at 12 rows / 7 headings, unchanged in all three locales — with `passes_key_per_match` intact in all four protected frontend files and `types.ts` moved.
  - All six `accepted_values` lists read by eye: the three that change named, and `passes_per90` asserted still present in both player lists.
  - ⚠ `check_ui_i18n_metrics.py` is run because it is a real CI gate, but it is **NOT evidence** for this MR — it validates only the frozen `site/**` tree this branch never touches. Recorded on `!128` by `platform-reviewer`.
