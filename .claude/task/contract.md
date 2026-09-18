# Task contract — README: a static CI badge pointing at GitLab

objective: >
  Add one static badge to the README's badge row — "CI · GitLab", linking to the GitLab
  repository — in place of the two dead GitHub Actions badges !204 removed. Static because the
  project's pipelines are members-only (`public_jobs: false`) and the CPO chose to keep them so,
  which makes a live status badge impossible for a visitor.

refs: >
  CPO in chat, 2026-09-18: asked "what if we put the CI/CD not public on GitLab", offered a
  static badge linking to the GitLab repo or no badge, answered "yes, static badge". !204
  (merged) removed the two dead badges and left the CI bullet naming GitLab.

scope_paths:
  - README.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  The badge is a shields.io static image in the style of the row's other badges (shields.io with
  a logo), labelled `CI` / `GitLab`, GitLab's brand colour, linking to the repository page rather
  than the pipelines page, because a visitor who clicks the pipelines page meets a sign-in prompt.
  One line added; nothing else in the README changes.

decisions_reserved:
  - none: the CPO chose static over public pipelines in chat; the badge's text and link target are the form, decided here and stated in the MR head.

done_when:
  - `README.md` line 5–9 badge row carries exactly one new badge, `CI`/`GitLab`, linking to `https://gitlab.com/rami.al-fahham/football-data-pipeline`; the image URL returns 200.
  - `git diff --stat gitlab/main -- README.md` shows one insertion and no deletion.

amendments: (none)
