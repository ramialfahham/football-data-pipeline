# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-14 (Pilot started + player-data initiative launched). Shipped this
session, all MERGED to main: Pilot PR1 #465 (GAP-15 team fixtures + GAP-19 consumption
migration), the onboard-endpoint skill #466, the transfers ingestion chain #467, and its
pagination fix #469. The agent-governance system (G1–G4) remains fully LIVE and UNCHANGED
this session — see "The governance machinery" below. **Website blueprint (#391) is still
PAUSED by CPO order.**_

## Standing authority (in force)
- The 2026-06-13 standing grant covered the G4 **audit-cleanup backlog** (#409–#430). That
  backlog is COMPLETE, so that autonomous lane is spent.
- **Current work is per-item CPO-directed.** The player-data initiative and the Pilot are
  both CPO-approved; the CPO directs each PR explicitly. Run the full review cycle → open
  PR; **CPO merges**. Stop-conditions ALWAYS hold: never merge, escalate §10 blinded, stop
  for cost/destructive.

## This session — shipped (all MERGED to main)
1. **Pilot PR1 — #465 (commit 4a83e5e)** — GAP-15 `mart_team_fixtures` (new view) +
   `mart_head_to_head` pair_key/is_canonical + `mart_momentum__player.top_player_rank` +
   `mart_player_profile` `*_rank` columns; `competition_types.csv` `display_group`. Moved
   ALL ranking/H2H derivation OUT of `scripts/export_site_data.py` INTO dbt (consumption
   layer = select/group/rename only — never derive facts).
2. **onboard-endpoint skill — #466 (commit 2350d19)** — `.claude/skills/onboard-endpoint/SKILL.md`:
   check-if-ingested → throwaway verification calls (mask the API key) → cost estimate vs
   /status quota → CPO cost gate → CPO history-depth gate → build.
3. **Transfers ingestion chain — player-data PR-i #467 (commit bea45e0)** — reinstates
   `/transfers` (REVERSES retirement #420). Ingestion (`loads/transfers.py`,
   `transfers_response_for_team`, `run_transfers_for_competition`, orchestrator Phase 4) +
   dbt stg/base/core → `fct_transfer` + un-retired transfers in `docs/data_contract.md`.
4. **Transfers pagination fix — #469 (commit 56e80a5)** — `/transfers` REJECTS the `page`
   param; the chain had fetched EMPTY (every `transfers_payload` was `[]`), and a green
   build masked it. Fixed to `fetch_merged_paged(..., paginate=False)` (verified `team=157`
   → 289 moves, total=1); documented `/transfers` in `data_contract.md §Pagination`.

> **`fct_transfer` is currently EMPTY.** The only run so far populated `RAW_APIF_TRANSFERS`
> under the bug (empty payloads). Real data lands on the next full pipeline run on main
> (scheduled 04:00 OR a dispatch). Validation (fct_transfer non-empty + DQ on real moves)
> is still OUTSTANDING — see NEXT.

## The player-data initiative (CPO-approved, in progress)
Goal: ingest the player endpoints fans want AND solve GAP-16 "is current team" via a dated
affiliation timeline (instead of an is_current_team flag on the season mapping).
- Endpoints to ingest: `/players/profiles`, `/players/squads`, `/players/teams`,
  `/players/seasons`, + `/transfers` (DONE — chain landed above).
- History depth (CPO ruling 2026-06-14): **full history of all CURRENT players** (extend
  later).
- **Transfers DEDUP ruling (escalations.log 2026-06-14):** one row per
  `(player_id, team_in_id, team_out_id, transfer_date)` in BASE; `league_code` EXCLUDED
  from the partition (it is ingest provenance, not identity).
- Remaining PRs (CPO directs each — NOT auto-granted):
  - **PR-ii (core)** — enrich `dim_player` with bio; `fct_player_team_season` appearance
    fact; `int_player_affiliation_timeline` (valid_from/valid_to + sequence DERIVED from
    `fct_transfer`); + ingest profiles/squads/teams/seasons. Depends on transfers data
    being populated for the timeline.
  - **PR-iii (marts / GAP-16)** — current-team derivation on the affiliation, consumed by
    marts.
  - **PR-iv (UI #156)** — player insights screens.
- See memory [[project-player-model-redesign]] (dim_player = pure global entity; affiliation
  = mapping + facts) and [[project-metrics-context-model]].

## NEXT (CPO directs — none auto-granted)
- **Validate transfers real data** — wait for the next 04:00 run on main, OR dispatch now (a
  cost decision). Confirm `fct_transfer` non-empty + DQ tests pass on real moves.
- **Player-data PR-ii (core)** — biggest next chunk (see above).
- **Pilot PR2 (slugs)** — STILL BLOCKED on two BLINDED §10 rulings, do NOT pre-decide
  either: **E2** (where slugs are produced — frontend slug-map vs warehouse) and **E3**
  (slug spelling — transliteration vs ASCII-strip).
- **GAP-18 parent-child Core dim** — `parent_competition` (qualifier→tournament, cup→league)
  is in the registry but consumed by no model; proper home for the WC↔qualifier form link +
  tournament form windows before WC 2026.
- **GAP-17** (season-rollup denominator alignment, F8/F9) remains FROZEN — do NOT act.
- **layering.md mart-inventory** — add a `mart_team_fixtures` row (chip task_c530a020).

## Process lessons locked this session (do not repeat)
- **A GREEN build on EMPTY data masks a fetch bug.** The transfers chain built green while
  every `transfers_payload` was `[]`; only RUNNING the ingestion surfaced it. Inspect actual
  ingested ROWS before declaring an ingestion chain done.
- **`/transfers`, `/teams`, `/standings` REJECT the `page` param** → `fetch_merged_paged(...,
  paginate=False)` (one un-paged call). Listed in `data_contract.md §Pagination`.
- **Hand-provisioning shared prod BigQuery (`bq mk`) is classifier-blocked** — populate raw
  tables via the sanctioned ingestion (workflow_dispatch), never hand-DDL.
- **Editing `.claude/active_work.md` needs it in the contract's scope_paths** (edit-gate),
  even though the handover commit itself is artifact-only (commit-gate review-exempt). Add
  the scope line on a clean tree, edit + commit ONLY active_work.md, then revert the
  scaffolding scope edit so the tree ends clean. (Reconfirmed this session.)
- **Write the handover ONLY at session END, in its own artifact-only branch/PR — NEVER
  inside a task PR.** (Carry-over; still in force.)
- **`git commit` must be the SOLE command** in the Bash call — no `cd … &&` prefix, no
  `git add … &&` chain, no pipes. Stage and commit as SEPARATE calls. (Carry-over.)
- **Finalize the contract (full scope_paths) on a CLEAN tree BEFORE any code edit.**
  (Carry-over.)

## PENDING CPO ACTIONS (outside the tree — verify if done)
1. **Set `PROJECT_AUTOMATION_TOKEN`** to the fine-grained least-privilege scope (from #413,
   merged) per `docs/board_request_sync.md`.
2. **Remove now-unused secrets** `CURSOR_EXECUTOR_BRIDGE_URL` + `CURSOR_EXECUTOR_BRIDGE_TOKEN`
   (from #458, merged — nothing in the tree references them anymore).

## The governance machinery (G1–G4 all LIVE — unchanged this session)
- **Contract first**: every unit of work writes `.claude/task/contract.md` (objective,
  scope_paths allowlist, decisions_reserved, done_when) on a CLEAN tree BEFORE any code.
  `task_contract_gate.py` denies edits outside scope_paths and edits to PROTECTED paths
  (`.claude/hooks/`, `.claude/agents/`, `.github/workflows/`, `.claude/settings.json`,
  `.claude/review_routing.json`) without a `protected_override:` naming CPO authority.
- **4-step review cycle** (Code Lock → cold Blinding → Cross-Examination → SHA-256 Lock) in
  `.claude/task/review.md`. Reviewers routed by `.claude/review_routing.json` (scope-auditor
  always; dbt → analytics-engineer; ingestion/data_contract/registry → data-engineer;
  scripts/hooks/CI/agents → cto; etc.). PASS requires ≥2 named risks; default FAIL.
- **Commit gate** (`git_discipline.py`): `git commit` must be the SOLE plain command;
  allowlisted flags only; the staged-diff SHA-256 must match review.md's `diff_sha256`;
  required reviewers PASS, no FAIL, every ESCALATE has a recorded CPO ANSWER. Artifact-only
  commits (`.claude/task/**`, `.claude/active_work.md`) are review-exempt — EXCEPT
  `contract.md` (it authorizes scope, so it is never exempt and is hashed).
- **CI backstop** `scripts/check_task_artifacts.py` recomputes the diff hash over
  `git diff base...HEAD` and re-binds review.md to the PR.
- **Decision rights** (working_agreement §10): never decide CPO-class questions
  (product/UX, metrics, naming, anything permanent, NEW mechanisms, rule extensions);
  unclear classification is itself a CPO call. Escalate blinded (§11): premise_check, ≥2
  conflicting paths, NO recommendation. Hunt Appendix A anti-patterns A1–A5.

## Form-window model vocabulary (shipped #463 — use these names)
- live form: `int_momentum_window__team` (selection legs) + `int_momentum__{team,player}`
  (aggregate); marts `mart_momentum_window__team` + `mart_momentum__{team,player}`.
- season record: `int_season_record__{team,player}`; marts `mart_season_record__{team,player}`.
- KEPT: `window_type` VALUES (`last_5`/`season_to_date`/`prev_season`) and the published JSON
  key `form_window` (UI contract). Window matrix = `docs/metrics_context_model.md §4`.

## Parked state (do not touch until directed)
- Pilot PR2 slug rulings E2/E3 (above) — BLINDED, do NOT pre-decide.
- The original parked marts stash `data/marts-gap15-16-19`: GAP-15 + GAP-19 are now SHIPPED
  via #465; GAP-16 folded into player-data PR-iii; slugs → PR2.
- Blueprint #391 PAUSED; resume-state (when CPO un-pauses): PR3 = screens 04–07; slim export
  PR; GAP-18 tournament windows before WC 2026; GAP-17 ruling pending.

## Do NOT
- **No blueprint/feature work while #391 is PAUSED** unless the CPO directs it.
- **Never decide CPO-class questions** (working_agreement §10); escalate blinded (§11) — no
  recommendations. Don't over-read one model and invent a §10 question.
- Do not compute/derive anything in the frontend/export (layering.md §Consumption layer) —
  the export may select/group/rename, never derive facts.
- Do not touch the live MVP; do not change shipped numbers (GAP-17 parked).
- File edits via Edit/Write tools only — never shell redirection/heredocs (A5; G2 enforces).
- Honor `.claude/task/contract.md`: no edits outside scope_paths; protected paths need
  `protected_override:`; amendments only on a clean tree.
- Branch from main; never commit to main; the post-commit hook auto-pushes + opens PRs.
- **Never merge a PR — the CPO merges.**
- **Never print the API key** — mask it in any verification call.
- **Bash only** for all commands (git, bq, gh, python) — never PowerShell.

## Environment notes
- dbt/sqlfluff from project `.venv`. BQ is a SHARED single environment (CI rebuilds from
  whichever branch built last — redeploy before BQ-based verification).
- sqlfluff 4.1.0 parse-depth cliff ≈ 7 nested calls (relevant to the parked slug work; the
  UDF approach in the old stash was the unapproved workaround — see A3).
- The pipeline runs once daily at 04:00 UTC; do not add extra runs without CPO approval.
