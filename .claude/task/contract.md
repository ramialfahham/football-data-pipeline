# Task contract — requirements live in the issue, decisions in the MR head; the ruling log is frozen

objective: >
  `escalations.log` (810 KB, 172 entries, ~2 CPO-quote lines per entry, the rest builder
  narrative) was the only place a "the CPO ruled X" claim could be checked — and it is written by
  the builder, in the branch it authorises. On `!173` three of four review rounds were spent on
  that record, none on the code; across the session, seven misattributed quotes. The CPO's
  question: "What are the decisions worth being logged? And where?" His answer, after a fresh
  independent review of the proposal: requirements go in a GitLab issue per major task, in a
  fixed short shape the plan is part of; a rule change is edited into the document that owns it;
  the MR description starts with a head he can scan; his merge is the approval. Nothing else is
  written down. This branch makes that the written process and freezes the log.

refs: >
  GitLab #115 step 5 ("split `escalations.log`") — resolved as FREEZE rather than split, because
  the fresh review found the growth is all narrative and the self-attestation cannot be cured by
  restructuring the same builder-written file. The CPO's "go" (chat, 2026-09-11) to the plan
  quoted in the issue this MR closes. Independent review: a fresh general-purpose agent, prompt and
  answer in the issue's fold. Overlap noted, not taken: GitLab #77 (per-task paperwork vs durable
  records).

protected_override: >
  `.claude/agents/scope-auditor.md` — one sentence changes: the auditor stops requiring a log entry
  for a cited approval and instead checks the contract quotes it and the MR head declares it. The
  CPO approved this plan in chat on 2026-09-11 ("ok go", after "Explain like I am twelve" ×3 and a
  fresh-agent review he asked for). Under the rule this branch introduces, the durable approval is
  his MERGE of this MR, whose head declares the locked file. The final entry of the frozen log
  records the same approval — the last entry it will ever take.

scope_paths:
  - .gitlab/issue_templates/Task.md
  - .gitlab/merge_request_templates/Default.md
  - docs/working_agreement.md
  - CLAUDE.md
  - docs/wireframes/00_overview.md
  - .claude/task/TEMPLATE.md
  - .claude/task/escalations.log
  - .claude/agents/scope-auditor.md
  - .claude/skills/onboard-endpoint/SKILL.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: none — no code, no model, no export, no CI job changes. Two new template files, five
    prose files, one reviewer brief (one sentence), the log (a banner and a final entry).

  downstream: the process every future task follows. `.gitlab/issue_templates/` and
    `.gitlab/merge_request_templates/` are read by GitLab's UI; the post-commit hook opens MRs with
    `glab mr create --fill`, which takes the description from the commit message, so the MR head is
    set by the builder right after (`glab mr update`) — a rule, stated in the working agreement.
    `review_routing.json` is NOT changed: the log stays un-excluded from the review patch (frozen,
    it never diffs again), so `test_governance_hooks.py`'s patch-composition tests are untouched.

  layer_rules: n/a.

  deploy_order: none.

  blast_radius: the scope-auditor's brief no longer says "you cannot verify a cited ruling without
    the log". If that sentence carried real protection, this weakens it. It did not: the log is
    builder-written, so the check it enabled was "did the builder write the same thing twice". The
    protection that remains is the one that always existed — the CPO reads the MR head and merges
    or not — now stated as the rule instead of assumed.

acceptance_criteria:
  - A GitLab issue template exists with exactly the four fields — Requested by / What exactly (a
    checklist, each line checkable without reading code) / Why / How (≤7 lines) — plus a fold for
    exploration detail and a Not-in-scope line; and the issue this MR closes uses it.
  - An MR template exists whose head is `Closes #N`, the issue's checklist ticked with one link per
    tick, and a `Locked files` line; and this MR's description carries that head.
  - `docs/working_agreement.md` states, in §1 and §11: one issue per major task in that shape; the
    plan is the issue's How and the plan file shown for approval is the same text; a rule change is
    edited into the document that owns it in the same MR; the MR head lists decisions and locked
    files; the merge is the approval; nothing else is logged. The two sentences that said
    "escalations are appended to `escalations.log`" are gone.
  - `escalations.log` carries a FROZEN banner at the top and a final entry recording this approval
    as its last; `CLAUDE.md`'s authority row, `00_overview.md`, `TEMPLATE.md`'s override guidance,
    the onboard-endpoint skill and the scope-auditor's brief no longer instruct anyone to write to
    it or to require an entry in it. Verified by grep for instructing sentences, not by word count:
    citations of past entries stay.
  - No gate, hook, CI job or routing row is added or changed — `git diff --stat` shows no
    `.claude/hooks/`, `scripts/`, `.gitlab-ci.yml` or `review_routing.json` change.

decisions_taken: >
  FREEZE, NOT SPLIT. #115 step 5 said "split". The fresh review measured the log — growth is all
  builder narrative; CPO quotes stay ~2 lines per entry — and found the self-attestation survives
  any restructuring of a builder-written file. The CPO chose freeze + the issue/MR-head process.
  #115's bar ("every step ships a mechanism") is met by the harness-enforced plan approval on the
  issue text and by the merge, not by a new gate; the CPO was told this conflict plainly and chose.

  NO NEW CI CHECK. The proposed MR↔contract description check was dropped by the fresh review: it
  binds two builder-written texts to each other, and GitLab truncates
  `CI_MERGE_REQUEST_DESCRIPTION` at 2,700 characters. The CPO asked what "no CI check" means and
  accepted it: the one thing no machine can verify — "did he build what I asked" — is his read of
  the head.

  THE MR HEAD IS SET BY THE BUILDER AFTER THE HOOK OPENS THE MR. `glab mr create --fill` uses the
  commit message; a commit message cannot carry file links cleanly under the commit form gate. So
  the rule is "open, then `glab mr update` with the head", and the template file is the shape.

  SEVEN OTHER REVIEWER BRIEFS SAY THE LOG "carries authority" AND ARE LEFT ALONE. The sentence
  explains why the file is in the patch (it still is — frozen), not an instruction to check it.
  Editing eight protected files for one word is the churn this cleanup exists to stop.

  THE "NO ISSUE FOR A TYPO OR REFACTOR" EXCEPTION IS HIS, NOT MINE. His words (chat, 2026-09-11):
  "There are some small exceptions but I think we need an issue for every major task with clear
  requirements and documentation including a plan." Naming the exceptions (typo, refactor with no
  requirement) is form; the exception itself is quoted in §1 so it is traceable (cto-reviewer,
  round 1).

  A LOCKED-FILE APPROVAL IS WRITTEN TWICE, AND THE CPO SEES BOTH. cto-reviewer, round 1: rules and
  requirements keep a second artifact (the owning doc, the issue); a `protected_override` would
  have had only the contract — and the second copy is what caught the misattributions on `!173`.
  So the MR head's `Locked files` line REPEATS the quoted approval and date, next to the contract's
  copy, which the CPO reads at merge. Reviewers still cannot verify the quote — nobody can but him
  — but a quote that differs between the two copies is now visible to the one person who knows.

  THRESHOLD — NEW MECHANISM: none. Two templates and prose. THRESHOLD — RECURRING COST: none.

decisions_reserved:
  - Whether #77 (per-task paperwork vs durable records) absorbs the rest of the contract/evidence
    artifact question.
  - Steps 6-9 of #115.

done_when:
  - All five criteria proven; `pytest tests/test_governance_doc_parity.py tests/test_post_commit_hook.py`
    green (prose-parity and hook tests are the ones that could see these edits).
  - The issue this MR closes exists in the new shape; the MR head is set.

amendments:
  - Round 1 (scope-auditor PASS, cto-reviewer FAIL). Two findings, both taken: (1) a locked-file
    approval had no second copy under the new rule — the MR head's `Locked files` line now repeats
    the quote and date (template, §11 table, scope-auditor sentence, the head of this MR); (2) the
    "no issue for a typo/refactor" exception was new rule text without a source — it is the CPO's
    own "some small exceptions", now quoted in §1 and above. Also corrected in the record: the
    review prompt claimed this contract cites `fix/merge-guard-covers-the-api`; it did not and
    does not — that precedent is in the fresh review's answer, in #116's fold.
  - Round 2 (cto-reviewer FAIL, scope-auditor PASS). The second copy of a locked-file approval
    was a template line set by hand after the hook opens the MR — a promise, not evidence, and on
    the one branch where it applies. FIX, a rule refinement in §11: the COMMIT MESSAGE carries the
    `Locked files` line with the quote, so `glab mr create --fill` puts it in the MR description
    automatically and `git log` holds it in a tracked place; the hand-set head only adds the ticks
    and links. The evidence now quotes that commit-message line verbatim beside the contract's
    quote — identical strings — and says what remains unverifiable until the commit exists.
  - Round 3 (cto-reviewer FAIL, scope-auditor FAIL, same finding). "Identical strings" above was
    FALSE when written: the commit-message line paraphrased the contract's approval ("the
    explanation he asked for three times" for `"Explain like I am twelve" ×3`) and the evidence
    called that verbatim. Inside the fix for quote drift, quote drift. FIX: the commit message now
    carries the contract's approval span character-for-character, and the evidence records a
    Python equality on the two spans (`IDENTICAL`), not a reading. Round 4 runs under a
    `rounds_cap_override` in `review.md`, recorded as on `!172` and `!173`: to clear a standing
    FAIL by review, not to ship past one.
