# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-18 (dbt MCP server — a CPO-directed tooling detour off a LinkedIn post). Merged
**#497**: a read-only dbt MCP server (`.mcp.json`, local-manifest lineage) + MCP config classified
PROTECTED command-class. main at dff05d7. The prior session's product work (#491 spec, #493 content
architecture, #494/#480 player-season) is the roadmap below — UNCHANGED. Governance G1–G4 LIVE.
**Website blueprint #391 still PAUSED.**_

## FIRST next session (do this first)
- Nothing pending-merge. `git fetch` + ff to confirm (main dff05d7). The **dbt MCP server is LIVE** — it
  loads on session start, so this fresh session should have `mcp__dbt__get_lineage_dev` /
  `get_node_details_dev` (read-only local-manifest lineage; refresh with `dbt parse` if stale). Then the
  CPO directs the next item (none auto-granted) — see NEXT. **Read `docs/content_architecture.md` first** —
  it is the IA + data spec everything below builds against.

## Standing authority (in force)
- **Per-item CPO-directed.** Run the full review cycle → open PR; **CPO merges**. Stop-conditions
  ALWAYS hold: never merge, escalate §10 (in PLAIN LANGUAGE), stop for cost/destructive.

## This session (2026-06-18) — dbt MCP server (CPO-directed tooling detour)
- **#497 (MERGED) — read-only dbt MCP server + MCP-config protection.** Prompted by a LinkedIn post on dbt
  Labs "Wizard"; the one real gap it named for us was **edit-time lineage/impact analysis** (the rest —
  validation loop, skills — we already have, often stricter). `.mcp.json` runs `uvx --python 3.12.13
  dbt-mcp` with a read-only allowlist (`DBT_MCP_ENABLE_TOOLS=get_lineage_dev,get_node_details_dev,list,parse`)
  — **no warehouse tools, no dbt Cloud, dbt stays 1.7.19** (dbt-mcp shells out; no forced upgrade). The
  cto-reviewer caught a real bug pre-merge (the group-enable + allowlist combo leaked all 11 CLI tools incl.
  build/run/test) → fixed to allowlist-only, live-verified exactly 4 tools + dim_date lineage.
- **§10 ruling (2026-06-18):** `.mcp.json` / `.cursor/mcp.json` are **PROTECTED command-class** (they
  auto-launch a command each session, like `.claude/commands/`) — in `task_contract_gate.py` PROTECTED_FILES
  + routed to cto-reviewer (opus floor). No agent self-grants an MCP server in an ordinary task. Memory:
  [[project-dbt-mcp-server]]. `.cursor/mcp.json` path is protected but NOT created (Cursor config deferred).

## Product roadmap (merged 2026-06-17 — the basis for NEXT below; UNCHANGED this session)
1. **#491 (MERGED) — player performance-surface spec** (`metrics_context_model.md` §8): one aggregation /
   two windows over the per-match leg; the 9 locked rows + an appearance/playing-time block; one per-club
   season model; club/national window matrix with **national = context** (last-5 NT appearances pooled;
   big-tournament cumulative); overrides the catalogue's domestic-substitution dispatch.
2. **#493 (MERGED) — `docs/content_architecture.md`**, the modular IA: **blocks (1 block = 1 mart) → tabbed
   entity pages → navigation graph.** Entity types (Competition, Team, Player, Fixture rich; Matchday,
   Coach thin). Block library + block↔mart map. Flagship reads (below). New-mart list + the backfill
   policy. Cross-linked from `site_architecture.md` + `metrics_context_model.md` §8.
3. **#494/#480 (MERGED) — player-season consolidation.** One shared `int_player_season__metrics`; both
   `mart_player_profile` (byte-identical) and `mart_player_season` compose it; the orphan's logic promoted;
   `mart_player_season` pass accuracy corrected naive-avg → **weighted** (was unconsumed). Kept today's
   grain; the per-club split + side-by-side + appearance block are the deferred §8.3 follow-up.
4. **Flagship reads (CPO-LOCKED):** **deserved-vs-actual** + **vs-own-history (YoY)** = v1; **opponent /
   schedule context** = v1.x (hardest, football-analytics-owned); **contribution-share** = bonus.
   **Vs-benchmark/percentile = the supporting ENGINE, not a flagship** (it's table stakes — kicker/fbref
   both do it). No xG — deserved-vs-actual uses our chance-quality metrics.
5. **Backfill depth policy (CPO-agreed):** tiered — top leagues 10 seasons / 2nd-tier + smaller 5 /
   continental club 10 / world+continental championships last 4 editions / qualifiers current+previous
   cycle / cups 5 — + a data-quality floor (skip empty-player-stat seasons) + phased rollout.

## NEXT — the content_architecture build sequence (CPO directs; none auto-granted)
1. **Backfill** — set per-competition `history_seasons` in `docs/competition_registry.yml` (the agreed
   tiered policy) + run it. Cost-gated ingest (data-engineer); uses spare API budget + BQ. Lights up
   History/Career, makes season-over-season real, deepens benchmarks. (This is #479's territory.)
2. **`mart_leaderboards`** (generalise `mart_top_scorers` to any catalogue metric) + **`mart_roster`**
   (from the team↔player mapping) — cheap, high navigability/SEO, no governance.
3. **`mart_competition_benchmarks`** (team+player) — the flagship engine; UNBLOCKED now (#480 gave a clean
   season aggregation). Percentile def → metric_catalogue + football-analytics (position-aware = v1.x).
4. **Coaches ingest + `dim_coach`**; **`mart_player_career`** (on the backfill) for the Career/History tabs.

### Carryovers (also open, CPO directs)
- **#484** — player national/tournament **context** window (a NEW national-anchored intermediate selector
  per §8.4 — NOT mart logic). Changes shipped numbers → own validation.
- **Team season-record ↔ rollup unification** — the team-side analog of #480 (the season record's final
  row == the rollup; they're one aggregation). Latent consolidation.
- **Team season-rollup enhancement** — point `mart_team_season`/`int_team_season` at the mapping spine so
  pre-season teams appear (deferred from the dim_team work).
- **Display-contract amendment** — record the appearance/playing-time block + the no-framing ruling into
  the locked `docs/wireframes/metrics_display.md` (bi-analyst-owned).
- **#483** — qualifying-type cumulative window (GAP-18 follow-up).
- **Pilot PR2 (slugs)** — STILL BLOCKED on the two BLINDED §10 rulings E2/E3 (do NOT pre-decide).

## Key specs to read before building (the source of truth)
- **`docs/content_architecture.md`** — blocks/tabs/navigation, entity types, block↔mart map, flagship
  reads, new-mart list, backfill policy. The engine spec.
- **`docs/metrics_context_model.md` §8** — the player performance surface (windows + aggregation).
- `docs/player_metrics_catalogue.md` + `docs/wireframes/metrics_display.md` — metric defs + locked display.
- Player season agg is now ONE model: `int_player_season__metrics` → `mart_player_profile` +
  `mart_player_season`. Do NOT re-introduce inline player-season aggregation.

## dim_team model (still current — from the prior session)
- **`dim_team`** = pure team ENTITY (one row per team_api_id; identity/venue only; **NO league_code**).
- **`dim_team_competition_season_mapping`** = team↔competition↔season membership (keys-only, fixtures-
  derived). "Teams in competition X, season Y" = the mapping (or fct_fixture), NEVER a dim_team column.

## Process lessons locked (do not repeat)
- **Design-spec review altitude** ([[feedback-design-spec-altitude]] in memory): on a reviewer FAIL of a
  DESIGN spec, fix design-level gaps + RESERVE genuine build detail to the build PR; don't over-design a
  future PR or chase the build-readiness treadmill.
- **Sibling-PR rebase recovery** ([[feedback-sibling-pr-rebase-rebind]] in memory): when a sibling PR
  merges first, the `.claude/task/*` scratch files conflict (every task rewrites them) — rebase keeps the
  CODE clean; but contract.md is HASHED, so its diff-base shift moves the review hash → rebind review.md
  to the recomputed value (artifact-only commit); and **collapse a multi-commit branch to ONE commit**
  (`git reset --soft origin/main` → re-stage → commit once) so the staged hash == the PR diff the gate
  expects. Force-push the feature branch with `--force-with-lease`.
- A reviewer FAIL on a non-§10 finding → fix + re-review, don't escalate. Read the existing docs before
  claiming a gap. Communication: compact + plain, lead with decisions + a bolded recommendation.

## The governance machinery (G1–G4 all LIVE — unchanged)
- **Contract first**: every unit writes `.claude/task/contract.md` (objective, scope_paths, decisions,
  done_when) on a CLEAN tree BEFORE code. `task_contract_gate.py` denies edits outside scope_paths / to
  PROTECTED paths without `protected_override`; denies contract (re)writes on a dirty tree. `.claude/task/**`
  freely editable; `.claude/active_work.md` is NOT (needs scope_paths — as in this handover task).
- **4-step review cycle** (Code Lock → cold Blinding → Cross-Examination → SHA-256 Lock) in `review.md`.
  Reviewers routed by `.claude/review_routing.json` (scope-auditor always; dbt → analytics-engineer;
  scripts/tests/CI/hooks/agents/commands → cto; ingestion/registry-seed → data-engineer; wireframes/i18n →
  bi-analyst; metric_catalogue → +football-analytics). Plain `docs/**` routes ONLY to scope-auditor — the
  CPO can direct extra reviewers (this session: +analytics-engineer, +bi-analyst on the IA doc). PASS needs
  ≥2 named risks; default FAIL. Reviewer FAIL on a §10 → put to CPO in PLAIN language (review.md + log).
- **Commit gate** (`git_discipline.py`): `git commit` SOLE plain command; allowlisted flags only
  (message/quiet/verbose/sign — NOT --amend); staged SHA-256 must equal review.md `diff_sha256`
  (`python .claude/hooks/git_discipline.py --staged-hash`); required reviewers PASS, no FAIL, every
  ESCALATE has a CPO ANSWER. Artifact-only commits (`.claude/task/**` except contract.md, `active_work.md`)
  are review-exempt — but a commit that ALSO carries contract.md is never exempt. The gate assumes ONE
  substantive commit per PR (staged == PR diff); collapse multi-commit branches before committing.
- **CI backstop** `scripts/check_task_artifacts.py --base origin/main` re-binds review.md to the PR diff.

## Form-window model vocabulary (use these names)
- **W1 live form / momentum:** `int_momentum_window__team` → `int_momentum__team` → `mart_momentum__team`
  (+ `mart_momentum_window__team` drill-down). window_type: `last_5` / `tournament_to_date` / `qualifiers`.
  Player path `int_momentum__player`/`mart_momentum__player` is still `last_5`; player NT/tournament context
  window is specced (§8.4) and built by #484.
- **W2 season record:** `int_season_record__{team,player}` → `mart_season_record__{team,player}`
  (`season_to_date` + `prev_season`). **Player full-season agg is now `int_player_season__metrics`** (#480).

## Parked state (do not touch until directed)
- v2 blueprint drill-down — under #391 (PAUSED).
- Pilot PR2 slug rulings E2/E3 — BLINDED, do NOT pre-decide.
- Team market-value automation (#476 + #418) — new external-LLM source, CPO cost gate.
- #477 historical/per-edition squad membership — overlaps the backfill (NEXT #1) + the Career/History tabs.

## PENDING CPO ACTIONS (outside the tree — verify if done)
1. **Set `PROJECT_AUTOMATION_TOKEN`** to the fine-grained least-privilege scope (from #413).
2. **Remove now-unused secrets** `CURSOR_EXECUTOR_BRIDGE_URL` + `CURSOR_EXECUTOR_BRIDGE_TOKEN` (from #458).

## Do NOT
- **No blueprint/feature work while #391 is PAUSED** unless the CPO directs it.
- **Never decide CPO-class questions** (§10); escalate in PLAIN language (§11). Don't over-read one model
  and invent a §10; but DO escalate genuine layer/rule/scope/metric/naming questions.
- Do not compute/derive facts in the frontend/export (layering.md §Consumption) — select/group/rename only.
- Do not change shipped numbers without a directed PR + before/after deltas + reviewer sign-off.
- File edits via Edit/Write tools only — never shell redirection/heredocs (A5). (Generated artifacts like
  review_input.patch via `git diff >` are the exception — bookkeeping, hash-excluded.)
- Branch from main; never commit to main; the post-commit hook auto-pushes + opens PRs.
- **Never merge a PR — the CPO merges.**
- **MCP config (`.mcp.json` / `.cursor/mcp.json`) is PROTECTED** — editing needs `protected_override` + cto
  review; keep the dbt server's tool allowlist READ-ONLY (never enable build/run/test — they hit BQ and
  bypass the cost guard).
- **Never print the API key** — mask it. **Reading `.env` is deny-listed.**
- **Bash only** for all commands (git, bq, gh, python) — never PowerShell.

## Environment notes
- dbt/sqlfluff from project `.venv` (`.venv/Scripts/dbt`, `.venv/Scripts/sqlfluff`) — the GLOBAL dbt is
  broken. Run dbt with `--project-dir dbt_project --profiles-dir "$HOME/.dbt"` to avoid cd prompts. BQ is a
  SHARED single environment (CI rebuilds from whichever branch built last; a local `dbt build` clobbers the
  shared marts — rely on ci-data-build on the PR). dbt build uses BQ query bytes, NOT the API budget.
- **API budget (API-Football Ultra) = 75,000 calls/day, resets daily** — largely unused, so the backfill
  (NEXT #1) is affordable. Pipeline runs once daily at 04:00 UTC (drifts ~07:45–10:30). Skip-if-present
  loaders keep most runs cheap.
- **dbt MCP server (read-only lineage)** wired in `.mcp.json` — `uvx --python 3.12.13 dbt-mcp`, loads on
  session start. `uv` is installed (global Python311 Scripts) + Python 3.12.13 cached. Tools:
  `get_lineage_dev` / `get_node_details_dev` / `list` / `parse` (local manifest only — as fresh as the last
  `dbt parse`, which is offline/free; does NOT touch BigQuery or the API budget). MCP config is PROTECTED.
