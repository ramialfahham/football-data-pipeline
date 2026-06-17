# Task contract — docs: content architecture spec (blocks / tabs / navigation + flagships + new-mart map)

> CPO-directed across this conversation (2026-06-17). Writes a NEW doc `docs/content_architecture.md`
> capturing the modular content architecture we iterated: the 3-layer model (blocks=1 mart → tabs →
> navigation graph), the entity-type templates, the block library + block↔mart map, the tabbed page
> compositions, the flagship reads, the list of NEW marts to build, and the backfill depth policy.
> Cross-linked from `site_architecture.md` (the v2 IA it extends) and `metrics_context_model.md` (the
> §8 metrics foundation). DOCS ONLY — the engine spec every later build follows. No models, no
> registry change, no ingest. Reviewers: scope-auditor (always) + analytics-engineer-reviewer
> (block↔mart map, new marts, layer soundness) + bi-analyst-reviewer (the IA / wireframe organizing
> principle + display contract) — CPO-directed.

objective: >
  Create docs/content_architecture.md as the modular IA + data-architecture spec; add cross-link
  pointers in docs/site_architecture.md and docs/metrics_context_model.md. Records decisions already
  taken this conversation; introduces no new ones. It is the spec the wireframes arrange and the
  marts (existing + new) build against.

refs: >
  This conversation 2026-06-17. Builds on docs/metrics_context_model.md §8 (player performance
  surface, PR #491 merged) and docs/site_architecture.md (v2 IA, epic #361). Downstream builds:
  #480 (player-season model), plus the new marts and the backfill listed in the doc.

scope_paths:
  - docs/content_architecture.md
  - docs/site_architecture.md
  - docs/metrics_context_model.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO (this conversation, 2026-06-17), all explicitly ruled and to be RECORDED (not re-decided):
  (1) Three-layer model: BLOCKS (one block = one mart, sliced by league_code/season/entity) -> TABS
      (per-entity compositions; "profile" is just the Overview tab) -> NAVIGATION GRAPH (entity<->entity
      cross-links). Pages never compute; they arrange blocks. Density = compact/full via the tier rule.
  (2) Entity types: Competition, Team, Player, Fixture (rich, full tabbed templates); Matchday, Coach
      (thin SEO templates; Coach feasible — API-Football has coaches); Nation, Stadium deferred.
  (3) The block library + block->mart map across families (Identity, Performance, Standings/rank,
      Schedule, Listings, Matchup, Insight), with subject (team/player) and where-applicable rules.
  (4) Flagship reads = a small signature set, NOT vs-benchmark (which is table stakes / the engine):
      deserved-vs-actual (v1) + vs-own-history/YoY (v1); opponent & schedule context (v1.x, the
      hardest, football-analytics-owned); contribution-share (cheap bonus). Benchmark mart is the
      supporting engine that supplies league context.
  (5) New marts to build (each its own later PR): mart_competition_benchmarks (team+player),
      mart_leaderboards (generalize mart_top_scorers), mart_roster, mart_player_career (+ team
      history), dim_coach (+ block).
  (6) Backfill depth policy: tiered — top leagues 10 seasons / 2nd-tier + smaller 5 / continental club
      10 / world+continental championships last 4 editions / qualifiers current+previous cycle / cups
      5 — PLUS a data-quality floor (skip seasons with empty player-stats) and a phased rollout.
  (7) Build order: #480 (one player-season model) -> backfill -> leaderboards/roster -> benchmark ->
      coaches/career. The season record<->rollup unification is the team-side analog of #480.

decisions_reserved:
  - SPEC ONLY. Every build is a separate PR with its own review (and its own number-change sign-off):
    #480, the new marts, coaches ingest, and the backfill execution.
  - Applying the backfill depths to docs/competition_registry.yml (history_seasons) and RUNNING the
    backfill = a separate registry change + cost-gated ingest task (data-engineer) — NOT here.
  - Player-side flagship analogs (player deserved-vs-actual; position-aware percentile; the
    opponent-adjustment definition) are v1.x and football-analytics-owned where football-domain.
  - New metric mechanisms (benchmark/percentile, contribution-share) get metric_catalogue rows +
    football-analytics sign-off at BUILD time, not in this doc.
  - Naming-consistency cleanup (suffix __team/__player vs prefix team_/player_; mart_team_fixtures vs
    mart_player_match_log) is a separate pass, only NOTED here.
  - Any further §10 (a NEW mechanism, a grain change, a shipped-output change) -> escalate in plain
    language; do not decide.

done_when:
  - docs/content_architecture.md exists with: principles; entity types; block library + block->mart
    map; tabbed page compositions; navigation graph; flagship reads; new-mart list; backfill policy;
    build sequence; honest limits.
  - docs/site_architecture.md and docs/metrics_context_model.md carry a cross-link pointer to it.
  - Internal consistency: no new CPO decision beyond decisions_taken; everything traces to a decision
    made this conversation; build/registry/ingest work is reserved, not performed.
  - Docs-only — no model/SQL/seed/registry/python touched, so NO dbt build / ingest is run.
  - reviewers: scope-auditor + analytics-engineer-reviewer + bi-analyst-reviewer all PASS (>=2 named
    risks each), no FAIL, every ESCALATE has a recorded CPO ANSWER.

amendments: (none)
