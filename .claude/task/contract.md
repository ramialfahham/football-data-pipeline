# Task contract — the Team page shows the served league rank, and a build check holds it

objective: >
  The Team page's "Compared with the league" block shows the league rank as the warehouse serves
  it. This task removes the unused site helpers that flip a served rank and fixes the mock
  generator's flip. A built-page check fails every build whose Team page shows another rank.

refs: >
  #236 (the issue text and plan approved in chat, 2026-10-30); design #134.

scope_paths:
  - site_v2/src/lib/bars.ts
  - site_v2/src/components/team/TeamLeagueStrips.astro
  - site_v2/scripts/check-built-pages.mjs
  - site_v2/scripts/check-built-pages.test.mjs
  - design-mocks/gen_team_mock.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  Short form: frontend, build check and mock only. No model, export or payload change.
  `TeamLeagueStrips.astro` is rendered only by `site_v2/src/pages/[lang]/[teams]/[team].astro`
  (`grep -rn TeamLeagueStrips site_v2/src`). `displayRank`, `rankFill` and `beatsMedian` have no
  caller in `site_v2/src` or `design-mocks/` (grep). The row already shows `ordinal(b.rank, lang)`,
  the served rank. blast_radius: no shown number changes; each row gains one invisible
  `data-metric` attribute; `npm run build` gains one check on the Team pages.

approved_design:
  - team: #134

acceptance_criteria:
  - "On the Team page, \"Compared with the league\", a less-is-better metric shows the club's league rank as the warehouse serves it. Less is better for fouls, goals against, shots on target against, yellow cards and red cards. The club with the lowest fouls per match shows 1st."
  - "A metric where more is better keeps showing its rank as served (goals per match: the highest value shows 1st)."
  - "Every site build fails when a Team-page row shows a rank other than the served one."
  - "A test pins a less-is-better row: served rank 1 of 18 displays \"1st\", and a page showing \"18th\" for it fails."
  - "The Team-page mock generator `design-mocks/gen_team_mock.py` shows the served rank."
  - "The site code holds no helper that flips a served rank."

decisions_taken: >
  The plan approved in chat, 2026-10-30: path A, a check on the built Team pages. The check reads
  the served rank from the team payload's featured season and renders it with `ordinal`. No new
  mechanism: the rule joins `check-built-pages.mjs`, which `npm run build` already runs. No
  recurring cost.

decisions_reserved:
  - "none: no copy, label, order or shown number changes"

done_when:
  - npm test in site_v2 passes, with the new less-is-better and more-is-better cases.
  - check-built-pages.mjs passes on a sample build, or the MR's build:site-v2 job passes.
  - python -m py_compile design-mocks/gen_team_mock.py passes; the whole pytest passes.
  - The offline gates of validate-local pass.

amendments: (none)
