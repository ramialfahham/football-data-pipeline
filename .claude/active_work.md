# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-23 (**two-track operating model adopted** — see the next section). **Today:** deep #526
investigation. The wrong-team events are a provider **duplicate-team-id** quirk (6424 ASC Kara ↔ 25274 ASKO Kara;
2263 Riga FC ↔ 10124 Riga), and the data is **complete / uncorrupted** (raw=core: fixtures 63=63, events 731=731 — NO
loss). The clubs only LOOK thin because we ingest them solely via continental cups, not their domestic leagues. That
realisation seeded three program epics: **coverage expansion #545** (~146 missing domestic leagues; scoped — API-cheap,
real cost is DQ-at-scale), **data-quality routines #546** (seeded by #526), **cost optimization #547**. `stream:*`
labels + epics now structure the work. #526's own fix is **STILL OPEN** — decision pending on where/how to canonicalize
duplicate team ids (no canonicalization layer exists today). Prior merged: **#540** (impact-map gate, #518), **#542**
(#539 read-all staging codify), **#544** (#510 team-dribbles retire); **#510/#539 CLOSED**. main GREEN.
OPEN: #500/#506/#517/#521/#526 + program epics #545/#546/#547. Governance G1-G4 LIVE. **Website #391 PAUSED.**_

## How work is organized — two tracks (NEW 2026-06-23)
- **PRODUCT (primary track)** — the `docs/content_architecture.md` roadmap (entity pages, blocks, marts, the website).
  This is the GOAL; everything else is an enabler paced around it. Label `stream:product`.
- **PROGRAMS (enablers — pull in deliberately; never let them eclipse product):**
  - **Coverage expansion — #545** (`stream:coverage`): onboard the ~146 missing domestic leagues, phased by tranche
    (discover → onboard via registry zero-file → `verify-competition-ingest`, paired with a DQ sweep). API-cheap
    (~25-40k calls one-time vs 75k/day); **DQ-at-scale is the real cost**.
  - **Data-quality routines — #546** (`stream:data-quality`): a growing CI integrity-test suite + a scheduled DQ sweep
    across ALL leagues + the triage rule (diagnose-to-root → bounded fix or tracked issue → **never** coverage-cut).
    Seeded by #526.
  - **Cost optimization — #547** (`stream:platform`): BQ build-bytes / storage / materialisation, sized BEFORE the
    expansion lands.
- **One board + `stream:*` labels** group everything; the **CPO sets the per-stretch mix** (default = product).

## FIRST next session (do this first)
- **Nothing pending-merge** (`git fetch` + ff main). main GREEN.
- **PROGRAMS — pick the cut, then build:**
  - **#545 (coverage):** CPO picks the first tranche (by confederation, or highest-club-count-first). Then build that
    tranche's exact league list + `provider_league_id` discovery (**search-first** — 4 wrong IDs happened before),
    onboard (registry, zero-file), `verify-competition-ingest`.
  - **#546 (data-quality):** (a) land the **#526 fix — STILL OPEN**, decision pending on where/how to canonicalize the
    duplicate team ids. Map facts to resume from: NO team-canonicalization layer exists (`team_sk = cast(team_api_id)`,
    minted at ~8 points); the events carry a club's ALIAS id while the fixture uses its canonical id; a global merge
    would break 4 legit events unless the fixtures are canonicalized too; CPO said **"not core"** — fix at team
    identity (base), not a fct patch. The complete map is in #526's thread. (b) Generalise the #526 detection into the
    standing DQ scan (template for the class).
  - **#547 (cost):** size BQ build cost before the expansion scales.
- **PRODUCT (primary):** the content_architecture roadmap — **coaches + `mart_player_career`** (unblocked), player
  **benchmark / opponent-context** (v1.x), carryovers **#500** (team season-model consolidation + rename) / **#506**
  (leaderboards rate boards). **Read `docs/content_architecture.md` §8/§9 first.**
- **#521** (phantom-current-season parity — `history_seasons`+1, a registry depth decision; deferred, NOT a fetch gap).
- **To backfill a league (post-#520):** set its `history_seasons` in the registry — AUTHORITATIVE, no V1 cap —
  then run a `full`-profile scoped ingest (`LEAGUE_CODES=<code>`, `INGEST_FORCE_FULL=1`, `LOG_QUOTA=1`), measure
  the call delta, verify RAW depth, then `verify-competition-ingest`.
- **Cost reality (locked):** deep backfills are ~10x cheaper than `fixtures × 4` estimates — the per-fixture
  sub-endpoints batch ~20 fixtures/call (the `ids` param), so a season's fanout is ~fixtures/20 × 4, not
  fixtures × 4. (PL was ~3k not ~10.7k partly for this + pre-existing details.)
- The **dbt MCP server** cold-start race may recur — see [[project-dbt-mcp-server]].

## This session (2026-06-21) — deep-backfill DQ heal (#527) + Phase 2a depths (#524)
- **#527 (MERGED) — the complete, bounded deep-backfill DQ fix.** The PD/SA/L1 + partial Phase 2a deep data
  (2016-era) surfaced 3 DQ failures; enumerated the FULL defect set from RAW via one clean build (bounded:
  ~15 fixable rows; recent seasons 0 dupes / 280k+ legs). Fixes: (a) **events** — recover null `team_id` in
  base_apif__fixture_events from the same team's other events in the fixture (by name), + a SELF-HEAL clause in
  fct_fixture_event's incremental filter to reach already-committed null rows; (b) **standings** — removed the
  mis-placed `not_null` on FAITHFUL `stg_apif__standings.team_id` (the provider legitimately leaves it null in
  old data); cleanliness stays guarded at base + `fct_standings.team_sk`; (c) **player id-collision** — provider
  reused one `player_id` for two players in a fixture; extended base_apif__fixture_players's phantom-leg cleanup
  to drop real-id collisions, + a one-time CPO-authorized `--full-refresh` of fct_fixture_player_stats to heal
  the 4 committed rows (merge can't delete; verified 0 remaining). Both reviewers PASS.
- **#524 (MERGED) — Phase 2a registry §8 depths.** 15 `history_seasons` lines (7 domestic 2->5, 8 continental-
  club 5->10). Registry-only; rebased on the #527-healed main (sibling-PR rebase: only `.claude/task/*` conflicted;
  registry replayed byte-identical; review hash rebound; collapsed to one commit — [[feedback-sibling-pr-rebase-rebind]]).
- **Process lesson (locked, #518 updated):** I first framed the old-data DQ failures as "older data is messier"
  and floated PULLING BACK ingest depth as the "fix". CPO: *"the fix is not fixing it but just not ingesting it."*
  **A failing DQ test is a defect to fix, NEVER a reason to ingest less; COUNT the offending rows in RAW before
  any "messier data / skip it" framing** ([[feedback-no-hacky-solutions]]).

## Standing authority (in force)
- **Per-item CPO-directed.** Run the full review cycle → open PR; **CPO merges**. Stop-conditions
  ALWAYS hold: never merge, escalate §10 (in PLAIN LANGUAGE), stop for cost/destructive.

## This session (2026-06-20) — #414 closed, PL backfill, season-depth config refactor
- **#414 closed obsolete (premise-check, §11).** The "supporting_leagues guard checks an unused
  competition_type" DQ bug targeted a mechanism RETIRED by #429/#430 — the guard, the registry keys, and the
  silent-drop path no longer exist; form selection is now taxonomy-driven (validated by
  assert_tournament_form_window.sql). Surfaced the stale premise, CPO chose to close. Residual noted
  (empty-tournament-window loudness) -> GAP-18/#483 cluster, not #414.
- **PL deep-season backfill DONE.** Two `full`-profile scoped runs: run1 restored the thin fixtures snapshot
  (2017-2026; details pre-existed in RAW, ~1.8k calls); run2 (post-refactor) fetched 2016 (~1.2k). PL RAW now
  **2016-2026, 10 finished seasons (2016-2025) = BL1 parity**, all 4 fanout endpoints 100% covered. Total ~3k
  calls — over-estimated at ~10.7k because the per-fixture details already lived in RAW (the thin snapshot
  masked them; [[feedback-raw-staging-latest-payload]]). **PD/SA/L1 are NOT pre-existing → ~12k each.**
- **#520 (MERGED) — season-depth config refactor (Path A).** Per-competition `history_seasons` is now the
  AUTHORITATIVE depth knob in `seasons._seasons_for_ingestion`: `lo = resolved_current - (history_seasons-1)`,
  the old `max(global_lo, …)` clamp DROPPED (deterministic depth, can exceed the old 10-yr ceiling); the
  default window applies only when history_seasons is unset. Retired the v1 artifact:
  `V1_SEASON_WINDOW_YEARS` -> `DEFAULT_SEASON_WINDOW_YEARS`. Economy/MAX_SEASONS cap unchanged. PL hs 10->11
  (offsets provider current=2026, one ahead of BL1's 2025). 2 regression tests; 282 pass; 3 reviewers PASS.
- **#521 (FILED)** phantom-current-season hardening (anchor depth to the latest FINISHED season) — deferred,
  separable; would let PL use hs=10 like BL1.
- **Process note (locked):** I first mis-framed the 2016 fix as needing a global v1-constant bump; the CPO
  pushed back ("shouldn't be rocket science"); re-derived from seasons.py — it was a 1-line hs + clamp removal.
  HOLD a defensible position when challenged, but re-derive from the CODE, not the lean ([[feedback-no-hacky-solutions]]).

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
1. **Backfill** (#479) — **PL + PD/SA/L1 DONE (2016-2025 finished = BL1 parity; #523, 2026-06-21); config
   robust (#520).** Phase 2a registry §8 depths MERGED (#524) but the deep INGEST was STOPPED partway →
   **RESUME** for the leagues not yet at depth (8 continental-club → 10, 7 domestic → 5; see FIRST-next-session).
   Then **Phase 2b** (national-team tournaments + qualifiers; DEFERRED — per-cadence editions/cycle mapping).
   Recipe: set `history_seasons` (authoritative post-#520) + `full`-profile scoped run + verify RAW. Cost-gated;
   ~10x cheaper than `fixtures × 4` (batched sub-endpoints).
2. ~~**`mart_leaderboards`** + **`mart_roster`**~~ — **DONE 2026-06-19** (#503 roster, #507 composites, #508 mart
   + full consolidation). The 5 rate boards + the qualification floor are deferred → **#506**.
3. ~~**`mart_competition_benchmarks`** (team)~~ — **TEAM DONE 2026-06-19** (#511 direction/interpretation
   semantic + #512 mart_competition_benchmarks__team; median-led, rank-of-N, direction-agnostic). **Player
   benchmark + percentile-vs-peers = v1.x** (needs per-90 — a NEW catalogue metric — + position-aware peers +
   a minutes floor). The **opponent/schedule-context flagship** (weights opponents via this engine) is also v1.x.
4. **Coaches ingest + `dim_coach`**; **`mart_player_career`** (on the backfill) for the Career/History tabs.

### Carryovers (also open, CPO directs)
- **#484** — player national/tournament **context** window (a NEW national-anchored intermediate selector
  per §8.4 — NOT mart logic). Changes shipped numbers → own validation.
- **Team season-record ↔ rollup unification + naming (#500)** — the team-side analog of #480 (the season
  record's final row == the rollup; they're one aggregation), bundled with the model-naming fix
  (`int_team_season__full_season_metrics` → `int_team_season__metrics`). Now tracked as **#500**. NOTE: the
  benchmark (#512) now also reads this model — the rename updates its refs too.
- **#510** — retire leftover team `dribbles_success_pct` (catalogue row + the `mart_momentum__team` computation
  + the range test; a player metric ruled dropped team-side 2026-06-11, never fully cleaned up).
- **Team season-rollup enhancement** — point `mart_team_season`/`int_team_season` at the mapping spine so
  pre-season teams appear (deferred from the dim_team work).
- **Display-contract amendment** — record the appearance/playing-time block + the no-framing ruling into
  the locked `docs/wireframes/metrics_display.md` (bi-analyst-owned).
- **#483** — qualifying-type cumulative window (GAP-18 follow-up).
- **#506** — leaderboards v1.x: the 5 RATE boards (pass% / duels% / dribble% / save% / finishing) + a new
  `finishing_efficiency` (uncapped) + the per-denominator qualification floor (deferred from the v1 count boards).
- **Pilot PR2 (slugs)** — STILL BLOCKED on the two BLINDED §10 rulings E2/E3 (do NOT pre-decide).

## Key specs to read before building (the source of truth)
- **`docs/content_architecture.md`** — blocks/tabs/navigation, entity types, block↔mart map, flagship
  reads, new-mart list, backfill policy. The engine spec.
- **`docs/metrics_context_model.md` §8** — the player performance surface (windows + aggregation).
- `docs/player_metrics_catalogue.md` + `docs/wireframes/metrics_display.md` — metric defs + locked display.
- Player season agg is now ONE model: `int_player_season__metrics` → `mart_player_profile` +
  `mart_leaderboards` (`mart_player_season` was RETIRED in #508). Do NOT re-introduce inline player-season aggregation.

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
- **Size the solution to the need** ([[feedback-no-hacky-solutions]]): don't over-build (the reverted
  metric-layer conformance engine) and don't hack (a flag-to-ignore instead of the principled fix).
  Before building any mechanism, ask what it buys over the simplest thing + what is already solved.
- **Don't over-produce docs** ([[feedback-doc-clutter-discipline]]): Rami flagged `.md` clutter — default to NOT
  creating a new doc; fold into the authoritative one or keep it in the PR/issue. #505 tracks the docs/ audit.
- **Reviewer-driven scope amendment** (PR1 + 2b this session): when a reviewer FAIL's fix needs a NEW file (an
  upstream DQ test; a stale-ref doc), it is a clean-tree contract amendment — stash the code changes, edit
  contract.md (authority = the FAIL + standing rule), unstash, fix, re-review. A mart's SELECT must exactly
  match its documented `shared.yml` columns (the analytics-engineer hunts undocumented columns every round).

## The governance machinery (G1–G4 LIVE; + the #518 impact-map gate, PR #540)
- **Contract first**: every unit writes `.claude/task/contract.md` (objective, scope_paths, decisions,
  done_when) on a CLEAN tree BEFORE code. `task_contract_gate.py` denies edits outside scope_paths / to
  PROTECTED paths without `protected_override`; denies contract (re)writes on a dirty tree. `.claude/task/**`
  freely editable; `.claude/active_work.md` is NOT (needs scope_paths — as in this handover task).
- **Impact-map gate (#518/#540, NEW)**: `task_contract_gate.py` also denies the first edit on the
  **structural surface** (`ingestion/**`, `dbt_project/models/**`, `scripts/export_*.py`, `site*/`) until the
  contract carries a non-placeholder `impact_map` (writers + lineage + layer rules + deploy ordering + blast
  radius; evidence, not assertion). Presence-gated; the routed reviewers judge honesty (they hunt the map +
  coverage-cut "fixes"). Anti-pattern named in `working_agreement.md` Appendix A6. Trivial edits = one-line
  short-form. Limit: Edit/Write path only (not shell writes).
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
