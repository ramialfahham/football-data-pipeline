# Task contract — the club Team page as approved, on the parts library

objective: >
  Issue #250 and #243 step 5, first page group: every club's Team page shows the design approved
  on #250 (6 Nov 2026 and the notes after it), built from the parts library. This season (six
  cards over all the club's competitions) above the tabs; Overview with Competitions one line
  each, Next matches before Recent matches, the Player page's result row; Performance without the
  tab explainer and the Standing block; Deserved points led by its competition; Compared with
  other teams with a choice of the league and each international competition that has a table
  phase, the median on every strip, no card row; Compared with last season over this season so
  far against the whole of last season, all competitions, per match, from the first match, no
  card row. National team pages keep today's page; their redesign is its own page group.

refs: >
  #250 (notes 4178375624, 4178573544 of 6 Nov; 4254003834 explainers and 4253950937 cards of
  17 Nov; 4264380396 metrics_display.md of 18 Nov), #253 (cards are counts), #254, #255, #230,
  #231, #243 (parts library, one form per part). The same-N year-over-year chain and rule R6 are
  retired in the next merge request.

scope_paths:
  - .claude/task/250-team-page-build/
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/5_marts/shared/mart_team_competition_benchmarks.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/tests/assert_team_benchmark_round_stage_kind_follows_the_phase.sql
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - site_v2/src/pages/[[]lang]/[[]teams]/[[]team].astro
  - site_v2/src/components/team/*.astro
  - site_v2/src/components/player/PlayerComparison.astro
  - site_v2/src/components/player/PlayerLastSeason.astro
  - site_v2/src/components/fixture/RecentMatch.astro
  - site_v2/src/components/ui/*.astro
  - site_v2/src/lib/*.ts
  - site_v2/src/lib/*.mjs
  - site_v2/src/i18n/strings.ts
  - site_v2/src/styles/system.css
  - site_v2/src/specs/teams/team.spec.json
  - site_v2/src/data/teams/*.json
  - site_v2/scripts/*.mjs
  - tests/test_check_chart_components.py
  - scripts/check_chart_screenshots.py
  - docs/wireframes/02_team_profile.md
  - docs/wireframes/metrics_display.md
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - design-mocks/README.md
  - design-mocks/renders/team-page_2026-11-06_01.html
  - design-mocks/renders/team-page_2026-11-06_02.html
  - design-mocks/renders/team-page_2026-11-06_03.html
  - scripts/parts_page.py
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/chart_screenshots/*
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json

protected_override: >
  docs/design/components.yml: the parts this page's approved design names. The strip plot becomes
  one component (`ui/StripPlot.astro`) with the median on every page and lists the Player page;
  the last-season table becomes one component (`ui/LastSeasonTable.astro`) for the Team and
  Player pages, its trend empty when either season has no value (#255); the table's file list
  takes the last-season table component; the card block lists the Team page; the chart's tick
  label drops the strip plot's direction note, which no page draws any more. The Team page
  design approved in chat, 6 Nov 2026 (#250 note 4178573544: "the registry's Strip plot gains
  the median and lists the Player page"), the approved text of #255, and the component-library
  step of #243 approved in chat,
  17 Nov 2026; visual details are the coordinating agent's under docs/design/design_standard.md,
  approved in chat, 16 Nov 2026.

impact_map: >
  writers: int_team_competition_benchmark_metrics_long gains `round_stage_kind`, the existing
  round kind of int_round_names ('table' for a competition-season benchmarked over its table
  rounds, int_team_competition_phase__metrics; NULL where every match counts), carried by
  mart_team_competition_benchmarks; no value, rank, pool or row changes. scripts/export_site_data.py
  reads marts.mart_team_page_window_metrics (served by !424, not exported until now) into each
  club's payload and attaches the strip plot to each this-season competition benchmarked over its
  table phase, besides the featured league.
  downstream: `dbt ls --select int_team_competition_benchmark_metrics_long+ --resource-type model`
  -> int_team_competition_benchmark_metrics_long, int_team_competition_benchmarks,
  mart_team_competition_benchmarks. int_team_competition_benchmarks aggregates by
  (league_code, season_api_year, metric_key) and does not read the new column. The mart's readers:
  the export (team payloads), assert_team_benchmark_rank_follows_direction,
  assert_team_benchmark_international_pool_is_the_league_phase,
  assert_team_benchmark_prev_season_matches_yoy, assert_player_stat_corrections_within_limit
  (none selects the new column by name).
  guard: docs/design/components.yml is read by scripts/check_component_registry.py,
  scripts/check_design_inventory.py, scripts/design_inventory.py, scripts/parts_page.py and
  site_v2/scripts/check-term-list.test.mjs; a wrong entry fails the registry or design check.
  layer_rules: one new column in an intermediate and a mart, both under the materialisation rule
  of dbt_project/docs/layering.md, enforced by scripts/check_layer_contract.py; no partition or
  cluster key.
  deploy_order: the column lands with the nightly build after merge; the export that reads it
  runs at deploy, which is manual and follows data:build:main.
  blast_radius: every club's Team page (about 3,100 pages per language); national team pages keep
  their blocks. Measured sizes before and after are in acceptance_evidence.md.

acceptance_criteria:
  - The Team page's "Compared with last season" compares this season so far against the whole of last season, across all competitions.
  - The block shows from the team's first match of the season, without a minimum.
  - The explainer gives the matches on both sides, says the values are per match, and says that early in the season a few matches can swing them. Its text is approved before the build, following the player page's approved wording on #136.
  - On every club Team page of the committed sample, This season stands above the tab bar with six cards (Matches, Wins, Goals, Goals against, Yellow cards, Red cards) and the explainer of #250 note 4254003834 listing the season's competitions, in EN, DE and FI.
  - Overview shows Competitions one line per competition, then Next matches, then Recent matches, then Highs and lows and Squad; Recent matches and the Matches tab's Results use the Player page's result row.
  - Performance has no tab explainer and no Standing block; Deserved points' explainer opens with "{competition} {season} only." (DE "Nur …", FI "Vain …").
  - Compared with other teams offers the featured league and each this-season international competition benchmarked over its table phase, shows the median on every strip, has no Yellow cards or Red cards row, and its explainer is note 4254003834's for the chosen competition.
  - Compared with last season shows this season against the whole of last season from mart_team_page_window_metrics, from the first match, with note 4254003834's explainer ("1 match" / "1 Spiel" / "1 ottelu" for one), no card row, and an empty trend where either season has no value; it is absent when last season has no value.
  - Every national team page renders the same blocks, in the same order, with the same text as before; its strip plot takes the part's standard form (the median, no "better →" marks), per #250 note 4178375624.
  - The Player page's comparison and last-season blocks render from the shared parts with no change in what they show.
  - Every Team page passes the design check, and none breaks or scrolls sideways at 280, 320, 360, 375, 700 and 768px in EN, DE and FI.

criteria_confirmed: >
  Confirmed by the coordinating session, 2026-11-18, against #250 notes 4178573544, 4178375624,
  4254003834; the CPO's go on #243 step 5 is the Confirm.

approved_design:
  - team: #134
  - player: #136

depends_on:
  - none: !479 is merged (main de65e45a)

shared_files:
  - docs/design/components.yml
  - site_v2/src/styles/system.css
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/types.ts
  - scripts/export_site_data.py
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/chart_screenshots/*

decisions_taken: >
  A club page is one whose payload carries `this_season` (mart_team_page_window_metrics serves
  clubs only); a national team's page keeps today's blocks. The comparison tables leave out the
  card metrics (#253). The strip plot and the last-season table become one component each, used
  by the Team and Player pages. `round_stage_kind` on the benchmarks names, in the warehouse's
  existing vocabulary, the rounds a competition-season is benchmarked over, so the export selects
  the competitions by a served column. The same-N chain and rule R6 retire
  in the next merge request, since retiring them touches core documents with their own approval.
  Engineering and visual calls by the coordinating agent and the builder under
  docs/design/design_standard.md. No new mechanism, dependency or recurring cost beyond the
  measured export and page sizes.

decisions_reserved:
  - Any wording not in #250's approved notes: the coordinating session.
  - docs/wireframes/02_team_profile.md restates the approved design: a plain yes/no from the CPO through the coordinating session.

done_when:
  - The before/after capture of every Team page, player page and match page of the sample shows only the approved changes; every difference listed.
  - dist and export size before and after measured and reported.
  - python scripts/check_component_registry.py passes; pins do not rise.
  - Full pytest and the site's node tests pass.
  - python scripts/ci_local.py --mr is green; the MR's data build passes.

amendments: >
  tests/test_check_chart_components.py names every chart component; ui/StripPlot.astro is a new
  one, so the list gains it. The built-page check (site_v2/scripts/check-built-pages.mjs) reads
  each strip panel's rank against that panel's competition (`data-league`), as the page now
  shows more than one. #254 (equal tab widths on every tab bar) stays out: it changes the
  Competition and Player pages, which criterion 10 keeps unchanged. Engineering calls of the
  builder under docs/design/design_standard.md (mandate approved in chat, 16 Nov 2026),
  18 Nov 2026.
  Review round 1: a singular test pins `round_stage_kind` to int_team_competition_phase__metrics
  (table exactly where the phase model supplies the season, NULL elsewhere), since
  accepted_values passes on an all-NULL column; protected_override names only the
  components.yml edits made. Same mandate, 18 Nov 2026.
  Local CI: scripts/check_chart_screenshots.py checks the Team page strip's other-team marks as
  the SVG circles (`.rs-band .rs-peers circle`, fill) the shared strip draws, and the Team page
  chart screenshot pins are retaken in CI's Linux image for the new layout. Same mandate,
  18 Nov 2026.
