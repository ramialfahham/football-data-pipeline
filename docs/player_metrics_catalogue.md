# Player Metrics Catalogue

Canonical specification for the player insights surface in Matchday IQ. Sits alongside `docs/player_stats_ui_data_modeling_concept.md` and supersedes that document's vague "Threat / Creation / Reliability" metric placeholders.

This document is the contract that the analytics engineer, data engineer, and UI engineer build against. No metric, sort, copy, or window reaches production without being defined here.

## Surface model

Player insights is rendered inside the existing fixture-detail card via the segment control proposed in `player_stats_ui_data_modeling_concept.md` (`Team insights | Player insights`).

The player insights view shows **9 leaderboards per side** (home + away), each presenting the **top 5 players on that team** for that leaderboard's metric, ranked over the player's form window.

Leaderboards are displayed as an ordered list with no section headings. The order is:

1. Scorer points
2. Shots on target
3. Successful dribbles
4. Key passes
5. Pass accuracy
6. Duels won
7. Tackles + Interceptions + Blocks
8. Save percentage
9. Cards

## The 9 leaderboards

Each leaderboard surfaces 1–3 **atomic metrics** computed from API-Football fields. The catalog comprises ~18 atomic metrics total.

| # | Leaderboard | Atomic metrics surfaced | Sort top 5 by | Section |
|---|---|---|---|---|
| 1 | Scorer points | `goals`, `assists` | `goals + assists` desc | Offense |
| 2 | Shots on target | `shots_on` | `shots_on` desc | Offense |
| 3 | Successful dribbles | `dribbles_success`, `dribbles_attempts`, `dribbles_success_pct` (derived) | `dribbles_success` desc | Offense |
| 4 | Key passes | `passes_key` | `passes_key` desc | Offense |
| 5 | Pass accuracy | `passes_total`, `pass_accuracy_pct` | `pass_accuracy_pct` desc | Possession |
| 6 | Duels won | `duels_total`, `duels_won_pct` | `duels_won_pct` desc | Defense |
| 7 | Tackles + Interceptions + Blocks | `tackles_total`, `tackles_interceptions`, `tackles_blocks` | `tackles + interceptions + blocks` desc | Defense |
| 8 | Save percentage | `save_pct` | `save_pct` desc | Goalkeeping |
| 9 | Cards | `cards_yellow`, `cards_red` | `cards_yellow + cards_red` desc | Discipline |

Sections are informational (for documentation/categorization purposes) and not rendered as UI groupings.

## Atomic metric formulas

All sums are computed across the player's form window (see "Form window dispatch" section below).

### 1. Scorer points

```
goals    = sum(goals_total)
assists  = sum(goals_assists)
```

Source fields: `goals_total`, `goals_assists` from `fct_fixture_player_stats`.

### 2. Shots on target

```
shots_on = sum(shots_on)
```

Source field: `shots_on`.

### 3. Successful dribbles

```
dribbles_success      = sum(dribbles_success)
dribbles_attempts     = sum(dribbles_attempts)
dribbles_success_pct  = dribbles_success / dribbles_attempts        (when denominator > 0)
```

Source fields: `dribbles_success`, `dribbles_attempts`.

### 4. Key passes

```
passes_key = sum(passes_key)
```

Source field: `passes_key`. API definition: a pass that leads directly to a shot (not necessarily a goal). Every assist is a key pass; not every key pass is an assist.

### 5. Pass accuracy

```
passes_accurate    = sum(passes_total * passes_accuracy_percent / 100)
passes_total       = sum(passes_total)
pass_accuracy_pct  = passes_accurate / passes_total                 (when denominator > 0)
```

Source fields: `passes_total`, `passes_accuracy_percent`. The `passes_accuracy_percent` field is stored as INTEGER by API-Football, so each per-fixture accurate-pass count inherits a small rounding error (~±1–2 passes); aggregate error over a 5-game window is well under 1 percentage point on the ratio.

### 6. Duels won

```
duels_won      = sum(duels_won)
duels_total    = sum(duels_total)
duels_won_pct  = duels_won / duels_total                            (when denominator > 0)
```

Source fields: `duels_total`, `duels_won`. API definition: a duel is any 1v1 physical contest — ground AND aerial pooled. Tackles and duels are tracked independently by the provider; they are not strict subsets.

### 7. Tackles + Interceptions + Blocks

```
tackles                = sum(tackles_total)
interceptions          = sum(tackles_interceptions)
blocks                 = sum(tackles_blocks)
defensive_actions_sum  = tackles + interceptions + blocks           (used for sort only)
```

Source fields: `tackles_total`, `tackles_interceptions`, `tackles_blocks`.

### 8. Save percentage

```
goals_saves     = sum(goals_saves)
goals_conceded  = sum(goals_conceded)
save_pct        = goals_saves / (goals_saves + goals_conceded)     (when denominator > 0)
```

Source fields: `goals_saves`, `goals_conceded`. Denominator = total shots on target faced. Only the percentage is displayed; underlying counts are stored in the mart for DQ tests and future use.

### 9. Cards

```
cards_yellow  = sum(cards_yellow)
cards_red     = sum(cards_red)
```

Source fields: `cards_yellow`, `cards_red`.

## Display patterns

> **Superseded for v2 (CPO, 2026-06-11):** row order, grouping and the ratio
> display strings are now governed by
> [`docs/wireframes/metrics_display.md`](wireframes/metrics_display.md) — rows
> resequenced into the shared block order, ratio rows standardized to
> `{num} of {den} · {pct}%`, GK row gains `saves of shots_on_target_faced`.
> The definitions, formulas, windows and the zero-denominator rule below remain
> canonical.

Each leaderboard row renders: `{rank}. {player_name}    {metric_display}`.

| # | Leaderboard | Per-row display | Example |
|---|---|---|---|
| 1 | Scorer points | `{goals} G · {assists} A` | `3 G · 2 A` |
| 2 | Shots on target | `{shots_on}` | `9` |
| 3 | Successful dribbles | `{success} of {attempts} · {pct}%` | `12 of 18 · 67%` |
| 4 | Key passes | `{count}` | `14` |
| 5 | Pass accuracy | `{pct}% · {total} passes` | `92% · 305 passes` |
| 6 | Duels won | `{pct}% · {total} duels` | `63% · 51 duels` |
| 7 | Tackles + Interceptions + Blocks | `{T} T · {I} I · {B} B` | `9 T · 5 I · 2 B` |
| 8 | Save percentage | `{pct}%` | `82%` |
| 9 | Cards | `{Y} Y · {R} R` | `3 Y · 0 R` |

## Zero-denominator rule

When a ratio's denominator is zero, the **counts are still shown** but the percentage renders as `—`. The user sees the activity volume (zero) clearly; the ratio is honestly declared undefined.

Examples:
- `Shots 0 · on target 0 · —`
- `Dribbles 0 · successful 0 · —`
- `Passes 0 · accurate 0 · —`
- `Duels 0 · won 0 · —`
- `Save % —` (no qualifying shots faced)

Never substitute a `0%` or omit the row entirely.

## Top-5 rule

Each leaderboard shows top 5 players from that side, ranked by the leaderboard's sort logic.

Tie-break: `minutes_played` desc. Beyond that, deterministic by `player_sk` asc to ensure stable ordering across builds.

If the side has fewer than 5 eligible players for a leaderboard, render the available rows. Do not pad with empty rows.

A player is **eligible for a leaderboard** when they have at least one finished match in their form window. A player with zero appearances in the window does not appear on any leaderboard for that team.

## Form-window dispatch

The window from which atoms are aggregated depends on the fixture context. The dispatch logic mirrors the existing team form-window dispatch where possible, but with one important divergence: for World Cup pre-tournament fixtures, player metrics draw from **domestic club data**, not qualifier data.

| Context | Source competition for player | Window | User-facing source copy |
|---|---|---|---|
| Domestic in-progress | The player's current domestic league (same as the fixture) | Last 5 matches in current season; previous-season fallback before MD1 | "Form window: last 5 {league} matches" |
| Domestic ended (season review) | Same | Full ended season | "Form window: full {league} season" |
| WC pre-tournament (before GS-MD1) | The player's domestic club's league | Last 5 matches in current or most-recent domestic season | "Form window: player's last 5 {domestic_league} matches before the tournament" |
| WC GS-MD1 onward through tournament end | World Cup | Cumulative WC matches played so far (no 5-cap) | "Form window: WC matches so far" |

### Why qualifier data is not used for player form

This is an explicit divergence from the team-level form rule, with three reasons:

1. **Roster turnover.** National squads change between qualification and tournament. Many qualifier participants don't appear at the WC, and many WC players didn't appear in qualifiers.
2. **Time gap.** Some qualifying cycles (e.g., CAF for WC 2026) span 2023–2025. A player's 2024 qualifier form is stale by June 2026.
3. **Opposition context.** Qualifier opposition is often weaker than tournament opposition; player stats inflate against minnows in ways that don't generalize.

Team-level form retains some signal from qualifiers (team identity is more stable than individual form). Player-level form does not.

### Form-source mapping for WC pre-tournament

The player's domestic league is resolved via the player's current team registration in API-Football's `/players/profiles` data (already ingested via the `/players` and squad endpoints). The mart joins on `player_sk -> current_team_sk -> league_code`.

When the player's domestic league is **not in the registry of ingested competitions**, the form source is unavailable for that player and the relevant atoms render as "Not provided" with the unavailability reason recorded on the row.

## Data source transparency

Every player insights surface must show the user where the data comes from. This is a hard UX requirement, not optional copy.

### Fixture-level context line

Below the `Player insights` segment header, render one of these copies (i18n-keyed):

- `"Form window: last 5 BL1 matches"` *(domestic in-progress)*
- `"Form window: full BL1 2024/25 season"` *(domestic ended)*
- `"Form window: player's last 5 domestic matches before the World Cup. Sources vary per player and are listed in each row."` *(WC pre-tournament — heterogeneous sources)*
- `"Form window: World Cup matches so far"` *(WC tournament from GS-MD1)*

### Per-row source indication (WC pre-tournament only)

Because each player on a national-team roster may draw from a different domestic league, WC pre-tournament rows include a small source tag visible on hover/tap:

```
1. Musiala    3 G · 2 A    (Bayern · BL1 · last 5)
2. Sané       1 G · 2 A    (Galatasaray · league not yet covered)
```

For other contexts, the fixture-level line is sufficient — all players share the same source.

### "Not provided" copy

When a player's domestic league is not ingested OR the player has zero appearances in the window:

```
{player_name} — Not provided ({reason})
```

`reason` enum:
- `"league_not_covered"` — Player's domestic league is not in the ingestion registry.
- `"no_appearances_in_window"` — Player did not feature in any qualifying match.
- `"data_unavailable"` — Stats coverage gap at the API level (API returned empty stats for the player's matches).

## Mart contract

A new mart `mart_matchday_player_insights` is added.

Grain: `(fixture_sk, team_sk, player_sk, leaderboard_id)`.

Required columns:

| Column | Type | Notes |
|---|---|---|
| `fixture_sk` | INT | Foreign key to `fct_fixture` |
| `fixture_api_id` | INT | For UI linking |
| `team_sk` | INT | Foreign key to `dim_team` |
| `team_api_id` | INT | For UI logo lookup |
| `player_sk` | INT | Foreign key to `dim_player` |
| `player_api_id` | INT | For UI |
| `player_name` | STRING | Denormalized for UI |
| `player_position_code` | STRING | Denormalized; informational, not used for filtering |
| `league_code` | STRING | The fixture's competition |
| `leaderboard_id` | STRING | Enum: `scorer_points`, `shots_on_target`, `dribbles`, `key_passes`, `pass_accuracy`, `duels`, `defensive_actions`, `save_pct`, `cards` |
| `rank_for_leaderboard` | INT | 1–5; null if not in top 5 (we still store all eligible rows; UI filters to top 5 at render) |
| `sort_score` | FLOAT | The value the rank is computed from (sum or pct depending on leaderboard) |
| `goals` | INT | Atom for leaderboard 1 |
| `assists` | INT | Atom for leaderboard 1 |
| `shots_on` | INT | Atom for leaderboard 2 |
| `dribbles_success` | INT | Atom for leaderboard 3 |
| `dribbles_attempts` | INT | Atom for leaderboard 3 |
| `dribbles_success_pct` | FLOAT | Atom for leaderboard 3; null if denominator zero |
| `passes_key` | INT | Atom for leaderboard 4 |
| `passes_total` | INT | Atom for leaderboard 5 |
| `passes_accurate` | INT | Derived atom for leaderboard 5 |
| `pass_accuracy_pct` | FLOAT | Atom for leaderboard 5; null if denominator zero |
| `duels_total` | INT | Atom for leaderboard 6 |
| `duels_won` | INT | Atom for leaderboard 6 |
| `duels_won_pct` | FLOAT | Atom for leaderboard 6; null if denominator zero |
| `tackles` | INT | Atom for leaderboard 7 |
| `interceptions` | INT | Atom for leaderboard 7 |
| `blocks` | INT | Atom for leaderboard 7 |
| `goals_saves` | INT | Atom for leaderboard 8 |
| `goals_conceded` | INT | Atom for leaderboard 8 |
| `save_pct` | FLOAT | Atom for leaderboard 8; null if denominator zero |
| `cards_yellow` | INT | Atom for leaderboard 9 |
| `cards_red` | INT | Atom for leaderboard 9 |
| `minutes_played_window` | INT | Tie-break key |
| `matches_in_window` | INT | Sample size for transparency |
| `form_source_league_code` | STRING | The competition the window was drawn from (may differ from `league_code` for WC pre-tournament) |
| `form_window_kind` | STRING | Enum: `domestic_last_5`, `domestic_full_season`, `domestic_prev_season_fallback`, `wc_pre_via_domestic`, `wc_tournament_cumulative` |
| `form_source_unavailable_reason` | STRING | Enum or null; `league_not_covered`, `no_appearances_in_window`, `data_unavailable` |

## Data quality tests

Hard gates that must pass before any UI surface ships:

### Grain
- `unique` on `(fixture_sk, team_sk, player_sk, leaderboard_id)`.

### Relationships
- `player_sk` → `dim_player.player_sk` not_null + relationship
- `team_sk` → `dim_team.team_sk` not_null + relationship
- `fixture_sk` → `fct_fixture.fixture_sk` not_null + relationship

### Range tests (atomic)
- All count atoms (`goals`, `assists`, `shots_on`, `dribbles_success`, etc.): `>= 0`.
- All percent atoms (`*_pct`): in `[0, 1]` OR null.

### Formula consistency
- `passes_accurate <= passes_total` (derived numerator never exceeds denominator)
- `dribbles_success <= dribbles_attempts`
- `duels_won <= duels_total`
- `goals_saves + goals_conceded > 0 OR save_pct IS NULL` (no fabricated denominator)

### Sort consistency
- For each (fixture_sk, team_sk, leaderboard_id), the player with `rank_for_leaderboard = 1` has the highest `sort_score`; rank 2 is second-highest, etc.

### Source transparency
- `form_source_unavailable_reason IS NOT NULL` implies all atomic metrics on that row are NULL.
- `form_window_kind` is never null.

## i18n keys

All user-facing labels and copy are i18n-keyed under `playerMetrics.*` in `site/i18n/{en,de}.json`. Finnish (`fi.json`) follows once VL onboarding's translation pattern is extended.

| Key | EN | DE |
|---|---|---|
| `playerMetrics.section.title` | Player insights | Spielereinblicke |
| `playerMetrics.scorerPoints.label` | Scorer points | Scorerpunkte |
| `playerMetrics.scorerPoints.display` | `{{goals}} G · {{assists}} A` | `{{goals}} T · {{assists}} V` |
| `playerMetrics.shotsOnTarget.label` | Shots on target | Schüsse aufs Tor |
| `playerMetrics.dribbles.label` | Successful dribbles | Erfolgreiche Dribblings |
| `playerMetrics.dribbles.display` | `{{success}} of {{attempts}} · {{pct}}%` | `{{success}} von {{attempts}} · {{pct}}%` |
| `playerMetrics.keyPasses.label` | Key passes | Schlüsselpässe |
| `playerMetrics.passAccuracy.label` | Pass accuracy | Passgenauigkeit |
| `playerMetrics.passAccuracy.display` | `{{pct}}% · {{total}} passes` | `{{pct}}% · {{total}} Pässe` |
| `playerMetrics.duels.label` | Duels won | Gewonnene Zweikämpfe |
| `playerMetrics.duels.display` | `{{pct}}% · {{total}} duels` | `{{pct}}% · {{total}} Zweikämpfe` |
| `playerMetrics.defensiveActions.label` | Tackles + Interceptions + Blocks | Tacklings + Abfangaktionen + Blocks |
| `playerMetrics.defensiveActions.display` | `{{T}} T · {{I}} I · {{B}} B` | `{{T}} T · {{I}} A · {{B}} B` |
| `playerMetrics.savePct.label` | Save percentage | Gehaltene Torschüsse |
| `playerMetrics.cards.label` | Cards | Karten |
| `playerMetrics.cards.display` | `{{Y}} Y · {{R}} R` | `{{Y}} G · {{R}} R` |
| `playerMetrics.zeroDenominator.placeholder` | — | — |
| `playerMetrics.formWindow.domesticInProgress` | Form window: last 5 {{league}} matches | Formfenster: letzte 5 {{league}}-Spiele |
| `playerMetrics.formWindow.domesticEnded` | Form window: full {{league}} {{season}} season | Formfenster: komplette {{league}} {{season}}-Saison |
| `playerMetrics.formWindow.wcPreTournament` | Form window: player's last 5 domestic matches before the World Cup. Sources vary per player. | Formfenster: die letzten 5 Ligaspiele jedes Spielers vor der WM. Quellen können sich je Spieler unterscheiden. |
| `playerMetrics.formWindow.wcTournament` | Form window: World Cup matches so far | Formfenster: bisherige WM-Spiele |
| `playerMetrics.unavailable.leagueNotCovered` | Player's domestic league not yet covered | Liga des Spielers wird noch nicht abgebildet |
| `playerMetrics.unavailable.noAppearancesInWindow` | No appearances in form window | Keine Einsätze im Formfenster |
| `playerMetrics.unavailable.dataUnavailable` | Statistics unavailable from data provider | Statistiken vom Datenanbieter nicht verfügbar |

## Known limitations (v1)

Documented openly here and surfaced in user-facing copy.

1. **Domestic coverage.** Currently ingested leagues: BL1, BL2, PL, PD, SA, L1, VL. National-team players whose club plays in Eredivisie, Liga Portugal, Süper Lig, Liga MX, MLS, Saudi Pro League, J-League, K-League, Belgian Pro League etc. have no domestic data → "Not provided".
2. **No event-level data.** API-Football aggregates passes/shots/duels per fixture. We do not have pass-by-pass success/failure events, shot locations, or pressure data. Therefore: no xG, no pass-progression metrics, no positional context for actions.
3. **API stats coverage gaps.** Some qualifier confederations (notably CAF and OFC) have incomplete fixture-statistics coverage at the API level. This affects WC tournament-phase aggregation when a player has stats-incomplete tournament appearances.
4. **Club form as a proxy for international form.** A player's domestic club form correlates with but does not equal their international form. Different teammates, system, role, opposition. Surfaced as a proxy with explicit source labeling; not as ground truth.
5. **No leaderboard for goalkeepers beyond Save %.** Save percentage is the only GK-specific leaderboard. Other GK metrics (distribution accuracy, claims, etc.) require fields API-Football does not expose distinctly.

## Iteration roadmap (post-v1)

1. **More leagues onboarded.** Eredivisie + Liga Portugal first (most non-Big-5 European squad players); then Liga MX + MLS for CONCACAF; then Asian top leagues.
2. **Analytics corner / deeper-stats surface.** Holding place for ratio metrics that don't make the 9-leaderboard cut (e.g., key passes per 100 passes, dribble take-on rate by zone if zone data ever lands).
3. **Position-aware filtering or weighting.** Currently all players are eligible for all leaderboards. v1.x could filter by position group for goalkeeping-style leaderboards. Out of v1 scope.
4. **Cross-competition blending for big-game players.** Currently a single window draws from a single competition. If a player appears in BL1 + UCL, only BL1 is used (because UCL is not ingested). When UCL is onboarded, a separate "club competitive form" view may blend leagues — explicitly opt-in.
5. **Player share-surface and tracking.** Per `player_stats_ui_data_modeling_concept.md`, growth surface for player cards is a phase 2 concern.

## Implementation chain

This catalog unblocks the PR sequence already laid out in `player_stats_ui_data_modeling_concept.md`:

1. ~~Metric spec ticket~~ → this document
2. Core fixture-player unification (`2_base` + `3_core`)
3. Intermediate player insight features (`4_intermediate` + tests)
4. Player insights mart + export wiring (`5_marts` + exporter)
5. UI integration in fixture detail (segment control + leaderboards + i18n)
6. Cross-device QA + regression

Each is a separate PR. The catalog stays the source of truth across all of them.

## Easy access

Repo path: `docs/player_metrics_catalogue.md`.
After merge: `https://github.com/ramialfahham/football-data-pipeline/blob/main/docs/player_metrics_catalogue.md`.
