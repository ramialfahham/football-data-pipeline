# Task contract — dead issue references in the files that instruct

objective: >
  767 references across `CLAUDE.md`, `docs/` and the memory store point at GitHub issues that no
  longer exist — 257 distinct numbers, of which 180 survive as merged PRs in git history and 77 are
  gone entirely. Fix the ones that DIRECT ACTION, guard the two files where a dead pointer causes
  harm, and leave the archaeology alone. Do not sweep 767 edits.

refs: >
  Measured: GitLab's highest issue is **#114**, so every `#115+` reference is GitHub-era and
  unreachable. Counts — `CLAUDE.md` 5, `docs/` 292, memory 470. Of 257 distinct, 180 appear in a
  commit message (recoverable), 77 do not.
  The trigger: going to build the player page, the chain read memory -> "the authority is issue
  #753's design-state comment, trust its sections, never a summary of them" -> **#753 does not
  exist**. The instruction not to trust the summary survived; its referent did not.
  `.claude/task/escalations.log` `2026-09-10 chore/dead-issue-references` — the CPO's direction
  that the context cleanup finishes BEFORE product work resumes, and that dead references go first:
  *"do as recommended but before we get back to product work I want to have this setup/cleanup for
  better context management first."* That entry also carries the REVISED nine-step plan and
  supersedes the six-step list in the preceding `chore/authority-map-in-claude-md` entry.
  This is step 3 of the revised plan; steps 1 and 2 merged as `!169` and `!170`.
  ⛔ THE `refs:` LINE HERE PREVIOUSLY CITED THE OLDER ENTRY AND CALLED THIS "step 3 of that plan".
  That entry's step 3 is "split `escalations.log`". `scope-auditor` FAILed it, correctly: the
  citation was to a REAL log entry for a DIFFERENT sequence, which is a harder defect to catch than
  an invented ruling and is the fourth branch running to produce this class.

scope_paths:
  - CLAUDE.md
  - .claude/active_work.md
  - tests/test_no_dead_issue_refs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/escalations.log

impact_map: >
  writers: no model, mart, export or site source. One new test file; two markdown files.

  downstream: `CLAUDE.md` loads every session and is read by Cursor too; `active_work.md` is the
    handover a cold session continues from. The new test runs in CI's `test:python`.

  blast_radius: the new test asserts a property that is TRUE at commit time and will fail any future
    edit that reintroduces a `#115+` reference into either file. That is the intent — it is a
    ratchet, not a one-off cleanup. Nothing else in the repo reads either file.

  deploy_order: none.

acceptance_criteria:
  - `CLAUDE.md` and `.claude/active_work.md` contain ZERO references to `#115` or above.
  - `tests/test_no_dead_issue_refs.py` fails if one is reintroduced — proven by mutation, not by
    passing once.
  - The test explains WHY in its own failure message, so a future session that trips it knows the
    number is unreachable rather than merely unwelcome.
  - `CLAUDE.md`'s "Next:" line no longer names an issue at all.
  - No file outside `scope_paths` is touched: the 292 references in `docs/` are deliberately LEFT.
  - `pytest tests/` and `ruff check .` stay green.

decisions_taken: >
  ⛔ THE 292 REFERENCES IN `docs/` ARE DELIBERATELY NOT SWEPT, and that is the main decision here.
  Rewriting them is a ~25-file mechanical diff no reviewer can meaningfully read, for almost no
  value per edit: most are PROVENANCE ("shipped #627", "corrected under #33"), where the sentence
  already carries the fact and the number is decoration. 180 of the 257 distinct numbers are
  recoverable from git history anyway.
  WHAT IS FIXED IS WHERE A REFERENCE INSTRUCTS. `CLAUDE.md` said "Next: player insights chain
  (#153 -> #156)" — the always-loaded file telling every session its next work is two issues that
  resolve to nothing.

  A WARNING WAS ALREADY THERE AND DID NOT WORK. The memory index says, in bold, "any GitHub number
  in these files is a pointer to nothing — re-derive from code". I read that index every session
  and still followed #753. So this ships a TEST, not another sentence.

  THE "NEXT" LINE NAMES NO ISSUE AT ALL. Any number written into a file this durable goes stale
  silently and then instructs. It points at `glab issue list`, which cannot rot.

  ⚠ LOW NUMBERS ARE NOT AMBIGUOUS, CHECKED BEFORE ASSUMING. `#33` in `CLAUDE.md` reads like a
  GitHub-era audit reference, and GitHub's number space overlapped GitLab's. It resolves: GitLab #33
  is "Pipeline cost/scalability: diagnosis and ordered plan", exactly what the sentence means. So
  the `>=115` boundary is real and the guard can use it.

  THRESHOLD — NEW MECHANISM: one test, in the existing suite, no new runner or gate config.
  THRESHOLD — RECURRING COST: none.

decisions_reserved:
  - The 292 `docs/` references and the 470 in memory. Whether they are worth a sweep at all is the
    CPO's; my recommendation is no for docs, yes for memory (memory is loaded every session and is
    where #753 sent me).
  - Whether the 13 superseded `session_handoff_*.md` files (68 KB) should be deleted from the memory
    store. The index already declares them superseded and one is still being cited. Memory lives
    outside the repo so it is not in this MR either way.
  - Steps 4-9 of the REVISED plan (logged in full under `2026-09-10 chore/dead-issue-references`):
    split `escalations.log`; where parked work lives (10 stashes, one holding the built player
    Overview tab); memory-vs-handover-vs-wireframe precedence; a non-code place for reviewer
    reasoning; decision history out of code plus a hook; memory cut + size budgets.

done_when:
  - The guard is mutation-proven and the two files are clean.
  - `pytest tests/` and `ruff check .` green.

amendments:
  - none yet
