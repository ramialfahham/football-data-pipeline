# Task contract — the site build's two checks run after Astro exits

objective: >
  The SEO check and the built-pages check run as steps of `npm run build` after `astro build` has
  exited, instead of as child processes inside it, so their memory no longer adds to Astro's and
  the full-scale build fits ci-runner-01.

refs: >
  #209 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/209). Checks after the
  build, over a bigger machine: approved in chat, 2026-10-10. The plan: approved in chat,
  2026-10-11. The runner measurement: #208
  (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/208#note_3990668184).

scope_paths:
  - site_v2/package.json
  - site_v2/astro.config.mjs
  - site_v2/integrations/seo-audit.mjs
  - site_v2/integrations/built-pages.mjs
  - site_v2/scripts/check-built-pages.mjs
  - site_v2/scripts/build-wiring.test.mjs
  - site_v2/src/config/indexability.mjs
  - site_v2/src/specs/page-spec.schema.json
  - tests/test_no_decision_history_in_code.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: none; the two check scripts and the export are unchanged in what they check.
  downstream: `grep -rln "seoAudit\|builtPages\|integrations/seo-audit\|integrations/built-pages"`
  over site_v2 lists astro.config.mjs, the two integration files, and two comments
  (scripts/check-built-pages.mjs, src/config/indexability.mjs). `grep -n "npm run build"
  .gitlab-ci.yml` gives build:site-v2 (line 642) and deploy:site-v2 (line 1077): both run the
  build script, so both keep both checks. tests/test_governance_hooks.py names
  site_v2/integrations/seo-audit.mjs only as a routing example.
  layer_rules: none; build wiring, no page logic.
  deploy_order: none; a site build.
  blast_radius: no built page changes, verified by a byte compare of every built file with main's
  build of the same day. Lost: the route-pattern page-count log line the SEO integration printed,
  which nothing reads.

acceptance_criteria:
  - "`npm run build` runs the SEO check and then the built-pages check after `astro build` has exited; a page the SEO check refuses still makes `npm run build` exit non-zero."
  - "Today's site is unchanged: every file built from the committed sample is byte-identical to main's build, built the same day."
  - On ci-runner-01, this branch's full-scale build (62,800 match payloads, 3,348 team payloads) passes both checks without being killed; its peak process memory and time are on this issue.

decisions_taken: >
  The issue's plan, approved in chat, 2026-10-11: the build script runs `astro build`, then
  scripts/audit-seo.mjs, then scripts/check-built-pages.mjs, each only if the previous step passed;
  astro.config.mjs drops the two integrations and site_v2/integrations/ is deleted; comments and
  schema descriptions that name the integrations or astro:build:done say where the checks run now.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; two existing scripts move from build hooks to the
  build script, approved in chat, 2026-10-10. RECURRING COST: none.

decisions_reserved:
  - The machine or runner size, and the nightly site build (#156).
  - The played match payload (#175, #176), which changes the full-scale numbers.

done_when:
  - npm test in site_v2 passes; pytest tests/ passes; the offline CI gates pass.
  - npm run build on the committed sample prints both checks' OK lines after Astro completes, and a byte compare with main's build of the same day finds 0 differences.
  - A planted duplicate page makes npm run build exit non-zero with the SEO check's finding.
  - The ci-runner-01 full-scale measurement is in .claude/task/acceptance_evidence.md and on #209.

amendments: >
  tests/test_no_decision_history_in_code.py joins: authority, the approved plan's deletion of
  site_v2/integrations/ (approved in chat, 2026-10-11). One deleted file carried one flagged line,
  so the tree holds 748 flagged lines in 188 files against the pin of 749 in 189; the test requires
  the pin to follow the sweep down. Content: PINNED_LINES 749 to 748, PINNED_FILES 189 to 188.

  site_v2/scripts/build-wiring.test.mjs joins: approved in chat, 2026-10-11, after the
  platform-reviewer's round-1 finding that no test pins the build script. Content: a node --test
  file that fails unless the build script is `astro build`, then scripts/audit-seo.mjs, then
  scripts/check-built-pages.mjs, each joined by `&&`, and unless astro.config.mjs imports nothing
  from ./integrations/.
