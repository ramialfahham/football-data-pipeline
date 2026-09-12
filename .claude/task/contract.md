# Task contract — the roadmap has one home

objective: >
  The roadmap now lives in GitLab: seven milestones in the site's menu order (Home, Competitions,
  Matches, Teams, Players, Standings, Stats) and one review issue per page under each (#127–#140),
  every page rechecked and approved by the product owner before it is built. Four documents also
  carried a roadmap — two dead, two partial. This branch deletes the two dead ones and turns the
  two partial sections into a pointer at the milestones, so there is exactly one roadmap.

refs: >
  GitLab #141 (this task, `Task` template; the What/Why/How below are copied from it). The
  product owner's words, 2026-09-12, in chat: "go, create the milestones and delete the dead
  docs", after "we need a single source of truth that we adhere to and where we track our
  progress". `CLAUDE.md` "Which source answers which question": what is next is the GitLab
  tracker, never a document.

protected_override: none — no protected path is touched (`.github/ISSUE_TEMPLATE/` is not
  `.github/workflows/`).

scope_paths:
  - docs/agent_company_roadmap.md
  - docs/backlog.md
  - docs/north_star.md
  - docs/site_architecture.md
  - .github/ISSUE_TEMPLATE/config.yml
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: two files deleted; one section each in `north_star.md` and `site_architecture.md`
    replaced by a pointer; one link in the dormant GitHub issue-template config repointed; the
    handover.

  downstream: nothing reads these files — `git grep` for the two deleted names finds one
    reference, the issue-template config, which is repointed here. No code, model, script, test,
    CI job or site source reads `north_star.md` or `site_architecture.md`. `tests/test_no_dead_issue_refs.py`
    covers `CLAUDE.md` and the handover only; the GitHub-era numbers removed from
    `site_architecture.md` §7 were not in its scope.

  what stops being enforced if it is wrong: nothing — prose only.

  layer_rules: n/a. deploy_order: none. blast_radius: none in behaviour; in prose, a reader of
    either section now finds one line and a link instead of a stale sequence.

acceptance_criteria:
  - `docs/agent_company_roadmap.md` and `docs/backlog.md` are gone; `git grep` for either name
    over the tree finds nothing.
  - `docs/north_star.md` "Next milestone" and `docs/site_architecture.md` §7's go-live bullet
    each point at the GitLab milestones in one line, keeping the non-roadmap facts (the quality
    bar; Firebase hosting, no MVP to switch from, no redirects); no GitHub-era issue number
    remains in either section.
  - `.github/ISSUE_TEMPLATE/config.yml` links the milestones, not the deleted file.
  - The handover names the milestones as the roadmap and #127 (Home) as the first review.

decisions_taken: >
  CPO, 2026-09-12, in chat: "go, create the milestones and delete the dead docs". The milestones
  and the review issues were created before this branch (GitLab #127–#140, milestones 1–7);
  this branch is the documentation half of that instruction.

  THRESHOLD — NEW MECHANISM: none. THRESHOLD — RECURRING COST: none.

decisions_reserved:
  - The wireframe overview's status table (`docs/wireframes/00_overview.md`) — corrected page by
    page as each review issue closes, not here. Whether the dormant `.github/ISSUE_TEMPLATE/`
    directory should exist at all.

done_when:
  - The four criteria proven; `pytest tests/test_no_dead_issue_refs.py` green.

amendments:
  - none yet.
