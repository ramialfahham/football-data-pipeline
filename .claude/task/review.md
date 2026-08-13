# Review — fix/63-review-hash-content-identity — 2026-08-12

diff_sha256: e1a379b2c94e353456b2b37813f5d85bb18b1254b304a0e38bc76aeace7650ba

rounds: 4

rounds_cap_override: >
  ONE CPO grant, recorded in `.claude/task/escalations.log` BEFORE the round it authorises and
  verifiable there independently of this file: round 3 hit the documented cap with
  scope-auditor and cto-reviewer PASSING and platform-reviewer FAILING on a single finding. The
  finding was verified by the builder before being brought over, three options were offered with a
  stated recommendation, and the CPO answered **"fix it"**.
  WHY IT RAN TO FOUR, stated plainly rather than excused: every round failed on something NARROWER
  than the last, and rounds 2, 3 and 4 each ended with a REPRODUCED defect rather than a reviewer
  opinion. Round 4 was scoped to the single round-3 finding; platform-reviewer listed four further
  residuals and explicitly judged none of them grounds for a fifth round. They are filed as **#64**.

⚠ Routing for these paths requires cto-reviewer AND platform-reviewer (`.claude/hooks/**` is one of
the three guard paths carrying both, at the opus floor) plus the always-on scope-auditor.
⚠ All three verdicts below cover the FINAL diff. scope-auditor passed round 3 and was re-run after
round 4 changed the code, tests, contract and escalations log — a PASS that predates the delta it
is supposed to cover is not a PASS.

<!--
Round-by-round, kept because the progression is the record:
  1  scope-auditor FAIL  — contract RESERVED the 21 label strings while the diff shipped them.
     analytics FAIL      — (that was #57; not this branch)
  1  cto FAIL + platform FAIL — INDEPENDENTLY found the same hole: `_staged_diff_bytes` returning
                          b"" on an unresolvable base was not fail-closed. `--staged-hash` printed
                          sha256(b"") with exit 0, that value goes into review.md, the gate
                          recomputes the same empty value, they AGREE, and the commit passes bound
                          to ZERO bytes. Reproduced in a scratch dir before fixing.
  2  cto FAIL           — the deny message promised a `GOVERNANCE_BASE` escape hatch the hook never
                          read; the justification for departing from fail-open rested on it.
                          Also `if not blob` conflated None with a legitimately empty diff.
     platform FAIL      — same two, plus: the base reorder had NO test (reverting it left the whole
                          suite green), a stale warning survived in `.claude/active_work.md` (which
                          is injected into EVERY session), and a test inherited CLAUDE_PROJECT_DIR
                          so it could pass for the wrong reason.
  3  scope PASS · cto PASS
     platform FAIL      — `GOVERNANCE_BASE` resolved to the branch TIP while CI resolves it through
                          MERGE-BASE, so the halves disagreed the moment the override named a
                          branch that had moved on — the very defect this task removes,
                          reintroduced through its own escape hatch. The test could not catch it:
                          it used a direct ancestor, where tip and merge-base coincide.
  4  all three PASS.
⚠ THREE of this task's tests passed against the defect they were written to catch, each found by
running them against a reverted copy rather than trusting a green run.
-->

## scope-auditor
VERDICT: PASS
risks_checked:
- Enumerated every `diff --git` header in the patch against `scope_paths`: all seven files are
  listed, none is a scope violation.
- Verified the round-cap override is a real recorded ruling in `escalations.log` with the
  situation, options and a stated recommendation, and that it reads as recorded BEFORE round 4
  rather than backfilled — the round-3 verdicts and the exact defect are documented first, then
  the answer.
- Checked `decisions_taken` item 6 against the actual `_base_commit` delta: the claim (round 2's
  hatch resolved to the ref TIP, now resolves through `merge-base` to match CI's three-dot
  `base...HEAD`) is exactly what the diff does, and it honestly flags itself as a correction to
  item 5's own fix rather than to the original defect.
- Verified the protected-path authority's stated boundary holds: no other hook, no routing file,
  no reviewer brief, no commit-form deny package appears in the diff.
- Checked item 6's test claim against the test itself — it builds a diverged `upstream` branch and
  asserts `ancestor != tip`, rather than the direct ancestor the earlier version used.
- Swept all seven files for credential-shaped content and widened CI permissions: none.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Verified `protected_override` against `escalations.log` — the ruling exists, predates the
  contract, and the contract reproduces its narrow bound rather than widening it. Confirmed
  `.claude/hooks/` is genuinely a protected prefix (`task_contract_gate.py:66`) and that routing
  puts platform beside the CTO on that path.
- Verified the round-cap override is recorded in PROSPECTIVE voice, and said explicitly that
  ordering two additions inside one cumulative diff is not git-provable — evidence is consistent,
  and it declined to claim proof it did not have.
- Attacked the `--raw` argument for lost discriminating power across mode-only changes, add/delete,
  renames, binaries, textconv filters and `diff.context`; could not construct a content change that
  moves the old hash but not the new one. Binaries get STRONGER — the rendered form emits
  "Binary files differ" with no blob SHA.
- Ruled on the fail-open departure: the outer handler is untouched and still fails open loudly on
  hook bugs; exactly one value now fails closed, and the alternative (`sha256(b"")` matching
  itself) was a bypass rather than a fail-open. Declared in `decisions_taken` item 5, not smuggled
  into a docstring.
- On round 4: confirmed the capability removed was a FAKE exit — a tip-resolved base produced a
  hash CI could never reproduce — and that a real, CI-consistent exit still exists (any commit in
  HEAD's own ancestry).
- Thresholds, dependencies, credentials, workflow permissions: nothing added, nothing widened;
  the deferred second-git-version CI job is correctly parked in `decisions_reserved` as CPO-class
  recurring cost.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Traced both hash implementations by hand and confirmed they compute identical bytes: local
  `git diff --staged <merge-base> --raw --no-renames --no-abbrev <pathspec>` versus CI
  `git diff --raw --no-renames --no-abbrev <base>...HEAD <pathspec>`; three-dot IS merge-base, so
  the two now agree on the base as well as on the bytes. The hand-mirror `branch_hash` moved to
  `--raw` in the same commit, so the third copy does not lie.
- Verified the round-3 finding is closed at `_base_commit`: the override resolves through
  `merge-base HEAD <resolved>`, and both failure paths (unresolvable value, no common ancestor)
  raise loudly rather than falling back to a different diff.
- Verified the override test now DISCRIMINATES structurally rather than incidentally: `upstream` is
  cut after the feature commit and gains its own file, so diffing from the tip emits an extra
  deletion row and the two hashes cannot coincide. Also confirmed the fixture is non-vacuous.
- Re-verified all five of its round-2 findings closed, each against the code rather than the
  contract's narration.
- Guard orientation: the local hook still fails OPEN on an escaping exception (handler intact);
  the CI backstop still fails CLOSED (`check=True`). Both `_staged_diff_bytes` callers handle
  `None`; no third caller exists.
- Re-run and interruption safety: every changed path is a read-only git invocation with a 30s
  timeout and no writes.
- Listed four residuals and explicitly judged none of them grounds for a fifth round — filed as
  **#64**, together with one PRE-EXISTING local/CI reviewer-set split it noticed in passing.

## Verification (all LOCAL — no CI run on this branch yet)

`pytest tests/test_governance_hooks.py` **295 passed** · the five fast governance gates pass ·
`check_task_artifacts` OK.

⚠ **THE PROOF THAT MATTERS HAS NOT HAPPENED YET.** This change exists because `validate:governance`
fails on `!33`. Until `!33` is rebound to the new hash and that job goes GREEN on the runner, this
is a fix that passes its own tests, which is exactly what the previous implementation also did.
`done_when` records that, and it is not satisfied by this file.

⚠ **Merging this invalidates every existing `review.md` hash** — `!27` and `!33` both need
rebinding afterwards. Stated in the contract's `impact_map` so it is planned, not discovered.
