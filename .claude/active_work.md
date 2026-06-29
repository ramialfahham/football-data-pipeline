# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: **2026-06-29** — main GREEN at **6dd1f89** (#530(a) split merged via #604). The recent arc shipped #596 (formalization) → #598 (TEAM deserved-vs-actual) → #600 (integrity guards) → **#530(a)** (split the 2 entity-dual catalogue rows per entity), all MERGED. **NEXT (CPO-agreed): the #391 conversation** — a DISCUSSION (not a build) of whether to un-pause the website so the metric layer (deserved-vs-actual, benchmarks, leaderboards, profiles) finally gets a user-facing consumer. Detailed below._

main carries the full #500 metric layer + #596 (formula formalization) + #598 (deserved-vs-actual) + #600 (integrity guards) + **#530(a)** (entity-dual rows split per entity). **CPO merges, never self-merge — standing rule.** **Website #391 PAUSED; the live MVP must NOT break — standing CPO rule.** **The 5-step protocol is LIVE:** Explore → Plan → **Confirm** → Implement → Verify; for any file-touching task ENTER PLAN MODE at the Plan step and WAIT for the CPO's ExitPlanMode approval (= Confirm) before editing.

### FIRST STEPS (cold chat — do in order)
1. `git checkout main && git pull`. **main is GREEN at 6dd1f89.** Confirm tree clean.
2. Read this file top-to-bottom before touching anything.
3. **NEXT = the #391 conversation** (see the block below) — a DISCUSSION, not a build: present state + options on whether to un-pause the website so the metric layer gets a user-facing consumer. Do NOT start product work without the CPO's explicit un-pause. No locked build task; for any new build, present candidates and get the CPO's pick (§10).
4. **Bash only; never PowerShell.** For any file-touching task: write `.claude/task/contract.md` on a CLEAN tree BEFORE touching any file (impact-map gate for `dbt_project/models/**` + `scripts/export_*.py` + `ingestion/**` + `site*/`); use **PLAN MODE** for the plan-back.

---

### ⭐ DONE — #530(a): split the 2 entity-dual catalogue rows (MERGED #604)
`finishing_efficiency` and `duels_won_pct` were split from entity `team and player` into per-entity rows:
- `duels_won_pct` → team (`int_legs__team_from_players`) + player (`int_legs__player_match`), both `sum(duels_won)/sum(duels_total)`. Fully resolvable.
- `finishing_efficiency` → team (`int_legs__team_match`, `sum(goals_for - goals_penalty - goals_own)/sum(shots_on_goal)`) + **player DEFERRED** (blank base/exprs) to **#530(b)** — pending the event-derived `goals_penalty` atom in `int_legs__player_match` (player formula will be `sum(goals_total - goals_penalty)/sum(shots_on)`).
`assert_metric_catalogue_expr_resolvable` now covers the 3 resolvable rows; the deferred player row stays skip-listed.
**Hard-won lesson (logged [[feedback-premature-escalation]]):** `finishing_efficiency` is locked to **[0,1]** by the deployed model (`int_team_season__metrics.sql:156-158`), a dbt test (`int_player_season_position.yml:21`) and **CPO "Option A"** — the catalogue prose matches that. A blinded reviewer cited the wireframe's stale "never capped" line (`docs/wireframes/metrics_display.md:107`); I escalated the doc-vs-doc conflict WITHOUT checking the code first → wasted a fix-now/revert loop. **When two specs disagree, the deployed code + tests + last CPO ruling are the tiebreaker — read them before escalating.** (The stale wireframe line is a separate reconciliation, not yet done.)

### ⭐ NEXT — the #391 conversation (CPO-agreed)
The metric layer is solid (formalization + deserved-vs-actual + integrity guards + the entity split) but has **no user-facing surface** — deserved-vs-actual is intermediate-only, and benchmarks/leaderboards/profiles are marts with no frontend, because the website **#391 is PAUSED**. The CPO-agreed next step is the conversation about **whether to un-pause #391** so the work gets a consumer. This is a **DISCUSSION, not a build** — present the state + options; do NOT start product work without the CPO's explicit un-pause (standing rule).

---

### ⭐ RECENT PRs

- **#604 (latest) — #530(a) entity-dual catalogue split, MERGED.** The 2 `team and player` rows (`finishing_efficiency`, `duels_won_pct`) split per entity with explicit base_relation + numerator_expr/denominator_expr; player `finishing_efficiency` deferred to #530(b). Catalogue-only. See the DONE block above + the [0,1]/Option A lesson.

Prior arc (2026-06-29):
1. **#598 — TEAM deserved-vs-actual read (SoT rank-space gap), MERGED.** The flagship process read. 4 catalogue rows (`sot_difference`, `shots_on_goal_against_per_match` per-match over `int_legs__team_match`; `deserved_rank`, `sot_rank_gap` rank-derived/blank-expr). New model `int_team_season__deserved_vs_actual` (composes the gated `sot_difference` + standings rank; `deserved_rank` = rank by sot_difference within league-season; `sot_rank_gap = actual_rank − deserved_rank`, positive = under-performing) under a **full-table coverage gate**. Intermediate-only; method CPO-locked; TEAM only, no xG. See memory [[project-team-metric-rank-correlation-sweep]].
2. **#599 — handover refresh, MERGED.**
3. **#600 — metric_catalogue integrity guards, MERGED.** Two CI singular tests + filling the only 3 team meaning-gaps:
   - **`assert_team_metric_meaning_complete`** — every TEAM metric must carry `direction` + `interpretation`; PLAYER rows **exempt** (v1.x). `team and player` counts as team.
   - **`assert_metric_catalogue_expr_resolvable`** (#530 PR2) — every `numerator_expr`/`denominator_expr` column resolves against its `base_relation` (introspected via `adapter.get_columns_in_relation`); rank-derived (blank `base_relation`) rows skipped; SQL-token stoplist grounded in the actual expr vocabulary; a new formula function fails-forward.
   - **Filled the 3 team open-play atoms** (`goals_penalty`, `goals_own`, `goals_open_play`) = `direction=higher_better` (CPO: they are goals FOR the team — they help the result and often reflect pressure; `goals_own` is the for-version) + interpretation. `lower_is_better` unchanged; no `*_expr` change.

### ⚠️ Standing ruling — do NOT relitigate ([[feedback-metric-formula-vs-availability]])
A metric's **formula is its fixed mathematical definition**. Data availability decides only whether a model can **APPLY** it (compute vs null) — it is **NEVER** in the formula. Per-match denominator = **`count(*)`**; **no `coalesce`/`countif`/null-gate in any `*_expr`**. A `Null when…` clause in the catalogue **description prose** is allowed/expected (house style); only `*_expr` must stay pure.

---

### NEXT candidates (after #530(a) + the #391 conversation — CPO directs; none auto-granted)
- **#530 remaining follow-ups** (completeness + resolvability DONE via #600; **(a) DONE via #604** — entity-dual rows split per entity):
  (b) add the event-derived **`goals_penalty` to `int_legs__player_match`**, then fill the **3 deferred player rows** (`finishing_efficiency`, `goals_penalty`, `goals_open_play`) — blank `base_relation`/`*_expr` today (the player `finishing_efficiency` row from (a) is now one of these). **This is the lead #530 follow-up.**
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
