# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: **2026-06-28** — **Macro-cleanup thread COMPLETE.** This session shipped & merged: **#590** (#500 PR-d step-6 teardown cand. 1+4), **#592** (new macro standard), **#593** (the `team_benchmark_metrics` macro REMOVED via COMPOSE), **#594** (standard trimmed to a "calibrated default"). The player benchmark macro is **KEPT** (it encodes B3 position-eligibility logic — a legitimate macro), with seed-ifying deferred to player-benchmark ship time. **Nothing pending-merge; main is GREEN. There is NO locked next task — the CPO directs from the NEXT candidates below.**_

main carries the full #500 metric layer (#574–#587) + **#590 + #592 + #593 + #594**. **CPO merges, never self-merge — standing rule.** **Website #391 PAUSED; the live MVP must NOT break — standing CPO rule.** Per-item CPO-directed. **The 5-step protocol is LIVE:** Explore → Plan → **Confirm** → Implement → Verify; for any file-touching task ENTER PLAN MODE at the Plan step and WAIT for the CPO's ExitPlanMode approval (= Confirm) before editing.

### FIRST STEPS (cold chat — do in order)
1. `git checkout main && git pull`. **Nothing is pending-merge; main is GREEN.**
2. Read this file top-to-bottom before touching anything.
3. **There is NO locked next task.** The macro thread is finished. Pick the next unit WITH the CPO from "NEXT candidates" below — present the options in plain language and let the CPO choose. Do NOT infer a task from an issue title and do NOT pre-decide a CPO-class (§10) question.
4. **Bash only; never PowerShell.** For any file-touching task: write `.claude/task/contract.md` on a CLEAN tree BEFORE touching any file (impact-map gate for `dbt_project/models/**` + `scripts/export_*.py` + `ingestion/**` + `site*/`; `protected_override` for `.github/workflows/**` etc.) + use **PLAN MODE** for the plan-back. **CPO merges — never self-merge.**

---

### ⭐ THIS SESSION (2026-06-27 → 28) — macro cleanup

| PR | What changed |
|----|--------------|
| **#590** | #500 PR-d step-6 teardown cand. 1+4: `pages-match-preview.yml` trigger repointed off the deleted `metric_definitions.csv` → `metric_catalogue.csv`; doc globs `mart_fixture_stats__{team,player}` / `__*` → `mart_team_fixture_stats` / `mart_player_fixture_stats` (`docs/content_architecture.md` + `docs/wireframes/99_gaps_register.md`). |
| **#592** | NEW "Macros" standard in `dbt_project/docs/engineering_standards.md` §1.3. |
| **#593** | **Removed the `team_benchmark_metrics` Jinja macro via COMPOSE.** New `int_team_competition_benchmark_metrics_long` (BigQuery `UNPIVOT` of the 20 team metrics from `int_team_season__metrics`, `>= 3` games, per team-season). The engine `int_team_competition_benchmarks` now aggregates it; the mart `mart_team_competition_benchmarks` ranks it + joins the engine. Number-preserving — CI `data-build` + benchmark DQ tests GREEN. |
| **#594** | Trimmed §1.3 to a **calibrated default, not a rulebook**: keeps the plain-SQL default + the COMPOSE alternative + 2 verified examples (override hook; an expression that must sit inside a query); drops the "test" line; closes "beyond those, an experienced analytics engineer judges." |

#### Macro decisions LOCKED this session (do NOT re-open without the CPO)
- **Player `player_benchmark_metrics` macro = KEEP.** It is NOT a flat list — it encodes a metric × position **eligibility matrix + a per-metric floor** (`finishing_efficiency` needs `shots_on_goal >= 10`), the CPO **B3** ruling. The engine renders each entry as `CASE WHEN position_group IN (...) [AND floor] THEN col`. That's logic → the §1.3 "earns its place" case. Removing it inline would be 18 verbose CASE blocks (worse, not better).
- **DEFERRED — seed-ify the player eligibility** (a seed: metric × position + a min-shots column; the principled data-driven version, aligned with the metric_catalogue/SSoT direction) **ONLY when the player benchmark actually ships** (#391 paused; nothing reads the mart yet). It is number-sensitive + B3-ruled + unvalidatable locally — do it as its own careful, CI-gated PR.
- **The "dead macro cluster" was a MIRAGE — nothing else is safe to delete.** Read the doc before calling any macro "dead": the round-name macros (`bl1/bl2/l1_*_round_names`) are PLAYOFF-POLICY SCAFFOLDING (`docs/playoff_window_policy.md`, awaiting CPO Phase-3 sign-off + named in the §11 Pages export contract); `union_all` is the layer-contract base-union tool; `domestic_league_codes_in_clause` is referenced only by the stale Pages trigger (= part of task_44698a18); `team_name_key` + `apif_latest_source_partition` look abandoned but are UNCONFIRMED → leave.

#### The live metric chain (durable reference — how the metric layer wires together)
```
metric_catalogue.csv  (SSoT — format, lower_is_better, label_i18n_key, formula)
        +  site/match-preview/metric_bindings.csv  (wiring: live_id → catalogue id + home/away cols + context)
        ↓  scripts/export_metric_definitions_json.py  → site/match-preview/metric_definitions.json
        ↓  site/match-preview/index.html  (reads def.label / def.format / lower_is_better)
Team-season:  int_team_season__metrics  →  mart_team_season_record / _insights / mart_team_profile
        →  scripts/export_team_season_json.py (SELECT *)  →  site/team-season/index.html
```
- **Byte-identity guard:** `tests/test_metric_bindings.py::test_regenerated_json_matches_committed`.
- **Drift guard:** `dbt_project/tests/assert_no_uncatalogued_season_metric.sql` (catches any metric column with no catalogue row).

---

### Session lessons (hard-won — read before touching these areas)

**(2026-06-28, #593) De-macro a shared-list macro via COMPOSE:** build ONE long-form model (BigQuery `UNPIVOT`) that both consumers read — the distribution/engine model aggregates it, the mart ranks it. Number-equivalent by construction: same columns, the `>= N games` filter applied ONCE (in the long form), and `UNPIVOT` default EXCLUDE-NULLS == the prior `where x is not null` (keep the filter defensively in consumers). **Gotcha:** every column in the `UNPIVOT IN (...)` list must share ONE type or it errors at build — verify (the 20 team metrics are all `safe_divide`/`CASE` → FLOAT64). The benchmark mart was a LEAF (nothing reads it) → low blast radius; confirm with `git grep ref('<mart>')` + a scripts/site grep.

**(2026-06-28) Macros are a JUDGMENT call, not a mechanical strip.** Team benchmark macro = flat list → removed (#593). Player benchmark macro = eligibility logic → KEPT. Apply §1.3: remove a macro only when plain SQL reads BETTER. Do NOT remove a macro for consistency.

**(2026-06-28, #592→#594) The CPO pushes back on standards that over-reach.** The first macro standard dressed judgment as a rule/test; the CPO had it trimmed to an honest "calibrated default + the trap + examples + judge the rest." Write standards that calibrate judgment, not decision procedures.

**(2026-06-28) NO local dbt validation this session:** the dbt CLI is BROKEN (`No module named dbt.adapters.factory`) AND the dbt MCP server did not connect. So neither `dbt parse` nor `mcp__dbt__parse` was available. For dbt changes the ONLY gates were the blinded analytics-engineer review + CI `data-build`. Do not assume `mcp__dbt__parse` exists — check.

**`cd && git commit` trips the sole-command gate:** `git_discipline.py` blocks `git commit` unless it is the SOLE command in the Bash call. Run `git commit …` with NO `cd` prefix (cwd already persists at repo root) and nothing chained.

**docs/workflow-only PRs skip the expensive CI:** a PR touching only `.github/workflows/**` + `docs/**` (no dbt models, no `site/**`) has `data-build` + `ui-checks` SKIP — only `validate` + `test` + gates run. `.claude/**`-only PRs trigger NO checks (artifact-only). Don't wait for data-build on those.

**Sibling-PR rebase recipe** (when a sibling merges first, the `.claude/task/*` scratch files collide): see memory `feedback_sibling_pr_rebase_rebind.md` — incl. the `reset --soft` reversion trap (going straight to `git reset --soft main` stages a REVERSION of the sibling's non-scratch changes; `git checkout main -- <those files>` to drop it). Force-push with `--force-with-lease`.

**Plain-language communication:** Do NOT ask the CPO cryptic/jargon questions or use AskUserQuestion with jargon labels. Explain what a thing DOES in plain words first, lead with a decision frame + a bolded recommendation.

---

### #500 metric-layer — STATUS (COMPLETE)

| Phase | PR(s) | Status |
|-------|-------|--------|
| PR1–PR-c + rename sweep | #574 / #577 / #579 / #580 | MERGED |
| PR-d steps 1–5 (WC cleanup → SSoT migration → labels → corners → drop `_season`) | #582–#585 + #587 | MERGED |
| PR-d step 6 — teardown cand. 1 + 4 | #590 | MERGED |
| PR-d step 6 — cand. 3 (team benchmark macro) | #593 | **DONE — whole macro removed via COMPOSE (better than the original "collapse the pairs")** |
| PR-d step 6 — cand. 5 (catalogue description enrichment) | — | OPEN (low priority; domain + CPO) |
| Trigger-block-rot follow-up | task_44698a18 | OPEN (PROTECTED path; CPO scopes) |

The metric layer is **one entity-first naming scheme + one definition SSoT (`metric_catalogue.csv`)**.

---

### NEXT candidates (CPO directs; none auto-granted)
- **task_44698a18 — trigger-block rot:** `pages-match-preview.yml`'s `on.push.paths` still lists a dead `scripts/build_metric_glossary_json.py` path + stale flat mart paths (lines ~18–23; marts moved to `5_marts/{domestic_league,shared}/`) + the now-orphaned `domestic_league_codes_in_clause.sql`. PROTECTED file → needs `protected_override` + cto-reviewer; CPO scopes.
- **#500 PR-d cand. 5** — enrich `metric_catalogue.csv` descriptions (provider-semantics nuance). Domain + CPO; lowest priority.
- **Player benchmark eligibility → seed** — deferred to player-benchmark ship time (see locked decisions above).
- **TEAM deserved-vs-actual REDESIGN** — a DESIGN discussion (below), not a build.
- **PROGRAMS** — a tranche of #545 (coverage) / #546 (data-quality) / #547 (cost) (below).
- **Carryovers (open):** #484 (player NT/tournament context window); #510 (retire leftover team `dribbles_success_pct`); team season-rollup → mapping spine (pre-season teams appear); #483 (qualifying-type cumulative window, GAP-18); display-contract amendment (appearance/playing-time block into `metrics_display.md`); Pilot PR2 slugs (BLOCKED on blinded §10 rulings E2/E3); opponent-context v1.x; Coach + career CONSUMPTION marts (DEFERRED, #391 paused).

### TEAM deserved-vs-actual REDESIGN (design discussion — do NOT build yet; TEAM only)
The flagship "how you PLAY vs what you GET" read. The prior crude implementation (`performance_vs_results_gap = shot_share − points_capture`) was REMOVED in #563 (uncatalogued + non-commensurable shares). Framing settled: the real failure was **comparability** → compare deserved + actual in a **common space**. **Lean (NOT decided): percentile-space gap via the benchmark engine.** Alternative: a non-xG deserved-goals/points composite. **Explicitly NO xG.** RESERVED: the comparability METHOD, the "deserved" input set, the "actual" set. Process: catalogue-first (define metric_catalogue rows with football-analytics + CPO approval BEFORE building).

### PROGRAMS (enablers — pull in deliberately; never eclipse product)
- **#545 coverage** (`stream:coverage`): onboard ~146 missing domestic leagues by tranche. API-cheap; DQ-at-scale is the real cost. CPO picks the first tranche. `provider_league_id` discovery is search-first.
- **#546 data-quality** (`stream:data-quality`): CI integrity suite + scheduled DQ sweep + triage rule. NEXT: generalise the detector; #550 automated-triage design (SCOPE = §10 awaiting CPO).
- **#547 cost** (`stream:platform`): size BQ build-bytes/storage before expansion scales.

---

### The governance machinery (G1–G4 LIVE)
- **Contract first:** every unit writes `.claude/task/contract.md` (objective, scope_paths, decisions, done_when) on a CLEAN tree BEFORE code. `task_contract_gate.py` denies edits outside scope_paths / to PROTECTED paths (`.claude/hooks|agents|commands/`, `.github/workflows/`, `.claude/settings.json`, `.claude/review_routing.json`, `.mcp.json`, `.cursor/mcp.json`) without `protected_override`.
- **Impact-map gate:** denies the first edit on the structural surface (`ingestion/**`, `dbt_project/models/**`, `scripts/export_*.py`, `site*/`) until the contract carries a non-placeholder `impact_map` (evidence, not assertion).
- **4-step review cycle** (Code Lock → cold Blinding → Cross-Examination → SHA-256 Lock) in `review.md`. Routing via `.claude/review_routing.json`: scope-auditor always; `dbt_project/**` → analytics-engineer; `scripts/export_*.py` → +cto; hooks/CI/`scripts/**`/`tests/**` → cto; ingestion/registry → data-engineer; wireframes + i18n → bi-analyst; `metric_catalogue.csv` → +football-analytics. PASS needs ≥2 named risks; default FAIL. Compute the hash with `python .claude/hooks/git_discipline.py --staged-hash`.
- **Commit gate** (`git_discipline.py`): staged SHA-256 must equal review.md `diff_sha256`; required reviewers PASS, no FAIL, every ESCALATE has a CPO ANSWER. ONE substantive commit per PR; `git commit` must be the SOLE command. Post-commit hook auto-pushes + opens the PR.
- **CI backstop** `scripts/check_task_artifacts.py --base origin/main` re-binds review.md to the PR diff.
- **Reviewer-driven scope amendment:** when a FAIL fix needs a file outside scope → stash code changes, amend contract.md on a clean tree, unstash, fix, re-review.

### Form-window model vocabulary (CURRENT names)
- **W1 momentum:** `int_team_momentum__metrics` → `mart_team_momentum` (+ `mart_team_momentum_window`). Player: `int_player_momentum__metrics` → `mart_player_momentum`. window_type: `last_5` / `tournament_to_date` / `qualifiers`.
- **W2 season record:** `int_team_season_record` → `mart_team_season_record`; `int_player_season_record` → `mart_player_season_record`. Player full-season agg = `int_player_season__metrics`.
- **Benchmarks:** `int_team_competition_benchmark_metrics_long` (NEW #593 — shared per-team long form) → `int_team_competition_benchmarks` (distribution) + `mart_team_competition_benchmarks` (per-team rank). Player: `int_player_season_position__metrics` → `int_player_competition_benchmarks` → `mart_player_competition_benchmarks` (still uses the `player_benchmark_metrics` macro — KEPT by ruling). Per-fixture: `mart_team_fixture_stats` / `mart_player_fixture_stats`. Shared leg builders = the `int_legs__*` family.

### Parked state (do not touch until directed)
- Team **SoT-difference** metric build STASHED (`git stash list` → "sot-difference WIP (paused for #500)"). Design settled (Camp 2, `sot_difference` = SoT for − against; TEAM only). Re-add when directed (#500 is done).
- v2 blueprint drill-down — under #391 (PAUSED). Pilot PR2 slug rulings E2/E3 — BLINDED, do NOT pre-decide.
- Backfill Phase 2a: registry depths MERGED (#524) but deep ingest STOPPED partway → RESUME for leagues not yet at depth. ~10x cheaper with `history_seasons` + `full`-profile scoped run.

### PENDING CPO ACTIONS (outside the tree)
1. **Set `PROJECT_AUTOMATION_TOKEN`** to fine-grained least-privilege scope (from #413).
2. **Remove now-unused secrets** `CURSOR_EXECUTOR_BRIDGE_URL` + `CURSOR_EXECUTOR_BRIDGE_TOKEN` (from #458).

### Key specs to read before building
- `docs/content_architecture.md` — blocks/tabs/navigation, entity types, block↔mart map.
- `docs/metric_layer.md` — the metric-layer map (seed is SSoT; display → `metrics_display.md`; windows → `metrics_context_model.md`).
- `docs/metrics_context_model.md` §8 — player performance surface.
- `dbt_project/docs/layering.md` — layer contract + exhaustive mart inventory.
- `dbt_project/docs/engineering_standards.md` §1.3 — the macro guidance (calibrated default, not a rulebook).

### Do NOT
- **No blueprint/feature work while #391 is PAUSED** unless the CPO directs it.
- **Never decide CPO-class questions** (§10); escalate in PLAIN language (§11).
- **Never mechanically remove a macro** — judge per §1.3; the player benchmark macro is KEPT by ruling.
- **`pages-match-preview.yml` is PROTECTED** — the trigger-rot cleanup (task_44698a18) needs `protected_override` + CPO scope approval.
- Do not compute/derive facts in the frontend/export — select/group/rename only (layering.md §Consumption).
- **Do not change shipped numbers** without a directed PR + before/after deltas + reviewer sign-off. (For dbt changes you can't run locally, "deltas" = equivalence-by-construction + CI data-build + the benchmark DQ tests.)
- Branch from main; never commit to main. **Never merge a PR — the CPO merges.**
- **Bash only** for all commands (git, bq, gh, python). Never PowerShell.
- **dbt CLI is broken locally AND the dbt MCP may not connect** — there may be NO local dbt validation; rely on the blinded analytics-engineer review + CI (`data-build` for data tests + SQLFluff).
