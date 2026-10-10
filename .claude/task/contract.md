# Task contract — the site build carries every played match

objective: >
  The site build renders and checks about 63,000 match payloads within the CI's 8 GB heap. The
  match page reads its data files from disk instead of bundling them, and the SEO check keeps only
  what it compares.

refs: >
  #174 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/174): every played
  match in the data window gets a page, approved in chat, 2026-10-10. The plan: approved in chat,
  2026-10-10.

scope_paths:
  - site_v2/src/pages/?lang?/?competition?/?matches?/?fixture?.astro
  - site_v2/src/pages/?lang?/?teams?/?team?.astro
  - site_v2/scripts/audit-seo.mjs
  - site_v2/scripts/audit-seo.test.mjs
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: scripts/export_site_data.py writes site_v2/src/data/fixtures/*.json; unchanged.
  downstream: `grep -rln "data/fixtures" site_v2/src` lists the match page and its spec only, so
  the match page is the one reader of those files. The SEO check runs after every site build
  (site_v2/integrations/seo-audit.mjs) and in CI's build:site-v2; its checks and its verdicts are
  unchanged.
  layer_rules: the page selects and renders served data; nothing is computed.
  deploy_order: none; a site build.
  blast_radius: no built page changes (verified by comparing every page's text with main). The
  build's memory and time change; measured before and after at 628 and 62,800 match payloads.

acceptance_criteria:
  - Every built page's visible text on the branch equals main's.
  - A build of 62,800 match payloads with NODE_OPTIONS=--max-old-space-size=8192 ends with exit 0 and every build check passing; the same build on main runs out of memory.

decisions_taken: >
  Every played match gets a page, and the build must carry it: approved in chat, 2026-10-10. The
  plan (the match page reads its files with node:fs; the SEO check keeps each page's dead links
  and its link count, not its full link list): approved in chat, 2026-10-10.

  THRESHOLD DECLARATIONS: NEW MECHANISM: the match page's data is read from disk at build time
  instead of through Vite's import; no new dependency, library or service. RECURRING COST: none.

decisions_reserved:
  - The played match payload and page (#175, #176), and any change to the other data the build bundles (teams, players, competition payloads).

done_when:
  - npm test in site_v2 passes; pytest tests/ passes.
  - The criteria are shown in .claude/task/acceptance_evidence.md.

amendments: >
  The team data joins: approved in chat, 2026-10-10. Measured on a scratch build of today's live
  site at full scale (5,024 upcoming match payloads, 3,348 team payloads of ~540 KB each): with
  the team files bundled the build runs out of memory at 8 GB while bundling; read from disk it
  passes every check (25,662 pages, 4.2 GB peak memory). The team page and the match page's team
  slug list read src/data/teams/*.json with node:fs. A third criterion: that live-site build ends
  with exit 0 and every build check passing.
