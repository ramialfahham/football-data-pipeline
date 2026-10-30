# Verification — the committed team samples, re-exported from prod

The 34 payloads were written on 2026-10-30, after main's build of the merge of MR !353, by a
scratch driver that imports scripts/export_site_data.py, orders the 34 committed ids first in
fetch_team_payloads' grouping and calls it with sample=34, so the fixtures, roster, career,
competitions and recent-match reads are scoped to the 34 while mart_team_profile and
mart_team_competition_benchmarks stay whole for the scatter and the strip. Each file is written
by write_entity into a scratch folder and copied in unchanged; the marts read about 311 MB.

criteria_demonstrated:
  - site_v2/src/data/teams/ holds the same 34 file names; git reports 34 modified files and none added or removed.
  - All 34 slugs equal the committed ones (a script compared each pair: no difference).
  - teams/33.json carries recent_matches (5), its one featured season carries competitions and league_strip, and all 32 of its squad members carry appearances.
  - The data folder holds no ignored untracked file (git status --ignored lists none), so the build reads exactly the tracked set; npm run build in site_v2 exits 0 with its prebuild tests, 2,268 pages built, "audit-seo: 2269 built page(s) checked. OK." and "check-built-pages: ... OK."

The Team page at /en/teams/manchester-united-fc/ renders in the v2 dev server with no console
error. pytest: 1,612 passed, 2 skipped; the offline gates pass.
