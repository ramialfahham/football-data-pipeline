# Verification — a window of one played match on mart_leaderboards

The site does not read the new match boards: every export read of mart_leaderboards takes the
season rows alone. This change leaves site_v2/src untouched: `git diff --stat gitlab/main --
site_v2/src` on the branch prints nothing. The fouls label goes in with the page that shows it.

criteria_demonstrated:
  - Committed sample payloads unchanged: `git diff --stat gitlab/main -- site_v2/src/data` on the branch prints nothing; no file under site_v2/src/data differs from main.
  - Built site unchanged: no file under site_v2/src differs from main, so the build reads the same inputs. `npm run build` on the branch, the full CI sequence, exits 0: 120 site tests pass, check-page-specs validates 10 pages, 2,538 pages are built, audit-seo checks 2,539 built pages OK, and check-built-pages reports OK. An earlier build of the branch with the label still in strings.ts was byte-identical to main over all 2,539 HTML files.
  - Season rows only: `test_every_leaderboard_read_takes_the_season_rows_only` in tests/test_export_site_data.py finds the three reads of mart_leaderboards in scripts/export_site_data.py (competition, leaderboard, landing) and asserts each carries `window_type = 'season_to_date'`; it passes.
