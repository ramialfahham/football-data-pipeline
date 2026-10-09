# Task contract — #166, part 3 of the page build: the next match page, built to the approved design

objective: >
  The next match page draws render match-page_2026-10-07_75 (Proposed): breadcrumb with its markup,
  header, one form window per side, Recent matches, Players to watch and Head to head in the ruled
  rows, every name from strings.ts, every value served. The export carries each field the design reads
  and decides nothing. block_standard.md and 01_fixture_page.md say what the page now is.

refs: >
  #166 (match page, state 1) and render match-page_2026-10-07_75; #132 (the design review); #129 (row
  links: every row of a block or none). The plan, the new strings in EN/DE/FI, the readings and the
  acceptance criteria: approved in chat, 2026-10-09.

scope_paths:
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - site_v2/src/pages/*/*/*/*fixture*.astro
  - site_v2/src/components/fixture/*.astro
  - site_v2/src/styles/system.css
  - site_v2/src/i18n/strings.ts
  - site_v2/src/i18n/strings.test.mjs
  - site_v2/src/lib/types.ts
  - site_v2/src/lib/format.ts
  - site_v2/src/lib/metricRows.ts
  - docs/content_architecture.md
  - site_v2/src/specs/competition/matches/fixture.spec.json
  - docs/wireframes/block_standard.md
  - docs/wireframes/01_fixture_page.md
  - tests/test_no_decision_history_in_docs.py
  - tests/test_no_decision_history_in_code.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md

impact_map: >
  writers: scripts/export_site_data.py writes site_v2/src/data/fixtures/{fixture_id}.json. The fixture
    payload gains round_order and the team slugs (mart_competition_fixtures), one form block per side
    (the block whose is_form_window is true), and top_players from mart_player_season_record by
    top_player_rank. The competition's name, slug, type and logo come from competitions.json and
    competition_index.json, which the export already writes from mart_competition_index. No dbt model
    changes.
  downstream: the match page is the payload's only reader ([fixture].astro and components/fixture/*,
    imported by no other page). system.css and strings.ts are shared: rules for existing classes used by
    other pages (.rmatch, .res, .crumb, .here) are changed only where the match page's markup needs them,
    and acceptance criterion 8 checks every other page's text against main's build. The committed sample
    payloads keep their shape; the page renders a missing field as absent.
  layer_rules: the export selects and filters served columns; which window a side shows is the served
    is_form_window; the page formats and routes only.
  deploy_order: the nightly export writes the new fields after merge; the site changes on the next
    manual deploy (deploy:site-v2).
  blast_radius: every match page; no other page's text.

acceptance_criteria:
  - Every match page's breadcrumb reads Home › Competitions › {competition} › Matchdays|Rounds › {home} vs {away}; the last item is not a link and has aria-current="page"; every other item is a link exactly when its page is built; the BreadcrumbList JSON-LD lists the same names in the same order.
  - Every match page has one H1 and a kick-off line "Matchday N · date · HH:MM UTC · venue" for a domestic league round with a number, the round name otherwise; no standing chip without a rank.
  - No match page shows the sentence, a window switch, points, Explore chips or the "Sample data" line.
  - Each side's Form comparison is its served form window or absent; W/D/L pills and the H/A letters are in the page's language; no metric name carries Ø or %.
  - Recent matches show up to 5 result rows per side with the competition's name, never its code; Head to head shows the served intro or "No meetings on record." and at most 5 meetings, home side first, date with year, no totals or bar.
  - Players to watch shows up to 5 players per side in served rank order.
  - At 375, 700 and 1010px in EN, DE and FI the match page has no horizontal scroll, the teams stack under 700px, and check_design_inventory.py passes on it.
  - Every page that is not a match page shows the same text as main's build.
  - One real fixture's payload, exported for this check and never committed, renders every block above in EN, DE and FI.

decisions_taken: >
  The plan, the strings (formIntro, formIntroPrev, playersIntro, playersIntroPrev, h2hNone, haHome,
  haAway in EN/DE/FI), the readings and the acceptance criteria: approved in chat, 2026-10-09. Readings:
  a link exists only where its page is built, so Recent matches, Head to head and Players to watch rows
  stay unlinked until their pages ship; "Metric Glossary ›" is left out until the glossary page exists;
  W/D/L letters reuse compColWins/Draws/Losses; competition names as served; a goalkeeper's row shows
  saves without the save percentage, which metrics_display.md shows only with its denominator, and
  no mart serves shots faced for the season record. The two content_architecture.md rows for the
  match preview and the key players: exact text approved in chat, 2026-10-09. The German intros name
  the competition with its article, "im" before a name whose head noun is Cup or Pokal and "in der"
  before every other, the nine "im" competitions listed in strings.ts: approved in chat, 2026-10-09.

  THRESHOLD DECLARATIONS: NEW MECHANISM: the breadcrumb's small scroll script (progressive; the page works
  without it). RECURRING COST: the export reads mart_player_season_record (52.8 MB) in place of
  mart_player_momentum (54.9 MB), dry-run on prod.

decisions_reserved:
  - The site footer, menu marking, links in text site-wide, the team page's rows, Home's intros and the
    Rankings tab order: their own MRs.
  - The played-match page, the player pages and the glossary page: their own issues.

done_when:
  - check_copy_gate.py, pytest tests/, npm test, npm run build (audit-seo, check-built-pages),
    check_page_css.py and check_design_inventory.py pass.
  - The acceptance criteria are shown in .claude/task/acceptance_evidence.md from the built pages.
