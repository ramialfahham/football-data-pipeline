# Task contract — the match row's tag on narrow screens

objective: >
  A match row's tag (Top match on Home and the competition matchdays, Next on the Team page) no
  longer covers a team name. A tagged row whose names fit keeps the tag before the kick-off; a row
  that does not fit takes its narrow form, the tag on its own line above the home team,
  left-aligned. The row is measured per page and language by the shared fit script.

refs: >
  #231, the rule that a team name never runs outside its space at 280–1010px. The narrow form and
  the plan approved in chat, 2026-11-01.

scope_paths:
  - site_v2/src/styles/system.css
  - site_v2/src/lib/fitBlocks.mjs
  - docs/wireframes/block_standard.md
  - tests/fixtures/design_inventory/green.html
  - tests/test_no_decision_history_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  Consumption only; no dbt model, no export, no data file changes. The tag is drawn by
  site_v2/src/components/ui/MatchRow.astro, which only three callers give a tag: Home's
  HeroFixtures.astro (topMatch), the competition page's MatchdaySchedule.astro (topMatch) and the
  Team page's TeamFixtureGroup.astro (nextMatch); NextMatches.astro and MatchesDay.astro draw rows
  without one. The `.fxrow .topmatch` rules are read only by those rows. fitBlocks.mjs is loaded
  once by Layout.astro; the new block kind touches only `.fxrow` elements holding a `.topmatch`.
  blast_radius: the tagged match rows on Home, the competition matchdays and the Team pages, in
  all three locales. No served number changes.

approved_design:
  - home: #127
  - competition: #129
  - team: #134

acceptance_criteria:
  - "On every built page whose match rows carry a Top match or Next tag (Home, competition matchdays, Team pages), at 280, 360, 560, 768 and 1010px in EN, DE and FI, no tag overlaps a team name or the kick-off, and no tagged row's names run past their column; measured over the built site."
  - "A tagged row whose names fit keeps the tag before the kick-off on the same line; a row that does not fit shows the tag on its own line above the home team, left-aligned, with names and kick-off below; at 1010px every tagged row has the wide form, and every visible tagged row carries fit-one or fit-two."
  - "block_standard.md's Tag row adds 'Narrow, a row's tag takes its own line above the home team, left-aligned' and the narrow-screen fix as a source; its Fitted block row adds `.fxrow:has(.topmatch)`; check_design_inventory.py --no-mocks passes at its default widths and at 280, 360, 560, 768 and 1010px."

decisions_taken: >
  Approved in chat, 2026-11-01: the narrow form (the tag on its own line above the home team,
  left-aligned), the plan, the acceptance criteria and the two block standard texts. No new
  mechanism: the tagged row joins the one shared fit script that #231 set for every narrow form,
  measured like the header row (the names' column holds its content). Without the script the row
  shows the narrow form, as #231 rules for every fitted block. No recurring cost.

decisions_reserved:
  - "none: every decision of this task is approved, see decisions_taken"

done_when:
  - npm run build in site_v2 (node tests, SEO audit, built-pages check), the full pytest, the offline gates and check_design_inventory.py --no-mocks (default widths, and --viewports 280,360,560,768,1010) pass.
  - The tag and name boxes are measured on every built page with a tagged row, at 280, 360, 560, 768 and 1010px in EN, DE and FI, and none overlap and no names run past their column.

amendments:
  - "Implementation within the approved plan, 2026-11-01: the Fitted block row now names the tagged match row (approved in chat, 2026-11-01), so the design check's green fixture page, which stands for a loaded page as ruled, marks its tagged row fit-one like its other fitted blocks; without the mark its built-page test fails."
  - "Implementation within the approved plan, 2026-11-01: the Tag row's source names the two earlier rulings in words instead of their issue numbers, because the comment history gate refuses an edited documentation line that carries an issue number; the approved sentence and the narrow-screen fix source are added unchanged. block_standard.md then holds one history line fewer, and the decision-history test's pin for it moves down from 48 to 47, as that test requires."
