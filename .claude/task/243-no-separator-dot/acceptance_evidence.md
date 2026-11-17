# Verification — the separator dot leaves the site, by the job it does

Read from the dev server of this branch (site_v2 sample data, port 4323) at 375px and 1280px in EN, DE and FI on six page kinds: Home, Matches, a competition overview, the Bayern München team page, a played match page, a player page.

criteria_demonstrated:
  - **No rendered "·":** the fetched HTML of the Bayern München team page, the played match page, the player page and the Bundesliga page holds 0 "·" and 0 `&middot;`; on 36 measurements (6 page kinds, 3 languages, 2 widths) the rendered text holds 0 "·".
  - **Facts are one shared class:** every fact line (team, competition, player and match headers, the kick-off line, the masthead standing, squad, player-index, line-up, result, recent and head-to-head rows, the goals-and-points and goals-and-assists lines, the footer) carries `facts-line`; the class is 12px column gap, 0 row gap, and each unit is `white-space: nowrap`; it is registered in `docs/design/components.yml`.
  - **Name and qualifier are two lines:** the competition row on the team page shows the competition name on line 1 and the round note on line 2 in the row's muted 12px style; the line-up head shows the team name and the formation on a second muted line.
  - **Wording takes a comma:** the 25 round names in `site_v2/src/i18n/strings.ts` (EN, DE, FI), the about sentence, the played match description, the goal detail list and the comparison legend label use ", ".
  - **No sideways scroll, nothing clipped:** on all 36 measurements the page is not wider than the viewport and no fact line or unit is wider than its box.
  - **No pin rises:** the component registry reports 0 failures against its unchanged baseline; the design inventory's SiteFooter literal-text count falls from 3 to 2 and its baseline is lowered.
