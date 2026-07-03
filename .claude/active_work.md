# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: **2026-07-03** — main GREEN at **a08c634**. **#645 MERGED: Phase D bonus — player contribution-share** — NEW `int_player_profile__contribution` (4_intermediate/shared, table): a player's goal-involvement share of the club's WHOLE-SEASON goals ("involved in X% of the club's goals"). Composing intermediate over `int_legs__player_match` + `int_legs__team_match` (atoms not recomputed; mirrors `int_team_season__deserved_vs_actual`); grain (player_sk, team_sk, season_sk); NOT domestic-restricted; NULL where the club scored 0; invariant 0 ≤ share ≤ 1. Composed into `mart_player_profile` via the primary club; auto-carries `scorer_points` + `team_goals_season` + `contribution_share` to the v2 player export via `select *` (#606). Catalogued `contribution_share` (BLANK base_relation — the deserved_rank/sot_rank_gap pattern; entity=player, format=percent, **direction=NEUTRAL**, metric_group=goals). CPO definition (AskUserQuestion 2026-07-03, escalations.log): numerator = goal involvements (goals + assists = the existing `scorer_points`); denominator = the club's whole-season goals_for. Honest limit (CPO-accepted, prose only): the share understates where the player's per-match stats are missing. **Player streaks (Phase C brick 2) is SKIPPED (CPO, 2026-07-03).** Prior: **#638 MERGED: Phase C brick 1** — the player year-over-year model `int_player_profile__yoy` (the player mirror of the shipped team YoY `int_team_profile__yoy`) on `int_player_season_record` (per-club, appearance-aligned, domestic-leagues only) with this-season-vs-last deltas for goals/assists/shots_on_goal/key_passes/defensive_actions (CPO "broader per-position set"); composed into `mart_player_profile` via the primary club; auto-carries to the player export via `select *`. **PLUS the portfolio arc #640–#643 MERGED** (public repo = Rami's job-application portfolio, [[project-repo-portfolio]]): README funnel + badges + architecture diagram (#640), MVP screenshot (#641), Design-decisions section (#642), and a **public dbt docs lineage site at `/dbt-docs/`** folded into the existing Pages deploy (#643, best-effort continue-on-error `dbt docs generate --static` step). **⭐ KEY FINDING this session: the history backfill is effectively DONE** — RAW + `mart_player_career` are **5–10 seasons deep** across every domestic league (top-5 Euro at 10, smaller leagues at 5); the "thin-until-backfill" premise was **STALE**. Remaining gaps marginal (VL/CNL at 2, some tournaments at 1 edition, a few continental at 5–9) — low value, a §10 cost call only if wanted. Prior: #636 doc-sync reconciliation; Career chain WIRED end-to-end (#630/#632/#634). **#391 stays UN-PAUSED, NARROW + DATA-FIRST** (CPO). **NEXT = a CPO pick** (nothing locked): **Phase D flagship marts** — opponent/schedule context (§10 method, football-analytics); player **season / YoY-extension** models (on `int_player_club_season__metrics` / `int_player_season_record`); or smaller catalogue/window carryovers (#530(b) player metric rows, #510, #484). **Player streaks (Phase C brick 2) is SKIPPED.** Portfolio remaining: the landscape social-preview image (manual CPO step). Two tiny doc follow-ups open (metrics_display.md:91 stale GAP-21 ref; GAP-20 "id+name only" note). The live MVP stays untouched until cutover (#377); do NOT start the frontend. (Post-#638 refresh #639 was superseded by #640–643 and CLOSED; this is its replacement.) Backlog + verified gap map below._

### ⭐ Stats-percentile track — CLOSED (spec #625 + wire #627)
The Player Stats percentile-vs-peers screen is DONE end-to-end: wireframe `docs/wireframes/12_player_stats.md`
(spec #625) + `mart_player_competition_benchmarks` built + **wired into the v2 player export (#627)**. Display
contract banked in memory [[feedback-percentile-display-phrasing]]: ladder = **"top X% / median / bottom X%"**
(median-anchored distributional position; of the 18 metrics **11 higher_better + 7 neutral + 0 lower_better**,
so "top" = *most* not good for the 7 neutral; no good/bad colour, deferred #366); ratio metrics show the
`{num} of {den} · {pct}%` triple. **#627 mechanics:** the mart gained `metric_numerator`/`metric_denominator`
(via the shared `player_benchmark_metrics()` macro, gated like `metric_value`, null on the 13 per-90 rows,
DQ-tested non-null iff a ratio metric); `int_player_season_position__metrics` exposes `goals_penalty` (the
finishing numerator = `goals - goals_penalty`); `shape_player_payload` attaches a per-season `benchmarks[]`
block (position_group → metrics[]), select/reshape only. **Two CI catches fixed in-flight** (both dbt-templated
SQLFluff, CI-only — `validate` misses them): LT02 indent on the num/den `{% if %}` block → uniform CASEs; and
"Unrecognized name: goals_penalty" (aggregated-but-not-output) → exposed it via a CI-driven scope amendment.
Team benchmark (`mart_team_competition_benchmarks`) = a separate **rank-based** screen, still un-spec'd.

main carries the full #500 metric layer + #596 + #598 + #600 + #530(a) + **#391 A1** (deserved-vs-actual on `mart_team_profile`, #606) + **GAP-15** (team fixtures → team payload, #607) + **GAP-14** (player `birth_date`, #609) + **GAP-16** (player team affiliation, #611) + **GAP-01** (team founded/venue, #613) + **#615** (content_architecture.md §3/§7 block↔mart reconciliation) + **#616** (handover refresh) + **#617** (#391 track A — Team → Squad wireframe spec + GAP-20) + **#618** (handover refresh) + **#619** (#391 GAP-20 — mart_roster wired to the team payload as squad[]) + **#620** (GAP-20 close-out doc-sync — roster ✓ in content_architecture §3/§7) + **#621** (#530(b) — player finishing_efficiency + duels_won_pct catalogue rows completed + goals_penalty atom on the player leg) + **#623** (handover refresh) + **#625** (#391 Stats-percentile wireframe 12 spec'd + GAP-21 registered) + **#626** (handover refresh) + **#627** (#391 GAP-21 — mart_player_competition_benchmarks wired into the player export; mart num/den columns + goals_penalty atom exposed) + **#630** (**#480 §8.3** — per-club player-season foundation `int_player_club_season__metrics` + rebuilt `mart_player_career` to per-club grain; `int_player_season__metrics` = a byte-identical composition; retired `int_player_career__metrics`) + **#631** (handover refresh) + **#632** (**#391** — Player Career wireframe 13 spec'd + GAP-22 registered) + **#633** (handover refresh) + **#634** (**#391 GAP-22** — mart_player_career wired into the v2 player export as career[] + national_appearances_total; a club_latest_kickoff_at ordering window column added to the mart) + **#636** (post-wiring doc-sync reconciliation — wireframes 11/12/13 + the gaps register + content_architecture flipped proposed/pending/orphan → wired/shipped for Squad #619 / Stats #627 / Career #634; 12/13 §5 JSON keys reconciled to the shipped export) + **#637** (handover refresh) + **#638** (**Phase C brick 1** — player YoY `int_player_profile__yoy` + `mart_player_profile` composition) + **#640–#643** (portfolio: README funnel/badges/architecture diagram, MVP screenshot, Design-decisions section, public dbt docs lineage site at `/dbt-docs/`) + **#645** (**Phase D bonus** — player contribution-share `int_player_profile__contribution` + `mart_player_profile` composition + catalogued `contribution_share`). **CPO merges, never self-merge — standing rule.** **#391 is UN-PAUSED but NARROW — only CPO-directed gap-backlog items; the live MVP must NOT break and there is NO frontend cutover yet — standing CPO rule.** **The 5-step protocol is LIVE:** Explore → Plan → **Confirm** (plan mode + ExitPlanMode) → Implement → Verify; for any code/model/metric task ENTER PLAN MODE and WAIT for the CPO's ExitPlanMode approval before editing. **EXCEPTION (CPO-set 2026-06-30): handover/bookkeeping refreshes SKIP plan mode** — show the diff inline, get a quick go, commit through the same contract+review+gate.

### FIRST STEPS (cold chat — do in order)
1. `git checkout main && git pull`. **main GREEN at a08c634** (or later if this refresh merged). Confirm tree clean.
2. Read this file top-to-bottom before touching anything (esp. the header lead + the #645 + #638 entries in RECENT PRs; the ⭐ Stats-percentile callout below is now historical — that track closed at #627).
3. **NEXT = a CPO pick from the un-picked backlog** — no locked task. **Phase C brick 1 (player YoY) is
   MERGED (#638)** — `int_player_profile__yoy` composed into `mart_player_profile`; the **portfolio arc
   #640–643 is MERGED** (README funnel + dbt-docs site); **Phase D bonus (player contribution-share) is
   MERGED (#645)** — `int_player_profile__contribution` composed into `mart_player_profile` + catalogued
   `contribution_share`. **Player streaks (Phase C brick 2) is SKIPPED (CPO).** **The history backfill is
   effectively DONE** (RAW + `mart_player_career` are 5–10 seasons deep across domestic leagues; the
   "thin-until-backfill" premise was STALE — do NOT re-scope a big backfill; see the header finding).
   Candidates: **Phase D flagship marts** (opponent/schedule context — §10 method); player **season /
   YoY-extension** models (on `int_player_club_season__metrics` / `int_player_season_record`); or smaller
   catalogue/window carryovers (#530(b), #510, #484). (Doc-sync DONE #636; player YoY DONE #638; contribution
   DONE #645.) Present candidates + get the CPO's pick;
   ENTER PLAN MODE for any code/model/metric task. #391 un-paused but NARROW — do NOT touch the live MVP or
   start the frontend.
4. **Bash only; never PowerShell.** For any file-touching task: write `.claude/task/contract.md` on a CLEAN tree BEFORE touching any file (impact-map gate for `dbt_project/models/**` + `scripts/export_*.py` + `ingestion/**` + `site*/`); use **PLAN MODE** for the plan-back — EXCEPT handover/bookkeeping refreshes (skip plan mode; show the diff inline + get a quick go; same contract+review+gate).

---

### ⭐ #391 UN-PAUSED — data-first: complete v2 data+export, THEN the frontend
The metric layer was rich but had no user-facing surface. The CPO un-paused #391 NARROWLY with a
**data-first strategy**: get every v2 content block to **built (mart exists) AND wired (the v2 export
carries it)** first, then build the frontend against a stable export. The live MVP (`site/`, fed by
`export_pages_data.py` + `mart_matchday_insights`) is SEPARATE — do NOT add to it; cutover is #377.

**Verified gap map** (`docs/content_architecture.md` §3/§7 — reconciled to reality by #615, with a built-vs-wired legend). Current state:
- v2 = `scripts/export_site_data.py` (8 entity types) + `docs/wireframes/` (**4 screens spec'd**:
  01 fixture, 02 team, 03 player, 11 Squad + the LOCKED metric contract; 04–10 pending). Data layer (~23 marts) ~mostly built.
- **Real gaps:** (1) the **frontend** — `site_v2/` is an empty Astro scaffold (2 stubs), the big lift;
  (2) **orphan marts** — benchmarks, career, player-season still EXIST but the v2 export does NOT carry them
  (wiring needs a wireframe step FIRST). **roster DONE** (#617 spec + #619 wired). **benchmarks: CLOSED**
  (#625 spec + #627 wire). **career: WIRED (#634, GAP-22)** — `mart_player_career` (built #630) carried by the
  player export as career[]; screen spec'd #632; the log is 5–10 seasons deep (backfill effectively done). (3) flagship deserved-vs-actual (DONE, A1),
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
  - ⚠️ benchmarks/career wiring is NOT Phase B — blocked on their screens being spec'd first.
- **Track A (Squad/roster) — FULLY GREEN.** SPEC merged #617 (`docs/wireframes/11_team_squad.md`, identity-only
  roster) + WIRED merged #619 (per-season `squad[]` on the team payload via `shape_team_payload` — id+name only,
  no slug; byte-stable player_sk order; null-identity members omitted; raw position). GAP-20 shipped; the
  content_architecture §3/§7 roster status flipped to ✓ (this doc-sync PR). `mart_roster` is now built AND wired.
  Stats-percentile CLOSED (#625 spec + #627 wire). **Career WIRED end-to-end** — `mart_player_career` built
  (#630) + screen spec'd (#632) + export-wired (#634, GAP-22; career[] + a club_latest_kickoff_at ordering
  column); the log is 5–10 seasons deep (backfill effectively done). (Team benchmark = a separate rank-based screen, not percentile.)
- **Phase C — player foundation + analogs:** foundation **DONE (#630):** the per-club base
  `int_player_club_season__metrics` + rebuilt `mart_player_career`; **Career screen SPEC'D (#632) + WIRED
  (#634, GAP-22).** **Player YoY DONE (#638)** — `int_player_profile__yoy` (mirror of `int_team_profile__yoy`)
  → `mart_player_profile`. The **history backfill is effectively DONE** (5–10 seasons deep; the premise was
  stale). **Brick 2 player streaks is SKIPPED (CPO, 2026-07-03)** — not pending. Remaining: player **season /
  YoY-extension** models (optional).
- **Phase D — design-heavy flagship marts (DECIDE first):** **bonus contribution-share DONE (#645)** —
  `int_player_profile__contribution` (goal-involvement share of the club's whole-season goals; NEUTRAL;
  §10 definition CPO-locked 2026-07-03) → `mart_player_profile` + catalogued `contribution_share`. Remaining:
  **opponent/schedule context** (§10 method, football-analytics) — a NEW mart, still to DECIDE.
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

- **#645 — Phase D bonus: player contribution-share (int_player_profile__contribution), MERGED.** dbt-only.
  NEW `int_player_profile__contribution` (4_intermediate/shared, table) = a player's goal-involvement share of
  the club's WHOLE-SEASON goals ("involved in X% of the club's goals"). A composing intermediate over
  `int_legs__player_match` + `int_legs__team_match` (atoms NOT recomputed; mirrors
  `int_team_season__deserved_vs_actual`); grain (player_sk, team_sk, season_sk); NOT domestic-restricted; NULL
  where the club scored 0; invariant 0 ≤ share ≤ 1. Composed into `mart_player_profile` via the primary club
  (left join, additive/nullable) → auto-carries `scorer_points` + `team_goals_season` + `contribution_share`
  to the v2 player export via `select *` (#606). Catalogued `contribution_share` (BLANK base_relation — the
  deserved_rank/sot_rank_gap flagship-output pattern, resolvability guard skips it; entity=player,
  format=percent, direction=**NEUTRAL**, metric_group=goals); the numerator atom reuses the existing catalogued
  `scorer_points` (goals + assists). CPO definition (AskUserQuestion 2026-07-03, escalations.log): numerator =
  goal involvements; denominator = the club's whole-season goals_for. Honest limit (CPO-accepted, prose only —
  no coverage-gate in the exprs): the share understates where the player's per-match stats are missing. Review:
  scope-auditor + analytics-engineer + football-analytics PASS; ci-data-build green. A contribution-share
  **screen** (wireframe + explicit export shaping) is a later gap, not this brick. Closes the Phase D **bonus**;
  the Phase D **flagship** (opponent/schedule context) is still to DECIDE.
- **#643 — publish dbt docs lineage site at /dbt-docs/, MERGED.** Portfolio/CI. Folded a public, static dbt
  docs site (model lineage graph + descriptions + columns) into the EXISTING GitHub Pages deploy: one additive
  `dbt docs generate --static` step (continue-on-error) in `pages-match-preview.yml`, a `-f`-guarded copy of
  `target/static_index.html` → `_site/dbt-docs/index.html` in `build_match_preview_site.sh`, + a README link.
  Best-effort (a docs failure can't block the app deploy). PROTECTED workflow → protected_override +
  cto-reviewer. Site: `https://ramialfahham.github.io/football-data-pipeline/dbt-docs/`.
- **#642 — README "Design decisions" section, MERGED.** Doc-only (portfolio funnel).
- **#641 — MVP screenshot for the README hero, MERGED.** Doc/asset-only.
- **#640 — README portfolio funnel (headline, badges, architecture diagram), MERGED.** Doc-only. [[project-repo-portfolio]].
- **#638 — Phase C brick 1: player year-over-year (int_player_profile__yoy), MERGED.** dbt-only. NEW
  `int_player_profile__yoy` (4_intermediate/shared) = the player mirror of the shipped team YoY
  `int_team_profile__yoy`, on `int_player_season_record` (per-club, appearance-aligned via `match_number`,
  domestic-leagues only): the current season through N appearances vs the prior season's first N, with deltas
  for goals / assists / shots_on_goal / key_passes / defensive_actions (CPO "broader per-position set",
  2026-07-03; defensive_actions = tackles + interceptions + blocks). Grain (team_sk, player_sk, league_code,
  season_api_year); delta NULL when there's no prior season. Composed into `mart_player_profile` via the
  primary club (`int_player_season__team`) so the profile carries the main-club YoY; auto-carries to the
  player export via `select *` (#606 precedent). Review: scope-auditor PASS; analytics-engineer r1 FAIL
  (naming: `shots_on_target` vs the catalogue `shots_on_goal`) → renamed → r2 PASS. ci-data-build green. A YoY
  **screen** + **brick 2 (player streaks)** are follow-ups. Lessons [[feedback-sibling-pr-rebase-rebind]] +
  [[feedback-governance-review-mechanics]] #4.
- **#637 — handover refresh (post-#636), MERGED.** Recorded #636 + dropped the now-done doc-sync candidate.
- **#636 — #391 post-wiring doc-sync reconciliation (chip task_4c709bd9), MERGED.** Doc-only. Flipped the 3
  now-wired screens proposed/pending/orphan → wired/shipped: wireframes 11 (Squad, #619) / 12 (Stats, #627) /
  13 (Career, #634) — banners, §3, §5, §6 state rows, §10 gaps; the gaps register GAP-21→#627 / GAP-22→#634
  (GAP-20 already done by #620); content_architecture §3 legend (post-#634; **15→17 marts**; orphan reworded to
  team-benchmark-only) + §3/§7 benchmark rows (player wired / team orphan) + career rows. Per a CPO **"full
  reconciliation"** ruling (AskUserQuestion 2026-07-02, logged in escalations.log) also corrected 12/13's §5
  JSON keys to the SHIPPED export (13: season_api_year→season, league_code→competition, team_name/team_logo_url→
  a nested `team` block; 12: `benchmarks[]` nest under `seasons[]`, ratio atoms `numerator`/`denominator`) — a
  wired screen's §5 keys must be greppable in the export (00 binding rule); resolved 13's reserved subtotal
  decision to display-side grouping. Review: bi-analyst PASS; scope-auditor r1 FAIL (cited the ruling in the
  contract but not in escalations.log — §11) → logged it (hash-excluded, so the staged SHA held) → r2 PASS.
  Governance lesson banked [[feedback-governance-review-mechanics]] #4. **Two tiny follow-ups left (out of
  scope):** metrics_display.md:91 still calls GAP-21 a future "wiring PR"; GAP-20's register note "id+name
  only" is loose (the shipped squad[] carries six identity fields).
- **#634 — #391 GAP-22: wire mart_player_career into the v2 player export, MERGED.** Export + a small mart
  add. `shape_player_payload` gains a TOP-LEVEL `career[]` block (one member per club × competition × season:
  season/competition/team/apps/goals/assists) + top-level `national_appearances_total`; `fetch_player_payloads`
  reads `mart_player_career` (scoped like the benchmark fetch). Select/reshape only. Ordering = a PURE sort over
  two mart-shipped recency signals: `last_kickoff_at` (per club-season) + a NEW `club_latest_kickoff_at` window
  column (`max(last_kickoff_at) over (player_sk, team_sk)`) — so a club's rows stay contiguous and clubs sort
  newest-first (handles mid-season transfer + return spell) with NO client-side aggregation. **4 review rounds**
  (the sort took iterations: team_sk→season-desc→mart column→mart window; two CPO rulings — doc-sync reconcile
  SEPARATELY, and "fix properly: add the mart column"); scope-auditor + analytics-engineer + cto all PASS;
  ci-data-build green. **Non-blocking (thrice-flagged): last_kickoff_at/club_latest_kickoff_at lack a not_null
  test** (transitively guaranteed; fold into the reconciliation). Doc-sync (wireframe/register "wired" flip) =
  the separate chip `task_4c709bd9`. Lesson [[feedback-decide-dont-escalate]]. Closes the Career chain.
- **#633 — handover refresh (post-#632), MERGED.** Recorded the Career screen spec + set GAP-22 wiring as next.
- **#632 — #391 Player Career wireframe (13) + GAP-22, MERGED.** Doc-only. NEW
  `docs/wireframes/13_player_career.md` — the Player → Career sub-screen, field-bound to the merged per-club
  `mart_player_career` (#630): a club-grouped season-by-season career log (Season · Competition · Apps · Goals ·
  Assists) + per-club/career subtotals + a National-team caps section; **counts only** (no per-90;
  `ui_design_brief.md` §6.4 + the CPO ruling); honest wording (national = appearances in COVERED competitions,
  never "caps"; thin-until-backfill). §5 binds 1:1 to real `mart_player_career` columns. Registered **GAP-22**
  (export wiring — `shape_player_payload` gains a `career[]` block; the subtotal precompute-vs-display call is
  reserved to that PR). Companion doc-syncs: 00 (inventory row 13 + census), 99 (GAP-22), 03 (§7 ▸Career link +
  §10 ref). Review: 2 rounds (bi-analyst r1 FAIL → added the §6 unresolved-identity state [mirrors 11] + fixed a
  metrics_display→ui_design_brief mis-citation; scope-auditor + bi-analyst r2 PASS). Mirrors #625 (Stats 12) +
  #617 (Squad 11).
- **#631 — handover refresh (post-#630), MERGED.** Recorded the #480 §8.3 foundation + set the Career screen
  spec as a next candidate.
- **#630 — #480 §8.3 per-club player-season foundation + rebuilt mart_player_career, MERGED.** NEW
  `int_player_club_season__metrics` (grain player×club×competition-season) = the canonical per-club atoms base
  (groups `fct_fixture_player_stats` + the penalty-events CTE by club; atoms only — ratios/per-90 derived at
  the rollup). `int_player_season__metrics` re-expressed as a **byte-identical** composition of it (re-sums the
  club rows, re-derives ratios/per-90/composites; `mart_player_profile` + `mart_leaderboards` unchanged — the AE
  reconstructed the OLD compiled model and diffed atom-by-atom; per-fixture ROUND `passes_accurate` is invariant
  to the grouping level; `team_sk` last-club stamp reproduced via `last_kickoff_at` + a deterministic tiebreak).
  `mart_player_career` **rebuilt** to grain (player_sk, team_sk, season_sk) = the Transfermarkt-shaped career log
  (a mid-season transfer = two rows; appearance-gated via `inner join finished`, distinct from the roster mapping
  `dim_player_team_season_mapping`; national-caps window kept). Retired `int_player_career__metrics`; extended the
  drift guard (+ exempt `last_kickoff_at`); synced the layering.md mart inventory. 4 review rounds (r1 both FAIL →
  team_sk tiebreak + test, impact_map → labeled TEMPLATE form, stale review_input.patch regenerated; r2 both PASS
  + 2 quality nits → tautological mart test replaced by `appearances >= 1` + restored the mapping-distinction doc;
  r3 scope-auditor FAIL on a contract-vs-code description drift → synced; r4 both PASS); ci-data-build green.
  **NOT exported (still orphan); screen unspec'd; thin until the backfill.** Career screen spec (13) / export
  wiring / backfill = separate follow-ups. Governance lessons banked [[feedback-governance-review-mechanics]].
- **#625 — #391 Stats-percentile wireframe (12) + GAP-21, MERGED.** Doc-only. Recovered the parked
  `docs/wireframes/12_player_stats.md` draft (the branch `docs/391-player-stats-percentile-spec` had NO unique
  commits — all WIP was in `stash@{0}`; fast-forwarded to main + reworked non-destructively, never popped) and
  reworked it: median word "median"; label = **distributional position** (honest for the 7 `neutral` metrics —
  the draft falsely claimed "all 18 higher_better / top=good"; catalogue = **11 higher_better + 7 neutral + 0
  lower_better**); all 18 metrics bound to real `mart_player_competition_benchmarks` columns; the 5 ratio
  metrics show the `{num} of {den} · {pct}%` triple (atoms in `int_player_season_position__metrics`); two-line
  03 footer (kept Top scorers + added Stats, matching 01's pattern — no rename, no drop). Registered
  **GAP-21** (export wiring). Companion edits: 00_overview (screen 12 + census), 99_gaps_register (GAP-21),
  metrics_display ("Percentile display (vs-peers)" section). Review: bi-analyst round-1 FAIL (silent
  Team-profile→Team footer rename + `rank` direction-mirror left half-done) → both fixed → scope-auditor +
  bi-analyst PASS. Memory [[feedback-percentile-display-phrasing]] updated (distributional framing + rank mirror).
- **#623 — handover refresh (post-#621), MERGED.** Recorded the Stats-percentile pick + the parked wireframe. (This refresh corrects two items resolved just after it locked: median word = "median"; naked-% = carry the denominators.)
- **#621 — #530(b): complete player finishing_efficiency + duels_won_pct catalogue rows, MERGED.** Added an event-derived `goals_penalty` atom to `int_legs__player_match` (mirrors the season model's derivation); filled the player `finishing_efficiency` row (`sum(goals_total - goals_penalty)`/`sum(shots_on)`, `higher_better`) + set `duels_won_pct` player `direction=higher_better`; synced the seed `schema.yml` deferred-rows note. Season model untouched (Option Y; finishing value unchanged). 3 review rounds: analytics-engineer FAIL (schema.yml SSoT drift) → fixed; ci-data-build FAIL (SQLFluff ST06 column-order) → fixed by reordering `goals_penalty` into the calc block; scope-auditor + analytics-engineer + football-analytics all PASS. Unblocks the parked Stats-percentile wireframe.
- **#620 — #391 GAP-20 close-out doc-sync, MERGED.** Marked GAP-20 shipped in the gaps register; flipped the Squad/roster block ⚠orphan→✓ in content_architecture §3/§7 + bumped the queried-mart count 14→15; refreshed the handover. bi-analyst round-1 FAIL (stale §3 legend prose) → fixed.
- **#619 — #391 GAP-20: wire mart_roster into the team payload as squad[], MERGED.** Export-only. `shape_team_payload` gains a per-season `squad[]` block (identity-only, mirroring the GAP-15 fixtures pattern); `_shape_squad_member` reshapes each `mart_roster` row (id+name only, no slug); `fetch_team_payloads` reads `mart_roster`. Null-identity members omitted (DQ-test-guarded), byte-stable player_sk order, raw position (grouping = frontend). Two unit tests. scope-auditor + analytics-engineer + cto PASS (scope-auditor round-1 FAIL was a stale slug claim in contract.md — code was correct; contract fixed, all re-confirmed). Turns `mart_roster` orphan → wired.
- **#618 — handover refresh (post-#617; GAP-20 wiring set as next), MERGED.**
- **#617 — #391 track A: the Team → Squad wireframe spec, MERGED.** Doc-only. New `docs/wireframes/11_team_squad.md` (identity-only roster list backed by `mart_roster`, grouped by position, links to player profiles) following the 00_overview §1–10 template + GAP-20 (export-wiring gap) + 02/00 stale-note/inventory/census reconciliation. scope-auditor + bi-analyst PASS over 4 rounds (bi-analyst caught an invented flag-rendering + a missing null-identity state → both fixed; then a sibling-PR rebase-rebind after #616 merged first, hash shifted `ecf12b17`→`4bcc72da`, both reviewers re-confirmed). Remaining green = the GAP-20 export-wiring PR.
- **#616 — handover refresh (post-#615; track A pick recorded), MERGED.** Dropped the resolved content_architecture drift note; bumped the pointer to dafd463.
- **#615 — content_architecture.md §3/§7 block↔mart map reconciled to reality, MERGED.** Doc-only; §3 status legend (✓ wired / orphan built-not-wired / ✗ not built) + §7 new-mart build status brought in line with the shipped code (14 v2-wired marts; Match-preview backing corrected). Resolves the drift note the prior handover reserved.
- **#614 — handover refresh (#391 GAP-01 merged), MERGED.** Recorded the post-#613 state; kept the fold-generalization question open.
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
  (b) **PARTLY DONE (#621):** added the event-derived `goals_penalty` atom to `int_legs__player_match` + filled the player `finishing_efficiency` row + set `duels_won_pct` (player) direction=higher_better. **Remaining:** the `goals_penalty` + `goals_open_play` player METRIC rows (still blank `base_relation`/`*_expr`; now UNBLOCKED since the atom exists on the leg).
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
