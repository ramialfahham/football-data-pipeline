# Task contract — the tracker has a backup in the repo: a generated snapshot nobody can edit, cite, or let drift

objective: >
  GitHub's suspension kept the repository and lost every issue. On GitLab the tracker — the
  roadmap milestones, the fourteen page reviews, every approval recorded on an issue — has no
  copy anywhere. This branch adds `scripts/snapshot_tracker.py`, which writes every milestone
  and every issue (open and closed, with bodies) into `docs/tracker/gitlab_snapshot.md`
  through the existing `glab` login, and the three guarantees that keep that file a backup and
  not a second roadmap: a hook that refuses any edit to it, a test that fails on any change the
  script did not make, and a line in `CLAUDE.md` that says it is read only when GitLab is
  unreachable. It is regenerated at the end of every session and rides in the handover commit,
  excluded from the review patch and the review hash.

refs: >
  GitLab #142 (this task, `Task` template; the What/Why/How below are copied from it). The
  product owner's words, 2026-09-12, in chat: "what if gitlab will be suspended as well. then
  the roadmap is lost" → "only if we don't produce two sources that contradict each other" →
  "go", to the three guarantees stated in the reply before it (nobody can edit it; it cannot be
  cited; it cannot drift far). `CLAUDE.md` "Which source answers which question": the GitLab
  issue answers "what is required"; that stays.

protected_override: >
  `.claude/hooks/tracker_snapshot_gate.py` (new), `.claude/settings.json` (one hook
  registration), `.claude/review_routing.json` (three list entries for `docs/tracker/**`). The
  product owner's words that require this mechanism are quoted in `decisions_taken` below, in
  the commit message and in the MR head; under working_agreement §11 the durable approval is his
  merge of this MR.

scope_paths:
  - scripts/snapshot_tracker.py
  - docs/tracker/gitlab_snapshot.md
  - .claude/hooks/tracker_snapshot_gate.py
  - .claude/settings.json
  - .claude/review_routing.json
  - tests/test_tracker_snapshot.py
  - tests/test_materialisation_policy.py
  - tests/test_governance_doc_parity.py
  - docs/agent_guardrails.md
  - CLAUDE.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: one script (reads GitLab through `glab api`, writes one markdown file), one generated
    file, one hook, one registration entry, three routing entries, one test file, one guardrails
    row, one `CLAUDE.md` table row plus one operational line, the handover.

  downstream (a guard's blast radius is every future edit): the hook fires on every `Edit`,
    `Write`, `MultiEdit` and `NotebookEdit` and denies ONLY when the target is inside
    `docs/tracker/` in this repo; every other path returns 0 with no output. The script writes
    the file with Python's own file write, which no edit-time hook sees — by design: the script
    is the one writer. The routing entries: `hash_exclude_paths` and `review_exclude_paths` gain
    `docs/tracker/**`, so a snapshot refresh never moves a review binding and is never pasted to
    a reviewer; `artifact_only` gains it, so a commit touching only the snapshot (with or
    without the handover) is review-exempt like the handover itself. `git_discipline.py` and
    `check_task_artifacts.py` read those lists as `fnmatch` patterns — `**` is fine there (the
    lists already use it). The test pins the header's checksum against the body, the hook's deny
    and pass, and the three routing entries. Nothing else reads `docs/tracker/`.

  what stops being enforced if it is wrong: nothing enforced today — the tracker had no backup.
    If the hook mis-denies, the message says the file is generated and names the script. If the
    checksum test fails, the file was changed by something other than the script: regenerate.

  layer_rules: n/a. deploy_order: none.

  blast_radius: a NEW DENY on edits under one path that holds one generated file; three routing
    entries that EXEMPT that path from review — the risk is a second roadmap accreting there
    unreviewed. What closes it and what does not: the hook closes every tool edit; the checksum
    test catches every change that did not also rewrite the header (a slip, a tool that bypassed
    the hook, a merge accident); a DELIBERATE write by a shell route that also recomputes the
    header passes the test — the checksum is self-consistency, not provenance, and nothing in
    CI can re-read GitLab without a token. That residual is the same class as deleting the
    handover or committing with `--no-verify`: forbidden by rule (`CLAUDE.md`), not prevented by
    mechanism, and no wider than the handover already carries (an artifact-only, hash-excluded
    file every session writes by hand with no hook on it at all).

acceptance_criteria:
  - `python scripts/snapshot_tracker.py` writes `docs/tracker/gitlab_snapshot.md` from the live
    tracker through `glab`: every milestone, every issue open and closed with its body, grouped
    by milestone in a deterministic order; the header names the script, the UTC time, the sha256
    of the body, and says in one line that the file is a backup, read only when GitLab is
    unreachable, never edited. The first snapshot is committed.
  - Nobody can edit it: on the real repo an `Edit` and a `Write` to `docs/tracker/gitlab_snapshot.md`
    are refused with the hook's own text; a `Write` to `docs/tracker/anything.md` too; a write
    anywhere else passes. `tests/test_tracker_snapshot.py`: the checksum in the committed
    snapshot's header equals the sha256 of its body; changing one character → red (mutation
    shown); the hook denies and passes as above on a temp repo; malformed stdin fails open; the
    hook is wired; `docs/tracker/**` is in all three routing lists.
  - It cannot be cited: `CLAUDE.md`'s table gains the one row; the operational notes gain the
    session-end line ("run the snapshot before the handover commit").
  - It cannot drift far: the routing entries are in place, proven by `--staged-hash` being
    unchanged before and after a snapshot regeneration on this branch, and by the patch not
    containing the file; the handover names the routine.
  - `pytest tests/` green with `main`'s count plus the new tests; ruff clean on the script, the
    hook and the test.

decisions_taken: >
  CPO, 2026-09-12, in chat: "go" — to the three guarantees put to him after his condition "only
  if we don't produce two sources that contradict each other": (1) nobody can edit it — a hook
  refuses the write and a checksum test fails any change the script did not make (CORRECTED at
  round 1, see amendments: the test fails any change that did not also rewrite the header; a
  deliberate forgery by shell is forbidden by rule, not prevented — told to him); (2) it cannot
  be cited — the `CLAUDE.md` table keeps the GitLab issue as the source and names the snapshot a
  backup read only when GitLab is unreachable; (3) it cannot drift far — regenerated at the end
  of every session, stamped with the time.

  THE SHAPE IS THE BUILDER'S: one script, one generated markdown file, one hook in the shape of
  the other edit-time gates, three routing entries so a refresh is never a reviewed diff.

  THRESHOLD — NEW MECHANISM: yes, required above. THRESHOLD — RECURRING COST: none (a `glab`
  read of the tracker once per session, on the product owner's own login; no schedule).

decisions_reserved:
  - Merge-request heads in the snapshot (decisions live there too); a mirror of the repository
    itself (an account or credential decision); an automated schedule instead of the session-end
    routine; CI verifying the snapshot against live GitLab (needs a read token in CI — a
    credential decision), which is the only thing that would turn the checksum from
    self-consistency into provenance.

done_when:
  - The five criteria proven; the mutation shown red; `pytest tests/` and ruff green; the first
    snapshot committed and the patch free of it.

amendments:
  - After round 1 (cto-reviewer): the checksum was represented — in this contract's
    `blast_radius`, in the evidence, and to the product owner — as failing "any change the script
    did not make". It does not: the header is computed by the same process that writes the body,
    so a writer who bypasses the hook by a shell route AND recomputes the header passes the test.
    The claim is corrected everywhere it was made (this contract, the evidence, the `CLAUDE.md`
    row, the guardrails row, the test's docstring, the hook's docstring) to what the pair actually
    gives: the hook closes every tool edit, the checksum catches every slip, and a deliberate
    forgery is a rule-forbidden act of the `--no-verify` class, no wider an exposure than the
    handover already carries. Provenance would need CI to re-read GitLab, which needs a token —
    reserved as the product owner's credential decision. The product owner is told in the report
    that the guarantee he approved was overstated in that one respect. No code changes; the
    routing exemption stays, with its residual named rather than claimed closed.
  - After round 1 (platform-reviewer): `is_governed` compared the path case-sensitively, and on
    Windows `Docs/Tracker/gitlab_snapshot.md` is the same file — a spelling away from silent. Now
    case-folded before the prefix test; three case variants pinned by a parametrised test; the
    mutation (fold removed) goes red on all three. Tests 22 → 25.
  - After the full-suite run: `tests/test_materialisation_policy.py`, which walks every tracked
    file for a superseded materialisation claim, read an old issue body quoted in the snapshot
    ("Staging as view") as a claim of the repo and failed twice. The snapshot is a quotation of
    the tracker, exactly the class its `_is_bookkeeping` already exempts for
    `docs/product_direction_threads.md` ("history, not a live claim"), so `docs/tracker/` joins
    that exclusion with the same reason — the test file is added to `scope_paths` for that one
    line. The other tree-wide walker, the host-fingerprint pin, deliberately keeps scanning it:
    an address in an issue body should fail CI. Criterion 5's suite count: measured on the final
    code once this lands.
  - After the second full-suite run: one more tree walker of the same class —
    `tests/test_governance_doc_parity.py` requires every file that mentions a guard or protected
    path to be either checked (`COVERED_FILES`) or exempted with a reason (`SWEEP_EXEMPT`); the
    snapshot quotes issue bodies that name those paths. It joins `SWEEP_EXEMPT` beside
    `docs/audits/` ("dated snapshots of what was true on the day") with its own reason line — a
    file that RECORDS, not one that GOVERNS. The test file joins `scope_paths` for that one entry.
    That makes three tree walkers exempting the snapshot for the same reason and one (the address
    pin) deliberately not; the pattern is named in the evidence so the next walker's author knows
    which side the snapshot falls on.
