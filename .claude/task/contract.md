# Task contract — #166 state 2: the future match page

objective: >
  A match further out than the next matchday gets the future match page: breadcrumb, header without the
  teams' table position, Head to head, each team's Next matches, the footer. A next-match page stays as it is.
  The export carries the served is_next_round and each side's next match as the site's match row.

refs: >
  #166 ("state 2, the future match page") as #132 decided it; renders future-match-page_2026-09-28_31 and
  _32. The plan, its readings and the acceptance criteria: approved in chat, 2026-10-09.

scope_paths:
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - site_v2/src/pages/*/*/*/*fixture*.astro
  - site_v2/src/components/fixture/*.astro
  - site_v2/src/styles/system.css
  - site_v2/src/lib/types.ts
  - site_v2/src/specs/competition/matches/fixture.spec.json
  - docs/wireframes/01_fixture_page.md
  - docs/wireframes/block_standard.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md

impact_map: >
  writers: scripts/export_site_data.py writes site_v2/src/data/fixtures/{fixture_id}.json. The fixture
    payload gains is_next_round (mart_competition_fixtures); each side's next_match takes the match-row
    shape _competition_fixture already gives the competition and match-day payloads, from the same mart.
    No dbt model changes.
  downstream: `grep -rn "data/fixtures" site_v2/src site_v2/scripts site_v2/integrations` (tests
    excluded) returns one reader, `pages/[lang]/[competition]/[matches]/[fixture].astro:33`, the
    `import.meta.glob` of the payloads; components/fixture/* take their values from it. `git diff --cached
    -- dbt_project` is empty: no model, seed or test changes, so no dbt lineage moves. A payload without
    is_next_round renders as today's next-match page, so the sample pages keep their text.
    ui/MatchRow.astro and the group head markup are reused, not changed.
  layer_rules: the export selects served columns; which page a fixture gets is the served is_next_round;
    the page formats and routes only.
  deploy_order: the nightly export writes the new fields after merge; the site changes on the next manual
    deploy (deploy:site-v2).
  blast_radius: every match page outside the next matchday; no other page's text.

acceptance_criteria:
  - A fixture whose payload says is_next_round false renders, in EN, DE and FI, the breadcrumb, the header without a standing chip, Head to head, then Next matches, then the footer; no Form comparison, Recent matches or Players to watch.
  - Next matches shows each team's next match under its competition's head, with a date heading per day and the match row with both crests and the kick-off with its zone, every row a link to that match's page; a team whose next match is this one, or who has none, adds no row.
  - A fixture with is_next_round true or missing renders exactly as main's build; every page that is not a match page shows the same text as main's build.
  - At 375, 700 and 1010px no horizontal scroll, and check_design_inventory.py passes.
  - One real future fixture's payload, exported for this check and never committed, renders every block above in EN, DE and FI.

decisions_taken: >
  The plan, the readings and the acceptance criteria: approved in chat, 2026-10-09. Readings: "drawn as
  the approved Home's Next matches" is the ruled elements that render draws (the competition group head,
  a date heading per day, the match row), as the Matches page draws them; a missing is_next_round renders
  as the next-match page; no new strings.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none. RECURRING COST: the export's fixture and next-match queries
  read more served columns of mart_competition_fixtures, dry-run measured and put to the CPO.

decisions_reserved:
  - Which future match pages search engines index: the go-live decision.
  - Home's Next matches block: Home's design review.

done_when:
  - check_copy_gate.py, pytest tests/, npm test, npm run build (audit-seo, check-built-pages),
    check_page_css.py and check_design_inventory.py pass.
  - The acceptance criteria are shown in .claude/task/acceptance_evidence.md from the built pages.

amendments:
  - block_standard.md's Match page entry expects only the parts both match-page states show (Block heading, Match header competition head, Navigation link, the search controls); Result row, Player row and the Next matches rows stay measured against their rules wherever they appear: approved in chat, 2026-10-09.
