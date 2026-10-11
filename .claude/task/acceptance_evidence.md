# Acceptance evidence — the site build's two checks run after Astro exits

The committed-sample builds ran on this machine; main's build ran in a scratch worktree at
gitlab/main the same day. The full-scale build ran on ci-runner-01 from a `git archive` of this
branch's tree. It used the `node:24` image in a container capped at 2.83 GiB, and the sample grown
to 62,800 match and 3,348 team payloads. A sampler preloaded into every Node process recorded each
one's peak, and the container's anonymous memory was read from cgroup v2 every second.

criteria_demonstrated:
  - CHECKS AFTER ASTRO, STILL GATING. `npm run build` on the branch prints `[build] Complete!` (log line 2717), then `audit-seo: 2539 built page(s) checked. OK.` (2718), then `check-built-pages: 1884 match page(s) = 628 payload(s) x 3 ... OK.` (2719), exit 0. `scripts/build-wiring.test.mjs` pins the wiring: both its tests fail against main's package.json and astro.config.mjs and pass on the branch. A planted page with a new id and slug but a repeated title (a gitignored `fixtures/9999991.json`, deleted after): after `[build] Complete!` the SEO check prints `audit-seo: 9 violation(s) in 2542 built page(s):`, listing the repeated title, description and h1 in each locale. `npm run build` exits 1 and the built-pages check does not run.
  - TODAY'S SITE UNCHANGED. Committed sample, built the same day: main and branch each produce 2,543 files. A script byte-compares every file: 0 differ, 0 on one side only. npm test 120 of 120. The design check on the branch's sample build: 165 renders at 375, 700 and 1010px, 0 failures, 27 warnings, the same as main.
  - FITS CI-RUNNER-01. The branch's `npm run build` at full scale, with `NODE_OPTIONS=--max-old-space-size=8192` as deploy:site-v2 sets it: exit 0 in 17.7 min, `audit-seo: 198991 built page(s) checked. OK.`, `check-built-pages: 188400 match page(s) = 62800 payload(s) x 3 ... OK.` memory.events oom_kill 0. The container peaks at 1.69 GiB. Per step: astro build 11.8 min at 1.70 GiB, SEO check 3.6 min at 1.13 GiB, built-pages check 2.2 min at 0.10 GiB. Main as wired before is killed on the same runner at 2.59 GiB. The numbers are on #209.
