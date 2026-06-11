# Metric display contract — groups, tiers, order (#391)

> The CPO-ruled display contract for metric lists everywhere they render (fixture
> comparison, team profile, player profile, leaderboards). The metric catalogue
> stays the single source of definitions; this document records the **display**
> rulings (grouping, importance tier, order) until they are codified as catalogue
> columns (GAP-09). **Team table: LOCKED (CPO, 2026-06-11). Player rows: LOCKED
> (CPO, 2026-06-11).**

## Tier semantics (ruled)

1. **Tier never orders.** Display order is fixed by this document (block sequence +
   row position within block) and is identical everywhere the list renders.
2. **Tier = visibility under constraint.** Surfaces that cannot show the full list
   (home fixture hooks, teaser cards) show only tier-1 rows, in the same order.
   Full pages show all rows.
3. Optional in-place progressive disclosure: tier-3 rows may collapse behind a
   "show all stats" expander, reappearing exactly where they sit in the order.
   Design call (#366), not a data rule.

Tier-1 selection principle: outcomes + the highest-signal quality metrics, and only
rows with near-universal data coverage (scoreline/team-stat derived — never
player-stat derived, which is the sparsest layer and would render "-" on compact
surfaces).

## Composite-row patterns (ruled)

- **No naked percentage** — every % must have its volume visible nearby. Two
  mechanisms by surface: team comparisons use an **adjacent count row** in the
  same block (Ø Duels before % Duels won); player bundles use the **inline full
  triple** `{num} of {den} · {pct}%`.
- **Context pairs travel together**: a count that contextualizes a percentage
  (Ø Duels before % Duels won) shares the percentage's tier — never separated.
- **Aggregates with breakdown**: defensive actions render as one number with the
  atomic breakdown as sub-display — `26.4` + `15 T · 9 I · 3 B` (the pattern
  established in `docs/player_metrics_catalogue.md`).
- **Window form display**: W1 shows the last-5 W/D/L pills (from `form_window[]`,
  recency order). W2 shows aggregate counts `10W · 3D · 1L` — pills would
  misrepresent a 14+-game window (needs GAP-10).

## Team metrics — LOCKED (CPO, 2026-06-11)

Display order top to bottom. MVP rows keep their relative order; new blocks slot
into the spine. Block order: Goals → Shooting → Duels → Defending → Passing →
Set pieces → Goalkeeping.

| # | Display label | metric_id | Group | Tier | Status |
|---|---|---|---|---|---|
| 1 | Ø Goals | `goals_per_match` | Goals | 1 | live |
| 2 | Ø Goals against | `goals_against_per_match` | Goals | 1 | live |
| 3 | Clean sheets (x/y) | `clean_sheets` | Goals | 2 | **new** (GAP-11) |
| 4 | Ø Shots | `shots_per_match` | Shooting | 2 | live |
| 5 | % Shots from box | `danger_zone_ratio` | Shooting | 2 | live |
| 6 | Ø Shots on target | `shots_on_target_per_match` | Shooting | 1 | **new** (GAP-11) |
| 7 | % Goals per shot on target | `finishing_efficiency` | Shooting | 1 | live — **relabeled** (was "% Conversion rate", GAP-11) |
| 8 | Ø Duels | `duels_per_match` | Duels | 2 | **new** (GAP-11) |
| 9 | % Duels won | `duels_won_pct` | Duels | 2 | live |
| 10 | Ø Defensive actions (`T · I · B`) | `defensive_actions_per_match` | Defending | 2 | **new aggregate** (GAP-11) |
| 11 | Ø Passes | `passes_per_match` | Passing | 3 | live |
| 12 | % Pass accuracy | `pass_accuracy` | Passing | 2 | live |
| 13 | Ø Key passes | `key_passes_per_match` | Passing | 2 | live |
| 14 | Ø Corners | `corner_kicks_per_match` | Set pieces | 3 | live |
| 15 | Ø Corners against | `corners_conceded_per_match` | Set pieces | 3 | live |
| 16 | % Save percentage | `save_ratio` | Goalkeeping | 2 | live |

Tier shape: 4 × tier 1 (rows 1, 2, 6, 7) · 9 × tier 2 · 3 × tier 3.

**Defined but not displayed** (stay in catalogue/marts, render nowhere in the
comparison): `shot_accuracy` (% shots on target — superseded by the Ø-shots vs
Ø-on-target juxtaposition), `tackles_per_match` / `interceptions_per_match` /
`blocks_per_match` (sub-display of row 10 only), `dribbles_success_pct`
(dropped team-side; stays a player metric), `points_won` + `league_rank`
(window header / standing chip, not metric rows).

### The shooting funnel (rationale, ruled with fix "a")

Volume (Ø shots) → location quality (% from box) → on-target volume (Ø shots on
target) → finishing (% goals per shot on target). The finishing metric keeps its
formula (goals ÷ shots on goal, coverage-aligned) — the old label "% Conversion
rate" was the misnomer and is replaced. Glossary carries the caveat that finishing
can exceed 100% (penalties/own goals counted as goals but not always as shots);
the true value is always shown, never capped.

## Player rows — LOCKED (CPO, 2026-06-11)

The player display unit is the **bundled row** established in
`docs/player_metrics_catalogue.md` (1–3 related atomics per row with a defined
display string) — NOT one metric per row, and **no tiers**. Tiers are a team-only
concept: player importance is position-dependent and the provider's metric scope
cannot ground a per-position importance claim. Constrained surfaces use
**per-surface rules** instead (e.g. the fixture top-players strip ranks
goals → assists → key passes, GK variant saves + save %).

Changes vs `player_metrics_catalogue.md` (which stays canonical for definitions,
formulas, windows): (1) rows resequenced into the shared block order; (2) every
bundle carries the `metric_group` it inherits from its atomics — a bundle never
mixes groups; (3) ratio displays standardized to the full triple
`{num} of {den} · {pct}%`; (4) the GK row gains the triple (two new atomics).

| # | Row | Display string | Atomics | Group |
|---|---|---|---|---|
| 1 | Scorer points | `{goals} G · {assists} A` | goals, assists | Goals |
| 2 | Shots on target | `{shots_on}` | shots_on_target | Shooting |
| 3 | Duels won | `{won} of {total} · {pct}%` | duels_won, duels_total, duels_won_pct | Duels |
| 4 | Successful dribbles | `{success} of {attempts} · {pct}%` | dribbles_success, dribbles_attempts, dribbles_success_pct | Duels |
| 5 | Tackles + Interceptions + Blocks | `{T} T · {I} I · {B} B` | tackles_total, tackles_interceptions, tackles_blocks | Defending |
| 6 | Pass accuracy | `{accurate} of {total} · {pct}%` | passes_accurate, passes_total, pass_accuracy_pct | Passing |
| 7 | Key passes | `{count}` | passes_key | Passing |
| 8 | Cards | `{Y} Y · {R} R` | cards_yellow, cards_red | Discipline |
| 9 | Save percentage | `{saves} of {faced} · {pct}%` | **saves (new)**, **shots_on_target_faced (new)**, save_pct | Goalkeeping |

- Row 9 renders only for `position_code = 'G'`; whether a GK profile pulls the
  Goalkeeping block forward is a design call (#366).
- The **zero-denominator rule** is unchanged and now self-explanatory:
  `0 of 0 · —`.
- Atomics not in a bundle (offsides, dribbled past, penalties won/committed,
  goals conceded) stay defined in the catalogue but unrendered — same status as
  team `shot_accuracy`.

## Data work implied (see 99_gaps_register.md)

- **GAP-09** — catalogue columns: `metric_group` (all atomics, team + player),
  `importance_tier` (**team-only** — null for player entries),
  `group_display_order` (this document is the source for the values).
- **GAP-10** — `wins`/`draws`/`losses` columns in `mart_season_to_date__team`
  (the W2 counts display).
- **GAP-11** — new team metrics (`clean_sheets` in both window marts,
  `duels_per_match`, `defensive_actions_per_match`, `shots_on_target_per_match`),
  the finishing relabel, catalogue description tightenings (coverage denominators,
  blocked-shots note, >100% finishing caveat).
- **GAP-12** — player additions: `saves` + `shots_on_target_faced` atomics (data
  exists as `goals_saves`/`goals_conceded`), display strings standardized to the
  full triple (duels, pass accuracy, saves), `player_metrics_catalogue.md`
  display table superseded by this document.

## Rulings log

| Date | Ruling |
|---|---|
| 2026-06-11 | Groups = MVP blocks; MVP row order untouched; new metrics slot into blocks. |
| 2026-06-11 | Duels + Defending blocks placed before Passing. |
| 2026-06-11 | Clean sheets added (new metric); team dribbles dropped; T·I·B aggregated. |
| 2026-06-11 | Ø Duels added as context row before % Duels won; context pairs share a tier. |
| 2026-06-11 | Shooting block reshaped: Ø shots, % from box, Ø shots on target (new), finishing; `shot_accuracy` unrendered; finishing relabeled (fix "a"). |
| 2026-06-11 | Tier 1 = goals, goals against, shots on target, finishing. Duels stay tier 2 (coverage + discrimination + compact-surface budget). |
| 2026-06-11 | W1 = form pills; W2 = W/D/L counts (GAP-10). |
| 2026-06-11 | Player display unit = the bundled rows from `player_metrics_catalogue.md`; resequenced into shared block order; groups inherited from atomics (no mixed bundles). |
| 2026-06-11 | **No tiers for players** — position-dependent importance can't be grounded in the provider's metric scope; compact surfaces use per-surface rules. |
| 2026-06-11 | No naked percentage: player ratio rows standardized to `{num} of {den} · {pct}%`; GK row gains the triple (`saves`, `shots_on_target_faced` atomics). Team comparisons keep single % values — adjacent count rows provide the volume. |
