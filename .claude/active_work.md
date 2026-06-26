# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: **2026-06-26 EOD** — **#579 (PR-c: metric-definition SSoT) + #580 (entity-first rename sweep) MERGED.** #500's whole NAMING + SSoT effort is now COMPLETE; all orphaned BQ relations dropped. **NEXT: CPO directs** — the remaining #500 unit is **PR-d** (the §10-heavy live-MVP→catalogue merge); other candidates below. Nothing pending-merge._

main carries #576 + #577 + #578 + **#579 + #580**. **Website #391 PAUSED; the live MVP must NOT break — standing CPO rule.** Per-item CPO-directed; **CPO merges, never self-merge.** **The 5-step protocol is LIVE (#576):** Explore → Plan → **Confirm** → Implement → Verify; for any file-touching task ENTER PLAN MODE at the Plan step and WAIT for the CPO's ExitPlanMode approval (= Confirm) before editing — UNLESS the CPO already gave an explicit go for the specific change. `working_agreement.md` §1 + CLAUDE.md carry it.

### FIRST STEPS (cold chat — do in order)
1. `git checkout main && git pull` (carries #579 + #580). **Nothing pending-merge; main GREEN.** **The NEXT unit is a CPO direction — do NOT infer it; ASK.** Candidates (see "NEXT candidates"): **#500 PR-d** (the live-MVP→catalogue merge, §10-heavy) · the **TEAM deserved-vs-actual** design discussion · a **program** tranche (#545/#546/#547) · a **carryover**.
2. **Bash only; never PowerShell.** For any file-touching task: write `.claude/task/contract.md` on a CLEAN tree BEFORE touching any model (the impact-map gate enforces it for `dbt_project/models/**` + `scripts/export_*.py` + `ingestion/**` + `site*/`) + use **PLAN MODE** for the plan-back. **Read `docs/working_agreement.md` §1 (the 5-step protocol) + the memory index first.**
3. **Metric definitions = ONE SSoT now (#579):** the **`dbt_project/seeds/metric_catalogue.csv` seed** is THE single source of truth for every metric definition (formula/description/group/tier/order); `docs/metric_layer.md` is the map. **No prose doc defines a metric.** `docs/player_metrics_catalogue.md` was DELETED. See [[project-semantic-layer-ai-ready]] + [[project-metric-layer-two-seeds]].

### ⭐ THIS SESSION (2026-06-26) — metric-layer naming + SSoT cleanup (closed out #500's naming) + the Confirm protocol
All merged:
- **#576 — Confirm-step protocol.** Named the **Explore→Plan→Confirm→Implement→Verify** ladder in `working_agreement.md` §1 (+ CLAUDE.md pointer); **Confirm = the human checkpoint, mechanised via native PLAN MODE** (EnterPlanMode → plan-back → CPO approves ExitPlanMode). A self-attested `cpo_go` token was considered + HELD IN RESERVE.
- **#577 — #500 PR2 player renames.** Entity-first rename of the 4 player momentum/season models. RENAMES ONLY (the two player season models don't merge — different grains). Byte-identical.
- **#579 — PR-c: crown the metric-definition SSoT.** Made the `metric_catalogue.csv` seed THE definition source; turned `metric_layer.md` into the "where each thing lives" map; **DELETED `docs/player_metrics_catalogue.md`** (the competing claimant — specced the retired `mart_matchday_player_insights`); added a one-line "definitions live in the seed" deferral to `metrics_display.md` (CPO-locked #391) + `metrics_context_model.md` (both KEPT); repointed every reference (incl. 2 dbt provenance comments) to the seed; cleared the deferred #577/#574 old-name doc debt. Docs + provenance only; zero metric logic change. **Root cause it fixes:** multiple docs each claimed to define metrics, so the SSoT was unidentifiable (the agent kept drifting).
- **#580 — entity-first rename sweep.** Renamed the 8 remaining `<surface>__<entity>` models → `<entity>_<surface>` (momentum_window / fixture_stats / competition_benchmarks; int+mart together) + every consumer (refs, yml, 2 DQ tests, the paused v2 export, docs) + added the missing `mart_player_competition_benchmarks` row to `layering.md` (CPO-ruled, resolving an analytics-engineer FAIL). EXCLUDED the `int_legs__*` family (a separate naming question). Pure rename, byte-identical; 5 reviewers PASS.
- **bq cleanup DONE:** all 16 orphaned old relations dropped (8 from #574/#577 + 8 from #580); verified zero remain.
- **New memory:** [[project-semantic-layer-ai-ready]] — the seed-as-SSoT is a deliberate on-ramp to a real semantic layer (dbt MetricFlow) for AI-readiness; don't build yet; the dbt MCP server is the AI seam; trigger = the first "any metric × any dimension" consumer.

### #500 metric-layer — STATUS (naming + SSoT COMPLETE; PR-d is the only remaining unit)
DONE: PR1 #574 (team consolidation) · PR2 #577 (player renames) · PR-c #579 (SSoT crown + retire the competing doc) · the rename sweep #580 (the leftover `__entity` marts/ints). The metric layer is now **one entity-first naming scheme + one definition SSoT (the catalogue seed)**.

**PR-d — the live-MVP → catalogue merge (the remaining #500 unit; §10-HEAVY; CPO-directed):**
There are **TWO metric-definition seeds** (the real "2-3 metric layers" — [[project-metric-layer-two-seeds]]): `metric_catalogue.csv` (v2; feeds the PAUSED v2 export) and **`metric_definitions.csv` (LEGACY MVP; feeds the LIVE site** via `build_match_preview_site.sh` + `site/match-preview` + `site/team-season`; window-suffixed ids like `goals_per_match_recent`; `*_recent`/`*_pretournament` i18n). PR-d = **migrate the LIVE MVP onto the catalogue + retire the legacy seed**, WITHOUT breaking the live MVP:
- Consolidate `metric_definitions.csv` INTO the catalogue; repoint `export_metric_definitions_json.py` at the catalogue; delete the legacy seed + the legacy `*_recent`/`*_pretournament` i18n; reconcile i18n onto `label_i18n_key`.
- Drop the `_season` column suffix end-to-end (changes the live `team_season_insights.json` keys → must move in lockstep with the site JS); `corners_conceded → corners_against` (the one live-shared rename); register `qualifier_games_played` (a LIVE metric not yet catalogued).
- **MVP-safety gate at every step:** the generated `site/match-preview/metric_definitions.json` must stay **byte-identical** to today's. If it moves, the step is wrong.
- **§10s to escalate blinded in PR-d's contract:** the single i18n key scheme; corners naming on the live surface; registering `qualifier_games_played`. Genuine CPO-class — do NOT pre-decide.

### NEXT candidates (CPO directs; none auto-granted)
- **#500 PR-d** (above) — finish the metric layer end-to-end on the live MVP.
- **TEAM deserved-vs-actual REDESIGN** — a DESIGN discussion (below), not a build.
- **PROGRAMS** — a tranche of #545 (coverage) / #546 (data-quality) / #547 (cost) (below).
- **Carryovers (open):** #484 (player NT/tournament context window — changes shipped numbers, own validation); #510 (retire leftover team `dribbles_success_pct`); team season-rollup → mapping spine (pre-season teams appear); #483 (qualifying-type cumulative window, GAP-18); display-contract amendment (appearance/playing-time block into `metrics_display.md`); Pilot PR2 slugs (BLOCKED on blinded §10 rulings E2/E3); opponent-context v1.x (weights opponents via the benchmark engine); Coach + career CONSUMPTION marts (DEFERRED, #391 paused).
- **Tiny follow-ups from this session:** two shorthand glob refs (`docs/content_architecture.md` `mart_fixture_stats__{team,player}`; `docs/wireframes/99_gaps_register.md` GAP-07 `mart_fixture_stats__*`) → entity-first; a small seed-`description` enrichment (provider-semantics nuances; football-analytics-reviewed) flagged in PR-c.

### TEAM deserved-vs-actual REDESIGN (design discussion — do NOT build yet; TEAM only, CPO excluded the player analog)
The flagship "how you PLAY vs what you GET" read (`content_architecture.md` §6). football-analytics owns the metric definition (§10). The prior crude implementation (`performance_vs_results_gap = shot_share − points_capture`) was REMOVED in #563 (uncatalogued + non-commensurable shares). Framing settled (carry in, don't re-derive): the real failure was **comparability** → compare deserved + actual in a **common space**. **Lean (NOT decided): percentile-space gap via the benchmark engine** (deserved = percentile on underlying-play metrics, actual = percentile on results metrics; both 0–1, interpretable). Alternative: a non-xG deserved-goals/points composite (richer; football-analytics must define+validate). **Explicitly NO xG.** RESERVED for the discussion: the comparability METHOD, the "deserved" input set, the "actual" set. **Process — catalogue-first** (define `metric_catalogue` rows with football-analytics + CPO approval BEFORE building; the #324 lesson). [[feedback-design-spec-altitude]].

### PROGRAMS (enablers — pull in deliberately; never eclipse product)
- **#545 coverage** (`stream:coverage`): onboard the ~146 missing domestic leagues by tranche (discover → registry zero-file onboard → `verify-competition-ingest` + a DQ sweep). API-cheap (~25-40k one-time); **DQ-at-scale is the real cost**. CPO picks the first tranche. `provider_league_id` discovery is **search-first** (4 wrong IDs happened before).
- **#546 data-quality** (`stream:data-quality`): a growing CI integrity suite + a scheduled all-league DQ sweep + the triage rule (diagnose-to-root → bounded fix or tracked issue → **never** coverage-cut, **never** merge-on-internal-similarity). The #526 fix LANDED (#551). NEXT: generalise the detector into the standing scan; the #550 automated-triage design (detect → gather + EXTERNALLY-verify → escalate; human decides; NO auto-fix — a §10 awaiting CPO scope).
- **#547 cost** (`stream:platform`): size BQ build-bytes/storage before the expansion scales. (Cost lever already pulled: #573 slim-CI — PR builds are `state:modified+` only.)

### The governance machinery (G1–G4 LIVE)
- **Contract first:** every unit writes `.claude/task/contract.md` (objective, scope_paths, decisions, done_when) on a CLEAN tree BEFORE code. `task_contract_gate.py` denies edits outside scope_paths / to PROTECTED paths (`.claude/hooks|agents|commands/`, `.github/workflows/`, `.claude/settings.json`, `.claude/review_routing.json`, `.mcp.json`, `.cursor/mcp.json`) without `protected_override`; denies contract (re)writes on a dirty tree. `.claude/task/**` freely editable; **`.claude/active_work.md` is NOT** (needs scope_paths — as in this handover).
- **Impact-map gate:** denies the first edit on the **structural surface** (`ingestion/**`, `dbt_project/models/**`, `scripts/export_*.py`, `site*/`) until the contract carries a non-placeholder `impact_map` (writers + lineage + layer rules + deploy ordering + blast radius; EVIDENCE, e.g. real `dbt ls`, not assertion). Trivial edits = one-line short-form.
- **4-step review cycle** (Code Lock → cold Blinding → Cross-Examination → SHA-256 Lock) in `review.md`. Reviewers routed by `.claude/review_routing.json`: scope-auditor always; `dbt_project/**` → analytics-engineer; `scripts/export_*.py` → +cto; `scripts|tests|CI|hooks|agents|commands` → cto; ingestion/registry → data-engineer; `docs/wireframes/**` + i18n → bi-analyst; `metric_catalogue.csv` → +football-analytics. PASS needs ≥2 named risks; default FAIL. A reviewer FAIL on a §10 → put to the CPO in PLAIN language; a FAIL on a non-§10 → fix + re-review.
- **Commit gate** (`git_discipline.py`): `git commit` SOLE plain command; allowlisted flags only (message/quiet/verbose/sign — NOT --amend/--no-verify); staged SHA-256 must equal review.md `diff_sha256` (`python .claude/hooks/git_discipline.py --staged-hash`); required reviewers PASS, no FAIL, every ESCALATE has a CPO ANSWER. Artifact-only commits are review-exempt — but a commit carrying contract.md is never exempt. ONE substantive commit per PR (staged == PR diff). The post-commit hook auto-pushes + opens the PR.
- **CI backstop** `scripts/check_task_artifacts.py --base origin/main` re-binds review.md to the PR diff.
- **Reviewer-driven scope amendment** (recurs): when a reviewer FAIL's fix needs a file outside scope, it is a clean-tree contract amendment — **stash the code changes** (leaving only `.claude/task/` dirty → the gate permits the amendment), edit contract.md (authority = the FAIL + standing rule), unstash, fix, re-review. Used this session for `mart_player_match_log.sql`. [[feedback-sibling-pr-rebase-rebind]].

### Process lessons locked (in memory — read the index)
[[feedback-no-hacky-solutions]] (don't over-build, don't hack, don't flip-flop; read the authoritative doc; trace RAW→consumption; query RAW not staging) · [[feedback-scope-discipline]] (no unauthorized PR additions — ask first) · [[feedback-design-spec-altitude]] · [[feedback-doc-clutter-discipline]] (#505 tracks the docs/ audit) · [[feedback-handover-discipline]] · [[macros-decrease-maintainability]] (plain inline SQL + COMPOSE, no Jinja macros) · [[feedback-verify-real-world-identity]] (external ground truth, never merge-on-internal-similarity) · [[feedback-communication-brevity]] (compact, lead with a bolded rec).

### Form-window model vocabulary (CURRENT names, post #574/#577/#580)
- **W1 momentum:** `int_team_momentum_window` → `int_team_momentum__metrics` → `mart_team_momentum` (+ `mart_team_momentum_window` drill-down). Player: `int_player_momentum__metrics` → `mart_player_momentum`. window_type: `last_5` / `tournament_to_date` / `qualifiers`.
- **W2 season record:** `int_team_season_record` → `mart_team_season_record`; `int_player_season_record` → `mart_player_season_record` (`season_to_date` + `prev_season`). Player full-season agg = `int_player_season__metrics` (#480).
- **Benchmarks:** `int_team_competition_benchmarks` → `mart_team_competition_benchmarks`; `int_player_competition_benchmarks` → `mart_player_competition_benchmarks`. Per-fixture stat lines: `mart_team_fixture_stats` / `mart_player_fixture_stats`. The shared per-perspective leg builders = the **`int_legs__*`** family (`team_match`, `player_match`, `team_from_players`) — deliberately NOT entity-renamed (a separate naming question).

### Parked state (do not touch until directed)
- Team **SoT-difference** metric build STASHED (`git stash list` → "sot-difference WIP (paused for #500)"). Design settled (Camp 2, `sot_difference` = SoT for − against; observational, no xG/predictions; TEAM only). Re-add after the metric-layer work. Analytics Corner ideas = issue #565.
- v2 blueprint drill-down — under #391 (PAUSED). Pilot PR2 slug rulings E2/E3 — BLINDED, do NOT pre-decide. Team market-value automation (#476 + #418) — external-LLM source, CPO cost gate. #477 historical/per-edition squad membership (overlaps the backfill).
- Backfill: Phase 2a registry depths MERGED (#524) but the deep INGEST was STOPPED partway → RESUME for leagues not yet at depth (8 continental-club→10, 7 domestic→5). To backfill: set `history_seasons` (authoritative post-#520) + a `full`-profile scoped run + verify RAW. ~10x cheaper than `fixtures × 4` (batched sub-endpoints).

### PENDING CPO ACTIONS (outside the tree)
1. ~~`bq rm` the orphaned metric-layer relations~~ — **ALL DONE** (16 dropped; verified zero remain).
2. **Set `PROJECT_AUTOMATION_TOKEN`** to the fine-grained least-privilege scope (from #413).
3. **Remove now-unused secrets** `CURSOR_EXECUTOR_BRIDGE_URL` + `CURSOR_EXECUTOR_BRIDGE_TOKEN` (from #458).

### Key specs to read before building
- `docs/content_architecture.md` — blocks/tabs/navigation, entity types, block↔mart map, flagship reads, new-mart list, backfill policy (the product engine spec).
- `docs/metric_layer.md` — the metric-layer map (the seed is the SSoT; display → `metrics_display.md`; windows → `metrics_context_model.md`).
- `docs/metrics_context_model.md` §8 — the player performance surface (windows + aggregation).
- `dbt_project/docs/layering.md` — the layer contract + the exhaustive mart inventory.

### Do NOT
- **No blueprint/feature work while #391 is PAUSED** unless the CPO directs it.
- **Never decide CPO-class questions** (§10); escalate in PLAIN language (§11). Don't over-read one model and invent a §10; but DO escalate genuine layer/rule/scope/metric/naming questions.
- Do not compute/derive facts in the frontend/export (layering.md §Consumption) — select/group/rename only.
- Do not change shipped numbers without a directed PR + before/after deltas + reviewer sign-off.
- File edits via Edit/Write tools only — never shell redirection/heredocs (the generated `review_input.patch` via `git diff >` is the bookkeeping exception — hash-excluded).
- Branch from main; never commit to main.
- **Never merge a PR — the CPO merges.**
