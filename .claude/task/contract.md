# Task contract — the Team page, built to its approved design

objective: >
  Build the Team page as approved on #134: three tabs, Overview, Matches and Performance, on the
  team's featured season, with copy in EN, DE and FI. The team export carries the team's full
  schedule so the Matches tab and the match links can be built, the 34 committed team samples are
  re-exported with it, and the documents that describe the old page are corrected to the design.

refs: >
  #235 (MR 2 of 2; the plan approved in chat, 2026-10-30, with its decisions recorded on #235);
  design #134 (notes 2026-10-17 to 2026-10-28, mock team.html in snippet 6069923); the shared
  Filter bar #223; the metric names #226.

scope_paths:
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - tests/test_design_inventory.py
  - tests/test_governance_hooks.py
  - tests/test_sentence_length_in_docs.py
  - tests/test_no_decision_history_in_docs.py
  - tests/test_no_decision_history_in_code.py
  - scripts/check_design_inventory.py
  - site_v2/src/pages/?lang?/?teams?/?team?.astro
  - site_v2/src/components/team/*
  - site_v2/src/components/ui/*
  - site_v2/src/components/competitions/FilterRows.astro
  - site_v2/src/components/fixture/RecentMatch.astro
  - site_v2/src/lib/*
  - site_v2/src/i18n/strings.ts
  - site_v2/src/styles/system.css
  - site_v2/src/specs/teams/team.spec.json
  - site_v2/src/data/teams/*.json
  - site_v2/src/data/README.md
  - site_v2/scripts/*
  - docs/wireframes/02_team_profile.md
  - docs/content_architecture.md
  - docs/wireframes/metrics_display.md
  - docs/wireframes/12_player_stats.md
  - .gitignore
  - docs/wireframes/00_overview.md
  - docs/wireframes/11_team_squad.md
  - docs/wireframes/14_team_stats.md
  - docs/wireframes/block_standard.md
  - design-mocks/gen_team_mock.py
  - design-mocks/README.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: scripts/export_site_data.py, the only writer of the team payload (fetch_team_payloads,
  shape_team_payload). It reads mart_team_fixtures; no dbt model, seed or mart changes. Lineage
  pasted from `.venv/Scripts/dbt.exe ls --project-dir dbt_project --select mart_team_fixtures+
  --resource-type model --output name`: "mart_team_fixtures" (no downstream model). Its tests are
  unchanged (team_fixtures_ranks_positive, team_fixtures_recency_has_result,
  team_fixtures_result_present and the two dim_team relationships). downstream: the team payload
  site_v2/src/data/teams/*.json, read by pages/[lang]/[teams]/[team].astro (one page per file and
  locale); the match page links a team only by its slug, which does not change.
  layer_rules: the export selects the mart's rows and ranks (upcoming_rank, recency_rank) and
  derives nothing; the page renders what it is served (layering.md, Consumption layer).
  deploy_order: none; the export runs in deploy:export, and deploy:site-v2 replaces the committed
  sample with the full export. blast_radius: the team payload gains a schedule key (every upcoming
  match and every result of the featured season's year, with the match id); every team page
  changes to the approved design. The 34 committed samples are re-exported once from prod, about
  310 MB read, same files and slugs. No published number changes meaning.
  cost per export run: the team export also reads core.dim_competition_season (about 11 KB, billed
  10 MB). The wider mart_team_fixtures filter reads no more bytes: the table is read whole either
  way (about 21 MB). The export runs only in deploy:export, started by hand; no schedule runs it.

approved_design:
  - team: #134

acceptance_criteria:
  - "Three tabs, **Overview · Matches · Performance**, on the page's one season (the featured season, `is_featured_season`); only the blocks that look ahead show what comes next."
  - "**Overview:** Competitions (standing, or the cup round with Through / Knocked out / Winners), Recent matches, Next matches, Highs and lows, Squad (by position, the approved second line)."
  - "**Matches:** the shared Filter bar (#223), Upcoming by competition, Results newest first."
  - "**Performance:** the tab's explainer, Standing, Deserved points (table and chart), Compared with the league (strip plot), Compared with last season (table with Trend), the key metrics with \"Show all metrics\". The \"Metric Glossary ›\" link at the end of each metric block's intro follows #168, which settles its address and copy."
  - "Copy in EN, DE and FI as approved on #134; metric names from the catalogue only (#226)."
  - "The documents that describe the old page are corrected to the design: `02_team_profile.md`, the screen inventory's Squad and Stats rows, and the mock's generator enters `design-mocks/`."

decisions_taken: >
  The plan approved in chat, 2026-10-30: the schedule export and the re-export of the 34 team
  samples are in this MR; no glossary link until #168; the squad line uses count phrases; the new
  copy recorded on #235 on 2026-10-30. Readings of approved rules: the page takes the site's
  960px width (legacyWidth goes, as for every approved page); squad, Next matches and Results rows
  link only to pages the build emits; Standing reads latest_rank and points_this_season, with
  points_rank_prev_season and points_prev_season as "Season before"; Next matches are the
  schedule rows with upcoming_rank 1, soonest first; the Filter bar gains a competition dimension
  with the "All competitions" copy approved on #223.

decisions_reserved:
  - The block standard's text for the new elements goes to the CPO before it is written.
  - Every changed sentence of the wireframes and design-mocks README goes to the CPO before it is written.
  - Any copy not approved on #134, #223, #226 or #235 goes to the CPO before it ships.

done_when:
  - The six acceptance criteria hold on the built page, shown in acceptance_evidence.md.
  - npm run build in site_v2 passes (prebuild tests, page specs, audit-seo); the whole pytest passes.
  - The MR's build:site-v2 and validate:ui pass.

amendments: >
  RecentMatch.astro joins the scope: the Matches tab's result rows carry the competition filter's
  mark on the row itself, inside the plan approved in chat, 2026-10-30.
  Where each reserved item was approved: the page copy on #134 (notes 2026-10-21 to 2026-10-28)
  and on #235 (note 2026-10-30); the filter label, the two re-exports, the mock generator as it is,
  the 02 wireframe, the screen inventory and census rows, the block standard rows and the
  design-mocks row, in chat, 2026-10-30. The content_architecture.md Team rows, the retirement
  notes of 11 and 14 and the strip plot sentence in metrics_display.md and 12_player_stats.md
  join the scope, approved in chat, 2026-10-30, so the documents match the approved design.
  .gitignore joins the scope for the generator's copied build assets (design-mocks/_astro/).
  The cross-competition order of the schedule moves to mart_team_fixtures in its own MR first
  (decided in chat, 2026-10-30); the export reads that order once it merges.
