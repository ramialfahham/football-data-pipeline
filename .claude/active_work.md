# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-25 (**#571 (incomplete-data→NULL, team-feed) MERGED. NOW: #500 PR-b1 (deep atom renames) IMPLEMENTED on `refactor/500-pr-b` — 3 reviewers PASS, PR being opened, awaiting CI + CPO merge. PR-b was SLICED: PR-b1 = atom renames; PR-b2 = file renames / `_season` / consolidation (mapping to pin first).**).
main carries #569 + #567 + #571. **Website #391 PAUSED; the live MVP must NOT break — standing CPO rule.** Per-item CPO-directed; **CPO merges, never self-merge.**

### FIRST STEPS (cold chat — do in order)
1. #571 (incomplete-null) MERGED. The `refactor/500-pr-b` branch (PR-b1 = deep atom renames) is DONE (PR open, awaiting CPO merge) — do NOT reopen it. NEXT after it merges: **#500 PR-b2** = the model FILE renames → `int_<entity>_<window>__metrics` + the `_season`-suffix drop + team-season consolidation. The file-rename MAPPING is §10 + underspecified — PIN it with the CPO FIRST (do the momentum builders rename? int_season_record__* / the position model?). Then PR-c (docs), PR-d (live merge). See the ⭐ #500 block.
2. Bash only; never PowerShell. Write `.claude/task/contract.md` on a CLEAN tree BEFORE touching any model (the impact-map gate enforces it).

## ✅ DONE — incomplete-data→NULL (TEAM-FEED ONLY) — PR open on `fix/incomplete-data-null`, awaiting CPO merge
The universal rule ("a metric over a partially-covered window is '—', never a value from partial data") was applied
to **TEAM-FEED stats only**, after measuring the source of record before building (Appendix A6). Two CPO rulings
reshaped the original "every metric, team + player" spec (all in `escalations.log` 2026-06-25):
- **Q1 = include counts + per-90s; Q2 = reverse #320** (AskUserQuestion).
- **PLAYER side DROPPED — null=zero is CORRECT, PROVEN.** Player stat nulls mean ZERO, not missing: of 1.29M
  played-minutes rows, 91.7% have null `goals_total` (team-stat nulls are only 1–3%). Decisive proof = scoreline
  reconciliation: summing player goals (null→0) per team-fixture equals the actual match score in **95.88%** of the
  85,738 finished team-fixtures that have player data (the rest off by exactly 1 = own goals). So `coalesce(field,0)`
  is correct and the spec's per-field player gate would have NULLed ~92% of players. CPO: "for player treat NULL as
  zero is correct. Do it." → **NO player-model edits.**
- **"Missing player stats must not affect the team stats" (CPO).** Team metrics split by source: genuine team-feed
  stats (shots/passes/corners/saves) get the NULL-on-partial gate; player-DERIVED team metrics (key_passes/tackles/
  duels) are LEFT on average-over-player-covered (player data quarantined).
- **The real player gap (~20% of finished team-fixtures have NO player data at all) is LEFT ALONE** per the CPO — a
  player in a no-data match is silently undercounted; NULLing their whole season would hide almost everyone.

**What shipped (the diff, 6 dbt files + 2 yml):** `int_momentum__team` + `int_season_record__team` add a
`games_with_save_stats` coverage count; `mart_momentum__team` + `mart_season_record__team` gate each team-feed rate
(`case when <coverage_count> < <window> then null else safe_divide(...)`); `int_team_season__metrics` computes
team-feed coverage buckets inline and gates the team-feed stat-count totals in a `season_gated` CTE so all team-feed
rates inherit the NULL by propagation. Scoreline metrics + player-derived team metrics + ALL player models UNCHANGED.
yml docs for the new column in `int_momentum.yml` + `int_season_record.yml` (the latter added by a recorded contract
amendment under the approved "schema docs for the touched models" category).

**Validated:** `dbt parse`/`compile` clean (88 models); sqlfluff clean; the existing range tests already tolerate the
new NULLs (`X is null or X between 0 and 1`), so NO new tests were needed; no-drift guard untouched (the 3 coverage
buckets never reach the season model's output). **Before/after (measured live, in `git diff`/PR body):** season page
~12% of latest-season teams flip a team-feed rate to "—" (292/2400 shots-passes-corners; 296 SoT; 340 save), match
preview ~14% (270/1972) — all genuine team-stat gaps; scoreline + player-derived unchanged. **G3 review: scope-auditor
+ analytics-engineer-reviewer BOTH PASS** (`review.md`, `diff_sha256` d448a8a8…).

**do-NOTs:** don't reopen the player side (null=zero settled, proven); don't gate scoreline or player-derived team
metrics; don't fold this into another PR; don't self-merge.

### ⚠️ 2026-06-25 CORRECTION — read this; it OVERRIDES any "later / #391-gated / combine later" framing in `contract.md`
The metric-layer merge is **NOT deferred and NOT gated on #391.** Do the FULL consolidation now. `contract.md`
currently files the live merge under a "Stage 4 / #391-gated" / "leave the live website alone, combine the seeds
later" scope — **that gating is the bug; disregard it.** The merge IS the deliverable.
- **One list, now:** `metric_definitions.csv` (the LIVE list) is a thin **UI-binding manifest** over the SAME metric
  identities the catalogue already holds (per-metric: `home_`/`away_`/`single_column` bindings + `context`
  match_preview/wc_pretournament + `_recent`/`_pretournament` window). So consolidate = the **catalogue is the single
  registry**, the **live build derives its binding from the catalogue** (the `home_`/`away_` prefix + window are
  mechanical; the surface/context is a tiny map), then **delete `metric_definitions.csv`**.
- **Sequence (both now, neither waiting for the new site):** (1) v2/player naming cleanup — already started in the
  tree (catalogue + `int_team_season__metrics` partial); (2) the live-MVP merge onto the catalogue.
- **MVP-safety gate at every step:** the generated `site/match-preview/metric_definitions.json` must stay
  **byte-identical** to today's. If it moves, the step is wrong. That is how the MVP is protected — not by gating.
- WIP is in the working tree on `refactor/500-metric-layer-naming` (catalogue + `int_team_season__metrics` renames,
  + a `contract.md` whose staging is wrong on the gating). Fresh chat: rewrite `contract.md` to this non-gated scope
  on a clean-ish tree, keep the good blast-radius/impact_map analysis, drop the #391 gate.

## ⭐ #500 metric-layer consolidation — STATUS (PR-a MERGED 2026-06-25; PR-b/c/d remain; non-gated sequence)
> NOTE: PR-a (#567) is MERGED. The "OPEN / awaiting merge / force-pushed" wording in the PR-a bullet below is
> historical. PR-b/c/d are the remaining #500 work (after the universal-NULL task above, per CPO sequencing).
Goal: **ONE metric layer (the catalogue), end-to-end, zero ambiguity** — the merge IS the deliverable, NOT
#391-gated. MVP-safety = byte-identical `site/match-preview/metric_definitions.json` at every step, not deferral.
The PR sequence is locked in `contract.md`'s reference block; each PR gets its own contract.

- **PR-a — OPEN as PR #567, REBASED on the new main (2026-06-25)**: catalogue restructure (entity values +
  CPO-locked de-dup) + metric-layer renames (`shots_on_goal`/`saves`/`goals_against` + per90/_per_match variants)
  across the catalogue, int metric models, benchmark macros, v2 marts + yml, the no-drift guard, tests, the v2
  export refs. Also fixed a CSV-corruption bug the prior WIP left (two merged rows). ZERO live-chain/atom edits.
  **#569 (finishing open-play) merged first**, so #567 was rebased on top — conflicts in the catalogue + the player
  finishing models + shared.yml resolved so the branch carries BOTH #567's renames/de-dup AND #569's open-play
  finishing (merged finishing_efficiency = one `team and player` row, numerator goals_open_play; my 5 new component
  rows kept as separate team+player rows). Re-reviewed on the rebased diff: scope-auditor + analytics-engineer PASS,
  cto PASS (carried — its files byte-identical to the pre-rebase review), football-analytics ESCALATE→CPO-answered
  (the universal NULL rule above; description states the correct rule, no reword). review.md rebound to the rebased
  diff (diff_sha256 addfa2af…). Validated (dbt parse/compile + sqlfluff models). Force-pushed. **Awaiting CPO merge.**
- **PR-b1 — IMPLEMENTED on `refactor/500-pr-b`, PR open (2026-06-25):** the deep ATOM renames end-to-end —
  player `goals_saves→saves`, `goals_conceded→goals_against` (staging→base→core fct+yml→5 int→4 player marts→
  catalogue numerators) + team `shots_on_target_per_match→shots_on_goal_per_match` (one mart alias). Pure 1:1
  rename, NUMBERS=NONE. COLLISION handled: mart_player_match_log DROPS the redundant player goals_conceded (it
  clashed with the match-scoreline goals_against; CPO ruling — it's the GK's conceded, redundant in a per-match log).
  3 reviewers PASS. **DEPLOY: fct_fixture_player_stats is incremental (sync_all_columns) → needs a one-time
  `dbt run --full-refresh --select fct_fixture_player_stats` at/after merge, else historical player GK data NULLs.**
- **PR-b2 — NEXT (after PR-b1 merges):** the model FILE renames → `int_<entity>_<window>__metrics` + the
  `_season`-suffix drop (+ the no-drift guard's `_season` strip) + team-season consolidation. The MAPPING is
  §10 + underspecified — PIN with the CPO BEFORE building: do the momentum BUILDERS (int_momentum__{team,player})
  rename? do int_season_record__* / int_player_season_position__metrics rename? what consolidation remains (the
  2026-06-23 ruling already did rename + W/D/L-fold)?
- **PR-c:** doc consolidation — one `metric_layer.md`; retire/fold `player_metrics_catalogue.md` + `metrics_display.md`.
- **PR-d (the live merge — non-gated, NOW in this stream):** consolidate `metric_definitions.csv` INTO the catalogue;
  repoint `export_metric_definitions_json.py` at the catalogue; delete `metric_definitions.csv` + legacy
  `*_recent`/`*_pretournament` i18n; `corners_conceded→corners_against` END-TO-END (the only live-shared rename);
  reconcile i18n onto `label_i18n_key`; register `qualifier_games_played` (a LIVE metric not yet catalogued).
  **§10s to escalate in PR-d's contract:** the single i18n key scheme; corners naming on the live surface;
  registering `qualifier_games_played`. Genuine CPO-class — do NOT pre-decide.

**THE CRITICAL DISCOVERY (do not miss):** there are **TWO metric-definition SEEDS / two parallel systems** —
`metric_catalogue.csv` (v2; `export_site_data.py` → the PAUSED v2 site) and `metric_definitions.csv` (LEGACY MVP;
`build_match_preview_site.sh` + `site/match-preview` + `site/team-season` = the LIVE site; window-suffixed ids
like `goals_per_match_recent`; `*_recent`/`*_pretournament` i18n). That split IS the "2-3 metric layers". "One
layer" = consolidate `metric_definitions.csv` INTO `metric_catalogue.csv`, migrate the LIVE MVP onto the catalogue,
retire the legacy seed + its build + legacy i18n — WITHOUT breaking the live MVP.

**LOCKED decisions (CPO 2026-06-24; full block in contract.md):**
- One seed (the catalogue); `metric_id` **==** model column; one explainer doc (`metric_layer.md`); retire/fold
  `player_metrics_catalogue.md` + `metrics_display.md` (group/tier/order are already catalogue columns).
- `entity ∈ {team, player, team and player}` — de-dup the only 2 dual rows (`duels_won_pct`, `finishing_efficiency`).
- Naming, one term per stat (provider term kept when good football language): **`shots_on_goal`** (not shots_on_target),
  **`saves`** (not goals_saves), **`_against`** for every conceded stat → `goals_against`, `corners_against`,
  `shots_on_goal_against` (`_conceded`/`_faced` retired).
- Models named **`int_<entity>_<window>__metrics`** (int_team_season__metrics, int_team_momentum__metrics,
  int_player_season__metrics, int_player_momentum__metrics) + consolidate the 3 redundant team-season models.
- **End-to-end, no translation layer:** dbt + catalogue + export + LIVE site + i18n + docs all use the one name.
- Staged sequence (contract.md): (1) end-to-end naming + catalogue restructure + seed consolidation; (2) model-file
  renames + team-season consolidation; (3) doc consolidation. Each its own reviewed PR; MVP-safe throughout.

**Branch:** `refactor/500-metric-layer-naming` (from origin/main, --no-track) — created; **NO code edits yet**
(contract.md only; tree clean). Blast radius mapped in contract.md (shots_on_goal/goals_saves/corners_conceded each
span ~15-20 source files incl. macros, marts, export, the no-drift guard, tests; goals_saves runs staging→marts;
corners_conceded + i18n reach the LIVE site). Validate with `.venv/Scripts/dbt parse|compile` + sqlfluff + the
no-drift guard before review.

**PARKED (resume AFTER #500, on the consistent base):**
- Team **SoT-difference** metrics build is **STASHED** (`git stash list` → "sot-difference WIP (paused for #500)").
  Design is settled: Camp 2, `sot_difference` = SoT for − against (the non-xG "deserved" primitive), observational
  (no pseudo-accuracy / no predictions), TEAM only. Re-add cleanly after #500.
- **Analytics Corner ideas = issue #565** (deserved-vs-actual scatter; observational; live-season after MD3 + historical).
- OTHER OPEN: #545/#546/#547 programs; #530 (catalogue-first CI enforcement); opponent-context v1.x; Coach/career
  marts (#391-gated)._

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

## Player competition benchmark — COMPLETE (PR1 #559 + PR2 #561, both MERGED)
The vs-benchmark engine for PLAYERS (`content_architecture.md` §6), the player analog of the team benchmark
(#511/#512). **PR1 (#559)** = the metric layer (13 per-90 metrics in `int_player_season__metrics` + catalogue
rows + direction/interpretation). **PR2 (#561)** = the engine + mart: `int_player_season_position__metrics`
(per (player,season,position) in-role aggregate from the per-fixture leg) → `int_competition_benchmarks__player`
(per (league_code,season_api_year,**position_group**,metric_key) distribution count/mean/p25/median/p75) →
`mart_competition_benchmarks__player` (LONG, per (player,season,**position_group**,metric_key): in-position
value, distribution, **rank + percentile + peer_count**, vs-median, minutes/appearances) + a
`player_benchmark_metrics()` macro (18-metric set + per-position eligibility, shared engine↔mart).

**THREE build-time CPO refinements that DEVIATED from the original D1-D8 lock** (logged
`.claude/task/escalations.log` 2026-06-23 "player competition benchmark PR2" B1/B2/B3 — each discovered by
querying RAW before building, NOT by re-litigating the design):
- **B1 — peers from match-time `position_code` (G/D/M/F→GK/DEF/MID/ATT), NOT `dim_player.player_position`.**
  The "~0.5% null" premise held ONLY for 2025; the current-bio snapshot is 18-58% null in old seasons (it loses
  retired players' positions). `position_code` is 100% qualifier-covered EVERY season + season-accurate. (A
  premise-correction escalation, not a re-design.)
- **B2 — floor = 270 minutes IN the position** (per `position_code`), which both QUALIFIES and ASSIGNS — no
  modal step. The per-90 VALUE is per-(player,season,position) [in-role], NOT the #559 whole-season per-90 (that
  stays the profile metric). Multi-position players (~10%) appear once per qualifying role; ~4.2% of whole-season
  qualifiers split out (no single position ≥270) — by design. finishing also needs SoT≥10 in-position.
- **B3 — per-position metric ELIGIBILITY** (NOT compute-all-×-all like team): GK = {saves_per90, save_pct,
  passes_per90, pass_accuracy_pct}; DEF=MID=ATT = the other 16. Kills degenerate boards (outfield saves=0, GK
  goals~0); no finer outfield split (the peer pool already makes within-outfield comparisons position-relative).
  52 boards not 72. **RESERVED (still §10):** which eligible metrics a PAGE surfaces + their order = display.
- **percentile = `percent_rank`** (fraction strictly below), NOT cume_dist — so a 0-goal defender reads 0th not
  87th. 18 metrics, all pre-catalogued (no catalogue change). Direction-agnostic. ALL competitions, no
  prev-season fallback (D5/D6 carried).

## Leaderboards vs benchmark — coherence ruling (CPO, this session)
TWO deliberate lenses, kept separate (CPO chose this over merging): **leaderboards = totals/achievements** (top
scorer; the count boards rank season TOTALS) · **benchmark = per-90 standing vs position peers** (percentile). The
same metric can rank differently across them — INTENDED (Golden Boot vs efficiency; fbref carries both). The only
alignment: finishing% uses the SAME floor on both (minutes>=270 AND SoT>=10). The leaderboard count boards stay
TOTALS — do NOT convert them to per-90.

## Deserved-vs-actual REDESIGN — TEAM only (NEXT SESSION's design discussion; do NOT build yet)
The flagship "how you PLAY vs what you GET" read (`content_architecture.md` §6). **This is a DESIGN
discussion, not a build** — football-analytics owns the metric definition (§10). **TEAM only this round —
the CPO explicitly excluded the player analog.**

**What happened (context, do not re-litigate):** the prior team implementation —
`mart_team_profile.performance_vs_results_gap = shot_share_season − points_capture_season` — was REMOVED in
#563. It was uncatalogued + never approved (a #324 governance violation), AND substantively crude: it
subtracted two **non-commensurable [0,1] shares with different baselines** (shot_share ≈ 0.50, points_capture
≈ 0.44), so the gap had no meaningful zero. CPO called it correctly. shot_share_season + points_capture_season
remain in the mart as plain catalogued metrics.

**The framing we settled this session (carry into the discussion — don't re-derive):**
- The real failure was **comparability**. The fix = compare deserved and actual in a **common space**.
- **Candidate (my lean, NOT decided): percentile-space gap via the #511/#512 benchmark engine** — deserved =
  the team's percentile on the *underlying-play* metrics, actual = its percentile on the *results* metrics,
  gap = the difference (both 0–1, same meaning → interpretable). The benchmark engine already produces these
  percentiles. The narrative target: *"creating like a top-2 side, sitting 7th → likely to climb."*
- **Alternative:** a non-xG "deserved-goals/points" composite, then gap vs actuals (richer; a new composite
  football-analytics must define + validate). **Explicitly NO xG** (north-star constraint).
- **RESERVED for the discussion (football-analytics + CPO):** (1) the comparability METHOD (percentile-space
  vs composite); (2) the "deserved" input set (shot_share / danger_zone_ratio / shots_on_target / finishing /
  chance creation); (3) the "actual" set (points_capture / rank / goals).
- **Process — catalogue-first this time:** define the metric(s) as `metric_catalogue` rows with football-
  analytics + CPO approval BEFORE building (the #324 lesson). The football-analytics-expert-reviewer gates the
  catalogue rows.

## FIRST next session (do this first)
- **Nothing pending-merge** (`git fetch` + ff main). main GREEN. **FIRST TOPIC (CPO-directed): the TEAM
  deserved-vs-actual REDESIGN discussion** — see the section directly above; it is a DESIGN discussion (settle
  the method + inputs, catalogue-first), NOT a build, and NOT for players this round. Do not jump to code.
- The player competition benchmark is COMPLETE (PR1 #559 + PR2 #561). Other open items (CPO picks after the
  deserved-vs-actual discussion): a program tranche (#545/#546/#547), opponent-context v1.x, Coach/career
  marts, #530 (catalogue-first CI enforcement), #500 column-align, or wiring the benchmark into an export.
- **PROGRAMS — pick the cut, then build:**
  - **#545 (coverage):** CPO picks the first tranche (by confederation, or highest-club-count-first). Then build that
    tranche's exact league list + `provider_league_id` discovery (**search-first** — 4 wrong IDs happened before),
    onboard (registry, zero-file), `verify-competition-ingest`.
  - **#546 (data-quality):** the **#526 fix LANDED (#551, merged)** — `assert_event_team_in_fixture_participants`
    (event team ∈ {home, away}) is the generic detector and `fixture_event_team_overrides` is the CPO-owned
    correction seed. NEXT: (a) generalise the detector into the standing all-league DQ scan; (b) the **#550**
    automated-triage design (detect → gather-evidence + EXTERNALLY verify → escalate; human decides; NO auto-fix) —
    a §10 design awaiting CPO scope. Triage rule holds: diagnose-to-root, never coverage-cut, never
    merge-on-internal-similarity.
  - **#547 (cost):** size BQ build cost before the expansion scales.
- **PRODUCT (primary):** the content_architecture roadmap — **#506 leaderboards rate boards (#558) + the player
  competition benchmark (PR1 #559 + PR2 #561) now DONE.** Next product slices: the **Coach + career CONSUMPTION
  marts** (Coach page Overview / team-header current-coach chip — both DEFERRED, website #391 PAUSED); the
  **opponent-context** flagship (v1.x — weights opponents via the #561 benchmark engine); **wiring the benchmark
  into an export/display** (deferred with #391); the deferred **#500 column-alignment** (`_season`-suffix /
  goals_saves). **Read `docs/content_architecture.md` §8/§9 first.**
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
3. ~~**`mart_competition_benchmarks`** (team + player)~~ — **TEAM DONE 2026-06-19** (#511 + #512); **PLAYER DONE
   2026-06-23 — PR1 metric layer (#559) + PR2 engine/mart (#561)** (see the benchmark section near the top for the
   B1/B2/B3 build-time refinements). The **opponent/schedule-context flagship** (weights opponents via the #561
   engine) is v1.x, the next benchmark-adjacent product slice.
4. ~~**Coaches + `dim_coach`**; **`mart_player_career`** for the Career/History tabs~~ — **DONE 2026-06-23**
   (#555 `mart_player_career`, counts only; #556 `dim_coach` + `dim_coach_team_mapping`). The **Coach + career
   CONSUMPTION marts** (page Overview / team-header current-coach chip) remain DEFERRED — website #391 PAUSED.

### Carryovers (also open, CPO directs)
- **#484** — player national/tournament **context** window (a NEW national-anchored intermediate selector
  per §8.4 — NOT mart logic). Changes shipped numbers → own validation.
- ~~**Team season-record ↔ rollup unification + naming (#500)**~~ — **DONE 2026-06-23** (consolidation + rename
  `int_team_season__full_season_metrics` → `int_team_season__metrics`, dedup folded; benchmark #512 refs updated).
  RESIDUAL (deferred, logged): the `_season`-suffix / goals_saves column-alignment follow-up.
- **#510** — retire leftover team `dribbles_success_pct` (catalogue row + the `mart_momentum__team` computation
  + the range test; a player metric ruled dropped team-side 2026-06-11, never fully cleaned up).
- **Team season-rollup enhancement** — point `mart_team_season`/`int_team_season` at the mapping spine so
  pre-season teams appear (deferred from the dim_team work).
- **Display-contract amendment** — record the appearance/playing-time block + the no-framing ruling into
  the locked `docs/wireframes/metrics_display.md` (bi-analyst-owned).
- **#483** — qualifying-type cumulative window (GAP-18 follow-up).
- ~~**#506**~~ — leaderboards rate boards **DONE 2026-06-23 (#558)**: the 5 RATE boards + the CPO qualification
  rule (minutes>=270 + position scope + finishing SoT>=10); `finishing_efficiency` extended to the player entity.
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
