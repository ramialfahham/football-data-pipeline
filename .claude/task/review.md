# Review — chore/backfill-pl-history-seasons — 2026-06-20

> Path A: season-depth config refactor — make per-competition `history_seasons`
> authoritative (drop the `max(global_lo, …)` clamp in seasons.py), retire
> `V1_SEASON_WINDOW_YEARS` -> `DEFAULT_SEASON_WINDOW_YEARS`, + PL history_seasons 10 -> 11.
> Required reviewers for this footprint (ingestion/** + registry + data_contract -> data-engineer;
> tests/** -> cto; scope-auditor always): all three PASS, blinded. No FAIL, no ESCALATE.
> See "post-review delta" below for the one comment-only change applied after the blinded round.

diff_sha256: 0a1ee130e563ea8d1cfde9102bba3cb4a2152fd38e19598d91c7ba4a4d6a0c11

## scope-auditor
VERDICT: PASS
risks_checked:
- All changed paths inside the amended scope_paths; the diff changes ONLY PL's history_seasons
  (no other league/field) + the documented refactor files. The `amendments:` entry records the
  expansion with CPO Path-A authority (this conversation, 2026-06-20), on a clean tree per §2.
- No §10 decision taken unilaterally: the constant rename is an internal, non-user-visible name
  (agent-executable) and CPO-flagged; the docs/working_agreement.md edit is a faithful name-sync
  within the existing rule (not a rule change); the phantom-current-season hardening and PD/SA/L1
  Phase 2 are correctly RESERVED, not bundled. No Appendix A anti-pattern recurs.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Lower-bound arithmetic: traced lo = resolved_current - (history_seasons - 1) for PL
  (2026-10=2016, correct), BL1 (2025-9=2016, unchanged), and all hs=1/hs=2 comps (clamp removal
  is harmless wherever competition_lo >= the old global_lo, which holds across the registry). No
  off-by-one; no unintended change to any existing competition's output.
- Economy/default MAX_SEASONS cap preserved: the want_multi=False branch still computes the band
  and truncates to band[-max_band:]; dropping the early global_lo variable does not break the csv
  or band branches (lo is set unconditionally before any branch). A PL hs=11 economy run still
  yields the last 3 seasons, not 11.
- Rename complete (no V1_SEASON_WINDOW_YEARS in ingestion/ or tests/; imports ordered; no NameError),
  CPO approval for the history_seasons increase is recorded, and the #514 carry-forward invariant
  is unaffected (it lives in the competition runner, not in _seasons_for_ingestion).

## cto-reviewer
VERDICT: PASS
risks_checked:
- The new test test_full_profile_history_seasons_authoritative_below_default_floor is a genuine
  regression guard: traced against the OLD code (effective_season_min monkeypatched to 2017 ->
  lo=max(2017,2016)=2017 -> range(2017,2027)) it would FAIL the assertion list(range(2016,2027));
  against the new code it passes. Not a vacuous/tautological test.
- Monkeypatch targets the correct import site (ingestion.api_football.seasons.effective_season_min,
  the name bound in the consuming module). Catalogs supply >=10 seasons so the < 2 HTTP fallback
  (_season_years_from_leagues_seasons_endpoint) never fires — no real network call. global_lo dead
  variable fully removed; import ordering intact; no CI gate (python-ci = pytest only) is at risk.

## post-review delta
- After the blinded round (which the cto-reviewer PASSED) the cto noted one non-blocking nit: the
  seasons.py MODULE docstring still described the old "rolling 10-year window". Applied the cto's
  requested fix — a COMMENT-only change to the seasons.py module docstring (lines 6-9), no logic,
  scope, or test change. Rebound diff_sha256 from a244e7bc...9b2a to 0a1ee130...0c11. No reviewer's
  risk analysis is affected: scope unchanged (seasons.py already in scope + reviewed), no behaviour
  change, and it is precisely the cto's recommended fix. The full delta is visible in review_input.patch.

## escalations
(none)
