# 03 — Player profile ⭐ (#391)

> Field-bound against `shape_player_payload` / `mart_player_profile` /
> `mart_player_match_log` (verified 2026-06-11). Stat rows follow the LOCKED
> player bundles in [`metrics_display.md`](metrics_display.md) — 9 bundled rows,
> no tiers, full-triple ratios, zero-denominator rule.

## 1. Purpose

A player's season in one screen: who they are, what they produce, and the match
log behind the numbers. The **stop-scrolling moment** is the **match log** — the
per-match line (score, result, minutes, goals) that turns a season
aggregate into a story you can scroll. Aggregates are honest counts only — no
per-90, no composite ratings (locked).

## 2. URL

```
/{locale}/players/{kebab-name}-{player_id}/
```

- `slug` from the payload (e.g. `jamal-musiala-1090`).
- Breadcrumb: Home → Players → {player}.
- One canonical URL per player; season is a selector.

## 3. Data sources

`data/players/{player_id}.json` —
top level: `player_id, slug, name, nationality, photo, position`;
`seasons[]` (per league-season, year desc): appearance facts + the bundle
atomics; `match_log[]` (all matches with a stat line, latest first).

## 4. Layout

```
┌────────────────────────────────────────────┐
│ ▸Home › ▸Players › Jamal Musiala           │  (1) breadcrumb
├────────────────────────────────────────────┤
│  [photo]  Jamal Musiala          [MF]      │  (2) identity header
│           Germany                          │      (birth date: GAP-14,
│           ▸FC Bayern München               │       team: GAP-16)
│  [ Bundesliga 2025/26          ▾ ]         │  (3) season selector
├────────────────────────────────────────────┤
│  14 apps (12 starts) · 1.102 min           │  (4) appearance facts
├────────────────────────────────────────────┤
│  SEASON STATS                              │  (5) the 9 bundled rows
│  Scorer points        9 G · 6 A            │
│  Shots on target      21                   │
├──────────────— fold (~700px) —─────────────┤
│  Duels won            96 of 178 · 54%      │
│  Successful dribbles  38 of 61 · 62%       │
│  Tackles+Int.+Blocks  18 T · 11 I · 2 B    │
│  Pass accuracy        581 of 654 · 89%     │
│  Key passes           31                   │
│  Cards                2 Y · 0 R            │
│  (GK only) Saves      41 of 50 · 82%       │
├────────────────────────────────────────────┤
│  MATCH LOG                                 │  (6) latest first
│  6 Dec  BL1  Gladbach [crest] H            │
│  ▸ W 3-1 · 90' · 1 G · 1 A                 │
│    …all matches with a stat line…          │
├────────────────────────────────────────────┤
│  ▸Team profile ▸Bundesliga ▸Top scorers    │  (7) internal links
└────────────────────────────────────────────┘
```

**Above the fold**: identity + selector + appearance facts + the first bundles
(scorer points visible). **Desktop**: two columns — left: identity + facts +
season stats; right: match log (it carries the scroll).

## 5. Module bindings

### (2) Identity + (3) selector

| Element | JSON key | Notes |
|---|---|---|
| Name / photo / nationality | top-level `name`, `photo`, `nationality` | photo fallback = initials monogram |
| Position badge | `position` (`G/D/M/F`) | i18n badge labels (GK/DF/MF/FW) |
| Birth date / age | — | **GAP-14, approved** — `player_birth_date` is in the mart; export will surface `birth_date` top-level |
| Current team + history | — | **GAP-16, approved** — `current_team` from the latest match-log row + per-season team history; ▸ team profile link |
| Selector | `seasons[].league_code` + `season_api_year` | default = most recent |

### (4) Appearance facts (selected season row)

`appearances`, `starts`, `substitute_appearances`, `minutes` — facts, not
catalogue metrics; rendered as a one-line summary.

### (5) Season stats — the 9 locked bundles

| Bundle (contract) | JSON keys (selected season row) |
|---|---|
| Scorer points | `goals`, `assists` |
| Shots on target | `shots_on_target` |
| Duels won | `duels_won`, `duels_total`, `duels_won_pct` |
| Successful dribbles | `dribbles_success`, `dribbles_attempts`, `dribbles_success_pct` |
| Tackles + Interceptions + Blocks | `tackles_total`, `tackles_interceptions`, `tackles_blocks` |
| Pass accuracy | `passes_accurate`, `passes_total`, `pass_accuracy_pct` |
| Key passes | `passes_key` |
| Cards | `cards_yellow`, `cards_red` |
| Save percentage | `save_pct` + **GAP-12** atomics (`saves`, `shots_on_target_faced`) — until they ship the row renders `{pct}%` only |

Rendering rules per contract: group subheads optional (design call), order fixed,
zero-denominator → `0 of 0 · —`, GK row only for `position = 'G'` (pull-up of the
GK block on keeper profiles = design call #366). Unbundled atomics
(`dribbles_past`, `offsides`, `penalty_won`, `penalty_committed`) stay unrendered.

### (6) Match log — `match_log[]`, latest first

| Element | JSON key | Notes |
|---|---|---|
| Date | `kickoff_datetime` | locale short date |
| Competition | `league_code` | badge |
| Opponent | `opponent_name`, `opponent_logo_url` | ▸ opponent profile (`opponent_team_sk`) |
| Home/away | `is_home` | H/A badge |
| Score + result | `goals_for`, `goals_against`, `result` | team perspective; W/D/L chip |
| Minutes | `minutes_played` | `90'`; sub appearance flagged via `is_substitute` |
| Goals / assists | `goals_total`, `goals_assists` | shown when > 0 |
| Cards | `cards_yellow`, `cards_red` | icons when > 0 |
| GK line | `goals_saves`, `goals_conceded` | replaces G/A for keepers |
| Round (secondary) | `round_name` | GAP-08 applies |

Row click-through → `matchstats/{fixture_sk}` **only when that file exists**
(matchstats covers form-window-referenced fixtures; the build links rows against
the export manifest, others render non-clickable). Expanded row (design option)
may show the full per-match line: `shots_total`, `shots_on`, `passes_total`,
`passes_key`, `passes_accuracy_percent`, `tackles_total`,
`tackles_interceptions`, `duels_total`, `duels_won`, `dribbles_attempts`,
`dribbles_success`, `fouls_drawn`, `fouls_committed`, `is_starter`.

## 6. States

| State | Trigger | Render |
|---|---|---|
| Normal | — | everything above |
| GK profile | `position = 'G'` | Save-percentage bundle renders; GK match-log line |
| Zero denominator | e.g. `duels_total = 0` | `0 of 0 · —` (counts shown, ratio undefined) |
| No stat line for a match | match absent from `match_log[]` | nothing fabricated — the log only contains matches with player stats (a COMMON state, brief §2: style it, don't hide it) |
| Multi-competition season | several `seasons[]` rows per year | selector lists each; no blending |
| Thin page | no `mart_player_profile` row | page not generated |

## 7. Interactions

- **Season selector**: swaps (4)+(5) and filters (6) in place (all data in the
  payload). Default season server-rendered.
- Match-log row → matchstats page when available; opponent → team profile.
- No charts required at v1.

## 8. SEO

- `schema.org/Person` (athlete): name, image = photo, nationality;
  `memberOf` once GAP-16 lands.
- Title: `{name} — Stats & Match Log | Matchday IQ` (localized).
- Meta description templated from season facts (apps, goals, assists).
- `BreadcrumbList`; canonical + hreflang; OG card with photo.

## 9. Component census

Breadcrumb · profile header (player) · position badge ➕ · season selector
(shared with 02) · **fact summary line ➕** · bundled stat row (the player-row
component, contract-defined) · group subhead · **match-log row ➕** · result chip ·
empty/absent states · internal-links footer.

## 10. Gaps

- [GAP-08](99_gaps_register.md) — `round_name` localization (match log secondary line).
- [GAP-12](99_gaps_register.md) — GK triple atomics (save bundle, §5.5).
- [GAP-14](99_gaps_register.md) — birth date not in the payload (§5.2).
- [GAP-16](99_gaps_register.md) — no current-team affiliation in the profile (§5.2).
