# Task contract — #160 part 2: the Matches page and its day pages

objective: >
  Build the Matches page and its day pages to #130's "The approved design": an export entity writing
  one payload per day from mart_match_days, the page composed only of shipped elements (breadcrumb and
  heading, the Competitions page's filter rows, the Matchdays picker as a day switcher, the Schedule
  block with Home's competition heading and fold, THE match row), the menu link, the page specs and
  copy, the three inventory rows, the committed sample refreshed as one set, and the documents.

refs: >
  #160 (the build issue; its What exactly is the requirement); #130 "The approved design" and its
  rulings (the fold); #131 rulings (reach); part 1 merged (mart_match_days); the plan approved in plan
  mode, with the CPO's answers: the committed sample holds every competition; the opening day lives
  only at /matches/.

scope_paths:
  - scripts/export_site_data.py
  - tests/test_export_matches.py
  - scripts/check_design_inventory.py
  - tests/test_address_words.py
  - tests/test_design_inventory.py
  - site_v2/src/pages/[[]lang]/[[]matches]/index.astro
  - site_v2/src/pages/[[]lang]/[[]matches]/[[]day].astro
  - site_v2/src/components/matches/MatchesDay.astro
  - site_v2/src/components/competitions/FilterRows.astro
  - site_v2/src/components/competitions/CompetitionIndexGrid.astro
  - site_v2/src/components/chrome/SiteHeader.astro
  - site_v2/src/lib/addressWords.mjs
  - site_v2/src/lib/addressWords.test.mjs
  - site_v2/src/lib/format.ts
  - site_v2/src/lib/types.ts
  - site_v2/src/i18n/strings.ts
  - site_v2/src/specs/matches/index.spec.json
  - site_v2/src/specs/matches/day.spec.json
  - site_v2/src/specs/page-spec.schema.json
  - site_v2/scripts/check-page-specs.mjs
  - site_v2/scripts/check-page-specs.test.mjs
  - site_v2/scripts/audit-seo.test.mjs
  - site_v2/src/data/matches/*.json
  - site_v2/src/data/fixtures/*.json
  - site_v2/src/data/competitions/BL1/2026.json
  - site_v2/src/data/competitions.json
  - site_v2/src/data/competition_index.json
  - site_v2/src/data/README.md
  - .gitignore
  - docs/wireframes/block_standard.md
  - docs/wireframes/00_overview.md
  - docs/site_architecture.md
  - design-mocks/renders/*
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  writers: no warehouse change. The export gains an entity `matches` that reads mart_match_days,
    mart_competition_fixtures and mart_competition_index (through the existing name, crest and
    region helpers) and the registry slug, and writes matches/{yyyy-mm-dd}.json. The competition
    payload's fixture shaper moves to module level unchanged so both entities share it.
  downstream: the site only. New routes [lang]/[matches]/index.astro and [lang]/[matches]/[day].astro
    (same-shape siblings of [competition] and [teams]/[players] routes, which Astro 5.18.2 resolves
    by trying each; the clash check already refuses a slug equal to `spiele`/`ottelut`/`matches`);
    SiteHeader's Matches item becomes a link; CompetitionIndexGrid's filter rows move into a shared
    component with unchanged markup. addressWords.mjs: `matches` becomes a top word too, so the
    language links of /de/spiele/ translate (the Python copy in check_design_inventory.py follows).
    deploy:export's entity list (protected .gitlab-ci.yml) is NOT changed: a manual deploy keeps the
    committed matches sample and re-exports teams and fixtures live.
  layer_rules: the export groups by day and competition and orders nothing except by served order
    columns (day_row_order); the site orders a day's competitions by the site's shared order
    (orderUpcomingGroups), as Home does and as #130 names it.
  deploy_order: part 1 is built in prod (the nightly after its merge); the sample is exported after
    that. deploy:site-v2 is manual; the site is unlisted and noindex.
  blast_radius: the committed sample moves to one date: 58 day files, the fixture payloads their
    unplayed rows link to, the Bundesliga payload and its fixtures, competitions.json and
    competition_index.json; landing.json is untouched. The Competitions page renders the same markup
    from the extracted filter component.

acceptance_criteria:
  - The Matches menu item links to the Matches page (`/en/matches/`, `/de/spiele/`, `/fi/ottelut/`), built to the design approved on #130.
  - "Every day in reach has its own page: forward to the end of each competition's next matchday, back to its last matchday of this season; the switcher's arrows step through them and skip days without a match (#131)."
  - Each competition shows its first 3 matches by kick-off and folds the rest under "Show all {n}"; a played match shows its score, an unplayed one its kick-off.
  - The filter rows, the fold and the page heading are in the block standard's inventory and measured on the built page in EN, DE and FI.
  - Every page has its own title and description in all three languages; the Matches page's title carries the search phrase ("Fußball heute", "football today", "jalkapallo tänään"); the wording is on the MR head as copy.
  - A competition heading links to its competition page and a row to its match page.

decisions_taken: >
  The design is the CPO's (#130 "The approved design", the fold ruling; #131 reach) and so are two
  answers in plan mode: the committed sample holds every competition; the opening day lives only at
  /matches/, every other day at /matches/yyyy-mm-dd/. Every element is a shipped one; the three the
  inventory lacks (filter rows, fold, page heading) join it measured from the CSS that ships. The
  crest sits in the competition heading as the rule and #160 say. Day pages carry the site's
  breadcrumb mechanic (Home › Matches › the day). The title and description wording is proposed on
  the MR head for the CPO, as #130 rules. Builder's: the entity name `matches`, the payload shape,
  the component names, the spec entity `matchDay`, `matches` as a top word.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none (an export entity, routes and specs on the existing
  patterns; the spec entity enum gains a value). RECURRING COST: none; the export entity is not in
  any scheduled job.

decisions_reserved:
  - The title and description wording: proposed on the MR head, the CPO's to approve.
  - The venue's local day (#146); the match page (#132); the nightly export (#156).
  - The Home page's missing crest in its competition headings: Home's defect, not touched here.

done_when:
  - npm run build (node tests, check-page-specs, audit-seo, check-built-pages) exits 0 on the
    refreshed committed sample.
  - python -m pytest tests/ -q passes; python scripts/check_design_inventory.py --dist site_v2/dist
    reports 0 failures with the Matches rows measured in EN, DE and FI.
  - dist holds /{en,de,fi}/{matches word}/ as the opening day and one page per other day in reach;
    every arrow resolves; a competition with more than 3 matches shows 3 rows and "Show all {n}".
  - A self-contained snapshot of the built pages (site_v2/dist, the stylesheet inlined) is sent to
    the CPO; the design's render of record stays design-mocks/renders/matches-hub_2026-09-23_02.html.

amendments:
  - done_when's render line: render.py runs mock generators only, so a built page is sent as a
    snapshot of site_v2/dist instead; no scope, criterion or decision changes. Authority: the
    builder's correction of its own done_when (not a CPO-class change; acceptance_criteria
    untouched).
