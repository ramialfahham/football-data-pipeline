# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: **2026-06-29** — **[PR #600](https://github.com/ramialfahham/football-data-pipeline/pull/600) MERGED: metric_catalogue integrity guards** (meaning completeness + #530 PR2 resolvability). main is GREEN at **bc94b61** (data-build passed). This session shipped THREE PRs: **#598** (TEAM deserved-vs-actual / SoT rank-space gap), **#599** (handover refresh), **#600** (integrity guards). **There is NO locked next task — the CPO directs from the NEXT candidates below.**_

main carries the full #500 metric layer + #596 (formula formalization) + #598 (deserved-vs-actual) + **#600** (integrity guards). **CPO merges, never self-merge — standing rule.** **Website #391 PAUSED; the live MVP must NOT break — standing CPO rule.** **The 5-step protocol is LIVE:** Explore → Plan → **Confirm** → Implement → Verify; for any file-touching task ENTER PLAN MODE at the Plan step and WAIT for the CPO's ExitPlanMode approval (= Confirm) before editing.

### FIRST STEPS (cold chat — do in order)
1. `git checkout main && git pull`. **main is GREEN at #600 (bc94b61).** Confirm tree clean.
2. Read this file top-to-bottom before touching anything.
3. **No locked next task.** Present the NEXT candidates (below) to the CPO in plain language with a brief recommendation, then WAIT for the pick. Do NOT pre-decide any §10 question.
4. **Bash only; never PowerShell.** For any file-touching task: write `.claude/task/contract.md` on a CLEAN tree BEFORE touching any file (impact-map gate for `dbt_project/models/**` + `scripts/export_*.py` + `ingestion/**` + `site*/`); use **PLAN MODE** for the plan-back.

---

### ⭐ THIS SESSION (2026-06-29) — three PRs

1. **#598 — TEAM deserved-vs-actual read (SoT rank-space gap), MERGED.** The flagship process read. 4 catalogue rows (`sot_difference`, `shots_on_goal_against_per_match` per-match over `int_legs__team_match`; `deserved_rank`, `sot_rank_gap` rank-derived/blank-expr). New model `int_team_season__deserved_vs_actual` (composes the gated `sot_difference` + standings rank; `deserved_rank` = rank by sot_difference within league-season; `sot_rank_gap = actual_rank − deserved_rank`, positive = under-performing) under a **full-table coverage gate**. Intermediate-only; method CPO-locked; TEAM only, no xG. See memory [[project-team-metric-rank-correlation-sweep]].
2. **#599 — handover refresh, MERGED.**
3. **#600 — metric_catalogue integrity guards, MERGED.** Two CI singular tests + filling the only 3 team meaning-gaps:
   - **`assert_team_metric_meaning_complete`** — every TEAM metric must carry `direction` + `interpretation`; PLAYER rows **exempt** (v1.x). `team and player` counts as team.
   - **`assert_metric_catalogue_expr_resolvable`** (#530 PR2) — every `numerator_expr`/`denominator_expr` column resolves against its `base_relation` (introspected via `adapter.get_columns_in_relation`); rank-derived (blank `base_relation`) rows skipped; SQL-token stoplist grounded in the actual expr vocabulary; a new formula function fails-forward.
   - **Filled the 3 team open-play atoms** (`goals_penalty`, `goals_own`, `goals_open_play`) = `direction=higher_better` (CPO: they are goals FOR the team — they help the result and often reflect pressure; `goals_own` is the for-version) + interpretation. `lower_is_better` unchanged; no `*_expr` change.

### ⚠️ Standing ruling — do NOT relitigate ([[feedback-metric-formula-vs-availability]])
A metric's **formula is its fixed mathematical definition**. Data availability decides only whether a model can **APPLY** it (compute vs null) — it is **NEVER** in the formula. Per-match denominator = **`count(*)`**; **no `coalesce`/`countif`/null-gate in any `*_expr`**. A `Null when…` clause in the catalogue **description prose** is allowed/expected (house style); only `*_expr` must stay pure.

---

### NEXT candidates (CPO directs; none auto-granted)
- **#530 remaining follow-ups** (the completeness + resolvability tranche is now DONE via #600):
  (a) **split the 2 entity-dual rows** (`finishing_efficiency`, `duels_won_pct`, entity `team and player`) into per-entity rows with explicit `base_relation`/`*_expr`;
  (b) add the event-derived **`goals_penalty` to `int_legs__player_match`**, then fill the 2 deferred player rows (`goals_penalty`, `goals_open_play`) — they currently have blank `base_relation`/`*_expr`;
  (c) **model-conformance** test — does each model actually COMPUTE the catalogue formula (modulo availability)? The deeper guard beyond resolvability.
- **Player-metric direction/interpretation classification** (v1.x deferral) — the completeness test is team-only; when the player benchmark matures, classify the ~28 blank player rows and widen the test. CPO call.
- **Deserved-vs-actual extensions (NOT granted):** a consumption mart when a frontend consumer exists (#391 paused); `rank()` tie semantics revisit; other windows (form panel could compute sot_difference too).
- **PROGRAMS** (enablers; never eclipse product): #545 coverage tranche · #546 data-quality suite · #547 cost sizing.
- **Carryovers (open):** #484 (player NT/tournament window); #510 (retire leftover team `dribbles_success_pct`); team season-rollup → mapping spine; #483 (qualifying-type cumulative window, GAP-18); display-contract amendment (appearance/playing-time block); Pilot PR2 slugs (BLOCKED on blinded §10 rulings E2/E3); Coach + career CONSUMPTION marts (DEFERRED, #391 paused).
- **Trigger-block-rot follow-up** (background task_44698a18) — dead `build_metric_glossary_json.py` + stale flat mart paths in `pages-match-preview.yml`; PROTECTED-path unit.

---

### The governance machinery (G1–G4 LIVE — unchanged)
- **Contract first:** every file-touching unit writes `.claude/task/contract.md` (objective, scope_paths, impact_map for structural surfaces, decisions, done_when) on a CLEAN tree BEFORE code. `task_contract_gate.py` denies edits outside scope_paths / to PROTECTED paths without `protected_override`. Amend only on a clean tree.
- **Hashing:** `python .claude/hooks/git_discipline.py --staged-hash` prints the `diff_sha256` the commit gate checks (staged diff vs HEAD, EXCLUDING `hash_exclude_paths`; covers code + contract.md). `review.md` + `review_input.patch` are hash-excluded.
- **4-step review cycle** (Code Lock → cold Blinding → Cross-Examination → SHA Lock) in `review.md`. Routing (`.claude/review_routing.json`): scope-auditor always; `dbt_project/**` → analytics-engineer; `dbt_project/seeds/metric_catalogue.csv` → +football-analytics-expert; `scripts/export_*.py`/hooks/CI → cto; ingestion/registry → data-engineer; wireframes+i18n → bi-analyst. PASS needs ≥2 named risks; default FAIL. **Re-run ALL required reviewers fresh whenever the hash changes.**
- **Commit gate** (`git_discipline.py`): staged SHA == review.md hash; required reviewers PASS, no FAIL, every ESCALATE has a CPO ANSWER. **ONE substantive commit per PR**; run `git commit` **alone** (no `cd`, no chaining; **`--amend` is NOT allowlisted** — only message/quiet/verbose/sign). Post-commit hook auto-pushes + opens the PR.

### Session lessons (hard-won)
- **dbt/SQLFluff validation is CI-only** (dbt CLI broken locally; SQLFluff uses the dbt templater; the dbt MCP didn't connect). `ci-data-build` is the real gate. Offline you CAN run: `python scripts/check_layer_contract.py`, scratchpad python CSV/resolvability spot-checks, and reading model SQL.
- **BigQuery rejects a FROM-less `WHERE`** — a singular test whose empty/pass-case fallback is `select … where 1 = 0` (no FROM) ERRORS at execution. `validate` (parse) and an offline python check BOTH miss it; only `data-build` catches it (it executes). Fix: give the fallback a FROM (`from {{ ref('metric_catalogue') }} where 1 = 0`). Note: `assert_no_uncatalogued_season_metric`'s equivalent else-branch never fires (its model always has rows), so it never exposed this. (#600 round-2.)
- **Collapsing a CI-fix to ONE commit:** `--amend` is gate-blocked → use `git reset --soft HEAD~1`, re-stage, recompute the hash **vs main** (the full diff), re-run reviewers on that full diff, write review.md, plain `git commit`, then `git push --force-with-lease origin <branch>:<branch>` (the post-commit auto-push fails non-ff first — that's expected). The commit-gate staged hash and the CI `base...HEAD` hash must equal the SAME review.md hash, which only holds with one commit.
- **The drift guard `assert_no_uncatalogued_season_metric`** checks every non-exempt/non-`_sum_season`/non-`_sk` OUTPUT column of `int_team_season__metrics` (and the player model) against the catalogue — when adding a metric there, catalogue it and keep raw/coverage helpers OUT of the final SELECT (reference inline only).

### Standing rules / Do NOT
- **No locked next task — present candidates, get the CPO's pick, do NOT pre-decide §10** (product/UX, metrics, naming, NEW mechanisms, rule extensions). Escalate in PLAIN language.
- **No blueprint/feature work while #391 is PAUSED** unless the CPO directs it. Live MVP must not break.
- Do not compute/derive facts in the frontend/export — select/group/rename only.
- Branch from main; never commit to main. **Never merge a PR — the CPO merges.**
- **Bash only** for all commands. **dbt CLI + SQLFluff broken locally** — rely on CI + the blinded reviewers.

### Key specs to read before building
- `dbt_project/seeds/metric_catalogue.csv` (+ its `schema.yml` entry) — the metric SSoT (formalized formulas; now guarded by `assert_team_metric_meaning_complete` + `assert_metric_catalogue_expr_resolvable`).
- `dbt_project/tests/assert_metric_catalogue_expr_resolvable.sql` — the resolvability guard (the pattern for any future catalogue-integrity test; note the FROM-ful empty fallback).
- `dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__deserved_vs_actual.sql` — the rank-space read.
- `docs/metric_layer.md` · `docs/metrics_context_model.md` §8 · `dbt_project/docs/layering.md`.
- Memory: [[feedback-metric-formula-vs-availability]], [[feedback-metric-catalogue-governance]], [[feedback-metric-calc-layer-placement]], [[project-team-metric-rank-correlation-sweep]], [[project-semantic-layer-ai-ready]].
