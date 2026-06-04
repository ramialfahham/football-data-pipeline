# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-04 (end of session — #327 PR open; next action: merge #333, then #320)_

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
- ✅ **#331** merged — enforced cross-chat handover: global hooks (`handover_in` /
  `handover_plan_gate` / `handover_out`) + this file. Hooks are **registered and active**
  in `~/.claude/settings.json`. This file is what you (a fresh chat) were just handed.
- 🔁 **#333 / #327 open PR** — `feat/327-metric-catalogue`. Adds
  `dbt_project/seeds/metric_catalogue.csv` (46 rows: 13 team match_preview + 14 WC
  pre-tournament + 19 player atomics), schema.yml entry, `scripts/check_metric_catalogue.py`
  (wired into ci-validate). Frontend JSON untouched (already display-only). CI check
  confirms all 13 manifest metrics have catalogue rows. **Merge this before starting #320.**

## Next concrete action (build order)
1. **Merge [PR #333](https://github.com/ramialfahham/football-data-pipeline/pull/333)** (#327
   metric catalogue seed) — CI must go green first.
2. **#320 — windows + momentum marts** (last-5 momentum builder + season-to-date builder →
   two cross-type momentum marts, team + player; wire consistency tests to the catalogue).
3. **#321 — de-hardcoding cut-over** (retire `int_matchday__*`/`int_wc__*`, the
   `mart_matchday_insights`/`_wc`/`_bl1_relegation` variants, BL1/BL2/L1 round vars;
   parallel-run + validate; update product thread 2 folder rule).

## Do NOT
- Do **not** add descriptions/tests to `mart_matchday_insights`, `_wc`, or
  `mart_matchday_player_insights` — they are retired in #321.
- Do **not** use dbt MetricFlow / Semantic Layer — decided against (query-time/dbt-Cloud;
  doesn't fit pre-computed-marts → static-CDN). Use the catalogue **seed**.
- Do **not** start coding a scoped issue before restating its spec and getting approval.

## Conventions reminder
- Bash for all commands; branch before writing; `validate-local` + `sqlfluff lint models/...`
  before pushing (ci-data-build lints before building). Issue **body** is the contract —
  if it's not fully specified there, stop and ask.
