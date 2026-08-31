# 11 — Team → Squad

> **SUPERSEDED IN PART, 2026-07-24 (Squad tab built):** this spec was written identity-only.
> The CPO approved the FULL squad mock `f6348775` (AskUserQuestion 2026-07-23), so the built Squad
> tab now shows **per-player appearances · mins/app · goals · assists**, grouped by position, on top
> of the identity fields. The per-club season stats come from `mart_player_career` (appearances +
> goals + assists shipped #480; `minutes_per_appearance` added later), joined onto each roster member
> in the export. The "identity only" language below (§1, §5, §10) is HISTORY; the statted design is
> live. Sections updated in place with dated notes.
>
> A sub-screen of the team page (02). Field-bound against `mart_roster` (the roster identity) plus
> `mart_player_career` (the per-player season stats). The squad payload is **wired** — every key in §5
> is carried by the team export ([GAP-20](99_gaps_register.md), shipped #619; stats join GAP-22).

## 1. Purpose

Who plays for this club — the full squad, grouped by position, each player a
gateway to their profile. This is the **team → player navigation bridge** and a
programmatic-SEO surface (one indexable roster per team-season), not a
stop-scrolling "wow" screen. **UPDATED 2026-07-24:** the tab now shows, per player,
appearances / mins-per-appearance / goals / assists for the competition-season (joined from
`mart_player_career`), grouped by position, alongside the identity fields (name, position,
nationality, age, monogram avatar — no photo, standing CPO decision). Members with `>= 1`
appearance are listed, ordered by appearances desc, under an "N of M shown" caption; never-played
squad members are counted in M but not listed. (Was: "identity only today ... per-club stats are
not shown because mart_roster carries none" — that limit no longer holds.)

## 2. URL

```
/{locale}/teams/{kebab-name}-{team_id}/squad/
```

- Sub-path of the canonical team URL (`/teams/{slug}/`, `site_architecture.md` §3);
  `slug` = latest-season name + id (e.g. `bayern-munchen-157`), same rule as 02.
- Breadcrumb: Home → Teams → {team} → Squad.
- Competition-season is a **selector on the page** (not a URL segment) — the roster
  is per competition-season, so the selector mirrors the team profile's; one
  canonical squad URL per team.

## 3. Data sources

`data/teams/{team_id}.json` — the existing team payload. Addition (GAP-20, **shipped
#619**): a per-season `squad[]` array on each `seasons[]` row, one member object per
rostered player, sourced 1:1 from `mart_roster` and attached the same way
`next_fixture` / `recent_results` are (per `(league_code, season_api_year)`). The
export **selects/reshapes only** — no derivation (consumption-layer contract).

A season with no roster rows carries no `squad[]` — that season renders its designed
absent state; a team with no roster at all is not generated (see §6).

## 4. Layout

```
┌────────────────────────────────────────────┐
│ ▸Home › ▸Teams › ▸Bayern München › Squad   │  (1) breadcrumb
├────────────────────────────────────────────┤
│  [crest]  Bayern München — Squad           │  (2) identity header
│  [ Bundesliga 2025/26          ▾ ]         │  (3) competition-season selector
├────────────────────────────────────────────┤
│  GOALKEEPERS                               │  (4) position group
│  [photo] Manuel Neuer     Germany   38     │      player row → profile
│  [photo] Sven Ulreich     Germany   36     │
│  DEFENDERS                                 │
│  [photo] Dayot Upamecano  France    26     │
│  …                                         │
├──────────────— fold (~700px) —─────────────┤
│  MIDFIELDERS                               │
│  [photo] Joshua Kimmich   Germany   30     │
│  …                                         │
│  FORWARDS                                  │
│  [photo] Harry Kane       England   31     │
│  …                                         │
├────────────────────────────────────────────┤
│  ▸Team profile ▸Table ▸Top scorers         │  (5) internal links
└────────────────────────────────────────────┘
```

> NOTE (2026-07-24): the ASCII above is an illustrative sketch drawn for the identity-only draft
> (hence "[photo]" and no stats). The BUILT tab uses monogram avatars (no photos) and each row also
> carries the season stats per §5 — apps · mins/app · goals · assists on a second line.

**Above the fold**: identity + selector + the first position group(s). Groups
render in football order (Goalkeepers → Defenders → Midfielders → Forwards).

**Desktop (≥ ~900px)**: position groups as a multi-column grid (group headers span
the row); each player is a row (monogram, name, nationality, age, and the season stats:
appearances, mins per appearance, goals, assists).

## 5. Module bindings

Squad members come from the selected season's `squad[]`. All keys **wired** (GAP-20,
#619); each maps to a real `mart_roster` column.

### (2) Identity + (3) selector

| Element | JSON key | Notes |
|---|---|---|
| Name / crest | top-level `name`, `crest` | reused from the team payload; crest fallback = monogram |
| Selector options | `seasons[].league_code` + `season_api_year` (+ `competition_type`) | same rule/default as 02 §5; roster is per competition-season |

### (4) Position groups + player rows

| Element | JSON key | ← `mart_roster` column | Format |
|---|---|---|---|
| Group | `squad[].position` | `player_position` | grouped into Goalkeepers / Defenders / Midfielders / Forwards (§ build note); unknown → "Other" |
| Name | `squad[].name` | `player_name` | text; links to the player profile |
| Nationality | `squad[].nationality` | `player_nationality` | plain text (country **name**, e.g. "Germany") — same treatment as 03 §5; `player_nationality` is a country name, not an ISO/flag code, and no name→flag mapping exists (a flag treatment would need its own gap) |
| Age | derived from `squad[].birth_date` | `player_birth_date` | integer years at render time (the mart stores birth_date, not a stored age — per its header); null → omit |
| Photo | `squad[].photo` | `player_photo_url` | avatar; null → monogram |
| Link / slug | `squad[].player_id` (+ name) | `player_sk` | player-profile URL (slug rule = player page 03) |

**UPDATED 2026-07-24 — per-player season stats now bound** (joined from `mart_player_career` by
`player_sk` within (league_code, season) in the export):

| Field | Payload key | Source column | Notes |
|-------|-------------|---------------|-------|
| Appearances | `squad[].appearances` | `mart_player_career.appearances` | matches actually played (minutes > 0) |
| Mins per appearance | `squad[].minutes_per_appearance` | `mart_player_career.minutes_per_appearance` | catalogue metric (neutral); read, never divided in the frontend |
| Goals | `squad[].goals` | `mart_player_career.goals_player` | competition-season |
| Assists | `squad[].assists` | `mart_player_career.assists_player` | competition-season |

Position-group header labels are **new i18n keys** (copy work, not metric labels). Only
`minutes_per_appearance` is a catalogue metric; appearances / goals / assists are dimensions.
(Was: "No metric rows — mart_roster is identity-only.")

### (5) Internal links

Back to the team profile (02), the competition `/table/`, `/top-scorers/`; each
player row → the player profile (03).

## 6. States

| State | Trigger | Render |
|---|---|---|
| Normal | — | groups + rows above |
| No photo | `squad[].photo` null | monogram avatar |
| No age | `birth_date` null | age omitted (name/position/nationality remain) |
| Unknown position | `player_position` null/unmapped | player placed in an "Other" group at the end |
| Unresolved player | all identity fields null (a roster membership with no resolvable `dim_player` — the mart LEFT-joins `dim_player`, per its header) | member omitted from the render; this is guarded upstream by the `player_sk` → `dim_player` relationships DQ test (`mart_roster` is not silently dropped, so the case surfaces as a test failure, not a nameless row) |
| Empty season | selected season has no `squad[]` rows | designed absent state ("Squad not available for this season") |
| Thin page | team has no roster rows at all (no `squad[]` in any season) | Squad surface not generated; the team-page link is hidden |

## 7. Interactions

- **Competition-season selector**: swaps the roster in place (all seasons are in
  the payload — no fetch); default season = same rule as 02 (most recent, domestic
  league first).
- Player row → player profile.
- Static-site constraint: the default season renders in HTML for crawlability;
  other seasons may be JS-swapped (sitemap carries one squad URL per team).

## 8. SEO

- `schema.org/SportsTeam` with `athlete` members = the squad list (name + profile
  URL per player), `memberOf` = the selected competition.
- Title: `{team} Squad {season} | Matchday IQ` (localized).
- Meta description templated from the count + competition (e.g. "The {season}
  {competition} squad of {team} — {N} players.").
- `BreadcrumbList` (Home → Teams → {team} → Squad); canonical per locale + hreflang.

## 9. Component census

Breadcrumb · profile header (team) · competition-/season selector · **position-group
header ➕** · **squad player row ➕** (monogram · name · nationality · age · apps · mins/app ·
goals · assists, links to profile) · empty/absent state · internal-links footer.

## 10. Gaps

- [GAP-20](99_gaps_register.md) — **shipped #619**: `mart_roster` (built #503) is now
  carried by the team export as a per-season `squad[]` block (selects/reshapes only,
  byte-stable player_sk order, null-identity members omitted).
- ~~Stats/appearances on the squad are deferred to #480 ... out of scope for this identity-only
  screen.~~ **DONE 2026-07-24:** #480 shipped appearances/goals/assists and a later PR added
  `minutes_per_appearance`; the export now joins `mart_player_career` onto each squad member and the
  built Squad tab shows apps / mins-per-app / goals / assists (GAP-22). No longer deferred.
