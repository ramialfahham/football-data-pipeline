# Site architecture — Matchday Pilot (programmatic content site)

> This document defines the v2 site's URLs, locales, slugs, navigation rule, template data contract
> and SEO surface. Every v2 page builds against it.
>
> [`content_architecture.md`](content_architecture.md) defines the blocks, tab compositions and
> navigation graph that the templates render. An edit to this document follows
> `working_agreement.md` §10.

## 1. What v2 is

Matchday Pilot (v2) is a responsive, multilingual football-analytics website for fans. It is a
programmatic content site: a small set of page templates renders the dbt marts into one page per
entity. Nobody writes page content by hand. New fixtures, teams and players flow through the
pipeline, and the next build adds their pages.

```
dbt marts → scripts/export_site_data.py → site_v2/src/data/{entity}/{id}.json
  → Astro build (one template × N entities) → static pages + sitemap + structured data
  → Firebase Hosting (CDN)
```

## 2. Hard constraints (locked)

| Constraint | Rule |
|---|---|
| Surface | `site_v2/` (Matchday Pilot) is the only site. The retired MVP in `site/` is offline and frozen. v2 needs no parity with it, no cutover and no restore. Legal pages are a v2 build requirement. |
| Tech stack | **Astro**, static output only, deployed to Firebase Hosting. Interactivity uses islands (charts, search). There is no server-side rendering and no backend. |
| Competition IA | The competitions index page (`/{locale}/competitions/`) groups competitions by `competition_type`, from `mart_competition_index`. Country hubs are not built. Adding a competition adds no template or model file (CLAUDE.md, "No-new-model rule"). |
| Metric governance | **Catalogue-only.** Pages render `metric_catalogue` metrics by their catalogue formula. Labels come from the catalogue's i18n keys. A new metric needs a catalogue extension first (`working_agreement.md` §10). |
| Data honesty | Nulls render as `–`, never as fabricated zeros. No unmodelled KPIs and no fabricated probabilities. Pages with insufficient data are not generated (no thin pages). |
| Competition discriminator | `league_code` discriminates the competition everywhere. No template or export logic hardcodes a competition. |

## 3. URL scheme

All pages live under a locale prefix. Addresses use trailing slashes and lowercase kebab-case.

An address has three kinds of segment. The **locale** comes first. **Words** say what kind of page
it is. **Names** say which competition, season, club, player or match. Words are in the reader's
language and come from the word table below; names keep one spelling in every language (§ Slugs).
The scheme is written here with the English words.

```
/{locale}/                                                   landing
/{locale}/competitions/                                      all competitions (grouped by type)
/{locale}/football/{country-slug}/                           country hub (e.g. /football/germany/)
/{locale}/{competition-slug}/                                competition page, Overview tab (latest season)
/{locale}/{competition-slug}/{season-slug}/                  competition season archive
/{locale}/{competition-slug}/matches/                        competition page, Matchdays tab (every round, results and fixtures; "Rounds" for a cup), the same word for every kind of competition
/{locale}/{competition-slug}/matches/{date}-{home}-vs-{away}/   fixture page (preview → report), under its competition's Matchdays tab
/{locale}/{competition-slug}/stats/                          competition page, Rankings tab (the top five of every team and player board under the catalogue's groups); the tab's on-screen name stays Rankings
/{locale}/teams/{team-slug}/                                 team profile, a club or a national team
/{locale}/players/{player-slug}/                             player profile
/{locale}/matches/                                           Matches menu page: the day it opens on (the build day, else the next day with a match), every competition playing it
/{locale}/matches/{yyyy-mm-dd}/                              every other day in reach, from each competition's last matchday to the end of its next
```

Every address in the block above has a built page, except the country hub and the season archive.
The player page is a stub.

Planned, not designed yet; each address is provisional until its page's review (§ Address words):

```
/{locale}/teams/                                             Teams menu page
/{locale}/players/                                           Players menu page
/{locale}/standings/                                         Standings menu page
/{locale}/stats/                                             Statistics menu page
/{locale}/stats/{metric-slug}/                               one statistic across competitions; whether it also holds the metric's definition, in place of a separate glossary, is the Statistics review's
/{locale}/{competition-slug}/stats/{metric-slug}/            one statistic's full list in one competition
/{locale}/h2h/{teamA}-vs-{teamB}/                            head-to-head
```

Reserved: structural only, renders nothing until built.

```
/{locale}/{competition-slug}/matches/{...}/prediction        prediction slot
```

### Address words: in the reader's language

The site reads the words from `site_v2/src/i18n/address_words.json`, the one list rule 4 names. It
holds the words of the pages built today. A page adds its word there when the page is built.
Search engines weigh address words lightly. Each word is clear and stable; each page's title
carries its search phrase.

1. **Words are in the reader's language; names are not.** Competition, season, club, player and
   match names keep one spelling in every language (§ Slugs).
2. **A word is the menu word in that language, lower case**. One word serves a list and the pages
   it lists: `/de/mannschaften/` lists the teams, `/de/mannschaften/bayern-munchen/` is one of
   them. English uses `stats`, not `statistics`. A competition's tab takes the word of what it
   lists. So the Matchdays tab is `/de/bundesliga/spiele/`, and each match sits under it. A tab or
   menu item may have an on-screen name that differs from its address word. The Rankings tab lives
   at `stats`.
3. **Words avoid umlauts**. Names fold them to the base letter (§ Spelling: `ä` → `a`, `ü` → `u`,
   `ß` → `ss`). A folded letter is fine in a name and reads as a misspelling in a word. No word in
   the table has an umlaut.
4. **One list holds every word in every language.** Every link and the language switch read from
   it. Nothing else spells a word. The language switch translates each word through the list. It
   never assumes that two languages share a path after the prefix.
5. **A word never equals a competition's name** (its registry `slug`), in any language. Both sit
   directly after the locale, so a clash makes two pages claim one address. The site build and
   `tests/test_address_words.py` fail on a clash.
6. **Once a page is public, its words never change.** Names carry the same promise (§ Slug
   stability). A new language ships only with every word in the table named.
7. **A date in an address is `yyyy-mm-dd`** in every language.
8. **A page not designed yet has a provisional word**, the one this rule gives it. Its own review
   confirms it, changes it, or removes it if the page is not built. A tab that a future design adds
   is named at that review by the same rule. Its address sits under its page
   (`/de/mannschaften/bayern-munchen/kader/`), so adding a tab never moves its page.

| Word | `en` | `de` | `fi` | Settled: pages built today | Provisional: pages not designed yet |
|---|---|---|---|---|---|
| competitions | `competitions` | `wettbewerbe` | `kilpailut` | the competitions index | |
| matches | `matches` | `spiele` | `ottelut` | a competition's Matchdays tab, and every match under it; the Matches menu page and its day pages | |
| teams | `teams` | `mannschaften` | `joukkueet` | a team's page, club or national team | the Teams menu page |
| players | `players` | `spieler` | `pelaajat` | a player's page | the Players menu page |
| stats | `stats` | `statistiken` | `tilastot` | a competition's Rankings tab | the Statistics menu page, one statistic's pages |
| standings | `standings` | `tabelle` | `sarjataulukko` | | the Standings menu page |
| h2h | `h2h` | `h2h` | `h2h` | | head-to-head |

The name of each statistic in an address (`/de/bundesliga/statistiken/tore/`) is a word too. The
Statistics review names it by the same rule.

Examples: `/de/bundesliga/spiele/`, `/de/bundesliga/statistiken/`, `/fi/joukkueet/hjk/` and
`/de/bundesliga/spiele/{yyyy-mm-dd}-bayern-munchen-vs-borussia-dortmund/`. A word that the scheme
shows and the table does not (`football`, `prediction`) is named with its page's own design, before
that page is built.

A match address carries the UTC date of the kick-off. That date moves when a league fixes its
schedule. Whether the address keeps the date is an open question.

### Locale routing

- **Every locale is prefixed** (`/de/…`, `/en/…`, …). No locale is unprefixed.
- Root `/` runs a client-side redirect to the browser's language, with **`en` as fallback**. It
  renders a language chooser for clients without JavaScript and for crawlers.
- Live locales: `de`, `en`, `fi`. Next: `es`, `fr`, `it`, `nl`, `pt`. Then `ar`, which is
  right-to-left and needs design-system support first.
- **`hreflang="x-default"` points at the `en` URL, not at `/`.** `/` is a client-side redirect,
  and a crawler cannot run it. `x-default` follows the fallback locale.

### Slugs (locale-independent)

- **Competition**: the registry's `slug` field, e.g. `bundesliga`, `premier-league`, `world-cup`.
  The build never derives it from a display name.
- **Season**: from `season_api_year` and the registry's `season_type`. A split-year season is
  `2025-26`; a calendar-year season is `2026`.
- **Team**: `{kebab-name}`, e.g. `bayern-munchen`, `aston-villa`, with **no provider id**.
  `base_apif__teams_global` derives it from the corrected team name, and `dim_team` publishes it as
  `team_slug`. Collisions resolve by a **symmetric, closed ladder**:

  1. An uncontested name takes its own slug.
  2. A contested name goes to nobody. Every contender takes `{name}-{country}`, with the
     provider's country.
  3. Otherwise the slug ends in the provider id. This happens when that slug is taken, the country
     is missing, or the name folds to nothing.

  Step 3 is the only place a provider id appears in any URL.
- **Player**: `{kebab-name}-{player_api_id}`, e.g. `jamal-musiala-1090`. The export builds it
  (`player_slug_with_id`). It keeps the id because player names collide too often for the team
  scheme.
- **Fixture**: `{yyyy-mm-dd}-{home-team-slug}-vs-{away-team-slug}`, under the competition's
  `/matches/`. `mart_competition_fixtures` builds it as `fixture_slug` from the two published team
  slugs. The fixture payload carries `fixture_id` for the data join.
- **H2H pair**: lower `team_api_id` first, so each pair has one canonical URL. The reversed order
  is a redirect or canonical alias.
- **Metric**: `metric_id` from `metric_catalogue`, kebab-cased.

#### Spelling: fold to the base letter, expand only where there is none

A character that decomposes to a base letter takes that letter. A character with no base letter
takes its conventional digraph.

| | |
|---|---|
| `Bayern München` → `bayern-munchen` | `ü` HAS a base letter |
| `Rot-Weiß Essen` → `rot-weiss-essen` | `ß` has NONE |

The two rows follow **one rule**. Umlauts never expand to `ue`, `oe` or `ae`.
`translit_latin` in `dbt_project/macros/team_name_normalization.sql` holds the map.
`assert_team_name_slug_alphabet` fails the build on a team-name letter that the map does not cover.
A new target comes from an external source of record, never from the shape of the glyph.

The rule applies to team slugs, and so to fixture slugs. Player slugs drop a character that has no
base letter.

#### Slug stability

Every build derives the slugs again. A rename, or a new team with the same name, can change a URL.
No slug is stored, and no alias or redirect exists.

Before the site goes public, each slug must be assigned once and stored. Once published, a slug
never changes. A rename gets a new alias, not a new canonical; the alias redirects (301) to the canonical.

The export writes `slug_map.json`: each slug with its entity type and id. No page reads it. Each
page takes its slugs from the payloads it reads.

### Navigation — what is clickable, and where it goes

Status: provisional. The **header + row** rule is confirmed, and the Next matches block applies it.

**Three families of clickable thing. Only two navigate.**

| Family | Examples | Goes where |
|---|---|---|
| **Chrome** | site header, footer, breadcrumb | a section of the site; identical on every page |
| **Content links** | row · heading · chip · prose link | an entity page |
| **Controls** | tabs, segmented switches | **nowhere** — they change what is shown on the page you are on |

**The rule:** *every content link points at the one entity it names, and a row names its subject.
Nothing inside a row is separately clickable.*

The four content-link shapes:

| Shape | Points at | Affordance at rest |
|---|---|---|
| **row** | what the row is *about* — its subject | list structure + separators; background lift on hover |
| **heading** | what the section is about (`Premier League ›` → that competition) | a chevron, always present |
| **chip** | the single thing named on it | its own border |
| **prose link** | whatever it names, in running text | a real underline |

Applied: a match row → the match. A Top players row → the player. A Top teams row → the team. A
standings row → the team. A squad row → the player.

The rule has three consequences:

- **A match row cannot also reach its two clubs.** The reader reaches them from the match page,
  where the teams are headings. That costs one extra click, and the path is visible at rest.
- **Controls never look like links**, or a reader cannot learn which one leaves the page. Tabs use
  underline and colour; heading links use a chevron.
- **Clickability is visible at rest; hover only confirms it.** A hover-only affordance does not
  exist on a phone.

The interaction standard (`design-mocks/interaction.py`) also holds two rules: **never nest a link
inside a link**, and **one element, one destination**.

Colour: rest, hover and active stay on the neutral ramp, e.g. `--muted` → `--ink-2` → `--ink` for
text. `system.css` reserves `--accent` for "better value" and `--loss` for a Loss pill. **The
keyboard focus ring is the one exception.** It uses `--accent` sitewide (`.fx a:focus-visible` in
`system.css`). A focus ring is an accessibility signal, not a meaning signal. It stays distinct
from every hover state, so it never moves to the neutral ramp.

## 4. Competition IA

The competitions index page (`/{locale}/competitions/`) is the route to a competition. It groups
competitions by `competition_type`. `docs/wireframes/08_browse.md` owns its grouping and order.

The home page is fixtures-first and has no browse block. `docs/wireframes/10_home.md` §0 owns its
composition. The nav exposes `Competitions · Matches · Teams · Players · Standings · Statistics`.

Two more axes feed `build_nav()` in `scripts/export_site_data.py`, which writes `nav.json`. No page
reads `nav.json`, and neither axis has a page.

**Competition groups.** `display_group` in `dbt_project/seeds/competition_types.csv` maps each
`competition_type` to a group. The groups, in order:

| Group | Competition types |
|---|---|
| `leagues` | `domestic_league` |
| `cups` | `domestic_cup`, `domestic_super_cup` |
| `continental-club` | `continental_cup`, `continental_super_cup`, `club_qualifying`, `club_world_cup`, `intercontinental_super_cup` |
| `national-teams` | `world_championship`, `continental_championship`, `qualifying` |

**Country hubs.** Each domestic competition belongs to the hub of its registry `country`.
`/football/germany/` lists BL1, BL2, DFB-Pokal …, ordered by `tier`, then `sort_order`.
International competitions belong to no country hub.

## 5. Templates → data contract

One template per entity type; each consumes exactly the export files listed. Adding a competition,
team or player adds pages with **zero template changes**. `scripts/export_site_data.py` writes
every file. The `fetch_*` function for a file holds its live list of marts.

| Template | Export file(s) | Upstream marts |
|---|---|---|
| Landing | `landing.json` | The next-matchday hero: `mart_next_matchday` (every competition's next round, read whole), `mart_competition_fixtures` and `core.dim_team`. Names and `region_rank`: `mart_competition_index`. Top players: `mart_leaderboards`. Top teams: `mart_team_leaderboards`. Read `fetch_landing_payload` for the live list. |
| Competitions index / country hub | `competition_index.json` | `mart_competition_index` |
| Matches page and its days | `matches/{yyyy-mm-dd}.json`, one per day | `mart_match_days` (the reach, each day's neighbours, the opening day), `mart_competition_fixtures` (the match rows), `mart_competition_index` (a competition's name, crest, kind and region rank). Read `fetch_match_day_payloads`. |
| Competition page, all three tabs | `competitions/{league_code}/{season}.json` (the page shows the latest season served) | Header: `mart_competition_index`. The table: `mart_standings`, with `table_kind`. The deserved points table: `mart_team_profile`. The season in numbers: `mart_competition_season_summary`. The Matchdays tab, the header's round and the match-that-matters flag: `mart_competition_fixtures`. The Rankings tab's boards, the top five per board: `mart_team_leaderboards` and `mart_leaderboards`. Read `fetch_competition_payloads` for the live list. |
| Fixture page ⭐ | `fixtures/{fixture_api_id}.json` | `mart_team_momentum` (W1), `mart_team_season_record` (W2), `mart_fixture_standing_context` (rank), `mart_head_to_head` (H2H), `mart_team_momentum_window` (the form list), `mart_player_momentum` (top players). Read `fetch_fixture_payloads`. **Not** `mart_matchday_insights`, the retired MVP's presentation pivot of the momentum mart. v2 reads the source marts directly. The played-match drill-down has no page; its export is `matchstats/{fixture_api_id}.json`, from `mart_team_fixture_stats` and `mart_player_fixture_stats`. |
| Team profile ⭐ | `teams/{team_api_id}.json` | `mart_team_profile`, `mart_team_fixtures` (next match, last five), `mart_roster` (the squad), `mart_team_competition_benchmarks`, `mart_player_career` (squad season stats). Read `fetch_team_payloads`. |
| Player profile ⭐ | `players/{player_api_id}.json` | `mart_player_profile`, `mart_player_match_log`, `mart_player_competition_benchmarks`, `mart_player_career`. Read `fetch_player_payloads`. The page is a stub and does not read `players/`. It takes its players from `landing.json` and the competition files. |
| Standings | within the competition file | `mart_standings` (league and group tables, incl. WC group letters) |
| Leaderboards | `leaderboards/{league_code}/{season}.json` | `mart_leaderboards`, player catalogue metrics |
| Head-to-head | `h2h/{pair_key}.json` (not exported) | `mart_head_to_head` |
| Metric glossary | `metrics.json` | `metric_catalogue` seed (descriptions, formulas, labels) |

`competitions.json` maps each `league_code` to its competition name and slug. The fixture and team
pages read it.

Export data is **locale-independent**. Display strings resolve at build time from the locale files
and the catalogue's i18n keys. `site_v2/src/lib/format.ts` formats numbers and dates with each
locale's `Intl` conventions and renders a null as `–`.

## 6. SEO surface

| Page | schema.org type | Notes |
|---|---|---|
| Fixture | `SportsEvent` | teams as `competitor`, kickoff, venue snapshot |
| Team | `SportsTeam` | crest as `logo`, memberOf league |
| Player | `Person` (athlete) | photo, nationality |
| All | `BreadcrumbList` | mirrors the URL hierarchy |

Each page's spec (`site_v2/src/specs/**/*.spec.json`, field `seo.schema_org`) names its type.

- Templated `<title>`, meta description and canonical per entity per locale.
- `hreflang` across all locales plus `x-default`; a sitemap index (`sitemap-index.xml`);
  `robots.txt`.
- OpenGraph and Twitter cards on every page.
- **Data-to-text narratives**: short, metric-backed sentences generated at build time per page
  (anti-thin-content). They come only from real mart values and are skipped when data is
  insufficient. The generator belongs in the export layer; none exists yet.
- Internal links follow the navigation graph in [`content_architecture.md`](content_architecture.md)
  §5.

## 7. Repository & build layout

```
site_v2/                      Astro project
  src/pages/[lang]/…          routes per §3
  src/components/             design-system components
  src/i18n/                   chrome strings (strings.ts) and address words (address_words.json)
  src/data/                   the export's JSON, read at build time (see its README.md)
scripts/export_site_data.py   per-entity export; the only export the v2 site reads
.gitlab-ci.yml                build:site-v2, deploy:export, deploy:site-v2
```

- `deploy:export` runs the export into `site_v2/src/data/`. `deploy:site-v2` builds the site and
  deploys it to Firebase Hosting. Both run only on a manual web dispatch.
- The site serves at its Firebase `.web.app` address, unlisted. `INDEXABLE` in
  `site_v2/src/config/indexability.mjs` keeps every page `noindex`.
- v2 goes live on `matchdaypilot.com`. No redirect maps a URL of the retired MVP to v2.
- The GitLab milestones hold the road to go-live:
  https://gitlab.com/rami.al-fahham/football-data-pipeline/-/milestones
- Monetization hooks are placeholders only: a named slot (header, in-content) that renders
  nothing. No template has one yet.
