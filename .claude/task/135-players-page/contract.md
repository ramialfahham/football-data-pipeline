# Task contract — the Players page and the nation pages

objective: >
  Issue #135: build the Players page at /{locale}/players/ (World's best, then Players by nation)
  and one page per nation with more players than the Players page shows, at
  /{locale}/players/{nation}/, to the approved design and its amendment for nation pages.

refs: >
  #135 "The approved design" (approved in chat, 2026-11-09) and note 4199794512 (nation pages,
  approved in chat, 2026-11-10); the acceptance criteria, words, SEO texts and the two protected
  edits below approved in chat, 2026-11-10. Data from mart_player_index (!415). Plan ruled by the
  coordinating session on 2026-11-10.

scope_paths:
  - dbt_project/models/5_marts/shared/mart_player_index.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_player_index_hub_flags_follow_the_rule.sql
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - .gitlab-ci.yml
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - tests/fixtures/component_registry/baseline.json
  - docs/site_architecture.md
  - site_v2/src/i18n/strings.ts
  - site_v2/src/pages/*players*.astro
  - site_v2/src/components/player/PlayerIndex.astro
  - site_v2/src/components/player/PlayerIndexRow.astro
  - site_v2/src/components/competitions/FilterRows.astro
  - site_v2/src/lib/playerIndex.mjs
  - site_v2/src/lib/playerIndex.test.mjs
  - site_v2/src/lib/types.ts
  - site_v2/src/lib/menu.ts
  - site_v2/src/styles/system.css
  - site_v2/src/specs/players/index.spec.json
  - site_v2/src/specs/players/nation.spec.json
  - site_v2/src/specs/page-spec.schema.json
  - site_v2/scripts/check-page-specs.mjs
  - site_v2/scripts/audit-seo.mjs
  - site_v2/scripts/audit-seo.test.mjs
  - site_v2/src/data/players_index.json
  - site_v2/src/data/README.md
  - .gitignore
  - .claude/task/135-players-page/contract.md
  - .claude/task/135-players-page/review.md
  - .claude/task/135-players-page/review_input.patch
  - .claude/task/135-players-page/acceptance_evidence.md
  - .claude/task/135-players-page/rendered_page_evidence.md

protected_override: >
  .gitlab-ci.yml (players_index in the deploy export list) and docs/design/components.yml (the
  fold control used as a link, and the Players page and nation pages in the used-on lists of the
  components they use): approved in chat, 2026-11-10.

impact_map: >
  writers: dbt only on the warehouse side. mart_player_index gains nation_slug, is_hub_shown,
  is_hub_shown_in_position and has_nation_page; no other model changes.
  lineage: `dbt ls --resource-type model --select mart_player_index+` returns
  mart_player_index alone: a leaf.
  consumption: export_site_data.py fetch_player_index reads the four new columns into
  players_index.json; no other export file changes. The deploy job's export list
  (.gitlab-ci.yml) gains players_index, so the deployed site gets the file. The site reads it at
  build time for the Players page and the nation pages.
  protected_paths: .gitlab-ci.yml is fired by every pipeline; the one change adds an entity to the
  deploy export command, which only adds a file to the export; a wrong entity name fails the
  deploy export job loudly. docs/design/components.yml is read by check_component_registry.py and
  design_inventory.py; the change adds a part (the fold control as a link) and used-on entries;
  a wrong entry fails validate:ui.
  ci_layer_rules: check_layer_contract.py, check_description_hygiene.py,
  check_relationships_coverage.py, check-page-specs.mjs, audit-seo.mjs, check-term-list,
  check_page_css.py, check_component_registry.py.
  deploy_order: one merge; the nightly builds the columns; deploy:site-v2 is manual and builds
  from the export.
  blast_radius: four new mart columns; one export file gains four fields; 3 new hub pages and
  about 303 nation pages; the menu's and the footer's Players item and the Player page's
  breadcrumb level become links.

approved_design:
  - players: #135

decisions_taken: >
  The approved design of #135 with note 4199794512, and the coordinating session's rulings of
  2026-11-10: the warehouse serves which rows the Players page shows and which nations have a page
  (is_hub_shown, is_hub_shown_in_position, has_nation_page), and the nation slug
  (dim_country.country_key); the group of players with no nation recorded shows its first 10, with
  no link and no page; nation pages sit beside the player pages under the players word, and a slug
  clash is stopped three ways (a dbt test that a nation slug is letters and hyphens only, the
  nation route refusing a slug a player page uses, a node test); each player renders once on the
  Players page, tagged with the views he shows in. The "Show less stays pinned" fold rule is its
  own later MR. No new mechanism, no recurring cost.

decisions_reserved:
  - none: the design, the words, the SEO texts and the acceptance criteria are CPO-approved
    (approved in chat, 2026-11-10) and this builds them unchanged.

acceptance_criteria:
  - In EN, DE and FI, the Players page is at /{locale}/players/ (DE /de/spieler/, FI /fi/pelaajat/) and shows World's best, then Players by nation.
  - World's best shows this year's Ballon d'Or nominees in the Forwards, Midfielders and Defenders lists and the Yashin Trophy nominees in the Goalkeepers list, each list ordered by the player's current club in the Top clubs order; every nominee with a Player page shows, with no fold.
  - In Players by nation, each nation shows its national team's regulars, then its 10 leading club players, then "Show all {n}" linking to the nation's page. A nation with no more players than that shows them all, with no link.
  - The group of players with no nation recorded comes last, shows its first 10 players, and has no link and no page.
  - Choosing a position keeps, in each nation, that position's regulars plus its 10 leading club players of that position, with the position's count; a nation with none hides. Choosing a region keeps that region's nations.
  - Each nation with more players than the Players page shows has its own page at /{locale}/players/{nation}/ (for example /en/players/spain/), with the breadcrumb Home › Players › {nation}, the nation's name as heading, every player of the nation in the same order, and the position filter. The nation's heading on the Players page and its "Show all" link both open it.
  - No nation page has the same address as a player page, and the build fails if one ever would.
  - The menu's Players item, the footer's Players item and the "Players" level of a Player page's breadcrumb link to the Players page.
  - At 280, 360, 375, 700 and 1010px, in EN, DE and FI, no page scrolls sideways, no name is cut off, and the filters show as buttons when they fit on one line and as dropdowns otherwise.

done_when:
  - dbt parse, the layer, description and relationships checks pass; the new dbt test passes on the CI build.
  - python -m pytest tests -q is green.
  - npm test and the site build (check-page-specs, audit-seo) pass in site_v2 on the committed sample.
  - validate:ui's checks pass locally (check_page_css.py, check_component_registry.py).
  - acceptance_evidence.md demonstrates every criterion from the built pages.
  - CI is green after !419 is merged into this branch.

amendments:
  - 2026-11-10: page paths written as `site_v2/src/pages/*players*.astro`, because the gate reads `[lang]` as a character class; + docs/wireframes/block_standard.md, tests/fixtures/component_registry/baseline.json — authority: the components.yml edit approved in chat, 2026-11-10 (the block standard's element table is generated from the registry, and its baseline pins the registry's counts); content: regenerated by check_component_registry.py, no hand edit.
  - 2026-11-10: + site_v2/src/specs/page-spec.schema.json, site_v2/scripts/check-page-specs.mjs — authority: the two approved pages need a spec each (the spec checker refuses a page without one); content: the page entities "playerIndex" and "nation" added to the schema's enum and the checker's set, which a test keeps equal.
  - 2026-11-10: + site_v2/scripts/audit-seo.mjs, site_v2/scripts/audit-seo.test.mjs — authority: the approved address /{locale}/players/{nation}/ beside the player pages (#135 note 4199794512); content: the SEO audit matches a `[player]` segment only to a slug ending in its id and a `[nation]` segment only to letters and hyphens, so the two specs never claim one URL; a test pins both shapes.
