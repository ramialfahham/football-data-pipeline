# Review — reviewers stop reviewing the review's own paperwork (#868 follow-up)

branch: fix/868-review-scope
diff_sha256: c7faa3465b951e4ee2bc6a4d094a951b801369debb4c45e161e77e2e9e654db6
rounds: 4
rounds_cap_override: >
  CPO, 2026-08-01. Told that rounds 1-3 had all FAILed and a fourth was needed, he
  answered "ok go ahead", having also said "You are running into multiple rounds again" —
  so the cost was named to him before he authorised it.
  The rounds are also the argument for the change. Unlike #370, where rounds 6-12 found
  nothing a visitor would see, EVERY finding here was a real machinery defect.
  Round 1: the fail-closed CI twin still enforced the repealed PASS floor, so the change
  was inoperative at the PR boundary — and the contract's `impact_map` asserted a
  verification I had not performed. Round 2: `--review-patch` emitted the staged diff
  while every brief promises the cumulative branch diff. Round 3: my fix for that silently
  narrowed in several real clone shapes while its own comment claimed it was safe. Two
  guards turned out to be pinned by nothing. Three briefs kept the repealed rule, the last
  because the phrase straddles a line break and my sweep was line-based.

> **All three required reviewers PASS at this hash.**

## cto-reviewer
VERDICT: PASS
risks_checked:
- `_base_commit` hunted for a narrowing path across seven states — local `main`, stale
  `main`, `origin/main` only, neither ref, unrelated histories, shallow clone, multiple
  root commits. None yields less than the cumulative branch diff; stale `main` fails
  LARGER; unrelated histories raise. The only case where base equals HEAD is when the
  branch work is already an ancestor of `main`, where the staged increment IS cumulative.
- Fail direction: `_load_routing` still returns None on a malformed file, yielding no
  exclusions and the WHOLE diff — the correct direction for reviewer input. The new
  `raise` sites are reachable only from the `--review-patch` CLI branch, never from the
  PreToolUse path, so a bug in them cannot lock the workflow. Commit gate still fails
  open; CI twin still fails closed.
- The two PASS floors agree in value, counted region and message, pinned in both
  directions on both copies.
- Nothing enforced less than before: routing `paths` untouched, all eight guard rows
  present, exactly two files newly leave `hash_exclude_paths`, and `contract.md` stays
  hashed — pinned against both the fixture and the real routing file.
- The four quoted CPO rulings verified verbatim in `escalations.log` before relying on
  `protected_override`; the amendment cites ruling (3)+(4), not the reviewers' FAIL.
- Repealed-rule sweep done independently, whitespace-collapsed plus a windowed search:
  no live statements remain.

## platform-reviewer
VERDICT: PASS
risks_checked:
- `_base_commit` traced state by state: detached HEAD, stale `main`, already-merged
  branch, `origin/main` only, linked worktree, `--single-branch` clone, unrelated
  histories. No narrowing in any of them.
- Fail-on-revert verified for the four newest tests; none can pass vacuously, and
  `test_every_task_artifact_is_classified` now asserts its file list is non-empty.
- PreToolUse reachability confirmed clean: `_base_commit` is reachable only through the
  `--review-patch` argv branch, which returns before `read_event()`. Zero added git calls
  per Bash call.
- Item 8 parity checked line by line: floor, regex, marker and message identical in the
  hook and the CI twin and asserted on both sides; the other hand-copied loops are
  byte-unchanged by this diff; `review_exclude_paths` has one consumer, so no twin.
- Re-run and interruption safety: `--review-patch` is read-only and deterministic; the
  gate changes mutate nothing.
- No dependency, lockfile, workflow, credential or build surface in the diff.

## scope-auditor
VERDICT: PASS
risks_checked:
- Base resolution: enumerated every ref state and none yields a patch narrower than the
  cumulative branch diff; the range equals CI's `base...HEAD`, and both refusal paths are
  pinned by tests that fail on revert. The `origin/main`-only shape — the specific hole
  this reviewer failed at round 3 — is closed.
- Authority after the delta: `protected_override` quotes rulings (1)-(4) verbatim, the
  single amendment cites ruling (3)+(4) rather than reviewer findings, and the rulings are
  now in `escalations.log`, the durable place. Nothing new is decided; every delta file is
  inside `scope_paths`; nothing in `decisions_reserved` is touched.
- Doc-sync on the nine corrected places: the "`.claude/task/**` excluded" claim now
  matches the mechanism in both directions across eight briefs and both docs, with the
  authority-visible invariant asserted against the real routing file. Whitespace-collapsed
  sweep found no residual "Default verdict FAIL".
- Credentials and thresholds on the delta: nothing credential-shaped, no env block, no
  workflow or permission change.

## escalations
(none)

## owed — recorded by the reviewers, none blocking
- A shallow `actions/checkout` clone (feature ref only, no `main`/`origin/main`) reports
  the graft boundary as a root commit, so the fallback would narrow rather than raise.
  Unreachable today: `--review-patch` has no CI caller and the governance job checks out
  at `fetch-depth: 0`. Remedy if it is ever wired: test
  `git rev-parse --is-shallow-repository` in the fallback branch.
- `_cumulative_diff`'s returncode `raise` is not itself revert-detected, because the
  loud-failure test raises earlier in `_base_commit`. The invariant is pinned for the
  reachable failure family; this is a second layer on the same one.
- `TEMPLATE.md` and `REVIEW_TEMPLATE.md` are now hidden from reviewers. They are durable
  rule statements rather than task notes, so the authority-vs-notes split arguably puts
  them on the visible side.
- The test fixture's comment says it "mirrors the REAL `review_exclude_paths`" while
  omitting three real entries. Comment accuracy only; the real list is pinned elsewhere.
