# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: **2026-06-28** — **[PR #596](https://github.com/ramialfahham/football-data-pipeline/pull/596) MERGED: metric_catalogue formula FORMALIZATION.** Every metric now carries a structured, resolvable formula — `base_relation` + clean `numerator_expr` / `denominator_expr` over the `int_legs__*` building-block columns (67/71 rows; 4 deferred). **A CPO RULING was set this session and must NOT be relitigated: a metric's formula is its fixed mathematical definition; data availability decides only whether a model can APPLY it (compute vs null) and is NEVER encoded in the formula.** main is GREEN. **There is NO locked next task — the CPO directs from the NEXT candidates below.**_

main carries the full #500 metric layer + the macro-cleanup thread + **#596** (formula formalization). **CPO merges, never self-merge — standing rule.** **Website #391 PAUSED; the live MVP must NOT break — standing CPO rule.** **The 5-step protocol is LIVE:** Explore → Plan → **Confirm** → Implement → Verify; for any file-touching task ENTER PLAN MODE at the Plan step and WAIT for the CPO's ExitPlanMode approval (= Confirm) before editing.

### FIRST STEPS (cold chat — do in order)
1. `git checkout main && git pull`. **main is GREEN at #596.** Then **close stale PR #595** (the pre-session 2026-06-28 EOD handover, superseded by this one) if still open.
2. Read this file top-to-bottom before touching anything.
3. **No locked next task.** Present the NEXT candidates (below) to the CPO in plain language with a brief recommendation, then WAIT for the pick. Do NOT pre-decide any §10 question.
4. **Bash only; never PowerShell.** For any file-touching task: write `.claude/task/contract.md` on a CLEAN tree BEFORE touching any file (impact-map gate for `dbt_project/models/**` + `scripts/export_*.py` + `ingestion/**` + `site*/`); use **PLAN MODE** for the plan-back.

---

### ⭐ THIS SESSION (2026-06-28) — the arc

Started on the **TEAM deserved-vs-actual** thread; it cascaded into formalizing the whole metric layer.

1. **SoT deserved-vs-actual — VALIDATED, design settled, NOT built.** Ran a full correlation sweep of every team metric vs final league rank (149 league-seasons / ~3,500 team-seasons, Spearman): **`sot_difference_per_match` (SoT for − against) = +0.70, statistically tied with `goals_per_match` (+0.70)** — the best *process* (deserved) predictor. Defensive action-counts are noise (tackles −0.05 … blocks −0.32). **Design settled (CPO-locked in this session's design discussion; recorded in memory [[project-team-metric-rank-correlation-sweep]] — NOT yet in any build contract):** method = **rank-space gap**; deserved = rank teams by `sot_difference`; actual = `league_rank`; **gap = actual_rank − deserved_rank**. Catalogue-first (define + approve the metric rows before building). See memory [[project-team-metric-rank-correlation-sweep]]. `sot_difference` itself is the stash `feat/team-sot-difference-metrics`. **NOT built** — the formalization below became the prerequisite foundation.
2. **Catalogue-coverage gate (#530) was explored, then RESHAPED.** Sequence of CPO decisions: declarative schema.yml tags → audit found calc spread across ~11 models → momentum/record mart-calc is a *justified* placement (no refactor) → CPO then observed the catalogue lacked the "how it's calculated" → pivoted to **formalizing the formula**, which **supersedes the labeling gate**.
3. **#596 — formula formalization (MERGED).** See below.

### #596 — what shipped (metric_catalogue formula formalization)
- Added `base_relation` + replaced prose `numerator`/`denominator` with **`numerator_expr` / `denominator_expr`** = window-free aggregates over the **`int_legs__*`** per-(entity, fixture) building blocks:
  - team scoreline/team-stat → `int_legs__team_match`; team player-derived (tackles/duels/key_passes) → `int_legs__team_from_players`; player → `int_legs__player_match`.
- Patterns: per-match rate = `sum(x) / count(*)`; ratio = `sum(a) / sum(b)`; count = `sum(x)`; per-90 = `sum(x) * 90 / sum(minutes_played)`; points = `sum(case result when 'W' then 3 when 'D' then 1 else 0 end)`.
- **67/71 formalized; all resolve. 4 blank-deferred** (CPO follow-ups): the 2 entity-dual `team and player` rows (`finishing_efficiency`, `duels_won_pct`) and player `goals_penalty` / `goals_open_play`.
- `numerator`/`denominator` were **documentation-only** (no consumer) → additive metadata, **no model SQL, no shipped-number change**.

### ⚠️ THE RULING — do NOT relitigate ([[feedback-metric-formula-vs-availability]])
A metric's **formula is its fixed mathematical definition**. Data availability (missing stats) decides only whether a model can **APPLY** it (compute vs null) — it is **NEVER** in the formula. So per-match denominators are **`count(*)`** (number of matches), NOT coverage counts (`games_with_team_stats`); and **no expression carries `coalesce` / `countif` / null-gates**. The models' coverage handling is *application*, not the formula. (This came after I wrongly bent `save_ratio` toward the model's coverage path chasing reviewer findings — reverted. The reviewers' "count(*) infidelity" findings describe model availability handling, not the formula.) **Authority:** the CPO stated this in chat this session ("the formula doesn't depend on availability of data; availability tells us whether we can apply it"); it is recorded as a CPO RULING in the **MERGED #596 contract `decisions_taken`**, in the seed schema docs, and in memory [[feedback-metric-formula-vs-availability]]. Cite those — it is settled, not a fresh assertion.

---

### NEXT candidates (CPO directs; none auto-granted)
- **SoT deserved-vs-actual BUILD** — now unblocked by the formalized catalogue. **Catalogue-first: the metric names + rows need football-analytics + CPO sign-off BEFORE building** — candidate names `sot_difference` (the CPO's own named metric / the stash) + `sot_against` (a proposed companion), then the rank-space gap. The flagship product read; the *design method* is CPO-locked (above), the *catalogue rows* are not yet approved.
- **#530 follow-ups from #596** (review-flagged): **(a)** PR2 — the **automated resolvability check** (every `*_expr` column ∈ `base_relation`; reviewers said key it on `base_relation` + (metric_id, entity), and handle dialect tokens `cast`/`round` + the `count(*)`-domain difference between legs); **(b)** **split the 2 entity-dual rows** per entity; **(c)** add the event-derived **`goals_penalty` to `int_legs__player_match`** then fill the 2 deferred player rows; **(d)** later — **model-conformance** (does each model compute the catalogue formula, modulo availability).
- **PROGRAMS** (enablers; never eclipse product): #545 coverage tranche · #546 data-quality suite · #547 cost sizing.
- **Carryovers (open):** #484 (player NT/tournament window); #510 (retire leftover team `dribbles_success_pct`); team season-rollup → mapping spine; #483 (qualifying-type cumulative window, GAP-18); display-contract amendment (appearance/playing-time block); Pilot PR2 slugs (BLOCKED on blinded §10 rulings E2/E3); Coach + career CONSUMPTION marts (DEFERRED, #391 paused).
- **Trigger-block-rot follow-up** (background task_44698a18) — dead `build_metric_glossary_json.py` + stale flat mart paths in `pages-match-preview.yml`; PROTECTED-path unit.

---

### The governance machinery (G1–G4 LIVE — unchanged)
- **Contract first:** every file-touching unit writes `.claude/task/contract.md` (objective, scope_paths, impact_map for structural surfaces, decisions, done_when) on a CLEAN tree BEFORE code. `task_contract_gate.py` denies edits outside scope_paths / to PROTECTED paths without `protected_override`. **Amending the contract requires a clean tree** — if code is staged, `git stash push -- <code paths>`, amend, `git stash pop`, re-stage (used twice this session).
- **Hashing:** `python .claude/hooks/git_discipline.py --staged-hash` prints the exact `diff_sha256` the commit gate checks (staged diff EXCLUDING `hash_exclude_paths`; covers code + contract.md).
- **4-step review cycle** (Code Lock → cold Blinding → Cross-Examination → SHA Lock) in `review.md`. Routing (`.claude/review_routing.json`): scope-auditor always; `dbt_project/**` → analytics-engineer; `dbt_project/seeds/metric_catalogue.csv` → +football-analytics-expert; `scripts/export_*.py`/hooks/CI → cto; ingestion/registry → data-engineer; wireframes+i18n → bi-analyst. PASS needs ≥2 named risks; default FAIL. **Re-run ALL required reviewers fresh whenever the hash changes.**
- **Commit gate** (`git_discipline.py`): staged SHA == review.md hash; required reviewers PASS, no FAIL, every ESCALATE has a CPO ANSWER. ONE substantive commit per PR; run `git commit` **alone** (no `cd`, no chaining). Post-commit hook auto-pushes + opens the PR.

### Session lessons (hard-won — read before touching these areas)
- **[[feedback-metric-formula-vs-availability]]** — the ruling above. The deepest lesson of the session: do NOT conflate the formula with whether you can compute it. I patched it wrong twice before the CPO corrected; don't repeat.
- **The review cycle earns its keep** — it caught real fidelity issues (save_ratio, per-90 doc, resolvability). When a reviewer FAILs, FIX the root cause; don't patch-to-pass. When findings rest on a premise the CPO has ruled on, cite the ruling in the contract + reviewer prompt so they evaluate against it.
- **dbt validation is CI-only** — dbt CLI broken locally; the dbt MCP did not connect this session. `ci-data-build` is the real gate for seeds/models. Offline: a scratchpad python resolvability/parse spot-check (read leg columns from the model SQL).
- **`bq` is not on Python's PATH** (it's a shell wrapper) — `subprocess.run(["bq", ...])` fails on Windows. Fetch columns via shell `bq` and pipe to python via stdin, or read columns from the model SQL.
- **Contract gate blocks Bash writes outside scope_paths** (e.g. `> /tmp/...`) once a contract is active — keep helper scripts in the scratchpad (Write tool, outside the repo) and pipe via stdin (no `>` redirects to non-scope paths).

### Standing rules / Do NOT
- **No locked next task — present candidates, get the CPO's pick, do NOT pre-decide §10** (product/UX, metrics, naming, NEW mechanisms, rule extensions). Escalate in PLAIN language.
- **No blueprint/feature work while #391 is PAUSED** unless the CPO directs it. Live MVP must not break.
- Do not compute/derive facts in the frontend/export — select/group/rename only.
- Branch from main; never commit to main. **Never merge a PR — the CPO merges.**
- **Bash only** for all commands. **dbt CLI broken locally** — rely on CI + the blinded reviewers.

### Key specs to read before building
- `dbt_project/seeds/metric_catalogue.csv` (+ its `schema.yml` entry) — the metric SSoT, now with formalized formulas.
- `docs/metric_layer.md` · `docs/metrics_context_model.md` §8 (player performance surface) · `dbt_project/docs/layering.md` (layer contract + mart inventory).
- Memory: [[feedback-metric-formula-vs-availability]], [[feedback-metric-catalogue-governance]], [[feedback-metric-calc-layer-placement]], [[project-team-metric-rank-correlation-sweep]], [[project-semantic-layer-ai-ready]].
