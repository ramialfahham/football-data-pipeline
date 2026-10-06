# Metrics Context & Window Model

For an upcoming fixture, this document states which past matches form each team and player figure.
It also states how each figure names its window.

- What a metric means, and its formula: the `metric_catalogue.csv` seed.
- Where every other metric rule lives: `docs/metric_layer.md`.
- How a figure is shown: `docs/wireframes/metrics_display.md`.

Nothing here hardcodes a competition. Three declared properties drive the rules: the **competition
type**, the **phase** and the **club or national** split. `league_code` is the competition
discriminator on every model.

---

## 1. Two kinds of figure

Every performance figure is one of two kinds. Each kind has its own window. An entity is a team or
a player.

| Kind | Answers | Scope |
|------|---------|-------|
| **Live form** | "How are they playing *at the moment*?" | **Cross-competition**: the entity's last 5 matches across all its competitions |
| **Season record** | "What have they done *in this competition*?" | **Within that one competition**: cumulative season to date, the basis of year-over-year |

Only live form crosses competitions. The season record always stays within one competition. The
models name live form "momentum".

---

## 2. Club or national: a property of the competition type

The `competition_types` seed declares, once per competition type, whether clubs or national teams
play it. It holds one row per type. `scripts/check_competition_type_seed.py` fails CI when a
`competition_type` in `docs/competition_registry.yml` has no row in the seed.

- No competition type is both club and national.
- `qualifying` is national-team qualifying, such as World Cup or European Championship qualifiers.
  Club qualifying rounds take the club type `club_qualifying`.
- Models resolve club or national by looking up the type. SQL never hardcodes it.

A club's form holds club matches only. A national team's form holds national-team matches only.

---

## 3. Temporal phases

There are three phases. Fixture counts in the current edition detect each phase. No rule is per
league, and no rule reads a table of dates. An edition is one season of one competition: one
`league_code` and one `season_api_year`.

The counts are the **team's own fixtures** in that edition, not the competition's. For a league the
two are the same, because every team plays to the final matchday. For a knockout they differ. A
club knocked out in the first round has at least 1 finished fixture and 0 upcoming. That club is in
"After it's finished", and the cup continues for other teams.

| Phase | Detection | Meaning |
|-------|-----------|---------|
| **Before it starts** | 0 finished, ≥1 upcoming | the first fixture of the edition; no live form yet |
| **While it's running** | ≥1 finished, ≥1 upcoming | the edition is under way |
| **After it's finished** | ≥1 finished, 0 upcoming | the edition is complete |

- "Before it starts" is literal: exactly zero finished matches.
- From the first finished match, the phase is "While it's running", and the window shows *up to*
  the last 5.
- A window never mixes seasons to pad an early-season sample.
- The off-season needs no rule. A competition stays "After it's finished" until the next edition's
  fixtures appear. Those fixtures move it to "Before it starts".
- A play-off round is a stage within its parent competition (section 6). A league is therefore not
  finished until its play-offs are also played.

---

## 4. The window matrix (per competition type)

The rows are the types of `dbt_project/seeds/competition_types.csv`.

**Window meanings.** One doc block describes each window, on the column that names it. The form
window's `window_type` carries the `window_type__form` doc block. The season record's `window_type`
carries the `window_type__season_record` doc block. BigQuery shows both.

**Full completed.** A full completed season, edition, campaign or tournament holds all of that
team's matches in that edition. It does not depend on how far the team went.

**Type status.** This column is not the registry's `status` field.

| Type status | Meaning |
|---|---|
| `active` | The registry holds at least one competition of this type. |
| `taxonomy` | The registry holds no competition of this type. |
| `not ingesting` | A friendly type. The registry holds no competition of it, and form windows defer it. |

### Club competitions

- `club_world_cup` takes the `continental_cup` windows.
- `intercontinental_super_cup` takes the `continental_super_cup` windows.
- A club competition has an "After it's finished" figure only when every entrant plays a group or
  league phase. Only then are there enough matches to aggregate.
- `domestic_league`, `continental_cup` and `club_world_cup` meet that condition.
- A pure knockout does not: `domestic_cup`, `club_qualifying` and the super cups show nothing after
  they finish.
- The tournament exception is national-only. A club competition never takes it, however
  tournament-shaped it is, so `club_world_cup` uses the last 5.

| competition_type | type status | Before it starts | While it's running | After it's finished |
|---|---|---|---|---|
| domestic_league | active | Previous season of this league | Last 5 across all the club's competitions | Full completed season |
| domestic_cup | active | Last 5 across all the club's competitions | Last 5 across all the club's competitions | — |
| domestic_super_cup | taxonomy | Last 5 across all the club's competitions | — (single match) | — |
| club_qualifying | taxonomy | Last 5 across all the club's competitions | Last 5 across all the club's competitions | — |
| continental_cup | active | Last 5 across all the club's competitions | Last 5 across all the club's competitions | Full completed edition |
| continental_super_cup | active | Last 5 across all the club's competitions | — (single match) | — |
| club_friendly_domestic | not ingesting | Defer (low signal) | — | — |
| club_world_cup | active | Last 5 across all the club's competitions | Last 5 across all the club's competitions | Full completed edition |
| intercontinental_super_cup | taxonomy | Last 5 across all the club's competitions | — (single match) | — |
| club_friendly_international | not ingesting | Defer (low signal) | — | — |

### National-team competitions

| competition_type | type status | Before it starts | While it's running | After it's finished |
|---|---|---|---|---|
| qualifying | active | Last 5 across the national team's matches | All matches so far in this qualifying campaign | Full completed campaign |
| continental_championship | active | The team's qualifier matches | All matches so far in this tournament | Full completed tournament |
| world_championship | active | Qualifier matches (until group-stage MD1) | All matches so far in this tournament (from group-stage MD2) | Full completed tournament |
| national_team_friendly | not ingesting | Defer (low signal) | — | — |

**The tournament exception.** Live form is cross-competition for every running competition.
Tournaments are the deliberate exception: `world_championship` and `continental_championship` use
every match so far within the tournament. That window is cumulative and is never capped at 5. Its
`window_type` values are `tournament_to_date` and `qualifiers` (section 8.4). MD1 and MD2 are the
team's first and second group-stage matches.

### Football rules for every window

- **No opponent exclusion.** Every match stays in the form window. No filter removes a match, such
  as a cup tie against lower-division opposition.
- Context, such as the standings and the opponent's league or level, lets the fan read the number
  correctly.
- Cross-competition rates are raw: they do not adjust for opponent quality. The window meta line
  names the window, so the fan reads the rate correctly.
- The team form window always carries its sample size, `games_in_window`, even where a surface does
  not show it.

---

## 5. Model architecture

Selection decides which matches a window holds. Aggregation applies the metric formulas to those
matches. The two are separate, and both live in the **intermediate** layer.

| Step | Team | Player |
|---|---|---|
| Match rows: one row per entity per finished match | `int_legs__team_match` | `int_legs__player_match` |
| Form window | `int_team_momentum_window` selects; `int_team_momentum__metrics` aggregates | `int_player_momentum__metrics` aggregates over the team's selection |
| Season record | `int_team_season_record` selects; `int_team_season__metrics_cumulative` aggregates | `int_player_season_record` selects and aggregates |

- **Match rows.** A team match row carries the team's cleaned stats, the opponent's stats,
  `competition_type` and `entity_type`. Every window is a filter and an aggregate over these rows.
- **Form window.** It holds the entity's last 5 matches across all its competitions, as of the
  upcoming fixture. It exists only for an upcoming fixture, because a played match makes it
  obsolete.
- **Season record.** It is cumulative within one competition through each match of the season. One
  model gives the record to date, the full season and year-over-year.

Each form window carries a descriptor for the UI's window meta line: `window_type`,
`games_in_window`, `contributing_competitions`, `phase`.

---

## 6. Marts

### Momentum marts

- `mart_team_momentum` and `mart_player_momentum` each serve every competition type. A reader
  filters them by `league_code`.
- Each metric is a column, beside the descriptor columns.
- `mart_team_momentum_window` lists the matches of each team form window.
- The mart inventory in `dbt_project/docs/layering.md` states each grain.

### Play-offs

A relegation or promotion play-off is a **stage within its parent competition**. It takes that
competition's type and is never a type of its own. Cross-competition form covers a play-off with no
special rule: each side brings its own recent form. No model reads a per-league list of play-off
rounds. A "Relegation play-off" label derives **generically from the round name**.

### Folder organisation

> **Shared by default; a type-specific folder only where the output shape truly differs.**

Cross-type concerns live in a **shared** folder: form, the match rows and window selection.
Genuinely type-specific surfaces keep type folders.

| Type-specific | Shared (cross-type) |
|---|---|
| Standings + relegation/promotion zones (leagues) | Form / momentum |
| Bracket / knockout progression (cups) | Building-block match rows |
| Group-stage tables (continental / tournaments) | Window selection |

---

## 7. Out of scope

- **Opponent-adjusted form.**
- **Other surfaces**: standings, per-fixture stats, team profile and player profile. Each has its own
  mart and wireframe.
- **Friendlies**: taxonomy only. Form windows exclude them once they are ingested.
- **Year-over-year**: rule R6 in `dbt_project/models/docs/metric_rules.md` states where it applies.

---

## 8. Player performance surface

> [`content_architecture.md`](content_architecture.md) specifies the site-wide content model that
> reads this surface: blocks, tabs, navigation and the marts.

This section states the player windows and the one aggregation rule. Metric definitions stay in
the `metric_catalogue.csv` seed. The locked display rows stay in
`docs/wireframes/metrics_display.md`.

### 8.1 One aggregation, two windows (the core rule)

There is **one** aggregation logic, and the window is the only variable. The per-match player row
(`int_legs__player_match`) is the shared building block. **Form** and **season** apply the same
aggregation to a *different set of matches*. The aggregation never forks.

- Rules R1 to R7 of the catalogue table's description state how each value is computed over the
  window's matches, and when it is blank. They live in `dbt_project/models/docs/metric_rules.md`.
- `scripts/generate_metric_sql.py` writes the aggregation of every window from the catalogue
  formulas.
- `docs/wireframes/metrics_display.md` states how a zero denominator renders.
- The display shows **totals and the four weighted percentages** of the locked rows, **not**
  per-match rates.
- The single deliberate average is "average minutes per appearance" in the context block (section
  8.2). Appearances normalise it.

**Selection is separate from aggregation.** Selection takes several shapes: club last 5, season to
date within one competition, and the national-team context window (section 8.4). Each shape feeds
the *same* aggregation. Every selector lives in the **intermediate** layer
(`dbt_project/docs/layering.md`). A new window shape needs a new intermediate selector. A mart never
holds selection logic.

### 8.2 What we show

The surface shows the nine locked player rows of `docs/wireframes/metrics_display.md`. It adds an
appearance and playing-time **context block**. The context block is a proposed addition to that
locked display contract.

| Row | Form (last 5) | Season | Aggregation |
|-----|---------------|--------|-------------|
| **Appearances** (apps · starts · subs) | `4 of 5 · 3 starts` | `26 · 22 starts · 4 sub` | count |
| **Playing time** (total · avg per app) | `310 min · Ø 78` | `2,040 min · Ø 78` | sum; avg = total ÷ apps |

The **window meta line** also shows the **last appearance with the year**, such as
`18 May 2026 vs Dortmund`. The block gives the sample size and availability that make the season
totals readable.

All of these are **mart columns**: appearances, starts, subs, total minutes,
avg-minutes-per-app, `last_appearance_date` and `last_appearance_opponent`. The model picks the
`max(kickoff)` and joins the opponent. The export and the UI only **format** these values. They
derive, rank and select nothing (`dbt_project/docs/layering.md`, consumption layer).

### 8.3 Season model

**One** player-season model holds a player's season.

- **Grain:** one row per player **per club** per competition per season. A mid-season transfer
  gives a **separate per-club row**; the rows are not pooled.
- **Within one competition** always, never across competitions.
- The row carries **this season and the previous season side by side**. This is a persistent
  comparison, not only a pre-season fallback.
- The previous season is a set of **parallel columns on the same per-club-season row**, such as a
  `_prev_season` set. It is **not** a second row, so the grain and the key stay as stated.
- **The surrogate key covers the full grain.** The model is `int_player_club_season__metrics`, and
  its key is `player_club_season_sk`.
- The key hashes `player_sk`, `team_sk` and `season_sk`. `season_sk` identifies one competition in
  one season.
- A `unique` test holds the grain. The key mirrors the team mapping's
  `team_competition_season_sk`.

### 8.4 Window matrix: which matches form each window

**Club competitions:** the club rows of section 4 apply to players unchanged. A player's club form
is his club's form window, so there is no second table.

**National-team competitions** are **context, not form**. Club and national figures stay strictly
separate: the national view never borrows club data.

| State | What we show |
|---|---|
| Any national-team match outside a big tournament (qualifiers, friendlies, warm-ups) **and** before a big tournament | Last **≤5 national-team appearances**, pooled across **all** national-team competition types (friendlies included once ingested), by recency, **no season cap** |
| **Big tournament** (world / continental championship): **during and after** | **Cumulative** tournament figures **only** |
| *(Once national-team history is ingested)* | Career national-team record, **grouped by national-team competition type** (WC · Euro · qualifiers · friendlies) |

Symmetry: a club fixture takes the last 5 across club competitions. A national fixture takes the
last 5 across national-team competitions. Big national tournaments are the cumulative exception,
the same shape as the team rule in section 4.

This matrix produces a **fixed set** of window kinds:

- domestic previous season;
- club last 5;
- domestic or club full season;
- national-team context: up to 5 national-team appearances, pooled;
- big-tournament cumulative.

The models' `window_type` values carry these kinds. Each column has an `accepted_values` test. The
`window_type` columns are the single source for window kinds.

| Path | `window_type` values |
|---|---|
| Form window (momentum) | `last_5`, `tournament_to_date`, `qualifiers` |
| Season record | `season_to_date`, `prev_season` |

### 8.5 National figures are context

A player's national-team figures are context, not a prediction of tournament form. They never draw
on club matches. A player's World Cup figures therefore never come from his domestic club.

### 8.6 Framing

**No separate "context against form" UI mechanism exists.** The **window meta line** declares the
scope for each state. Its copy carries the difference: club "form", national "appearances /
record". The i18n layer sets the final wording. `docs/wireframes/metrics_display.md` owns the window
meta line.

### 8.7 Where each player window is served

- **A national fixture preview:** the momentum path serves the national-team context, framed by the
  section 8.6 meta line.
- That path is `mart_player_momentum` over the team's window from `int_team_momentum_window`. The
  national window is cross-competition with no season cap, which is the section 8.4 shape.
- **The player profile:** the national rows of `mart_player_career` and its
  `national_appearances_total` column carry the career national-team record.
