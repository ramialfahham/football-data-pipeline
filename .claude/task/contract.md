# Task contract — #158: page addresses follow the reader's language

objective: >
  Switch every site_v2 page address to the per-language word list in docs/site_architecture.md
  "Address words": one word table the site and Python read, the words as route parameters, every link
  and the hreflang language links mapped through it, the build refusing a competition slug that
  equals a word, and the SEO audit, built-page check, page specs and design check following the table.

refs: >
  #158 (the build issue; its What exactly is the requirement); docs/site_architecture.md "Address
  words" (the ruled word table and its rules 1-8); the plan approved in chat in plan mode.

scope_paths:
  - site_v2/src/i18n/address_words.json
  - site_v2/src/lib/addressWords.mjs
  - site_v2/src/lib/addressWords.test.mjs
  - site_v2/src/lib/href.ts
  - site_v2/src/layouts/Layout.astro
  - site_v2/src/config/indexability.mjs
  - site_v2/src/pages/[[]lang]/competitions/index.astro
  - site_v2/src/pages/[[]lang]/[[]competitions]/index.astro
  - site_v2/src/pages/[[]lang]/teams/[[]team].astro
  - site_v2/src/pages/[[]lang]/[[]teams]/[[]team].astro
  - site_v2/src/pages/[[]lang]/players/[[]player].astro
  - site_v2/src/pages/[[]lang]/[[]players]/[[]player].astro
  - site_v2/src/pages/[[]lang]/[[]competition]/index.astro
  - site_v2/src/pages/[[]lang]/[[]competition]/fixtures/index.astro
  - site_v2/src/pages/[[]lang]/[[]competition]/rankings/index.astro
  - site_v2/src/pages/[[]lang]/[[]competition]/matches/[[]fixture].astro
  - site_v2/src/pages/[[]lang]/[[]competition]/[[]matches]/index.astro
  - site_v2/src/pages/[[]lang]/[[]competition]/[[]matches]/[[]fixture].astro
  - site_v2/src/pages/[[]lang]/[[]competition]/[[]stats]/index.astro
  - site_v2/src/specs/index.spec.json
  - site_v2/src/specs/competitions/index.spec.json
  - site_v2/src/specs/competition/index.spec.json
  - site_v2/src/specs/competition/fixtures/index.spec.json
  - site_v2/src/specs/competition/rankings/index.spec.json
  - site_v2/src/specs/competition/matches/index.spec.json
  - site_v2/src/specs/competition/matches/fixture.spec.json
  - site_v2/src/specs/competition/stats/index.spec.json
  - site_v2/src/specs/teams/team.spec.json
  - site_v2/src/specs/players/player.spec.json
  - site_v2/src/components/chrome/SiteHeader.astro
  - site_v2/src/components/competition/CompetitionTabs.astro
  - site_v2/src/components/competition/DeservedTable.astro
  - site_v2/src/components/competition/RankingBoard.astro
  - site_v2/src/components/competition/StandingsTable.astro
  - site_v2/src/components/home/FixtureRow.astro
  - site_v2/src/components/home/TopPlayers.astro
  - site_v2/src/components/home/TopTeams.astro
  - site_v2/src/components/ui/MatchRow.astro
  - site_v2/scripts/audit-seo.mjs
  - site_v2/scripts/audit-seo.test.mjs
  - site_v2/scripts/check-built-pages.mjs
  - site_v2/scripts/check-built-pages.test.mjs
  - site_v2/scripts/check-page-specs.mjs
  - site_v2/scripts/check-page-specs.test.mjs
  - scripts/check_design_inventory.py
  - scripts/design_inventory.py
  - tests/test_design_inventory.py
  - tests/test_address_words.py
  - tests/test_no_decision_history_in_docs.py
  - docs/site_architecture.md
  - docs/wireframes/block_standard.md
  - docs/wireframes/00_overview.md
  - docs/wireframes/02_team_profile.md
  - design-mocks/README.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  writers: none in the warehouse; no dbt model, export script or registry field changes. The words are
    a new site data file; competition slugs keep coming from docs/competition_registry.yml `slug`
    through src/data/competitions.json and competition_index.json, unchanged.
  downstream: consumption only. Route files emitting a word today (find site_v2/src/pages -type f):
    [lang]/competitions/index.astro, [lang]/teams/[team].astro, [lang]/players/[player].astro,
    [lang]/[competition]/fixtures/index.astro, [lang]/[competition]/rankings/index.astro,
    [lang]/[competition]/matches/[fixture].astro. Link sites spelling a word (grep of
    site_v2/src for (competitions|fixtures|rankings|matches|teams|players)/ in hrefs): SiteHeader:27,
    CompetitionTabs:35,40, DeservedTable:38, RankingBoard:32, StandingsTable:46, FixtureRow:22,
    TopPlayers:54, TopTeams:67, MatchRow:33, and the competitions crumb and link on the three
    competition pages. hreflang: Layout.astro:33 via href.ts alternatePaths, its only caller. Checks
    that assume one path across locales: audit-seo.mjs entityKey/specRouteRegex,
    check-built-pages.mjs MATCH_PAGE/FIXTURES_PAGE/RANKINGS_PAGE, check_design_inventory.py
    resolve_built, and the Pages table URLs in block_standard.md.
  layer_rules: none apply (no dbt model); check_layer_contract.py untouched.
  deploy_order: site-only. deploy:site-v2 is manual; production is unlisted, noindex and shows the
    committed sample, so the old /fixtures/, /rankings/ and English-word addresses vanish without
    redirects; nothing public links them.
  blast_radius: every non-English page address that has a word, and the two competition tabs in all
    three languages. No number, label or rendered block changes.

acceptance_criteria:
  - Every page address uses the word list in `docs/site_architecture.md` "Address words" for its language, for example `/de/bundesliga/spiele/`, `/de/bundesliga/statistiken/`, `/fi/joukkueet/hjk/`, `/de/spieler/jamal-musiala-1090/`.
  - The Matchdays tab lives at the matches word and the Rankings tab at the stats word, in all three languages; their on-screen names do not change.
  - The language links between versions of a page (hreflang) point at that page's real address in each language, and every pair points both ways.
  - The build fails when a competition's address name equals any address word in any language.
  - The site's search checks (the SEO audit, the built-page check, the page specs) match a page across languages through the word list, and pass.

decisions_taken: >
  The word list and its rules are the CPO's, in docs/site_architecture.md "Address words" (rule 4:
  one list, every link and the language switch read it, the switch translates each word; rule 5: a
  word never equals a competition slug, "The switch adds the check that fails the build on one").
  Built here are only the five words pages use today: competitions, matches, teams, players, stats.
  The approved plan fixes the mechanics: the word is a route parameter named after its key (so each
  page keeps its spec file); same-shape routes are used as Astro 5.18.2 falls through between them in
  dev and emits each route's own paths in the build; the language links translate by position (the
  segment after the locale is a top word or a competition slug, the next is a tab word only after a
  slug); the Matchdays and Rankings built-page checks fail on zero pages.

  THRESHOLD DECLARATIONS: NEW MECHANISM: the clash check. It is the check rule 5 says the switch
  adds; it runs in the site build (the competition hub's getStaticPaths, over the 48 slugs in
  competitions.json) and as a pytest over the registry, both inside existing jobs; no new job, no CI
  edit. RECURRING COST: none.

decisions_reserved:
  - Words for pages not designed yet (standings, h2h, the menu pages, statistic names, football,
    prediction): named at each page's review, not here.
  - Whether a match address keeps its kick-off date: a separate decision, not touched.
  - The stale comments in .gitlab-ci.yml (the design check's viewports, the owed follow-up): a
    protected file, out of scope.

done_when:
  - npm run build in site_v2 (after git clean -fX site_v2/src/data) exits 0, including the node tests,
    check-page-specs, audit-seo and check-built-pages.
  - python -m pytest tests/ -q exits 0; python scripts/check_design_inventory.py --dist site_v2/dist
    reports 0 failures with the same render count as main.
  - dist holds /de/bundesliga/spiele/, /de/bundesliga/statistiken/, /fi/joukkueet/<team>/,
    /de/spieler/<player>/, and no */fixtures/ or */rankings/ directory; every hreflang pair in the
    built HTML is reciprocal.
  - Mutations watched red then reverted: a registry slug set to a word fails the pytest and the build;
    a prefix-only alternatePaths fails audit-seo; a word removed from the table fails the built-page
    check.

amendments:
  - + tests/test_no_decision_history_in_docs.py — authority: the CPO in chat, answering "May I add
    tests/test_no_decision_history_in_docs.py to the #158 contract, so I can remove the dates from
    the two stale rows, correct them, and lower their pins (00_overview.md 8->7,
    site_architecture.md 22->21)?" with "Yes, amend". Content: the competition page's row in
    docs/wireframes/00_overview.md and the "Address words" row of the decisions table in
    docs/site_architecture.md still say the tabs sit at /fixtures/ or are not built; the history
    gate refuses rewriting a dated line with its date, so each row is corrected without its date and
    the document's pin moves down by one.
