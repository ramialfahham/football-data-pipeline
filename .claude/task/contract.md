# Task contract — reviewers stop reviewing the review's own paperwork (#868 follow-up)

> Written on a clean tree before any file was touched. Branch `fix/868-review-scope` from `main` at
> `cc6cc45`; `gh pr list --state open` empty. Governance task: it edits the guards, so it carries
> `protected_override` and `impact_map`.

objective: >
  #370 took twelve review rounds for a ~300-line change. The code was correct from round 5; rounds 6
  to 12 found nothing a visitor would see. Measured cause, three mechanisms compounding:

  1. Governance artifacts are inside `scope_paths`, so reviewers read the paperwork the review itself
     produces — 839 lines of code inside a 38,932-line reviewed diff.
  2. Two evidence artifacts are inside `diff_sha256`, so correcting a typo in prose voids every PASS
     already given and forces a new round.
  3. Every reviewer brief says a PASS requires two named risks, so on correct code a reviewer is
     *required* to find something. It finds prose.

  This closes all three. It changes what reviewers see, what invalidates their verdict, and what a
  PASS must contain. It does NOT change the org, the roles, the activation model, the decision rights
  or the definition of done.

refs: >
  #868. CPO rulings 2026-08-01, in this conversation, quoted in `protected_override` below.

scope_paths:
  - .claude/review_routing.json
  - .claude/hooks/git_discipline.py
  - .claude/agents/*.md
  - docs/working_agreement.md
  - docs/agent_guardrails.md
  - tests/test_governance_hooks.py
  - .claude/task/*.md
  - .claude/task/escalations.log
  - .claude/active_work.md
  # ADDED after round 1. All three reviewers found that this file re-implements the
  # PASS floor (`:169`) and enforces the OLD value of 2 in CI, fail-closed, on every
  # PR — so change 3 was inoperative at the PR boundary and a one-entry PASS would
  # have commited locally and reddened CI. See the amendment.
  - scripts/check_task_artifacts.py

protected_override: >
  CPO approval, 2026-08-01, this conversation. He was shown the defect in plain language and approved
  each change separately:
  (1) and (2) — **"yes to those two"**, to reviewers no longer seeing task notes, and to a note fix no
  longer restarting the review.
  (3) — **"why would we force it? Of course, the reviewer needs to have he critical attitude but it's
  allowed to approve and not invent some finding."**
  (4) — **"go ahead"**, to implementing all three.
  He also ruled, correcting me, that the ORG IS NOT THE PROBLEM: activation-on-necessity is right and
  low activation is not a defect. No role, brief or routing row is removed by this task.

acceptance_criteria:
  # NOT drafted by me. These are the CPO's own three sentences turned into checks, so the lock is his
  # wording rather than my paraphrase.
  - A reviewer does not see the review's own paperwork. `review_input.patch` is generated with
    `.claude/task/**` and `.claude/active_work.md` excluded, by a command in the hook rather than by
    hand, and the briefs say what is in scope for them to read.
  - Correcting a note does not restart the review. Editing `acceptance_evidence.md` or
    `rendered_page_evidence.md` leaves `--staged-hash` unchanged, so a PASS survives it. Editing
    `contract.md` still changes the hash, because `scope_paths` and `acceptance_criteria` carry
    authority and must not move after review.
  - A reviewer may approve without inventing a finding. A PASS states what was examined and needs no
    named risk. It still cannot be a bare verdict with nothing behind it.
  - Nothing about the org changes. The same eight briefs exist, the same routing rows fire, the same
    decision rights hold, `done_when` is unchanged.

impact_map: >
  writers: `.claude/review_routing.json` has exactly two consumers — `git_discipline.py::_load_routing`
    (fails OPEN, swallows exceptions and returns None, so a malformed file silently disables the local
    gate) and `scripts/check_task_artifacts.py` (fails CLOSED in CI). Both must agree on the new key.

  downstream: the PASS floor exists in TWO places and both must move together —
    `git_discipline.py::_commit_gate` (the local hook) and `scripts/check_task_artifacts.py:169`
    (the CI twin, fail-closed, run on every PR by `ci-validate.yml`). The twin also re-implements the
    reviewer-matching loop by hand with no parity test (#873, open).
    ⚠ This entry previously claimed the quota "exists in one place. Verified before editing." **That
    was false and it was the load-bearing sentence of this impact map.** All three reviewers caught it
    in round 1. I asserted a verification I had not actually performed — the exact failure the
    impact_map field exists to prevent.

  layer_rules: no warehouse change. The machine rules that apply are in
    `tests/test_governance_hooks.py`: every `.claude/agents/*.md` must carry a byte-identical
    `## Delta re-review` section with nothing after it (globbed, no opt-out), and every routing
    pattern must be pinned in `PINNED_CASES`.

  deploy_order: this branch is routed BY ITS OWN new table, because both consumers read the file from
    the working tree rather than from HEAD. It is also the first branch reviewed under its own new
    PASS condition.

  blast_radius: every future commit in this repo. What stops being enforced if this is wrong: a PASS
    could become a rubber stamp (mitigated — a PASS must still state what was examined, and the gate
    still requires one entry), or the hash could stop covering something that carries authority
    (mitigated — `contract.md` stays inside the hash; only the two evidence artifacts leave).

decisions_taken: >
  - The four CPO rulings above.
  - Builder judgement: `contract.md` STAYS inside `diff_sha256`. Excluding it would let scope or
    acceptance criteria be widened after every reviewer has passed, which is the F10/#409 guard. Only
    the two evidence artifacts leave the hash, because they carry evidence rather than authority.
  - Builder judgement: the PASS floor drops from two entries to one, not to zero. Zero would allow a
    bare `VERDICT: PASS` with nothing behind it, which is the rubber-stamp the two-risk rule was
    written to prevent. One entry keeps that protection and removes the forced invention.
  - Builder judgement: `risks_checked:` keeps its name in the artifact format so no reviewer brief or
    test has to change key names, but the briefs now ask for what was EXAMINED rather than what was
    FOUND.

decisions_reserved:
  - The round cap still records rather than refuses: it is checked at commit time against a number the
    builder types, so nothing stops a fourth round while rounds are running. Fixing it means deriving
    the count mechanically. Not in this task.
  - `.claude/task/escalations.log` is in `hash_exclude_paths`, so the durable ruling record sits
    outside the hash and can be rewritten after every reviewer passes. Whether to bind it is a
    mechanism question.
  - No gate records when it denies, so most of the 72 enumerated checks are unobservable and cannot be
    shown to have ever fired. Adding one appended line per denial is the highest-value follow-up.
  - Whether any reviewer or role should be removed. The CPO ruled the org is not the problem; nothing
    here touches it.

done_when:
  - `python -m pytest tests/test_governance_hooks.py -q` green, with new tests pinning each of the
    three changes so a revert fails.
  - `python .claude/hooks/git_discipline.py --staged-hash` is unchanged by an edit to
    `acceptance_evidence.md`, and changed by an edit to `contract.md`. Demonstrated, not asserted.
  - `python scripts/check_task_artifacts.py` agrees with the local hook on the new table.
  - `python -c "import json; json.load(open('.claude/review_routing.json'))"` parses, and the number of
    `paths` keys equals the number of distinct pattern strings in the file text.
  - The four CPO rulings are appended to `.claude/task/escalations.log`, the durable record. They
    authorise a change whose blast radius is every future commit, and `contract.md` does not survive
    the next task.

amendments:
  - `+ scripts/check_task_artifacts.py` — **authority: the CPO's 2026-08-01 ruling (3) + (4)**,
    quoted in `protected_override`. He ruled that a reviewer may approve without inventing a finding,
    and said "go ahead" to implementing it. That ruling CANNOT be satisfied in only one of the two
    places the floor lives: this file is the fail-closed CI twin, so leaving it at 2 meant a one-entry
    PASS committed locally and then reddened the PR — the permission he granted would not have existed
    at the boundary that matters. Extending scope to the second copy is the minimum needed to carry out
    the ruling, not a new decision.
    (Round 1's reviewers found the divergence; both `cto-reviewer` and `scope-auditor` then noted that
    an amendment must record the CPO's authority and not the reviewers' — §2, and the precedent in
    `escalations.log` 2026-06-23. Correct: a reviewer FAIL is a reason to look, never an authority.)

  - Round 1, three reviewers, eight findings, all real machinery defects and none about artifact
    phrasing — which is the evidence that the change works. Fixed:
    (1) the CI twin above. This contract's `impact_map` had asserted a verification I never performed.
    (2) `_review_patch_bytes` ignored git's return code, so any git failure wrote a zero-byte patch and
    exited 0 — a reviewer would read "nothing changed" and could pass on it. Now fails loud.
    (3) `.claude/task/escalations.log` REMOVED from `review_exclude_paths`. `cto-reviewer` was right
    that it is AUTHORITY, not a note: `protected_override` cites it as the locatable record, and
    "does the claimed ruling actually exist" is a check that has fired before. I applied the
    authority-vs-evidence split to the hash and forgot to apply it to visibility.
    (4) `docs/agent_guardrails.md` still stated the old rule, in scope and untouched.
    (5) `seo-expert-reviewer.md` carried the old rule one line under the new one.
    (6) No test pinned the REAL routing's new `hash_exclude_paths` entries, so deleting them left the
    suite green. (7) `test_every_task_artifact_is_classified` could pass vacuously on an empty
    `git ls-files` and hand-rolled an enumeration the file's own `tracked()` helper already does safely.
