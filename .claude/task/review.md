# Review — perf/ingestion-hoist-per-run-reads — 2026-08-08

> Wave 1 item 1 of GitLab #33. Required reviewer set for the staged paths: `scope-auditor`
> (always), `data-engineer-reviewer` (`ingestion/**`), `platform-reviewer` (`tests/**`). No guard
> path is staged, so no opus promotion applies and all three ran on their pinned sonnet floor.
>
> REBASED onto `main` @ `5c268e5` after !24 merged, and the hash below is REBOUND accordingly.
> !24 and this branch both rewrite `.claude/task/{contract,review,review_input}.md/patch`, and
> nothing else — `git diff --name-only` of each against the old base `72a6a69` overlaps on exactly
> those three. All three were resolved by taking THIS branch's version; `escalations.log` came
> from main untouched, so !24's standing-rule entry is intact.
> The reviewers' verdicts stand because the CODE did not move: `git diff dc97c8e a80b5f2` (the
> pre- and post-rebase commits) shows changes only in `.gitlab-ci.yml`, `escalations.log`,
> `tests/test_ci_data_job_invariants.py` and `tests/test_governance_hooks.py` — all of them !24's,
> arriving via the new base. No `ingestion/**` file and no line of
> `tests/test_ingestion_read_hoisting.py` differs. Full suite re-run on the rebased tree: 683
> passed, 1 skipped, exit 0 (666 on main + 17 here), so the two changes coexist.
>
> The hash MOVED without the code moving, which is expected and is why it must be rebound: it
> covers code + `contract.md`, and `contract.md` now diffs against !24's version rather than !23's.
> Recomputed with `scripts/check_task_artifacts.py --base gitlab/main`, i.e. the way CI computes
> it — NOT with `--staged-hash`, which on a second commit covers only the increment.

diff_sha256: 07c5c9b48e25da5877df3fc236ba3d394cc0b2ba2594d68f7b30a0941a14a46d

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: the patch touches exactly the 8 ingestion files, `tests/test_ingestion_read_hoisting.py`
  and `contract.md`, all listed in `scope_paths`. No file outside scope.
- The two DEFERRED sub-items ("lazy `_finished_fanout_has_gaps`", "cache the FIXTURES_NEXT
  payload") judged against their stated reasoning: the first is mooted because the hoist already
  removes the query from that function, leaving only an in-memory branch to make lazy; the second
  is a pruned equality read rather than a full-table scan and is recorded on #33 as follow-up.
  Ordinary builder scoping on diff-size grounds, not a narrowing of approved work — #33 marks item
  1 "mechanical, no CPO decision".
- The "46 -> 2, not 1" correction traced against the diff rather than taken on trust:
  `phase1_covered = read_coverage(ctx.client)` is hoisted above the per-competition loop while
  `run_ingest_completeness_checks` keeps its own independent read after Phase 2's fanout write,
  and a test fails if someone collapses it further. Evidenced by code plus a load-bearing test.
  The further collapse-to-1 is correctly routed to `decisions_reserved` as a DQ-gate-weakening §10
  question rather than decided.
- Threshold declarations present and consistent with the diff: recurring cost reduced, no new
  mechanism, no guard weakened.
- `impact_map` present; its "nothing in dbt is touched" claim is evidenced by the diff scope, and
  RAW schemas, payloads and merge keys are untouched.
- No credentials, no new dependency, no widened permission anywhere in the patch.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 was a FAIL and it was correct, on the finding that mattered most in this MR: the
  completeness-snapshot hoist made a FIRST RUN WORSE. `read_prior_snapshot()` returns None when
  there is no prior record, None was also the "caller supplied nothing" sentinel, so all three
  readers re-fetched — 1 hoisted read + 3 re-reads = 4 against a baseline of 3, in exactly the
  case each reader's docstring says it exists for. Round 2 verified the cure: a private `_UNREAD`
  sentinel, all three guarding `if payload is _UNREAD:`, so an explicit None is treated as the
  answer and a first run costs ONE read.
- Hoist 1 safety re-derived independently: grepped for writers of RAW_APIF_FIXTURE_DETAILS and
  confirmed only `loads/batch_fixtures.py` (Phase 2) writes it, and the Phase-1 loop touches only
  FIXTURES_NEXT/LEAGUES/STANDINGS/TEAMS/INJURIES/COACHES. Nothing writes it between the 45 uses of
  the hoisted value. Confirmed `run_ingest_completeness_checks` still issues its own read after
  Phase 2, matching the "2, not 1" correction.
- Hoist 2 safety, all three failure paths traced: the mutation `already_captured.add(...)` runs
  only inside the success branch after both the load and the superseded-row delete succeed; an
  incomplete fetch never enters `written_keys` (preserving the #896 "only a complete fetch may
  supersede" invariant); a quota cut mutates only over what was actually stored; a BQ-write
  exception skips the mutation entirely, leaving the set as accurate as a fresh read. Worst case
  is one redundant re-fetch, never a silent miss.
- Hoist 3: both callers check `universe is None` rather than truthiness, so a legitimately empty
  universe does not fall back; `_query_universe` never returns None, so the orchestrator's failure
  sentinel and the "no answer" case cannot collide.
- Verified the required-argument change breaks no caller: the orchestrator is the sole production
  caller of `run_squads_for_competition`, `load_player_profiles_global`, `load_player_teams_global`
  and `resolve_ingest_mode`.
- No change to the fetch plan or API-call count anywhere — BigQuery reads only. This matters
  because `captured_player_team_seasons` feeds a fetch-side skip, so a stale value would have
  changed API spend.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL (two findings) and round 2 FAIL (two more), all four correct and all four accepted.
  Round 1: the correctness pin could be defeated by ADDING an `all_covered=None` parameter to
  `run_ingest_completeness_checks` and wiring Phase 1's result in — a behavioural test cannot see
  that; and the other three hoists had defaults, so deleting one keyword argument at the single
  orchestrator call site restored a full-table scan with the suite green. Fixed structurally: the
  signature is pinned to `["client"]`, and the three hoisted arguments now have no defaults.
- Round 2: the required-argument fix closed only the narrowest revert. Moving the computation back
  INSIDE the loop while still passing it restores the whole quadratic scan with every callee-level
  assertion green. Also caught `done_when` claiming a multi-competition orchestrator count test
  that does not exist. Both fixed — an AST pin on call placement, and a rewritten `done_when`.
- Round 3: traced `_calls_inside_any_loop` by hand against the AST walk and confirmed the three
  current call sites sit outside their loops, so the new test is not vacuously green, and it does
  catch the literal round-2 revert path.
- Verified the earlier decoration fixes are real: `test_completeness_keeps_its_own_coverage_read`
  monkeypatches `completeness.read_coverage` (imported into that module's namespace) and asserts
  the call rather than grepping source; `test_a_first_run_still_costs_one_snapshot_read_not_four`
  counts `read_latest_payload_json` rather than `client.query`, matching that reader's Storage
  Read API path.
- Checked `_CountingClient`'s substring markers against the real SQL in `coverage.read_coverage`
  (FIXTURE_DETAILS + JSON_QUERY_ARRAY), `squads.captured_player_team_seasons` (RAW_APIF_PLAYERS +
  UNNEST) and `player_universe._query_universe` (`players_payload`) — all faithful, none
  vacuously-always-zero.
- FURTHER BYPASS FOUND AND RECORDED, not failed on: wrapping the read in a helper defined outside
  the loop but INVOKED inside it evades the AST check, because the call sits in a sibling
  `FunctionDef` rather than the `For` subtree, and no callee-level test catches it either. A
  plausible non-adversarial refactor, beyond the disclosed name-aliasing limit. It does not reopen
  either round-2 finding, both of which are closed for the reverts identified.
- Fail direction: the new assertions live in `tests/`, run under `test:python`, which has no
  `changes:` filter, so they fire on every MR and every push and redden the pipeline. Fail closed.
- Delta touches no `*requirements*.txt`, `package*.json`, `.github/workflows/**`, `.gitlab-ci.yml`
  or `.claude/hooks/**`, so dependency hygiene, guard fail-open mechanics and duplicated
  enforcement do not apply.

## escalations
(none)
