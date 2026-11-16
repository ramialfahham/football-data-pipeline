# Task contract — the separator dot leaves the site, by the job it does

objective: >
  Issue #243: the middle dot (U+00B7, also &middot;) is removed from every rendered line of site_v2,
  by the job it does. Facts separated in a header line or a row's secondary line become unbreakable
  units in one wrapping line (one shared class, 12px column gap, no glyph). A name joined to its
  qualifier becomes two lines in the row's existing muted secondary style. A dot inside wording
  (round names, goal-minute lists, about sentences, titles) becomes a comma and a space in EN, DE
  and FI. dotEdges.mjs, the dot unit in wholeWords.mjs, data-dot, dot-only CSS and the
  dot-placement tests and registry rules go.

refs: >
  #243. Rule approved in chat, 16 Nov 2026 (the coordinator's brief of that date, which replaced an
  earlier own-line rule that was withdrawn).

scope_paths:
  - .claude/task/243-no-separator-dot/
  - site_v2/src/components/chrome/SiteFooter.astro
  - site_v2/src/components/competition/CompetitionHeader.astro
  - site_v2/src/components/competition/CompetitionTabs.astro
  - site_v2/src/components/competition/RankingBoard.astro
  - site_v2/src/components/competition/SeasonFacts.astro
  - site_v2/src/components/competition/StandingsTable.astro
  - site_v2/src/components/fixture/HeadToHead.astro
  - site_v2/src/components/fixture/Masthead.astro
  - site_v2/src/components/fixture/MatchGoals.astro
  - site_v2/src/components/fixture/MatchLineups.astro
  - site_v2/src/components/fixture/MetricRow.astro
  - site_v2/src/components/fixture/PlayerRow.astro
  - site_v2/src/components/fixture/RecentMatch.astro
  - site_v2/src/components/home/HeroFixtures.astro
  - site_v2/src/components/player/PlayerComparison.astro
  - site_v2/src/components/player/PlayerHeader.astro
  - site_v2/src/components/player/PlayerIndexRow.astro
  - site_v2/src/components/player/PlayerRecent.astro
  - site_v2/src/components/team/TeamCompetitions.astro
  - site_v2/src/components/team/TeamFixtureGroup.astro
  - site_v2/src/components/team/TeamHeader.astro
  - site_v2/src/components/team/TeamSquad.astro
  - site_v2/src/i18n/strings.ts
  - site_v2/src/layouts/Layout.astro
  - site_v2/src/lib/dotEdges.mjs
  - site_v2/src/lib/dotEdges.test.mjs
  - site_v2/src/lib/wholeWords.mjs
  - site_v2/src/lib/wholeWords.test.mjs
  - site_v2/src/pages/[[]lang]/[[]competition]/index.astro
  - site_v2/src/pages/[[]lang]/[[]competition]/[[]matches]/[[]fixture].astro
  - site_v2/src/styles/system.css
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - tests/test_phone_built_pages_231.py
  - tests/test_phone_fixes_231.py
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json
  - tests/fixtures/chart_screenshots/

protected_override: >
  docs/design/components.yml: the new shared line class is registered and its rules about where a
  dot may sit are removed with the dot. Approved in chat, 16 Nov 2026.

impact_map: >
  writers: none; page templates, one build-step module (wholeWords.mjs, runs in middleware.ts over
  every page's body text), one client script (dotEdges.mjs, deleted), the stylesheet, label
  strings, the component registry. No dbt model, no export script.
  downstream: site_v2/dist only. leaf: consumption layer, no computation added or changed.
  layer_rules: not applicable; no computation.
  deploy_order: none; deploy:site-v2 is manual.
  blast_radius: every rendered middle dot on every page and language becomes a unit gap, a second
  line or a comma; registry rule text and block_standard.md are regenerated; pins only go down.

acceptance_criteria:
  - On the built pages (Home, Matches, a competition overview, Bayern München, a played match, a player page) at 375px and 1280px in EN, DE and FI, no rendered text contains "·".
  - Every dot that separated facts is now one shared line class; each fact is one unbreakable unit, the gap is 12px, nothing else is added.
  - Every name-plus-qualifier place shows the name on line 1 and the qualifier on line 2 in the row's existing muted secondary style.
  - Every dot inside wording is ", " in EN, DE and FI.
  - No page scrolls sideways at 375px or 1280px and nothing is clipped.
  - No pin baseline (component registry, design inventory) rises.

approved_design:
  - home: #127
  - competitions: #128
  - competition: #129
  - matches: #130
  - match: #132
  - teams: #133
  - team: #134
  - players: #135
  - player: #136

depends_on:
  - none: the work is on main alone

shared_files:
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json
  - tests/fixtures/chart_screenshots/

decisions_taken: >
  The three-job rule above, approved in chat 16 Nov 2026 on #243. A place that fits none of the
  three is left and reported.

decisions_reserved:
  - none: the rule is approved; questions go to the coordinating session.

done_when:
  - python scripts/ci_local.py --mr is green.
  - Full pytest and the site's node tests pass.
  - Built pages at 375 and 1280, EN DE FI, show zero "·" and no overflow.

amendments:
  - + tests/fixtures/chart_screenshots/ (scope and shared files) — authority: the comparison legend label lost its dot, so five chart screenshot pins change; they are renewed from the CI image's own output. Content: pins only.
