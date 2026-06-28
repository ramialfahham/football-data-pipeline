# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: **2026-06-29** — **[PR #598](https://github.com/ramialfahham/football-data-pipeline/pull/598) MERGED: the TEAM deserved-vs-actual read (SoT rank-space gap).** The flagship product read shipped, catalogue-first, on the #596 formula-formalization foundation. main is GREEN (data-build passed, 3m45s). **There is NO locked next task — the CPO directs from the NEXT candidates below.**_

main carries the full #500 metric layer + #596 (formula formalization) + **#598** (deserved-vs-actual). **CPO merges, never self-merge — standing rule.** **Website #391 PAUSED; the live MVP must NOT break — standing CPO rule.** **The 5-step protocol is LIVE:** Explore → Plan → **Confirm** → Implement → Verify; for any file-touching task ENTER PLAN MODE at the Plan step and WAIT for the CPO's ExitPlanMode approval (= Confirm) before editing.

### FIRST STEPS (cold chat — do in order)
1. `git checkout main && git pull`. **main is GREEN at #598 (cc1bfd0).** Confirm tree clean.
2. Read this file top-to-bottom before touching anything.
3. **No locked next task.** Present the NEXT candidates (below) to the CPO in plain language with a brief recommendation, then WAIT for the pick. Do NOT pre-decide any §10 question.
4. **Bash only; never PowerShell.** For any file-touching task: write `.claude/task/contract.md` on a CLEAN tree BEFORE touching any file (impact-map gate for `dbt_project/models/**` + `scripts/export_*.py` + `ingestion/**` + `site*/`); use **PLAN MODE** for the plan-back.

---

### ⭐ LAST SESSION (2026-06-28/29) — TEAM deserved-vs-actual BUILT & MERGED (#598)

The flagship "which teams over/under-perform their process" read. Catalogue-first.

**What shipped (#598, MERGED, data-build GREEN):**
- **4 metric_catalogue rows** (formalized structure): `sot_difference` + `shots_on_goal_against_per_match` (per-match aggregates over `int_legs__team_match`; `sum(...)`/`count(*)`); `deserved_rank` + `sot_rank_gap` (rank-derived, **blank-expr** like `league_rank`, derivation in the description). All four carry a `Null when…` clause (catalogue house style).
- **`int_team_season_record`** (shared) — additive rollup of `opponent_shots_on_goal` + a new opponent-SoT coverage counter `games_with_opp_sot_stats`.
- **`int_team_season__metrics`** (domestic_league) — two gated metrics added: `sot_difference`, `shots_on_goal_against_per_match` (availability gate in the model CASE, NOT the formula).
- **`int_team_season__deserved_vs_actual`** (NEW, domestic_league) — composes the gated `sot_difference` + `int_team_season__standings_primary.standing_rank` (= actual_rank). `deserved_rank = rank() by sot_difference within league-season`; `sot_rank_gap = actual_rank − deserved_rank` (**positive = under-performing**). **Full-table coverage gate:** a league-season is rankable only if EVERY team has full SoT coverage AND a league rank, else deserved_rank/sot_rank_gap are NULL for that whole league-season. No hardcoded competition filter — the standings join generically restricts to competitions with a league table.
- **Tests** (`int_team_season.yml`): grain unique-at-source on `int_team_season__metrics.team_season_sk`; the `sot_rank_gap` null/arithmetic invariant; gate invariants; companion non-negativity.

**Design (CPO-LOCKED — do not reopen):** deserved signal = `sot_difference` (Spearman +0.70 vs league rank, the best non-outcome predictor); method = rank-space gap; **TEAM only, no xG**; gap display = **neutral** ("a narrative, not good or bad"); scope = **intermediate-only** (no mart/i18n/frontend, #391 paused); i18n labels deferred. See memory [[project-team-metric-rank-correlation-sweep]].

**Review:** blinded cycle PASS over 4 rounds — analytics-engineer FAIL (2 test gaps) fixed; football-analytics FAIL x2 (nullability clauses on all 4 rows) fixed, CPO-approved. The cycle earned its keep again.

### ⚠️ Standing ruling — do NOT relitigate ([[feedback-metric-formula-vs-availability]])
A metric's **formula is its fixed mathematical definition**. Data availability decides only whether a model can **APPLY** it (compute vs null) — it is **NEVER** in the formula. Per-match denominator = **`count(*)`**; **no `coalesce`/`countif`/null-gate in any `*_expr`**. A `Null when…` clause in the catalogue **description prose** is allowed and expected (house style); only the `*_expr` must stay pure. Recorded in the MERGED #596 + #598 contracts + the seed schema docs.

---

### NEXT candidates (CPO directs; none auto-granted)
- **Governance: metric-meaning completeness test** (CPO ruled 2026-06-28 "queue as its own PR") — a test that every **displayed** metric has `direction` + `interpretation` (scoped to displayed metrics: player v1.x rows + team component atoms like `goals_penalty`/`goals_own`/`goals_open_play` are legitimately exempt — needs a "displayed metric" definition). **Pair with #530 PR2** — the automated **resolvability check** (every `*_expr` column ∈ `base_relation`; key on base_relation + (metric_id, entity); handle dialect tokens `cast`/`round` + the `count(*)` domain). Both are seed-integrity tests; one governance PR.
- **#530 other follow-ups:** split the 2 entity-dual rows (`finishing_efficiency`, `duels_won_pct`) per entity; add event-derived `goals_penalty` to `int_legs__player_match` then fill the 2 deferred player rows (`goals_penalty`, `goals_open_play`); later — model-conformance (does each model compute the catalogue formula, modulo availability).
- **Deserved-vs-actual extensions (NOT granted):** a consumption mart when a frontend consumer exists (#391 paused — none yet); `rank()` tie semantics revisit (currently rank() per approved plan — ties share a rank, next skips); other windows (the form panel could compute sot_difference too).
- **PROGRAMS** (enablers; never eclipse product): #545 coverage tranche · #546 data-quality suite · #547 cost sizing.
- **Carryovers (open):** #484 (player NT/tournament window); #510 (retire leftover team `dribbles_success_pct`); team season-rollup → mapping spine; #483 (qualifying-type cumulative window, GAP-18); display-contract amendment (appearance/playing-time block); Pilot PR2 slugs (BLOCKED on blinded §10 rulings E2/E3); Coach + career CONSUMPTION marts (DEFERRED, #391 paused).
- **Trigger-block-rot follow-up** (background task_44698a18) — dead `build_metric_glossary_json.py` + stale flat mart paths in `pages-match-preview.yml`; PROTECTED-path unit.

---

### The governance machinery (G1–G4 LIVE — unchanged)
- **Contract first:** every file-touching unit writes `.claude/task/contract.md` (objective, scope_paths, impact_map for structural surfaces, decisions, done_when) on a CLEAN tree BEFORE code. `task_contract_gate.py` denies edits outside scope_paths / to PROTECTED paths without `protected_override`. Amending the contract requires a clean tree (stash code, amend, pop, re-stage).
- **Hashing:** `python .claude/hooks/git_discipline.py --staged-hash` prints the `diff_sha256` the commit gate checks (staged diff EXCLUDING `hash_exclude_paths`; covers code + contract.md). `review.md` + `review_input.patch` are hash-excluded, so writing them does not shift the hash.
- **4-step review cycle** (Code Lock → cold Blinding → Cross-Examination → SHA Lock) in `review.md`. Routing (`.claude/review_routing.json`): scope-auditor always; `dbt_project/**` → analytics-engineer; `dbt_project/seeds/metric_catalogue.csv` → +football-analytics-expert; `scripts/export_*.py`/hooks/CI → cto; ingestion/registry → data-engineer; wireframes+i18n → bi-analyst. PASS needs ≥2 named risks; default FAIL. **Re-run ALL required reviewers fresh whenever the hash changes.**
- **Commit gate** (`git_discipline.py`): staged SHA == review.md hash; required reviewers PASS, no FAIL, every ESCALATE has a CPO ANSWER. ONE substantive commit per PR; run `git commit` **alone** (no `cd`, no chaining). Post-commit hook auto-pushes + opens the PR.

### Session lessons (hard-won)
- **dbt validation is CI-only** — dbt CLI broken locally (`No module named 'dbt.adapters.factory'`); SQLFluff uses the dbt templater so **SQL lint is also CI-only**; the dbt MCP did not connect. `ci-data-build` is the real gate for seeds/models. Offline you CAN run: `python scripts/check_layer_contract.py`, a scratchpad python CSV/resolvability spot-check, and reading model SQL to confirm additive-only.
- **The `assert_no_uncatalogued_season_metric` drift guard** checks every non-exempt/non-`_sum_season`/non-`_sk` OUTPUT column of `int_team_season__metrics` (and the player model) against the catalogue. When adding a metric there: catalogue it, and keep raw/coverage helper columns OUT of the final SELECT (reference them inline only) — else the guard fails.
- **The review cycle keeps finding "one more place"** for a convention (nullability clauses spread across rounds). When a finding rests on a real house-style convention the CPO has endorsed, apply it **consistently to all affected rows at once** to converge, rather than one row per round.

### Standing rules / Do NOT
- **No locked next task — present candidates, get the CPO's pick, do NOT pre-decide §10** (product/UX, metrics, naming, NEW mechanisms, rule extensions). Escalate in PLAIN language.
- **No blueprint/feature work while #391 is PAUSED** unless the CPO directs it. Live MVP must not break.
- Do not compute/derive facts in the frontend/export — select/group/rename only.
- Branch from main; never commit to main. **Never merge a PR — the CPO merges.**
- **Bash only** for all commands. **dbt CLI + SQLFluff broken locally** — rely on CI + the blinded reviewers.

### Key specs to read before building
- `dbt_project/seeds/metric_catalogue.csv` (+ its `schema.yml` entry) — the metric SSoT, formalized formulas; now incl. the 4 deserved-vs-actual rows.
- `dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__deserved_vs_actual.sql` — the rank-space read (the pattern for any future deserved-vs-actual extension).
- `docs/metric_layer.md` · `docs/metrics_context_model.md` §8 · `dbt_project/docs/layering.md` (layer contract + mart inventory).
- Memory: [[feedback-metric-formula-vs-availability]], [[feedback-metric-catalogue-governance]], [[feedback-metric-calc-layer-placement]], [[project-team-metric-rank-correlation-sweep]], [[project-semantic-layer-ai-ready]].
