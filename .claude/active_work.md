# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-16 (squads catch-up + player bio). Shipped + MERGED this session: **#478**
(squad catch-up for finished competitions — club + national, team-keyed, atomic-per-comp) and **#481**
(player-core PR-b — `dim_player` bio enrichment from `/players/profiles`). Filed **#477** (historical
squad membership, parked), **#479** (opportunistic spare-budget backfill, design later), **#480**
(player-season aggregation consolidation, governed). A `dbt-scheduled` run was dispatched on main
(lands the squad catch-up + finishes the player backfill) — VERIFY its coverage next session. The
agent-governance system (G1–G4) is LIVE and unchanged. **Website blueprint (#391) is still PAUSED.**_

## Standing authority (in force)
- **Per-item CPO-directed.** Run the full review cycle → open PR; **CPO merges**. Stop-conditions
  ALWAYS hold: never merge, escalate §10 (in PLAIN LANGUAGE — see lessons), stop for cost/destructive.

## This session (2026-06-16) — shipped (all MERGED to main)
1. **Squads watch-item RESOLVED (was the prior handover's open watch-item).** Investigated why
   `RAW_APIF_SQUADS` held only 14 leagues (majors PL/PD/BL1/BL2 absent). Root cause = **ingest-mode
   behaviour, NOT a bug**: poll/`idle_complete` comps skip ALL per-team phases; the table is new so
   only the currently in-season (full-mode) comps landed. No loader/provider defect.
2. **#478 (commit 34c7bf2) — squad CATCH-UP for finished competitions.** Capture `/players/squads`
   for teams whose comps have all finished, keyed by TEAM, deduped across comps, **club + national**
   (validated: real national rosters incl. non-players). Uses existing signals (still-playing? +
   last-recorded season) + a season stamp — NO day-window. Writes are **atomic per comp** (discard a
   partial on quota exhaustion; re-capture whole next run) so `stg_apif__squads` (latest-per-league)
   never sees a partial. Code+tests only (no API spend in the PR). The cold review caught + fixed TWO
   real bugs (unqualified BQ table → dead dedup; partial-row write → staging silent-loss). Two §10
   rulings (escalations.log 2026-06-16): the 2026-06-12 sample-fixtures rule does NOT apply to a
   BQ-read/tuple-capture; ACCEPT the atomic-discard (stg_apif__squads UNION-ALL deferred).
3. **#481 (commit f99bd12) — player-core PR-b, reduced to BIO ONLY.** New base `base_apif__player_profiles`
   (current-per-player) → `dim_player` gains 5 bio fields (birth_place, birth_country, height, weight,
   position); 4 overlapping descriptors (name, birth_date, nationality, photo) prefer the richer
   `/players/profiles` source via coalesce (CPO-approved; may refresh descriptors, no number changes).
   Excluded age + squad_number. Surfaced additively on `mart_player_profile`. dbt-only; reviewers
   scope-auditor + analytics-engineer PASS. Full BQ build ran in ci-data-build.
4. **Budget / dispatch (CPO-directed).** CPO directed using spare daily budget ("I'm paying for it").
   A `dbt-scheduled` run was dispatched on main (run 27613585802) to execute the merged squad catch-up
   + finish the player-teams backfill. **VERIFY next session** (read-only): finished-comp squads
   (PL/PD/BL1/BL2 …) landed; player-teams backfill reached ~100% (was ~95%, 4 provenance leagues left).
5. **Memory saved:** `communication-brevity` (compact, plain language, lead with decisions + a rec).

## Issues filed this session (NOT built — CPO directs)
- **#477** — historical/per-edition squad membership (`/players/squads` is current-only). Parked;
  needs a CPO cost gate.
- **#479** — opportunistic spare-budget backfill (use leftover daily budget to deepen history).
  A NEW ingest mechanism + spend policy; needs a per-comp depth target + budget ceiling → CPO design.
- **#480** — player-season aggregation **consolidation**. The rollup already exists THREE ways
  (`mart_player_season` + `mart_player_profile` compute it inline; `int_player_season__metrics` is
  orphaned) and they DISAGREE on metrics (e.g. pass accuracy: floor vs round vs naive avg → two live
  marts publish DIFFERENT numbers). GOVERNED: reconciling canonical metric definitions CHANGES
  shipped numbers → metric_catalogue + football-analytics sign-off. NOT a quick refactor.

## The player-data initiative — status
- **DONE:** transfers chain; PR-a (ingestion #473 + staging #474); squad catch-up (#478); PR-b bio (#481).
  `dim_player` (pure Type-1 entity, now bio-enriched) + `dim_player_team_season_mapping` (rostered) exist.
- **The "appearance fact" is NOT needed as a new model** — it already exists (see #480). The
  consolidation (#480) is the next player-data step, but it is GOVERNED (metric reconciliation).
- **PR-iv (#156) — UI** player insights screens (later; part of the PAUSED blueprint #391).

## NEXT (CPO directs — none auto-granted)
- **Verify the dispatched run** (squads + backfill coverage) — read-only, no cost.
- **#480 consolidation** — governed metric-definition decision first (canonical pass-accuracy etc.),
  then one shared intermediate model both marts consume + retire the orphan. Changes shipped numbers.
- **#479 spare-budget backfill** — design (history depth + budget ceiling).
- **Pilot PR2 (slugs)** — STILL BLOCKED on two BLINDED §10 rulings E2/E3 (do NOT pre-decide):
  E2 (slug-map frontend vs warehouse), E3 (transliteration vs ASCII-strip).
- **GAP-18 parent-child Core dim** (`parent_competition`; WC↔qualifier form link) — possibly
  time-sensitive (WC 2026 window is mid-June–July; today is 2026-06-16).
- **Mart rationalization** (optional) — ~20 marts; the player marts look partly redundant
  (`mart_player_season` vs `mart_player_profile` share grain `(player_sk, season_sk)`). Flagged, not scoped.
- **GAP-17** (season-rollup denominator alignment) remains FROZEN — do NOT act.

## Process lessons locked (do not repeat)
- **Check existing CONSUMERS + duplication BEFORE building a new model.** PR-b's planned "appearance
  fact" already existed twice inline + an orphaned int model, with divergent metrics. Ask "which mart
  consumes this?" and trace marts→sources FIRST. A model with no consumer is premature (the
  "deferred fact" rule); a model that already exists should be consolidated, not re-built.
- **Aggregations belong in intermediate/marts, NEVER core.** Core = atomic facts only (layering.md).
  An aggregation of `fct_fixture_player_stats` is intermediate, even when called a "fact".
- **Communication: compact + plain, lead with decisions + a bolded recommendation.** No walls of
  text, no jargon (§-refs, model names, rule-codes) in chat. (memory: `communication-brevity`.)
- **"Unblocked by data" ≠ "design decided"** (still in force): a populated dependency is not a settled
  model; within-design choices (grain, metric definitions, edge cases) are CPO decisions.
- **Write the handover ONLY at session END, in its own artifact-only branch/PR.** Stage
  `.claude/active_work.md` ONLY (artifact_only → review-exempt); add it to a contract's scope_paths to
  satisfy the edit-gate, but do NOT commit contract.md in the handover commit. `git commit` must be
  the SOLE command (no `cd …&&`, no pipes; stage separately).

## PENDING CPO ACTIONS (outside the tree — verify if done)
1. **Set `PROJECT_AUTOMATION_TOKEN`** to the fine-grained least-privilege scope (from #413).
2. **Remove now-unused secrets** `CURSOR_EXECUTOR_BRIDGE_URL` + `CURSOR_EXECUTOR_BRIDGE_TOKEN` (from #458).

## The governance machinery (G1–G4 all LIVE — unchanged this session)
- **Contract first**: every unit of work writes `.claude/task/contract.md` (objective, scope_paths
  allowlist, decisions_reserved, done_when) on a CLEAN tree BEFORE any code. `task_contract_gate.py`
  denies edits outside scope_paths and edits to PROTECTED paths (`.claude/hooks/`, `.claude/agents/`,
  `.claude/commands/`, `.github/workflows/`, `.claude/settings.json`, `.claude/review_routing.json`)
  without a `protected_override:`. Anything under `.claude/task/` is freely editable (incl.
  escalations.log); `.claude/active_work.md` is NOT (needs scope_paths).
- **4-step review cycle** (Code Lock → cold Blinding → Cross-Examination → SHA-256 Lock) in
  `.claude/task/review.md`. Reviewers routed by `.claude/review_routing.json` (scope-auditor always;
  dbt → analytics-engineer; ingestion/data_contract/registry → data-engineer; scripts/hooks/CI/agents/
  commands/tests → cto; etc.). PASS needs ≥2 named risks; default FAIL. A reviewer FAIL on a §10-class
  question → put it to the CPO in PLAIN language; record the answer in review.md (VERDICT: ESCALATE +
  `CPO ANSWER:` in the SAME section — the literal token) and escalations.log.
- **Commit gate** (`git_discipline.py`): `git commit` is the SOLE plain command; allowlisted flags only;
  staged-diff SHA-256 must match review.md `diff_sha256` (`python .claude/hooks/git_discipline.py
  --staged-hash`); required reviewers PASS, no FAIL, every ESCALATE has a recorded CPO ANSWER.
  Artifact-only commits (`.claude/task/**` except contract.md, `.claude/active_work.md`) are review-exempt.
- **CI backstop** `scripts/check_task_artifacts.py` re-binds review.md to the PR diff hash.
- **Decision rights** (working_agreement §10/§11): never decide CPO-class (product/UX, metrics, naming,
  NEW mechanisms, rule extensions, scope, shipped numbers); unclear classification is itself a CPO call.

## Form-window model vocabulary (shipped #463 — use these names)
- live form: `int_momentum_window__team` + `int_momentum__{team,player}`; marts `mart_momentum_window__team`
  + `mart_momentum__{team,player}`. season record: `int_season_record__{team,player}`; marts
  `mart_season_record__{team,player}`. KEPT: `window_type` values + published key `form_window`.

## Parked state (do not touch until directed)
- Pilot PR2 slug rulings E2/E3 — BLINDED, do NOT pre-decide.
- Blueprint #391 PAUSED; resume-state (when un-paused): PR3 = screens 04–07; slim export PR; GAP-18
  tournament windows before WC 2026; GAP-17 ruling pending.
- Team market-value automation (#476 + #418) — new external-LLM source, needs a CPO cost gate.

## Do NOT
- **No blueprint/feature work while #391 is PAUSED** unless the CPO directs it.
- **Never decide CPO-class questions** (§10); escalate in PLAIN language (§11). Don't over-read one
  model and invent a §10 question; but DO escalate genuine layer/rule/scope/metric questions.
- Do not compute/derive facts in the frontend/export (layering.md §Consumption) — select/group/rename only.
- Do not touch the live MVP; do not change shipped numbers (GAP-17 parked).
- File edits via Edit/Write tools only — never shell redirection/heredocs (A5; G2 enforces).
- Honor `.claude/task/contract.md`: no edits outside scope_paths; protected paths need `protected_override`;
  contract amendments only on a clean tree.
- Branch from main; never commit to main; the post-commit hook auto-pushes + opens PRs.
- **Never merge a PR — the CPO merges.**
- **Never print the API key** — mask it. **Reading `.env` is deny-listed.**
- **Bash only** for all commands (git, bq, gh, python) — never PowerShell.

## Environment notes
- dbt/sqlfluff from project `.venv` (`.venv/Scripts/dbt`, `.venv/Scripts/sqlfluff`) — the GLOBAL dbt is
  broken (`dbt.adapters.factory` missing). BQ is a SHARED single environment (CI rebuilds from whichever
  branch built last; concurrent builds can contend). dbt build uses BQ query bytes, NOT the API budget.
- **API budget (API-Football Ultra) = 75,000 calls/day, resets daily.** The pipeline runs once daily at
  04:00 UTC (empirically drifts to ~07:45–10:30 UTC). Skip-if-present loaders make most runs cheap.
