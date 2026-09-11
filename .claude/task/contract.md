# Task contract — one table says which source answers which question; memory answers none

objective: >
  Memory said the player page is three tabs; a later handover said four; nothing said which wins,
  and the four-tab record survives only as a commit on the dead GitHub remote. Memory also said
  the built Overview tab was lost when the repo had it in a stash. A session acted on memory both
  times. This branch states the precedence once, in `CLAUDE.md`, demotes memory in its own index,
  moves the tab decision into the player page's issue, and preserves the commit that records it.

refs: >
  GitLab #117 (this task, `Task` template — the What/Why/How below are copied from it). GitLab
  #115 step 6. The CPO's "go" in chat on 2026-09-11 to the issue text as shown to him. The
  four-tab record: commit `1f0af6ae` on `origin/docs/handover-player-tabs-and-seo`, 2026-07-27,
  "docs(handover): player page is four tabs (848)".

scope_paths:
  - CLAUDE.md
  - docs/working_agreement.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: none — two prose files in the repo. Outside the repo, and outside this diff: the memory
    index and one memory file (my notes), a new GitLab issue for the player page, and a pushed
    `archive/` branch that points at an existing commit.

  downstream: every session reads `CLAUDE.md` first; the table changes where a session looks for
    an answer, not any answer. No hook, test, CI job or routing reads the section edited.

  layer_rules: n/a.

  deploy_order: none.

  blast_radius: none in the repo. The archive branch is a new ref on GitLab pointing at a commit
    the repo already holds; deleting it is one command.

acceptance_criteria:
  - `CLAUDE.md` has one table saying which source answers which question — what a screen shows
    (the design chain via `00_overview.md`), what is required / what is next (the GitLab issue),
    where we are right now (`.claude/active_work.md`), how we work (`working_agreement.md`) — and
    one line: memory answers none of these; a product fact found only in memory is not a fact
    until verified in the repo or an issue.
  - The memory index opens with that same line.
  - The "3 tabs" memory claim is gone. The player page's tab list is recorded as a requirement in
    the player page's GitLab issue: four tabs, International gated on
    `national_appearances_total ≥ 1`, as the CPO's 2026-07-27 decision.
  - That commit's branch is preserved on GitLab as `archive/docs-handover-player-tabs-and-seo`.
  - Nothing else restates the table; the working agreement points at it.

decisions_taken: >
  THE TABLE IS A LOOKUP, NOT A RULING. Every row points at an authority that already exists
  (`00_overview.md` since `!170`, the issue since `!174`, `active_work.md` since 2026-08-06, the
  working agreement); the table only says which answers which question. The one new sentence —
  memory answers none of these — is the demotion the failures above justify, and it binds only me.

  THE FOUR TABS ARE MOVED, NOT DECIDED. The player page issue records the tab structure as the
  CPO's 2026-07-27 decision per the commit, marks it as such, and says the per-tab requirements
  are written when that work starts — which is where he confirms or changes it.

  THE ARCHIVE BRANCH IS A REF, NOT A COPY. `git branch archive/… origin/docs/handover-player-tabs-and-seo`
  makes a GitLab ref to a commit already in the repository; nothing is rewritten. My initiative,
  reversible, listed in #117's How before the go.

  THRESHOLD — NEW MECHANISM: none. THRESHOLD — RECURRING COST: none.

decisions_reserved:
  - Whether the four-tab structure still stands — his, when the player page's requirements are
    written.
  - Steps 7-9 of #115.

done_when:
  - The five criteria proven; `pytest tests/test_governance_doc_parity.py tests/test_no_dead_issue_refs.py`
    green (the two tests that read `CLAUDE.md`).
  - #117 closed by the MR; the player page issue exists; the archive branch is on GitLab.

amendments:
  - Scope +`.claude/active_work.md`, before any edit to it. It is the "where are we right now" row
    of the table this branch writes, and it is stale: last updated 2026-09-08, its NEXT ACTION is
    "#40 MR B" (merged as `!166`), and it predates #115 entirely. A precedence table pointing at a
    stale handover would be the defect this step exists to fix. Handover upkeep is bookkeeping
    inside an already-approved task, not a decision; the file is artifact-only and its edit rides
    into this reviewed commit (§2).
