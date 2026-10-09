# Content architecture: blocks, tabs, navigation

This document defines the content model of the Matchday Pilot site. Reusable **blocks**, each
backed by one mart, compose into **tabbed entity pages**. A **navigation graph** links the pages.
The wireframes arrange the blocks on screens, and the marts feed them.

| Topic | Owner |
|---|---|
| URL scheme, locale routing, export files per template | [`docs/site_architecture.md`](site_architecture.md) |
| What each screen shows, and where each block sits | the wireframes, in the reading order of [`docs/wireframes/00_overview.md`](wireframes/00_overview.md) |
| Which metric rows a block shows, and in which order | [`docs/wireframes/metrics_display.md`](wireframes/metrics_display.md) |
| Metric definitions | the `metric_catalogue.csv` seed |
| Windows (section 4) and the player performance surface (section 8) | [`docs/metrics_context_model.md`](metrics_context_model.md) |
| Configured history depth per competition | `history_seasons` in [`docs/competition_registry.yml`](competition_registry.yml) |
| Work not yet built, and its order | the GitLab issues |

---

## 1. Principles

1. **Three layers.** Blocks are reusable content units. Tabs arrange blocks for one entity. The
   navigation graph links entities. Nothing computes in a page; pages only arrange blocks.
2. **One block = one mart**, parameterised by `league_code`, season and entity. A new competition,
   team, player or season adds rows and pages, never a mart. This is the no-new-model rule of
   `CLAUDE.md`, applied to the site.
3. **"Profile" is not a separate unit.** It is the Overview tab, a compact digest of the entity.
   Each entity page is a set of tabs.
4. **Languages add labels, not data.** Blocks hold locale-independent data. Labels resolve at build
   time from the catalogue i18n keys and the entity names. Every language uses the same data.
5. **Every block has a compact form and a full form.** The placement picks the form. Overview,
   teasers and home hooks use the compact form; dedicated tabs use the full form.
   `metrics_display.md` owns which rows each form shows.
6. **Honest limits.** The site fabricates nothing. A block with no data does not render. Section 7
   lists what the site leaves out.

---

## 2. Entity types (the programmatic-SEO templates)

Each entity type below has one page template, except the deferred ones. Everything else is rows
inside these pages.
`site_architecture.md` section 3 owns the URL of each page.

| Entity | Tier | Page-count driver |
|---|---|---|
| **Competition** | rich | competitions × seasons |
| **Team** | rich | teams (× seasons) |
| **Player** | rich | players (× seasons) |
| **Fixture** | rich | fixtures |
| **Matchday** | thin SEO | competitions × rounds |
| **Coach** | thin SEO | coaches (the provider supplies them; `dim_coach`) |
| Nation, Stadium | deferred | — |

Every template reads `league_code`-keyed marts. The page count of an entity type is its driver
multiplied by the number of languages.

---

## 3. The block library (block ↔ mart)

A block is a mart sliced by `league_code` and entity. So one block works for any competition and
either subject, and appears on many tabs. The Subject column names the entity a block describes.

| Family | Block | Subject | Backing mart |
|---|---|---|---|
| **Identity** | Team header | team | `mart_team_profile`: identity from `dim_team` (+ founded year, venue), + standing chip |
| | Player header | player | `mart_player_profile`: identity from `dim_player` (+ birth date), + current club |
| | Competition header | competition | `mart_competition_index` (name, crest, region) + `mart_competition_fixtures` (the next round) |
| **Performance** | Form (recent) | team, player | `mart_team_momentum`, `mart_player_momentum` (+ `mart_team_momentum_window` drill-down, team only) |
| | Season (this season; per-game toggle) | team, player | `mart_team_profile`, `mart_player_profile` |
| | Season-over-season | team, player | `int_team_profile__yoy` → `mart_team_profile`; `int_player_profile__yoy` → `mart_player_profile` |
| | Vs-benchmark (bars vs league avg + percentile) | team, player | `mart_team_competition_benchmarks`, `mart_player_competition_benchmarks` |
| | Single fixture | team, player | `mart_team_fixture_stats`, `mart_player_fixture_stats` |
| **Standings / rank** | League / group table | team | `mart_standings`: the league's official row (the provider's, except where corrected), with `table_kind` |
| | Standing-as-context | team | `mart_fixture_standing_context` on the fixture page; `mart_team_profile` on the team page |
| | Deserved points (better / worse than the table says) | team | `mart_team_profile` |
| | Leaderboards (scorers + the metric set) | player | `mart_leaderboards` |
| **Facts** | Fact row (label · value · context) — the season in numbers | competition | `mart_competition_season_summary` + the `is_match_that_matters` flag from `mart_next_matchday` |
| **Schedule** | Upcoming / Results | team, player | `mart_team_fixtures` (filter) |
| | Matchday schedule | competition | `mart_competition_fixtures`: every fixture of the competition-season by round, with the `is_next_round` and `is_match_that_matters` flags |
| **Listings** | Squad / roster | team→players | `mart_roster` + `mart_player_career` (per-player season stats) |
| | Team directory | competition→teams | `dim_team_competition_season_mapping` (a core model) |
| | Player career (clubs + per-comp totals) | player | `mart_player_career` |
| **Matchup** | Match preview (two sides) | fixture | composed: the form window (`mart_team_momentum` or `mart_team_season_record`, whichever `is_form_window` flags) + standing (`mart_fixture_standing_context`) + head-to-head (`mart_head_to_head`) |
| | Lineups / key players | fixture | `mart_player_season_record` (key players, by `top_player_rank`). No mart serves lineups. |
| | Head-to-head | fixture | `mart_head_to_head` |
| **Insight** | Deserved-vs-actual *(flagship)* | team (player v1.x) | `mart_team_profile` (`deserved_points`, `deserved_rank`, `deserved_points_gap`) |
| | Vs-own-history / YoY *(flagship)* | team (player v1.x) | `int_team_profile__yoy` → `mart_team_profile` |
| | Opponent / schedule context *(flagship, v1.x)* | team, player | none (section 6) |
| | Contribution-share *(bonus)* | player↔team | `int_player_profile__contribution` → `mart_player_profile` (catalogued as `contribution_player_pct`) |
| | Streaks | team | `int_team_profile__streaks` → `mart_team_profile` |

The Fact row block type recurs on team, player and match pages.

### Page specs

Each page template declares a spec in `site_v2/src/specs/**/*.spec.json`. A spec names the page's
blocks, the source of each block, and a sample of its i18n keys.
`site_v2/src/specs/page-spec.schema.json` documents the spec shape.

`site_v2/scripts/check-page-specs.mjs` runs as the `prebuild` step of `npm run build`. It fails the
build when a page that imports `Layout.astro` has no spec. It also fails the build when a spec
names a source or an i18n key that does not exist. It does not compare block names with this
table. The specs check a subset of what the wireframes describe.

---

## 4. Pages = tabbed compositions

The tab set per entity is settled. The blocks per tab are the default arrangement. The wireframes
own the exact block placement, and which compact blocks an Overview shows.

| Entity | Tab | Blocks |
|---|---|---|
| **Team** | **Overview** | header, form, season highlights, standing, next match, key players, deserved-vs-actual teaser |
| | **Matches** | upcoming, results |
| | **Stats** | season per-game, vs-benchmark, season-over-season, deserved-vs-actual, streaks |
| | **Squad** | roster, with per-player appearances, minutes per appearance, goals and assists |
| | **History** | past-season records, all-time, coach |
| **Player** | **Overview** | header, form, season highlights, position, next match |
| | **Matches** | match log; each row links to its fixture |
| | **Stats** | season per-game, percentile vs peers, season-over-season |
| | **Career** | clubs, per-competition totals, caps |
| **Competition** | **Overview** | header, table, next matchday, deserved points, the season in numbers |
| | **Matchdays** | every round, results and upcoming, one round at a time; a cup names this tab "Rounds" |
| | **Rankings** | team boards and player boards, under metric groups |
| **Coach** | **Overview** | current club, clubs managed |
| **Fixture** | — | match preview, key players, fixture stats after the match, lineups |
| **Home** | — | fixtures first: next matches, Top players, Top teams |

---

## 5. Navigation graph (what makes it a site)

Every entity links to its neighbours. `site_architecture.md` section 3, "Navigation", owns which
element on a page carries each link.

| From | Links to |
|---|---|
| Home (upcoming) | → Fixture |
| Fixture | → each Team · → Players (lineups / leaderboards) · → Competition |
| Team | → Competition (its table) · → Players (squad) · → its Fixtures · → Coach |
| Player | → current Team · → Competition · → his Matches |
| Competition | → Teams (directory) · → Fixtures · → Players (scorers) |
| Coach | → current Team |

The graph is closed. A reader goes from upcoming matches to team stats, clubs, players, and their
upcoming matches.

---

## 6. Flagship reads (the differentiators)

The flagship reads are a small set of smart reads that raw-number sites do not synthesise.
Vs-benchmark and percentile are table stakes, because other sites show them too. They are the
context and the engine, not the headline. A player benchmark compares a player with his positional
peers and gives a percentile. A team benchmark ranks a team within its league.

1. **Deserved-vs-actual** *(v1)*: underlying play against actual results, with the gap. Example:
   *"Creating like a top-2 side but sitting 7th — likely to climb"*. Teams have it in points, for
   domestic leagues. `mart_team_profile` serves `deserved_points`, `deserved_rank` and
   `deserved_points_gap`. `int_team_season__deserved_vs_actual` owns the method, which uses no xG.
   The player analog, output against underlying play, is v1.x.
2. **Vs-own-history (year-over-year)** *(v1)*: the entity against itself one season earlier, at the
   same point. Example: *"22 points after 10 games against 18 last year"*. A team aligns by games
   played; a player aligns by appearances at the same club. Rule R6 in
   `dbt_project/models/docs/metric_rules.md` owns the alignment. `int_team_profile__yoy` and
   `int_player_profile__yoy` compute it, for domestic leagues only.
3. **Opponent and schedule context** *(v1.x)*: performance weighted by opposition quality, through
   the benchmark engine. Its other name is opponent-adjusted form. Backward: *"the unbeaten run came
   against the bottom half"*. Forward: *"4 of the next 5 are top-six"* (fixture difficulty). The
   football analytics expert owns the definition. No mart serves it, and it has no display home.
   Season-level schedule strength is near-constant in a balanced league.
4. **Contribution-share** *(bonus)*: a player's share of the team's output. Example: *"involved in
   45% of Bayern's goals"*. It is cheap, tells a story, and links team and player pages.
   `mart_player_profile` serves it as `contribution_player_pct`.

The three main reads form one axis set: **vs your own play** · **vs your own past** · **vs your
opponents**.

---

## 7. Out of scope and limits

- **No xG.** The deserved-vs-actual read uses the pipeline's own chance-quality measure, never a
  faked xG.
- **No News tab and no Transfers tab.** The site has no news source and no transfers surface.
- **Career and History depth** equals the backfill depth of each competition (section 8).
- **Coach and Stadium blocks** appear only where the provider data is clean.
- **Mart naming mixes patterns**, for example `mart_team_fixtures` beside `mart_player_match_log`.
  This document does not settle naming.

---

## 8. Backfill (history depth) policy

History depth is a number per competition: `history_seasons` in `docs/competition_registry.yml`.
The registry holds the configured value; this section holds the policy. Value and data quality set
the depth, not the API budget. The policy is tiered, with a quality floor.

| Competition type | Depth |
|---|---|
| Top domestic leagues (BL1, PL, PD, SA, L1…) | 10 seasons |
| 2nd-tier / smaller leagues (BL2, ED, VL, MLS…) | 5 seasons |
| Continental club (UCL…) | 10 seasons |
| World / continental championships (WC, EURO, AFCON…) | last 4 editions |
| Qualifiers | current + previous cycle |
| Domestic cups | 5 seasons |

- **Quality floor:** backfilling a competition stops at the first season with empty player
  statistics. An empty season wastes budget and makes thin pages. Record the achieved depth.
- **Phased rollout:** the featured competitions come first. The measured call cost against the
  budget decides each extension.
- Changing `history_seasons` and running a backfill are cost-gated ingest work, outside this
  document.
