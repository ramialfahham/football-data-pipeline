# Acceptance evidence — the roadmap has one home

criteria_demonstrated:
  - THE TWO DEAD DOCUMENTS ARE GONE. `git rm docs/agent_company_roadmap.md docs/backlog.md`; the
    patch shows both as deletions. `git grep -n "agent_company_roadmap\|backlog\.md"` over the
    tree → 3 hits, all inside `.claude/task/contract.md` naming them as the files this task
    deletes; none anywhere else.
  - THE TWO PARTIAL SECTIONS POINT AT THE MILESTONES. `docs/north_star.md` "Next milestone"
    keeps the quality-bar sentence and adds one paragraph naming the seven milestones in menu
    order with the milestones URL; `docs/site_architecture.md` §7's go-live bullet keeps Firebase
    hosting, no MVP to switch from, no parity and no redirects, and replaces the written sequence
    (which cited #377 and #799, both GitHub-era numbers) with the milestones URL and "go-live
    items follow the last page there". `grep -c "#[0-9]"` over each edited section → 0.
  - THE ONE REFERENCE TO THE DELETED FILE IS REPOINTED. `.github/ISSUE_TEMPLATE/config.yml`'s
    contact link now names the GitLab milestones and says the GitHub repository is dormant;
    `.github/workflows/` untouched.
  - THE HANDOVER NAMES THE MILESTONES AS THE ROADMAP AND #127 AS NEXT. `.claude/active_work.md`
    "WHERE WE ARE" states the seven milestones in menu order, the review-before-build rule, the
    fourteen review issues (#127–#140), this branch (#141), and the Home review as the next step;
    15,615 chars, under the 16,000 budget (a history paragraph about three merged MRs was cut to
    its current-state facts to make room). `pytest tests/test_no_dead_issue_refs.py` → 6 passed.

## What is NOT demonstrated
- The milestones and issues themselves were created on GitLab before this branch (milestones
  1–7; #127–#140; the existing page issues attached to their milestones) and are not in the
  patch; they are visible on the project's milestones page.
- `docs/wireframes/00_overview.md`'s status table still reads like a roadmap; it is corrected page
  by page as each review issue closes, by decision, not here.
