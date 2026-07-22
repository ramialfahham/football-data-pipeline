# Task contract — carry two shots-on-target metrics through to the marts

> Written on a CLEAN tree (branch `feat/sot-metrics-into-marts` off main @ 341a29c).
> CPO-approved via ExitPlanMode 2026-07-22 against a plan naming every file below.
> See [[feedback-metric-catalogue-governance]] [[feedback-metric-calc-layer-placement]].

objective: >
  Two catalogued team metrics are computed in the intermediate layer and never reach a mart, so the
  frontend cannot read them: `shots_on_goal_against_per_match` (shots on target conceded per match)
  and `sot_difference` (the difference between a team's own and its opponent's, per match).

  WHY THIS TASK EXISTS AND WHY IT COMES FIRST. The approved team-page mock displays both. My
  previous plan proposed hand-writing them into a committed sample file so the page would look
  finished while the chain stayed broken. That violates the binding rule in
  `docs/wireframes/00_overview.md`, titled "the whole point": a block may reference ONLY fields that
  exist in today's exported data, and anything missing goes to the gaps register and is NEVER
  SILENTLY DRAWN. The CPO caught it. The architecture is metric layer -> mart -> frontend, and the
  fix is to repair the broken link, not to route around it.

  The work is small because nothing needs deriving. Both metrics already exist, correctly
  coverage-gated. They stop at two hard-coded enumerations that were never extended.

  Also renames `sot_difference` -> `sot_difference_per_match`. CPO naming rule 2026-07-18: a
  per-match metric carries the suffix. Doing it now, BEFORE the name reaches the export and the
  frontend, is strictly cheaper than after.

refs: >
  Verified this session at source and against live BigQuery, not recalled:
  - `int_team_season__metrics_cumulative.sql` computes `shots_on_goal_against_per_match` (line 116,
    gated on `games_with_opp_sot_stats < games_played`) and `sot_difference` (line 121, gated on
    BOTH the for and against coverage counters). `int_team_season__metrics.sql` is a final-row
    projection of it (`sf.* except (match_number)`), so both already flow through untouched.
  - Both are CATALOGUED: `metric_catalogue.csv` rows 75 and 76.
  - The break is two enumerations. `int_team_competition_benchmark_metrics_long.sql` unpivots a
    hard-coded list of exactly 20 metric names; neither is in it. `mart_team_profile.sql` selects
    columns explicitly and takes `shots_on_goal_per_match` (line 103) but neither of these two.
  - CONFIRMED IN BIGQUERY (dataset `marts`, NOT `dbt_analytics` — my first query looked in the
    wrong dataset and wrongly concluded the data was missing entirely): `mart_team_profile` has
    `shots_on_goal_per_match` and `sot_rank_gap` but no column for either metric; the benchmark
    mart returns exactly 20 distinct `metric_key` values for PL 2025 and neither is among them.
  - THE RENAME IS SAFE FROM THE INCREMENTAL TRAP: `int_team_season__metrics_cumulative` is
    `materialized='table'`, not incremental, so this is NOT the case where renaming a column NULLs
    history without `--full-refresh` ([[reference-incremental-rename-full-refresh]]).
  - THE EXPORT NEEDS NO CHANGE: `shape_team_payload` passes profile rows through `_strip_identity`
    and carries every remaining column; the benchmark mart is keyed by `metric_key` as ROWS, so new
    metrics arrive as extra rows. Read from the code, and `done_when` proves it by running the
    export rather than trusting the reading.
  - A stale compiled artifact `target/.../team_profile_sot_difference_sane.sql` dated 24 June
    suggests this column once was, or was once intended to be, on the profile mart. No such test
    exists in any current `.yml`. Noted so a reviewer does not mistake the artifact for a live test.

impact_map: >
  writers: no raw writer, no ingestion. The only computed change is two columns added to an
    existing SELECT and two names added to an existing UNPIVOT list, plus a rename of an existing
    column that is already computed.
  downstream: dbt CLI and SQLFluff are BROKEN LOCALLY (documented; confirmed again this session,
    `dbt --version` tracebacks) and the dbt MCP lineage server is not connected, so `dbt ls` output
    cannot be pasted. `target/manifest.json` is dated 2026-06-29 and does NOT contain
    `int_team_season__metrics_cumulative` at all, so it is STALE and is not relied on. Lineage is
    therefore traced from LIVE `ref()` grep, pasted here:
      ref('int_team_season__metrics_cumulative') <- int_team_profile__yoy, int_team_season__metrics
      ref('int_team_season__metrics')            <- int_team_competition_benchmark_metrics_long,
                                                    int_team_season__deserved_vs_actual,
                                                    mart_team_profile, mart_team_season,
                                                    mart_team_season_insights, mart_team_season_record
      ref('int_team_competition_benchmark_metrics_long') <- int_team_competition_benchmarks,
                                                            mart_team_competition_benchmarks
      ref('mart_team_profile')                   <- (nothing; it is a leaf)
    The stale manifest agrees on the two lists it can speak to, and recorded 117 tests downstream
    of `int_team_season__metrics`, which is the order of magnitude CI will re-run.
  layer_rules: intermediate composes, marts consume; no staging or base touched. The catalogue is
    the SSoT for metric identity, so the rename must move the seed row and the model column
    TOGETHER or the drift guard `assert_no_uncatalogued_season_metric` fails — which is the guard
    working, and `done_when` asserts it passes.
  deploy_order: `dbt_analytics` and the CI dataset are target-blind and SHARED
    ([[project-dbt-shared-ci-prod-datasets]]), so the PR's data build rewrites the same relations
    prod reads. The rename means the OLD column disappears and the new one appears in the same
    build; there is no window where a downstream model reads a name that does not exist, because
    every consumer is renamed in the same commit. Nothing is sequenced around the 04:00 nightly.
  blast_radius: THE FLAGSHIP READ IS THE RISK. `int_team_season__deserved_vs_actual` ranks teams by
    exactly this column to produce `deserved_rank` and `sot_rank_gap`, which is the team page's
    headline "have they earned it" answer. A botched rename would silently move that ranking rather
    than error. `done_when` therefore compares `deserved_rank` and `sot_rank_gap` for every team in
    a real league-season before and after. Two mart surfaces gain data: `mart_team_profile` gains
    two columns, `mart_team_competition_benchmarks` goes from 20 metric keys to 22. No existing
    number changes value. No frontend file, no page, no export code.

scope_paths:
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics_cumulative.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__deserved_vs_actual.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_team_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmarks.sql
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/mart_team_competition_benchmarks.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/docs/layering.md
  - dbt_project/seeds/metric_catalogue.csv

decisions_taken: >
  (1) The rename `sot_difference` -> `sot_difference_per_match`.
      AUTHORITY: **ESCALATED AND ANSWERED.** CPO, AskUserQuestion 2026-07-22: **"Yes, rename it
      now"**, to a discrete question naming the old and new identifier, stating that only the id
      and label key change, and offering three paths (rename now / leave it permanently / ship the
      plumbing and decide later). Recorded verbatim in `.claude/task/escalations.log`, which is the
      durable authority this rests on. Everything below is the history of how a weaker claim was
      refused, kept because the refusal was correct and the lesson is worth the lines.

      THE CLAIM I FIRST MADE, and why BOTH reviewers were right to refuse it. It said "the CPO ruled on 2026-07-18 that per-match metrics carry the
      suffix, and the handover records it as owed" — asserted, not quoted, and the reviewer
      searched the current handover, `escalations.log`, the engineering standards and the memory
      files and found nothing. It was right to refuse it.
      I THEN ARGUED the plan approval was itself sufficient, since the plan named the rename. The
      reviewer refused that too, and its reasoning is the part worth keeping: approving a bundled
      twelve-file plan whose text ASSERTS a rule as settled is a quote of my sentence, not of the
      CPO's. Every comparable naming ruling in `escalations.log` is a discrete question with his
      own words on that specific point. §10 also removes the "it is obviously right" escape hatch
      by saying naming is escalated "regardless of how obvious the answer seems" — and it IS
      obviously right, which made getting the real answer cheap rather than optional.
      THE CORROBORATING RECORD EXISTS BUT I DELETED IT. `git show 0ff5037:.claude/active_work.md`
      line 172 reads: "the deserved-vs-actual hero needs `sot_difference` renamed to
      `sot_difference_per_match` (per-match metrics must carry the suffix - CPO naming rule
      2026-07-18). The rename ripples: catalogue id + label key + the mart column +
      int_team_season__deserved_vs_actual + i18n." That line was in the handover on main until I
      rewrote the file THIS MORNING and dropped it. So the reviewer could not find it because I
      removed the only live copy — a real cost of that rewrite, recorded here rather than glossed.
      HONEST LIMIT: even that line is my own prior note asserting a ruling, not the CPO's quoted
      words — two self-authored assertions are one source counted twice. It corroborates nothing
      on its own. The authority is the quoted answer at the top of this entry, and nothing else.
      BANKED: a handover rewrite that drops "owed work" lines destroys the only live record of
      decisions not yet executed. Anything carried as owed must survive the rewrite, or be moved
      into `escalations.log` before the rewrite happens.
  (2) The whole change, file by file, was approved via ExitPlanMode on 2026-07-22, against a plan
      that stated the binding-rule violation it replaces and the order it restores.
  (3) Both metrics keep their EXISTING coverage gates unchanged. The formula is fixed mathematics
      and availability decides only whether a model can apply it
      ([[feedback-metric-formula-vs-availability]]) — this task moves columns, it does not touch a
      formula, a numerator, a denominator or a NULL rule.

decisions_reserved:
  - Adding these two metrics to the LOCKED display contract (`docs/wireframes/metrics_display.md`,
    a 16-row team table that excludes both) is a §10 display decision and is deliberately NOT in
    this task. It becomes legal only once the export carries them, which is what this change makes
    true. The approved mock shows both, so the CPO has effectively signalled the answer, but the
    locked doc is amended with the page work and with the display reviewer in the loop.
  - The `label_i18n_key` for the renamed metric, now `metrics.sot_difference_per_match.label`.
    Whether the German, English and Finnish label STRINGS change is a user-visible wording call
    and is not taken here. No i18n file is in scope.
    DEBT THIS TASK CREATES AND DEFERS, named by the football-analytics-expert reviewer: the NEW
    key has no entry in any i18n resource file — and neither did the OLD one, so nothing regresses
    and nothing renders this metric today. It is inert, but it is debt, and it must be resolved
    before either metric is displayed. That resolution belongs with the display decision below.

done_when:
  - CI `ci-data-build` green: `dbt build` over the touched models and their downstream (the local
    dbt and SQLFluff are broken, so CI is the gate).
  - The benchmark mart returns 22 distinct `metric_key` values for a real league-season instead of
    20, and BOTH new keys carry a rank and a median.
  - `mart_team_profile` exposes both new columns, non-null for a fully-covered league-season and
    NULL where opponent shots-on-target coverage is incomplete — proving the coverage gate survived
    the move rather than being silently dropped.
  - `deserved_rank` and `sot_rank_gap` are UNCHANGED for every team in a real league-season,
    compared before and after. This is the blast-radius check, not a formality.
  - `assert_no_uncatalogued_season_metric` passes, proving the renamed column and the renamed
    catalogue row agree.
  - `scripts/export_site_data.py` run for one team emits both fields with NO export code change.
  - `python scripts/check_layer_contract.py` passes.
  - ONE commit, pushed with an explicit refspec, PR opened. The CPO merges.

amendments:
  - 2026-07-22: + `dbt_project/models/5_marts/shared/mart_team_competition_benchmarks.sql`.
    AUTHORITY: none needed beyond the approved plan — this is the SAME edit the plan already
    describes ("document the new mart columns"), on a file I failed to list. The contract gate
    caught it, which is the gate working.
    CONTENT: that mart's header comment says the benchmark set is "the 20 team season metrics".
    Adding two metrics makes the sentence false. Its sibling
    `int_team_competition_benchmark_metrics_long.sql` carried the identical stale count and is
    already in scope. Leaving one of a matched pair stale is exactly the failure class the
    cto-reviewer found three rounds running in the guardrails PR earlier today: a count in a
    comment that stops being true the moment the list beneath it grows.
  - 2026-07-22: + `int_competition_benchmarks.yml`, + `int_team_competition_benchmarks.sql`,
    + `dbt_project/docs/layering.md`.
    AUTHORITY: none needed beyond the approved plan — same edit, more files. Found by searching
    for every place the metric set is pinned, after the gate caught the first miss.
    CONTENT: the benchmark metric set is enumerated or counted in SIX places, and my scoping
    found two of them. `int_competition_benchmarks.yml` carries TWO `accepted_values` tests
    listing all 20 keys (for `int_team_competition_benchmarks` and the long form) plus four
    "20-metric set" phrases; `int_team_competition_benchmarks.sql` and `layering.md` each carry
    the count in prose. Adding two metrics without these WOULD HAVE FAILED CI on the
    accepted_values tests — which is the guard working, and the reason to find them all before
    pushing rather than after.
    THE REAL LESSON, for the skill the CPO asked about: adding one team metric to the benchmark
    set touches SIX files across models, schemas and docs, and nothing enumerates that list. The
    skill's whole value is being that list.
