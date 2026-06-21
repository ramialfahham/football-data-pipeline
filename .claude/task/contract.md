# Task contract — Phase 2a backfill: club + domestic competitions (§8 depths)

objective: >
  Apply the §8 tiered depths to the club/domestic competitions (the mechanical part of Phase 2):
  set history_seasons for 7 non-top-5 domestic leagues 2->5 and 8 continental-club competitions
  5->10, then run a scoped backfill. Completes the deep-history foundation for all club competitions.
  Phase 2b (national-team tournaments + qualifiers) is DEFERRED per the CPO (Option A) — their
  "editions/cycle" depth does not map to the history_seasons year-count and needs its own pass.
refs: >
  #479 (deep-season backfill); docs/content_architecture.md §8 (tiered depths); CPO "Execute 2a" +
  defer 2b (Option A) 2026-06-21. The batched-fanout cost finding (~1k/league) from PL/PD/SA/L1.

scope_paths:
  - docs/competition_registry.yml
  - .claude/task/**

decisions_taken: >
  CPO directed "Execute 2a" (2026-06-21). Mechanical application of content_architecture §8 by each
  league's registry competition_type: domestic_league (non-top-5) = 5 seasons; continental_club = 10.
  Changed (15): domestic 2->5 = BL2, ED, LMX, LP, MLS, SPL, VL; continental_club 5->10 = UCL, UEL,
  UECL, LIBER, CAFCL, AFCCL, CCCU, CWC. NOT changed (already at §8 depth): APD/BSA/J1/KL1 (domestic, 5),
  all 5 domestic cups (5). UESC (continental_super_cup) is NOT in the §8 table -> left at status-quo 5
  (no forced classification). CWC/CCCU are tournaments but registered as continental_club -> treated per
  that type (10), not reclassified. Cost is cheap (batched fanout ~1k/league, proven on PL/PD/SA/L1) -
  the spend is covered by the CPO's Phase-2 direction. The continental_club set + APD/BSA/J1/KL1 are
  status=in_progress, so the run uses INCLUDE_IN_PROGRESS=1. Only the registry history_seasons values
  are committed; the run is env-var driven.

decisions_reserved:
  - Phase 2b — national-team tournaments (WC + 7 continental_championship) + 7 WCQ* qualifiers: DEFERRED
    (CPO Option A). "Last 4 editions" / "current+prev cycle" need a per-cadence mapping, not a year-count;
    a separate task. NOT decided here.
  - UESC depth (super cup, absent from §8) and any CWC/CCCU reclassification — left at status quo; a CPO
    call if revisited.

done_when:
  - Registry: the 15 history_seasons values set (7 domestic=5, 8 continental_club=10); no other field/league
    changed except those values. check_registry_var_sync.py green.
  - Backfill run (full profile, scoped to the 15, INCLUDE_IN_PROGRESS=1) completes within quota; actual
    call count captured + reported.
  - Each league reaches its §8 depth in RAW (RAW_APIF_FIXTURES_NEXT latest snapshot): domestic >=5 finished
    seasons, continental_club >=10 (or the API's available depth); fanout 100% (all_fanout_complete).
  - ci-data-build green on the PR.

amendments: (none)
