# Acceptance evidence — requirements in the issue, decisions in the MR head, the log frozen

criteria_demonstrated:
  - ISSUE TEMPLATE, AND THE ISSUE USES IT. `.gitlab/issue_templates/Task.md` (31 lines): Requested
    by / What exactly (checklist) / Why / How (≤7) / Not in scope / a `<details>` fold. GitLab
    #116 was created from that exact shape — five checklist lines, one-sentence Why, five-line
    How, the fresh review's measurements in the fold. `glab issue view 116` shows it.
  - MR TEMPLATE, AND THIS MR'S HEAD. `.gitlab/merge_request_templates/Default.md`: `Closes #`,
    ticked checklist with a link per tick, `Locked files:` carrying the quoted approval, a fold.
    THE SECOND COPY OF THE LOCKED-FILE APPROVAL, ON THIS BRANCH, VERBATIM. The contract's
    `protected_override` reads: `The CPO approved this plan in chat on 2026-09-11 ("ok go", after
    "Explain like I am twelve" ×3 and a fresh-agent review he asked for)`. The commit message
    (scratchpad, committed with `-F`) carries, as its third paragraph:
    `Locked files: .claude/agents/scope-auditor.md — approved in chat on 2026-09-11 ("ok go",
    after "Explain like I am twelve" ×3 and a fresh-agent review he asked for)`. From `in chat on`
    to the closing parenthesis the two strings are character-identical — checked by a Python
    equality on the two substrings, not by eye, after round 3 caught a paraphrase presented as
    verbatim. The hook's `glab mr create --fill` copies the commit message into the MR
    description, so the MR shows that line before any hand edit, and `git log -1 --format=%B`
    holds it afterwards. What is NOT verifiable until the commit exists: that this exact message
    was used — the CPO sees the result on the MR; a reviewer sees it in `git log` after the fact.
  - THE WORKING AGREEMENT SAYS IT, IN §1 AND §11. `grep -n` on `docs/working_agreement.md`: line 36
    "The requirement lives in a GitLab issue, and the plan is part of it"; line 40 "the plan file
    shown for approval is the issue's text, not a second document"; line 356 a rule change is
    "edited in the same MR"; line 358-361 the MR head and "the merge is the approval"; line 359
    "not a decision. Not written anywhere"; line 363 the log "is frozen". The two old sentences
    ("Escalations are appended to…", "Every escalation is appended to…") return zero hits.
  - THE LOG IS FROZEN AND NOTHING INSTRUCTS WRITING TO IT. Banner at line 1 ("FROZEN 2026-09-11 —
    HISTORY ONLY. NO NEW ENTRIES"); final entry at line 8922. Sweep for instructing sentences —
    `append.*escalations.log`, `record.*in.*escalations.log`, `log.*to.*escalations.log` — across
    `*.md *.py *.json *.mdc *.yml`, excluding the log and this branch's artifacts: the hits left
    are the contract quoting the deleted sentence, `CLAUDE.md`'s new row, a `_doc` string in
    `review_routing.json` describing a 2026-07 routing decision, `layering.md:226` and
    `design-mocks/README.md:42` citing past entries, and a test docstring calling the log
    append-only as history. None instructs. `.cursor/rules/` and `docs/agent_guardrails.md`: zero
    hits for "escalations".
  - NO GATE, HOOK, CI JOB OR ROUTING CHANGE. `git status --short`: eight modified files and the
    new `.gitlab/` directory — no `.claude/hooks/`, no `scripts/`, no `.gitlab-ci.yml`, no
    `review_routing.json`. `pytest tests/test_governance_doc_parity.py tests/test_post_commit_hook.py`:
    46 passed, 1 skipped.

## What is NOT demonstrated

- That the process holds. The measure is stated in #116: review rounds spent on the record, judged
  in a month (`!173`: 3 of 4).
- That GitLab applies `Default.md` to hook-opened MRs — it does not; `--fill` wins. That is why
  `Closes #N` and the `Locked files` line live in the commit message: they reach the MR on their
  own. The ticked checklist with links is a builder step after; if skipped, the MR shows the
  commit message and no checklist, which the CPO sees before merging.
- The seven other reviewer briefs still say `escalations.log` "carries authority". Left alone on
  purpose (contract `decisions_taken`): the sentence explains patch composition, which is unchanged.
