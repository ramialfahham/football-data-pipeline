# Task contract — #25: name the excluded files instead of hiding them without trace

> Branch `fix/25-review-exclude-trailer` from `main` (`c5d6088`). PROTECTED + guard path, so
> `protected_override` AND `impact_map` are both present below, and `cto-reviewer` +
> `platform-reviewer` run at an OPUS floor. No `site_v2/src/` path, so no `acceptance_criteria`.
> A commit touching `contract.md` is NEVER artifact-exempt.

objective: >
  Make `git_discipline.py --review-patch` announce, by name and line count, any
  `review_exclude_paths` file that IS edited on the branch, instead of removing it from the patch
  with nothing said.

  THE DEFECT. Exclusion deletes the file entirely, so a reviewer cannot tell a file that was never
  edited from one that was edited and deliberately hidden. Both look identical: absent. A reviewer
  that sees a path in `scope_paths` and not in the patch reasonably concludes the scope is wrong or
  an edit is missing. Both conclusions are false and both cost a round.

  IT HAS FIRED THREE TIMES, and each time the reviewer was reasoning correctly from what it was
  given: 2026-08-03 `.claude/active_work.md` ("scope names an unedited file"), 2026-08-06
  `.claude/task/TEMPLATE.md` ("a required edit is missing" — it was edited at both sites), and
  2026-08-07 `.claude/active_work.md` (*"the diff I was handed does not contain the change the
  entire task is about"*). All three withdrawn on the evidence. Three occurrences is a missing
  affordance, not reviewer carelessness.

  THE REPO ALREADY SOLVED THIS FOR THE SIBLING LIST. `review_summarise_paths` (2026-08-06) does not
  hide content; it substitutes a MANIFEST naming the files and their counts. `review_exclude_paths`
  predates that mechanism and never got it. The reasoning in its `_doc` transfers unchanged:
  hiding outright *"would silently delete that check — trading payload for coverage, which is the
  'never loosen a guard' failure."*

refs: >
  GitLab #25. Second item of the AI-collaboration audit stream (handover `NEXT` step 1). Order set
  by the CPO this session: #29 (merged as !18), then #25, then #21 brought as a recipe. Cost is a
  SEPARATE stream and explicitly out of this session.

scope_paths:
  - .claude/hooks/git_discipline.py
  - tests/test_governance_hooks.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log

protected_override: >
  CPO instruction, conversation 2026-08-07: **"start #25"**, following **"yes, that order. start
  with #29"** against a recommended order of #29, then #25, then #21 as a recipe. GitLab #25's own
  closing paragraph states that the fix requires a governance task carrying `protected_override`
  and an `impact_map` with `cto-reviewer` and `platform-reviewer` at opus, so instructing the work
  to start authorises the protected edit the work requires.

  RECORDED IN FULL at `.claude/task/escalations.log`, entry
  `## 2026-08-07 fix/25-review-exclude-trailer`. That entry and this field were written in the SAME
  action, which is GitLab #28's class fix.

  THE AUTHORITY IS FOR THIS CHANGE, NOT A STANDING ONE. It covers ONE protected file,
  `.claude/hooks/git_discipline.py`, for the one purpose in `objective:`. It does NOT authorise
  editing `.claude/review_routing.json`, the reviewer briefs under `.claude/agents/`,
  `docs/working_agreement.md`, or `hash_exclude_paths`. Naming the file literally rather than
  pointing at `scope_paths` is deliberate: GitLab #18 is open on exactly that self-reference,
  where an override that defines its reach as "the paths in scope_paths" grows whenever an
  amendment adds one.

impact_map: >
  writers: not applicable — no table, no model. The edited unit is one PROTECTED guard script, so
  this traces what depends on the guard, per the TEMPLATE instruction for protected paths.

  events that fire it: `PreToolUse` with matcher `Bash` on EVERY Bash tool call
  (`.claude/settings.json`, verified by parsing the file). Plus two hand-invoked CLI modes,
  `--review-patch` and `--staged-hash`.

  what imports it: TWO files, measured with
  `grep -rln "import git_discipline" --include="*.py"` rather than asserted.
    1. `scripts/check_task_artifacts.py:52` (`import git_discipline as _gd`), the CI backstop that
       runs in `validate:governance`. It uses exactly ONE symbol, `_gd._rounds_gate` (line 58) —
       `grep -n "_gd\." scripts/check_task_artifacts.py` returns that single line.
    2. `tests/test_governance_hooks.py`, at TWO sites, `:438` and `:2798`, which import the module
       and call internals directly. That is real code coupling, and this task adds a third such
       call site, so a change to these internals breaks tests rather than only behaviour.

  ⚠ THIS FIELD PREVIOUSLY CLAIMED *"Nothing else in the tree imports the module; the remaining
  references ... are prose in five docs plus the settings wiring."* FALSE, and `scope-auditor`
  FAILed round 1 on it. The two test imports are code, not prose; `.claude/review_routing.json` is
  config, not a doc; and the reference count is 14 files, not seven. Corrected against the grep
  rather than reworded. Recorded rather than quietly replaced because of what it is: the #904
  class — a contract claim about the code, written before the code and never re-read against the
  finished tree — occurring inside the very `impact_map` whose job is to prevent it.

  reference-only, no import (12 files, none edited here): `.claude/settings.json` (the PreToolUse
  wiring), `.claude/review_routing.json`, `.claude/agents/platform-reviewer.md`,
  `.claude/active_work.md`, `.claude/task/TEMPLATE.md`, `.claude/task/REVIEW_TEMPLATE.md`,
  `.claude/task/contract.md`, `docs/agent_guardrails.md`, `docs/north_star.md`,
  `docs/roles/platform_reliability.md`, `docs/working_agreement.md`,
  `tests/test_governance_doc_parity.py`.

  what stops being enforced if it is wrong: nothing. The change is confined to the `--review-patch`
  CLI product. `_commit_gate`, the commit-flag allowlist, the push checks, `_rounds_gate` and the
  hash are all on code paths this does not modify.

  blast radius on the review hash: NONE, verified rather than assumed. `--staged-hash` calls
  `_staged_diff_bytes` (`main()`, line 643) which resolves `hash_exclude_paths`; the trailer joins
  `_review_patch_bytes`, which resolves `review_exclude_paths`. Different function, different list.
  A test in `done_when` pins it.

  deploy_order: not applicable. No warehouse object, nothing sequenced around the 04:00 nightly,
  and `.claude/hooks/**` is absent from `data_paths` so no prod build is triggered.

  on failure: `--review-patch` exits non-zero and `review_input.patch` is not produced, stalling
  the review cycle loudly rather than emitting a patch that under-reports.

decisions_taken: >
  THRESHOLD DECLARATIONS, stated because no gate parses this field.

  ⭐ NEW MECHANISM — YES. RECLASSIFIED BY THE BUILDER BEFORE BUILDING, and this is the honest
  declaration rather than the convenient one. The approved plan framed this as applying an existing
  pattern to a sibling list. `escalations.log:1106` shows that is wrong:
  `review_summarise_paths` counted as a NEW MECHANISM partly because it added *"a manifest emitter
  in `git_discipline.py`, which changes what every reviewer is handed in every future task"*
  (:1117). This trailer is the same emitter, in the same file, with the same reach.

  Per `escalations.log:1108`, declaring a crossing to a REVIEWER is not approval and a reviewer
  cannot convert one into the other, so this is not a request for `cto-reviewer` to rule. The
  approval is the CPO's own, given at plan time on a plan that described the emitter, its wording
  and its raise-don't-degrade behaviour. Recorded at `escalations.log`, entry
  `## 2026-08-07 fix/25-review-exclude-trailer`, and surfaced to him in the turn the
  reclassification was made so he can reject it.

  WHAT IS GENUINELY NARROWER than the 2026-08-06 precedent, so this is not read as equivalent: no
  new routing key, no content removed from the patch body, no verdict rule changed, no hash effect.
  The trailer only annotates what is already absent.

  RECURRING COST — NO. One extra `git diff --staged --stat` per `--review-patch` invocation, which
  is a local, hand-invoked command run a few times per task. No new reviewer, no model change, no
  service, no schedule. It should REDUCE cost: the measured price of the defect is one wasted
  review round per occurrence, three so far and accelerating.

  NEW EXTERNAL SURFACE — NO.

  GUARD INVARIANT — STRENGTHENED, never loosened, and the direction matters. This ADDS information
  to what reviewers are handed and removes none. It does not touch `hash_exclude_paths`, so nothing
  that invalidated a verdict before stops doing so. It cannot hide anything that is visible today,
  because it only emits for paths that are ALREADY excluded.

  WHY IT RAISES RATHER THAN DEGRADING QUIETLY. `_summary_manifest` raises because silence there is
  a coverage loss. Silence here is not, and the trailer still raises for a different reason: an
  absent trailer is ambiguous between "no excluded file changed" and "the trailer broke", and that
  ambiguity is the exact defect #25 exists to remove.

decisions_reserved:
  - "Whether `.claude/active_work.md` belongs in `review_exclude_paths` at all. Occurrence 3 was a
    handover task, where the reviewer legitimately could not judge the work with the handover
    hidden. The trailer removes the false inference but does not answer that question, and moving a
    path between the two lists is a §10 decision on the same reasoning as
    `escalations.log:1138`. NOT decided here and NOT in scope."

done_when:
  - "FIVE new tests ship in `tests/test_governance_hooks.py`, and the red/green claim is stated per
    test rather than as one number. MEASURED against the unfixed `git_discipline.py`: THREE of the
    first four go red (`..._are_named`, `..._without_pasting_them`,
    `..._does_not_reach_the_review_hash`); `test_no_trailer_when_no_excluded_path_changed` cannot,
    because it asserts the trailer is ABSENT; and the fifth,
    `test_excluded_trailer_failure_is_loud_not_silent`, cannot either, because `_excluded_trailer`
    does not exist in the unfixed file. Both runs pasted — a test never seen red is decoration
    (`feedback_verify_the_test_fails.md`)."
  - "⚠ THIS CRITERION SAID 'the four new tests' UNTIL ROUND 3, when a fifth had been added on a
    `platform-reviewer` finding and the count was not updated with it. `cto-reviewer` caught it.
    Recorded rather than silently renumbered, because of where it happened: it is the #904 class —
    a contract claim that drifted from the tree — inside the same contract that cites #904 two
    fields above. The reusable lesson is that a numeric claim must be re-read after EVERY round,
    not written once and trusted."
  - "The tests pin all four properties: an edited excluded file is NAMED in the trailer; its
    CONTENT is still not pasted; NO trailer is emitted when no excluded path changed; and
    `--staged-hash` is byte-identical with and without the trailer."
  - "`python -m pytest tests/ -q` is clean and the collected count is MEASURED with
    `pytest --collect-only -q`, never predicted (#904)."
  - "The five offline gates pass, and `check_task_artifacts.py` is run BARE."
  - "END-TO-END on this branch's own review: this task edits `contract.md` and `review.md`, so its
    real `review_input.patch` must carry the trailer naming the excluded files it edited. The
    trailer pasted from the real patch, not from a test fixture."

amendments: (none)
