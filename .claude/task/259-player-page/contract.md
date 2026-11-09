# Task contract — the Player page: both tabs on the site

objective: >
  Issue #259, step 3. The Player page replaces its stub with the Club and National team tabs of the
  approved design (#136), read from the payload the export writes, with sample data for the players
  the boards link to. Every row of Players to watch links to the player's page when this build makes
  one, and `players` joins the deploy export.

refs: >
  #259, plan approved in chat 2026-11-06. Design: #136, its cards rule approved in chat 2026-11-06.
  Data: !387.

scope_paths:
  - site_v2/src/pages/*player*.astro
  - site_v2/src/pages/*fixture*.astro
  - site_v2/src/components/player/*
  - site_v2/src/components/fixture/PlayerRow.astro
  - site_v2/src/components/competition/RankingBoard.astro
  - site_v2/src/components/ui/*
  - site_v2/src/components/competitions/*
  - site_v2/src/lib/*
  - site_v2/src/styles/system.css
  - site_v2/src/i18n/strings.ts
  - site_v2/src/specs/players/player.spec.json
  - site_v2/src/config/indexability.mjs
  - site_v2/src/data/players/*
  - site_v2/src/data/player_peers/*
  - site_v2/src/data/player_metric_rows.json
  - site_v2/src/data/player_pages.json
  - site_v2/src/data/README.md
  - site_v2/scripts/*
  - .gitignore
  - .gitlab-ci.yml
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - docs/wireframes/00_overview.md
  - docs/wireframes/03_player_profile.md
  - docs/wireframes/12_player_stats.md
  - docs/wireframes/13_player_career.md
  - docs/site_architecture.md
  - docs/wireframes/metrics_display.md
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - scripts/check_page_css.py
  - scripts/check_copy_gate.py
  - tests/test_check_copy_gate.py
  - tests/fixtures/design_inventory/*
  - tests/fixtures/font_coverage/*
  - tests/test_no_decision_history_in_code.py
  - tests/test_no_decision_history_in_docs.py
  - tests/test_design_inventory.py
  - tests/test_check_chart_components.py
  - .claude/task/259-player-page/

protected_override: >
  docs/design/components.yml: the card and the chart parts of the Player page are registered, the
  card with its six-card rule. .gitlab-ci.yml, job deploy:export only: `players` joins its
  `--entities` list; nothing else in the file changes. The plan naming both edits approved in chat,
  2026-11-06; the cards rule approved in chat, 2026-11-06, on #136. tests/test_design_inventory.py,
  one line: the Player page leaves the list of pages that keep the earlier widths, because its
  design is approved (`00_overview.md`, "a page whose new design is not yet approved keeps the
  earlier widths"); the list is then empty. docs/design/components.yml also names the Player page in
  the Tab bar's files and used-on, and registers its Recent matches rows as Result row parts
  (approved in chat, 2026-11-09).

impact_map: >
  writers: none in the warehouse. scripts/export_site_data.py reads the set of players with a page
  from mart_player_profile's flag and writes player_pages.json; deploy:export now also runs its
  players entity. Reads marts only and writes no BigQuery table.
  lineage: `git diff --stat gitlab/main -- dbt_project/` is empty on this branch, so no lineage
  moves; the export selects mart_player_profile.shares_name_at_club, added by !404.
  consumption: the Player page reads site_v2/src/data/players/*.json, player_peers/** and
  player_metric_rows.json. builtPlayers.mjs reads player_pages.json. Every link to a player follows
  that list: the board rows, the squad rows and the match page's Players to watch rows, which gain a
  link. The shared parts of system.css, fitBlocks.mjs and filterBar.mjs
  serve the Team, Competition and match pages too, so their design counts are measured.
  ci_layer_rules: scripts/check_page_css.py, scripts/check_design_inventory.py,
  scripts/check_component_registry.py, audit-seo.mjs, check-exported-text.mjs.
  deploy_order: after !389, which serves the two card counts and the page flag, !391, !392, !393
  and !394, which align the shared last-season table, the strips and the tab to the registry, !395,
  which keeps hyphen-joined words whole and opens every tab in the design check, and !399, which
  counts a class the registry lists as known, and !404, which serves the shared-name flag. One
  merge.
  The next manual deploy runs the export with players, about 15,700 pages per language.
  blast_radius: the Player stub goes and with it the STUB_PAGES entry. INDEXABLE stays false. The Player
  pages arrive with no design gap, every tab measured, so no design pin rises.

approved_design:
  - player: #136
  - match: #132
  - home: #127
  - competition: #129

decisions_taken: >
  From the plan on #259. A player gets a page after 3 matches played this season or last (#259,
  note 4178916887, approved in chat, 2026-11-06), which replaces the board-based set. A player with
  no club match in our data has no Club tab, and the page opens on National team (approved in chat,
  2026-11-06). Where the approved title passes the audit's limit it takes a shorter form (approved
  in chat, 2026-11-06), then the shorter forms of #259. The page's new texts use the term table on
  #243, and check_copy_gate.py accepts a listed unit symbol that matches across languages (both
  approved in chat, 2026-11-06). Two locked files change, declared above (decision 3). "Metric Glossary ›" stays out until #168 (decision 5).
  Wireframes 03, 12 and 13 retire as 11 and 14 did: the file stays, with one line under its title,
  and its overview row changes, with text the CPO approves first (decision 6). The mock is the copy
  approved with the six-card rule. Two players of one name at one club get their position beside the
  club in the title; two players of one name keep the name as the heading (both approved in chat,
  2026-11-06). The registry is the standard: where the mock differs from a registered rule, the page
  follows the rule, with no page-only variant (approved in chat, 2026-11-07).

decisions_reserved: none.

done_when:
  - python -m pytest tests passes.
  - npm run build and the design check pass in site_v2.
  - Every criterion below is shown in the Browser pane at every listed width and language.

acceptance_criteria:
  - "The header shows photo, full name, position, club (linked), nation, age, height and season. A missing value drops with its separator."
  - "Club tab: This season, Next matches, Compared with other players, Compared with last season, Recent matches."
  - "National team tab: Current competitions, Next matches, Compared with other players, Recent matches, including the 0-minutes squad member case."
  - "Goalkeepers get their own cards and metric groups, with no switch and no Squad button."
  - "Every card block shows six cards as ruled on #136: Yellow cards and Red cards are the fifth and sixth, a 0 included, in one row of six while all fit, then three across, otherwise two across."
  - "Every text from #136 is in `strings.ts` in EN, DE and FI, the page title and meta description included."
  - "The page matches the mock at 280, 320, 360, 375, 700 and 1010px in EN, DE and FI, with no sideways scroll, overflow or split word."
  - "Every row of Players to watch on the match page links to the player's page when this build makes one."
  - "The card is a registered component, and the separators are in `block_standard.md`."
  - "The stub is gone: `stub: true` and the `STUB_PAGES` entry are removed."
  - "Wireframes 03, 12 and 13 are retired."
  - "All MRs are green, and both design baselines match CI's measurement."

amendments: >
  2026-11-09, approved in chat: components.yml also names the Player page under the Tab bar and its
  Recent matches rows as Result row parts; approved_design adds Home #127 and Competition #129, whose
  board rows link to a player only when the player has a page; the baselines criterion reads "both
  design baselines match CI's measurement". 2026-11-09, approved in chat: the Player page's
  comparison blocks follow the team rule for a percentage's volume, and metrics_display.md states
  it.
