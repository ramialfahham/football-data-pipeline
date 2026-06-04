# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-04 (end of session — #320 PR #337 open; next: CI green → merge → start #321)_

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
- 🔁 **PR #337 open** — `feat/320-momentum-builder`. W1 last-5 momentum builders +
  marts. **Wait for CI green then merge.**

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

### 1. Merge [PR #337](https://github.com/ramialfahham/football-data-pipeline/pull/337) (#320)
Wait for CI green then merge.

### 2. #321 — de-hardcoding cut-over
Retire `int_matchday__*`/`int_wc__*`, the `mart_matchday_insights`/`_wc`/`_bl1_relegation`
variants, BL1/BL2/L1 round vars. Parallel-run + validate. CI check (manifest → catalogue)
lands here when manifest is updated to window-agnostic names.

## Do NOT
- Do **not** put window suffixes in metric IDs (`_recent`, `_pretournament`, etc.).
- Do **not** add descriptions/tests to `mart_matchday_insights`, `_wc`, or
  `mart_matchday_player_insights` — they are retired in #321.
- Do **not** use dbt MetricFlow / Semantic Layer — use the catalogue **seed**.
- Do **not** infer season boundaries from dates or status flags — use `season_api_year`.
- Do **not** start coding before restating the spec and getting approval.
- **Read `project_metrics_context_model.md` memory AND the updated issue body before
  any build.** Previous chats drifted by skipping one or both.

## Conventions reminder
- Bash for all commands; branch from main before writing any file.
- `validate-local` + `sqlfluff lint models/...` before pushing.
- Issue **body** is the contract — if it's not fully specified there, stop and ask.
