# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: **2026-06-30** — main GREEN at **f4b1aa8** (#391 GAP-01 team founded year + venue → the v2 team profile, MERGED **#613**). **#391 stays UN-PAUSED, NARROW + DATA-FIRST** (CPO) — build the v2 site by completing the data+export layer to "all green" first, THEN the frontend. The live MVP stays untouched until cutover (#377). **Phase B spec'd screens COMPLETE** — A1 (#606), GAP-15 (#607), GAP-14 (#609), GAP-16 (#611), GAP-01 (#613) all merged; the 3 spec'd screens (01 fixture / 02 team / 03 player) are data-complete. **NEXT = CPO pick** among Phase C (player-season foundation), Phase D (flagship design marts), and a doc-status reconciliation. Backlog + verified gap map below._

main carries the full #500 metric layer + #596 + #598 + #600 + #530(a) + **#391 A1** (deserved-vs-actual on `mart_team_profile`, #606) + **GAP-15** (team fixtures → team payload, #607) + **GAP-14** (player `birth_date`, #609) + **GAP-16** (player team affiliation, #611) + **GAP-01** (team founded/venue, #613). **CPO merges, never self-merge — standing rule.** **#391 is UN-PAUSED but NARROW — only CPO-directed gap-backlog items; the live MVP must NOT break and there is NO frontend cutover yet — standing CPO rule.** **The 5-step protocol is LIVE:** Explore → Plan → **Confirm** (plan mode + ExitPlanMode) → Implement → Verify; for any code/model/metric task ENTER PLAN MODE and WAIT for the CPO's ExitPlanMode approval before editing. **EXCEPTION (CPO-set 2026-06-30): handover/bookkeeping refreshes SKIP plan mode** — show the diff inline, get a quick go, commit through the same contract+review+gate.

### FIRST STEPS (cold chat — do in order)
1. `git checkout main && git pull`. **main GREEN at f4b1aa8** (or later if this refresh merged). Confirm tree clean.
2. Read this file top-to-bottom before touching anything.
3. **NEXT = Phase B spec'd screens COMPLETE** (see THE GAP-CLOSURE BACKLOG below). A1 (#606), GAP-15 (#607), GAP-14 (#609), GAP-16 (#611), GAP-01 (#613) all merged — no spec'd-screen Phase-B items remain. The next track is a **CPO pick**: Phase C (player-season foundation), Phase D (flagship design marts), or the doc-status reconciliation. #391 is un-paused but NARROW — present the candidates + get the CPO's go before building; do NOT touch the live MVP or start the frontend.
4. **Bash only; never PowerShell.** For any file-touching task: write `.claude/task/contract.md` on a CLEAN tree BEFORE touching any file (impact-map gate for `dbt_project/models/**` + `scripts/export_*.py` + `ingestion/**` + `site*/`); use **PLAN MODE** for the plan-back — EXCEPT handover/bookkeeping refreshes (skip plan mode; show the diff inline + get a quick go; same contract+review+gate).

---

### ⭐ #391 UN-PAUSED — data-first: complete v2 data+export, THEN the frontend
The metric layer was rich but had no user-facing surface. The CPO un-paused #391 NARROWLY with a
**data-first strategy**: get every v2 content block to **built (mart exists) AND wired (the v2 export
carries it)** first, then build the frontend against a stable export. The live MVP (`site/`, fed by
`export_pages_data.py` + `mart_matchday_insights`) is SEPARATE — do NOT add to it; cutover is #377.

**Verified gap map (this session). NOTE:** `docs/content_architecture.md` §3's status column has drifted since 2026-06-17 and needs a reconciliation pass (a doc-only follow-up — CPO call); the verified current state is:
- v2 = `scripts/export_site_data.py` (8 entity types) + `docs/wireframes/` (only **3 of 10 screens spec'd**:
  01 fixture, 02 team, 03 player + the LOCKED metric contract; 04–10 pending). Data layer (~23 marts) ~mostly built.
- **Real gaps:** (1) the **frontend** — `site_v2/` is an empty Astro scaffold (2 stubs), the big lift;
  (2) **orphan marts** that EXIST but the v2 export does NOT carry (benchmarks, roster, career, player-season)
  AND whose screens (Squad / Stats-percentile / Career tabs) are NOT spec'd → wiring them needs a wireframe
  step FIRST (NOT cheap "just wire it" — corrected this session); (3) flagship deserved-vs-actual (DONE, A1),
  opponent-context + contribution-share (need new marts).

### ⭐ THE GAP-CLOSURE BACKLOG (A–D; order = value ÷ cost; CPO directs each item)
- **A1 — deserved-vs-actual → `mart_team_profile`. MERGED #606.** Composed `int_team_season__deserved_vs_actual`
  (deserved_rank, sot_rank_gap) into the team mart; auto-carried by the team export (select *). Option-1 placement.
  Verified actual_rank == latest_rank (same `int_team_season__standings_primary.standing_rank`) → no redundant column.
- **Phase B — wire the SPEC'D-screen gaps (export-only, the cheap green):**
  - **GAP-15 — team fixtures (next + last 5) → team payload. MERGED #607.** `mart_team_fixtures` (a view)
    precomputes ranks; `shape_team_payload` attaches `next_fixture` + `recent_results` per season, display
    fields only. Per-fixture deep-link deferred to GAP-19.
  - **GAP-14 — player `birth_date` → player payload. MERGED #609.** Export-only (+1 line in
    `shape_player_payload`) **PLUS** the directly-coupled wireframe/gaps-register doc-sync, folded in at the
    CPO's explicit direction. scope-auditor FAILed the code-only round on the missing doc-sync → resolved by
    folding it in; all 4 routed reviewers then PASSed.
  - **GAP-16 — player team affiliation (current team + per-season history) → player profile. MERGED #611.**
    NEW `int_player_season__team` derives each player's team per competition-season = the club of their
    **most-recent finished match** (Option B, CPO-ruled — deterministic/byte-stable; the roster source has no
    transfer date) + an `is_current_team` flag; `mart_player_profile` joins it + dim_team identity, DQ-tested
    (relationships `team_sk` → `dim_team`); the export reshapes into top-level `current_team` + a per-season
    `team` block (selected by the dbt flag, never re-ranked). Wireframe §3/§4/§5/§8/§10 + register doc-sync
    FOLDED in (CPO-directed). All 4 reviewers PASS; `data-build` green.
  - **GAP-01 — team founded year + venue (name/city/capacity) → team profile. MERGED #613.** The register's
    4 fields (CPO-ruled this session) added to `mart_team_profile` from its existing dim_team join (additive,
    no new model); the export surfaces top-level `founded_year` + a nested `venue` block (None when absent);
    the 4 fields stripped from per-season rows. Wireframe §3/§4/§5/§10 + register doc-sync FOLDED in
    (CPO-directed). All 4 reviewers PASS; `data-build` green. **→ Phase B's spec'd-screen gaps are COMPLETE.**
  - ⚠️ **Open (CPO call, NOT decided):** whether folding a closed gap's directly-coupled spec-sync into its
    gap PR GENERALIZES — now **3 CPO-directed instances** (#609 status-only, #611 + #613 substantive) — vs the
    gaps-register note "gap fixes never ship inside blueprint PRs". Each fold was a specific CPO direction,
    not a general rule.
  - ⚠️ benchmarks/roster/career wiring is NOT Phase B — blocked on their screens being spec'd first.
- **Phase C — player foundation + analogs:** #480 player-season model → backfill (§10 depth+cost) → player
  YoY/streaks/season + wire. A chain.
- **Phase D — design-heavy flagship marts (DECIDE first):** opponent/schedule context (§10 method, football-analytics)
  + contribution-share (§10 definition). New marts.
- **Phase E (separate, the big lift, AFTER all green):** build the v2 frontend (Astro #366/#368) against the export.

### ⚠️ Two STALE-WIREFRAME flags (reconcile separately; NOT decided)
1. **02 block-5 deserved-vs-actual:** the wireframe binds to ratio-space `shot_share`/`points_capture`/
   `performance_vs_results_gap` (that gap column does NOT exist) — but A1 shipped the **rank-space** version
   (deserved_rank/sot_rank_gap, the CPO-locked #598 method). The wireframe is stale; block 5 needs reconciling
   to rank-space before it renders.
2. **finishing_efficiency [0,1]:** locked to [0,1] by the model (`int_team_season__metrics.sql:156-158`) + a dbt
   test (`int_player_season_position.yml:21`) + CPO "Option A"; the wireframe's "never capped" line
   (`metrics_display.md:107`) is the stale one. **Lesson ([[feedback-premature-escalation]]): when two specs
   disagree, the deployed code + tests + last CPO ruling are the tiebreaker — read them BEFORE escalating.**

---

### ⭐ RECENT PRs

- **#613 — #391 GAP-01: team founded year + venue → the v2 team profile, MERGED.** The register's 4 fields added to `mart_team_profile` from its existing dim_team join (additive, no new model); export surfaces top-level `founded_year` + a nested `venue` block (None when absent). Folded wireframe/register doc-sync. All 4 reviewers PASS; `data-build` + python-ci green. → **Phase B spec'd screens COMPLETE.**
- **#612 — handover refresh (#391 GAP-16 merged), MERGED.** Recorded the post-#611 state; kept the fold-generalization question open (then 2 instances).
- **#611 — #391 GAP-16: player team affiliation (current team + per-season history) → the v2 player profile, MERGED.** NEW `int_player_season__team` (most-recent-match club per player-season + `is_current_team`) → `mart_player_profile` (+ dim_team identity, relationships DQ test) → export (`current_team` + per-season `team`, selected by the dbt flag). Folded wireframe/register doc-sync. All 4 reviewers PASS; `data-build` + python-ci green. See the backlog GAP-16 entry above.
- **#610 — handover refresh (#391 GAP-14 merged), MERGED.** Recorded the post-#609 state; established the plan-mode carve-out for handover refreshes; reserved the doc-sync fold-generalization question to the CPO.
- **#609 — #391 GAP-14: player `birth_date` → the v2 player payload, MERGED.** Export-only (+1 line in `shape_player_payload`; the column was already on `mart_player_profile`, just unsurfaced) + the folded-in wireframe/gaps-register doc sync. `data-build` + `ui-checks` skip (no dbt/UI change); python-ci green. See the backlog GAP-14 entry above.
- **#607 — #391 GAP-15: team fixtures (next + last 5) → the v2 team payload, MERGED.** Export-only; `mart_team_fixtures` (a view) → `shape_team_payload` attaches `next_fixture` + `recent_results` per season.
- **#606 — #391 A1: deserved-vs-actual on `mart_team_profile`, MERGED.** See the backlog A1 entry above.
- **#604 — #530(a) entity-dual catalogue split, MERGED.** The 2 `team and player` rows (`finishing_efficiency`, `duels_won_pct`) split per entity; player `finishing_efficiency` deferred to #530(b). Catalogue-only.

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

### OTHER carryovers (the A–D backlog above is the PRIMARY track now; CPO directs; none auto-granted)
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
- **#391 is UN-PAUSED but NARROW** — only CPO-directed gap-backlog (A–D) items; do NOT touch the live MVP (`site/`), and do NOT start the v2 frontend (Phase E) until the data+export is "all green". Each item still needs the CPO's go.
- Do not compute/derive facts in the frontend/export — select/group/rename only.
- Branch from main; never commit to main. **Never merge a PR — the CPO merges.**
- **Bash only** for all commands. **dbt CLI + SQLFluff broken locally** — rely on CI + the blinded reviewers.

### Key specs to read before building
- `dbt_project/seeds/metric_catalogue.csv` (+ its `schema.yml` entry) — the metric SSoT (formalized formulas; now guarded by `assert_team_metric_meaning_complete` + `assert_metric_catalogue_expr_resolvable`).
- `dbt_project/tests/assert_metric_catalogue_expr_resolvable.sql` — the resolvability guard (the pattern for any future catalogue-integrity test; note the FROM-ful empty fallback).
- `dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__deserved_vs_actual.sql` — the rank-space read.
- `docs/metric_layer.md` · `docs/metrics_context_model.md` §8 · `dbt_project/docs/layering.md`.
- Memory: [[feedback-metric-formula-vs-availability]], [[feedback-metric-catalogue-governance]], [[feedback-metric-calc-layer-placement]], [[project-team-metric-rank-correlation-sweep]], [[project-semantic-layer-ai-ready]].
