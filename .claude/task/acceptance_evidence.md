# Verification — a window of one played match on the Form comparison's mart

The site does not read the renamed mart's new rows: the export's form read stays scoped to
upcoming fixtures. Of the two files under site_v2/src that change, the README is read by nothing,
and the spec is read only by the prebuild gate `check-page-specs.mjs`, which checks that every mart
a spec names exists: on the branch it prints "10 page(s) validated against their specs. OK." The
checks below show the site and its payloads unchanged.

criteria_demonstrated:
  - Committed sample payloads unchanged: `git diff --stat gitlab/main -- site_v2/src/data` on the branch lists one file, `site_v2/src/data/README.md` (10 insertions, 10 deletions: the mart's new name and two sentences split); no payload under site_v2/src/data differs from main.
  - Built site unchanged: main (7601c714, a scratch worktree) and the branch each built with astro build, 2,538 pages plus the root redirect `dist/index.html`; a script compared every HTML file under dist: pages main=2539 branch=2539, only on one side 0, pages with different text 0, pages with different HTML 0 (byte-identical).
  - Fixture payload keys unchanged: tests/test_export_site_data.py feeds fetch_fixture_payloads a mart_team_window_metrics row keyed by fixture_sk and asserts the home side's form block is exactly {"window_type": "last_5", "goals_per_match": 1.4}; test_form_block_is_the_block_the_warehouse_flags asserts the same with a fixture_sk-keyed row; both pass.
