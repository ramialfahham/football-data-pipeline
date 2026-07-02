# Review — chore/handover-refresh-623 — 2026-07-02

> G3 Lock artifact. Final bookkeeping handover refresh (prep a fresh chat): corrects the two items the CPO
> resolved AFTER #623 locked — the median-band word is "median" (CONFIRMED, not the "provisionally middle"
> #623 recorded), and naked-% is RESOLVED (carry the denominator atoms from int_player_season_position__metrics
> + show the {num} of {den} · {pct}% triple — a shaping step, not an open call). All 4 wireframe-rework items
> now settled/resolved; NEXT = resume the parked wireframe. Required set (routing): scope-auditor only —
> .claude/active_work.md (artifact) + .claude/task/contract.md (hashed).
>
> Round 1 (hash 3480e36e) FAIL — contract.md named "int_legs__player_match's source model" for where the
> ratio % is computed, inconsistent with active_work.md + the memory (int_player_season_position__metrics).
> Round 2 (hash 9b2ad88b, THIS lock) — contract corrected to name int_player_season_position__metrics; all
> three artifacts now consistent. scope-auditor PASS.

diff_sha256: 9b2ad88be2c731d573befd22dce92bfeb78839ffcd0e8d46e68b15727541b6fe

## scope-auditor
VERDICT: PASS
risks_checked:
- Stash-recovery brittleness — the handover directs recovering stash@{0} on docs/391-player-stats-percentile-spec
  via `git stash pop`, with the explicit fallback "if the pop conflicts, don't fight it: this rework list is
  the source of truth, re-create 12_player_stats.md from it." The fallback prevents DATA LOSS (the 4-item
  rework list is complete enough to recreate the spec), so the handoff is safe; a pre-pop `git stash show`
  verify would be a nicety but isn't required. Held.
- Data-layer-settled ≠ export-layer-shipped (naked-% atoms) — item 4 is correctly RESOLVED at the DATA layer
  (the atoms exist + the % is computed in int_player_season_position__metrics); the actual carrying of num/den
  into the payload is a SEPARATE follow-up (the benchmark→player-export wiring PR), correctly listed in
  decisions_reserved + the callout, so a cold chat won't mistake it for already-shipped. Scope =
  .claude/active_work.md + .claude/task/**; bookkeeping-only; both CPO resolutions faithfully recorded; no
  §10 decision made. Held.

## escalations
(none) — records the two CPO resolutions already made this session (median word = "median"; naked-% = carry
the atoms). The wireframe rework itself + the benchmark→export wiring PR are reserved follow-ups.
