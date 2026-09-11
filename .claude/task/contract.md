# Task contract — reasoning lives in git, not in code comments: the rule and the recipe

objective: >
  429 comment lines in code carry a date, "CPO", "reviewer" or "round N" — history, not reasoning.
  `engineering_standards.md` §1.2 already forbids it and is ignored, because the contract reviewers
  read dies with the task, so the builder writes the reasoning next to the line to make it survive.
  Since `!174` the durable place exists — commit message, MR head and fold, issue fold, reached
  from any line by `git blame` — it just is not named. This branch names it, in the document that
  owns code comments, and records the count step 8's hook will ratchet down.

refs: >
  GitLab #119 (this task; the What/Why/How below are copied from it). GitLab #115 step 7; step 8
  depends on it. The CPO's "go" in chat on 2026-09-11 to the issue text as shown to him.

scope_paths:
  - dbt_project/docs/engineering_standards.md
  - CLAUDE.md
  - .gitlab/issue_templates/Task.md
  - .gitlab/merge_request_templates/Default.md
  - .claude/task/TEMPLATE.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: none — five prose files. No code, model, hook, test, CI job or routing row.

  downstream: `engineering_standards.md` §1.2 is the standard `scripts/check_description_hygiene.py`
    cites for descriptions (§2), not §1.2; nothing parses §1.2. `CLAUDE.md` is read by every
    session. The templates are read by GitLab's UI and by the builder.

  layer_rules: n/a.

  deploy_order: none.

  blast_radius: none in code. A rule that already existed is restated with the place the
    reasoning goes and the count of violations; enforcement is step 8.

acceptance_criteria:
  - `dbt_project/docs/engineering_standards.md` §1.2 says, for every language in the repo: a
    comment says why, in one line. Who decided, when, which reviewer, which round, which MR or
    issue — never in code; that lives in the commit message, the MR and the issue, and `git blame`
    reaches it from any line. With the recipe.
  - `CLAUDE.md` says the same in one sentence.
  - The issue and MR templates' folds say they are the place for the reasoning reviewers and
    future readers need.
  - The contract template says: reviewers read `decisions_taken` and `amendments` — argue with a
    reviewer there, never in a code comment.
  - The count of such comment lines is recorded (429 today) as the number step 8's hook ratchets
    down.

decisions_taken: >
  THE NON-CODE PLACE IS GIT, NOT A NEW FILE. A "decisions.md" or a per-file reasoning doc would be
  a second `escalations.log`: builder-written, unbound, growing. The commit message, the MR and the
  issue already exist, are reachable from any line, and — since `!174` — are the CPO's check.

  THE COUNT IS A GREP, STATED AS SUCH. `(#|--|//|\*).*(20\d\d-\d\d-\d\d|CPO|reviewer|round \d)`
  over the code trees. It over-counts a little (a docstring line quoting a date for a real reason)
  and under-counts a little (a "his 'do both'" with no date). It is a ratchet's starting number,
  not a claim of precision; step 8 decides the exact pattern.

  NO REVIEWER BRIEF CHANGES. Grepped `.claude/agents/*.md`: none asks for reasoning in code. The
  pressure was mine.

  THRESHOLD — NEW MECHANISM: none. THRESHOLD — RECURRING COST: none.

decisions_reserved:
  - The hook's exact pattern and whether the 429 are swept or ratcheted — #115 step 8.

done_when:
  - The five criteria proven; `pytest tests/test_governance_doc_parity.py tests/test_no_dead_issue_refs.py`
    green (the suites that read `CLAUDE.md`).
  - The recipe verified on a real line of `!175`, output in the evidence.

amendments:
  - none yet
