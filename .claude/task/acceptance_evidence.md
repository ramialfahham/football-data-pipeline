# Verification — pages hold on narrow screens

Built locally with `npm run build` in `site_v2` on the committed sample: exit 0, the site's tests
pass (with `fitBlocks.test.mjs`), audit-seo checks 2,269 pages OK, check-built-pages checks 1,644
match pages and 15,606 match rows OK. Main's build (`gitlab/main` at c1f2a9a6) was kept beside it.
Both builds were served over HTTP and measured in the browser, each page in an iframe of the given
width with the scrollbar hidden as on a phone, every tab opened in turn. The sample is Home,
Competitions, the Bundesliga, Champions League and World Cup pages, the Bundesliga's Rankings tab,
the Matches page and two match pages, in EN, DE and FI.

criteria_demonstrated:
  - At 280, 320, 375, 430, 700, 768, 1010 and 1440px, 216 renders of the branch build show no element whose text is narrower than its longest word. On main's build the same sweep found names split or overrunning on Home, the competition page's tables, the Rankings boards and the match page's Recent matches, at 280–430px; the Deserved points table gave a club name 0px at 280px.
  - The same 216 renders show no sideways scroll except the filter rows of the DE Competitions and Matches pages at 280px (13–17px, `.seg-btn`), which the Filter bar (#223) replaces. On main's build the header pushed every page 2px sideways at 280px, and the Competitions grid 16px in EN and FI.
  - On the DE competition page at 375px the Deserved points table is marked fit-two; the 1. FC Union Berlin row is 69px high with the name on one line (111px wide) and the four numbers under their heads. On main's build the same row was up to 263px high with the name in single letters.
  - On the DE competition page at 320px the Season pulse block is marked fit-two; on the Team page mock's Standing block the longest row needs 151px of 233px at 280px and stays side by side.
  - At 1010 and 1440px, 48 readings (16 pages in three languages, every tab) of every element's box, images excluded, are identical on both builds. The images differ only by load timing.
  - `python scripts/check_design_inventory.py --dist site_v2/dist`: 24 pages × 3 viewports × 3 languages, 174 renders, 0 failures and 0 warnings. On main's build the same check gives 123 failures, 90 of them the new Fitted block row: without the script no block carries fit-one or fit-two, so removing or breaking the script fails the check. The Header row, a warning at 700px on main, is now ruled and measured.
