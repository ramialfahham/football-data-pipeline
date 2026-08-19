# Site architecture — Matchday Pilot (programmatic content site)

> The contract for epic #361. Every v2 workstream — templates (#368), export (#365),
> SEO (#369), i18n (#370), design (#366), go-live (#377) — builds against this
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
  → Firebase Hosting (CDN) → indexed, multilingual
```

## 2. Hard constraints (locked)

| Constraint | Source |
|---|---|
| **The Matchday IQ MVP (`site/`) is RETIRED — offline, Pages deleted, frozen.** v2 (Matchday Pilot) lives in `site_v2/` and is the only surface being built. There is **no parity requirement, no cutover and no restore**; #377 is now the go-live of v2 itself, not a switch away from the MVP. Legal pages become a v2 build requirement (#799). | CPO, 2026-07-21, superseding CPO 2026-06-10 |
| **Tech stack: Astro**, static output only, deployed to Firebase Hosting (vendor chosen by CPO 2026-07-24, superseding the original GitHub Pages plan). Interactivity via islands (charts, search) — no SSR, no backend. | Epic #361 |
| **Competition IA**: the competitions index page (`/{locale}/competitions/`, built 2026-08-18) groups by `competition_type` from `mart_competition_index`; country hubs remain unbuilt. Zero-file rule holds. ⚠ The original "hybrid" pairing of a group axis AND a country axis on the home page was **dropped 2026-08-19** with the browse block. | Epic #361; CPO 2026-08-19 |
| **Metric governance: catalogue-only.** Pages render `metric_catalogue` metrics by their catalogue formula; labels come from catalogue i18n keys. New metrics require a CPO-approved catalogue extension first. | #327 / governance memory |
| **Data honesty**: nulls render as "-", never fabricated zeros; no unmodelled KPIs, no fabricated probabilities. Pages with insufficient data are not generated (no thin pages). | north_star.md |
| `league_code` is the partition key everywhere; no competition hardcoded in templates or export logic. | CLAUDE.md |

## 3. URL scheme

All pages live under a locale prefix. Trailing slashes; lowercase kebab-case slugs.

```
/{locale}/                                                   landing
/{locale}/competitions/                                      all competitions (grouped by type)
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
- **`hreflang="x-default"` points at the `en` URL, NOT at `/`** (#844). This paragraph did not say
  which, and the answer was about to be settled implicitly by a checker — recorded here instead,
  because a machine-enforced rule that exists only in code is not a documented decision.
  Reasoning: `/` is a CLIENT-SIDE language redirect, and a crawler resolving `x-default` cannot run
  it, so pointing there hands the fallback to a page that renders nothing for the audience
  `x-default` exists to serve. The `en` URL is a real page. `/` keeps the job this paragraph gives
  it (a human arriving with no locale match); it simply is not the hreflang fallback.
  If the CPO overrides the `en` fallback above, `x-default` follows it — the two are one decision.

### Slugs (locale-independent)
- **Competition**: `slug` field in the registry (#364), e.g. `bundesliga`,
  `premier-league`, `world-cup`. Never derived from display names at build time.
- **Season**: from `season_api_year` + registry `season_type`: split-year → `2025-26`,
  calendar-year → `2026`.
- **Team**: `{kebab-name}`, e.g. `bayern-munchen`, `aston-villa`. **No provider id** — CPO
  ruling 2026-07-27, *"there is no aston-villa-66"*. Derived in
  `base_apif__teams_global` from the CORRECTED name (#850) and published on `dim_team`,
  because assigning an identifier is derivation and the export is the consumption layer
  (#846). Collisions resolve by a **symmetric, closed ladder**: an uncontested name takes
  its own slug; a contested one is given to *nobody* and every contender takes
  `{name}-{country}`; if that is still not free anywhere, or the country is missing, or
  the name folds to nothing, the provider id is appended. That last branch is the **only**
  place an id appears in any URL, and today it fires for exactly two rows — one club the
  provider stores twice (#850's open alias decision).
- **Player**: `{kebab-name}-{player_api_id}`, e.g. `jamal-musiala-1090`. Still carries the
  id: 18.5% of provider player names collide (1.6% on the full name), so the team scheme
  does not transfer unchanged. Moving player slugs to the warehouse is its own work.
- **Fixture**: `{yyyy-mm-dd}-{home-team-slug-name}-vs-{away-team-slug-name}` under the
  competition's `/matches/`; the export carries `fixture_api_id` for the data join. Built in
  the export from team NAMES, so it does not yet share the team slug's transliteration —
  tracked with the player move.
- **H2H pair**: lower `team_api_id` first → one canonical URL per pair; the reversed
  order is generated as a redirect/canonical alias.
- **Metric**: `metric_id` from `metric_catalogue`, kebab-cased.

#### Spelling: fold to the base letter, expand only where there is none
CPO ruling on escalation E3, 2026-07-27. A character that decomposes to a base letter takes
that letter; a character with no base letter takes its conventional digraph:

| | |
|---|---|
| `Bayern München` → `bayern-munchen` | `ü` HAS a base letter |
| `Rot-Weiß Essen` → `rot-weiss-essen` | `ß` has NONE |

Those are **one rule, not an inconsistency** — the same rule `unidecode` and `iconv
//TRANSLIT` implement, and what Transfermarkt ships. Do not "fix" the apparent mismatch by
expanding umlauts to `ue`/`oe`/`ae`: it would change 17 German clubs' URLs for nothing.
The map lives in `macros/team_name_normalization.sql`; `assert_team_name_slug_alphabet`
fails the build on a letter it does not cover. Add targets from an external source of
record, never from the glyph's shape — two were wrong that way on the first attempt.

#### ⚠ Slugs are NOT yet stable across renames
The slug is **derived on every build**, so a rename or a newly ingested same-named team can
change a URL. Nothing is published yet — no public site, every page `noindex` — so no link
equity is at risk today, and the CPO deliberately deferred persistence rather than making
the warehouse non-reproducible before launch.

**Before this site goes public, #852 must land**: the slug assigned once and stored, plus the
alias/301 mechanism, so the promise below holds. Until then, treat it as an intent:

- Slug map (entity → slug → id) is produced by the export (#365) and is the single
  source for routing and internal links. **Target state (#852, not yet true):** slugs never
  change once published; a rename produces a new alias, not a new canonical.

## 4. Competition IA

⚠ **This section described TWO axes reached from the home page's browse block. That block was
dropped 2026-08-19, so neither axis has a page today.** `display_group` survives only as an input
to `build_nav()`/`nav.json` (an export target with no frontend consumer — see §3's note and the
seed's own column doc); country hubs were never built. The live route to a competition is the
competitions index page, which groups by the finer `competition_type` instead — see the note
below and `docs/wireframes/08_browse.md`. Both axes are kept documented because the registry
fields still exist and country hubs are still intended.

The two registry-driven axes, as designed (#364 adds the fields):

- **Competition groups** (`display_group`, defaultable from `competition_type`):
  `leagues` (domestic_league) · `cups` (domestic_cup, domestic_super_cup) ·
  `continental-club` (continental_cup, continental_super_cup, club_qualifying, club_world_cup,
  intercontinental_super_cup) ·
  `national-teams` (world_championship, continental_championship, qualifying).
- **Country hubs** (`country` field): `/football/germany/` lists BL1, BL2, DFB-Pokal …
  ordered by `tier` + `sort_order`. International competitions appear under their
  confederation grouping on `/competitions/`, not under a country.
  ⚠ `/competitions/` itself (#62 step 5, GitLab #54, built 2026-08-18) groups by the FINER
  `competition_type` (8 categories) rather than the `display_group` rollup above, and by
  `region_rank`/kickoff proximity rather than `tier`/`sort_order` (both retired for that page,
  `escalations.log` 2026-08-16). `display_group` and `sort_order` still exist and still feed
  `build_nav()`/`nav.json`, but NOT the home page any more: the home page's browse block was
  DROPPED 2026-08-19 (CPO: "drop the browse section"), so this section no longer describes it —
  see `docs/wireframes/08_browse.md` for the still-live competitions-index page's actual
  grouping/ordering rule instead. Country hubs themselves remain unbuilt.

⚠ **The landing page (#367) no longer surfaces this hybrid-browse axis** (dropped 2026-08-19,
same ruling as above) — the sentence below is the ORIGINAL 2026-06-10 composition and is kept for
history, not as a current description; item (2) is gone, and (3)/(4) were already separately
superseded before today (`docs/wireframes/10_home.md` §0). The nav exposes
`Competitions · Matches · Teams · Players · Standings · Stats`.

**Home composition (agreed hybrid, CPO 2026-06-10).** The MVP's competition-card
landing is obsolete for the website. The home is fixtures-first with stats/storylines
below: (1) **fixtures hero** — upcoming matches across competitions, the product's core
feature elevated (⚠ needs a cross-competition fixtures feed; the per-competition list +
fixture page exist); (2) ~~**hybrid browse** (groups + country hubs, registry-driven)~~ —
DROPPED 2026-08-19, see the warning above; (3) **storylines/trending** from `mart_team_profile`
(⚠ needs the data-to-text narrative generator); (4) **stats** — leaderboard teasers + mini
standings. Full module spec + data status: `docs/ui_design_brief.md` §6.3.

## 5. Templates → data contract

One template per entity type; each consumes exactly the export files listed.
Adding a competition/team/player adds pages with **zero template changes**.

| Template | Export file(s) (`data/…`) | Upstream marts |
|---|---|---|
| Landing | `landing.json` | `core.fct_fixture` + `core.dim_team` (the next-matchday hero), plus `mart_competition_index` for `region_rank` — read `fetch_landing_payload` in `scripts/export_site_data.py` for the live list, which is the authority. ⚠ NOT `mart_team_profile`: the trending block it fed was cut 2026-08-08, as the browse block was dropped 2026-08-19. Top players / Top teams will add marts here when built |
| Competitions index / country hub | `competition_index.json` (#62 step 4) | `mart_competition_index` |
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
scripts/export_site_data.py per-entity export (#365) — the ONLY live export
                            export_pages_data.py (legacy) is DEAD, kept for reference
data/ (build artifact)      per-entity JSON, slug map, export manifest — not committed
.github/workflows/          v2 build/deploy workflow, path-filtered to site_v2/**;
                            pages-match-preview.yml is DISABLED (`disabled_manually`)
```

- v2 deploys to **Firebase Hosting** (`.web.app`, unlisted, `noindex`). **There is no live MVP for it
  to serve behind** — `site/` went offline 2026-07-21 and its Pages deployment was deleted, so #377 is
  v2's own go-live on `matchdaypilot.com`: legal/imprint (#799) → CPO sign-off → connect the custom
  domain → drop `noindex` and publish the sitemap. **No parity check, no switch, and no redirects from
  old URLs** (the old URLs are gone and were never indexed under the new domain). Retiring `site/` +
  the legacy export is a cleanup PR that no longer blocks anything.
- Monetization hooks: templates keep a named slot (header/in-content) rendering nothing —
  placeholders only, no implementation.

## 8. Decisions log

| Decision | Status |
|---|---|
| Astro, static-only, Firebase Hosting (was GitHub Pages) | locked (CPO, 2026-06-10; vendor updated 2026-07-24) |
| ~~Hybrid IA (groups + country hubs), registry-driven~~ | **PARTLY SUPERSEDED** (CPO, 2026-08-19): the home page's browse block that rendered both axes is dropped. The registry fields remain, country hubs remain intended but unbuilt, and the live route to a competition is the competitions index page (grouped by `competition_type`) — see §4 |
| ~~Current MVP stays live until parity cutover~~ | **SUPERSEDED** (CPO, 2026-07-21): the MVP is retired, so there is no parity gate and no cutover — see §2 |
| All locales URL-prefixed; root redirects by browser language, `en` fallback | proposed default — CPO may override fallback locale |
| Slug formats per §3 | proposed default — review in #363 PR |
| Island framework for charts (svelte vs preact) | open — decide in #362 |
| Analytics tool (Plausible / Umami / GA4) | open — decide in #372 with Legal (#374) |
