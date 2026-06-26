# Site architecture — Matchday IQ v2 (programmatic content site)

> The contract for epic #361. Every v2 workstream — templates (#368), export (#365),
> SEO (#369), i18n (#370), design (#366), migration (#377) — builds against this
> document. Change it only with CPO sign-off; downstream issues inherit changes.
>
> **Content model:** the reusable blocks → tabs → navigation structure these templates render is
> specified in [`content_architecture.md`](content_architecture.md) — blocks (= marts), tab
> compositions, the navigation graph, the flagship reads, and the new marts to build.

## 1. What v2 is

A professional, responsive, multilingual football-analytics website for fans
(kicker / whoscored / fbref / onefootball class), built as a **programmatic content
platform**: a small set of page templates rendered from the dbt marts into tens of
thousands of SEO-relevant pages. No hand-authored content — new fixtures, teams and
players flow through the pipeline and new pages appear automatically.

```
dbt marts → per-entity export (Python) → data/{entity}/{id}.json
  → Astro build (one template × N entities) → static pages + sitemaps + structured data
  → GitHub Pages (CDN) → indexed, multilingual
```

## 2. Hard constraints (locked)

| Constraint | Source |
|---|---|
| **The current Matchday IQ MVP (`site/`) stays fully functional until v2 reaches parity.** v2 lives in `site_v2/`; the legacy export + deploy run unchanged; cutover only at CPO sign-off (#377). | CPO, 2026-06-10 |
| **Tech stack: Astro**, static output only, deployed to GitHub Pages. Interactivity via islands (charts, search) — no SSR, no backend. | Epic #361 |
| **Hybrid competition IA**: browse by competition group AND by country hub, both derived from registry metadata (#364). Zero-file rule holds. | Epic #361 |
| **Metric governance: catalogue-only.** Pages render `metric_catalogue` metrics by their catalogue formula; labels come from catalogue i18n keys. New metrics require a CPO-approved catalogue extension first. | #327 / governance memory |
| **Data honesty**: nulls render as "-", never fabricated zeros; no unmodelled KPIs, no fabricated probabilities. Pages with insufficient data are not generated (no thin pages). | north_star.md |
| `league_code` is the partition key everywhere; no competition hardcoded in templates or export logic. | CLAUDE.md |

## 3. URL scheme

All pages live under a locale prefix. Trailing slashes; lowercase kebab-case slugs.

```
/{locale}/                                                   landing
/{locale}/competitions/                                      all competitions (hybrid browse)
/{locale}/football/{country-slug}/                           country hub (e.g. /football/germany/)
/{locale}/{competition-slug}/                                competition hub (current season)
/{locale}/{competition-slug}/{season-slug}/                  competition season archive
/{locale}/{competition-slug}/table/                          standings (+ group tables)
/{locale}/{competition-slug}/fixtures/                       fixtures & results
/{locale}/{competition-slug}/top-scorers/                    leaderboard (more: /stats/{metric-slug}/)
/{locale}/{competition-slug}/matches/{date}-{home}-vs-{away}/   fixture page (preview → report)
/{locale}/teams/{team-slug}/                                 team profile
/{locale}/players/{player-slug}/                             player profile
/{locale}/h2h/{teamA}-vs-{teamB}/                            head-to-head
/{locale}/stats/{metric-slug}/                               metric glossary page
```

Reserved (structural only, render nothing until built — #376):

```
/{locale}/{competition-slug}/matches/{...}/prediction        prediction slot
```

### Locale routing
- **Every locale is prefixed** (`/de/…`, `/en/…`, …) — no unprefixed default. This keeps
  hreflang symmetric and lets every locale rank in its market.
- Root `/` performs a client-side browser-language redirect with **`en` as fallback**
  (global ambition; overridable by CPO) and renders a language chooser for no-JS/bots.
- Locale set (phased, #370): `de en fi` live → `es fr it nl pt` → `ar` (RTL, needs
  design-system support first).

### Slugs (stable, locale-independent)
- **Competition**: `slug` field in the registry (#364), e.g. `bundesliga`,
  `premier-league`, `world-cup`. Never derived from display names at build time.
- **Season**: from `season_api_year` + registry `season_type`: split-year → `2025-26`,
  calendar-year → `2026`.
- **Team**: `{kebab-name}-{team_api_id}`, e.g. `bayern-munchen-157`. The id suffix
  guarantees uniqueness and stability across renames; the name part carries the SEO.
- **Player**: `{kebab-name}-{player_api_id}`, e.g. `jamal-musiala-1090`.
- **Fixture**: `{yyyy-mm-dd}-{home-team-slug-name}-vs-{away-team-slug-name}` under the
  competition's `/matches/`; the export carries `fixture_api_id` for the data join.
- **H2H pair**: lower `team_api_id` first → one canonical URL per pair; the reversed
  order is generated as a redirect/canonical alias.
- **Metric**: `metric_id` from `metric_catalogue`, kebab-cased.
- Slug map (entity → slug → id) is produced by the export (#365) and is the single
  source for routing and internal links. Slugs never change once published; a rename
  produces a new alias, not a new canonical.

## 4. Hybrid competition IA

Two browse axes, both fully registry-driven (#364 adds the fields):

- **Competition groups** (`display_group`, defaultable from `competition_type`):
  `leagues` (domestic_league) · `cups` (domestic_cup, domestic_super_cup) ·
  `continental-club` (continental_club, continental_super_cup, club_qualifying) ·
  `national-teams` (world_championship, continental_championship, qualifying).
- **Country hubs** (`country` field): `/football/germany/` lists BL1, BL2, DFB-Pokal …
  ordered by `tier` + `sort_order`. International competitions appear under their
  confederation grouping on `/competitions/`, not under a country.

The landing page (#367) surfaces both axes; the nav exposes
`Competitions · Matches · Teams · Players · Standings · Stats`.

**Home composition (agreed hybrid, CPO 2026-06-10).** The MVP's competition-card
landing is obsolete for the website. The home is fixtures-first with stats/storylines
below: (1) **fixtures hero** — upcoming matches across competitions, the product's core
feature elevated (⚠ needs a cross-competition fixtures feed; the per-competition list +
fixture page exist); (2) **hybrid browse** (groups + country hubs, registry-driven);
(3) **storylines/trending** from `mart_team_profile` (⚠ needs the data-to-text narrative
generator); (4) **stats** — leaderboard teasers + mini standings. Full module spec +
data status: `docs/ui_design_brief.md` §6.3.

## 5. Templates → data contract

One template per entity type; each consumes exactly the export files listed.
Adding a competition/team/player adds pages with **zero template changes**.

| Template | Export file(s) (`data/…`) | Upstream marts |
|---|---|---|
| Landing | `landing.json` | landing feed (#365; next rounds, kickoff, trending from `mart_team_profile`) |
| Competitions index / country hub | `nav.json` (registry-derived) | registry seed + grouping fields |
| Competition hub + season | `competitions/{league_code}/{season}.json` | `mart_standings`, `mart_matchday_insights`, `mart_leaderboards` |
| Fixture page ⭐ | `fixtures/{fixture_api_id}.json` | `mart_team_momentum` (W1), `mart_team_season_record` (W2), `mart_fixture_standing_context` (rank), `mart_head_to_head` (H2H); drill-down (follow-up): `mart_player_momentum`, `mart_team_momentum_window`, `mart_team_fixture_stats`/`mart_player_fixture_stats`. **NOT** `mart_matchday_insights` — that is the MVP's presentation pivot of the same momentum mart; v2 reads the source marts directly to avoid coupling + duplication. |
| Team profile ⭐ | `teams/{team_api_id}.json` | `mart_team_profile`, `mart_team_season`, `mart_standings`, fixtures list |
| Player profile ⭐ | `players/{player_api_id}.json` | `mart_player_profile`, `mart_player_match_log` |
| Standings | within competition JSON | `mart_standings` (league + group tables, incl. WC group letters) |
| Leaderboards | `leaderboards/{league_code}/{metric_id}.json` | `mart_leaderboards`, player catalogue metrics |
| Head-to-head | `h2h/{pair_key}.json` | `mart_head_to_head` (**#375 — the one missing mart**) |
| Metric glossary | `metrics.json` | `metric_catalogue` seed (descriptions, formulas, labels) |

Export data is **locale-independent**; all display strings resolve at build time from
the locale files + catalogue i18n keys. Numbers/dates format with the locale's
`Intl` conventions (port `fmtNum`/`fmtPct`/`"-"`-for-null behavior from `site/i18n.js`).

## 6. SEO surface (built by #369)

| Page | schema.org type | Notes |
|---|---|---|
| Fixture | `SportsEvent` | teams as `competitor`, kickoff, venue snapshot |
| Team | `SportsTeam` | crest as `logo`, memberOf league |
| Player | `Person` (athlete) | photo, nationality |
| All | `BreadcrumbList` | mirrors the URL hierarchy |

- Templated `<title>` / meta description / canonical per entity per locale.
- `hreflang` across all locales + `x-default`; per-locale `sitemap.xml` under a sitemap
  index; `robots.txt`.
- OpenGraph/Twitter cards on every page (shareability is a north-star pillar).
- **Data-to-text narratives**: short, metric-backed sentences generated at build time
  per page (anti-thin-content). Honest only — generated from real mart values, skipped
  when data is insufficient. Generator lives in the export layer.
- Internal-linking graph: fixture ↔ teams ↔ players ↔ competition ↔ h2h on every page.

## 7. Repository & build layout

```
site_v2/                    Astro project (#362) — isolated from site/
  src/pages/[locale]/…      file-based + programmatic routes per §3
  src/components/           design-system components (#366)
  src/i18n/                 locale chrome strings (#370)
scripts/export_site_data.py per-entity export (#365) — NEW, additive;
                            export_pages_data.py (legacy) keeps running until #377
data/ (build artifact)      per-entity JSON, slug map, export manifest — not committed
.github/workflows/          v2 build/deploy workflow, path-filtered to site_v2/**;
                            the legacy pages-match-preview.yml is untouched until cutover
```

- v2 deploys to a **separate Pages path/preview** during the build phase; the live URL
  serves the MVP until cutover (#377: parity check → CPO sign-off → switch → redirects
  from old URLs → retire `site/` + legacy export in a separate cleanup PR).
- Monetization hooks: templates keep a named slot (header/in-content) rendering nothing —
  placeholders only, no implementation.

## 8. Decisions log

| Decision | Status |
|---|---|
| Astro, static-only, GitHub Pages | locked (CPO, 2026-06-10) |
| Hybrid IA (groups + country hubs), registry-driven | locked (CPO, 2026-06-10) |
| Current MVP stays live until parity cutover | locked (CPO, 2026-06-10) |
| All locales URL-prefixed; root redirects by browser language, `en` fallback | proposed default — CPO may override fallback locale |
| Slug formats per §3 | proposed default — review in #363 PR |
| Island framework for charts (svelte vs preact) | open — decide in #362 |
| Analytics tool (Plausible / Umami / GA4) | open — decide in #372 with Legal (#374) |
