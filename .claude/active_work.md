# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-16 (GAP-18 tournament form window). Shipped this session: **GAP-18** — the WC
tournament/qualifier form window. **PR #485** (mart layer / form NUMBERS) is **MERGED** to main.
**PR #486** (live form LABEL via `form_from_qualifiers`) is **OPEN + CI green** (validate passed,
data-build was running at session end) — **needs CPO merge** to complete the live fix. Filed **#483**
(qualifying-type cumulative window) + **#484** (player-strip tournament form), both deferred from
GAP-18. Governance G1–G4 LIVE. **Website blueprint #391 still PAUSED.**_

## FIRST next session (do this first)
- **Merge PR #486** if not already merged — the GAP-18 live LABEL. It is the re-land of the orphaned
  commit 2 after #485's squash-merge took only commit 1 (cherry-picked clean; validate green; confirm
  data-build green). **Until #486 merges, live WC previews show correct cumulative NUMBERS but the wrong
  "all World Cup matches so far" LABEL for qualifier-stage teams (the live MD1 previews).**

## Standing authority (in force)
- **Per-item CPO-directed.** Run the full review cycle → open PR; **CPO merges**. Stop-conditions
  ALWAYS hold: never merge, escalate §10 (in PLAIN LANGUAGE), stop for cost/destructive.

## This session (2026-06-16) — GAP-18 WC form window
1. **Verified the dispatched data-build run (read-only, no cost).** Both runs on main succeeded
   (daily schedule + the dispatched run). (a) Squads catch-up landed — `RAW_APIF_SQUADS` 14→38 leagues,
   season-stamped, ~2,026 distinct team squads; major club comps covered (PL/PD/SA/L1 100%; BL1/BL2
   19/19 each, captured under the German Cup via the cross-comp dedup). (b) player-teams backfill
   COMPLETE — 31,921 distinct players across all 33 provenance leagues (was 30,306 / 29).
2. **GAP-18 shipped (two commits, one branch).** WC tournament/qualifier form window, generic by
   competition_type (world_championship + continental_championship): `window_type='tournament_to_date'`
   (cumulative within the tournament, NO 5-cap) + `'qualifiers'` (the team's qualifier matches before
   its opener), via the registry `parent_competition` link **synced into the competition_registry seed**
   (extended scripts/sync_dbt_vars.py + check_registry_var_sync.py). Threaded `window_type` through
   `int_momentum__team` + the momentum marts; new DQ test `assert_tournament_form_window` (provenance +
   uncapped count). The live preview mart `mart_matchday_insights` reads `mart_momentum__team`, so the
   live WC form NUMBERS are now tournament-cumulative. The live LABEL switches via `form_from_qualifiers`
   booleans on `mart_matchday_insights` feeding the EXISTING `formContextLabel` UI + `formContextWc*`
   i18n (en/de/fi) — no export/UI change (export is `SELECT *` passthrough). Validated on live data:
   48 WC teams split 32 tournament-form / 16 qualifier-form; qualifier windows 6–21 games (5-cap gone).
   **#485 (numbers) MERGED; #486 (label) OPEN.**
3. **Two §10 rulings** (escalations.log 2026-06-16): (naming) MATCH the UI-pinned `form_from_qualifiers`
   name — a CPO-approved exception to the is_/has_ convention (the published UI pins it); (mixed-window)
   PROCEED — the mart surfaces one round per league so both fixture sides share the same window phase.
   `window_type` values `tournament_to_date` + `qualifiers` confirmed; existing `season_to_date` UNTOUCHED.

## WATCH-ITEM found this session (NOT fixed — needs a CPO decision; not yet filed)
- **`dim_team` has ZERO BL1/BL2 rows.** The two German leagues are entirely absent from the team
  directory (core.dim_team) even though fct_fixture has a full BL1/BL2 season (~308 fixtures each). The
  `/teams` feed (base_apif__teams_global) never landed for BL1/BL2; the German clubs exist in dim_team
  only under their cup/Euro codes. Pre-existing, unrelated to GAP-18. Any BL1/BL2-keyed dim_team lookup
  returns nothing. **Decide:** investigate root cause + file/fix, or accept. Not yet an issue.

## Issues filed this session (NOT built — CPO directs)
- **#483** — qualifying-type comps still use last-5, not the cumulative campaign window (matrix §4). Deferred.
- **#484** — player top-strip uses last-5 on tournament fixtures (GAP-18 was team-only). Deferred.

## NEXT (CPO directs — none auto-granted)
- **Merge #486** (above) — completes the GAP-18 live label.
- **#480** player-season consolidation — GOVERNED (reconcile divergent metric defs FIRST; changes shipped numbers).
- **#479** spare-budget backfill — DESIGN (per-comp history depth + budget ceiling).
- **#483 / #484** — the GAP-18 follow-ups (qualifying-type window; player-strip tournament form).
- **Pilot PR2 (slugs)** — STILL BLOCKED on the two BLINDED §10 rulings E2/E3 (do NOT pre-decide).
- **dim_team BL1/BL2 gap** (watch-item above) — DQ on two flagship leagues.

## Process lessons locked (do not repeat)
- **Squash-merge can drop a near-merge commit — VERIFY every commit landed.** #485 was squash-merged
  taking only commit 1 (the numbers); commit 2 (the label), pushed minutes before the merge, was NOT in
  it (`form_from_qualifiers` absent from main). Re-landed by **cherry-pick of the orphaned reviewed
  commit onto a fresh branch from main** (PR #486) — the cherry-pick carries the commit's review.md so
  the commit gate AND the CI artifact-backstop bind cleanly (validate passed). After a multi-commit PR
  merges, grep main for the last commit's signature change before declaring done.
- **A mart-layer fix may not reach the live screen by itself — trace the consumer.** GAP-18's numbers
  flow to the live preview via mart_matchday_insights → mart_momentum__team, but the LABEL needed a
  separate flag the live UI already expected (`form_from_qualifiers`). Always trace marts→export→UI for
  "live" fixes; the live MVP (mart_matchday_insights → export_pages_data.py SELECT* → site/match-preview)
  is NOT the paused v2 blueprint.
- **Contract scope grows = discrete commit, not a mid-tree amendment.** The contract gate forbids
  editing contract.md on a dirty tree, so widening scope mid-task = finish/commit the current unit
  first, then a fresh contract on the clean tree (here: numbers = commit 1, label = commit 2).
- **Branch on the competition TYPE, never a hardcoded league_code.** GAP-18 branches on
  competition_type ('world_championship'/'continental_championship') + window_type — generic to any
  tournament; "WC" appears only in comments/labels, never in business logic.
- Communication: compact + plain, lead with decisions + a bolded recommendation; no jargon in chat.

## The governance machinery (G1–G4 all LIVE — unchanged this session)
- **Contract first**: every unit writes `.claude/task/contract.md` (objective, scope_paths allowlist,
  decisions_reserved, done_when) on a CLEAN tree BEFORE code. `task_contract_gate.py` denies edits
  outside scope_paths / to PROTECTED paths (`.claude/hooks|agents|commands/`, `.github/workflows/`,
  `.claude/settings.json`, `.claude/review_routing.json`) without `protected_override`; and denies
  contract (re)writes on a dirty tree. `.claude/task/**` freely editable; `.claude/active_work.md` is
  NOT (needs scope_paths).
- **4-step review cycle** (Code Lock → cold Blinding → Cross-Examination → SHA-256 Lock) in
  `.claude/task/review.md`. Reviewers routed by `.claude/review_routing.json` (scope-auditor always;
  dbt → analytics-engineer; scripts/tests/CI/hooks/agents/commands → cto; ingestion/registry-seed →
  data-engineer; wireframes/i18n → bi-analyst; metric_catalogue → +football-analytics). PASS needs ≥2
  named risks; default FAIL. A reviewer FAIL on a §10 question → put it to the CPO in PLAIN language;
  record in review.md (VERDICT: ESCALATE + `CPO ANSWER:` same section) + escalations.log.
- **Commit gate** (`git_discipline.py`): `git commit` SOLE plain command; allowlisted flags only;
  staged SHA-256 must equal review.md `diff_sha256` (`python .claude/hooks/git_discipline.py
  --staged-hash`); required reviewers PASS, no FAIL, every ESCALATE has a CPO ANSWER. Artifact-only
  commits (`.claude/task/**` except contract.md, `.claude/active_work.md`) are review-exempt.
- **CI backstop** `scripts/check_task_artifacts.py` re-binds review.md to the PR diff hash.

## Form-window model vocabulary (use these names)
- **W1 live form / momentum:** `int_momentum_window__team` (selection) → `int_momentum__team`
  (aggregate) → `mart_momentum__team` + `mart_momentum_window__team`. `window_type` values:
  `last_5` (default), **`tournament_to_date`** + **`qualifiers`** (GAP-18, world+continental champ).
  Player path `int_momentum__player`/`mart_momentum__player` stays `last_5` (#484).
- **W2 season record:** `int_season_record__{team,player}` → `mart_season_record__{team,player}`;
  values `season_to_date` (UNTOUCHED — published key, frontend switches on it) + `prev_season`.
- Live WC label flag: `home/away_form_from_qualifiers` on `mart_matchday_insights` (= window_type
  'qualifiers') → the live `formContextLabel` UI + `formContextWc*` i18n. (#486.)

## Parked state (do not touch until directed)
- v2 blueprint drill-down (`form_window[]` ≤5 cap, separate `phase` column) — under #391 (PAUSED).
- Pilot PR2 slug rulings E2/E3 — BLINDED, do NOT pre-decide.
- Team market-value automation (#476 + #418) — new external-LLM source, needs a CPO cost gate.
- #477 historical/per-edition squad membership — needs a CPO cost gate.

## PENDING CPO ACTIONS (outside the tree — verify if done)
1. **Set `PROJECT_AUTOMATION_TOKEN`** to the fine-grained least-privilege scope (from #413).
2. **Remove now-unused secrets** `CURSOR_EXECUTOR_BRIDGE_URL` + `CURSOR_EXECUTOR_BRIDGE_TOKEN` (from #458).

## Do NOT
- **No blueprint/feature work while #391 is PAUSED** unless the CPO directs it.
- **Never decide CPO-class questions** (§10); escalate in PLAIN language (§11). Don't over-read one
  model and invent a §10; but DO escalate genuine layer/rule/scope/metric/naming questions.
- Do not compute/derive facts in the frontend/export (layering.md §Consumption) — select/group/rename only.
- Do not touch the live MVP UI logic without scope; do not change shipped numbers (GAP-17 parked).
- File edits via Edit/Write tools only — never shell redirection/heredocs (A5).
- Branch from main; never commit to main; the post-commit hook auto-pushes + opens PRs.
- **Never merge a PR — the CPO merges.**
- **Never print the API key** — mask it. **Reading `.env` is deny-listed.**
- **Bash only** for all commands (git, bq, gh, python) — never PowerShell.

## Environment notes
- dbt/sqlfluff from project `.venv` (`.venv/Scripts/dbt`, `.venv/Scripts/sqlfluff`) — the GLOBAL dbt is
  broken. BQ is a SHARED single environment (CI rebuilds from whichever branch built last; concurrent
  builds contend). dbt build uses BQ query bytes, NOT the API budget.
- **API budget (API-Football Ultra) = 75,000 calls/day, resets daily.** Pipeline runs once daily at
  04:00 UTC (empirically drifts to ~07:45–10:30 UTC). Skip-if-present loaders keep most runs cheap.
