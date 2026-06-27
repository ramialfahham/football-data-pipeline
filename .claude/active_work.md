# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: **2026-06-26 EOD** — **#500 PR-d (live-MVP → metric_catalogue SSoT) STEPS 1–5 ALL MERGED** (#582 + #583 + #584 + #585 + #587). The live match-preview and team-season MVP now reads entirely from `metric_catalogue.csv`; `metric_definitions.csv` is DELETED. **NEXT: step 6 — teardown (scope first, CPO directs; do NOT build until go).**_

main carries #582 + #583 + #584 + #585 + #587. **Website #391 PAUSED; the live MVP must NOT break — standing CPO rule.** Per-item CPO-directed; **CPO merges, never self-merge.** **The 5-step protocol is LIVE:** Explore → Plan → **Confirm** → Implement → Verify; for any file-touching task ENTER PLAN MODE at the Plan step and WAIT for the CPO's ExitPlanMode approval (= Confirm) before editing.

### FIRST STEPS (cold chat — do in order)
1. `git checkout main && git pull` (carries #582–#585 + #587). **Nothing pending-merge; main GREEN.**
2. Read this file top-to-bottom before touching anything.
3. **The NEXT unit is step 6 (teardown) — scope it first, present the candidate list to the CPO, wait for explicit go.** Do NOT begin building until the CPO approves.
4. **Bash only; never PowerShell.** For any file-touching task: write `.claude/task/contract.md` on a CLEAN tree BEFORE touching any file (the impact-map gate enforces it for `dbt_project/models/**` + `scripts/export_*.py` + `ingestion/**` + `site*/`) + use **PLAN MODE** for the plan-back.

---

### ⭐ THIS SESSION (2026-06-26) — #500 PR-d: live-MVP → metric_catalogue SSoT (steps 1–5)

| PR | Step | What changed |
|----|------|--------------|
| #582 | 1 — WC cleanup | Deleted 14 dead WC-pretournament metric rows from `metric_definitions.csv`; deleted matching i18n keys (3 langs) |
| #583 | 2 — SSoT migration | Deleted `metric_definitions.csv` entirely; created `site/match-preview/metric_bindings.csv` (thin wiring: live_id → catalogue_metric_id + home/away JSON column names + context); rewrote `export_metric_definitions_json.py` to compose catalogue + bindings; added `tests/test_metric_bindings.py` (byte-identity guard); removed seed block from `seeds/schema.yml` |
| #584 | 3 — label unification | Unified onto ONE label scheme (`metrics.<catalogue_id>.label`); rewrote `check_ui_i18n_metrics.py` to follow bindings → catalogue keys; updated `site/match-preview/index.html` (dropped `LEGACY_METRIC_LABEL_KEYS`); updated `site/team-season/index.html` (all 13 label refs); re-keyed all three i18n files (en/de/fi): `metrics.<windowed_id>` → `metrics.<official_id>` + deleted the `metric.*` block |
| #585 | 4 — corners rename | `corners_conceded_per_match` → `corners_against_per_match` end-to-end: catalogue id + label_i18n_key, i18n files (3 langs), bindings CSV, int_team_season__metrics.sql, mart_team_season_record.sql, team_benchmark_metrics.sql macro, schema YMLs, team-season page, wireframe. **Folded fix:** added `"team and player"` to entity `accepted_values` in `seeds/schema.yml` (pre-existing gap surfaced by CI) |
| #587 | 5 — drop `_season` suffix | Dropped `_season` from all **metric** columns (not `_sum_season` intermediates); int_team_season__metrics.sql, mart_team_season_record.sql, mart_team_season_insights.sql, mart_team_profile.sql, team_benchmark_metrics.sql macro, schema YMLs (int_team_season.yml / shared.yml / domestic_league.yml), DQ test (assert_mart_team_season_insights_metric_consistency.sql), drift guard (assert_no_uncatalogued_season_metric.sql comment), team-season page, wireframe 02_team_profile.md. **AL09 fix:** de-aliased `m.X as X` → `m.X` (19 rows in mart_team_season_record) + `col as col` → `col` (2 rows in int_team_season__metrics) |

#### The live metric chain post-migration

```
metric_catalogue.csv  (SSoT — format, lower_is_better, label_i18n_key, formula)
        +
site/match-preview/metric_bindings.csv  (wiring: live_id → catalogue_metric_id + home/away columns + context)
        ↓
scripts/export_metric_definitions_json.py  (composes both → site/match-preview/metric_definitions.json)
        ↓
site/match-preview/index.html  (reads def.label for i18n key; def.format / lower_is_better)
```

Team-season chain:
```
dbt_project/models/4_intermediate/…/int_team_season__metrics.sql
  (metric column names now = catalogue metric_ids, no _season suffix)
        ↓
mart_team_season_record / mart_team_season_insights / mart_team_profile
        ↓
scripts/export_team_season_json.py  (SELECT * → renamed columns flow through automatically)
        ↓
site/team-season/index.html  (row.<metric_id> — no _season suffix)
```

**Byte-identity guard:** `tests/test_metric_bindings.py::test_regenerated_json_matches_committed` — regenerates the JSON in a temp dir and asserts byte-equality with the committed file. Fails if bindings/catalogue drift without updating the JSON.

**Drift guard:** `dbt_project/tests/assert_no_uncatalogued_season_metric.sql` — catches any metric column in `int_team_season__metrics` or `int_player_season__metrics` that has no catalogue row. The `_season` strip is now a no-op (commented as defensive; #500 Stage 2 is done).

---

### Step 6 — teardown (NOT built; scope + CPO go first)

Present this candidate list to the CPO; do NOT pre-decide which to include:

1. **`pages-match-preview.yml:25` trigger** — still references `metric_definitions.csv` (now deleted). PROTECTED path; needs `protected_override` + cto-reviewer. Likely replace with `site/match-preview/metric_bindings.csv` as the trigger.
2. **Verify/retire `build_match_preview_site.{sh,ps1}` and `export_matchday_insights.ps1`** — likely KEEP (they assemble the whole Pages site); verify actual usage before touching.
3. **Benchmark macro pair simplification** — `team_benchmark_metrics.sql` now has `('X','X')` pairs after both renames; consider simplifying to single-element. Do NOT build until CPO-directed.
4. **Two stale glob refs** in `docs/content_architecture.md` and `docs/wireframes/99_gaps_register.md` (entity-first shorthand from the old naming).
5. **Seed description enrichment** — flagged in PR-c review as low-priority polish (provider-semantics nuances).

---

### Session lessons (hard-won — read before touching these areas)

**Local dbt validation gap:** `dbt CLI` is BROKEN locally (`No module named dbt.adapters.factory`). `mcp__dbt__parse` catches broken refs/Jinja/YAML but NOT data tests or SQL lint. **ci-data-build is the real gate** — every PR must pass CI before the CPO merges.

**SQLFluff AL09 — cannot run locally:** The `_season` rename turned `m.<metric>_season as <metric>` into `m.<metric> as <metric>` (self-alias). SQLFluff catches this in CI only. Fix: drop the redundant alias — `m.X as X` → `m.X`; `col as col` → `col`. Watch for this on any rename that produces a self-alias.

**entity accepted_values pre-existing gap:** `metric_catalogue.csv` legitimately has `"team and player"` on 2 rows (finishing_efficiency, duels_won_pct). The schema.yml `accepted_values` only had `["team","player"]` — a pre-existing gap exposed when #585 touched the catalogue. Fixed by adding `"team and player"` to the list.

**Force-push amendment dance (when ci-data-build fails mid-PR):**
1. Fix the file(s)
2. `git reset --soft HEAD~1` (unstage without losing changes)
3. Re-stage everything + `git commit` (single clean commit)
4. Re-run all reviewers (hash changed; all reviews must be fresh)
5. `git push --force-with-lease origin <branch>`

**"Mechanical" mis-framing:** Do NOT characterise a cross-layer rename as "mechanical" before tracing the full blast radius. Count files and patterns first; then name the scope accurately.

**Plain-language communication:** Do NOT ask the CPO cryptic technical questions. Ask in plain language; lead with a brief decision frame + options.

---

### #500 metric-layer — STATUS (COMPLETE bar step 6)

| Phase | PR(s) | Status |
|-------|-------|--------|
| PR1 — team consolidation | #574 | MERGED |
| PR2 — player renames | #577 | MERGED |
| PR-c — SSoT crown | #579 | MERGED |
| Rename sweep | #580 | MERGED |
| PR-d step 1 — WC cleanup | #582 | MERGED |
| PR-d step 2 — SSoT migration | #583 | MERGED |
| PR-d step 3 — label unification | #584 | MERGED |
| PR-d step 4 — corners rename | #585 | MERGED |
| PR-d step 5 — drop `_season` | #587 | MERGED |
| PR-d step 6 — teardown | — | NOT BUILT (scope first) |

The metric layer is now **one entity-first naming scheme + one definition SSoT (metric_catalogue.csv)**.

---

### NEXT candidates (CPO directs; none auto-granted)
- **#500 PR-d step 6** (above) — final teardown.
- **TEAM deserved-vs-actual REDESIGN** — a DESIGN discussion (below), not a build.
- **PROGRAMS** — a tranche of #545 (coverage) / #546 (data-quality) / #547 (cost) (below).
- **Carryovers (open):** #484 (player NT/tournament context window); #510 (retire leftover team `dribbles_success_pct`); team season-rollup → mapping spine (pre-season teams appear); #483 (qualifying-type cumulative window, GAP-18); display-contract amendment (appearance/playing-time block into `metrics_display.md`); Pilot PR2 slugs (BLOCKED on blinded §10 rulings E2/E3); opponent-context v1.x; Coach + career CONSUMPTION marts (DEFERRED, #391 paused).
- **Tiny follow-ups from the previous session:** two shorthand glob refs (`docs/content_architecture.md` `mart_fixture_stats__{team,player}`; `docs/wireframes/99_gaps_register.md` GAP-07) → entity-first.

### TEAM deserved-vs-actual REDESIGN (design discussion — do NOT build yet; TEAM only)
The flagship "how you PLAY vs what you GET" read. The prior crude implementation (`performance_vs_results_gap = shot_share − points_capture`) was REMOVED in #563 (uncatalogued + non-commensurable shares). Framing settled: the real failure was **comparability** → compare deserved + actual in a **common space**. **Lean (NOT decided): percentile-space gap via the benchmark engine**. Alternative: a non-xG deserved-goals/points composite. **Explicitly NO xG.** RESERVED for the discussion: the comparability METHOD, the "deserved" input set, the "actual" set. Process: catalogue-first (define metric_catalogue rows with football-analytics + CPO approval BEFORE building).

### PROGRAMS (enablers — pull in deliberately; never eclipse product)
- **#545 coverage** (`stream:coverage`): onboard ~146 missing domestic leagues by tranche. API-cheap; DQ-at-scale is the real cost. CPO picks the first tranche. `provider_league_id` discovery is search-first.
- **#546 data-quality** (`stream:data-quality`): CI integrity suite + scheduled DQ sweep + triage rule. NEXT: generalise the detector; #550 automated-triage design (SCOPE = §10 awaiting CPO).
- **#547 cost** (`stream:platform`): size BQ build-bytes/storage before expansion scales.

---

### The governance machinery (G1–G4 LIVE)
- **Contract first:** every unit writes `.claude/task/contract.md` (objective, scope_paths, decisions, done_when) on a CLEAN tree BEFORE code. `task_contract_gate.py` denies edits outside scope_paths / to PROTECTED paths (`.claude/hooks|agents|commands/`, `.github/workflows/`, `.claude/settings.json`, `.claude/review_routing.json`, `.mcp.json`, `.cursor/mcp.json`) without `protected_override`.
- **Impact-map gate:** denies first edit on structural surface until contract carries a non-placeholder `impact_map` (evidence, not assertion).
- **4-step review cycle** (Code Lock → cold Blinding → Cross-Examination → SHA-256 Lock) in `review.md`. Reviewer routing via `.claude/review_routing.json`: scope-auditor always; `dbt_project/**` → analytics-engineer; `scripts/export_*.py` → +cto; hooks/CI → cto; ingestion/registry → data-engineer; wireframes + i18n → bi-analyst; `metric_catalogue.csv` → +football-analytics. PASS needs ≥2 named risks; default FAIL.
- **Commit gate** (`git_discipline.py`): staged SHA-256 must equal review.md `diff_sha256`; required reviewers PASS, no FAIL, every ESCALATE has a CPO ANSWER. ONE substantive commit per PR. Post-commit hook auto-pushes + opens the PR.
- **CI backstop** `scripts/check_task_artifacts.py --base origin/main` re-binds review.md to the PR diff.
- **Reviewer-driven scope amendment:** when a FAIL fix needs a file outside scope → stash code changes, amend contract.md on a clean tree, unstash, fix, re-review.

---

### Form-window model vocabulary (CURRENT names, post #574/#577/#580)
- **W1 momentum:** `int_team_momentum__metrics` → `mart_team_momentum` (+ `mart_team_momentum_window` drill-down). Player: `int_player_momentum__metrics` → `mart_player_momentum`. window_type: `last_5` / `tournament_to_date` / `qualifiers`.
- **W2 season record:** `int_team_season_record` → `mart_team_season_record`; `int_player_season_record` → `mart_player_season_record`. Player full-season agg = `int_player_season__metrics`.
- **Benchmarks:** `int_team_competition_benchmarks` → `mart_team_competition_benchmarks`; `int_player_competition_benchmarks` → `mart_player_competition_benchmarks`. Per-fixture: `mart_team_fixture_stats` / `mart_player_fixture_stats`. The shared per-perspective leg builders = the `int_legs__*` family (NOT entity-renamed — separate naming question).

### Parked state (do not touch until directed)
- Team **SoT-difference** metric build STASHED (`git stash list` → "sot-difference WIP (paused for #500)"). Design settled (Camp 2, `sot_difference` = SoT for − against; TEAM only; CPO direction). Re-add after teardown.
- v2 blueprint drill-down — under #391 (PAUSED). Pilot PR2 slug rulings E2/E3 — BLINDED, do NOT pre-decide.
- Backfill Phase 2a: registry depths MERGED (#524) but deep ingest was STOPPED partway → RESUME for leagues not yet at depth. ~10x cheaper with `history_seasons` + `full`-profile scoped run.

### PENDING CPO ACTIONS (outside the tree)
1. ~~`bq rm` the orphaned metric-layer relations~~ — **ALL DONE** (16 dropped).
2. **Set `PROJECT_AUTOMATION_TOKEN`** to fine-grained least-privilege scope (from #413).
3. **Remove now-unused secrets** `CURSOR_EXECUTOR_BRIDGE_URL` + `CURSOR_EXECUTOR_BRIDGE_TOKEN` (from #458).

### Key specs to read before building
- `docs/content_architecture.md` — blocks/tabs/navigation, entity types, block↔mart map.
- `docs/metric_layer.md` — the metric-layer map (seed is SSoT; display → `metrics_display.md`; windows → `metrics_context_model.md`).
- `docs/metrics_context_model.md` §8 — player performance surface.
- `dbt_project/docs/layering.md` — layer contract + exhaustive mart inventory.

### Do NOT
- **No blueprint/feature work while #391 is PAUSED** unless the CPO directs it.
- **Never decide CPO-class questions** (§10); escalate in PLAIN language (§11).
- **Never build step 6 teardown without CPO scope approval first** — the trigger-file change is PROTECTED.
- **Never remove `build_match_preview_site.*` without verifying it's truly unused.**
- Do not compute/derive facts in the frontend/export — select/group/rename only (layering.md §Consumption).
- Do not change shipped numbers without a directed PR + before/after deltas + reviewer sign-off.
- Branch from main; never commit to main. **Never merge a PR — the CPO merges.**
- **Bash only** for all commands (git, bq, gh, python). Never PowerShell.
- **dbt CLI is broken locally** — use `mcp__dbt__parse` for ref/Jinja checks; rely on CI for data tests + SQLFluff.
