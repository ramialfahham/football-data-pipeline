# 01 — Fixture page ⭐ (#391)

> The heart of the product (brief §5 priority 1). Every field below is verified
> against the export (`scripts/export_site_data.py`, `fetch_fixture_payloads`) and
> the mart columns as of 2026-06-11.

## 1. Purpose

Pre-match: within seconds, give the fan **five things worth saying about this match**
(north star). The **stop-scrolling moment** is the side-by-side form comparison with
its W1↔W2 contrast — "hot right now vs the season reality" — switchable in place.
Secondary hook: the past-meetings record ("they've never beaten them at home" energy).

## 2. URL

```
/{locale}/{competition-slug}/matches/{yyyy-mm-dd}-{home-name}-vs-{away-name}/
```

- Slug from `slug` in the payload (built by `fixture_slug()`: kickoff date + kebab
  team names; falls back to `fixture-{id}`).
- `fixture_id` in the payload is the provider fixture id (verified:
  `fixture_sk == fixture_api_id` for all 20,149 fixtures).
- Breadcrumb: Home → {competition} → Matches → {this match}.

## 3. Data sources

| File | Used for |
|---|---|
| `data/fixtures/{fixture_id}.json` | Everything on this page |
| `data/matchstats/{played_fixture_sk}.json` | The drill-down target when a past-match row is clicked (§7) — exists exactly for fixtures referenced by a form window |

Payload top level: `fixture_id, slug, kickoff, status, league_code, league_name,
season, round, venue, home, away, head_to_head`.
Each side (`home`/`away`): `team_id, name, crest, country, w1, w2, standing,
form_window[], top_players[]`.

## 4. Layout

Mobile (primary). `▸` = link. Sections numbered for §5.

```
┌────────────────────────────────────────────┐
│ ▸Home › ▸Bundesliga › Matches              │  (1) breadcrumb
├────────────────────────────────────────────┤
│        Sat 13 Dec · 15:30 · Matchday 14    │  (2) match header
│   [crest]                       [crest]    │
│  ▸Bayern München    vs    ▸Borussia        │
│                            Dortmund        │
│        Allianz Arena · Bundesliga          │
│  ┌ #1 · 33 pts ┐          ┌ #4 · 26 pts ┐  │  (2a) standing chips
├────────────────────────────────────────────┤
│  [ Last 5 ●——○ Season ]                    │  (3) form comparison
│  5 games · 13/15 pts    5 games · 9/15 pts │  (3a) window header
│  Form  W W W D W        W L W W D          │  (3b) form strings
│  Goals/match       2.6 ▐████▌▐██▌ 1.8      │  (3c) metric rows
│  Goals against     0.6 ▐█▌  ▐███▌ 1.4      │
│  Shots/match      17.2 ▐████▌▐███▌ 14.1    │
│  Shot accuracy %    48 ▐███▌ ▐███▌ 44      │
├──────────────— fold (~700px) —─────────────┤
│   …13 more metric rows…                    │
│  ⓘ incl. Champions League, DFB-Pokal       │  (3d) window caption
├────────────────────────────────────────────┤
│  RECENT MATCHES                            │  (4) form drill-down
│  Bayern                                    │
│  ▸ W 3-1  H  Gladbach [crest]  BL1  6 Dec  │
│  ▸ W 2-0  A  Arsenal  [crest]  UCL  3 Dec  │
│    …up to 5 rows…                          │
│  Dortmund                                  │
│    …up to 5 rows…                          │
├────────────────────────────────────────────┤
│  PLAYERS TO WATCH                          │  (5) top players
│  Bayern: [photo] ▸Kane FW · 5 gls · 2 ast  │
│    …top 5 per side…                        │
├────────────────────────────────────────────┤
│  HEAD TO HEAD                              │  (6) past meetings
│  Bayern 18 — 8 draws — 6 Dortmund          │
│  ▐██████████▌▐███▌▐████▌  (32 meetings)    │
│  Last: 2-2 · Bundesliga · 12 Apr 2025      │
│  · 1-0 W · BL1 · 12 Apr 25                 │
│    …up to 10 recent meetings…              │
│  ▸ Full head-to-head                       │
├────────────────────────────────────────────┤
│  ABOUT THIS MATCH                          │  (7) narrative (slot)
│  (data-to-text — GAP-03; until then a      │
│   templated factual sentence)              │
├────────────────────────────────────────────┤
│  ▸Bayern profile ▸Dortmund profile         │  (8) internal links
│  ▸Bundesliga ▸Table ▸Top scorers           │
└────────────────────────────────────────────┘
```

**Above the fold (mobile)**: breadcrumb + header + standing chips + segment control +
window header + form strings + the first ~4 metric rows. The fold lands inside (3) by
design — the comparison must be visibly "going on" to pull the scroll.

**Desktop (≥ ~900px)**: header full-width; (3) stays a single centered column
(comparison is inherently two-sided already); (4) and (5) reflow to two columns
(home | away side by side); (6)–(8) full-width. Max content width ~1100px.

## 5. Module bindings

Labels: `chrome` = UI string from the locale files; `cat:{metric_id}` = catalogue
i18n key. Formats/direction from the catalogue row named.

### (1) Breadcrumb + (2) Match header

| Element | JSON key(s) | Notes / links |
|---|---|---|
| Competition crumb + name | `league_code`, `league_name` | ▸ competition hub |
| Kickoff | `kickoff` (UTC ISO) | locale date+time; TZ enhancement per 00 conventions |
| Round | `round` | provider string — localization is GAP-08 |
| Venue | `venue` | plain text; may be null → omit line |
| Status | `status` (`NS`/`TBD`) | `TBD` → show date, "time TBD" (chrome) |
| Team names/crests | `home.name`, `home.crest`, `away.name`, `away.crest` | ▸ team profiles; crest fallback = monogram (brief §4) |

### (2a) Standing chips — per side `standing`

| Element | JSON key | Format |
|---|---|---|
| Rank | `standing.league_rank` | cat:league_rank (integer, lower better) |
| Points | `standing.standing_points` | integer |
| Played | `standing.standing_played` | integer (chip tooltip/secondary) |
| Goal diff | `standing.standing_goals_diff` | signed integer (secondary) |
| Group | `standing.group_name` | shown for group-stage comps ("Group A") |

`standing` is **null by design** for knockout rounds (`is_knockout`) and
overlapping-table leagues → omit the chip entirely, no empty state.
`standing.standing_form` is NOT rendered here (the comparison's form strings come
from `form_window`, §3b) — it belongs to the competition-hub table (04).

### (3) Form comparison — per side `w1` / `w2` (segment control)

Window header (3a): W1 `w1.games_in_window` + `w1.points_won`; W2 `w2.games_played`
+ `w2.points_won` — points as `points_fraction` ("13/15", denominator = games × 3).

Form strings (3b): derived from `form_window[].result` in `recency_rank` order
(W/D/L chips, most recent first). Not a separate field.

Metric rows (3c) — identical set in W1 and W2; key = catalogue `metric_id`:

| Label (catalogue) | JSON key | Format | Lower better |
|---|---|---|---|
| Goals / match | `goals_per_match` | decimal_1 | |
| Goals against / match | `goals_against_per_match` | decimal_1 | ✓ |
| Shots / match | `shots_per_match` | decimal_1 | |
| Shot accuracy | `shot_accuracy` | percent | |
| Danger-zone ratio | `danger_zone_ratio` | percent | |
| Finishing efficiency | `finishing_efficiency` | percent | |
| Passes / match | `passes_per_match` | decimal_0 | |
| Pass accuracy | `pass_accuracy` | percent | |
| Corners / match | `corner_kicks_per_match` | decimal_1 | |
| Corners conceded / match | `corners_conceded_per_match` | decimal_1 | ✓ |
| Save ratio | `save_ratio` | percent | |
| Key passes / match | `key_passes_per_match` | decimal_1 | |
| Tackles / match | `tackles_per_match` | decimal_1 | |
| Interceptions / match | `interceptions_per_match` | decimal_1 | |
| Blocks / match | `blocks_per_match` | decimal_1 | |
| Duels won | `duels_won_pct` | percent | |
| Dribbles success | `dribbles_success_pct` | percent | |

Row order above is a **proposed default** (headline attacking/defending first,
volume/duel stats later) — CPO may reorder at review. Paired bars are normalized to
the larger of the two values (a relative share, never a probability).

Window caption (3d):
- W1: `w1.contributing_competitions` → "incl. {list}" when it names more than the
  fixture's own competition; coverage note from `w1.games_with_team_stats` when
  `< games_in_window` ("stats from N of M matches", chrome).
- W2: `w2.window_type` — `season_to_date` → "{season} season so far";
  `prev_season` → "last season ({w2.season_api_year})" (chrome templates; the
  season string uses the registry's split/calendar-year rule).

### (4) Form drill-down — per side `form_window[]` (≤5 rows, `recency_rank` asc)

| Element | JSON key | Notes |
|---|---|---|
| Result chip | `result` | W/D/L letter+color |
| Score | `goals_for`, `goals_against` | always from this team's perspective |
| Home/away | `home_away` | "H"/"A" badge |
| Opponent | `opponent_name`, `opponent_logo_url` | ▸ opponent team profile (`opponent_team_sk`) |
| Competition | `played_league_code` | badge — W1 is cross-competition |
| Date | `played_kickoff_datetime` | locale short date |
| Round | `played_round_name` | tooltip/secondary (GAP-08 applies) |
| Click-through | `has_team_stats`, `has_player_stats`, `played_fixture_sk` | row links to `matchstats/{played_fixture_sk}` **only when** `has_team_stats` or `has_player_stats` — else not clickable + "match stats not available" (chrome, a designed COMMON state) |

### (5) Top players — per side `top_players[]` (≤5, ranked goals → assists → key passes)

Compact row: `player_photo_url`, `player_name` (▸ player profile via `player_sk`),
`position_code` badge, then by position:
- Outfield: `goals_total`, `goals_assists`, `shots_on`, `passes_key`
- GK (`position_code = 'G'`): `goals_saves`, `save_pct`

Full per-player window stats available in the payload for an expanded row (design
decision): `passes_total/passes_accurate/pass_accuracy_pct, tackles_total,
tackles_blocks, tackles_interceptions, duels_won/duels_total/duels_won_pct,
dribbles_success/dribbles_attempts/dribbles_past, offsides, penalty_won/
penalty_committed, cards_yellow, cards_red, games_in_window`.
Ranking is transparent (counts), never a composite score.

### (6) Head-to-head — `head_to_head` (perspective = **home team**)

| Element | JSON key(s) | Notes |
|---|---|---|
| Record bar + counts | `wins`, `draws`, `losses`, `total_meetings` | "{home} {wins} — {draws} draws — {losses} {away}"; `losses` = away team's wins |
| Goals | `goals_for`, `goals_against` | secondary line ("48:39 goals") |
| Last-5 split | `meetings_last5`, `wins_last5`, `draws_last5`, `losses_last5` | "recent edge" sub-row |
| Last meeting | `last_meeting_at`, `last_meeting_league_code`, `last_meeting_goals_for`, `last_meeting_goals_against`, `last_meeting_result` | one highlighted row |
| Recent meetings (≤10) | `recent_meetings[]`: `kickoff_datetime`, `league_code`, `goals_for`, `goals_against`, `result` | **display-only** — the struct carries no fixture reference, so rows are not clickable (06 spec decides whether to extend) |
| Full H2H link | — | ▸ `/h2h/{pair}/` (page export is GAP-06) |

All-competitions, all-time record (mart scope). Raw facts only — no derived ratios.

### (7) Narrative + (8) internal links

Narrative: a named slot. Until GAP-03 lands, render one templated factual sentence
from already-bound fields (e.g. home `w1.points_won`/`games_in_window` + h2h
`total_meetings`) or omit. Never fabricated content.
Internal links: both team profiles, competition hub, `/table/`, `/top-scorers/`,
full H2H — the SEO internal-link graph (§8).

## 6. States

| State | Trigger | Render |
|---|---|---|
| Preview (normal) | `status` = `NS` | everything above |
| Time TBD | `status` = `TBD` | date without time + "time TBD" |
| No form data (side) | `w1`/`w2` = null | that column shows the designed empty state ("No recent matches"); the other side still renders |
| No standings context | `standing` = null | omit chips entirely (by design: knockout/overlapping) — not an error, no "-" |
| Prev-season fallback | `w2.window_type` = `prev_season` | W2 labelled "last season ({year})" |
| Reduced stat coverage | `games_with_team_stats < games` | coverage caption (3d); metric nulls → "-" per row |
| Never met | `head_to_head` = null | "First-ever meeting" styled state |
| Stats-less past match | `has_team_stats` & `has_player_stats` false | row not clickable + microcopy |
| Null metric value | any rate null | "-" + no bar (that row, that side) |
| **Report (finished match)** | `status` = FT | **no payload today — GAP-07.** URL stays (preview → report is the promise); until then the page is not regenerated after kickoff |
| Thin page | fixture not in export | page not generated (export covers upcoming NS/TBD fixtures only) |

## 7. Interactions

- **W1/W2 segment**: swaps the comparison values + captions in place. No data
  refetch (both windows are in the payload). Lightweight island or CSS toggle —
  implementation is #368's call; both windows must be crawlable in the HTML.
- **Past-match row** → `matchstats/{played_fixture_sk}` page (or overlay on
  desktop — design call), when flagged available.
- Team names/crests → team profiles; players → player profiles; H2H → pair page.
- No swipe-carousel between fixtures (that is the MVP's pattern, retired in v2);
  prev/next-match navigation belongs to the competition fixtures list (04).

## 8. SEO

- `schema.org/SportsEvent`: `startDate` = `kickoff`, `competitor` = both teams
  (SportsTeam: name + crest), `location` = `venue` (when present), part of
  `league_name`.
- Title: `{home.name} vs {away.name} — Form, Head-to-Head & Stats | {league_name}`
  (localized template).
- Meta description: templated from real fields (round, kickoff date, h2h record)
  until GAP-03 narratives.
- `BreadcrumbList` mirroring §2; canonical per locale + hreflang set + OG/Twitter
  card (both crests, kickoff).

## 9. Component census

Breadcrumb ➕ · fixture header · standing chip ➕ · segment control · metric
comparison row · window caption ➕ · form string · fixture row · result chip ·
player row · H2H record block ➕ · empty states · narrative slot ➕ ·
internal-links footer ➕. (➕ = new vs brief §7 — see 00 census.)

## 10. Gaps

- [GAP-03](99_gaps_register.md) — data-to-text narrative generator (section 7 slot).
- [GAP-06](99_gaps_register.md) — `/h2h/{pair}/` page has no export target (link in section 6).
- [GAP-07](99_gaps_register.md) — no report-state payload for finished fixtures (§6).
- [GAP-08](99_gaps_register.md) — `round_name` is a raw provider string; no localization strategy yet.
