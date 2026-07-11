# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: **2026-07-11** — **⭐ v2 FRONTEND (Phase E) STARTED — [PR #672](https://github.com/ramialfahham/football-data-pipeline/pull/672) open (awaiting ci-site-v2 + CPO merge). See the ⭐ ACTIVE (2026-07-11) section immediately below.** Prior refresh **2026-07-07** — main GREEN at **c1d9b2c**. **⭐ MILESTONE: the v2 data-foundation board now has NO orphans** — every built mart the frontend needs is wired. This session shipped the competition-header + team-benchmark arc: **#663** (competition-header registry identity — country/confederation/tier surfaced on the competition hub, GAP-01 pattern), **#664** (Team → Stats vs-league benchmark **wireframe spec**, screen 14 — rank-based "k of N" + vs-median + spread bar, no position dimension, field-bound to `mart_team_competition_benchmarks`, renders the LOCKED 16-row metrics_display set), **#665** (**GAP-23** — wired `mart_team_competition_benchmarks` into the team payload as a per-season flat `benchmarks[]`, the #627-for-teams analog; **this flipped the LAST orphan green** → content_architecture now "18 marts, no orphans"). Plus **#661** (handover + `metrics_context_model.md` §8 de-stale) + **#662** (content_architecture §3/§7 board reconcile to post-#648 reality). **The honest answer to "is the data foundation all green?" is now YES for everything that's a build** — the only non-green rows are the **two deliberate deferrals**: opponent/schedule-context (SHELVED 2026-07-03, no display home) + coach (un-ingested, a cost call) — both CPO policy decisions, not build gaps. So the **v2 FRONTEND (Phase E) is now the natural big frontier** — unblocked by the green export, but still **CPO-GATED** (the live MVP `site/` stays untouched until cutover #377; do NOT start the frontend without an explicit CPO go). **Review-process note (#664):** the team-stats spec took **4 bi-analyst rounds — all FOUR were REAL locked-contract catches** (rendered a display-excluded metric `shot_accuracy`; two unbound display fields `games`/clean_sheets-x-y; a shooting-funnel row-order violation; the Defending T·I·B "sub-display of row 10 only" rule), each fixed with judgment ([[feedback-decide-dont-escalate]]); the final spec maps 1:1 to the LOCKED 16-row team table. Team-benchmark carries all 20 mart rows; the FRONTEND renders 16 (drops shot_accuracy + T/I/B-as-separate). **NEXT = an OPEN CPO pick** (nothing locked/hot): (a) the **frontend, Phase E** — the big one, CPO-gated; (b) the **2 policy calls** — un-shelve opponent-context (needs a display spec) / approve a coach ingest (cost); (c) a tiny **matchday-schedule board note** (fixtures+`round_name` are already exported in the competition payload — a content_architecture §3 legend correction "~ → green", not a build); (d) the **`task_f876b853`** chip (2 stale "deferred" doc comments in `assert_metric_catalogue_expr_resolvable.sql:7-8` + `schema.yml:159-167`); (e) the **programs** #545 coverage / #546 DQ / #547 cost; (f) **#530(c)** model-conformance test. Prior-arc detail is in RECENT PRs below. Superseded lead (still valid history): **Prior #651: player goals_penalty + goals_open_play catalogue completion (#530(b))** — filled the two deferred player metric_catalogue rows (base_relation=`int_legs__player_match`, `sum(goals_penalty)` / `sum(goals_total - goals_penalty)`, direction=higher_better inheriting the settled #600 team ruling) + synced the `schema.yml` deferred note. 3 reviewers PASS (scope-auditor r1 ESCALATE on the §10 `direction` field → RESOLVED not by asking the CPO but by logging the #600/#621 inheritance in `escalations.log`, the #636 pattern; a spawned follow-up chip **task_f876b853** covers 2 non-blocking stale "deferred" doc comments in `assert_metric_catalogue_expr_resolvable.sql:7-8` + the `schema.yml:159-167` direction desc). **⭐ #510 (retire leftover team `dribbles_success_pct`) was found ALREADY DONE** — code-traced end-to-end (no team dribbles catalogue row; `int_team_momentum__metrics` + `mart_team_momentum` have 0 dribbles refs; no range test; export dribbles is the PLAYER leaderboard only). The 2026-06-11 drop got finished during a later momentum-model rename (`int_momentum__team`→`int_team_momentum__metrics`); issue CLOSED. **Do NOT re-attempt.** Prior: **#648 MERGED: player YoY full-season prior-year reference** — enriched the appearances-aligned player YoY (`int_player_profile__yoy`, #638) with the prior season's FULL-season totals as a context anchor: a `prev_full` CTE (prior season at the same club, max match_number, NO cutoff cap) + 6 nullable columns (`appearances_prev_full` + 5 `*_prev_season_full`), so the profile can anchor the pace-matched delta against how big last season actually was ("6 goals through 12 games; at this stage last year, 4; last season he finished with 15 in 34"). **Context only — NO delta-vs-full** (a part season vs a full season would mislead, the trap the model avoids); same #638 5-metric set; **zero new catalogue rows** (uncatalogued windowed variants like `*_prev_season`/`*_delta_yoy`; the drift guard doesn't cover this model). Surfaced in `mart_player_profile` → **auto-carries to the v2 player export** (`select *` + `_strip_identity`, no export edit). A `full >= pace-matched` invariant DQ test (`player_yoy_full_season_ref_ge_pace_matched`) — **passing in data-build = real-data proof** the columns populate non-vacuously wherever a prior season exists (a NULL full would fail the test). Reviews: scope-auditor + analytics-engineer PASS (2 rounds; round 2 after a proactive ST06 column reorder — simple cols before the calc deltas, matching sibling `int_team_profile__yoy`). **⚙️ Also this session: fixed a global commit-gate conflict** — the user-scoped `dbt-agent-kit` plugin's `commit_review_gate.py` double-fired with the repo's own `git_discipline.py` and blocked every code commit (it hashed the WHOLE staged diff incl. review.md). Patched the plugin gate to **stand down when the project ships `.claude/hooks/git_discipline.py`** (cache + marketplace copies); only the repo gate runs here now, plugin intact for standalone projects ([[project-guardrails-plugin]]). Prior: **#645 MERGED: Phase D bonus — player contribution-share** — NEW `int_player_profile__contribution` (4_intermediate/shared, table): a player's goal-involvement share of the club's WHOLE-SEASON goals ("involved in X% of the club's goals"). Composing intermediate over `int_legs__player_match` + `int_legs__team_match` (atoms not recomputed; mirrors `int_team_season__deserved_vs_actual`); grain (player_sk, team_sk, season_sk); NOT domestic-restricted; NULL where the club scored 0; invariant 0 ≤ share ≤ 1. Composed into `mart_player_profile` via the primary club; auto-carries `scorer_points` + `team_goals_season` + `contribution_share` to the v2 player export via `select *` (#606). Catalogued `contribution_share` (BLANK base_relation — the deserved_rank/sot_rank_gap pattern; entity=player, format=percent, **direction=NEUTRAL**, metric_group=goals). CPO definition (AskUserQuestion 2026-07-03, escalations.log): numerator = goal involvements (goals + assists = the existing `scorer_points`); denominator = the club's whole-season goals_for. Honest limit (CPO-accepted, prose only): the share understates where the player's per-match stats are missing. **Player streaks (Phase C brick 2) is SKIPPED (CPO, 2026-07-03).** Prior: **#638 MERGED: Phase C brick 1** — the player year-over-year model `int_player_profile__yoy` (the player mirror of the shipped team YoY `int_team_profile__yoy`) on `int_player_season_record` (per-club, appearance-aligned, domestic-leagues only) with this-season-vs-last deltas for goals/assists/shots_on_goal/key_passes/defensive_actions (CPO "broader per-position set"); composed into `mart_player_profile` via the primary club; auto-carries to the player export via `select *`. **PLUS the portfolio arc #640–#643 MERGED** (public repo = Rami's job-application portfolio, [[project-repo-portfolio]]): README funnel + badges + architecture diagram (#640), MVP screenshot (#641), Design-decisions section (#642), and a **public dbt docs lineage site at `/dbt-docs/`** folded into the existing Pages deploy (#643, best-effort continue-on-error `dbt docs generate --static` step). **⭐ KEY FINDING this session: the history backfill is effectively DONE** — RAW + `mart_player_career` are **5–10 seasons deep** across every domestic league (top-5 Euro at 10, smaller leagues at 5); the "thin-until-backfill" premise was **STALE**. Remaining gaps marginal (VL/CNL at 2, some tournaments at 1 edition, a few continental at 5–9) — low value, a §10 cost call only if wanted. Prior: #636 doc-sync reconciliation; Career chain WIRED end-to-end (#630/#632/#634). **#391 stays UN-PAUSED, NARROW + DATA-FIRST** (CPO). **NEXT = a CPO pick** (nothing locked): the **YoY-block enrichment realization is DONE (#648)**; remaining tracked candidate = **#484** (player NT/tournament context window) — the last open carryover (**#530(b) DONE #651**; **#510 found already-done** and CLOSED). (No new player-season surface is tracked; a brand-new one would need a display spec + CPO go first.) **⛔ Phase D flagship opponent/schedule context was EVALUATED then SHELVED 2026-07-03** — no display home (no wireframe/UI block consumes it), season-level strength-of-schedule is ~constant in a balanced double round-robin league (dead signal), and the real output is a one-line caption not worth a mart+index+metric; do NOT re-attempt without a **display spec FIRST** ([[feedback-display-first-flagship]]). Only ever-worthwhile forms: a tiny `opponent_tier` tag on the existing `mart_team_fixtures` (if a caption gets specced), or opponent-*adjusted* performance (a bigger, speculative build). **Player streaks (Phase C brick 2) is SKIPPED.** Portfolio remaining: the landscape social-preview image (manual CPO step). Two tiny doc follow-ups open (metrics_display.md:91 stale GAP-21 ref; GAP-20 "id+name only" note). The live MVP stays untouched until cutover (#377); do NOT start the frontend. (Post-#638 refresh #639 was superseded by #640–643 and CLOSED; this is its replacement.) Backlog + verified gap map below._

### ⭐ ACTIVE (2026-07-11) — v2 FRONTEND Phase E STARTED · [PR #672] open
The CPO gave the go to START the v2 frontend (Phase E). **Increment 1 is PR-d ([#672](https://github.com/ramialfahham/football-data-pipeline/pull/672)) — awaiting ci-site-v2 + CPO merge (CPO merges, never self-merge).** Ships in `site_v2/` (Astro 5, static, i18n de/en/fi): the **shared design system** — one GLOBAL `src/styles/system.css` (tokens + every component class, transcribed VERBATIM from the LOCKED reference mockup artifact `d70aae67`) imported by `src/layouts/Layout.astro` (dark-default `.fx` host) — plus `src/lib/{format,bars,href,metricRows,types}.ts` + `src/i18n/strings.ts` (DE/EN/FI chrome), and the **fixture page (screen 01)** `src/pages/[lang]/[competition]/matches/[fixture].astro` composing 13 components (Masthead · NarrativeSlot · FormSegment · MetricComparison/MetricRow · SplitSection · RecentMatch · PlayerRow · HeadToHead · LinksFooter · Crest · SectionHead · Breadcrumb), rendering ONE real exported fixture across de/en/fi. Build green (6 pages: the CI four `dist/index.html`+`dist/{de,en,fi}/index.html` + 3 fixture pages); serves HTTP 200 under `/v2/`.

**Decisions LOCKED this session (do NOT relitigate):**
- **Deploy = Option A (CPO-ruled 2026-07-11):** this PR sets `base:"/v2/"` and builds the `/v2/` artifact but does NOT wire the live Pages publish. **Wiring the live `/v2/` deploy is the NEXT, SEPARATE PR** — it edits the PROTECTED `.github/workflows/pages-match-preview.yml` + `scripts/build_match_preview_site.sh` (needs a `protected_override` + cto-review). Deliberately deferred so the live MVP can't break. `ci-site-v2.yml` already builds v2 on PR but does NOT deploy.
- **Sample fixture = BSA Palmeiras vs Atlético-MG (`site_v2/src/data/fixtures/1492306.json`)**, NOT BL1 — BL1 is OFF-SEASON (next round Aug 2026, `mart_team_momentum` empty → no live W1 form). A fully-populated in-season fixture proves every component. Committed as a TEMPORARY build input (real export: `python scripts/export_site_data.py --entities fixtures`, read-only, BigQuery ADC); replaced by the WIRED export at #365. `src/data/competitions.json` = registry-derived slug map (BSA→brasileirao); the frontend NEVER generates slugs.
- **Frontend is DISPLAY-ONLY** (consumption contract): ALL arithmetic (bar widths, direction→green, %×100, points-fraction ×3) confined to `lib/bars.ts` + `lib/format.ts`; components/pages have ZERO `.sort`/`.reduce`/`Math.`. Comparison renders the LOCKED 16-row `metrics_display.md` table; green = catalogue `direction` (neutral → NO green, both white); W1 pills / W2 count chips. Toggle is **JS-free** (CSS `:checked` radios), deferring the island framework (#362).
- **gitignore gotcha (FIXED, was a cto round-1 FAIL):** repo-root `.gitignore` `lib/` (dead Python boilerplate, UNANCHORED → `**/lib/`) silently ignored `site_v2/src/lib/` → the 5 helper files weren't staged (build passes locally on on-disk files but a fresh CI checkout would fail). Countered IN-SCOPE with `!src/lib/` in `site_v2/.gitignore`. **Root `.gitignore` cleanup (drop dead `lib/`/`lib64/`) is a separate repo-hygiene follow-up** (out of this contract's scope).

**NEXT (increment 2+ — CPO picks, nothing locked):** (a) **wire the live `/v2/` deploy** (protected PR, Option B); (b) **DE/FI metric-label i18n** via the catalogue `label_i18n_key`s (#370 — metric ROW labels are English-only today); (c) the **next page templates** (team / player / competition / leaderboards) reusing the SAME design system; (d) wire the now-INERT cross-page links (team/player/matchstats/h2h targets) as those pages land; (e) SEO schema.org (#369); (f) the island-framework decision (#362). Reviewers' non-blocking notes: 2 dead CSS selectors (`.mval .sub`, `.err`); `ci-site-v2` runs `npm run build` but NOT `astro check` (no type-check gate — possible CI hardening).

**Verify locally:** `npm --prefix site_v2 run build` (green) → `npm --prefix site_v2 run preview` → `http://localhost:4321/v2/en/brasileirao/matches/2026-07-26-palmeiras-vs-atletico-mg/`. (The preview-MCP `launch.json` is gitignored + OUT of contract scope — the gate blocks writing a `v2` config; run preview via Bash. No connected browser in this session, so screenshots via the browser MCP were unavailable — verified via built-HTML structure + live-serve curl instead.)

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

main carries the full #500 metric layer + #596 + #598 + #600 + #530(a) + **#391 A1** (deserved-vs-actual on `mart_team_profile`, #606) + **GAP-15** (team fixtures → team payload, #607) + **GAP-14** (player `birth_date`, #609) + **GAP-16** (player team affiliation, #611) + **GAP-01** (team founded/venue, #613) + **#615** (content_architecture.md §3/§7 block↔mart reconciliation) + **#616** (handover refresh) + **#617** (#391 track A — Team → Squad wireframe spec + GAP-20) + **#618** (handover refresh) + **#619** (#391 GAP-20 — mart_roster wired to the team payload as squad[]) + **#620** (GAP-20 close-out doc-sync — roster ✓ in content_architecture §3/§7) + **#621** (#530(b) — player finishing_efficiency + duels_won_pct catalogue rows completed + goals_penalty atom on the player leg) + **#623** (handover refresh) + **#625** (#391 Stats-percentile wireframe 12 spec'd + GAP-21 registered) + **#626** (handover refresh) + **#627** (#391 GAP-21 — mart_player_competition_benchmarks wired into the player export; mart num/den columns + goals_penalty atom exposed) + **#630** (**#480 §8.3** — per-club player-season foundation `int_player_club_season__metrics` + rebuilt `mart_player_career` to per-club grain; `int_player_season__metrics` = a byte-identical composition; retired `int_player_career__metrics`) + **#631** (handover refresh) + **#632** (**#391** — Player Career wireframe 13 spec'd + GAP-22 registered) + **#633** (handover refresh) + **#634** (**#391 GAP-22** — mart_player_career wired into the v2 player export as career[] + national_appearances_total; a club_latest_kickoff_at ordering window column added to the mart) + **#636** (post-wiring doc-sync reconciliation — wireframes 11/12/13 + the gaps register + content_architecture flipped proposed/pending/orphan → wired/shipped for Squad #619 / Stats #627 / Career #634; 12/13 §5 JSON keys reconciled to the shipped export) + **#637** (handover refresh) + **#638** (**Phase C brick 1** — player YoY `int_player_profile__yoy` + `mart_player_profile` composition) + **#640–#643** (portfolio: README funnel/badges/architecture diagram, MVP screenshot, Design-decisions section, public dbt docs lineage site at `/dbt-docs/`) + **#645** (**Phase D bonus** — player contribution-share `int_player_profile__contribution` + `mart_player_profile` composition + catalogued `contribution_share`) + **#648** (player YoY full-season prior-year reference — `int_player_profile__yoy` `prev_full` CTE + 6 `*_prev_season_full` context columns → `mart_player_profile`; a `full >= pace-matched` invariant DQ test; auto-carries to the v2 player export) + **#649** (handover refresh) + **#650** (handover — drop untracked "further player-season models") + **#651** (**#530(b)** — player `goals_penalty` + `goals_open_play` catalogue rows completed: `int_legs__player_match` formulas + direction=higher_better + `schema.yml` deferred-note sync) + **#653** (**#484** — player momentum consumes the shared `int_team_momentum_window`; the top-players strip + team form share ONE window; tournament-cumulative on tournament fixtures; `assert_player_momentum_window_matches_team` parity test) + **#655** (season-record campaign=season stale-note cleanup) + **[concurrent session]** squad `/players` skip-if-cached (450c205) + exclude All-Star teams from the player affiliation mapping (81eb1ed) + **#661** (handover + metrics_context_model §8 de-stale) + **#662** (content_architecture board reconcile) + **#663** (competition-header registry identity → competition hub) + **#664** (#391 — Team → Stats vs-league benchmark wireframe spec, screen 14) + **#665** (**#391 GAP-23** — mart_team_competition_benchmarks wired into the team payload as `benchmarks[]`; **flips the last board orphan green**). **CPO merges, never self-merge — standing rule.** **#391 is UN-PAUSED but NARROW — only CPO-directed gap-backlog items; the live MVP must NOT break and there is NO frontend cutover yet — standing CPO rule.** **The 5-step protocol is LIVE:** Explore → Plan → **Confirm** (plan mode + ExitPlanMode) → Implement → Verify; for any code/model/metric task ENTER PLAN MODE and WAIT for the CPO's ExitPlanMode approval before editing. **EXCEPTION (CPO-set 2026-06-30): handover/bookkeeping refreshes SKIP plan mode** — show the diff inline, get a quick go, commit through the same contract+review+gate.

### FIRST STEPS (cold chat — do in order)
1. `git checkout main && git pull`. **main GREEN at c1d9b2c** (or later if this refresh merged). Confirm tree clean.
2. Read this file top-to-bottom before touching anything (esp. the header lead — the ⭐ no-orphans MILESTONE; the ⭐ Stats-percentile callout below is now historical — that track closed at #627).
3. **NEXT = a CPO pick — no locked task, nothing hot.** ⭐ **The v2 data foundation is now all-green for builds**
   (no orphans left after #665 wired the team benchmark — the last one). The natural big frontier is the **v2
   FRONTEND (Phase E)** — but it stays **CPO-GATED**: do NOT start `site_v2/` without an explicit CPO go, and do
   NOT touch the live MVP `site/` (cutover is #377). Un-picked candidates:
   - **v2 FRONTEND (Phase E)** — the big one: build the Astro frontend (#366/#368) against the now-stable export.
     CPO go required; a major multi-session undertaking.
   - **2 policy calls** (CPO decisions, not builds): un-shelve **opponent/schedule context** (needs a display spec
     first — SHELVED 2026-07-03, no display home) · approve a **coach** ingest (cost-gated).
   - **matchday-schedule board note** — tiny: fixtures + `round_name` are already exported in the competition
     payload, so it's green at the data layer; a content_architecture §3 legend correction (~ → green), not a build.
   - **task_f876b853** chip — 2 stale "deferred" doc comments (`assert_metric_catalogue_expr_resolvable.sql:7-8`
     + `schema.yml:159-167` direction desc), both false after #621/#651. Doc-only, ~10-min green.
   - **Programs** (#545 coverage · #546 DQ suite · #547 cost) — strategic, multi-session; #545 needs a CPO tranche pick.
   - **#530(c)** model-conformance test; **player direction/interpretation classification** (widen the meaning test).
   - **Portfolio** — the landscape social-preview image (a manual CPO step).
   - **#3 career-NT-record-by-competition-type = PARKED** on NT-history + friendlies ingest (cost-gated §10).
   The national-team window thread is FULLY CLOSED (do NOT re-open — §4 + §8.4). Present candidates + get the CPO's
   pick; ENTER PLAN MODE for any code/model/metric task.
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
  stale). **Brick 2 player streaks is SKIPPED (CPO, 2026-07-03)** — not pending. **YoY full-season reference DONE
  (#648)** — `int_player_profile__yoy` `prev_full` CTE + 6 `*_prev_season_full` context columns → the profile.
  The player YoY chain is complete (base #638 + enrichment #648; streaks skipped). No tracked player-season
  model remains; any new surface is a fresh CPO-directed spec (with a display home first).
- **Phase D — design-heavy flagship marts:** **bonus contribution-share DONE (#645)** —
  `int_player_profile__contribution` (goal-involvement share of the club's whole-season goals; NEUTRAL;
  §10 definition CPO-locked 2026-07-03) → `mart_player_profile` + catalogued `contribution_share`.
  **Opponent/schedule context EVALUATED then SHELVED (2026-07-03)** — no display home; season-level SoS is
  ~constant in a balanced league (dead signal); the read is a one-line caption not worth a mart+index+metric.
  Do NOT re-attempt without a **display spec first**; the only ever-worthwhile forms are a tiny `opponent_tier`
  tag on `mart_team_fixtures` (if a caption is specced) or opponent-*adjusted* performance (bigger, speculative).
  See [[feedback-display-first-flagship]]. **Phase D is now COMPLETE (bonus only).**
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

- **#670 — CI-failure watchdog now watches dbt-scheduled, MERGED; follow-up adds ci-site-v2 + pages.**
  One-line add to `.github/workflows/ci-failure-watchdog.yml` `on.workflow_run.workflows:` so a failed
  nightly prod build (dbt-scheduled: ingest + `dbt build --target prod` + prod DQ tests) opens/updates a
  triage issue instead of only GitHub's easily-missed scheduled-failure email — it was the only significant
  workflow absent from the watch list. **This follow-up branch adds the two remaining unwatched significant
  workflows**: `Deploy match preview (GitHub Pages)` (pages-match-preview — a genuine prod-writer: `dbt
  run --target prod` + DQ on a 07:30 cron) and `ci-site-v2` (NOT a prod-writer — the v2 `npm run build`
  check, added for parity with the already-watched `ci-ui`). Watch entries key on each workflow's `name:`,
  not filename (pages → the display-name string). Protected-path (`.github/workflows/`) change under
  `protected_override`; scope-auditor + cto-reviewer (opus, guard path) PASS. All significant workflows
  now watched; no further watchdog candidates remain.
- **#665 — #391 GAP-23: wire mart_team_competition_benchmarks into the team payload, MERGED.** Export + docs.
  `shape_team_payload` gains a per-season **flat** `benchmarks[]` block from `mart_team_competition_benchmarks`
  (the #627-for-teams analog, team-simplified: NO position nesting, NO num/den atoms — team ratios use the
  adjacent-count-row mechanism). Two new pure shapers (`_shape_team_benchmark_member` carries the 8 spec-bound
  columns `metric_key`/`metric_value`/`rank`/`team_count`/`league_median`/`league_p25`/`league_p75`/
  `vs_median_delta`; `_shape_team_benchmarks` a byte-stable flat list); `fetch_team_payloads` fetches the mart
  scoped like mart_roster. **Select/reshape only** — carries all 20 mart rows, the frontend renders the LOCKED 16.
  **⭐ Flips the LAST board orphan green** → content_architecture "18 marts, no orphans"; 99_gaps GAP-23 → shipped;
  14 banner/§10 → wired. 4 unit tests; 32 export tests green. **scope-auditor + analytics-engineer + cto +
  bi-analyst PASS** (1 round). [[feedback-consumption-layer-contract]].
- **#664 — #391: Team → Stats (vs-league benchmark) wireframe spec (screen 14), MERGED.** Doc-only. New
  `docs/wireframes/14_team_stats.md` — the Team Stats sub-screen, field-bound to `mart_team_competition_benchmarks`.
  **Rank-based** ("k of N" + vs-median + p25/median/p75 spread bar, honest at league N≈18 — never percentile), **no
  position dimension** (season selector only), direction-aware from the catalogue (`goals_against_per_match` the
  sole rank-mirror). Renders the LOCKED 16-row metrics_display team set (20 mart-ranked, **16 rendered**:
  `shot_accuracy` + the T/I/B defensive sub-display are ranked but NOT independent rows). Companion syncs: 00 (screen
  14 + census), 99 (GAP-23), 02 (▸Stats link). **4 review rounds — the bi-analyst caught FOUR real locked-contract
  defects** (display-excluded metric; unbound `games`/clean_sheets-x-y; shooting-funnel row order; Defending
  sub-display), all fixed with judgment ([[feedback-decide-dont-escalate]]); scope-auditor + bi-analyst PASS.
- **#663 — competition-header registry identity → the competition hub, MERGED.** Export-only (+ tests). Surfaced
  `country`/`confederation`/`tier` on the competition-season hub payload (they flowed through `_registry_competitions`
  but were dropped when the `meta` dict was built; pure registry pass-through, no BigQuery; GAP-01/#613 pattern).
  Flipped the content_architecture Competition-header row partial → green. 2 unit tests; scope-auditor +
  analytics-engineer + cto PASS.
- **#662 — content_architecture §3/§7 board reconcile to post-#648 reality, MERGED.** Doc-only. Flipped stale
  markers: player Season (#630) / Season-over-season (#638+#648) / Contribution-share (#645) → ✓; opponent-context
  → ✗ SHELVED; player streaks → SKIPPED; career backfill note → effectively done. (Sibling-PR rebase-rebind after
  #661 merged first — content byte-identical via patch-id, hash rebound [[feedback-sibling-pr-rebase-rebind]].)
- **#661 — handover refresh + metrics_context_model §8 de-stale (post-#655), MERGED.** Doc-only. De-staled the
  §8-intro/§8.7 "#480/#484 build follow-ups" refs + the §8.4 `form_window_kind` enum that was never added.
- **#655 — season-record "campaign is the season" note cleanup, MERGED.** dbt docstring-only.
  Removed the stale "multi-season national qualifier campaigns are a separate follow-up" notes from
  `int_team_season_record` + `int_player_season_record`. CPO ruling: the campaign IS the season — confirmed a
  PHANTOM gap (each WCQ campaign carries ONE `season_api_year` spanning its full 2–3-yr run, e.g. WCQEU=2024 →
  matches 2025-03→2026-03), so the `(league_code, season_api_year)` partition already cumulates the whole
  campaign. Comment-only; compiled SQL byte-identical; scope-auditor + analytics-engineer PASS. **⚠️ This was
  redone in an ISOLATED git worktree→then the PRIMARY tree after a CONCURRENT Claude session (on
  `fix/ingest-squads-skip-cached`) collided — it repeatedly stashed the WIP; lesson: two sessions in one working
  dir don't compose with the primary-anchored governance hooks (the contract gate reads the PRIMARY contract, so
  it rejects worktree edits). Resolution: wait for the other session to finish, then work the primary tree.**
- **#654 — national-team context block on the profile (§8.4): EVALUATED then CLOSED, no consumer.** Not built.
  Recent NT context is already served on the national fixture preview via momentum (#653) + the career NT record
  via the Career screen national section (`mart_player_career` + `national_appearances_total`, #634); a standing
  profile block had no display-first justification. The national-team window SET is fully built where consumed.
- **#653 — #484: player momentum uses the same form window as team, MERGED.** dbt-only. Re-pointed
  `int_player_momentum__metrics` at the shared `int_team_momentum_window` (the #323 window-extraction de-dup) so
  the fixture-page top-players strip and the team form panel consume ONE window selection. On a tournament fixture
  (world_championship / continental_championship) the strip now inherits the GAP-18 cumulative window
  (`tournament_to_date` / `qualifiers`) instead of last-5, matching the team form; **non-tournament fixtures are
  byte-identical** (the shared model's last_5 branch = the same join + club/national season boundary +
  recency_rank<=5 as the retired inline CTEs — both reviewers verified). Widened `window_type` accepted_values →
  `[last_5, tournament_to_date, qualifiers]` on both builder (`int_momentum.yml`) + mart (`shared.yml`); corrected
  the stale `games_in_window` "max 5" wording (it's the player's appearance count, uncapped on tournament windows).
  NEW `assert_player_momentum_window_matches_team` (player vs team `window_type` must agree per shared side — the
  parity guard). **No export change** (`window_type` already in `_TOPPLAYER_DROP`); **team path untouched.**
  scope-auditor (2 risks) + analytics-engineer (6 risks) PASS first round; ci-data-build green. **Issue #484
  CLOSED** (literal scope done). Followed by the national-team window audit → **#654** (NT profile context,
  presence-gated) + **#655** (campaign=season note cleanup) filed with CPO rulings; **#3** career-NT-by-type parked.
- **#651 — #530(b): complete player goals_penalty + goals_open_play catalogue rows, MERGED.** Seed-only.
  Filled the two deferred player `metric_catalogue.csv` rows (label+description existed; formula fields were
  blank): base_relation=`int_legs__player_match`, numerator_expr `sum(goals_penalty)` / `sum(goals_total -
  goals_penalty)` (player `goals_total` already excludes own goals, so no `- goals_own` term — unlike the team
  row), denominator blank (count metrics), direction=**higher_better** + interpretation, mirroring the settled
  team rows (#600) + the player finishing_efficiency row (#621). Synced `seeds/schema.yml` (dropped the
  "still-deferred player rows" note + reworded the blank-row references). Brings both rows into the
  resolvability guard's coverage. No model/export change (values already flow from `int_player_season__metrics`).
  Review: scope-auditor + analytics-engineer + football-analytics **PASS** over **2 rounds** — round 1:
  analytics-engineer flagged a dangling "deferred rows above" schema.yml self-reference (fixed) + scope-auditor
  **ESCALATE** on whether setting the §10 `direction` field was a new decision → RESOLVED by logging the
  #600/#621 inheritance in `escalations.log` (the #636 log-then-repass pattern, NOT a CPO question — settled-
  ruling inheritance); round 2: all 3 PASS. ci-data-build green (resolvability guard confirms the rows resolve).
  **Spawned follow-up chip task_f876b853:** 2 non-blocking stale "deferred" doc comments (the sibling
  `assert_metric_catalogue_expr_resolvable.sql:7-8` header + `schema.yml:159-167` direction description) — out
  of #530(b)'s scope, so spawned rather than folded in ([[feedback-scope-discipline]]). Lessons
  [[feedback-decide-dont-escalate]] (resolved the process-ESCALATE with judgment), [[feedback-scope-discipline]].
- **#650 — handover: drop untracked "further player-season models" candidates, MERGED.** Doc-only. Removed
  brainstormed/declined ideas (multi-season trend / per-position YoY / milestones) that a prior refresh had
  over-formalized into the handover as "remaining candidates"; kept only the tracked backlog. Lesson banked
  [[feedback-handover-discipline]] (handover backlog = tracked/agreed work only, not declined brainstorm).
- **#649 — handover refresh (post-#648), MERGED.** Doc-only.
- **#648 — player YoY full-season prior-year reference (int_player_profile__yoy), MERGED.** dbt-only.
  Enriched the appearances-aligned player YoY (#638) with the prior season's FULL-season totals as a context
  anchor: a `prev_full` CTE (prior season at the same club, max match_number, NO cutoff cap) + 6 nullable
  columns (`appearances_prev_full` + 5 `*_prev_season_full`), so the profile anchors the pace-matched delta
  against how big last season actually was. **Context only — NO delta-vs-full** (a part vs a full season
  would mislead, the trap this model avoids); same #638 5-metric set; **zero new catalogue rows** (uncatalogued
  windowed variants like `*_prev_season`/`*_delta_yoy`; the drift guard `assert_no_uncatalogued_season_metric`
  doesn't cover this model). Surfaced in `mart_player_profile` → **auto-carries to the v2 player export**
  (`select *` + `_strip_identity`, no export edit). A `full >= pace-matched` invariant DQ test
  (`player_yoy_full_season_ref_ge_pace_matched`); **passing in data-build = real-data proof** the columns
  populate non-vacuously wherever a prior season exists (a NULL full would fail the guarded expression).
  Review: scope-auditor + analytics-engineer PASS (2 rounds; round 2 after a proactive **ST06** column reorder
  — simple cols before the calc deltas, matching sibling `int_team_profile__yoy`; SQLFluff is CI-only). Grain
  unchanged; domestic-only + primary-club scope inherited from #638. A YoY **display screen** (wireframe) +
  its export shaping is a later gap, not this brick. (Also this session, non-PR: fixed the global
  `dbt-agent-kit` commit-gate double-fire — plugin gate now stands down when the repo ships its own gate;
  [[project-guardrails-plugin]].)
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
  (b) **DONE (#621 + #651):** #621 added the event-derived `goals_penalty` atom to `int_legs__player_match` + filled the player `finishing_efficiency` row + set `duels_won_pct` (player) direction=higher_better; **#651 completed the `goals_penalty` + `goals_open_play` player METRIC rows** (base_relation=`int_legs__player_match` + `*_expr` + direction=higher_better). Follow-up chip **task_f876b853**: 2 stale "deferred" doc comments (sibling test header + schema.yml direction desc).
  (c) **model-conformance** test — does each model actually COMPUTE the catalogue formula (modulo availability)? The deeper guard beyond resolvability.
- **Player-metric direction/interpretation classification** (v1.x deferral) — the completeness test is team-only; when the player benchmark matures, classify the ~28 blank player rows and widen the test. CPO call.
- **Deserved-vs-actual extensions (NOT granted):** a consumption mart when a frontend consumer exists (#391 paused); `rank()` tie semantics revisit; other windows (form panel could compute sot_difference too).
- **PROGRAMS** (enablers; never eclipse product): #545 coverage tranche · #546 data-quality suite · #547 cost sizing.
- **Carryovers (open):** **#484 DONE (#653) + CLOSED**; the national-team window audit spun off **#654** (NT context block on the profile, presence-gated — needs a wireframe first) + **#655** (season-record campaign=season note cleanup, phantom gap) + parked **#3** (career NT record by competition type — data/cost-gated). Also open: team season-rollup → mapping spine; #483 (qualifying-type cumulative window, GAP-18); display-contract amendment (appearance/playing-time block); Pilot PR2 slugs (BLOCKED on blinded §10 rulings E2/E3); Coach + career CONSUMPTION marts (DEFERRED, #391 paused).
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
