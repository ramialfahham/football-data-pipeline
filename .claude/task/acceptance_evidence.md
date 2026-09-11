# Acceptance evidence — one table says which source answers which question

criteria_demonstrated:
  - THE TABLE, ONCE, IN `CLAUDE.md`. New section "Which source answers which question" directly
    above "Authoritative docs": four rows — what a screen shows → the design chain via
    `00_overview.md`; what is required / what is next → the GitLab issue (`Task` template); where
    are we right now → `.claude/active_work.md`; how do we work → `working_agreement.md` then
    `CLAUDE.md` — and the line "Memory answers none of these … A product fact found only in memory
    is not a fact until it is verified in the repo or an issue", with the two 2026-09 incidents
    named. The old first row of the docs table ("Project vision … → Claude memory files") — memory
    as an authority for product — is replaced by `docs/north_star.md`. `grep -c "Which source
    answers which question" CLAUDE.md` → 1.
  - THE MEMORY INDEX OPENS WITH IT. `MEMORY.md` line 3 (the first line after the title): "MEMORY
    ANSWERS NONE OF THE FOUR QUESTIONS … A product fact found only here is NOT a fact until
    verified in the repo or an issue; when this file disagrees with those, it loses and gets
    corrected." Outside the repo, so outside this diff — checked by opening the file.
  - THE "3 TABS" CLAIM IS GONE; THE TAB LIST IS IN THE PLAYER PAGE'S ISSUE. Memory sweep for
    `3 tabs|three tabs` across the memory folder: the two player-page hits
    (`project_player_page_design.md:38`, `feedback_v2_design_schema_first.md:200`) are rewritten
    to say the page is four tabs and to point at the issue; the remaining hits are the TEAM page
    (three tabs, correct) and past-event narrative. GitLab #118 "Player page: four tabs,
    International gated on national appearances" exists in the `Task` shape: its first `What
    exactly` line is the four-tab structure, marked as the CPO's 2026-07-27 decision per commit
    `1f0af6ae` and "to be confirmed or changed here before the page is built"; the per-tab
    requirements are left to be written with him.
  - THE COMMIT'S BRANCH IS ON GITLAB. `git branch archive/docs-handover-player-tabs-and-seo
    1f0af6ae…` then `git push gitlab archive/…:archive/…` → `* [new branch]`; `git ls-remote gitlab
    refs/heads/archive/*` → `1f0af6ae7270f8d9a6941c74ab26f30ceb30eb2d refs/heads/archive/docs-handover-player-tabs-and-seo`.
  - NOTHING ELSE RESTATES THE TABLE. `docs/working_agreement.md` §1 gains two sentences: the
    precedence "is stated ONCE, in `CLAUDE.md` … this document does not restate it. Memory answers
    none of them." `grep -c "Which source answers which question" docs/working_agreement.md` → 1,
    and it is the pointer. `pytest tests/test_governance_doc_parity.py tests/test_no_dead_issue_refs.py`
    (the two suites that read `CLAUDE.md`): 45 passed, 1 skipped.

## What is NOT demonstrated

- That the four-tab decision still stands. It is his, recorded as his July decision in #118 and
  reserved there — not re-decided by this branch.
- That memory stops asserting product facts. This branch demotes memory and removes the two
  claims that bit; cutting memory to behaviour rules is #115 step 9.
