# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-17 (dim_team entity/affiliation split). Shipped this session: verified GAP-18
live on main (WC tournament/qualifier form correct); then the **dim_team entity/affiliation split —
COMPLETE in two merged PRs**. **#488** (Phase 1: new `dim_team_competition_season_mapping`,
fixtures-derived team↔competition↔season membership; the BL1/BL2 directory bug fixed at root) and
**#489** (Phase 2: dropped `dim_team.league_code` → `dim_team` is a pure entity; repointed
`mart_team_market_value`). Both merged, ci-data-build green; main at 8f5d88e. Governance G1–G4 LIVE.
**Website blueprint #391 still PAUSED.**_

## FIRST next session (do this first)
- Nothing pending-merge. Both dim_team PRs are merged; main is clean at 8f5d88e. `git fetch` + ff to
  confirm. Then the CPO directs the next item (none auto-granted) — see NEXT.

## Standing authority (in force)
- **Per-item CPO-directed.** Run the full review cycle → open PR; **CPO merges**. Stop-conditions
  ALWAYS hold: never merge, escalate §10 (in PLAIN LANGUAGE), stop for cost/destructive.

## This session (2026-06-17) — dim_team entity/affiliation split
1. **Verified GAP-18 live (read-only, no cost).** On main: `int_momentum_window__team` carries
   window_type `tournament_to_date`/`qualifiers`; `mart_matchday_insights` carries
   `home/away_form_from_qualifiers`. Live WC MD1 fixtures show cumulative qualifier windows (6–18 games,
   not capped at 5), `form_from_qualifiers=true` for every opener team — the live label is right.
2. **Root-caused the dim_team BL1/BL2 watch-item (read-only).** NOT an ingestion gap — raw HAS BL1/BL2
   /teams. `dim_team.league_code` was a latest-ingest provenance stamp (one row per team, latest /teams
   payload wins) → all 19 BL1 + 19 BL2 clubs present but stamped DFBP (German Cup ingested 06-16, after
   the leagues' 06-10). Latent for every league (PL survived only by ingest timing). Live preview
   unaffected (reads league_code from fixtures). **The prior handover's "feed never landed" guess was WRONG.**
3. **CPO design session → fix = mirror the player entity/affiliation split.** Built in two phases:
   - **Phase 1 (#488, MERGED):** `dim_team_competition_season_mapping` — keys-only core relationship
     (mapping) dim, grain (team_sk, league_code, season_api_year), derived from FIXTURES (incl. scheduled),
     grain enforced by GROUP BY. Membership source = fixtures (NOT the /teams roster) because a team
     always plays what it enters (no never-played gap like a player). Bidirectional `fct_fixture`
     consistency test + FK relationships. Validated: BL1/BL2 = 19/19; multi-comp clubs (Bayern/Dortmund)
     now under BL1+DFBP+UCL+CWC.
   - **Phase 2 (#489, MERGED):** dropped `dim_team.league_code` → `dim_team` is a pure entity (mirrors
     `dim_player`); repointed the ONLY consumer (`mart_team_market_value`: WC set 23→48, output schema
     preserved; mart unexported + empty so structural-only). core.yml + layering.md updated.
4. **Governance ruling E1 (escalations.log 2026-06-17):** up-front CPO design approvals are LOGGED in
   escalations.log alongside review-time rulings (not only in contract decisions_taken). Both PRs' design
   + review rulings are recorded there.

## NEXT (CPO directs — none auto-granted)
- **Season-rollup enhancement** — point `mart_team_season` / `int_team_season` at the new mapping spine so
  upcoming-only (pre-season) teams appear. DEFERRED from Phase 2 (it's a shipped-mart rows change; needs
  its own validation). Small, well-scoped.
- **#480** player-season consolidation — GOVERNED (reconcile divergent metric defs FIRST; changes shipped numbers).
- **#479** spare-budget backfill — DESIGN (per-comp history depth + budget ceiling).
- **#483 / #484** — GAP-18 follow-ups (qualifying-type cumulative window; player-strip tournament form).
- **Pilot PR2 (slugs)** — STILL BLOCKED on the two BLINDED §10 rulings E2/E3 (do NOT pre-decide).

## dim_team model (the shape after this session — use these)
- **`dim_team`** = pure team ENTITY (one row per team_api_id; identity/venue only; **NO league_code**, no
  affiliation). Mirrors `dim_player`.
- **`dim_team_competition_season_mapping`** = team↔competition↔season membership (keys-only, fixtures-
  derived, grain (team_sk, league_code, season_api_year)). Mirrors `dim_player_team_season_mapping`.
- **"Teams in competition X, season Y" = the mapping (or fct_fixture), NEVER a dim_team column.** See
  memory `project_team_model_redesign`.

## Process lessons locked (do not repeat)
- **Verify the handover's stated root cause before building on it.** The BL1/BL2 "feed never landed" guess
  was wrong; read-only investigation found the real cause (provenance-stamp dedup). Map the system; don't
  inherit a guess.
- **A reviewer FAIL on a non-§10 finding → fix + re-review, don't escalate.** Phase 1's analytics-engineer
  FAILs (near-circular test, grain-on-untested-assumption) were code fixes (bidirectional cross-model
  test; GROUP BY-enforced grain), not CPO questions.
- **Up-front CPO design approvals get logged** (E1) — escalations.log records them, not just contract.md.
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
  `last_5` (default), `tournament_to_date` + `qualifiers` (GAP-18, world+continental champ).
  Player path `int_momentum__player`/`mart_momentum__player` stays `last_5` (#484).
- **W2 season record:** `int_season_record__{team,player}` → `mart_season_record__{team,player}`;
  values `season_to_date` (UNTOUCHED — published key) + `prev_season`.
- Live WC label flag: `home/away_form_from_qualifiers` on `mart_matchday_insights` → the live
  `formContextLabel` UI + `formContextWc*` i18n.

## Parked state (do not touch until directed)
- v2 blueprint drill-down (`form_window[]` ≤5 cap, separate `phase` column) — under #391 (PAUSED).
- Pilot PR2 slug rulings E2/E3 — BLINDED, do NOT pre-decide.
- Team market-value automation (#476 + #418) — new external-LLM source, needs a CPO cost gate.
  (`mart_team_market_value` is the placeholder mart — repointed in Phase 2 but still value-less + unexported.)
- #477 historical/per-edition squad membership — needs a CPO cost gate.

## PENDING CPO ACTIONS (outside the tree — verify if done)
1. **Set `PROJECT_AUTOMATION_TOKEN`** to the fine-grained least-privilege scope (from #413).
2. **Remove now-unused secrets** `CURSOR_EXECUTOR_BRIDGE_URL` + `CURSOR_EXECUTOR_BRIDGE_TOKEN` (from #458).

## Do NOT
- **No blueprint/feature work while #391 is PAUSED** unless the CPO directs it.
- **Never decide CPO-class questions** (§10); escalate in PLAIN language (§11). Don't over-read one model
  and invent a §10; but DO escalate genuine layer/rule/scope/metric/naming questions.
- Do not compute/derive facts in the frontend/export (layering.md §Consumption) — select/group/rename only.
- Do not touch the live MVP UI logic without scope; do not change shipped numbers (GAP-17 parked).
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
