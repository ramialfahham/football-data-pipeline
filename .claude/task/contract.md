# Task contract — refetch named matches and squad lists from the provider

objective: >
  One script, scripts/refetch_from_provider.py, asks the provider again for a given list of
  matches (their fixture details: line-ups, events, player stats, statistics) or a given list of
  team-seasons (their /players squad lists), and appends the answers to the existing raw tables
  through the existing loaders. A match is written only when its new fetch is no worse than what
  the warehouse holds and brings two full line-ups. It plans by default, stops at a call cap,
  holds the ingest lock and refuses to start after 02:00 UTC.

refs: >
  #176 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/176): the line-ups,
  step 2. The refetch plan: approved in chat, 2026-10-12.

scope_paths:
  - scripts/refetch_from_provider.py
  - tests/test_refetch_from_provider.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: the script appends to RAW_APIF_FIXTURE_DETAILS (one row per written match) and
  RAW_APIF_PLAYERS (one row per written team-season), as the nightly ingest does; it deletes
  nothing. It changes no ingestion module.
  downstream: no model changes. The next nightly reads the new rows: stg_apif__fixture_events,
  stg_apif__fixture_players, stg_apif__fixture_statistics and stg_apif__lineups read every fetch;
  base keeps the latest events fetch, the newest complete-format player fetch and the latest
  statistics per team; base_apif__player_team_season unions every squad fetch.
  layer_rules: raw stays append-only; base resolves the versions, unchanged.
  deploy_order: merge, then one run per list, started by hand outside the nightly window.
  blast_radius: only the listed matches and team-seasons. A written match's events, player stats
  and statistics may change to the new fetch's; the guard refuses a fetch with fewer events,
  player rows or statistics lines than any stored fetch of that match, or that loses the
  complete player format.

decisions_taken: >
  The refetch, its lists (matches with no line-up, fewer than eleven starters or one sheet;
  team-seasons with no squad list), the not-worse guard, the call cap, the lock and the 250 ms
  pacing: approved in chat, 2026-10-12. The script imports the loaders' own fetch, completeness
  check and raw writers rather than restating them.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; a one-off operator script on the existing
  loaders, like the scripts already in scripts/. RECURRING COST: none; each run is started by hand,
  and its call count is put to the CPO before it runs (about 1,000 calls of the 75,000 a day).

decisions_reserved:
  - Each run, with its call count.
  - The line-ups model and its checks (parked on parked/176-lineups).
  - The research of matches the refetch does not fix.

done_when:
  - pytest tests/ passes, the new tests included; the offline CI gates pass.
  - A plan-mode run on each list prints its call count and makes no call.

amendments: >
  none.
