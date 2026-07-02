# 12 — Player → Stats (percentile vs peers)

> A sub-screen of the player page (03). Field-bound against `mart_player_competition_benchmarks` — **built**
> (the player benchmark chain: #559 per-90 metric layer → #561 engine + mart; entity-renamed in #500). The
> benchmark payload is **not yet exported** — every key in §5 is a **proposed** shape pending
> [GAP-21](99_gaps_register.md) (the wiring PR); this spec is written ahead of it, the same way Squad (11)
> preceded its wiring (#619). Display rules follow the LOCKED contract in
> [`metrics_display.md`](metrics_display.md) §"Percentile display (vs-peers)".

## 1. Purpose

"Where does he sit — in context?" Each stat is placed against the player's **positional peers** in that
competition-season and read in plain language: **"top 5%"**, **"median"**, **"bottom 18%"**. This is the
fbref-grade context layer, worded for a fan rather than an analyst — the screen's **stop-scrolling moment**
is the column of percentile bars. The bar states a **distributional position** (where the value sits among
peers), not a verdict: for a quality metric a high position reads as good, for a volume/style metric it just
reads as *a lot* (§5). **Honest limit:** a player needs enough minutes to be ranked (the mart's floor, §6);
below it there is no benchmark, and we say so rather than draw a bar.

## 2. URL

```
/{locale}/players/{kebab-name}-{player_id}/stats/
```

- Sub-path of the canonical player URL (`/players/{slug}/`, 03 §2); same slug rule.
- Breadcrumb: Home → Players → {player} → Stats.
- Competition-season is a **selector** (peers are per competition-season); for a multi-position player a
  **position selector** picks which peer group is shown (§6, §7).

## 3. Data sources

`data/players/{player_id}.json` — the existing player payload. **Proposed** addition (GAP-21): a per-season,
per-position **`benchmarks[]`** set, one member per benchmarked metric, sourced 1:1 from the LONG
`mart_player_competition_benchmarks` (grain `(player_sk, season_sk, position_group, metric_key)`). The export
**selects/reshapes only** — the "top X%" label is applied at render from the catalogue `direction` (the mart
is direction-agnostic). For the five **ratio** metrics the wiring PR must additionally carry the num/den
atoms from `int_player_season_position__metrics` (§5, GAP-21), so the volume triple can render (no naked %).
The exact nesting (season → position_group → metrics) is confirmed at the wiring PR. Until GAP-21 lands the
payload carries no `benchmarks[]`; the surface is not generated (§6).

## 4. Layout

```
┌───────────────────────────────────────────────────┐
│ ▸Home › ▸Players › ▸Harry Kane › Stats            │  (1) breadcrumb
├───────────────────────────────────────────────────┤
│  [photo] Harry Kane — Stats                       │  (2) identity header
│  [ Bundesliga 2025/26 ▾ ] [ Forward ▾ ]           │  (3) season + position selector
│  vs 41 forwards · 2,470 min · 29 apps             │      sample line
├───────────────────────────────────────────────────┤
│  GOALS                                            │  (4) group subhead (metrics_display order)
│  Goals            0.82            ▐███████▌ top 5%│      per-90 value · bar (dashed median) · label
│  Assists          0.31            ▐█████▌ top 28% │
│  SHOOTING                                         │
│  Shots on target  1.9             ▐██████▌ top 12%│
│  Finishing        18 of 74 · 24%  ▐████▌ median   │      ratio → volume triple in the value slot
├────────────────── fold (~700px) ──────────────────┤
│  DUELS                                            │
│  Duels won        3.1             ▐███▌ bottom 40%│      per-90, neutral → a lot, not good
│  Duels won %      96 of 178 · 54% ▐████▌ top 30%  │      ratio → volume triple
│  …the rest of the position's eligible metrics…    │
├───────────────────────────────────────────────────┤
│  ▸Overview ▸Match log ▸Glossary                   │  (5) internal links
└───────────────────────────────────────────────────┘
```

Rows are grouped and ordered by the shared block order in
[`metrics_display.md`](metrics_display.md) (Goals → Shooting → Duels → Defending → Passing → Set pieces →
Goalkeeping). Each row: metric label + the player's value (a per-90 rate, or the **volume triple** for a
ratio metric) + a **single-fill rank bar on a track** with a **dashed median line** + the plain-language
label. The bar column is schematic here — a ratio triple is wider than a per-90 rate. **Desktop (≥ ~900px)**:
two columns of rows; header + selectors full-width.

## 5. Module bindings

Members come from the selected `(season, position_group)`; all keys **proposed** (GAP-21), each a real
`mart_player_competition_benchmarks` column.

### (2) Identity + (3) selectors + sample line

| Element | JSON key | ← mart column | Notes |
|---|---|---|---|
| Name / photo | top-level `name`, `photo` | (player payload) | photo fallback = monogram |
| Season options | `benchmarks[].season_api_year` (+ `league_code`) | `season_api_year`, `league_code` | per competition-season |
| Position options | `benchmarks[].position_group` | `position_group` | GK / DEF / MID / ATT; one set per qualifying position |
| Sample line | `peer_count`, `minutes`, `appearances` | `peer_count`, `minutes`, `appearances` | "vs {peer_count} {position}s · {minutes} min · {appearances} apps" |

### (4) Metric rows

| Element | JSON key (proposed) | ← mart column | Display |
|---|---|---|---|
| Label | `metric_key` | `metric_key` | label + format from `metric_catalogue` (never invented) |
| Value — per-90 metric (13) | `metric_value` | `metric_value` | the per-90 rate, catalogue `format` (`decimal_1`) |
| Value — ratio metric (5) | `metric_value` + num/den atoms | `metric_value` + atoms (carried by GAP-21) | the **volume triple** `{num} of {den} · {pct}%` — no naked % |
| Bar fill | derived from `percentile` (+ `direction`) | `percentile` | fill = the **distributional position** on a 0–100 track |
| Median line | fixed at 50 | (`peer_median`) | dashed reference = the median peer |
| Rank label | `percentile` (+ `direction`, `rank`, `peer_count`) | `percentile` / `rank` / `peer_count` | **"top X%" / "median" / "bottom X%"** (rule below) |
| Sample caption | `peer_count`, `minutes`, `appearances` | same | the sample line; `rank` k-of-`peer_count` is the exact "3rd of 41" form |

**The label rule (distributional position, per `metrics_display.md`).** The mart's `percentile` is
`percent_rank` by value **ascending** (0 = lowest value among peers, 1 = highest) — **direction-agnostic**.
Display reads it as a position among the player's positional peers:

- `higher_better` **or** `neutral` metric → position = `percentile`, and `rank` (mart-computed by value
  **descending**) is shown as-is ("1st of N" = the highest value).
- `lower_better` metric → **mirror both**: position = `1 − percentile` **and** the caption rank =
  `peer_count + 1 − rank`, so "top" / "1st" mark the better (low-value) end. The mart is direction-agnostic
  (`percentile` ascending, `rank` descending), so both mirrors are a display-side step.
  **Defined but dormant — 0 of the 18 metrics are `lower_better` today.**

Then, on a 0–100 scale: **above the median → "top X%"**, **below → "bottom X%"**, **at the median → "median"**
(the dashed line). The strong extreme reads **"top 1%"**, never "top 0%" (the exact percentile→label rounding,
and whether the extreme falls back to the `rank` "k of N" form, is a render detail confirmed at the wiring PR).

What "top" **means** depends on the metric and the screen does **not** editorialize it — of the 18 metrics
**11 are `higher_better`** and **7 are `neutral`** (`saves_per90`, `passes_per90`, `duels_won_per90`,
`defensive_actions_per90`, `tackles_per90`, `interceptions_per90`, `blocks_per90`). For a `higher_better`
metric a high position reads as quality; for a `neutral` volume/style metric "top" just means *most* (a busy
keeper, a high-volume passer) — not better. **No traffic-light colours** — they are redundant with the median
line and would wrongly imply a good/bad verdict on the neutral metrics; the bar is one neutral **data token,
colour deferred to the design pass (#366)**.

**Ratio metrics carry their volume (no naked %).** The five ratio metrics show the triple `{num} of {den} ·
{pct}%`; their atoms all exist in `int_player_season_position__metrics` and the GAP-21 wiring PR must carry
them into the payload:

| Ratio metric | numerator | denominator |
|---|---|---|
| `save_pct` | `saves` | `saves + goals_against` |
| `pass_accuracy_pct` | `passes_accurate` | `passes_total` |
| `finishing_efficiency` | `goals − goals_penalty` | `shots_on_goal` |
| `dribbles_success_pct` | `dribbles_success` | `dribbles_attempts` |
| `duels_won_pct` | `duels_won` | `duels_total` |

The benchmarked set is the **18 metrics** of `player_benchmark_metrics()`, each ranked **within its own
position group**: **GK** = saves, save %, passes, pass accuracy; **DEF / MID / ATT** = passes, pass accuracy,
goals, assists, scorer points, shots on target, key passes, finishing, dribbles (count + %), duels won
(count + %), defensive actions, tackles, interceptions, blocks. `finishing_efficiency` and `duels_won_pct`
are now catalogued (both `higher_better`, via #530b/#621) — they were the last blockers, so the screen can
bind all 18 honestly.

### (5) Internal links

Back to the player Overview (03), the Match log, and the metric Glossary (each metric label deep-links to
its glossary entry). No new player-level targets invented.

## 6. States

| State | Trigger | Render |
|---|---|---|
| Normal | — | grouped rows above |
| Below the minutes floor | player has no mart rows for the season (mart filters `minutes >= 270` in the position) | no bars; "Not enough minutes this season to rank {player} against peers" |
| Metric not eligible / below its floor | no row for that `metric_key` (position eligibility, or finishing with `shots_on_goal < 10`) | that row omitted (not a zero bar) |
| Thin peer group | small `peer_count` | render, but the sample line states `peer_count` plainly (honest small-N) |
| Multi-position | several `position_group` sets | position selector; **default = the position with the most `minutes`** (a display selection, not a derived fact) |
| No value | `metric_value` null | row omitted |
| Not yet wired | GAP-21 open (today) | payload carries no `benchmarks[]`; the surface is not generated |

## 7. Interactions

- **Season + position selectors** swap the rows in place (all sets are in the payload — no fetch); default
  season = most recent, default position = most minutes.
- Each metric label → its metric glossary entry.
- Static-site constraint: the default (season, position) renders in HTML for crawlability; other
  combinations may be JS-swapped (sitemap carries one Stats URL per player).

## 8. SEO

- `schema.org/Person` (athlete); no fabricated aggregate rating.
- Title: `{name} — Stats percentiles ({competition}) | Matchday IQ` (localized).
- Meta description templated from the top-ranked metrics (e.g. "top 5% for goals among Bundesliga forwards").
- `BreadcrumbList` (Home → Players → {player} → Stats); canonical per locale + hreflang.

## 9. Component census

Breadcrumb · profile header (player) · competition-/season selector · **position selector ➕** ·
group subhead · **percentile rank bar ➕** (single fill + track + dashed median line) · **sample caption ➕** ·
empty/absent state · internal-links footer.

## 10. Gaps

- [GAP-21](99_gaps_register.md) — `mart_player_competition_benchmarks` is built (#559 layer → #561 engine +
  mart) but not carried by the player export; the Stats surface has no payload. Disposition: add a
  per-(season, position) `benchmarks[]` block to `shape_player_payload` (select/reshape only), carrying the
  ratio num/den atoms so the volume triple renders. Own follow-up PR.
- The **team** vs-benchmark is a separate screen — `mart_team_competition_benchmarks` is **rank-based, not
  percentile** (honest at N≈18), so it renders "k of N" + vs-median, not "top X%". Its own later spec.
- Season-over-season / YoY for players depends on the player-season foundation (#480, Phase C) — not here.
