# Review — fix/33-completeness-gate-refetch-skip — 2026-08-14

diff_sha256: bc092a4c14893e4c095dbcc41441adf8acc9cf72503e2a9de8ec62aa3b34550d

rounds: 2

<!--
⚠ REBOUND after rebasing `a13c16e` -> `b5dbd80`. The MR reported a merge conflict: three MRs
landed on main while this was in review (#65 CI worktree prune, #57 taxonomy seed, #367 landing
page). The conflicts were the four `.claude/task/*` artifacts ONLY — no code conflict, and
`git diff --name-only main..HEAD` confirms the eleven paths are still exactly this branch's.
Resolution: mine for contract/review/review_input (they describe THIS task); UNION for
`escalations.log`, checked by arithmetic rather than eye — main 2,737 + (mine 2,412 − base 2,372)
= 2,777, which is what the resolved file has, so no entry was dropped or duplicated.
Full suite re-run against the new base: 808 passed / 1 skipped (up from 798; main brought tests
with it). The reviewed CODE did not change, so the verdicts below stand and were not re-run —
only the binding moved.
-->


<!--
Round 1: data-engineer PASS (traced the causal chain independently). scope-auditor PASS.
         platform FAIL with three findings, all correct and all about the same thing — the
         production fix was untested and one existing test was passing for the wrong reason.
Round 2: all three PASS.

The finding worth remembering: the six gate-level tests all called
`detect_stagnant_per_team_gaps` directly with a hand-built `skipped` set, so DELETING the one
production line that populates it left the whole suite green. The tests proved the gate's logic
and proved nothing about the fix.
-->

## scope-auditor
VERDICT: PASS
risks_checked:
- The `GUARD LOOSENED` declaration checked against the code: the exemption is keyed per
  (league, entity), not a blanket disable, and `PER_TEAM_GATED` is confirmed untouched — matching
  `decisions_reserved`, which reserves that question rather than deciding it.
- The rejected alternative (dropping TRANSFERS from `PER_TEAM_GATED`) is described accurately, so
  the CPO can see what was not done and why.
- CPO ruling "Do as recommended" located in `escalations.log`, with two paths in plain language, a
  stated recommendation and the reason for rejecting the other — the §11 form, and it precedes the
  contract citing it.
- Amendment 2's standing-rule citation traced to the actual 2026-08-08 entry, and the edit it
  authorises confirmed confined to adding one dict key with no behavioural change.
- Every changed file is inside `scope_paths`; nothing outside it appears in the patch.
- The `done_when` claim that skip visibility is "asserted by a test on the emitted text" checked
  against what shipped — honestly narrowed by extracting `skipped_exemption_note`, not aspirational.
- Threshold declarations checked against the diff: no new mechanism, no recurring cost, no dbt or
  mart file touched. No credential-shaped content anywhere in the patch.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Re-derived the causal chain rather than accepting it: the skip at `competition_runner.py:204`
  recorded nothing; `orchestrator.py:283` builds `per_team_missing` restricted to `PER_TEAM_GATED`;
  `detect_stagnant_per_team_gaps` flags any pair >0 in both runs with no knowledge of whether a
  fetch was attempted; the orchestrator then exits 3 before dbt. Diagnosis holds.
- Whether the exemption can swallow a real gap: traced the "skipped run N, fetched run N+1" case —
  on the fetch run `record_skipped` is not called, so the pair re-enters gating on a real
  comparison, and `persist_fixture_statistics_missing` stores the true counts either way, so the
  prior snapshot is not poisoned.
- COACHES recorded but not gated: `per_team_missing_by_league_entity` iterates `PER_TEAM_GATED`
  only, so no `LEAGUE/COACHES` key can ever exist to match — provably inert, exactly as its comment
  claims.
- Record-at-call-site vs the gate calling `should_refetch` itself: recording avoids two places
  deciding "due", and the failure mode of a future phase forgetting to record is a FALSE ALARM, not
  a silent hole — the safe direction.
- `PipelineContext` checked for construction, equality and serialisation breakage from the new
  field: one construction site, no `asdict`, no pickling, no equality comparison anywhere.
- Class-1 sweep: no raw writer, no merge logic, no cadence or history-window knob, no
  `WRITE_TRUNCATE`, no quota change. The cadence itself (`should_refetch`) is untouched.

## platform-reviewer
VERDICT: PASS
risks_checked:
- ⚠ FAILED round 1 on the finding that mattered: the production line
  `ctx.record_skipped(result.league_code, "TRANSFERS")` had NO test that would fail if reverted —
  every new test drove the gate function directly with a hand-built set. Re-verified at round 2
  that `test_a_skipped_league_is_recorded_for_the_completeness_gate` now drives
  `run_transfers_for_competition` itself and asserts both directions, and that deleting the line
  fails exactly that test.
- ⚠ FAILED round 1 on a subtler one: `test_a_skipped_league_writes_nothing_at_all` used a
  duck-typed fake with no `record_skipped`, so the new call raised `AttributeError`, the
  pre-existing broad `except Exception` swallowed it, and the test stayed green while the code it
  exercised was broken. Re-verified the fake now implements the real surface and the test asserts
  `ctx.errors == []`, so that divergence cannot recur silently.
- ⚠ FAILED round 1 because the "never silent" print was unreachable by any test while the contract
  claimed it was asserted on the emitted text. Re-verified the text now lives in
  `skipped_exemption_note()` with two direct tests, and that the residual uncovered code is a
  truthiness check plus `print`, matching the pattern already accepted for every other note line in
  that function.
- Both directional proofs checked against the code: disabling the exemption fails 3 tests, making
  it exempt everything fails 8 including pre-existing ones. The guard is still armed, and
  `test_fetched_pair_still_fails` is the test that proves it.
- Ordering and flake risk: `detect_stagnant_per_team_gaps` iterates `sorted(current.items())` and
  the exemption list is built with `sorted(...)`; no unsorted set or dict iteration reaches an
  assertion.
- `field(default_factory=set)` confirmed the correct idiom, not a shared mutable default; the one
  construction site passes no override.
- The exact-equality dict edit confirmed as adding one key without relaxing the assertion — the
  correct way to absorb a new outcome key, and the assertion is what caught it in the first place.

## escalations
(none — the CPO ruling "Do as recommended" is recorded in `.claude/task/escalations.log` and was
verified there by `scope-auditor`. No question was put to the CPO during the review cycle.)
