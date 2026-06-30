# Task contract — reconcile content_architecture.md §3 block↔mart status to reality

> Written on a CLEAN tree (branch chore/reconcile-content-arch-status off main @ 68915d0).
> Doc-only — no code/model change. Reconciles the drifted status columns to the shipped state.
> See docs/working_agreement.md §2 (contract), §10 (decision rights).

objective: >
  CPO asked "where do we stand on the UI-component ↔ marts mapping; update the overview". Reconcile
  docs/content_architecture.md §3 (block ↔ mart) — and the related §7 (new marts to build) — status
  columns to the VERIFIED current state: which marts are BUILT and WIRED to the v2 export vs BUILT-but-
  orphan (screen unspec'd) vs not-built. The §3 status column has drifted since 2026-06-17.

refs: >
  CPO request this session (2026-06-30, post-#614). Verified: export_site_data.py QUERIES 14 marts (the 3
  spec'd screens + competition/standings/leaderboards) — mart_matchday_insights is mentioned only in a
  comment (it is the SEPARATE live-MVP feed, not a v2 source). mart_team_competition_benchmarks (#512),
  mart_player_competition_benchmarks (#559 PR1), mart_roster (#503), mart_player_career = BUILT but NOT
  wired (orphan, screens unspec'd). GAP-14/16/01 (#609/#611/#613) completed the player + team identity blocks.

scope_paths:
  - docs/content_architecture.md
  - .claude/task/**

decisions_taken: >
  Documentation / status reconciliation only — RECORDS the verified current state (mart-built vs v2-wired
  vs orphan vs not-built) in the §3/§7 status columns + adds a one-line legend (✓ = mart built AND wired to
  the v2 export; "orphan" = built, not wired because the screen is unspec'd). Corrects two pre-existing
  inaccuracies the strict legend exposed: the wired count (14, not 15 — a comment-mention of
  mart_matchday_insights was miscounted) and the Match-preview backing (the v2 fixture preview composes
  W1/W2/standing/h2h marts; mart_matchday_insights is the live-MVP feed). Invents NO product/UX/metric/
  naming decision; does NOT decide whether/when to spec the orphan screens or build the flagship marts.

decisions_reserved:
  - Whether/when to spec the orphan-mart screens (Squad / Stats-percentile / Career) so benchmarks/roster/
    career can be wired — wireframe/design, CPO call. Recorded as status, not actioned.
  - The flagship v1.x marts (opponent/schedule context; contribution-share) — Phase D, §10 method/
    definition, not built. Recorded as status.
  - The two stale-wireframe flags + the broader wireframe §10 status drift (e.g. the stale GAP-15 line) —
    separate doc-status items, NOT in this §3/§7 reconciliation.

done_when:
  - §3 status reflects reality (player header ✓ incl. current club #611 + birth_date #609; team header ✓
    incl. founded/venue #613; leaderboards ✓ wired; benchmarks/roster/career = orphan built-not-wired;
    opponent-context/contribution-share = not built; deserved-vs-actual ✓ team #606), with a built-vs-wired
    legend stating the verified 14-mart count + the Match-preview correction. §7 notes the marts now built.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds the staged diff; CPO merges.

amendments: (none)
