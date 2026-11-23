# Task contract — the committed sample carries our crest paths; the provider-image pin is 0 (MR B)

objective: >
  The committed sample under `site_v2/src/data/**` is rolled forward from prod, now that
  `dim_team` and `dim_league` publish `/crests/{teams|leagues}/{id}-104.webp`, so the sample's
  crests and league logos are our own paths. `IMAGE_PINS.providerImage` in
  `site_v2/scripts/check-built-pages.mjs` goes from 59,337 to 0, so the built-pages check fails any
  page that renders a crest or logo from the provider's host on every build, sample or full. The
  runbook's order wording for the bucket is corrected. Done means 0 provider images in `dist/` and
  #36 ticked.
refs: "#36, #290 (gate item: crests from our own host)"

scope_paths:
  - site_v2/src/components/ui/ChartLegend.astro
  - tests/fixtures/chart_screenshots/**
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json
  - site_v2/src/data/**
  - site_v2/scripts/check-built-pages.mjs
  - site_v2/scripts/check-built-pages.test.mjs
  - site_v2/src/data/README.md
  - site_v2/.gitignore
  - .gitignore
  - deploy/nightly/README.md
  - .claude/task/36-crest-sample/contract.md
  - .claude/task/36-crest-sample/rendered_page_evidence.md
  - .claude/task/36-crest-sample/acceptance_evidence.md
  - .claude/task/36-crest-sample/review.md
  - .claude/task/36-crest-sample/review_input.patch

impact_map: >
  writers: the committed sample has one writer, `scripts/export_site_data.py` run as the recipe in
  `site_v2/src/data/README.md` (step 1 to 6). Nothing is hand-edited. The pin has one reader,
  `checkImageOrigins` in `site_v2/scripts/check-built-pages.mjs`, run by `npm run build` and by the
  full-export gate of `fdp-site`.
  downstream: every committed payload that carries a crest or league logo (landing, teams, matches,
  fixtures, competition, players) changes the address from the provider's to our path where an object
  is stored; a team without a stored object keeps a null logo and the page shows initials. One page
  component changes: `site_v2/src/components/ui/ChartLegend.astro` puts each legend label in one
  `<span>`. Its consumers, from `grep -rn ChartLegend site_v2/src`, are
  `site_v2/src/components/player/PlayerComparison.astro` (Player page),
  `site_v2/src/components/team/TeamDeserved.astro` and
  `site_v2/src/components/team/TeamLeagueStrips.astro` (Team page, Performance tab). All three pass
  plain strings; no CSS selects a child of `.chart-key` as a text node, so a plain label renders as
  before. The evidence is `rendered_page_evidence.md` in the task folder.
  blast_radius: the MR and main builds (`build:site-v2`) read the sample. A pin of 0 holds on every
  build, so a sample payload that still carries a provider address fails CI. The nightly full export
  carries the same paths already, so the pin cannot fail the nightly for a path that was published
  by the crest MR.
  deploy_order: nothing to order. The crest fill is complete and the dimensions publish the paths.

depends_on:
  - none: the crest-hosting MR (!516) and the first fill are on main and in prod

shared_files:
  - tests/fixtures/chart_screenshots/* the chart screenshot baselines are retaken because the committed sample changed; the layout and the axes do not change. glab mr list shows no other open MR that changes them
  - tests/fixtures/design_inventory/baseline*.json a count that fell is lowered; no count rises and no pin is loosened. glab mr list shows no other open MR that changes them

decisions_taken: >
  The coordinating session's message of 2026-11-23 orders this MR after the verified first fill:
  regenerate the sample from prod read-only, set the provider-image pin to 0, correct the order
  wording in the runbook. The CPO's ruling on how crests and placeholders look (approved in chat,
  2026-11-22, #36) stands. No new dependency, no new mechanism, no provider call. The read-only
  export queries run on prod under the standing BigQuery rule: a dry run first and the size reported.

decisions_reserved:
  - "none: the change moves committed data to the paths already published and lowers a pin"

approved_design:
  - player: #136
  - team: #134
  - none: no other page output changes beyond the crest address; the placeholder for a team without a crest is the existing approved initials spot. The player page change applies the ruled row "Name in whole words" of docs/wireframes/block_standard.md to the comparison legend: a label that holds markup wraps as one text between words.

acceptance_criteria:
  - No file under site_v2/src/data names a provider team or league image address, so the built pages carry 0 provider crest or logo images.
  - On the player page of Rabiot-Provost (id 272) at 280, 375 and 1010 px in en, de and fi, no comparison legend key is wider than its legend and the name wraps between words.
  - The design inventory reports 0 failures, and its pin for the chart on the Player pages stays at 0.
  - The retaken chart screenshots differ from the old ones in their data only: sizes of the scatter and strip charts equal, and the axes and layout unchanged.

done_when:
  - "`cd site_v2 && node --test` passes and `npm run build` reports 0 provider crest/logo images."
  - "`git grep -c 'api-sports.io/football/\\(teams\\|leagues\\)' -- site_v2/src/data` finds no match."
  - "On the player page of Rabiot-Provost (id 272) at 280, 375 and 1010 px in en, de and fi, no legend key is wider than the legend and the name wraps between words."
  - "The design inventory pin `Player pages · miss · Chart` stays at 0."
  - "`python scripts/ci_local.py --mr` passes."

amendments:
  - "The sample's new board players put a very long name in the legend of the player comparison, and the design inventory reported a legend wider than its page at 280 px. The coordinating session's message of 2026-11-23 (approved in chat, 2026-11-23) orders the fix in this branch, applying the ruled whole-words behaviour, and the refresh of the chart screenshot baselines after a check that the 18 differences come only from the data. Scope gains ChartLegend.astro, the chart screenshot baselines and the design inventory baselines."
  - "Review round 3 found that the legend is also used by the Team page. The page-surface line gains team: #134, the impact_map names the three consumers, and scope gains rendered_page_evidence.md."
  - "The commit gate for a change under site_v2/src asks for acceptance_criteria and acceptance_evidence.md. The criteria restate the done_when lines that concern the built pages, and the evidence file is in scope_paths."
