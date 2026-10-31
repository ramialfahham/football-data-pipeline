# Task contract — the Teams page

objective: >
  The Teams menu item leads to `/{lang}/teams/`, built as #133 approved it: the Filter bar, Top
  clubs, Top national teams, Clubs by country and National teams by region, in the block order
  the warehouse serves. The export writes `teams_index.json` from `mart_team_index`; the page
  groups and shows the served rows in the served orders and adds none of its own. The menu, the
  footer and the Team page breadcrumb link to it.

refs: >
  #222, the Teams menu page (build plan approved in chat, 2026-10-30; this MR's plan approved in
  chat, 2026-10-31); design #133; #223, the shared Filter bar, whose last page this is.

scope_paths:
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - .gitlab-ci.yml
  - site_v2/src/data/teams_index.json
  - site_v2/src/data/README.md
  - site_v2/src/pages/*/*teams*/index.astro
  - site_v2/src/pages/*/*/?team?.astro
  - site_v2/src/components/teams/TeamIndex.astro
  - site_v2/src/lib/teamIndex.mjs
  - site_v2/src/lib/teamIndex.test.mjs
  - site_v2/src/lib/types.ts
  - site_v2/src/lib/menu.ts
  - site_v2/src/styles/system.css
  - site_v2/src/i18n/strings.ts
  - site_v2/src/specs/teams/index.spec.json
  - site_v2/src/specs/page-spec.schema.json
  - site_v2/scripts/check-page-specs.mjs
  - docs/site_architecture.md
  - docs/wireframes/block_standard.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

protected_override: >
  .gitlab-ci.yml, job deploy:export only: `teams_index` added to its `--entities` list; nothing
  else in the file changes. The plan naming this edit approved in chat, 2026-10-31.

impact_map: >
  No dbt model changes. The export gains one file, `teams_index.json`, read from
  `mart_team_index` joined to the `confederations` seed for each region's `region_rank`; it is
  added to the deploy export's `--entities`. `.venv/Scripts/dbt.exe ls --project-dir dbt_project
  --select mart_team_index+ --resource-type model` lists only mart_team_index: nothing in the
  warehouse reads it, and this MR adds the export as its one reader.
  blast_radius: one new page per locale (3); the menu, drawer and footer item Teams becomes a link
  on every page; the Team page breadcrumb's "Teams" becomes a link. No existing page's data
  changes.

approved_design:
  - teams: #133
  - team: #134

acceptance_criteria:
  - "`/{lang}/teams/` renders in EN, DE and FI: breadcrumb Home › Teams, heading Teams, the Filter bar (type and region, no World), then the list; the menu, footer and Team page breadcrumb link to it."
  - "Top clubs: Europe's top 10 shown; under the fold Europe 11–20, then each other region's top 6 under its name; a region filter shows that region's own list (Europe 10, others 6)."
  - "Top national teams: the world's top 10 shown, 11–20 under the fold; a region filter shows that region's top 10, the rest under the fold."
  - "Clubs by country: one group per country with its team count, in the served country order; inside, each covered league under a heading linking to its competition page, then Other clubs, in the served order; 6 shown, the rest under the fold."
  - "National teams by region: one group per region with its team count, in the served order; hidden under a region filter."
  - "Filters: rows, headings, folds, groups and blocks with nothing left hide together; fold counts are the rows the filter leaves."
  - "Block order: national teams first when the warehouse's national_teams_first is true, clubs first otherwise."
  - "Every row links to its team's page when that page is built; every order shown is the warehouse's."

decisions_taken: >
  The plan approved in chat, 2026-10-31, with its decisions: teams sharing a place are listed A to
  Z inside it, ordered in the export; country and region groups use the existing group head with
  the team count at its right; inside a country, the clubs outside the covered leagues follow
  under "Other clubs"; the copy of the four block names, the team count, "Other clubs" and the
  SEO title and text in EN, DE and FI. Readings of #133: a club in Clubs by country is filtered by
  its country's region, so a country group stays whole; country names are shown as served, as on
  the Team page.

decisions_reserved:
  - "none: every decision of this task is approved, see decisions_taken and amendments"

done_when:
  - pytest, the offline gates, the copy gate and the new node tests pass.
  - "`npm run build` in site_v2 passes, including the SEO audit and the built-pages check."
  - The page is read in the v2 dev server in EN, DE and FI at 280–1010px across the filter combinations.

amendments:
  - "Approved in chat, 2026-10-31: the page kind teamIndex added to the page spec schema and its checker; the export query's bytes (about 0.46 MB, billed 10 MB per table) and its two runs, the second adding each region's name key; the exact text of the site_architecture.md, block_standard.md and data README changes."
  - "Approved in chat, 2026-10-31: the whole export (1.8 MB) is over the repo's 1,024 KB file limit, so the committed sample keeps the export's rows unchanged but only every national team, every club in a covered league and every ranked club (778 rows, 410 KB); the data README says so."
