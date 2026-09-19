# Task contract — #150: the competition page's Matchdays tab

objective: >
  Build the competition page's Matchdays tab as approved on #129 ("The approved design", "Matchdays
  tab", CPO 2026-09-16): the competition-season fixtures mart, the fixtures list on the competition
  payload, the tab page at /{lang}/{competition}/fixtures/ with the picker and the Schedule block, the
  build check that every unplayed match has a page, the nightly read measured, the copy, the documents.

refs: >
  #150 (the build issue; its What exactly is the requirement); #129 "Matchdays tab — approved" and
  "Rules that bind every block on every tab"; docs/wireframes/block_standard.md (Matchday picker,
  Picker title, Picker arrow, Tag, Date heading, Match row *, Block heading gap, Row link);
  design-mocks/renders/competition-matchdays_2026-09-16_01.html (the render of record); the plan
  approved in chat 2026-09-18 (steps 1–5, one step's evidence before the next starts).

scope_paths:
  - dbt_project/models/5_marts/shared/mart_competition_fixtures.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_mart_competition_fixtures_one_row_per_fixture.sql
  - dbt_project/tests/assert_mart_competition_fixtures_next_round_is_one_round.sql
  - dbt_project/tests/assert_mart_competition_fixtures_team_slugs_resolve.sql
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - tests/test_export_landing.py
  - site_v2/src/pages/[[]lang]/[[]competition]/fixtures/index.astro
  - site_v2/src/pages/[[]lang]/[[]competition]/index.astro
  - site_v2/src/specs/competition/fixtures/index.spec.json
  - site_v2/src/specs/competition/index.spec.json
  - site_v2/src/components/competition/CompetitionTabs.astro
  - site_v2/src/components/competition/MatchdaySchedule.astro
  - site_v2/src/components/ui/MatchRow.astro
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/types.ts
  - site_v2/scripts/check-built-pages.mjs
  - site_v2/scripts/check-built-pages.test.mjs
  - site_v2/scripts/audit-seo.mjs
  - site_v2/scripts/audit-seo.test.mjs
  - site_v2/integrations/built-pages.mjs
  - site_v2/astro.config.mjs
  - site_v2/src/data/competitions/BL1/2026.json
  - site_v2/src/data/fixtures/*.json
  - site_v2/src/data/README.md
  - .gitignore
  - docs/wireframes/block_standard.md
  - docs/wireframes/00_overview.md
  - docs/site_architecture.md
  - docs/content_architecture.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: the new mart is a leaf written by dbt only; it reads fct_fixture, dim_team,
    int_legs__team_match (the played definition, by semi-join, not restated) and mart_next_matchday
    (the flag, by left join; mart-to-mart refs are established: mart_team_profile, mart_matchday_insights).
    mart_next_matchday is unchanged.
  downstream: `dbt ls --select mart_competition_fixtures+ --resource-type model` →
    `football_data_pipeline.5_marts.shared.mart_competition_fixtures` alone (no downstream model);
    the full `dbt ls --select mart_competition_fixtures+` lists the model, its three singular tests
    (assert_mart_competition_fixtures_next_round_is_one_round, _one_row_per_fixture,
    _team_slugs_resolve) and its schema tests (accepted_values x3, not_null x15, unique, relationships
    to fct_fixture, competition_fixtures_played_has_a_score, _top_match_is_in_the_next_round,
    _slug_unique_per_competition, _order_unique_per_season). Leaf mart. The export's competition
    payload gains a key; the fixture slug the export writes at every call site is read from the mart.
  layer_rules: marts select and present; league_code on every row; materialisation per layer config,
    nothing per model (check_layer_contract.py).
  deploy_order: additive. A new table and new tests; the nightly builds it after merge; until then the
    committed sample carries its output, produced by the fetch with the compiled SQL inlined against
    prod, read-only (the method !191 used).
  blast_radius: no shipped number changes. Fixture slugs: 37 of 3,344 team names spell differently
    under the ruled slug (measured 2026-09-18 on dim_team); the site is unpublished and noindex.

acceptance_criteria:
  - /en/bundesliga/fixtures/, /de/bundesliga/fixtures/ and /fi/bundesliga/fixtures/ are emitted with the Overview's header and tab bar, no sentence, and the breadcrumb Home › Competitions › Bundesliga (a link to /{lang}/bundesliga/) › the tab label.
  - On the built page exactly one `.md-in` radio is checked and it belongs to the round whose picker carries the Next tag; each picker's arrows are labels for the neighbouring rounds; the first round's previous arrow and the last round's next arrow are `.step.off`.
  - The picker is its own line under the tab bar and the Schedule block's `.sechead` follows it; `check_design_inventory.py --dist site_v2/dist` measures Block heading gap 14px, Matchday picker visible=1 with a 2px line, Picker arrow 34px, Tag, Date heading and Match row kick-off on the built page at 375px and 700px in EN and FI, and passes on Home and the Overview.
  - Every unplayed row is `a.fxrow` with href /{lang}/bundesliga/matches/{fixture_slug}/ and the build emits that page (audit-seo's dead-link check green); played rows follow the step-3 ruling recorded in amendments.
  - A played row shows both scores with the winner's goals `.g.winner`; an unplayed row shows the kick-off in UTC with the zone label `.rowtz`; a `TBD` fixture shows the TBC copy in the time slot.
  - The flagged match of the next round carries the Top match tag before its kick-off; no other row on the page does.
  - check-built-pages fails the build when the count of emitted match pages differs from fixture payloads × locales, or from the export's manifest when one is present; shown red once with a payload removed, then green.
  - Every new label resolves in EN, DE and FI (check_copy_gate.py green) and the copy is listed on the MR for the CPO's ruling.

decisions_taken: >
  The fixture slug (CPO, in chat 2026-09-18, on the two paths put with the measurement): "Warehouse,
  from the team slugs" — slug = kickoff UTC date + home team_slug + "-vs-" + away team_slug, one column
  on the new mart; every fixture slug the export writes reads it, and the Python fixture_slug() goes.
  The round shown in the picker: "Matchday {n}" for a domestic league, n = the trailing integer of the
  provider's round text — the derivation int_legs__team_match already carries as round_order, computed
  in the warehouse (the mart's round_order, the shared doc block's name); every other competition
  kind shows the provider's round text until #148 lands and replaces both. Rounds are ordered by the
  round's first kick-off (the mart's round_sequence), which is what "round order" means before #148.
  The winner's bold score is the larger of the two served goal values, a formatting comparison of
  two displayed numbers, not a result derivation (no W/D/L, no perspective).
  The mock generator design-mocks/gen_competition_matchdays.py is already tracked and in the block
  standard's Pages table (#153 item 5); it renders the approved design from real data and is not
  touched here.
  is_next_round: mart_next_matchday's round, read from that mart (every fixture of the round it
  serves, played or not), never re-derived; a test recomputes the league-wide rule from fct_fixture
  and asserts every mart_next_matchday fixture is flagged. fixture_order is the served reading order
  (rounds in sequence, each by kick-off); the export orders by it and by nothing else. Which round opens: the flagged round, else the last
  round with a played fixture, else the first — a display default over served flags, no value derived.
  The played definition is not restated: a fixture is played when int_legs__team_match holds a leg
  for it. Kick-off in UTC with the label "UTC" until #146; the raw season year in the title until #105.
  THRESHOLD, NEW MECHANISM (for cto-reviewer): a build-done check, check-built-pages, wired like
  audit-seo, that counts match pages against the fixture payloads and the export's manifest and asserts
  the fixtures page's row and radio invariants.
  THRESHOLD, RECURRING COST (for cto-reviewer): the export's reads for every unplayed match are
  measured by dry run and put on the MR with the number before any full-scale run; the deploy export
  is not widened by this task.

decisions_reserved:
  - Copy: "Schedule / Spielplan / Otteluohjelma" and "Top match / Topspiel / Huippuottelu" are #129's; "Next" as a tag (DE "Nächster", not the existing fxNext "Nächstes"), "TBC / Offen / Avoin", the page title and description are drafts, listed on the MR for his ruling.
  - The number: bytes and dollars per night for the full-scale export, before it runs at scale.

done_when:
  - dbt parse clean; SQLFluff clean on every changed model and test; the three singular tests run against prod with the compiled SQL inlined, each RED under a mutation first; data:build:mr green.
  - pytest tests -q green; node --test green in site_v2; check-page-specs OK; check_copy_gate.py green.
  - astro build of the committed sample green through audit-seo and check-built-pages; check_page_css.py and check_design_inventory.py --dist site_v2/dist green on every page; tests/test_design_inventory.py green.
  - Blinded review: analytics-engineer, platform, bi-analyst, cto (the two thresholds), scope-auditor; review.md carries the --staged-hash; the MR head set right after the hook opens it.

amendments:
  - 2026-09-19, review round 1: + docs/wireframes/00_overview.md — authority: CLAUDE.md names it the owner of the design chain's reading order, and #129's ruling of 2026-09-16 (three tabs, Overview · Matchdays · Rankings) plus the built state (#149 Overview, #150 Matchdays) are what the two sibling documents this branch already updated record; its competition-page row still names four tabs and the 2026-09-15 ruling. One row edited, nothing else. Same round: the impact_map's downstream field now carries the pasted `dbt ls` output (scope-auditor); the export orders rows by a served `fixture_order` column instead of a Python comparator, `is_next_round` is read from mart_next_matchday's round instead of re-derived, and `fixture_slug`'s description no longer names a null case (analytics-engineer); the built-pages check matches a row's class in any attribute order and the allowlist range starts at 1575167 exactly (platform). Round 2: the yml block of fixture_order had swallowed is_match_that_matters's tests under a duplicated key (analytics-engineer); the tests are back under their column, fixture_order carries not_null, and the pasted count above is 15 not_null.
  - 2026-09-19, step 4, no path added: the full-scale build (every unplayed match, 15,078 match pages, the deploy job's heap) does not run out of memory and the page-count check passes on it; it fails audit-seo on one pre-existing defect of the match preview page (two meetings of the same clubs share one title, 12 pairings x 3 locales), filed as its own GitLab issue in the Matches milestone the same day. Whether #150 is blocked on it is the CPO's call, put on the MR; nothing of that page is touched here.
  - 2026-09-19, step 3: + site_v2/scripts/audit-seo.mjs, + site_v2/scripts/audit-seo.test.mjs — authority: #129 header ("The header never changes with the tab (crest · name · meta line) … the browser title carries the page's long name for search") against the audit's check 5, which fails two pages of one locale sharing an h1; the audit's own comment says the h1 "renders the entity name", and a tab page renders the same entity. The assertion is NARROWED, not removed: an h1 may repeat only between a page and a page one path segment beneath it (an entity page and its tab); every other repeat still fails, and the test pins both sides.
  - 2026-09-19, step 3: + site_v2/src/pages/[lang]/[competition]/index.astro (the Overview page) — authority: #150's What exactly ("the Overview's header and tab bar (three tabs …; this tab lit"), #129 header ("each a standalone page with an identical header and tab bar"): the shared tab bar links the built tabs both ways, so the Overview passes the competition slug and whether the fixtures page is emitted to the tab component. Two props on one component call; nothing else on the page changes.
  - 2026-09-18, before step 3, no path added: the played rows. #129 says every row is a link (a played match to the match report page #132 designs); the build fails a link to a page it did not emit, and no played match has a page yet. Put to the CPO with three paths; his ruling: "Inert until the report page exists" — played rows show the score and are not links, unplayed rows link to their preview page, the row component carries one switch that flips when the report page lands. The acceptance criterion "played rows follow the step-3 ruling" is this.
  - 2026-09-18, before step 2: + tests/test_export_landing.py — authority: the CPO's slug ruling of the same day ("Warehouse, from the team slugs": every fixture slug the export writes reads the warehouse's, the Python fixture_slug() goes); content: the landing test that pinned the Python spelling of the slug now pins that the served slug is carried through. No other change to the file.
