# 02 — Team profile ⭐ (#391)

> Field-bound against `shape_team_payload` / `mart_team_profile` (verified
> 2026-06-11). Metric rows follow the LOCKED contract in
> [`metrics_display.md`](metrics_display.md).

## 1. Purpose

The team's season story at a glance, for a fan deciding "how good are they
really?". The **stop-scrolling moment** is **deserved vs actual** — "they dominate
play more than results show" — two real ratios and their labelled gap, the
product's signature differentiator (brief §6.2). Secondary hooks: the
games-aligned year-over-year comparison and active streaks.

## 2. URL

```
/{locale}/teams/{kebab-name}-{team_id}/
```

- `slug` from the payload (latest-season name + id, e.g. `bayern-munchen-157`).
- Breadcrumb: Home → Teams → {team}.
- One page per team; competition-season is a selector on the page (not a URL
  segment) — keeps one canonical team URL.

## 3. Data sources

`data/teams/{team_id}.json` — top level: `team_id, slug, name, country, crest`;
`seasons[]` (one row per competition-season, sorted year desc) carrying record,
season rates, deserved-vs-actual, YoY and streaks (identity stripped per row).

## 4. Layout

```
┌────────────────────────────────────────────┐
│ ▸Home › ▸Teams › Bayern München            │  (1) breadcrumb
├────────────────────────────────────────────┤
│  [crest]  Bayern München                   │  (2) identity header
│           Germany                          │      (founded/venue: GAP-01)
│  [ Bundesliga 2025/26          ▾ ]         │  (3) competition-season selector
├────────────────────────────────────────────┤
│  #1 · 33 pts        Form W W D W W         │  (4) record block
│  14 played · 10W 3D 1L · 31:11 · +20       │
│  Clean sheets: 6                           │
├────────────────────────────────────────────┤
│  DESERVED VS ACTUAL                        │  (5) the differentiator
│  Shot share        62% ▐██████▌            │
│  Points capture    79% ▐███████▌           │
│  Gap: −17 — results outpace play (ⓘ)       │
├──────────────— fold (~700px) —─────────────┤
│  VS LAST SEASON (after 14 games)           │  (6) year-over-year
│  Points        33 ↑ +5      (28)           │
│  Goals for     31 ↑ +4      (27)           │
│  Goals against 11 ↓ −3      (14)           │
├────────────────────────────────────────────┤
│  STREAKS                                   │  (7) streak chips
│  ⬡ 8 unbeaten ⬡ 3 wins ⬡ 2 clean sheets    │
├────────────────────────────────────────────┤
│  SEASON METRICS                            │  (8) metric list (locked
│  GOALS                                     │      contract, single-value)
│  Ø Goals            2.2                    │
│  …16 rows under group subheads…            │
├────────────────────────────────────────────┤
│  FIXTURES                                  │  (9) next + recent (GAP-15)
├────────────────────────────────────────────┤
│  ▸Bundesliga ▸Table ▸Top scorers ▸Squad?   │  (10) internal links
└────────────────────────────────────────────┘
```

**Above the fold**: identity + selector + record block + deserved-vs-actual. The
differentiator deliberately sits above the fold — it is the screen's hook.

**Desktop (≥ ~900px)**: two columns — left: record + deserved-vs-actual + YoY +
streaks; right: season metrics list + fixtures. Header full-width.

## 5. Module bindings

All season-scoped keys come from the selected `seasons[]` row.

### (2) Identity + (3) selector

| Element | JSON key | Notes |
|---|---|---|
| Name / crest / country | top-level `name`, `crest`, `country` | crest fallback = monogram |
| Founded, venue | — | **GAP-01** (in `dim_team`, not exported) |
| Selector options | `seasons[].league_code` + `season_api_year` (+ `competition_type`) | label via registry name + season slug rule; default = most recent season, domestic league first |

### (4) Record block

| Element | JSON key | Format |
|---|---|---|
| Rank | `latest_rank` | integer; null → omit (cups/knockout) |
| Points | `points` | integer |
| Played / W / D / L | `played`, `wins`, `draws`, `losses` | integers |
| Goals | `goals_for`:`goals_against`, `goal_diff` | signed for diff |
| Clean sheets | `clean_sheets` | integer (count; the x/y form is the window-metric variant) |
| Form string | `latest_form` | W/D/L chips (standings-derived, this competition) |

### (5) Deserved vs actual

| Element | JSON key | Display |
|---|---|---|
| Shot share | `shot_share_season` | percent + bar |
| Points capture | `points_capture_season` | percent + bar |
| Gap | `performance_vs_results_gap` | signed percentage-point delta + plain-language label ("dominates play more than results show" / inverse); ⓘ → glossary |

Two real ratios and their difference — NEVER a composite score gauge (ruled).

### (6) Year-over-year (domestic leagues only)

Header: "after {yoy_games_played_cutoff} games" — the games-aligned cutoff.

| Row | This season | Prev | Delta |
|---|---|---|---|
| Points | `points_this_season` | `points_prev_season` | `points_delta_yoy` |
| Goals for | `goals_for_this_season` | `goals_for_prev_season` | `goals_for_delta_yoy` |
| Goals against | `goals_against_this_season` | `goals_against_prev_season` | `goals_against_delta_yoy` |

Delta direction: goals against is better when negative (`lower_is_better`).
All-null → module renders its designed absent state (§6).

### (7) Streaks

`unbeaten_run`, `win_run`, `winless_run`, `clean_sheet_run`, `scoring_run` —
chips, only runs ≥ 2 shown, positive runs first; `winless_run` is a negative
signal (styled accordingly). All < 2 → module omitted.

### (8) Season metrics — the locked 16-row contract, single-value layout

Label + one value per row (no comparison bars — single team), group subheads,
same order/tiers as [`metrics_display.md`](metrics_display.md). Available today:

| Contract row | JSON key (season variant) |
|---|---|
| Ø Goals | `goals_per_match_season` |
| Ø Goals against | `goals_against_per_match_season` |
| Clean sheets (x/y) | derivable: `clean_sheets` of `played` |
| Ø Shots | `shots_per_match_season` |
| % Shots from box | `danger_zone_ratio_season` |
| % Goals per shot on target | `finishing_efficiency_season` |
| Ø Passes | `passes_per_match_season` |
| % Pass accuracy | `pass_accuracy_season` |
| Ø Corners | `corner_kicks_per_match_season` |
| Ø Corners against | `corners_against_per_match_season` |
| % Save percentage | `save_ratio_season` |

**Missing season variants (GAP-13)**: Ø Shots on target, Ø Duels, % Duels won,
Ø Defensive actions, Ø Key passes — the full-season intermediate predates the
player-stat-derived team metrics. Until GAP-13 ships these rows render only in
the fixture comparison, not here. Coverage caption from
`stat_coverage_season_games` vs `season_games_played` ("stats from N of M").
`shot_accuracy_season` exists but is unrendered (contract).

### (9) Fixtures + (10) links

**Next fixture + last 5 results** per (team, season) — scope ruled (GAP-15,
approved): ships via the team-export extension from `fct_fixture`/legs. Rows
reuse the fixture-row component (opponent, H/A, score, result chip; next fixture
links to its fixture page). Until the data PR lands the section renders links to
the competition's `/fixtures/` page. Internal links: competition hub, `/table/`,
`/top-scorers/`; player links live on fixture pages (no squad surface yet — no
squad mart).

## 6. States

| State | Trigger | Render |
|---|---|---|
| Normal | — | everything above |
| No rank | `latest_rank` null (cup/knockout phase) | rank chip omitted |
| No YoY | all `*_yoy` null (non-domestic, or prior season not ingested, or before any match) | absent state: "No previous-season comparison available" (designed, brief §8) |
| No streaks | all runs < 2 | module omitted |
| Sparse stats | `stat_coverage_season_games < season_games_played` | coverage caption; null rates → "-" |
| Multiple competitions | several `seasons[]` rows per year | selector lists each; no cross-competition blending |
| Thin page | team has no `mart_team_profile` row | page not generated |

## 7. Interactions

- **Competition-season selector**: swaps all season-scoped modules in place (all
  rows are in the payload — no fetch). Crawlability: the default season renders
  in HTML; other seasons may be JS-swapped (sitemap carries one URL per team).
- Deserved-vs-actual ⓘ → metric glossary anchors.
- Links per (10).

## 8. SEO

- `schema.org/SportsTeam`: name, logo = crest, `memberOf` = selected competition.
- Title: `{name} — Stats, Form & Season Records | Matchday IQ` (localized).
- Meta description templated from record fields (rank, points, form).
- `BreadcrumbList`; canonical per locale + hreflang; OG card with crest.

## 9. Component census

Breadcrumb · profile header (team) · **competition-season selector ➕** ·
**big-number record block ➕** · form string · **single-bar ratio row ➕**
(deserved-vs-actual) · **gap callout ➕** · **aligned-comparison row ➕** (YoY) ·
**streak chip ➕** · stat row (label + value + direction) · group subhead ·
empty/absent states · internal-links footer.

## 10. Gaps

- [GAP-01](99_gaps_register.md) — founded/venue identity fields not exported (§5.2).
- [GAP-13](99_gaps_register.md) — five locked metric rows lack season variants (§5.8).
- [GAP-15](99_gaps_register.md) — no fixtures list in the team payload (§5.9).
