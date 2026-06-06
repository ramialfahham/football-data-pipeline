# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-06 (#321 PR #339 MERGED; all merged feature branches deleted; next: #322 standings mart)_

## Current focus
Building the **metrics context-model foundation** (epic **#317**) — the shared
context/window model + metric layer that all team/player performance marts consume.
Full design: `docs/metrics_context_model.md` (on main). Reasoning/history: memory
`project_metrics_context_model.md`.

## Status
- ✅ **#318** merged — `competition_types` seed (club/national) + CI coverage check.
- ✅ **#319** merged — `competition_registry.csv` seed (league_code→competition_type) +
  three shared building-block legs in `dbt_project/models/4_intermediate/shared/`:
  `int_legs__team_match`, `int_legs__player_match`, `int_legs__team_from_players`.
- ✅ **#331** merged — enforced cross-chat handover: global hooks + this file.
- ❌ **PR #333 closed (wrong)** — wrong metric IDs (window suffixes), missed team_from_players metrics.
- ✅ **Issues #327 + #320 re-specced** — read their issue bodies before starting any build.
- ✅ **#327 merged** (PR #336) — `metric_catalogue.csv` (42 rows: 19 team + 23 player),
  window-agnostic IDs, schema.yml entry.
- ✅ **#320 merged** (PR #337) — `int_momentum__team`, `int_momentum__player`,
  `mart_momentum__team`, `mart_momentum__player` in `shared/`. Validated: VL numbers
  match old mart exactly. WC comparison deferred to #326 (old mart was cumulative W2,
  not comparable to W1).
- ✅ **#321 merged** (PR #339) — de-hardcoding cut-over + a real correctness fix:
  - `mart_matchday_insights` refactored to read from `mart_momentum__team` (same-layer
    ref, documented in `layering.md`). Retired the old `int_matchday__*`/`int_wc__*` chain,
    the BL1-relegation + WC variant marts, `mart_matchday_player_insights`, BL1/BL2/L1
    round vars, 4 stale tests, the metric-consistency macro. `mart_team_season` +
    `int_team_season__full_season_metrics` rerouted to `int_legs__team_match`.
  - `check_layer_contract.py` now enforces the full cross-layer rule (staging no `ref()`;
    core no `ref('mart_*')`).
  - **Coverage-window fix:** cross-competition expansion exposed that momentum ratios
    mixed a full-window numerator with a partial-coverage denominator (sparse stats in
    KL1/VL/MLS → finishing_efficiency 267%). Same-window rule applied: num & denom over
    the same game set, null if none. Per-match stat rates ÷ `games_with_team_stats`,
    player rates ÷ `games_with_player_stats`. Verified on BQ: 0 rows with ratio > 1.
  - **save_ratio reverted** to `saves / (saves + goals_against)` (self-bounding, the
    agreed definition); #320 had silently changed it to `saves / opponent_shots_on_goal`.
    `metric_catalogue.csv` updated to match (consistent with player `save_pct`).
- 🧹 **Branch cleanup (2026-06-06)** — all merged feature branches deleted, local + remote.
  Only `main` remains.

## Key design decisions locked in #320 (do NOT re-debate)
- **W1 scope:** all competition types, club and national. Shown alongside W2 for every fixture.
- **Club season boundary:** `season_api_year` cap — real calendar boundary.
- **National season boundary:** no cap — qualifying campaigns span multiple API seasons;
  recency alone is the correct boundary.
- **W1 vs W2 split:** W1 = last 5 (this PR). W2 = cumulative season-to-date (#326, deferred).
  W2 for national: qualifying during = cumulative campaign; WC/EURO = tournament cumulative.
- **No club/national split at intermediate layer** for W1 — difference is one conditional
  in the JOIN. Split makes sense at W2 where logic truly diverges.
- **docs/metrics_context_model.md §4:** `qualifying during` corrected to
  "All matches so far in this qualifying campaign" (was incorrectly "Last 5").

## Next concrete action (build order)

### #322 — Standings mart (+ relegation/promotion zones) — NEXT
Own design discussion required before building. **Read the #322 issue body first** — it
has a settled scope (design discussion 2026-05-30):
- Two jobs: (1) the competition's own table from `fct_standings` (league table for
  domestic_league; group tables for group stages; none for knockout/super/friendly);
  (2) club domestic-league standing as context on ANY club fixture.
- **Plain table now — NO zones.** Rank, points, form, W/D/L only (all reliable). Zones
  deferred (need per-season sourced reference; data-honesty bar).
- Feeds `league_rank` into `mart_matchday_insights` (currently sourced from
  `mart_team_season.latest_rank` as a temporary measure — see #321).
- Implementation note: `fct_standings.group_description` is API *team description*
  (unreliable zone text), NOT the group name — source the real group id for group tables.

### Then #326 — W2 season-to-date builder + marts
Deferred from #320. Own design discussion. Validate WC cumulative numbers here (the
old WC mart was W2-cumulative; that comparison belongs in #326, not #321).

### Remaining epic #317 surfaces (each its own design pass)
#323 per-fixture stats mart, #324 team profile, #325 player profile.

## Do NOT
- Do **not** put window suffixes in metric IDs (`_recent`, `_pretournament`, etc.).
- Do **not** use dbt MetricFlow / Semantic Layer — use the catalogue **seed**.
- Do **not** infer season boundaries from dates or status flags — use `season_api_year`.
- Do **not** start coding before restating the spec and getting approval.
- Do **not** mix a full-window numerator with a partial-coverage denominator in any
  ratio — numerator and denominator must cover the **same** set of games; null when none.
  (This is the #321 coverage bug; the rule is now in `metrics_context_model` thinking and
  guarded by [0,1] range tests on `mart_momentum__team`.)
- Do **not** change a metric definition without flagging it against the live/old
  definition (the save_ratio drift in #320 went unreviewed — don't repeat).
- **Read `project_metrics_context_model.md` memory AND the issue body before any build.**

## Conventions reminder
- Bash for all commands; branch from main before writing any file.
- `validate-local` + `sqlfluff lint models/...` before pushing.
- Issue **body** is the contract — if it's not fully specified there, stop and ask.
