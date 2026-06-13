# Metrics Context & Window Model

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
per-league logic, no maintained date tables):

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

| competition_type | status | Before it starts | While it's running | After it's finished |
|---|---|---|---|---|
| domestic_league | active | Previous season of this league | Last 5 across all the club's competitions | Full completed season |
| domestic_cup | active | Last 5 across all the club's competitions | Last 5 across all the club's competitions | Their full cup run |
| domestic_super_cup | taxonomy | Last 5 across all the club's competitions | — (single match) | — |
| club_qualifying | taxonomy | Last 5 across all the club's competitions | Last 5 across all the club's competitions | Last 5 across all the club's competitions |
| continental_club | active | Last 5 across all the club's competitions | Last 5 across all the club's competitions | Full completed edition |
| continental_super_cup | active | Last 5 across all the club's competitions | — (single match) | — |
| club_friendly_domestic | not ingesting | Defer (low signal) | — | — |
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
  comparison for teams and players) — its own design discussion.
- **Opponent-adjusted form** — the named next metric.
- **Other surfaces** — standings, per-fixture stats, team profile, player profile — each
  its own mart and discussion.
- **Friendlies** — taxonomy only; excluded from form windows when eventually ingested.
- **Year-over-year-by-matchday** applies to **league formats**; cups/tournaments have a
  cumulative number but not matchday-aligned year-over-year.
