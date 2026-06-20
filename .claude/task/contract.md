# Task contract — Backfill PD/SA/L1 to 2016-2025 (BL1/PL parity)

objective: >
  Backfill La Liga (PD), Serie A (SA) and Ligue 1 (L1) to a full 10 finished seasons
  (2016-2025), matching BL1/PL — the §8 top-domestic depth. Completes the featured top-5
  deep history (BL1 + PL already done). Set per-competition history_seasons (authoritative
  post-#520): PD=10, SA=11, L1=11 — the differing values offset each league's provider
  current-season (PD resolves 2025, SA/L1 resolve 2026) to all reach 2016. Run a full-profile
  scoped ingest one league at a time (PD measured FIRST before the broader SA+L1 spend).
refs: >
  #479 (deep-season backfill); docs/content_architecture.md §8 (top-domestic = 10 seasons);
  the PL precedent (#520, 2016-2025 parity). CPO "continue with backfill" 2026-06-20.

scope_paths:
  - docs/competition_registry.yml
  - .claude/task/**

decisions_taken: >
  CPO directed "continue with backfill" (2026-06-20) = the featured top-5 completion (PD/SA/L1),
  to the same 2016-2025 finished depth as BL1/PL (consistent execution of the PL parity precedent,
  not a new decision). Depth authority: content_architecture §8 ("Top domestic leagues = 10 seasons").
  hs values reach 2016 given each league's resolved_current (verified via RAW max season this session:
  PD=2025 -> hs=10; SA=2026 -> hs=11; L1=2026 -> hs=11). The hs asymmetry is the phantom-current-season
  offset tracked by #521 (deferred). Cost (measured this session: detail rows PD/SA=760, L1=617 — details
  do NOT pre-exist, unlike PL) ~= ~12k calls each (~34k total); a fresh spend the CPO approved by
  directing the backfill. PD is the one-league measure before the broader SA+L1 spend (cost rule).
  Runs are env-var driven (full profile, LEAGUE_CODES per league); the only committed change is the
  three registry history_seasons values. Downstream rebuild rides ci-data-build / the nightly run.

decisions_reserved:
  - Phase 2 (the other ~40 leagues + their §8 per-type depths) — deferred; a separate cost decision.
  - If a league's resolved_current differs at run time and it does NOT reach 2016, adjust its hs
    empirically (NOT a CPO call; the §8 target is the 2016-2025 finished depth, confirmed post-run).

done_when:
  - Registry: PD history_seasons=10, SA=11, L1=11; no other field changed. check_registry_var_sync green.
  - PD backfill run completes; actual call count captured + reported BEFORE the SA+L1 spend.
  - Each league RAW (RAW_APIF_FIXTURES_NEXT latest snapshot) shows 2016-2025 finished seasons with
    populated RAW_APIF_FIXTURE_DETAILS; fanout 100% (all_fanout_complete).
  - verify-competition-ingest for each league: 0 NULL fixture_id / 0 stale wrong-id / 0 missing teams.
  - ci-data-build green on the PR (relationship/orphan tests against the new RAW).

amendments: (none)
