# Metrics Context & Window Model

> **Metric definitions live in the `metric_catalogue.csv` seed (the SSoT); this doc governs the
> window / context model only.** See `docs/metric_layer.md` for the map of where each thing lives.

How the platform decides, for a given upcoming fixture, **which past matches form a
team's or player's performance window, and how to label it**. This is the shared
foundation every performance-style mart consumes — today the matchday momentum marts,
later standings, per-fixture stats, and team/player profiles (each its own mart and
its own design discussion).

`league_code` remains the partition key everywhere; nothing here hardcodes a
competition. The rules are driven by two declared properties — **competition type**
and **temporal phase** — plus the **club/national** split.

---

## 1. Two kinds of number

Every performance figure in the product is one of two kinds, and they use different
windows:

| Kind | Answers | Scope |
|------|---------|-------|
| **Live form (momentum)** | "How are they playing *right now*?" | **Cross-competition** — the entity's last 5 matches across all its competitions |
| **Season record** | "What have they done *in this competition*?" | **Within that one competition** (cumulative season-to-date; powers year-over-year) |

Cross-competition applies **only** to the live form window. The season record is always
within one competition.

---

## 2. Club vs national — a property of the competition *type*

Club-vs-national is **declared once per competition type**, not stamped on every
competition. It lives in a dbt seed (`competition_types`), one row per type, with a
CI check that every `competition_type` used in the registry has a row.

- **Rule:** no competition type may be both club and national.
- `qualifying` means *national-team* qualifying (WC/EC qualifiers). Club qualifying
  rounds, if ever onboarded, get their own clearly-club type.
- Downstream models derive club/national by looking up the type — never hardcoded in SQL.

A club's form only ever includes club matches; a national team's only national matches.

---

## 3. Temporal phases (and how we detect them)

Three phases, detected **generically by fixture counts** in the current edition (no
per-league logic, no maintained date tables).

⚠ **The counts are the TEAM's own fixtures in that competition edition, not the competition's**
(clarified by the CPO 2026-08-12). For a league the two are the same — everyone plays to the final
matchday. For a **knockout** they are not: a club dumped out of the cup in round one has ≥1
finished and 0 upcoming from that moment, so it is in "after it's finished" while the cup itself
runs on for months. That is the intended reading, and it is what makes "their full cup run" honest
for a team whose run was a single match.

| Phase | Detection | Meaning |
|-------|-----------|---------|
| **Before it starts** | 0 finished, ≥1 upcoming | first fixture of the edition — no live form yet |
| **While it's running** | ≥1 finished, ≥1 upcoming | edition underway |
| **After it's finished** | ≥1 finished, 0 upcoming | edition complete |

- "Before it starts" is **literal** — exactly zero finished matches. From the first
  finished match we are "while it's running," showing *up to* the last 5. We **never mix
  seasons** to pad an early-season sample.
- The off-season handles itself: a competition stays "after it's finished" until the
  next edition's fixtures appear, which flips it to "before it starts."
- Play-off rounds are a **stage within** the parent competition (see §6), so a league is
  not "finished" until its play-offs are also played.

---

## 4. The window matrix (per competition type)

The 12 types from the taxonomy (`docs/product_direction_threads.md`). 7 are active; 5
are taxonomy-only / not yet ingested.

**Window meanings:**
- **Previous season of this league** — last season's record *in this same competition*
  (the reminder shown before live form exists).
- **Last 5 across all the club's / national team's competitions** — this season only,
  ordered by kickoff, capped at 5; club never includes national matches and vice-versa.
- **All matches so far in this tournament** — cumulative from the tournament's start.
- **Full completed edition** — the just-completed season/tournament record.

### Club competitions

**The two types added 2026-08-12 (#57) each inherit an existing row** — CPO ruling, same date:
`club_world_cup` follows **`continental_cup`**, `intercontinental_super_cup` follows
**`continental_super_cup`**.

**When a competition gets an "after it's finished" figure at all** (CPO 2026-08-12): only when
every entrant plays a group or league phase, so there are **enough matches to be worth
aggregating**. `domestic_league`, `continental_cup` and `club_world_cup` qualify — the Champions
League and the Club World Cup both have a group phase, so a club eliminated in the knockout still
has a full group campaign behind it. A **pure knockout does not**: `domestic_cup`,
`club_qualifying` and the super cups show nothing, because a team's run there can be a single
match and phase is per team (§3).

⚠ Read "full completed season / edition" as **all of that team's matches in that competition
edition** — not "only if they reached the final". That distinction is the whole reason the
knockout rows are empty.

So the cumulative-within-tournament exception stays **national-only**: a club competition never
gets it, however tournament-shaped it looks. That is also why `CWC`'s window is unchanged by the
re-type — it resolved to last-5 as `continental_club` and still does.

| competition_type | status | Before it starts | While it's running | After it's finished |
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

| competition_type | status | Before it starts | While it's running | After it's finished |
|---|---|---|---|---|
| qualifying | active | Last 5 across the national team's matches | All matches so far in this qualifying campaign | Full completed campaign |
| continental_championship | active | The team's qualifier matches | All matches so far in this tournament | Full completed tournament |
| world_championship | active | Qualifier matches (until group-stage MD1) | All matches so far in this tournament (from group-stage MD2) | Full completed tournament |
| national_team_friendly | not ingesting | Defer (low signal) | — | — |

**The principle:** live form is cross-competition for every ongoing competition. The
deliberate exception is **tournaments**, which use cumulative-within-the-tournament —
that is the football-correct framing (judge a team within this tournament's field), not
a compromise.

### Football-analyst notes

- **No opponent exclusion.** Every match stays in the form window; we never silently
  filter (e.g. a cup tie vs lower-division opposition). Instead we **show context**
  (standings, opponent league/level) so the fan reads the number correctly.
- **Opponent-adjusted form is the named next metric** — the proper fix for mixing
  opponent quality across competitions. Until then, cross-competition raw rates are
  accepted with honest labelling.
- **Sample size is always available** (`games_in_window`), even when not always shown.

---

## 5. Model architecture

Separate **which matches** (selection) from **the metric math** (aggregation). All in
the **intermediate** layer.

```
core facts (fct_fixture, fct_fixture_team_stats, fct_fixture_player_stats)
   └─ building-block "match leg" tables  (one row per team / player per finished match)
        ├─ last-5 momentum builder      (cross-competition, as of the upcoming fixture)
        └─ season-record builder         (within-competition, cumulative through matchday)
              └─ marts
```

- **Building-block leg** — one row per (team, finished match) with raw stats + opponent
  aggregates (generalised from `int_matchday__finished_fixture_team_leg`, now carrying
  `competition_type` and `entity_type`). A parallel player-leg comes off
  `fct_fixture_player_stats`. Every window is a *filter + aggregate* over these rows.
- **Last-5 momentum builder** — the entity's last 5 legs across all its competitions, as
  of the upcoming fixture. Computed **only for the upcoming fixture** — it is momentum,
  obsolete once the match is played. Grain: (upcoming fixture, team/player).
- **Season-record builder** — cumulative within one competition through each matchday (season-to-date).
  Grain: (team, league_code, season, matchday). Yields current-to-date, full-season, and
  year-over-year from one model. *How best to surface full-season analysis is its own
  discussion.*

Each window carries a descriptor for the UI's "form window: …" line: `window_type`,
`games_in_window`, `contributing_competitions`, `phase`.

---

## 6. Marts and de-hardcoding

### Momentum marts (this surface)

- **Two cross-type marts:** team momentum and player momentum. One row per upcoming-
  fixture side; the app slices by `league_code`. Wide shape (each metric a column) plus
  the descriptor columns.
- These **replace** the hardcoded `mart_matchday_insights` (BL1/BL2/L1 round exclusions),
  `mart_matchday_insights_bl1_relegation`, and `mart_matchday_insights_wc`.

### Play-offs

A relegation/promotion play-off is a **stage within its parent competition**, inheriting
that competition's type — never a standalone type. Cross-competition form handles play-
offs naturally (each side brings its own recent form), so the separate relegation mart
and the BL1/BL2/L1 round-name vars are **deleted**. A "Relegation play-off" label is kept
but derived **generically from the round name**, not per-league hardcoded lists.

### Folder organisation (refines product thread 2)

> **Shared by default; a type-specific folder only where the output shape truly differs.**

Cross-type concerns (form/momentum, the building blocks, the window selection) live in a
**shared** folder. Genuinely type-specific surfaces keep type folders:

| Type-specific | Shared (cross-type) |
|---|---|
| Standings + relegation/promotion zones (leagues) | Form / momentum |
| Bracket / knockout progression (cups) | Building-block legs |
| Group-stage tables (continental / tournaments) | Window selection |

This refines the earlier "type subfolders at intermediate and marts" decision, which
over-applied type folders to *form*. The instinct still holds for standings/brackets/
group-tables.

### Migration approach

**Parallel-run + validate** (data quality is non-negotiable): build the new marts
alongside the old, confirm the numbers match for BL1 and WC, then cut over and delete the
old models, the relegation variant, the BL1/BL2/L1 vars, and update product thread 2.

---

## 7. Deferred / out of scope here

- **Full-season analysis surface** (the season-to-date mart + year-over-year-by-matchday
  comparison) — its own design discussion. **The player half is now resolved in §8** (CPO,
  2026-06-17); the team season surface is already built and stays its own discussion.
- **Opponent-adjusted form** — the named next metric.
- **Other surfaces** — standings, per-fixture stats, team profile, player profile — each
  its own mart and discussion.
- **Friendlies** — taxonomy only; excluded from form windows when eventually ingested.
- **Year-over-year-by-matchday** applies to **league formats**; cups/tournaments have a
  cumulative number but not matchday-aligned year-over-year.

---

## 8. Player performance surface (resolves the §7 deferral for players)

> The site-wide content model that consumes this surface (blocks → tabs → navigation, the flagship
> reads, and the new marts) is specified in [`content_architecture.md`](content_architecture.md).

Ruled by the CPO, 2026-06-17. This is the player half of the deferred full-season surface.
It fixes the one real gap: the player season rollup exists three ways today with divergent
numbers (e.g. pass accuracy computed as an average of match percentages in one model, weighted
in another) because each re-implements its own aggregation. Definitions stay in the
`metric_catalogue.csv` seed; the locked display rows stay in
`docs/wireframes/metrics_display.md`. Build status: **#480** (consolidate to one
player-season model) shipped (#630); the player national / tournament context (§8.4) is
served without a separate build — see §8.7.

### 8.1 One aggregation, two windows (the core rule)

There is **one** aggregation logic; the window is the only variable. The per-match player leg
(one row per player per finished match, raw stats) is the shared building block. **Form** and
**season** are the same aggregation over a *different set of legs* — the aggregation never forks.

- **Counts** → sum over the window's legs.
- **The four ratios** — duels-won %, dribble-success %, pass-accuracy %, save % → **weighted**:
  `sum(numerator) / sum(denominator)`. **Never** an average of per-match percentages.
- **Honest absence** — only legs the provider gave stats for count; `games_played` is that
  appearance count, not team matches.
- **Zero denominator** → render `—`, the counts still shown (`0 of 0 · —`).
- **Display** is **totals + the four weighted %s** (per the locked rows), **not** per-match.
  The single deliberate average is "avg minutes per appearance" in the context block (§8.2),
  normalised by appearances.

This is why the three models diverged — they each re-implemented the math. The build collapses
them onto one shared aggregation step that both the form mart and the season mart call.

**Selection is separate from aggregation** and may take several shapes — club last-5,
within-competition season-to-date, and the national-team context window (§8.4) — but each feeds
the *same* aggregation. Every selector lives in the **intermediate** layer (`layering.md`); a new
window shape means a new intermediate selector, never selection logic pushed into a mart.

### 8.2 What we show

The nine CPO-locked player rows (`docs/wireframes/metrics_display.md`, 2026-06-11) — referenced,
not restated — **plus** an appearance / playing-time **context block** (a proposed addition to
that locked display contract; recorded here, to be formally amended there — bi-analyst-owned):

| Row | Form (last 5) | Season | Aggregation |
|-----|---------------|--------|-------------|
| **Appearances** (apps · starts · subs) | `4 of 5 · 3 starts` | `26 · 22 starts · 4 sub` | count |
| **Playing time** (total · avg per app) | `310 min · Ø 78` | `2,040 min · Ø 78` | sum; avg = total ÷ apps |

Plus, in the **window meta-line**, the **last appearance with the year** (e.g.
`18 May 2026 vs Dortmund`). The block is the sample-size / availability context that makes the
season totals interpretable.

All of these are **mart columns** — appearances, starts, subs, total minutes, avg-minutes-per-app,
and `last_appearance_date` + `last_appearance_opponent` (the `max(kickoff)` pick and the opponent
join happen **in the model**). The export and UI only **format** them; no derivation, ranking, or
"latest" selection in the consumption layer (`layering.md`).

### 8.3 Season model (what #480 builds)

**One** player-season model, replacing the three divergent rollups.

- **Grain:** per player **per club** per competition per season — a mid-season transfer yields a
  **separate per-club line** (not pooled).
- **Within one competition** always — never cross-competition (cumulative is the within-comp W2).
- Carries **this season + previous season side-by-side** (a persistent comparison, not a
  pre-season-only fallback) — as **parallel columns on the same per-club-season row** (wide; e.g. a
  `_prev_season` set), **not** a second row, so the grain and key below are unchanged.
- **Surrogate key covers the full grain** — `(player_sk, team_sk, league_code, season_sk)`. The
  current rollups key on only `(player_sk, season_sk)`, which is **non-unique** under per-club grain
  (a mid-season transfer collides). #480 replaces it with a full-grain key — mirroring the team
  mapping's `team_competition_season_sk` — under a `unique` test on the grain. The key's name is set
  in #480 (a naming call), but its **columns are fixed by the grain above**.

### 8.4 Window matrix — which legs form each window

**Club competitions — see §4. There is no player divergence, so there is no second table.**

A player's club form *is* his relevant form, which this section has always said. It used to restate
§4's club rules in a condensed two-row form, and that copy drifted: it still named
`continental club` after the type was renamed to `continental_cup`, it never gained
`club_world_cup` or `intercontinental_super_cup`, and its single "Full edition / cup run" cell
covered five competition types that no longer share an "after" rule — domestic cups, club
qualifying and the super cups have none (CPO 2026-08-12). **Struck rather than re-synced**: two
tables that must agree are one table too many, and this one was already wrong on three counts.

**National-team competitions** — reframed as **context, not form** (strict club/national
separation: the national view never borrows club data):

| State | What we show |
|---|---|
| Any NT match outside a big tournament (qualifiers, friendlies, warm-ups) **and** before a big tournament | Last **≤5 national-team appearances**, pooled across **all** NT competition types (friendlies included once ingested), by recency, **no season cap** |
| **Big tournament** (world / continental championship) — **during & after** | **Cumulative** tournament figures **only** |
| *(Future — when NT history is ingested)* | Career national-team record, **grouped by NT competition type** (WC · Euro · qualifiers · friendlies) |

Symmetry: club fixture → last 5 across club comps; national fixture → last 5 across national
comps. Big national tournaments are the cumulative exception (same shape as the team rule, §4).

The distinct **window kinds** this matrix produces are: domestic previous-season · club last-5 ·
domestic/club full-season · national-team context (≤5 NT appearances pooled) · big-tournament
cumulative. The **set is fixed by this matrix.** These kinds are realized as the models' `window_type`
values — `last_5` / `tournament_to_date` / `qualifiers` in the momentum path, `season_to_date` /
`prev_season` in the season-record path — each guarded by an `accepted_values` test. A catalogue
`form_window_kind` enum column was once envisaged but never added; the `window_type` columns are the SSoT.

### 8.5 Override of the legacy form-window dispatch

This **supersedes** the legacy "Form-window dispatch" rule (player WC form drawn from the
**domestic club**, qualifiers excluded). That rule treated
national data as predictive **form** and rejected stale qualifiers in favour of the domestic
club. Reframing the national surface as **context** (not a prediction of tournament form)
dissolves its three objections (roster turnover, stale dates, weaker opposition — all
form-prediction arguments), restores strict club/national separation, and removes the
domestic-league-coverage "Not provided" exposure. **CPO override, 2026-06-17;** football-analytics
confirms the football-correctness.

### 8.6 Framing

**No separate "context vs form" UI mechanism.** The existing locked **window meta-line** already
declares scope per state and carries the distinction through its copy (club → "form";
national → "appearances / record"). Final wording is set at i18n.

### 8.7 Build status

- **#480** — SHIPPED (#630): the three player-season rollups were consolidated onto the per-club
  foundation `int_player_club_season__metrics` (§8.3) using the one shared aggregation (§8.1);
  `int_player_season__metrics` re-expresses it byte-identically.
- **National / tournament context (§8.4)** — served WITHOUT a separate standing selector. On a
  national **fixture preview**, the momentum path supplies the recent NT context (last-5 pooled /
  `tournament_to_date` / `qualifiers`, #653), framed as "appearances / record" via the §8.6 meta-line;
  the national momentum window is already cross-competition with no season cap, so it IS the §8.4 shape
  (no third selector needed). On the **player profile**, the Career screen's national section
  (`mart_player_career` national rows + `national_appearances_total`, #634) carries the career national
  record. A standing NT-context block on the profile was evaluated (#654) and **CLOSED — no consumer**:
  the fixture strip + Career section already cover it, so a standing block had no display-first
  justification. #484 (the original momentum-parity gap) shipped as #653.
- **Cost-gated data** — friendlies ingest (for the NT pool); national-team history (≈ #477, for a
  grouped-by-competition-type career view). PARKED: the rules are defined; the data lights up only when
  ingest is CPO-approved.
