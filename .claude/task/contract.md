# Task contract — the site build's memory at full scale

objective: >
  Measure where the full-scale site build's memory goes, phase by phase. The match page and the
  team page then each read their own data file while that page renders, and the SEO check keeps
  only what it compares, so the build no longer holds every data file at once.

refs: >
  #208 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/208): the issue and
  its plan, approved in chat, 2026-10-10. Measure first, before an incremental build: approved in
  chat, 2026-10-10.

scope_paths:
  - site_v2/src/pages/?lang?/?competition?/?matches?/?fixture?.astro
  - site_v2/src/pages/?lang?/?teams?/?team?.astro
  - site_v2/src/lib/format.ts
  - site_v2/scripts/audit-seo.mjs
  - site_v2/scripts/audit-seo.test.mjs
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: scripts/export_site_data.py writes site_v2/src/data/fixtures/*.json and
  site_v2/src/data/teams/*.json; unchanged.
  downstream: `grep -rln "data/fixtures" site_v2/src` lists the match page and its spec only;
  `grep -rln "data/teams" site_v2/src` lists the match page, the team page, the team spec and the
  spec schema. So the two pages are the only code readers. The SEO check runs as a child process
  after every site build (site_v2/integrations/seo-audit.mjs) and in CI's build:site-v2 and
  deploy:site-v2; its checks and its verdicts are unchanged.
  layer_rules: the page selects and renders served data; nothing is computed.
  site_v2/src/lib/format.ts: `grep -rl "lib/format" site_v2/src | wc -l` gives 51 importers, every
  page type among them; no script or integration imports it. Its exports and their output are
  unchanged.
  deploy_order: none; a site build.
  blast_radius: no built page changes, verified by a byte compare of every built file with main's
  build of the same day. The build's memory and time change; measured before and after at full
  scale.

acceptance_criteria:
  - A full-scale build is measured: 62,800 match payloads and 3,348 team payloads. Peak process memory, peak heap and time are recorded per phase (bundling, page writing, sitemap, SEO check, built-pages check), on main and on this branch, on this issue.
  - A match page and a team page are each built from their own data file, read while that page renders. The build no longer holds every data file at once.
  - "Today's site is unchanged: every file built from the committed sample is byte-identical to main's build, built the same day."
  - With a 3 GB heap cap, the full-scale build passes every build check. If it does not, this issue names the phase that runs out of memory and its peak.

decisions_taken: >
  The issue's plan, approved in chat, 2026-10-10: getStaticPaths of the match page and the team
  page returns id, slug and locale only, and each page reads its own file as it renders. If the
  profile puts a peak in the SEO check, it keeps only the fields it compares, and its first pass
  collects paths from file names without reading the HTML.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; the pages already read their data with node:fs,
  and this moves the read of a page's own file from getStaticPaths into the page. RECURRING COST:
  none.

decisions_reserved:
  - A memory peak anywhere other than the two pages' route data and the SEO check goes to the CPO with the profile, unfixed.
  - The incremental build and the machine or runner size, decided from this issue's numbers.
  - The played match payload and page (#175, #176), and any change to the other data the build bundles (competition payloads).

done_when:
  - npm test in site_v2 passes; pytest tests/ passes.
  - A build of the committed sample ends with both build checks printing OK.
  - A byte compare of every built file against main's build of the same day finds 0 differences.
  - The full-scale measurements, main and branch, at 8 GB and 3 GB heap caps, are in .claude/task/acceptance_evidence.md and on #208.

amendments: >
  site_v2/src/lib/format.ts joins: approved in chat, 2026-10-10. Main's full-scale profile put
  about 7.8 GB of the page-writing peak outside the heap (11.2 GB process memory, 3.3 GB heap).
  format.ts builds a new Intl formatter on every call; a probe of that pattern held 4.2 GB outside
  the heap over 400,000 calls, against 0.05 GB with one formatter reused. The file keeps one
  formatter per locale and option set; every formatted string is unchanged.
