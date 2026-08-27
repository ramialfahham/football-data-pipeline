# 14 — Team → Stats (vs league)

> A sub-screen of the team page ([02](02_team_profile.md)). Field-bound against
> `mart_team_competition_benchmarks` — **built** (the team benchmark chain:
> `int_team_competition_benchmark_metrics_long` → the `int_team_competition_benchmarks` engine → the
> mart; both read the one long form, so the metric set cannot drift). **Rank-based, not percentile** —
> "k of N" + vs-median, honest at a league of N≈18; `metrics_display.md` §"Percentile display" is explicit
> that the team benchmark is never a percentile. The benchmark payload is **wired** — the team export
> carries a per-season flat `benchmarks[]` block ([GAP-23](99_gaps_register.md), shipped), the same way the
> player Stats screen ([12](12_player_stats.md)) was wired (#627). Display rules follow the
> LOCKED contract in [`metrics_display.md`](metrics_display.md).

## 1. Purpose

"How do they compare to the league — this season?" Each of the ~20 season metrics is placed against the
**other teams in the same competition-season** and read in plain language: **"3rd of 18 · +0.4 vs
median"**. The screen's **stop-scrolling moment** is the column of rank + spread bars. **Rank, not
percentile** — honest at league size N≈18 (a percentile would over-precision a ~18-team field; the mart
chose rank deliberately). The bar states a **distributional position** (where the value sits in the
league's p25–median–p75 spread) and its COLOUR says whether that end is the good one (§4). Since the
direction sweep every rendered metric carries a direction, so a strong rank reads as quality on every
row. **Honest limit:** a team needs **≥ 3 games** to
be ranked (the mart's floor, §6); below it there is no benchmark and we say so.

## 2. URL

```
/{locale}/teams/{kebab-name}-{team_id}/stats/
```

- Sub-path of the canonical team URL (`/teams/{slug}/`, 02 §2); same slug rule.
- Breadcrumb: Home → Teams → {team} → Stats.
- Competition-season is a **selector** (peers are per competition-season). **No position dimension** —
  teams have no positional peers (this is the one structural difference from the player Stats screen 12,
  which carries a position selector).

## 3. Data sources

`data/teams/{team_id}.json` — the existing team payload. Addition (GAP-23, the wiring PR): on each
`seasons[]` row a **`benchmarks[]`** set — one member per `metric_key` — sourced 1:1 from the LONG
`mart_team_competition_benchmarks` (grain `(team_sk, season_sk, metric_key)`). The export **selects/
reshapes only** — the direction-aware reading is applied **at render** from the catalogue `direction`
(the mart is direction-agnostic: `rank` is by `metric_value` DESC). **No num/den atoms** (unlike the
player mart, which carries them via #627): team ratios use the **adjacent-count-row** no-naked-%
mechanism (`metrics_display.md` §composite-row — team comparisons put the count metric in the same block
next to the %), both being separate metrics already in the set.

## 4. Layout

```
┌───────────────────────────────────────────────────┐
│ ▸Home › ▸Teams › ▸Bayern München › Stats          │  (1) breadcrumb
├───────────────────────────────────────────────────┤
│  [crest] Bayern München — Stats                   │  (2) identity header
│  [ Bundesliga 2025/26 ▾ ]                         │  (3) season selector
│  ranked within Bundesliga 2025/26                 │      each row shows its own "of N" (§5)
├───────────────────────────────────────────────────┤
│  GOALS                                            │  (4) group subhead (metrics_display order)
│  Ø Goals          2.2   3rd of 18   +0.4  ▐███▌   │      value · rank · vs-median · spread bar
│  Ø Goals against  0.8   1st of 18   −0.5  ▐█▌     │      lower_better → rank mirrored (1st = fewest)
│  % Clean sheets   43%   2nd of 18   +6pp  ▐███▌   │      clean_sheets_pct; the fixture windows show the count
│  SHOOTING                                         │      order = the LOCKED shooting funnel
│  Ø Shots         14.1   2nd of 18   +2.1  ▐███▌   │      volume →
│  % Shots from box 38%   6th of 18   +2pp  ▐██▌    │      location (% — volume is Ø Shots above) →
│  Ø Shots on target 5.3  3rd of 18   +0.8  ▐███▌   │      on-target volume →
│  % Finishing      28%   5th of 18   +3pp  ▐██▌    │      finishing (shot_accuracy mart-ranked but UNRENDERED — contract)
├────────────────── fold (~700px) ──────────────────┤
│  DUELS                                            │
│  Ø Duels          51    9th of 18   ±0    ▐███▌   │      higher_better, level with the median (±0) → plain ink
│  % Duels won      54%   3rd of 18   +4pp  ▐████▌  │
│  …Defending → Passing → Set pieces → Goalkeeping…  │
├───────────────────────────────────────────────────┤
│  ▸Overview ▸Table ▸Glossary                       │  (5) internal links
└───────────────────────────────────────────────────┘
```

Rows are grouped and ordered by the shared block order in [`metrics_display.md`](metrics_display.md):
**Goals → Shooting → Duels → Defending → Passing → Set pieces → Goalkeeping**. Each row: metric label +
the team's value + **"{rank} of {team_count}"** + the signed **vs-median delta** + a schematic
**spread bar** (the value on a p25–median–p75 track with a dashed median line). The bar column is
schematic here. **Desktop (≥ ~900px)**: two columns of rows; header + selector full-width.

## 5. Module bindings

Members come from the selected `season`; all keys are real `mart_team_competition_benchmarks` columns.
Shipped nesting (at wiring): `seasons[]` → `benchmarks[]` (one member per `metric_key`).

### (2) Identity + (3) selector + header context

| Element | JSON key | ← mart column | Notes |
|---|---|---|---|
| Name / crest | top-level `name`, `crest` | (team payload) | crest fallback = monogram |
| Season options | `seasons[].season_api_year` (+ `league_code`) | `season_api_year`, `league_code` | per competition-season; `benchmarks[]` nests under the season row |
| Header context | `seasons[].league_code` + `season_api_year` | (season selector) | "ranked within {competition} {season}" — **no single peer-count header.** `team_count` is `count(metric_value)` grouped **per `metric_key`** (the engine), so it varies with per-metric coverage; a header "vs N teams" could contradict a row's own "of N". Each metric row carries its own honest **"of {team_count}"** instead (§4 / (4) below). A games-played caption (like 12's minutes/apps) is not shown — the mart carries no games count (§10) |

### (4) Metric rows

| Element | JSON key | ← mart column | Display |
|---|---|---|---|
| Label | `metric_key` | `metric_key` | label + format from `metric_catalogue` (never invented) |
| Value — per-match metric | `metric_value` | `metric_value` | the per-match rate, catalogue `format` (`decimal_0`/`decimal_1`) |
| Value — ratio metric (%) | `metric_value` | `metric_value` | the `percent`; its **volume is the adjacent count row** in the same block (no naked %) |
| Value — `clean_sheets_pct` | `metric_value` | `metric_value` | the clean-sheet **share** — `safe_divide(clean_sheet_games, games_played)`, its own catalogue metric and not the count wearing another name. This screen ranks a team against a league whose teams have played different numbers of matches, so the proportion is the comparable number; the fixture windows serve the count (`clean_sheets`, x/y) instead. Labelled `% Clean sheets` |
| Rank | `rank` (+ `team_count`, `direction`) | `rank`, `team_count` | **"{rank} of {team_count}"** (e.g. "3rd of 18") — direction-mirrored (rule below) |
| vs-median | `vs_median_delta` | `vs_median_delta` | signed, catalogue-formatted (`+0.4`, `+3pp` for percent) |
| Spread bar | derived from `metric_value` vs `p25`/`median`/`p75` | `league_p25`, `league_median`, `league_p75` | the value's position on a p25–median–p75 track; dashed median reference |

**The rank rule (direction-aware, per `metrics_display.md`).** The mart's `rank` is by `metric_value`
**DESC** (rank 1 = the highest value), `team_count` = the ranked field size, and it is
**direction-agnostic**. Display reads it against the catalogue `direction`:

- `higher_better` **or** `neutral` metric → show `rank` as-is ("3rd of 18" = the 3rd-highest value); a
  strong rank reads as quality. (The `neutral` branch is retained for correctness but is dormant — no
  rendered metric is `neutral` since the direction sweep. It used to carry the caveat that for a neutral
  volume/style metric a strong rank meant *most*, not better.)
- `lower_better` metric → **mirror the rank**: `team_count + 1 − rank`, so "1st" marks the best (lowest-
  value) end. A display-side step (the mart ranks DESC). Since the catalogue-wide direction sweep
  (2026-07-21) **two rendered metrics are `lower_better`: `goals_against_per_match` and
  `corners_against_per_match`** (fewest conceded = 1st) — **both** are mirrored. `clean_sheets_pct` is
  `higher_better`. (Superseded: this used to say only `goals_against_per_match` was `lower_better` and that
  `corners_against_per_match` was `neutral` and therefore not mirrored.)

**Direction-aware colour** (CPO 2026-07-21, v2 design review) — ONE bar language across every vs-population
screen, team and player alike; the player percentile screen ([12](12_player_stats.md)) carries the identical
rule. The bar fill goes **green when the metric beats the median in its better direction** and stays **plain
ink** otherwise. Every rendered metric now carries a direction: of the **16 rendered** metrics **14
`higher_better` + 2 `lower_better` + 0 `neutral`** (the 4 mart-ranked-but-unrendered metrics are listed
below). (Superseded: the rule was **no traffic-light colours**, justified as redundant with the median line
and as wrongly verdicting the neutral metrics, with colour deferred to the design pass (#366); and the tally
read "10 `higher_better` + 5 `neutral` + 1 `lower_better`". Both are void — no neutral metrics remain, and
leaving this screen uncoloured while the player screen is coloured would be an inconsistency with no
remaining justification.)

### The benchmarked set — 20 ranked, 16 rendered (`int_team_competition_benchmark_metrics_long`)

The mart **ranks all 20** metrics; the screen **renders the LOCKED 16** (the `metrics_display.md` team
table). **Four** benchmark metrics are ranked in the mart but **NOT independently rendered**, per the
locked "defined but not displayed" list: `shot_accuracy` (superseded by the Ø-shots vs Ø-on-target
juxtaposition) and `tackles_per_match` / `interceptions_per_match` / `blocks_per_match` (the **T · I · B
sub-display of the single Ø Defensive actions row**, not separate ranked rows). `02_team_profile.md` §8
renders the same 16. Grouped and ordered per the metrics_display block order:

| Block | Rendered metrics (metric_key) |
|---|---|
| Goals | `goals_per_match` · `goals_against_per_match` (lower_better) · `clean_sheets_pct` |
| Shooting | `shots_per_match` · `danger_zone_ratio` (%) · `shots_on_goal_per_match` · `finishing_efficiency` (%) — the LOCKED shooting funnel: volume → location → on-target volume → finishing |
| Duels | `duels_per_match` · `duels_won_pct` (%) |
| Defending | `defensive_actions_per_match` — **one ranked row**; its `T · I · B` breakdown (`tackles_per_match` / `interceptions_per_match` / `blocks_per_match`, each a mart metric_value) is a **sub-display of this row**, not separately ranked (LOCKED row 10) |
| Passing | `passes_per_match` · `pass_accuracy` (%) · `key_passes_per_match` |
| Set pieces | `corner_kicks_per_match` · `corners_against_per_match` (lower_better) |
| Goalkeeping | `save_ratio` (%) |

The six `percent` ratios sit next to their volume count in the same block (Ø Shots → % accuracy; Ø Duels
→ % Duels won; Ø Passes → % accuracy). **`save_ratio` is the one `%` without a count peer in this set**
(the Goalkeeping block is save_ratio alone) — it renders the `%` as the team profile 02 §8 already does;
adding a saves/faced count is a catalogue matter (GAP-11 family), not this screen.

### (5) Internal links

Back to the team Overview (02), the competition `/table/`, and the metric Glossary (each metric label
deep-links to its glossary entry). No new team-level targets invented.

## 6. States

| State | Trigger | Render |
|---|---|---|
| Normal | — | grouped rows above |
| Below the games floor | team has no mart rows for the season (`season_games_played < 3`) | no bars; "Not enough games this season to rank {team} against the league" |
| Metric absent | no row for that `metric_key` (a coverage gap — UNPIVOT drops nulls) | that row omitted (not a zero bar) |
| Small / coverage-varying N | `team_count` is small, or differs across rows (a player-derived metric may cover fewer teams than a scoreline one) | render; each row shows its own honest "of {team_count}" — there is no single league-wide header count (§5) |
| Multi-competition | several `seasons[]` (competition-seasons) | season selector; no cross-competition blending |

## 7. Interactions

- **Season selector** swaps the rows in place (all seasons are in the payload — no fetch); default =
  most recent, domestic league first (mirrors 02's selector default).
- Each metric label → its metric glossary entry.
- Static-site constraint: the default season renders in HTML for crawlability; other seasons may be
  JS-swapped (sitemap carries one Stats URL per team).

## 8. SEO

- `schema.org/SportsTeam`; no fabricated aggregate rating.
- Title: `{name} — Stats vs {competition} | Matchday IQ` (localized).
- Meta description templated from the top-ranked metrics (e.g. "1st for goals against among Bundesliga teams").
- `BreadcrumbList` (Home → Teams → {team} → Stats); canonical per locale + hreflang.

## 9. Component census

Breadcrumb · profile header (team) · competition-/season selector · group subhead · **rank + spread bar
➕** (value + "k of N" + vs-median + p25/median/p75 track) · empty/absent state · internal-links footer.
(No position selector, and no peer-count sample caption — the two components the player Stats screen 12
has that this does not; the per-row "of N" carries the sample size instead.)

## 10. Gaps

- [GAP-23](99_gaps_register.md) — **export wiring: SHIPPED.** `shape_team_payload` carries a per-season
  flat `benchmarks[]` block from `mart_team_competition_benchmarks` (one member per `metric_key`, no
  position nesting; select/reshape only, consumption-layer contract; the "k of N"/vs-median/spread labels
  applied at render from the catalogue `direction`). All 20 mart rows are carried — this screen renders the
  LOCKED 16. Mirrors GAP-21/#627 for the player.
- `save_ratio` naked % (no count peer in the set) — a catalogue matter (GAP-11 family), not this screen.
- `clean_sheets_pct` renders as a **percent** here, and that is now the declared metric rather than a
  compromise: the count and the share are two catalogue rows, and this screen ranks the share because
  the teams it ranks have played different numbers of matches. The x/y form (02 §8) belongs to the
  fixture windows, which serve `clean_sheets` with its denominator.
- A **games-played sample caption** (the team's sample size, like 12's minutes/apps) would need a
  `season_games_played` column on `mart_team_competition_benchmarks` — a small mart enhancement, not part
  of the GAP-23 export wiring; deferred.
- ~~Colour on the spread bar — deferred to the design pass (#366).~~ **DECIDED 2026-07-21** (see §4):
  direction-aware, green when the metric beats the median in its better direction, plain ink otherwise.
