# Task contract — #19: split the RULE from the RECORD in the working agreement

> Branch `docs/19-compile-dont-append` from `main` (`5dbee13`). No protected path, so no
> `protected_override`. Nothing on the structural surface, so no `impact_map`. No `site_v2/src/`
> path, so no `acceptance_criteria`.

objective: >
  Stop `docs/working_agreement.md` being half its own changelog, without removing a single rule,
  and add the guard that stops it re-accumulating.

  THE PROBLEM, measured rather than quoted from the issue. §2 is 14,448 characters of a 26,374
  character document: 55% of it, and six times the next largest section. It interleaves four kinds
  of text — the operative rule, its rationale, dated corrections, and review archaeology — so an
  agent reading it under pressure retrieves the narrative, which is memorable, over the rule,
  which is buried in it.

  THE FINDING THAT MAKES THIS SAFE. Every narrative passage proposed for removal was checked
  against the durable record BEFORE being touched. Seven of eight are already recorded in
  `.claude/task/escalations.log` or `.claude/review_routing.json`'s `_doc`. So this is
  DE-DUPLICATION, not deletion of history: the same fact stored in two places with nothing
  reconciling them, which is GitLab #1's defect class in a different medium. Evidence per passage
  is under `decisions_taken`.

  THE ONE THAT STAYS. The delta-re-review rationale ("re-running every reviewer at full depth
  every round is what made a nine-round PR cost what it did") has NO counterpart: `nine-round` and
  `delta review` both return zero hits across both record files. It stays in §2 untouched. That is
  the safety rule doing its job, and it is why the rule is "locate the counterpart first" rather
  than "delete narrative".

  THE GUARD WAS PLANNED, BUILT, AND WITHDRAWN. #19's reusable conclusion is that when something
  recurs the answer is a hook, a test or a skill, so this task added a test asserting the rule
  documents carry no narrative. `platform-reviewer` FAILed it three rounds running, each time with
  a legitimate RULE sentence the test would wrongly reject, and each fix surfaced more. The CPO
  withdrew it and shipped the compression alone. Filed as GitLab #26.

  THE REASON IT DOES NOT WORK, recorded so #26 does not restart from the same premise: rules and
  history are written in the SAME ENGLISH. "A defect that round 2 found is not re-litigated in
  round 3" is a rule and contains "round 2 found". No word list separates the two, and the failure
  is ASYMMETRIC — a missed narrative waits for a reviewer, whereas a false hit fires on a real
  rule, and the cheapest way to green the build is to REWORD THE RULE. The guard would corrupt the
  document it protects. So this branch ships the de-duplication only.

refs: >
  GitLab issue #19 ("Compile, don't append: every governing artifact is 50-60% its own
  changelog"). Plan approved in plan mode 2026-08-07
  (`~/.claude/plans/splendid-tickling-bumblebee.md`), including the guard, which the plan flagged
  as a NEW MECHANISM and therefore the CPO's; approved with *"start #19"* against a plan
  recommending it be included. Builds directly on !12 (GitLab #1), whose test already guards the
  count and enumeration claims inside the section being edited.

scope_paths:
  - docs/working_agreement.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log

decisions_taken: >
  THRESHOLD DECLARATIONS, stated because no gate parses this field.

  NEW MECHANISM — NO, NOT ANY MORE. This task was planned with one: a test asserting the rule
  documents carry no NARRATIVE markers. It was built, and the CPO WITHDREW it after three review
  rounds (see `amendments`). `tests/test_governance_doc_parity.py` is byte-identical to `main` on
  this branch — verified with `git diff main -- tests/test_governance_doc_parity.py`, which is
  empty, and `tests/` is no longer in `scope_paths`. This diff adds no test, no hook, no script
  and no config surface. It is prose only.

  RECURRING COST — NO. Nothing executes that did not execute before.

  NEW EXTERNAL SURFACE — NO.

  GUARD INVARIANT — UNCHANGED. No hook, agent brief, routing row or protected path is edited.
  §2 DESCRIBES the guards; this task does not touch them. Every rule §2 states still binds after
  this change, and the diff is reviewable on exactly that question.

  THE COUNTERPART EVIDENCE, per removed passage. Located by proximity inside a single record
  entry, not by whether a word appears somewhere in a 1,154-line file — the first version of that
  check asked the looser question and produced four false positives, which is why the evidence
  below names an entry rather than a file:
    1. `consulted:` demoted -> escalations.log, "demoting the day-old consulted field to a
       reviewer habit", under CPO ANSWER "Trim the weak parts, then reframe".
    2. G3 bypasses at opus depth -> review_routing.json `_doc` lines 143-145, "hollows out the
       very depth the opus pin exists for, since the G3 commit-gate bypasses WERE fail-open and
       hook-test-coverage findings".
    3. scope-auditor haiku -> sonnet -> escalations.log, "moving `scope-auditor` haiku -> sonnet,
       which is a permanent per-commit increase".
    4. the split's rounds / "both on all eight" -> review_routing.json `_doc`, "three documents
       claiming BOTH reviewers on all EIGHT guard paths while routing gave platform two".
    5. FAIL/PASS rules rewritten -> escalations.log, the CPO quote "the reviewer needs to have the
       critical attitude but it's allowed to approve and not invent some finding".
    6. PASS required two named risks / #370 rounds 6-12 -> escalations.log, "every brief required
       two named risks for a PASS, so on correct code a reviewer was OBLIGED to find something",
       and separately "rounds 6-12 found nothing a visitor would see".
    7. delta re-review / nine-round PR -> escalations.log, the `2026-07-22 chore/review-economics`
       entry: "the guardrails PR cost nine rounds", and the chosen path "delta re-review + round
       cap + consult first". FOUND ONLY ON THE SECOND ATTEMPT: the first search asked for
       "nine-round" and "delta review" and got zero, because the log writes "nine rounds" and
       "delta re-review". Recorded because a literal search returning zero is not evidence of
       absence, and this is the second time in this task that it read as though it were.
    8. evidence artifacts / typo voided every PASS -> escalations.log, "two evidence artifacts sat
       inside `diff_sha256`, so correcting a typo voided every PASS already given".

decisions_reserved:
  - Whether the same pass is run on `.claude/review_routing.json`'s `_doc`, on `CLAUDE.md`, and on
    the 88 memory files. All three are excluded here for stated reasons: the routing file is
    PROTECTED and its `_doc` is read by reviewers rather than by builders, so it is load-bearing
    differently; `CLAUDE.md` is loaded into every session, so a bad cut costs every future one;
    the memory files are outside the repo and ungoverned by any gate. Each is its own task, and
    whether to do them at all is the CPO's.
  - Whether any RATIONALE compressed to a clause here should have been kept in full. Rationale is
    what stops a rule being re-litigated, so shortening it is a judgement with a real failure mode.
    Bias throughout was toward keeping; anything ambiguous stayed. Flagged so a reviewer checks the
    direction of the error rather than only its presence.

done_when:
  - "Every rule present in §2 before the change is present after it. The diff is reviewable on
    that single question, and nothing but RECORD text is removed."
  - "`git diff main -- tests/` is EMPTY. The withdrawn guard leaves no residue, and the diff is
    prose plus task artifacts only."
  - "GitLab #1's existing anchors still pass. §2 holds the count and enumeration claims that
    `test_every_prose_count_matches_the_derived_value` anchors on, so that suite is the mechanical
    check that this edit did not damage them — and it is the reason the compression could touch
    those sentences safely at all."
  - "`.venv/Scripts/python.exe -m pytest tests/ -q` green at 645, the same count as `main`, since
    no test is added or removed. MEASURED, not predicted: `pytest --collect-only -q` gives 645 for
    the tree and 40 for `tests/test_governance_doc_parity.py`, which `git diff main --quiet` shows
    is identical to `main`. This line said 646 until the suite was actually run — a contract claim
    about the code written as a prediction and not re-checked against the finished tree, which is
    #904's exact defect class. 646 was the count WITH the withdrawn narrative test, which added one
    parametrized case. No reviewer caught it; the measurement did."
  - "Section sizes reported before and after, measured rather than asserted."
  - "The five offline gates pass, with `--base gitlab/main` for the artifact gate."

amendments: >
  ONE amendment, 2026-08-07, on a clean tree (doc + test stashed by explicit path, popped
  immediately). NO PATH IS ADDED — `escalations.log` was already in `scope_paths`. What changes is
  the METHOD.

  AUTHORITY: `.claude/task/escalations.log`, the `⭐ CPO RULING: AUTHORITY FOR THE METHOD CHANGE`
  block under the `2026-08-07 docs/19-compile-dont-append` entry. CPO answer, in his words:
  *"go ahead as recommended"*, to path (a) of two named paths.

  THIS BLOCK PREVIOUSLY CITED NOTHING, and `scope-auditor` FAILED round 1 for exactly that. It was
  right: the justification below was written by the builder and rested on the failure message of a
  test the builder wrote in the same task, which is circular. §2 says extending a contract without
  recorded CPO authority is drift by definition, and it means it. The reasoning that follows is
  kept because it is the reasoning PUT TO the CPO; it was never the authority.

  APPROVED METHOD: remove a RECORD passage only where its counterpart is already in the durable
  record; a passage with no counterpart STAYS and is listed here.

  AMENDED METHOD: a passage with no counterpart is MOVED into `escalations.log` and replaced by a
  citation. Nothing is deleted either way.

  WHY IT CAME UP. Three passages had no counterpart anywhere — the acceptance-criteria failure
  ("a finished page passed both its reviewers while opening on the wrong season"), the Artifact
  gate's origin ("three player-page mocks produced and rejected in a single day"), and why a
  protected path needs an `impact_map` as well as an override. Under the approved method all three
  stayed, which capped the compression at 12.2% of §2 and, more to the point, left the rule
  document as the ONLY copy of three incidents. The new narrative test then failed on the third
  one, and its own failure message says what to do: *"Move each into
  .claude/task/escalations.log and leave a citation."*

  So the guard written in this task prescribed the method the task should have used. That is also
  what GitLab #19 asked for in the first place — "nothing deleted, only moved to git +
  escalations.log" — and the approved plan had narrowed it to removal-only.

  BOUNDED: it moves three passages, verbatim in substance, into a dated `escalations.log` entry
  that says where each came from. It removes no rule, and each site in §2 keeps a citation
  pointing at the entry.

  NOT CLAIMED: this does not authorise moving anything whose counterpart was NOT checked. The
  eight compressed passages were each located first; these three were each verified absent first.

  SECOND AMENDMENT, 2026-08-07, same clean-tree procedure. THE NARRATIVE TEST IS WITHDRAWN and
  `tests/test_governance_doc_parity.py` is reverted to `main`. `tests/` leaves `scope_paths`.

  AUTHORITY: `.claude/task/escalations.log`, the `⭐ CPO RULING: THE NARRATIVE TEST IS WITHDRAWN`
  block under the `2026-08-07 docs/19-compile-dont-append` entry — all six collisions with the rule
  sentence each would have rejected, the root cause, both paths as put, and the answer.

  THIS BLOCK ALSO CITED NOTHING AT FIRST, and `scope-auditor` FAILED round 4 for it — the SAME
  defect it failed round 1 for on the first amendment. The round-1 fix was applied to that
  amendment and not to the class, which is the failure mode `platform-reviewer` had already named
  once in this task. Recorded rather than quietly corrected, because it is the second instance.

  WHY. `platform-reviewer` FAILed it in rounds 1, 2 and 3, each time producing a legitimate RULE
  sentence the test would wrongly reject: "a round that was failed on a paperwork-only nit still
  counts", "a review's lock is void if it ran on a hash that predates the latest push", "a FAIL
  raised in round 2 of the cap must be fixed before round 3 opens", "a defect that round 2 found
  is not re-litigated in round 3". Six collisions in three rounds. Round 3 hit the ROUND CAP, so
  the builder stopped and brought the open findings to the CPO rather than patching a fourth time,
  which is what §2 requires.

  CPO ANSWER (conversation, 2026-08-07): **withdraw the test, ship the compression alone** — "B",
  against a builder recommendation that had initially been (A) ship it with the two contested
  markers removed, then was CORRECTED to (B) by the builder before he answered. The correction
  mattered and is recorded rather than smoothed over: the first recommendation was anchored on the
  work already done, not on the evidence.

  BOUNDED: nothing about the compression changes. This removes an addition; it restores no removed
  prose and alters no rule. Filed as GitLab #26.
