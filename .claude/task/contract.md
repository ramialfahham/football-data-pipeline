# Task contract — a floor under the match-row link check

objective: >
  The built-pages check fails when no row on any built page names its match with data-fixture
  while the build carries match payloads, so a component that drops the attribute cannot pass the
  row-link check by checking nothing. The row pattern also reads data-fixture in any attribute
  position: today it skips every tag where data-fixture is the first attribute.

refs: >
  The platform review of !320, the played match page
  (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/merge_requests/320), which named the
  missing floor as not blocking. The plan: approved in chat, 2026-10-16.

scope_paths:
  - site_v2/scripts/check-built-pages.mjs
  - site_v2/scripts/check-built-pages.test.mjs
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: none; the change is to a read-only check over the built HTML and src/data/fixtures.
  downstream: `grep -rn check-built-pages` outside node_modules and dist finds three readers:
  site_v2/package.json (`npm run build` runs it after astro build and audit-seo),
  site_v2/scripts/build-wiring.test.mjs (pins that order; unchanged) and its own test file.
  Every CI job that runs `npm run build` in site_v2 therefore runs it.
  guard: the check can only add failures. It now fails a build with fixture payloads and no
  data-fixture row, and it reads rows it skipped before. On the !320 build output the current
  pattern read 18,093 rows; the fixed pattern reads 19,650 (1,557 more, all of the form
  `<div data-fixture=… class=…>`) and finds 0 rows whose link disagrees with its payload, so it
  does not turn that build red. The build in this MR re-measures it.
  layer_rules: none; no dbt model, export or page source changes.
  deploy_order: none; nothing is deployed by this change.
  blast_radius: no page changes; a site build can fail where it passed before only when a row's
  link disagrees with its payload or no row names its match.

decisions_taken: >
  The floor is build-wide: one row named anywhere is enough. It is styled on checkTabPagesFound
  (a count passed in, one issue when it is zero and the payloads call for rows). No new mechanism,
  dependency or recurring cost.

decisions_reserved:
  - none: the plan was approved in chat, 2026-10-16, and this builds it unchanged.

done_when:
  - node --test site_v2/scripts/check-built-pages.test.mjs passes; the two new tests fail against the code before this change
  - npm run build in site_v2 passes and its OK line reports the rows checked
  - the validate-local gates pass

amendments: (none)
