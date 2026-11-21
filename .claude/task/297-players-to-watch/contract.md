# Task contract — Players to watch: the two approved boards

objective: >
  Issue #297: the next match page's Players to watch shows the design approved on #132: per side,
  two boards, Goals and assists and Ball actions per 90, each a Board name over the two-column split
  with each team's top three outfield players, the value alone in the catalogue's format, over the
  match's competition window. The export carries both boards per side from the ranks
  mart_player_season_record serves; the block is rebuilt from the parts library; the intro names the
  competition in EN, DE and FI.

refs: >
  #297; #132 notes of 2026-11-10 (17:45 no goalkeeper, 19:08 board names lead to their leaderboard,
  19:14 the decisions, 19:22 the intro texts, 19:46 the Finnish forms and their rule); #243 parts
  library; #290 go-live. The warehouse side (ranks, ball_actions_per90, its catalogue value test) is
  on main from the 132-players-to-watch-data task; the window fix and the export's eighth Match
  leaders board are on main from the 297-board-window task.

depends_on:
  - none: every warehouse and export fix this build reads is on main (dc309b34) and in prod

shared_files:
  - docs/design/components.yml
  - site_v2/src/styles/system.css
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/types.ts
  - scripts/export_site_data.py
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json

scope_paths:
  - .claude/task/297-players-to-watch/
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - site_v2/scripts/check-metric-labels.test.mjs
  - site_v2/src/i18n/strings.test.mjs
  - site_v2/src/pages/[[]lang]/[[]competition]/[[]matches]/[[]fixture].astro
  - site_v2/src/components/fixture/PlayerToWatch.astro
  - site_v2/src/components/fixture/PlayersToWatch.astro
  - site_v2/src/components/ui/PlayerRow.astro
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/types.ts
  - site_v2/src/specs/competition/matches/fixture.spec.json
  - site_v2/src/styles/system.css
  - site_v2/src/data/landing.json
  - site_v2/src/data/fixtures/*.json
  - site_v2/src/data/matches/*.json
  - site_v2/src/data/competitions/BL1/2026.json
  - site_v2/src/data/teams/*.json
  - site_v2/src/data/players/*.json
  - site_v2/src/data/player_peers/*
  - site_v2/src/data/player_pages.json
  - site_v2/src/data/player_metric_rows.json
  - site_v2/src/data/players_index.json
  - site_v2/src/data/teams_index.json
  - site_v2/src/data/README.md
  - tests/test_sentence_length_in_docs.py
  - tests/test_phone_built_pages_231.py
  - tests/fixtures/chart_screenshots/*
  - .gitignore
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - docs/wireframes/01_fixture_page.md
  - docs/content_architecture.md
  - docs/site_architecture.md
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json

protected_override: >
  docs/design/components.yml: the parts the approved Players to watch design names, the Board name
  over the two-column split and the player row's value alone, as the #250 Team page build added the
  parts its design names. The design is #132's note of 2026-11-10 19:14 (approved in chat,
  2026-11-10); the component-library step of #243 approved in chat, 17 Nov 2026; visual details are
  the coordinating agent's under docs/design/design_standard.md, approved in chat, 16 Nov 2026.

impact_map: >
  writers: scripts/export_site_data.py writes fixtures/{id}.json; no dbt model and no ingestion
  change. It reads mart_player_season_record, a leaf: `dbt ls --select mart_player_season_record+
  --resource-type model` returns only football_data_pipeline.5_marts.shared.mart_player_season_record.
  consumption: each fixture side's `top_players` (up to five rows of every mart column) becomes
  `players_to_watch` (window_type and two boards of at most three rows: player id, name, photo,
  position, value, with the board's catalogue label key and format). Readers of the old key:
  [fixture].astro, lib/types.ts, fixture.spec.json, tests/test_export_site_data.py; none outside the
  match page (Home's `top_players` is a different payload, shape_home_top_players, untouched).
  site: the match page's Players to watch block only; PlayerRow gains a value with no unit word, its
  other callers keep their numbers; the parts registry gains the parts the design names;
  the Players to watch intro takes the competition's Finnish inessive through playersInCompetition();
  inCompetition() and the competition page's Statistics tab intros are untouched.
  sample: the committed sample is refreshed as a set by the recipe in site_v2/src/data/README.md,
  because a past fixture can never be re-exported; the page set and the design baselines move with it.
  layer_rules: the export does not rank (anti-pattern A5): it selects by the mart's
  scorer_points_rank and ball_actions_per90_rank; check_component_registry.py and
  check_design_inventory.py check the parts; check_page_css.py the stylesheet.
  deploy_order: the mart columns and the window fix are in prod already (read-only checks of 18 and
  19 Nov 2026); the export and the site deploy together, so no window where one reads a key the
  other lacks.
  blast_radius: the match page's Players to watch on every next match page; no number or wording
  elsewhere changes. top_player_rank stays in the mart with no reader after
  this change.

approved_design:
  - match: #132
  - competition: #129

decisions_taken: >
  The board rules are #132's notes of 2026-11-10 (approved in chat): window, outfield only, top
  three per side, ties, the floor, a player may stand on both boards, the board names as catalogue
  labels. The intro texts are #132's note of 2026-11-10 19:22 (approved in chat); the Finnish forms
  and their fallback rule are #132's note of 2026-11-10 19:46 (approved in chat). The board name
  stays plain text until the leaderboard page it leads to is built (#132 note of 2026-11-10 19:08).
  A side with no ranked player on a board shows its column head with no rows. When the two sides'
  windows differ, the intro is playersIntroMixed, fan wording before go-live, the coordinating
  session's call of 21 Nov 2026: EN "Each team's key players {in}: this season's, or last season's
  before the team's first match in it."; DE "Die Leistungsträger der einzelnen Mannschaften {in}:
  aus dieser Saison oder, vor dem ersten Spiel dort, aus der Vorsaison."; FI "Kunkin joukkueen
  tärkeimmät pelaajat {in}: tältä kaudelta tai ennen joukkueen ensimmäistä ottelua siellä viime
  kaudelta." It reuses the rule of the old playersIntroPrev. The payload shape and
  component split are engineering calls of the coordinating session. The English intro reads "in
  {competition}" as the site does everywhere; the Finnish intro takes the researched inessive,
  #132's note of 2026-11-10 19:46. German "last season" is the #243 term list's "Vorsaison". The
  Players to watch board switches to two columns at 560px of its own width, 592px of the page,
  because a board is its own container, the principle stated in system.css. Box 3 holds where the provider sent player
  stats for every window match; the coordinating session ruled on 18 Nov 2026 that no refetch is
  due (the provider declares no player stats for the competitions without them, and the late-stats
  re-asks already reach the rest). No design-inventory pin rises: the three baselines differ from main's only by the Match page scroll pin, which falls.

decisions_reserved:
  - The number format of Ball actions per 90 (open on #132) and the German intro with "Vorsaison": the coordinator shows them to the CPO with the built block.
acceptance_criteria:
  - The match page's Players to watch shows the design approved on #132 (2026-11-10): per side, two boards, Goals and assists, and Ball actions per 90, outfield players only, over the match's competition window.
  - Ball actions per 90 is served by a warehouse model with the catalogue's minutes floor, and a dbt test checks its value against the catalogue formula.
  - Every next match whose teams have played in the window shows both boards.
  - The number format and the intro line with the competition name are approved before the build, in EN, DE and FI.

done_when:
  - python -m pytest passes, bar the built-page tests that read a stale local site build
  - python scripts/check_component_registry.py passes
  - python scripts/ci_local.py --mr is green
  - a fixtures export shows both boards on every next match side the mart ranks
  - the MR pipeline is green and python scripts/merge_ready.py <iid> says ready

amendments:
  - scope adds tests/test_sentence_length_in_docs.py: the data README's pin goes down by one long sentence the refresh split; the pin only moves down.
  - scope adds tests/test_phone_built_pages_231.py and tests/fixtures/chart_screenshots/*: the refreshed sample no longer holds the one player page the phone test names, and the scatter chart pins on the club Team page follow the refreshed team payload; authority: the coordinating session's go for the sample refresh, 19 Nov 2026.
