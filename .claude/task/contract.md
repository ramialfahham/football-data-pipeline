# Task contract — the chart theme and its checks

objective: >
  Issue #227 steps 3 to 5: one chart theme in code that every chart component reads, the scatter
  plot, the strip plot and the comparison element moved onto it, the site's tooltips removed, and
  checks that hold it: no chart component writes a look of its own and no site file draws a
  tooltip, every chart mark has its theme colour, the scatter plot's difference label meets
  nothing, and a changed chart look fails CI until its MR updates the pinned screenshots.

refs: >
  #227, its step 3 plan approved in chat, 2026-11-02; step 2's measurement is the issue's comment.

scope_paths:
  - site_v2/src/styles/system.css
  - site_v2/src/lib/chartTheme.ts
  - site_v2/src/lib/chartMarks.mjs
  - site_v2/src/components/ui/ChartLegend.astro
  - site_v2/src/components/team/TeamDeserved.astro
  - site_v2/src/components/team/TeamLeagueStrips.astro
  - site_v2/src/components/fixture/MetricComparison.astro
  - site_v2/src/components/fixture/MetricRow.astro
  - site_v2/src/components/fixture/FormSegment.astro
  - site_v2/src/components/fixture/MatchStats.astro
  - site_v2/scripts/check-built-pages.mjs
  - site_v2/scripts/check-built-pages.test.mjs
  - docs/wireframes/block_standard.md
  - tests/fixtures/design_inventory/baseline.json
  - scripts/check_chart_components.py
  - tests/test_check_chart_components.py
  - scripts/check_chart_screenshots.py
  - tests/test_check_chart_screenshots.py
  - tests/fixtures/chart_screenshots/*
  - .gitlab-ci.yml
  - .claude/skills/validate-local/SKILL.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

protected_override: >
  Approved in chat, 2026-11-02: the CPO approved the #227 step 3 plan, which adds the chart checks
  and their artifacts folder to the validate:ui job in .gitlab-ci.yml.

impact_map: >
  pages: TeamDeserved.astro and TeamLeagueStrips.astro have one importer,
  site_v2/src/pages/[lang]/[teams]/[team].astro (lines 145-146), so every Team page in every
  language changes in its Performance tab; `grep -rln "TeamDeserved|TeamLeagueStrips|chartMarks"
  site_v2/src` returns only TeamDeserved.astro and that page. TeamLastSeason.astro and its rules are
  unchanged (`git diff gitlab/main -- site_v2/src/components/team/TeamLastSeason.astro` is empty).
  The comparison element (MetricComparison.astro and MetricRow.astro, framed by FormSegment.astro
  and MatchStats.astro on every match page, `[fixture].astro` lines 168 and 196) takes the chart
  family's look: its frame moves into MetricComparison.astro, its bar becomes the theme's
  .chart-bar, its groups the family's group heading. `grep -rlnE "cmp-bar|cmp-side|cmp-group"
  site_v2/src` returns nothing.
  data: none; no model, export or committed payload changes, no BigQuery query.
  readers_of_the_classes: site_v2/scripts/check-built-pages.mjs and its test read dp-chart, the
  scatter's team dot and labels, rs-row and rs-val; each renamed class is renamed there.
  design_check: the Team and match pages' rendered and static pins may only move down;
  baseline.json takes CI's measurement. No mock generator is added or edited.
  ci (protected): validate:ui gains the chart-component check, the chart screenshot check and their
  tests after the design-inventory tests, and one artifacts path; same image, same playwright pin,
  nothing installed. fires_on: the existing *ui_paths rules (site_v2/**, .gitlab-ci.yml); the new
  scripts, tests and fixtures are added to *ui_paths. on_failure: the job fails and keeps the new
  screenshots as its artifact. stops_being_enforced_if_wrong: a check that never runs fails open;
  each new test has a RED proof, and the first MR pipeline fails on the missing pins before they
  are committed.
  blast_radius: every Team page's Performance tab and every match page's comparison element;
  validate:ui's run time grows by the screenshot check, about 2 minutes locally (18 screenshots and
  1,224 label measurements).

approved_design:
  - team: #134
  - match: #132

acceptance_criteria:
  - "One theme in code, in one place, that every chart component reads and none overrides: axis lines and ticks; grid; the text of tick labels, axis titles, names and values (from the text styles, #230), in screen pixels at every width; colours, including when a chart may use the accent green; the legend; no tooltips; the phone and desktop sizes, and the width at which every chart takes its narrow form."
  - "The marks for the team and the other teams, the same in every chart, in screen pixels at every width. The theme also says how a chart of two teams side by side, as on the match page, marks each."
  - "The theme is approved by the CPO's merge of this MR, on the built pages."
  - "Scatter plot (`.dp-chart`, Team page, Deserved points), re-derived from the theme."
  - "Strip plot (`.rs-row`, Team page, Compared with the league), re-derived from the theme."
  - "Comparison element (`.cmp`, match page), brought into the theme."
  - "Each chart type is drawn by one shared component; no page draws a chart of that type itself."
  - "A chart component sets no size, colour or font of its own; a check fails one that does."
  - "The site shows no tooltip; a check fails a title attribute or an SVG title in any site file."
  - "The charts on the built pages are pinned as screenshots at phone and desktop widths. A change to any chart's look fails the check until its MR updates the screenshots, so the change shows in the MR and the CPO's merge approves it."
  - "Each chart type's row in `docs/wireframes/block_standard.md` names its selector, its purpose and its component, and no look."

decisions_taken: >
  Approved in chat, 2026-11-02, with the step 3 plan: look values (colours, line widths, dot and bar
  sizes, text sizes) live in system.css and one layout file, site_v2/src/lib/chartTheme.ts, holds
  only the drawings' layout numbers; text sizes are the current ones until #230 sets the scale.
  Approved in chat, 2026-11-03: the comparison element is built in the chart family's look as
  mocked (today's bars, the theme's 5px bar mark, the better side green and the other in ink,
  values 15px bold, names 14px ink centred, the family's group heading with its 26px gap, the team
  names in the legend style); the last-season table is a table, not a chart, and stays as on main;
  the site has no tooltips; green is used only for the better of two values; the gallery page is
  not part of this MR; no checkpoint before the merge, the CPO's merge is the approval. The design
  standard allows no new proposed row, so the chart rows are ruled, citing the chart theme.
  NEW MECHANISM, approved in chat, 2026-11-02 with the plan: (1) the chart theme, chartTheme.ts and
  the Charts section of system.css; (2) the chart-component check,
  scripts/check_chart_components.py, which also fails any tooltip on the site; (3) the chart
  screenshot check, scripts/check_chart_screenshots.py, with its colour and scatter-label steps, in
  validate:ui. RECURRING COST: none; it runs in the existing validate:ui job on the existing
  runner.

decisions_reserved:
  - "none: every decision of this task is approved, see decisions_taken; the theme's approval is the CPO's merge."

done_when:
  - "cd site_v2 && npm test and npm run build pass: node tests, page specs, SEO audit, built-pages check."
  - "python scripts/check_page_css.py, python scripts/check_chart_components.py and python scripts/check_chart_screenshots.py pass, and python -m pytest tests/test_design_inventory.py tests/test_check_chart_components.py tests/test_check_chart_screenshots.py passes, each new test with a RED proof."
  - "The MR pipeline's validate:ui passes with the committed screenshots and baseline."
  - "An MR is open, never merged."

amendments:
  - "2026-11-03: rewritten — authority: CPO rulings approved in chat, 2026-11-03 (the comparison element built in the family's look; the last-season table out; no tooltips; the gallery out of this MR; the CPO's merge is the approval); content: scope loses the gallery generator, its README row and renders, .claude/launch.json, the seven mock generators and TeamLastSeason.astro; acceptance criteria follow the rulings (tooltip and gallery items rewritten, the trend item replaced by the comparison element item, a no-tooltip item added); decisions_reserved closed."
  - "2026-11-03: + .claude/skills/validate-local/SKILL.md — authority: the skill's own rule that a gate added to a CI job is added to its CI mapping table, raised by scope-auditor in review round 1; content: rows for the chart-component check and the chart screenshot check under validate:ui."
