# Task contract — #151: the Rankings tab, the Overview rework, the page rules

objective: >
  Build the competition page's Rankings tab and rework its Overview to the design approved on
  #129 (2026-09-16), on the metric groups #152 shipped. The team leaderboard mart grows from four
  boards to the twelve ruled and the player mart moves to the thirteen ruled; two team card
  metrics enter the catalogue and the season rollup; `clean_sheets` becomes a bare count
  everywhere; the export selects the boards per competition-season and drops the next-matchday
  block; the Rankings page renders the boards under the catalogue's groups from one board
  component; the Overview shows Table · Deserved points table · The season in numbers. The
  page-wide rules the issue names are already ruled in `block_standard.md` and live in
  `system.css` (#153); this task composes from them and adds no element.

refs: >
  #151 (the requirement; its checklist is `acceptance_criteria` below by content); #129 "The
  approved design" (the Rankings tab, the Overview rework, the binding rules); #152 (groups: key,
  order, names); #153 (the block standard, the measured check, the merge gate on the issue).
  `docs/metric_layer.md` (NULL unless every match in the window is covered);
  `docs/wireframes/metrics_display.md` (LOCKED; row 3); `docs/site_architecture.md` §3 (the tab's
  address row); `.claude/agents/bi-analyst-reviewer.md` item 4 (rendered evidence).
  Measured on `main` at `af081cae`: `mart_team_leaderboards` 4 boards desc-only,
  `mart_leaderboards` 15; `fct_fixture_team_stats` carries `yellow_cards`/`red_cards`, read by no
  model; 9 player board label keys and both team card labels absent from `strings.ts`.

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_legs__team_match.sql
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_team_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics_cumulative.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/5_marts/shared/mart_team_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_mart_team_leaderboards_all_boards_present.sql
  - dbt_project/tests/assert_mart_team_leaderboards_rank_follows_rank_order.sql
  - dbt_project/tests/assert_mart_team_leaderboards_one_leader_per_league.sql
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - tests/test_export_landing.py
  - tests/test_leaderboard_board_sets.py
  - site_v2/src/pages/*/*/index.astro
  - site_v2/src/pages/*/*/fixtures/index.astro
  - site_v2/src/pages/*/*/stats/index.astro
  - site_v2/src/pages/*/players/*.astro
  - site_v2/src/specs/competition/index.spec.json
  - site_v2/src/specs/competition/stats/index.spec.json
  - site_v2/src/components/competition/CompetitionTabs.astro
  - site_v2/src/components/competition/DeservedPoints.astro
  - site_v2/src/components/competition/DeservedTable.astro
  - site_v2/src/components/competition/NextMatchday.astro
  - site_v2/src/components/competition/RankingBoard.astro
  - site_v2/src/components/competition/RankingsBlock.astro
  - site_v2/src/components/competition/SeasonFacts.astro
  - site_v2/src/components/fixture/MetricRow.astro
  - site_v2/src/components/fixture/MetricComparison.astro
  - site_v2/src/components/fixture/FormSegment.astro
  - site_v2/src/specs/players/player.spec.json
  - site_v2/src/lib/competitionPayload.mjs
  - site_v2/src/lib/competitionPayload.test.mjs
  - site_v2/src/lib/format.ts
  - site_v2/src/lib/metricRows.ts
  - site_v2/src/lib/types.ts
  - site_v2/src/i18n/strings.ts
  - site_v2/src/styles/system.css
  - site_v2/src/data/competitions/BL1/2026.json
  - site_v2/src/data/README.md
  - site_v2/scripts/check-built-pages.mjs
  - site_v2/scripts/check-built-pages.test.mjs
  - site_v2/scripts/check-metric-labels.test.mjs
  - site_v2/scripts/audit-seo.mjs
  - site_v2/scripts/audit-seo.test.mjs
  - docs/site_architecture.md
  - docs/wireframes/metrics_display.md
  - docs/wireframes/block_standard.md
  - docs/wireframes/99_gaps_register.md
  - dbt_project/docs/layering.md
  - design-mocks/gen_competition_teams.py
  - design-mocks/gen_competition_matchdays.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/active_work.md
  - docs/tracker/gitlab_snapshot.md

impact_map: >
  writers: `int_legs__team_match` gains two columns from `fct_fixture_team_stats` (`yellow_cards`,
  `red_cards`, already on the fact, read by no model today — `grep -rn yellow_cards
  dbt_project/models` hits base, core.yml and the fact only). `int_team_season_record` gains their
  cumulative sums and one coverage count; `int_team_season__metrics_cumulative` gains the two
  gated catalogue-id columns, and the projection `int_team_season__metrics` selects `*`. Every
  addition is a new column; no existing column changes.
  downstream, measured on this branch with the scratchpad profile (`dbt ls --select
  int_legs__team_match+ --resource-type model`): int_legs__team_match, int_player_momentum__metrics,
  int_player_profile__contribution, int_team_competition_benchmark_metrics_long,
  int_team_competition_benchmarks, int_team_momentum__metrics, int_team_momentum_window,
  int_team_profile__streaks, int_team_profile__yoy, int_team_season__deserved_vs_actual,
  int_team_season__metrics, int_team_season__metrics_cumulative, int_team_season_record,
  mart_competition_fixtures, mart_competition_season_summary, mart_head_to_head,
  mart_matchday_insights, mart_player_momentum, mart_player_profile,
  mart_team_competition_benchmarks, mart_team_fixtures, mart_team_leaderboards, mart_team_momentum,
  mart_team_momentum_window, mart_team_profile, mart_team_season, mart_team_season_insights,
  mart_team_season_record — 28 models rebuild; the ones that select named columns are unchanged
  in output, the ones that `select *` (the projection) carry two more columns.
  `dbt ls --select mart_team_leaderboards+ mart_leaderboards+` → the two marts and their own tests
  only: both are LEAVES. `dbt ls --select metric_catalogue+ --resource-type model` → none today;
  after this change `mart_team_leaderboards` reads the seed for `direction`.
  Guards that read the change: `assert_no_uncatalogued_season_metric` (the two new columns must be
  catalogued — they are), `assert_metric_catalogue_expr_resolvable` (`sum(yellow_cards)` on
  `int_legs__team_match` — the column exists after the leg edit), `assert_metric_meaning_complete`,
  `assert_metric_direction_lower_is_better_agree`, `check_yml_vs_projection.py` (every new column
  documented in its yml), `sync_metric_docs_blocks.py --check` (regenerated in the same commit),
  `check_description_hygiene.py`.
  layer_rules: intermediate stays intermediate (first logic on the leg: the provider's blank card
  is a zero when the stat line exists); marts compose from `int_team_season__metrics` and the seed;
  no model overrides its layer's materialisation; `check_layer_contract.py`.
  deploy_order: the marts are views and rebuild with the nightly; `data:build:mr` builds the
  branch into `ci_mr<IID>_*`; nothing is served until `deploy:export` or #156 — the committed
  sample carries the new payload shape so the build is self-contained on the merge.
  consumption: `scripts/export_site_data.py` `fetch_competition_payloads` reads the two leaderboard
  marts (new) and stops reading `mart_next_matchday` for the competition payload (Home's landing
  read is untouched); `_LEADERBOARD_METRICS` follows the mart's board set. The committed
  `competitions/BL1/2026.json` is regenerated. The site: a new page at `/{lang}/{slug}/stats/`,
  the Overview's block list, the player stub's page set, `count_fraction` leaves the display
  layer.
  blast_radius: `mart_team_leaderboards` row set changes (12 boards, two ascending, zero rows kept
  on ascending boards only); `mart_leaderboards` loses six boards and gains five; no other mart's
  numbers move. On the site: the Rankings page is new; the Overview loses Next matches and the two
  deserved boards and gains the deserved table; the run facts stop linking to a team; the fixture
  page's form window shows clean sheets as `3` instead of `3/5`; Home is unchanged (its four
  team boards and four player boards are all in the new sets, and `board_leader_order` orders
  them as before — all four are `desc`).

acceptance_criteria:
  - The built `site_v2/dist/en/bundesliga/stats/index.html` exists, its tab bar has three tabs with Rankings lit (`span.tab.on` text "Rankings"), and it carries exactly two `.sechead .eyebrow` block names, "Team rankings" then "Player rankings" (DE "Team-Rankings" / "Spieler-Rankings", FI "Tiimirankingit" / "Pelaajarankingit" on the DE/FI builds).
  - On that page every `.ctab.rkt` board has between 1 and 5 `.ctab-row` rows, the boards sit under `.rkgroup > .gh .nm` headings whose text is the group name in `metric_groups.json` order, and no board on a `desc` board (per the payload's `rank_order`) shows a `.n.pts` value of 0; every `asc` board's head carries the `.bnote` "(fewest first)" and no `desc` board does.
  - The built `site_v2/dist/en/bundesliga/index.html` carries exactly three `.sechead .eyebrow` block names in order — "Table", "Deserved points table", "The season in numbers" — no "Next matches", and its `.ctab.dpt` table has one row per team in the payload's `deserved` list ordered by the served `deserved_rank`, with the Deserved column as the row's `.n.pts` cell.
  - On every competition page under `site_v2/dist` the `.facts` block has no `a.frow` (every fact row inert) and no row labelled "The match that matters next".
  - `python scripts/check_design_inventory.py --dist site_v2/dist` exits 0 with the built Rankings page listed in `block_standard.md`'s Pages table, and Home, the Overview and the Matchdays page still pass.
  - `mart_team_leaderboards` serves `rank_order` = `asc` on exactly `goals_against_per_match` and `shots_on_goal_against_per_match` and `desc` on the other ten (checked in `data:build:mr`'s built view by the new singular test and the accepted values).

decisions_taken: >
  The CPO's rulings this contract rests on, all on #129 "The approved design" (2026-09-16) and
  #151: three tabs and their labels; the Rankings tab's two block names and its board sets (12
  team, 13 player, in the stated groups and order); the board rules (five rows, the dense rank as
  served, the catalogue's format, "fewest first" beside an ascending board, no zero row on a
  most-first board, headings and fact rows inert until #140); the card boards most first
  regardless of catalogue direction; `clean_sheets` to `integer`, `points_won` keeps
  `points_fraction`; the Overview's blocks (Next matches struck, the deserved table's columns and
  block name EN/DE/FI, six fact rows as leaderboard links); the page-wide rules; the gate that the
  measured check passes on its pages and on Home.

  Taken as implementation, inside those rulings: (1) the tab's address is `/stats/` — the issue
  gives the address to the builder "optimised for search", and fans search "stats" / "Statistik"
  / "tilastot" the way #150 chose "fixtures" over "matchdays"; the glossary's `/{lang}/stats/{metric}/`
  is another level of the tree. (2) The provider writes zero cards as a blank in the team
  statistics line: measured on prod `core.fct_fixture_team_stats`, BL1 holds 3,909 rows with a stat
  line and a blank red-card value against 1,865 explicit zeros (PL 6,798 / 465; SA 4,703 / 2,237).
  So the leg reads a blank card as 0 when the team's stat row exists and NULL when it does not,
  and the season total is NULL unless every non-awarded match is covered — the metric layer's rule.
  (3) The team mart reads each board's direction from the catalogue seed (a `ref` to
  `metric_catalogue`, entity team) and serves it as `rank_order`, with `cards_yellow` and
  `cards_red` forced `desc` by the ruling; ranking, tie-break and the Home order follow the signed
  value; the zero cut applies to `desc` boards only, since 0 conceded is a ranking. (4) Board order
  within a group is the export's list in the ruled order and the group order is
  `metric_groups.json`; the export carries `metric_group`, `per_match` (the catalogue's
  `denominator_expr = count(*)`) and `rank_order` per board so the page classifies nothing.
  (5) Player board rows link to the player stub page, whose page set grows to every player a
  competition payload's boards name — its own rule, a destination is built, not routed around;
  the board heading is a plain name until #140, since a chevron that leads nowhere is not drawn,
  and the six fact rows are inert for the same reason. (6) The Overview's header round comes from
  the fixtures' `is_next_round` row now that `next_matchday` leaves the payload. (7) The tab-bar fit
  and the 14px gap are measured by `check_design_inventory.py` on every MR (#153's mechanism, the
  ruled rows `nav.tabs` and `.sechead`); the Astro-side proofs added here are the zero rule and
  the five-row cut over the built page. (8) `count_fraction` leaves the format enum, `format.ts`
  and `metricRows.ts` with its last row; `.ctab.dp` leaves `system.css` with the boards it styled.
  (9) The six player boards the ruling dropped leave `mart_leaderboards` and `_LEADERBOARD_METRICS`;
  their display-atom columns stay on every row. No new mechanism: one page, three components, one
  singular test, one pytest, one seed read in a mart. No recurring cost.

decisions_reserved:
  - none: every label is put to the CPO on the MR head (the copy table), as #151 asks; the merge is the approval.

done_when:
  - `.venv/Scripts/dbt.exe parse` green with the scratchpad profile; every touched model and test lints clean from the repo root; `python scripts/check_layer_contract.py`, `python scripts/sync_metric_docs_blocks.py --check`, `python scripts/check_description_hygiene.py` exit 0.
  - `python -m pytest tests/test_export_site_data.py tests/test_export_landing.py tests/test_leaderboard_board_sets.py tests/test_metric_groups.py tests/test_metric_bindings.py tests/test_design_inventory.py -q` green; the board-set pin seen RED with one key removed from the export's list.
  - `python scripts/export_site_data.py --entities competitions` regenerates `competitions/BL1/2026.json` with `team_boards` and `player_boards` and no `next_matchday`.
  - `cd site_v2 && npm test && npm run build` green on the committed sample; the Rankings checks in `check-built-pages` seen RED on a six-row and on a zero-row fixture.
  - `python scripts/check_design_inventory.py --dist site_v2/dist` exits 0 (the merge gate); the acceptance criteria demonstrated from `dist` in `acceptance_evidence.md`; the rendered measurements at 375/700 px EN/FI in `rendered_page_evidence.md`.
  - `data:build:mr` green; the MR head carries the copy table, the two catalogue rows and the address.

amendments:
  - 2026-09-22: + `dbt_project/models/docs/shared_columns.md` — authority: repo practice, `engineering_standards.md` §2 Form as `check_description_hygiene.py` enforces it (a column whose name is a shared block references a block, never restates it); content: the leg's `yellow_cards` / `red_cards` read a blank as 0 on a present stat line, a meaning the fact's block does not carry, so they get their own `__leg` blocks beside `opponent_corner_kicks__leg`, and the cumulative sums on the season record reference the metric blocks. No behaviour, no path beyond the docs file.
  - 2026-09-22: + `site_v2/src/components/fixture/MetricComparison.astro` — authority: the issue's line "`format.ts` / `metricRows.ts` and the fixture page's form window follow" and the memory rule that a correction replaces; content: with `count_fraction` gone, `MetricRow.astro` no longer reads a window's denominator, so its `windowKey` prop is dead and the one call site passing it is this file. One prop removed at one call site; no rendered change.
  - 2026-09-22: + `site_v2/src/components/fixture/FormSegment.astro` (the prop above enters the chain there — two attributes removed, no rendered change) and + `site_v2/src/specs/players/player.spec.json` — authority: the page-spec contract (`check-page-specs.mjs`, `prebuild`) that a page's spec states its data source and page-count driver; content: the player stub's page set grows from Home's linked players to every player a competition payload's boards name, so its spec's `minimum_data` and `page_count_driver` say so.
  - 2026-09-22: the four page paths respelled with `*` for the bracketed route segments — no new path: the contract gate matches with fnmatch, where `[lang]` is a character class, so the literal spellings matched nothing (`CLAUDE.md`, the `scope_paths` trap). The pages listed are the same four.
  - 2026-09-22: + `site_v2/scripts/check-metric-labels.test.mjs` — authority: #370's locked criterion the file enforces ("every metric name the page asks for resolves in all three locales", and no locale carries a label nothing renders); content: the set of names the page asks for grows by the Rankings tab's board labels (the two export tuples resolved through the catalogue, as the Home tuple already is), so the new team card labels and the nine player labels are asked for and pinned in EN/DE/FI rather than reported as unused.
  - 2026-09-22: + `site_v2/scripts/audit-seo.mjs` and its test — authority: #129 "the header never changes with the tab" (the `<h1>` is the competition's name on every tab) and the audit's own stated exemption ("an entity page and its tab pages share one header by design"); content: the exemption was written for one tab and reads "one path is the other plus a segment", so two sibling tabs (`/fixtures/`, `/stats/`) of one entity fail it — measured on the first build: 3 violations, all `h1 is not unique`. The exemption is widened to sibling tabs of the same entity page carrying that page's h1, nothing else; two unrelated pages with one h1 still fail, and the test shows both.
  - 2026-09-22: + `design-mocks/gen_competition_matchdays.py` — authority: the issue's "the Overview payload without the next-matchday block" and the block standard's Pages table, which the measured check runs this generator from; content: the generator read the flagged match from the payload's `next_matchday` key, which this task removes, and the check failed on it (`KeyError: 'next_matchday'`); it now reads `is_match_that_matters` from the payload's `fixtures`, the same flag on the same fixtures. The render is unchanged.
  - 2026-09-22: + `docs/wireframes/99_gaps_register.md` and `dbt_project/docs/layering.md` — authority: the scope-auditor's round-1 FAIL (a design-chain document the diff contradicts must move in the same branch) and the analytics-engineer's round-1 note, under the rule that a correction replaces the old text everywhere; content: GAP-11 still names `clean_sheets (x/y)` as the approved shape (superseded on #129: a bare count) and the layering doc's mart inventory still describes the two leaderboard marts as four and ten boards. Two rows corrected; no code.
  - 2026-09-22: + `dbt_project/tests/assert_mart_team_leaderboards_one_leader_per_league.sql` — authority: the issue's line "the ascending boards carry their direction from the catalogue" and `data:build:mr` on !216's first pipeline (201 failures, every one a leader pair on the two ascending boards); content: the test's adjacency check reads "the later leader is not strictly better" as "not a larger value", which is the descending rule only; it now reads the board's served `rank_order` and holds the mirror rule on an ascending board. The tie-break and the other three invariants are untouched.
