# Task contract — competition page tab titles within the title limit

objective: >
  Eight competition-page tab titles run past the SEO audit's 660px title limit on long competition
  names, so the site deploy fails audit-seo. Shorten the Rankings title in EN/DE/FI and the
  Matchdays title in DE/FI to the wording the CPO approved; competition names stay.

refs: >
  #129, the competition page's design
  (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/129); the wording is
  recorded there. Approved in chat, 2026-10-17.

scope_paths:
  - site_v2/src/i18n/strings.ts
  - tests/test_sentence_length_in_docs.py
  - tests/test_no_decision_history_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: none; five copy strings in site_v2/src/i18n/strings.ts change.
  downstream: seoCompetitionFixturesTitle is read only by
  site_v2/src/pages/[lang]/[competition]/[matches]/index.astro and seoCompetitionStatsTitle only by
  site_v2/src/pages/[lang]/[competition]/[stats]/index.astro (git grep); each sets that page's
  title, og:title and twitter:title through Layout.astro. No dbt model, export key or other page
  reads them.
  layer_rules: copy lives in strings.ts only (layering.md Consumption layer); check_copy_gate.py
  covers EN/DE/FI parity.
  deploy_order: none; the titles change on the next site build.
  blast_radius: the title of each competition's Matchdays page in DE and FI and of each Rankings
  page in EN, DE and FI; 48 competitions.

approved_design:
  - competition: #129

acceptance_criteria:
  - On every built competition Rankings page the title reads "{competition}: Stats {season}" (EN), "{competition}: Statistiken {season}" (DE), "{competition}: tilastot {season}" (FI).
  - On every built competition Matchdays page the title reads "{competition}: Fixtures and results {season}" (EN, unchanged), "{competition}: Spielplan {season}" (DE), "{competition}: otteluohjelma {season}" (FI).
  - The Overview titles are unchanged.
  - Measured with audit-seo.mjs's titleWidthPx over all 48 competitions in competition_index.json, no competition tab title is over 660px.

decisions_taken: >
  Approved in chat, 2026-10-17: the wording in the acceptance criteria, recorded on #129. Nothing
  else on the page changes.

decisions_reserved:
  - none: the CPO approved the exact wording, and this task writes it unchanged.

done_when:
  - npm run build in site_v2 passes (its prebuild runs the site's tests, then audit-seo and the built-pages check).
  - The full pytest suite passes.
  - Reviewers per review_routing.json pass.

amendments: (none)
