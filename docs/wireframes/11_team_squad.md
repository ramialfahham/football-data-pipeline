# 11 — Team → Squad

> A sub-screen of the team page (02). Field-bound against `mart_roster`
> (identity-only squad list, #503). The squad payload is **not yet exported** —
> every key in §5 is a **proposed** shape pending [GAP-20](99_gaps_register.md)
> (the export-wiring PR); this spec is written ahead of that PR, the same way 02's
> fixtures block preceded its data PR (GAP-15 → #607).

## 1. Purpose

Who plays for this club — the full squad, grouped by position, each player a
gateway to their profile. This is the **team → player navigation bridge** and a
programmatic-SEO surface (one indexable roster per team-season), not a
stop-scrolling "wow" screen. **Honest limit:** identity only today (name,
position, nationality, age, photo) — appearances and per-club stats are not shown
because `mart_roster` carries none; they arrive with the per-club player-season
model (#480, Phase C).

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

`data/teams/{team_id}.json` — the existing team payload. **Proposed** addition
(GAP-20): a per-season `squad[]` array on each `seasons[]` row, one member object
per rostered player, sourced 1:1 from `mart_roster` and attached the same way
`next_fixture` / `recent_results` are (per `(league_code, season_api_year)`). The
export **selects/reshapes only** — no derivation (consumption-layer contract).

Until GAP-20 lands the team payload carries no `squad[]`; the Squad surface is not
generated (see §6, thin page).

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

**Above the fold**: identity + selector + the first position group(s). Groups
render in football order (Goalkeepers → Defenders → Midfielders → Forwards).

**Desktop (≥ ~900px)**: position groups as a multi-column grid (group headers span
the row); each player is a compact card (photo, name, nationality, age).

## 5. Module bindings

Squad members come from the selected season's `squad[]`. All keys **proposed**
(GAP-20); each maps to a real `mart_roster` column.

### (2) Identity + (3) selector

| Element | JSON key | Notes |
|---|---|---|
| Name / crest | top-level `name`, `crest` | reused from the team payload; crest fallback = monogram |
| Selector options | `seasons[].league_code` + `season_api_year` (+ `competition_type`) | same rule/default as 02 §5; roster is per competition-season |

### (4) Position groups + player rows

| Element | JSON key (proposed) | ← `mart_roster` column | Format |
|---|---|---|---|
| Group | `squad[].position` | `player_position` | grouped into Goalkeepers / Defenders / Midfielders / Forwards (§ build note); unknown → "Other" |
| Name | `squad[].name` | `player_name` | text; links to the player profile |
| Nationality | `squad[].nationality` | `player_nationality` | plain text (country **name**, e.g. "Germany") — same treatment as 03 §5; `player_nationality` is a country name, not an ISO/flag code, and no name→flag mapping exists (a flag treatment would need its own gap) |
| Age | derived from `squad[].birth_date` | `player_birth_date` | integer years at render time (the mart stores birth_date, not a stored age — per its header); null → omit |
| Photo | `squad[].photo` | `player_photo_url` | avatar; null → monogram |
| Link / slug | `squad[].player_id` (+ name) | `player_sk` | player-profile URL (slug rule = player page 03) |

No metric rows — `mart_roster` is identity-only. Position-group header labels are
**new i18n keys** (copy work, not metric labels; catalogue untouched).

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
| Not yet wired | GAP-20 open (today) | as "thin page" — no `squad[]` in the payload, surface not generated |

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
header ➕** · **squad player row ➕** (photo · name · nationality · age, links to
profile) · empty/absent state · internal-links footer.

## 10. Gaps

- [GAP-20](99_gaps_register.md) — `mart_roster` is built (#503) but not carried by
  the team export; the Squad surface has no payload. Disposition: add a per-season
  `squad[]` block to the team payload (export selects/reshapes only) in a follow-up PR.
- Stats/appearances on the squad are deferred to #480 (per-club player-season model,
  Phase C) — out of scope for this identity-only screen.
