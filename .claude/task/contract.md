# Task contract — #63: bind the review to content identity, not to rendered diff text

objective: >
  `validate:governance` fails on `!33` and would fail on every merge request after it. The local
  commit gate and the CI recompute produce DIFFERENT `diff_sha256` values for provably identical
  commits, so the check that binds a review to its code cannot pass at all.

  Root cause: both sides hash the RENDERED PATCH TEXT — the human-readable output of `git diff`.
  That is a presentation format whose bytes depend on git version, platform and diff settings, so
  the same content can hash two ways on two machines. This change hashes CONTENT IDENTITY instead
  (`git diff --raw`: mode, blob SHAs, status, path), which is byte-identical everywhere.

  A second defect in the same family is fixed with it: the local side diffs `--staged`
  (HEAD -> index) while CI diffs `base...HEAD`, so on a MULTI-COMMIT branch the local number is
  simply the wrong diff. That is the standing `CLAUDE.md` warning that `--staged-hash` is "the
  WRONG number" on a second commit; it cost two wasted cycles on `!33` alone.

refs: >
  GitLab #63 (the failure, the five ruled-out hypotheses, and the local demonstration).
  ⚠ BLOCKS `!33` and `!27` — both are waiting on this and neither can go green until it merges.
  Context only, not in scope: #33 item 13 (an MR pipeline can write production raw) and #2
  (`data_paths` rebuilds prod on governance-only changes), both read while tracing the CI job.

protected_override: >
  CPO, in session 2026-08-12, recorded in `.claude/task/escalations.log` BEFORE this contract was
  written: asked whether to fix the check as its own task, answered **"yes"**, and on method
  **"Fix it systematically like a top-notch engineer would do it."**
  `.claude/hooks/` is a PROTECTED prefix (`task_contract_gate.py:66`), so `git_discipline.py` may
  not be edited inside an ordinary contract.
  ⚠ THE AUTHORITY IS NARROW and the log says so: it covers HOW the review-binding hash is
  computed, in the two implementations that must agree, plus the tests and docs describing it. It
  does NOT extend to any other hook, the routing file, the reviewer briefs, or the commit-form
  deny package. None of those is touched.

scope_paths:
  - .claude/hooks/git_discipline.py
  - scripts/check_task_artifacts.py
  - tests/test_governance_hooks.py
  - docs/agent_guardrails.md
  - CLAUDE.md
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/review_input.patch
  # added by amendment 1 — see amendments
  - .claude/active_work.md

impact_map: >
  ⚠ REQUIRED HERE BECAUSE THE PATH IS PROTECTED, not because a model moved
  (`task_contract_gate.py:195` — "a guard's blast radius is every future task in the repo, which is
  wider than almost any model's"). `protected_override` answers "may you"; this answers "do you
  know what breaks".

  who COMPUTES the hash — exactly two, and they must agree or every commit is falsely rejected:
    `.claude/hooks/git_discipline.py::_staged_diff_bytes` (line ~94) — feeds BOTH the PreToolUse
      commit gate (line ~659, denies `git commit` on mismatch) and the `--staged-hash` CLI
      (line ~729), which is how `review.md`'s number is produced.
    `scripts/check_task_artifacts.py` (line ~165) — the CI recompute, invoked by
      `.gitlab-ci.yml`'s `validate:governance` as
      `--base "origin/${CI_MERGE_REQUEST_TARGET_BRANCH_NAME:-main}"`.

  who CONSUMES it: `.claude/task/review.md`'s `diff_sha256` line, on every branch. Nothing else
    parses it, but SIX places DESCRIBE it, and the first draft of this list missed one:
    the two implementations, `tests/test_governance_hooks.py` (which hand-mirrors the CI command
    in `branch_hash`), `docs/agent_guardrails.md:57`, `docs/working_agreement.md:183`, the
    CLAUDE.md warning being deleted — and **`.claude/active_work.md:118`**, which repeated the same
    now-false "on a multi-commit branch `--staged-hash` is the WRONG number" sentence.
    ⚠ THAT MISS MATTERED MORE THAN THE OTHERS: `handover_in.py` injects `active_work.md` into
    EVERY new session at SessionStart, so the sentence deleted from CLAUDE.md would have survived
    verbatim in the one file guaranteed to be read first, and a fresh agent would have collapsed
    commits to work around a trap that no longer exists. Found by platform-reviewer, opus, which
    also correctly noted the completeness claim behind this list did not hold. Added under
    amendment 1.

  ⚠ BLAST RADIUS — EVERY EXISTING `review.md` HASH BECOMES INVALID. The number is a function of
    the algorithm, so changing the algorithm invalidates every recorded value. **`!27` and `!33`
    both need rebinding after this merges.** Stated here so it is planned rather than discovered.
    Nothing else in the repo, no model, no mart, no shipped number and no page is affected — this
    file set contains no SQL, no seed and no export.

  deploy_order: none. No image, no schedule, no warehouse object. The hooks take effect on the
    next tool call locally and on the next pipeline in CI, independently.

  layer_rules: none engaged. `check_layer_contract.py` judges `dbt_project/models/**`, untouched.

decisions_taken: >
  1. HASH `--raw`, NOT THE RENDERED PATCH. `git diff --raw` emits
     `:mode mode <blobA> <blobB> STATUS<TAB>path`. Blob SHAs ARE content hashes, so the output is
     identical on every platform and git version, forever. The exclusion pathspec, `--no-renames`
     and `--no-abbrev` are all kept exactly as they were.
     EVIDENCE, measured on this machine with identical commits (GitLab #63):
       rendered -U3 -> 0c1ef8af...  51,628 bytes
       rendered -U0 -> ca1afb7d...  46,687 bytes   <- same content, DIFFERENT hash
       --raw        -> 974cd829...   1,459 bytes   <- stable
  2. DIFF FROM THE BASE ON BOTH SIDES, so the local number is the same diff CI recomputes even on a
     multi-commit branch. `_review_patch_bytes` already resolves the base correctly via
     `_cumulative_diff` / `_base_commit`; those are REUSED rather than a second resolver written.
  3. The `CLAUDE.md` warning about `--staged-hash` is DELETED, not qualified — the trap it warns
     about stops existing. A correction replaces; it never accumulates.
  4. ⚠ FOUND WHILE BUILDING, AND NOT IN THE APPROVED PLAN: `_base_commit` preferred a LOCAL `main`
     branch over the remote-tracking ref. A local `main` is a cached copy that goes stale the
     moment anyone branches from `gitlab/main` without checking main out — the normal flow here.
     Measured on this branch: local `main` sat at `57175fc` while `gitlab/main` was `a2b4184`, two
     merges newer. The consequences were not cosmetic — the reviewers' patch listed
     `deploy/nightly/README.md` and `tests/test_alert_policy_recipe.py`, files from the
     already-merged #61 that this task never touched, and the hash could not have matched the CI
     recompute no matter what bytes were fed to it.
     Preference order is now `gitlab/main` -> `origin/main` -> `main`, matching
     `check_task_artifacts.py::default_base`, which already resolved the live remote for exactly
     this reason.
     ⚠ THIS IS INSIDE THE OBJECTIVE, NOT SCOPE DRIFT, and the distinction is worth stating: the
     stated objective is that the local gate and the CI recompute agree. They must agree on the
     BASE as well as on the bytes; fixing only the bytes would have shipped a change that still
     could not pass. It is recorded here rather than folded in silently.

  5. ⚠ THE GUARD'S BEHAVIOUR WHEN IT CANNOT COMPUTE THE HASH AT ALL — declared here because both
     opus reviewers were right that it is a guard-behaviour change and a docstring is the wrong
     place to introduce one.
     The first draft swallowed every exception and returned `b""`, calling that fail-closed. It was
     the opposite, and it was REPRODUCED before being fixed: `--staged-hash` printed
     `sha256(b"")` = `e3b0c442…` with EXIT 0; that value goes into `review.md`; the gate recomputes
     it from the same broken call; the two AGREE; the commit passes bound to ZERO bytes — no code,
     not even `contract.md`. Deterministic, not a race, and the states that reach it are the ones
     `_base_commit` already names (a `--single-branch` clone, a shallow checkout, unrelated
     histories) — real, because these hooks travel to other repos by design.
     NOW: failure returns `None`, distinguishable from an empty diff. `--staged-hash` refuses to
     print a hash it did not compute (stderr, exit 1) and the gate denies with its own message.
     ⚠ THIS IS A DELIBERATE DEPARTURE from the file's fail-open house rule, and the case where the
     departure is right: an unresolvable base is not a hook bug, it is the guard being unable to do
     its job, and the deny is actionable (fetch the base branch, or set `GOVERNANCE_BASE`).
     platform-reviewer offered the alternative — let the exception propagate so the existing loud
     fail-open banner fires — and explicitly left the choice open. Denying is strictly stronger
     than warning-then-allowing, so denying is what ships.
     Pinned by `test_staged_hash_refuses_to_emit_a_hash_it_could_not_compute` and
     `test_commit_gate_denies_when_the_hash_cannot_be_computed`, both shown to go RED against the
     `b""` behaviour before being trusted green.

  6. ⚠ `GOVERNANCE_BASE` RESOLVES THROUGH MERGE-BASE, NOT TO THE BRANCH TIP — round 4, and it is a
     correction to item 5's own fix rather than to the original defect.
     The escape hatch added in round 2 resolved the override with `rev-parse <ref>^{commit}`, i.e.
     the TIP. The CI twin spells the base `f"{args.base}...HEAD"` — three-dot, the COMMON ANCESTOR.
     Point the variable at a branch that has moved on (the documented use) and the two halves hash
     different bytes: the local diff carries the branch's own changes PLUS a reverse delta for
     everything merged upstream since the branch was cut. Red pipeline on a correct branch, and a
     reviewers' patch full of already-merged work — the same symptom item 4 records as the measured
     harm of the stale-local-`main` bug, and the exact defect this whole task exists to remove,
     reintroduced through its own escape hatch.
     ⚠ AND THE TEST COULD NOT SEE IT: the override was pointed at a direct ANCESTOR of HEAD, where
     tip and merge-base are the same commit, so reverting the fix left the suite green. Third test
     in this task that passed either way. Now uses a genuinely diverged ref and was proved RED
     against the tip-resolving version before being trusted.
     Every other base path in the repo is merge-based, including the ref loop directly below it.
     Found by platform-reviewer (opus) at the round cap; round 4 authorised by the CPO ("fix it"),
     recorded in `escalations.log` before this round ran.

  # THRESHOLD DECLARATIONS
  NEW MECHANISM — **no**. Same gate, same `sha256`, same `review.md` field, same failure message.
    Only the bytes fed to the hash change.
  RECURRING COST — **no, and it drops**. The hashed input goes from ~51,600 bytes to ~1,460 on
    this branch's own diff. No new job, query, dependency or schedule.
  GUARD LOOSENED — **no, and it is TIGHTENED in one place.** On discriminating power: a rendered
    patch is DERIVED from the blobs and cannot differ unless a blob SHA differs, so every content
    change that moved the old hash moves the new one. Mode changes and add/delete/modify status are
    carried in `--raw` explicitly. What is removed is only the ability of a PRESENTATION setting to
    change the value — never protection, only a false-rejection surface. cto-reviewer attacked this
    directly (mode-only changes, add/delete, renames, binaries, textconv filters, `diff.context`)
    and could not construct a content change that moves the old hash but not the new one.
    ⚠ TIGHTENED: an uncomputable hash now DENIES instead of resolving to a constant that matches
    itself (item 5). The first draft of this branch loosened it, both reviewers caught it, and the
    fix leaves the gate stronger than it was before this task started.
  SHIPPED NUMBERS — **no**. No SQL, seed, mart or export is touched.

decisions_reserved:
  - Why CI's specific value (`be3a493d...`) differs from this machine's is NOT diagnosed, and this
    change does not need it diagnosed: it removes the entire class by not hashing a rendering.
    ⚠ Deliberately not chased further — the remaining candidates (git version, a platform default)
    are unobservable from here and the fix is correct against all of them.
  - Whether `test_local_staged_hash_equals_ci_recompute` should ALSO run under a second git
    version in CI. That would catch the real cross-platform case rather than a proxy, but it is a
    new CI job and therefore recurring cost — CPO-class, and out of scope here.
  - #33 item 13 and #2, both noted in `escalations.log` and neither touched.

done_when:
  - `.claude/hooks/git_discipline.py` and `scripts/check_task_artifacts.py` hash the SAME bytes for
    the same content, both from the base, both `--raw`.
  - NEW TEST, invariance: the same content hashed under two different rendering settings produces
    ONE hash. ⚠ It must be shown to FAIL against the pre-change implementation, not merely to pass
    after it — a test only ever seen green proves nothing.
  - NEW TEST, multi-commit: after two commits on a branch, the local `--staged-hash` equals the CI
    recompute. ⚠ Also shown to fail against the pre-change implementation.
  - `test_local_staged_hash_equals_ci_recompute` (line ~1691) still passes UNCHANGED — it is the
    existing load-bearing invariant and this change must not need it edited.
  - `python -m pytest tests/test_governance_hooks.py -q` green, then the full suite green.
  - `docs/agent_guardrails.md` describes the new mechanism; the CLAUDE.md warning is gone.
  - END TO END, and the only proof that counts: `!33`'s `review.md` rebound to the new hash, and
    `validate:governance` GREEN on the runner. Until that is observed, this is unproven.

amendments:
  - id: 1
    date: 2026-08-12
    authority: >
      Not a new CPO ruling — the SAME protected-path authority already recorded in
      `escalations.log` for this task, which covers "the tests and docs that describe" the hash.
      `.claude/active_work.md` is one of those docs and was missed when `scope_paths` was drawn.
      Recorded as an amendment rather than edited quietly because the gate is right that an
      out-of-scope edit is drift however obviously it belongs.
    adds:
      - .claude/active_work.md
    why: >
      `active_work.md:118` repeated the now-false warning that `--staged-hash` is "the WRONG
      number" on a multi-commit branch, verbatim. ⚠ `handover_in.py` injects that file into EVERY
      session at SessionStart, so deleting the sentence from `CLAUDE.md` while leaving it there
      would have preserved it in the one file guaranteed to be read first — and a fresh agent
      would keep collapsing commits to dodge a trap that no longer exists. Found by
      platform-reviewer (opus), which also caught that the impact_map's "nothing else parses it"
      completeness claim was drawn from a grep that missed this file. Both the file and the claim
      are corrected.
