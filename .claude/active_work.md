# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-17 (player performance-surface spec). Shipped this session: a long CPO design
conversation that produced the **player performance-surface spec — merged as #491** (main at 4a1a348).
It resolves the deferred player season surface: a new **§8 in `docs/metrics_context_model.md`** plus a
supersession pointer in `docs/player_metrics_catalogue.md`. Docs only — no models changed; it is the
spec that **#480** and **#484** build against. Governance G1–G4 LIVE. **Website blueprint #391 still
PAUSED.**_

## FIRST next session (do this first)
- Nothing pending-merge. #491 is merged; main is clean at 4a1a348. `git fetch` + ff to confirm. Then
  the CPO directs the next item (none auto-granted) — see NEXT.

## Standing authority (in force)
- **Per-item CPO-directed.** Run the full review cycle → open PR; **CPO merges**. Stop-conditions
  ALWAYS hold: never merge, escalate §10 (in PLAIN LANGUAGE), stop for cost/destructive.

## This session (2026-06-17) — player performance-surface spec (#491, MERGED)
A design conversation, not a build. Settled and recorded in **§8** (everything below is now spec, not
open):
1. **One aggregation, two windows.** The per-match player **leg** is the shared building block. Form and
   season are the SAME aggregation over a DIFFERENT set of legs — it never forks. Rules: sum counts; the
   four ratios (duels-won %, dribble-success %, pass-accuracy %, save %) are **weighted** (Σnum ÷ Σden,
   never an average of per-match %s); honest absence (only legs with provider stats count); zero
   denominator → `—` with counts shown. Display = **totals + the four weighted %s**, NOT per-match.
2. **What we show** = the nine CPO-locked player rows (`metrics_display.md`, 2026-06-11) + a NEW
   **appearance/playing-time context block**: two rows (apps·starts·subs; total min·avg-per-app) + last
   appearance in the window meta-line, **with the year** (`18 May 2026 vs Dortmund`). These are mart
   columns; the export only formats them.
3. **Season model** = ONE model, **per-club grain** (a transferred player → separate per-club line),
   within one competition, **this + last season side-by-side** (wide columns, not a second row). Full
   grain key `(player_sk, team_sk, league_code, season_sk)`. Replaces the three divergent rollups.
4. **Window matrix.** Club: the player's club form (last 5 across club comps; domestic = prev season
   before MD1, full after). **National = CONTEXT, not form** (strict club/national separation, never
   borrows club data): last ≤5 **national-team** appearances pooled across ALL NT comp types (friendlies
   once ingested), no season cap; **big tournament → cumulative ONLY** during & after; (future, when NT
   history ingested) career view grouped by NT comp type.
5. **Override** (CPO, logged): §8.5 supersedes the catalogue's "Form-window dispatch" (WC player form via
   the domestic club, qualifiers excluded). Reframe form→context dissolves its three (form-prediction)
   objections; football-analytics confirmed the football-correctness.
6. **No separate framing** — the existing locked window meta-line carries club-form vs national-context
   through its copy (final wording at i18n).
- **Review:** scope-auditor + analytics-engineer + football-analytics all PASS. Two analytics-engineer
  FAIL rounds were fixed at design altitude (surrogate key stated; NT selector forced into the
  intermediate layer with its national anchor; last-appearance declared a mart column not export logic;
  form_window_kind set shown derivable + final labels reserved to build) and re-reviewed clean.

## NEXT (CPO directs — none auto-granted)
- **#480** — build the ONE canonical per-club player-season model from §8 (applies the weighted
  aggregation; retires `mart_player_season` + the divergent rollups). **Changes shipped numbers** (e.g.
  pass accuracy → weighted) → its own validation; analytics-engineer + football-analytics on that PR.
- **#484** — build the national-team **context** window (a NEW national-anchored intermediate selector
  per §8.4 — not mart logic). **Changes shipped numbers** → its own validation.
- **Display-contract amendment** — record the appearance/playing-time block + the no-framing ruling into
  the locked `docs/wireframes/metrics_display.md` (bi-analyst-owned). Small follow-up.
- **Season-rollup enhancement (TEAM)** — point `mart_team_season` / `int_team_season` at the mapping
  spine so pre-season teams appear. DEFERRED from the dim_team work; a shipped-mart rows change, own
  validation. (The player analog is now specced as #480.)
- **#479** spare-budget backfill — DESIGN (per-comp history depth + budget ceiling).
- **#483** — GAP-18 follow-up (qualifying-type cumulative window).
- **Pilot PR2 (slugs)** — STILL BLOCKED on the two BLINDED §10 rulings E2/E3 (do NOT pre-decide).

## Player performance surface (the shape after this session — use these)
- **The spec is `docs/metrics_context_model.md` §8** + the supersession note in
  `docs/player_metrics_catalogue.md`. Definitions stay in the catalogue; locked display rows in
  `docs/wireframes/metrics_display.md`. Read §8 before any player-mart work.
- "Player season form / context" → §8 (one aggregation, per-club season model, club/national matrix),
  NOT the old three rollups. National player performance = **context** (NT appearances), never the
  domestic-club substitution (that catalogue rule is superseded).

## dim_team model (still current — from the prior session)
- **`dim_team`** = pure team ENTITY (one row per team_api_id; identity/venue only; **NO league_code**).
- **`dim_team_competition_season_mapping`** = team↔competition↔season membership (keys-only, fixtures-
  derived). "Teams in competition X, season Y" = the mapping (or fct_fixture), NEVER a dim_team column.

## Process lessons locked (do not repeat)
- **A reviewer FAIL on a non-§10 finding → fix + re-review, don't escalate.** This session the
  analytics-engineer FAILed twice on build-readiness gaps in a DESIGN spec (surrogate key, layer
  placement, mart columns, enum). Fix them **at design altitude** — state what's derivable, enforce
  existing layer rules, and RESERVE genuine build detail to the build PR — do NOT over-design a future
  PR inside the spec. If a reviewer keeps demanding build-level detail the contract scopes out, that
  altitude question is the CPO's call.
- **Read the existing docs before claiming a gap.** Early in the session I said "no clarity for players";
  reading `metrics_context_model.md` + `player_metrics_catalogue.md` showed live-form WAS specced and the
  real gap was only the season surface. Map the written design first.
- **Up-front CPO design approvals get logged**; communication compact + plain, lead with decisions + a
  bolded recommendation; no jargon in chat.

## The governance machinery (G1–G4 all LIVE — unchanged this session)
- **Contract first**: every unit writes `.claude/task/contract.md` (objective, scope_paths allowlist,
  decisions_reserved, done_when) on a CLEAN tree BEFORE code. `task_contract_gate.py` denies edits
  outside scope_paths / to PROTECTED paths (`.claude/hooks|agents|commands/`, `.github/workflows/`,
  `.claude/settings.json`, `.claude/review_routing.json`) without `protected_override`; and denies
  contract (re)writes on a dirty tree. `.claude/task/**` freely editable; `.claude/active_work.md` is
  NOT (needs scope_paths — as in this handover task).
- **4-step review cycle** (Code Lock → cold Blinding → Cross-Examination → SHA-256 Lock) in
  `.claude/task/review.md`. Reviewers routed by `.claude/review_routing.json` (scope-auditor always;
  dbt → analytics-engineer; scripts/tests/CI/hooks/agents/commands → cto; ingestion/registry-seed →
  data-engineer; wireframes/i18n → bi-analyst; metric_catalogue → +football-analytics). Plain `docs/**`
  (e.g. metrics_context_model.md) routes ONLY to scope-auditor — the CPO can direct extra reviewers
  (this session: +analytics-engineer +football-analytics). PASS needs ≥2 named risks; default FAIL. A
  reviewer FAIL on a §10 question → put it to the CPO in PLAIN language; record in review.md (VERDICT:
  ESCALATE + `CPO ANSWER:`) + escalations.log.
- **Commit gate** (`git_discipline.py`): `git commit` SOLE plain command; allowlisted flags only;
  staged SHA-256 must equal review.md `diff_sha256` (`python .claude/hooks/git_discipline.py
  --staged-hash`); required reviewers PASS, no FAIL, every ESCALATE has a CPO ANSWER. Artifact-only
  commits (`.claude/task/**` except contract.md, `.claude/active_work.md`) are review-exempt — but a
  commit that ALSO carries contract.md is never exempt (so this handover commit gets scope-auditor).
- **CI backstop** `scripts/check_task_artifacts.py` re-binds review.md to the PR diff hash.

## Form-window model vocabulary (use these names)
- **W1 live form / momentum:** `int_momentum_window__team` → `int_momentum__team` →
  `mart_momentum__team` + `mart_momentum_window__team`. `window_type`: `last_5` (default),
  `tournament_to_date` + `qualifiers` (GAP-18). Player path `int_momentum__player`/`mart_momentum__player`
  is still `last_5` — the player national/tournament context window is specced (§8.4) and built by #484.
- **W2 season record:** `int_season_record__{team,player}` → `mart_season_record__{team,player}`; values
  `season_to_date` (published key) + `prev_season`. The player season surface is now specced in §8 (#480).
- Live WC label flag: `home/away_form_from_qualifiers` on `mart_matchday_insights`.

## Parked state (do not touch until directed)
- v2 blueprint drill-down (`form_window[]` ≤5 cap, separate `phase` column) — under #391 (PAUSED).
- Pilot PR2 slug rulings E2/E3 — BLINDED, do NOT pre-decide.
- Team market-value automation (#476 + #418) — new external-LLM source, needs a CPO cost gate.
  (`mart_team_market_value` is the placeholder mart — value-less + unexported.)
- #477 historical/per-edition squad membership — needs a CPO cost gate (also feeds §8.4's future NT
  history-by-type view and friendlies in the NT pool).

## PENDING CPO ACTIONS (outside the tree — verify if done)
1. **Set `PROJECT_AUTOMATION_TOKEN`** to the fine-grained least-privilege scope (from #413).
2. **Remove now-unused secrets** `CURSOR_EXECUTOR_BRIDGE_URL` + `CURSOR_EXECUTOR_BRIDGE_TOKEN` (from #458).

## Do NOT
- **No blueprint/feature work while #391 is PAUSED** unless the CPO directs it.
- **Never decide CPO-class questions** (§10); escalate in PLAIN language (§11). Don't over-read one model
  and invent a §10; but DO escalate genuine layer/rule/scope/metric/naming questions.
- Do not compute/derive facts in the frontend/export (layering.md §Consumption) — select/group/rename only.
- Do not touch the live MVP UI logic without scope; do not change shipped numbers without a directed PR.
- File edits via Edit/Write tools only — never shell redirection/heredocs (A5). (Generated artifacts like
  review_input.patch via `git diff >` are the exception — bookkeeping, hash-excluded.)
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
