# Review — fix/896-guard-partial-writes — 2026-08-08

> #33 item 8a. Required reviewer set for the staged paths: `scope-auditor` (always),
> `data-engineer-reviewer` (`ingestion/**`), `platform-reviewer` (`tests/**`). No guard path is
> staged, so no opus promotion applies and all three ran on their pinned sonnet floor.

diff_sha256: 78b98eb0873c4cefd9e571132ba75ad5821489e0d20ac48178d782a007400342

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL, and it was correct: the 8a/8b split, the CPO's "go ahead with 8a", and the
  four-loader scope were asserted only in `contract.md` and appeared nowhere in
  `escalations.log`. The blanket 2026-08-08 #33 approval covers item 8 as ONE thing ("raw
  merge-on-write with the raw_archive backup first"), so a split that changes what item 8 IS is a
  new decision. Fourth time this repo has ruled that recording a ruling in the contract is not
  recording it (2026-07-31, 2026-08-01, 2026-08-08 standing rule).
- Round 3: verified the new `escalations.log` entry cures it — it records the split, the
  file:line evidence that forced it, the CPO's quoted ruling, the FOUR-loader scope stated
  explicitly rather than left inferable, the five excluded gaps named by file, the forward limit
  on 8b (`PLAYER_PROFILES`/`PLAYER_TEAMS` must never take a `league_code`-keyed delete), and a
  correction to #33's own counts. No ambiguous edge left for a later reader to widen or narrow.
- `contract.md`'s AUTHORITY paragraph cites that entry by title and explains why the blanket
  approval does not cover a split; no drift between the two documents.
- The `done_when` rewrite replaces an overstated verification claim with what was actually
  verified. A correction toward honesty, needing no separate authority.
- Mechanism/cost: no merge-on-write, no DELETE, no `league_code`-keyed delete anywhere in the
  diff. Every change either skips a write or threads the existing `result_is_complete` primitive.
  No new mechanism, no new recurring cost, no credential-shaped content.
- Item-8b pull-forward: checked for merge-on-write or DELETE logic arriving early — none.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL, and it was correct: `_patch_transfers` monkeypatched `transfers_response_for_team`
  out entirely and substituted a hand-rolled stand-in, so the real guard at
  `fixture_scheduling.py:513` — protecting RAW_APIF_TRANSFERS, 6.99 GiB, 59% of raw — was never
  executed by any test. Reverting it to `complete = True` left the whole suite green.
- Round 2: traced the fix rather than accepting it. `transfers_response_for_team` calls the bare
  name `fetch_merged_paged`, resolved against `fixture_scheduling`'s module globals at call time,
  so patching `fixture_scheduling.fetch_merged_paged` lands exactly where the lookup resolves and
  the real `result_is_complete(data)` now executes on every call.
- Re-derived the revert outcome independently instead of trusting the report: with
  `complete = True` hardcoded, the body-error case fails (no quota flag is set by a body error, so
  the loader's own per-iteration check never trips either) and the direct helper test fails —
  exactly two cases, matching the claim.
- Checked why the other three loaders needed no equivalent fix: their `result_is_complete` calls
  are inline in the same module `_patch_fetch` already patches, so round 1's indirection defect
  was specific to transfers and the fix is correctly scoped to it.
- Read `result_is_complete` (`http_client.py:83-107`) and confirmed it combines both signals — a
  body-level error AND the latched daily-quota flag — as its docstring and the guards claim.
- Verified guard ordering in all four loaders: the quota flag is checked at the top of the loop,
  and `result_is_complete` is called immediately after each fetch and before the next one, which
  is what that primitive's docstring requires.
- Discard-versus-mark: correct for these tables. They are ONE row per league, so there is no
  per-key withholding available as in `squads.py`; `player_squads.py` faces the same shape and
  also discards.
- Idempotency: every write is still `append=True`; no merge-on-write or DELETE introduced.
- Completeness honesty: every discard path appends an `INCOMPLETE ... DISCARDED` entry to
  `ctx.errors`, so a degraded run is visible rather than silent.
- No new API call, endpoint, cadence or history-depth change; the guard only gates the final
  `load_json_to_bq`, the fetch loops are unchanged.
- `teams.py` extending `team_ids` even when the snapshot is discarded: traced the caller chain —
  `team_ids` is populated primarily by `fetch_merge_and_persist_fixtures` BEFORE this runs, so a
  degraded `/teams` fetch does not starve the coaches/transfers/squads phases, and the
  unconditional extension is unchanged from `main`. Not a defect introduced here.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL (two findings) and round 2 FAIL (one), all three correct and all three accepted.
- Round 1: the real transfers guard was untested, and the transfers quota case passed for the
  wrong reason — `load_transfers_batch`'s pre-existing per-iteration check fired on the second
  team. Fixed by patching the HTTP layer beneath the real helper, plus a direct unit test of the
  helper's own return value.
- Round 2, the sharpest finding on this branch: the mid-loop quota cases were masked for ALL FOUR
  loaders, not just transfers. The fake sets the latched flag on iteration 1 and every loader's
  PRE-EXISTING top-of-loop `break` catches it on iteration 2, so the new check could be regressed
  to body-errors-only — blind to the quota flag, which is half of what #896 is about — and all
  four cases would still pass on the old code.
- Round 3: verified the fix structurally for all four. The top-of-loop guard is checked BEFORE
  the fetch, so on iteration 1 the flag is always unset; `_invoke_*_one` passes exactly one
  team/season, so the loop body runs once and that guard cannot supply the verdict. The only
  remaining path to `writes.tables == []` is the new `result_is_complete` call — confirmed
  independently in `transfers.py:41-49`, `coaches.py:50-63`, `standings.py:34-47`,
  `teams.py:32-68`, including the `if complete:` branch around the envelope write.
- Confirmed the test and production code import the SAME `quota` module object, so the fake's
  `errors_quota._http_quota_exhausted = True` is visible to the loader under test rather than
  mutating a disconnected copy — the fake genuinely exercises the quota-latch path.
- Confirmed the claimed differential: under a body-errors-only regression the four new
  single-iteration cases fail while the four mid-loop cases still pass, which is precisely what
  makes the new test non-decorative.
- Checked the LOADERS tuple arity change (4 to 5) is applied consistently at every parametrize
  site, and that the pre-existing tests still use the multi-item invoke.
- Confirmed production code is unchanged since round 2 by diffing the patch against direct reads
  of the five source files.
- Fail direction: the guards only ever suppress a write — fail closed on doubt. The new
  assertions run under `test:python`, which has no `changes:` filter, so they fire on every MR
  and every push.
- Re-run safety: a discarded snapshot writes nothing and appends an error; the next run retries
  from scratch with no partial state to corrupt.
- Quota global-state leak: the autouse `_reset_quota` fixture resets before and after every test
  in the file; no cross-test leak or ordering dependency found.

## escalations
(none — the 8a/8b split was ruled by the CPO before this branch began and is recorded in
`.claude/task/escalations.log`, entry "2026-08-08 — #33 item 8 SPLIT into 8a/8b".)
