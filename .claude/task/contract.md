# Task contract — the Team page's league strip plot and scatter labels

objective: >
  The Team page's "Compared with the league" strip plot drops the league median and shows the
  team's rank first with its value under it, keeping the "better" marker (#241). The deserved
  points scatter puts the difference label on the side of the dot opposite the team name, so the
  two never overlap (#242). Five explainers become the approved one-sentence texts, and the block
  standard's two strip plot rows say what the row now shows.

refs: >
  #241, the strip plot and the explainer texts; #242, the scatter label overlap. The plan and its
  texts approved in chat, 2026-11-01.

scope_paths:
  - site_v2/src/components/team/TeamLeagueStrips.astro
  - site_v2/src/components/team/TeamDeserved.astro
  - site_v2/src/styles/system.css
  - site_v2/src/i18n/strings.ts
  - site_v2/src/specs/teams/team.spec.json
  - site_v2/scripts/check-built-pages.mjs
  - site_v2/scripts/check-built-pages.test.mjs
  - docs/wireframes/block_standard.md
  - docs/wireframes/02_team_profile.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  No dbt model and no export change; no data file changes. Consumption only: two Team page
  components, their CSS rules and five i18n keys. `teamLeagueMedian` is read only by
  TeamLeagueStrips.astro and listed in the Team page spec (grep over site_v2/src); `compDeservedExplainer` is read by the Team
  page's TeamDeserved.astro and the competition page's DeservedTable.astro;
  `homeTopPlayersIntro` and `homeTopTeamsIntro` by Home's TopPlayers.astro and TopTeams.astro;
  `teamPerfIntro` by the Team page; `teamVsLeagueIntro` by TeamLeagueStrips.astro. The `.rs-*`
  rules are used only by TeamLeagueStrips.astro.
  blast_radius: the Team page Performance tab (strip plot, scatter, two explainers), the
  competition page's deserved points explainer and Home's two top-list explainers, in all three
  locales. No served number changes.

approved_design:
  - team: #134
  - competition: #129
  - home: #127

acceptance_criteria:
  - "On the built Team page, the Compared with the league rows show no median tick and no median value; the legend lists the team first, then the other clubs; each row's right column shows the rank first in bold with the value under it; the better marker remains."
  - "On every built Team page with the deserved points scatter, in both the wide and the narrow chart, the bounding boxes of the team name and the difference label do not overlap, and the difference label stays inside the chart without reaching the y axis; the built-pages check holds the placement on every build."
  - "teamVsLeagueIntro, compDeservedExplainer, homeTopPlayersIntro, homeTopTeamsIntro and teamPerfIntro render the approved one-sentence texts in EN, DE and FI; teamLeagueMedian is gone from strings.ts."
  - "block_standard.md's Strip plot row and Strip plot value rows carry the approved texts, and check_design_inventory.py --no-mocks passes."

decisions_taken: >
  Approved in chat, 2026-11-01: the plan for #241 and #242, the five explainer texts in EN, DE and
  FI, and the two block standard texts. The difference label takes the side of the dot opposite
  the name, in both charts. The deserved points components keep passing the names the old
  explainer used; t() ignores a name the text does not use. No new mechanism, no recurring cost.

decisions_reserved:
  - "none: every decision of this task is approved, see decisions_taken"

done_when:
  - npm run build in site_v2 (node tests, SEO audit, built-pages check), the full pytest, the offline gates and check_design_inventory.py --no-mocks pass.
  - The built Team page Performance tab, a competition page and Home are checked in the Browser pane at 280, 360, 560, 768 and 1010px in EN, DE and FI.
  - The scatter name and difference label boxes are measured on every built Team page and none overlap.

amendments:
  - "Implementation within the approved plan, 2026-11-01: removing teamLeagueMedian, approved in chat, 2026-11-01, also removes it from the Team page spec's i18n key list (team.spec.json), which the build's page-spec check reads."
  - "Implementation within the approved plan, 2026-11-01: the rank now leads the strip plot's right column (approved in chat, 2026-11-01), so the built-pages check reads the shown rank from that place instead of from under the value, and its test row is built the same way; the check still compares every row's shown rank with the served one."
  - "Approved in chat, 2026-11-01, after review: where the difference label, on the side opposite the name, would reach the y axis, it moves to the name's side, one line under the name; the built-pages check fails a built Team page whose scatter label is neither opposite the name across the dot nor under it, with a test row that fails when the placement is reverted; the Team page wireframe's Compared with the league row drops `league_median`, strip-only."
