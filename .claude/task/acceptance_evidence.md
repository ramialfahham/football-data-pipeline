# Acceptance evidence — the site build carries every played match

Full-scale builds ran in a scratch worktree at gitlab/main with this branch's three site files
copied in byte for byte, on payload copies of the committed sample (new ids, slugs, titles and
descriptions). Every build process ran with `NODE_OPTIONS=--max-old-space-size=8192`, as CI sets
it; a preloaded sampler recorded each process's peak.

criteria_demonstrated:
  - TODAY'S SITE UNCHANGED. Branch build of the committed sample: 2538 pages, `audit-seo: 2539 built
    page(s) checked. OK.`, `check-built-pages: ... OK.`, npm test 118 of 118. A script compares the
    visible text of all 2539 built HTML files with main's build: 0 differ.
  - EVERY MATCH. 62,800 match payloads: exit 0, `audit-seo: 189055 built page(s) checked. OK.`,
    `check-built-pages: 188400 match page(s) = 62800 payload(s) x 3 ... OK.` Page build 14.6 GB peak
    memory, 2.9 GB peak heap, 16.8 min; SEO check 7.6 GB peak memory, 7.2 GB peak heap, 58 s. On main
    the same harness runs out of memory already at 12,560 payloads (`FATAL ERROR: Reached heap limit
    Allocation failed`).
  - TODAY'S LIVE SITE AT FULL SCALE. 5,024 upcoming match payloads and 3,348 team payloads: exit 0,
    `audit-seo: 25663 built page(s) checked. OK.`, `check-built-pages: 15072 match page(s) ... OK.`
    Page build 4.3 GB peak memory, 2.5 GB peak heap, 3.7 min; SEO check 1.4 GB. On main the same
    build runs out of memory while bundling (`FATAL ERROR: Ineffective mark-compacts near heap
    limit`).
