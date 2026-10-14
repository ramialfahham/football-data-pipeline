# Verification — a window of one played match on mart_leaderboards

The site does not read the new match boards: every export read of mart_leaderboards takes the
season rows alone, and the one site file that changes, `site_v2/src/i18n/strings.ts`, gains a
label key no page uses yet. The prebuild gate `check-page-specs.mjs` prints "10 page(s) validated
against their specs. OK." on the branch.

criteria_demonstrated:
  - Committed sample payloads unchanged: `git diff --stat gitlab/main -- site_v2/src/data` on the branch prints nothing; no file under site_v2/src/data differs from main.
  - Built site unchanged: main (5b37e6ec, a scratch worktree) and the branch each built with astro build, 2,538 pages plus the root redirect `dist/index.html`; a script compared every HTML file under dist: pages main=2539 branch=2539, only on one side 0, pages with different text 0, pages with different HTML 0 (byte-identical).
  - Season rows only: `test_every_leaderboard_read_takes_the_season_rows_only` in tests/test_export_site_data.py finds the three reads of mart_leaderboards in scripts/export_site_data.py (competition, leaderboard, landing) and asserts each carries `window_type = 'season_to_date'`; it passes.
