# Acceptance evidence — the site build's memory at full scale

Full-scale builds ran in two scratch worktrees at gitlab/main, one of them with this branch's four
site files copied in byte for byte. Both used the same payload copies of the committed sample: 628
match payloads to 62,800 and 36 team payloads to 3,348, each copy with a new id, slug and team
names. That gives 198,991 pages. A sampler preloaded into every Node process of the build (the
Astro build and its two check child processes) recorded memory every 250 ms. Each process's OS
peak and its heap at exit were recorded too. Phases are cut by the build's own timestamped log
lines.

criteria_demonstrated:
  - FULL SCALE MEASURED, MAIN AND BRANCH. 8 GB heap cap, main: exit 0, 20.4 min. Bundling 3 s at 0.35 GB. Page writing 1,059 s at 11.2 GB process memory and 3.3 GB heap. Sitemap and hooks 48 s at 6.1 GB. SEO check 80 s at 7.9 GB and 7.5 GB heap. Built-pages check 30 s at 0.1 GB. Branch, same cap: exit 0, 11.1 min. Bundling 4 s at 0.35 GB. Page writing 525 s at 1.4 GB process memory and 1.2 GB heap. Sitemap and hooks 43 s at 1.7 GB. SEO check 64 s at 1.1 GB and 1.0 GB heap. Built-pages check 28 s at 0.1 GB. All build processes together peak at 11.3 GB on main and 2.5 GB on the branch. The numbers are also on #208.
  - EACH PAGE READS ITS OWN FILE. getStaticPaths of the match page and the team page hands each route its file name, the slug and the locale. The page reads its own file as it renders. At full scale the page-writing heap falls from 3.3 GB to 1.2 GB, so the build no longer holds every data file at once. Two more fixes take the rest. The SEO check copies the strings it keeps, and its first pass reads paths only. The site's number and date formatting reuses one formatter per locale and option set. Together they take the SEO check from 7.9 GB to 1.1 GB and page writing from 11.2 GB to 1.4 GB.
  - TODAY'S SITE UNCHANGED. Committed sample, built the same day: main and branch each produce 2,543 files, and a script byte-compares every file. Result: 0 differ, 0 on one side only. npm test 118 of 118, `audit-seo: 2539 built page(s) checked. OK.`, `check-built-pages: 1884 match page(s) = 628 payload(s) x 3 ... OK.` The same compare at full scale: 198,999 files each, 0 differ, 0 on one side only. The design check on the branch's sample build: 165 renders, 0 failures, 27 warnings, the same as main.
  - 3 GB HEAP CAP. Branch: exit 0, `audit-seo: 198991 built page(s) checked. OK.`, `check-built-pages: 188400 match page(s) = 62800 payload(s) x 3 ... OK.` Page writing 1.4 GB, SEO check 1.1 GB, whole build 1.8 GB. 13.3 min, slower because the design check and pytest ran alongside. Main at the same cap: page writing completes at 7.9 GB process memory and 2.5 GB heap. Then the SEO check stops with `FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory`, and the build exits non-zero.
