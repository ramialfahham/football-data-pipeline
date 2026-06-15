# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-15 (player-data PR-a — ingestion + staging). Shipped + MERGED this session:
**#473** (PR-a1 — player-endpoint ingestion CODE) and **#474** (PR-a2 — the three staging models + a
CPO-ruled layering.md rule). The transfers chain (#467/#469) is now VALIDATED on real data
(`fct_transfer` = 152,006 moves, 0 grain dupes). The agent-governance system (G1–G4) is LIVE and
unchanged. **Website blueprint (#391) is still PAUSED by CPO order.**_

## Standing authority (in force)
- **Per-item CPO-directed.** Run the full review cycle → open PR; **CPO merges**. Stop-conditions
  ALWAYS hold: never merge, escalate §10 blinded, stop for cost/destructive.

## This session (2026-06-15) — shipped (all MERGED to main)
1. **Transfers VALIDATION (was the outstanding item from the prior handover) — DONE.** CPO-approved a
   dispatch of `dbt-scheduled.yml` on main; the fixed `paginate=False` ingestion populated
   `RAW_APIF_TRANSFERS`, and `fct_transfer` built to **152,006 rows, 0 grain dupes** at
   (player, team_out, team_in, transfer_date) — the CPO dedup ruling holds on real data — 47,066
   players, dated/directed real moves; DQ tests pass.
2. **PR-a1 — #473 (commit e63cf7c) — player-endpoint ingestion CODE only.** Three endpoints via the
   onboard-endpoint skill: `/players/squads` (per-team → `RAW_APIF_SQUADS`), `/players/profiles` +
   `/players/teams` (per-player GLOBAL phase over the current universe season>=2025 ~31.9k, gathered
   from `RAW_APIF_PLAYERS`, deterministic provenance `league_code` = MIN per player,
   skip-if-already-ingested, quota-guarded) → `RAW_APIF_PLAYER_PROFILES` / `RAW_APIF_PLAYER_TEAMS`.
   + 3 un-paged HTTP helpers, orchestrator Phase 3b (squads) + Phase 5 (global profiles/teams),
   data_contract. NO dbt models / NO backfill in PR-a1 (the split — R4). CPO rulings R1–R4 in
   escalations.log: R1 scope = profiles+teams+squads (DROP /players/seasons); R2 bio axis = per-player
   (SUPERSEDES plan's "directory"); R3 universe = current season>=2025 ~31.9k; R4 split code→staging.
3. **Backfill dispatch (CPO-approved cost — "8% of budget used, run now").** Ran on main; the new tables
   were created + populated: **profiles 100% (31,920 distinct players), teams ~88% (29/33 provenance
   leagues), squads 14 leagues**. Today's API budget was exhausted by it (expected for a one-day
   backfill); the remainder AUTO-RESUMES on tomorrow's 04:00 run via skip-if-present. **WATCH-ITEM:**
   squads landed only 14 leagues (`/players/squads` returned empty for many comps) — verify after
   tomorrow's run whether that's provider sparsity (acceptable — squads is a secondary cross-check) or a
   loader gap.
4. **PR-a2 — #474 (commit d587027) — player-endpoint staging models.** `stg_apif__squads`
   (latest-snapshot-per-league, like `stg_apif__players`), `stg_apif__player_profiles` +
   `stg_apif__player_teams` (UNION ALL snapshots — see the new layering rule), + `sources.yml` +
   `stg_apif__generic.yml`. Validated against the real backfill (profiles 31,920 rows / 31,920 distinct
   players, perfect grain). **`layering.md` §1_staging now formally recognizes "incremental-accumulation
   raw tables"** (skip-if-present loaders → read all snapshots vs latest-per-league) as a named pattern —
   CPO ruling **Path B** (escalations.log E1; both reviewers escalated it blinded, CPO chose B over a
   docs-only clarification). Two analytics-engineer test findings resolved with real-data evidence (no
   `unique` on squads / no `not_null` on `season_year` — 10 dupes / 995 nulls are real; base dedups/filters).

## The player-data initiative — status + remaining
- **DONE:** transfers chain (validated); PR-a (ingestion #473 + staging #474). `dim_player_team_season_mapping`
  (rostered membership) + `dim_player` (pure entity) already existed ([[project_player_model_redesign]], COMPLETE).
- **PR-b (next buildable) — core:** enrich `dim_player` with bio (from `stg_apif__player_profiles`);
  `fct_player_team_season` appearance fact (first/last_appearance_date, games — from
  `fct_fixture_player_stats` + `fct_fixture`). Independent of the timeline; buildable now (data exists).
- **PR-c — `int_player_affiliation_timeline` — DESIGN NOT DECIDED (CPO flagged 2026-06-15).** The plan §6 D5
  recorded only a DIRECTION ("transfer-dated timeline: valid_from/to + affiliation_seq from `fct_transfer`;
  current = open span; squads cross-check; appearance-date fallback") — approved BEFORE the real data was in
  hand. The buildable design is OPEN and much of it is §10-class — do NOT pre-decide: grain (span per
  (player,team) vs per stint/re-join); span construction from discrete transfer dates (ordering, gaps,
  overlaps, the open/current span); LOAN handling (Loan / Return from loan — overlapping span vs replacement);
  messy/edge data (Free agent w/ null team_in, null sides, dates to 1926, noisy `transfer_type`); "current
  club" = GAP-16 (product-facing). At PR-c: reconfirm D5 against the real data, do a design pass, bring the
  §10 choices to the CPO (blinded where appropriate) — NOT a build-from-plan task.
- **PR-iv (#156) — UI** player insights screens (later).
- Plan: `C:\Users\Rami\.claude\plans\player_data_ingestion_plan.md` — but D-bio "directory" + §8 4-endpoint
  scope were SUPERSEDED this session by R1/R2; D5 timeline is direction-only. See also [[project_metrics_context_model]].

## NEXT (CPO directs — none auto-granted)
- **PR-b (core)** — `dim_player` bio + `fct_player_team_season`. Buildable now (data exists).
- **PR-c (timeline)** — needs a DESIGN decision first (above). NOT queued to build.
- **Tomorrow's 04:00 run** finishes the teams/squads backfill; verify coverage + the squads watch-item.
- **Pilot PR2 (slugs)** — STILL BLOCKED on two BLINDED §10 rulings E2/E3 (do NOT pre-decide either):
  E2 (slugs produced frontend slug-map vs warehouse), E3 (slug spelling transliteration vs ASCII-strip).
- **GAP-18 parent-child Core dim** (`parent_competition`; WC↔qualifier form link before WC 2026).
- **GAP-17** (season-rollup denominator alignment) remains FROZEN — do NOT act.
- **layering.md mart-inventory** — add a `mart_team_fixtures` row (chip task_c530a020) — still open.

## Process lessons locked (do not repeat)
- **"Unblocked by data" ≠ "design decided."** Don't treat a satisfied data DEPENDENCY (e.g. `fct_transfer`
  populated) as a settled MODEL. A plan marking something "SETTLED" usually records a DIRECTION, not a
  buildable spec — the within-design choices (grain, edge cases, product concepts) are still CPO decisions.
  (CPO correction 2026-06-15 re: `int_player_affiliation_timeline`.)
- **Incremental-accumulation staging is now a recognized pattern (layering.md §1_staging, CPO Path B).**
  Skip-if-present loaders → staging reads ALL snapshots (no latest-per-league qualify; the CI check permits
  omitting it). A table is incremental-accumulation IFF its loader is skip-if-present; state it in the model
  header + the generic-yml entry.
- **To bring a NEW path into a contract's scope on a dirty tree:** stash the code (`git stash push -u -- <path>`),
  amend `contract.md` on the now-clean tree, `git stash pop`, then edit the newly-scoped file. (Used this session
  to add `layering.md` to PR-a2's scope, and to add `active_work.md` for this handover.)
- **A GREEN build on EMPTY/missing data masks a bug** — inspect actual ROWS before declaring an ingest done
  (transfers lesson; applied to PR-a's split: code first → backfill → INSPECT rows → staging).
- **Write the handover ONLY at session END, in its own artifact-only branch/PR — NEVER inside a task PR.**
  Editing `.claude/active_work.md` needs it in the contract's scope_paths (edit-gate). **`git commit` must be
  the SOLE command** in its Bash call (no `cd …&&`, no `git add …&&`, no pipes; stage separately).
- **Finalize the contract (full scope_paths) on a CLEAN tree BEFORE any code edit.**

## PENDING CPO ACTIONS (outside the tree — verify if done)
1. **Set `PROJECT_AUTOMATION_TOKEN`** to the fine-grained least-privilege scope (from #413, merged).
2. **Remove now-unused secrets** `CURSOR_EXECUTOR_BRIDGE_URL` + `CURSOR_EXECUTOR_BRIDGE_TOKEN` (from #458).

## The governance machinery (G1–G4 all LIVE — unchanged this session)
- **Contract first**: every unit of work writes `.claude/task/contract.md` (objective, scope_paths
  allowlist, decisions_reserved, done_when) on a CLEAN tree BEFORE any code. `task_contract_gate.py` denies
  edits outside scope_paths and edits to PROTECTED paths (`.claude/hooks/`, `.claude/agents/`,
  `.claude/commands/`, `.github/workflows/`, `.claude/settings.json`, `.claude/review_routing.json`) without
  a `protected_override:` naming CPO authority. `.claude/settings.json` also carries a `permissions.deny`
  backstop UNDER the hooks.
- **4-step review cycle** (Code Lock → cold Blinding → Cross-Examination → SHA-256 Lock) in
  `.claude/task/review.md`. Reviewers routed by `.claude/review_routing.json` (scope-auditor always; dbt →
  analytics-engineer; ingestion/data_contract/registry → data-engineer; scripts/hooks/CI/agents/commands →
  cto; etc.). PASS requires ≥2 named risks; default FAIL.
- **Commit gate** (`git_discipline.py`): `git commit` is the SOLE plain command; allowlisted flags only; the
  staged-diff SHA-256 must match review.md's `diff_sha256`; required reviewers PASS, no FAIL, every ESCALATE
  has a recorded CPO ANSWER. Artifact-only commits (`.claude/task/**`, `.claude/active_work.md`) are
  review-exempt — EXCEPT `contract.md` (it authorizes scope, never exempt, hashed).
- **CI backstop** `scripts/check_task_artifacts.py` recomputes the diff hash over `git diff base...HEAD` and
  re-binds review.md to the PR.
- **Decision rights** (working_agreement §10/§11): never decide CPO-class questions; unclear classification is
  itself a CPO call; escalate blinded (premise_check, ≥2 conflicting paths, NO recommendation — but the CPO
  may ask for a plain-language explanation + recommendation, as happened with E1 this session). Hunt A1–A5.

## Form-window model vocabulary (shipped #463 — use these names)
- live form: `int_momentum_window__team` (selection legs) + `int_momentum__{team,player}` (aggregate);
  marts `mart_momentum_window__team` + `mart_momentum__{team,player}`.
- season record: `int_season_record__{team,player}`; marts `mart_season_record__{team,player}`.
- KEPT: `window_type` VALUES (`last_5`/`season_to_date`/`prev_season`) + the published JSON key `form_window`.

## Parked state (do not touch until directed)
- Pilot PR2 slug rulings E2/E3 — BLINDED, do NOT pre-decide.
- Blueprint #391 PAUSED; resume-state (when un-paused): PR3 = screens 04–07; slim export PR; GAP-18
  tournament windows before WC 2026; GAP-17 ruling pending.

## Do NOT
- **No blueprint/feature work while #391 is PAUSED** unless the CPO directs it.
- **Never decide CPO-class questions** (§10); escalate blinded (§11). Don't over-read one model and invent a
  §10 question; but DO escalate genuine layer-contract / rule-extension questions (E1 this session was real).
- Do not compute/derive facts in the frontend/export (layering.md §Consumption) — select/group/rename only.
- Do not touch the live MVP; do not change shipped numbers (GAP-17 parked).
- File edits via Edit/Write tools only — never shell redirection/heredocs (A5; G2 enforces).
- Honor `.claude/task/contract.md`: no edits outside scope_paths; protected paths need `protected_override`;
  amendments only on a clean tree.
- Branch from main; never commit to main; the post-commit hook auto-pushes + opens PRs.
- **Never merge a PR — the CPO merges.**
- **Never print the API key** — mask it in any verification call. **Reading `.env` is deny-listed** (use the
  sanctioned ingestion, not ad-hoc key reads).
- **Bash only** for all commands (git, bq, gh, python) — never PowerShell.

## Environment notes
- dbt/sqlfluff from project `.venv`. BQ is a SHARED single environment (CI rebuilds from whichever branch
  built last — redeploy before BQ-based verification). dbt build uses BQ query bytes, NOT the API budget.
- **API budget (API-Football Ultra) = 75,000 calls/day, resets daily.** Today's was exhausted by the PR-a
  backfill; player backfill auto-resumes (skip-if-present) on tomorrow's 04:00 run.
- The pipeline runs once daily at 04:00 UTC (empirically drifts to ~07:45–08:45 UTC). Do not add extra runs
  without CPO approval.
