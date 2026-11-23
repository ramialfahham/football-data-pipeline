# Verification — the sample carries our crest paths

Read from the built output of `python scripts/ci_local.py --mr` (job `build:site-v2` for the pages, job `validate:ui` for the inventory and the screenshots) and from the dev server for the legend geometry; the geometry is in rendered_page_evidence.md.

criteria_demonstrated:
  - **Provider images in the built pages:** `check-built-pages` on the sample build prints "0 provider crest/logo image(s), 0 player photo(s), 0 other foreign image(s); 1226 crest path(s) on our domain", and `git grep "api-sports.io/football/(teams|leagues)" -- site_v2/src` finds no file.
  - **Legend of player 272:** the dev server reports legend scrollWidth equal to clientWidth in all nine cells (en, de, fi at 280, 375 and 1010 px); the name key is 248 x 39 at 280 px and 343 x 39 at 375 px, so it wraps to two lines, and 20 px high at 1010 px.
  - **Design inventory:** the run prints "175 pages · 6 viewports · 3 languages · 13686 renders · 0 failures · 0 warnings" and "0 off the baseline", and the Player pages row reads "classes 0" with no chart miss.
  - **Chart screenshots:** `check_chart_screenshots` prints "0 screenshot difference(s) over 18 screenshots" against the retaken baselines; the scatter and strip sizes equal the old ones (928 x 578, 343 x 359, 928 x 1124, 343 x 1640) and only the points and the axis ranges moved. The match comparison grew by 148 px because the played-match payload now has the Yellow cards and Red cards rows.
