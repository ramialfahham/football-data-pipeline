# Task contract — Home rebuilt to its approved design

objective: >
  The built Home has its own match row and its own board, where every other page shares one, and
  it orders its competitions in the page code. Rebuild it to its approved design: Next matches on
  the site's shared match row in the order mart_next_matchday.competition_order serves, Top
  players and Top teams on the Rankings tab's board, the two intros as the block explainer.

refs: >
  #219, the Home build (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/219);
  #127, Home's approved design; the reference render is
  design-mocks/renders/home_2026-09-17_02.html. The warehouse half merged with !330. Plan approved
  in chat, 2026-10-18.

scope_paths:
  - scripts/export_site_data.py
  - tests/test_export_landing.py
  - tests/test_export_site_data.py
  - tests/test_no_decision_history_in_code.py
  - tests/test_no_decision_history_in_docs.py
  - tests/test_sentence_length_in_docs.py
  - site_v2/src/components/home/HeroFixtures.astro
  - site_v2/src/components/home/TopPlayers.astro
  - site_v2/src/components/home/TopTeams.astro
  - site_v2/src/components/home/FixtureRow.astro
  - site_v2/src/components/competition/RankingBoard.astro
  - site_v2/src/lib/types.ts
  - site_v2/src/specs/index.spec.json
  - site_v2/src/data/landing.json
  - site_v2/src/data/fixtures/*.json
  - site_v2/src/data/teams/*.json
  - site_v2/src/data/matches/*.json
  - site_v2/src/data/competitions/BL1/*.json
  - site_v2/src/data/README.md
  - .gitignore
  - docs/wireframes/10_home.md
  - docs/wireframes/block_standard.md
  - docs/site_architecture.md
  - site_v2/src/styles/system.css
  - .pre-commit-config.yaml
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: scripts/export_site_data.py fetch_landing_payload is the only writer of landing.json;
  group_upcoming_fixtures and the two Home board shapers are its helpers and have no other caller
  (git grep). No dbt model changes.
  downstream: landing.json is read only by site_v2/src/pages/[lang]/index.astro, which passes it to
  HeroFixtures, TopPlayers and TopTeams. FixtureRow.astro has one importer, HeroFixtures.
  RankingBoard.astro is also rendered by RankingsBlock.astro (the Rankings tab) and
  MatchLeaders.astro (the match page); only its Props type widens, its markup is unchanged.
  MatchRow.astro is read unchanged. competitionOrder.mjs keeps its other two callers, MatchesDay
  and CompetitionIndexGrid.
  layer_rules: the page renders the order it is served (layering.md, Consumption layer); the export
  selects, groups and shapes served columns: competition_order and fixture_order from the marts,
  the format and per-match flag from the metric catalogue.
  deploy_order: the export reads mart_next_matchday.competition_order, which !330 added and the
  nightly builds; it is in prod before this merges. deploy:site-v2 is manual and runs the export
  fresh.
  blast_radius: the three locale Home pages and landing.json; the committed sample set (landing.json,
  the fixture and team payloads it links, their .gitignore allowlist) rolls forward to the current
  next matchdays and boards.

approved_design:
  - home: #127

acceptance_criteria:
  - "Next matches uses the site's shared match row, the one on the Matches page, the competition's Matchdays tab and the match page: a date heading per day, the kick-off with its zone, the Top match tag on each competition's flagged match, and the whole row one link with the shared hover."
  - "Next matches keeps the competition head (name, chevron, the 2px line), three matches per competition and the rest under \"Show all {n}\"."
  - "The order of the competitions in Next matches is served by the warehouse; the page applies no order of its own."
  - "Top players and Top teams use the competition Rankings tab's board unchanged: a single-value table, the board name in the head row, seven rows on Home."
  - "The intros of Top players and Top teams are the block explainer, 13px grey, like every block intro."
  - "Nothing else on Home changes: the same blocks, boards, leagues and intro wording, in EN, DE and FI."

decisions_taken: >
  Plan approved in chat, 2026-10-18, with these readings of approved rules: the competition head
  carries the competition crest, as the reference render and the block standard's competition group
  head show; board rows show what the Rankings board shows (a player's club under the name, no
  sub-line on a team row), the 2026-10-17 recheck ruling the board unchanged; the rank column is the
  row's place 1-7 in the served board order, as Home shows it today; board names stay plain text
  (#139, #140) and the kick-off stays UTC with its zone label (#146). The doc texts for 10_home.md
  §5 (1) and block_standard.md (the Home Pages row, the Legacy board value rule) are the ones in the
  approved plan. No new mechanism, no recurring cost: the export's landing read gains one read of
  mart_competition_index and drops one of core.dim_team.

decisions_reserved:
  - none: the sample set's size and its refresh were put to the CPO and decided in chat, 2026-10-18 (see amendments).

done_when:
  - npm run build in site_v2 passes (prebuild tests, astro build, audit-seo, check-built-pages).
  - python scripts/check_design_inventory.py --dist site_v2/dist --pages Home passes at 375, 700 and 1010px in EN, DE and FI.
  - The full pytest suite and the offline gates pass.
  - Reviewers per review_routing.json pass.

amendments:
  - 2026-10-18: + site_v2/src/data/matches/*.json, site_v2/src/data/competitions/BL1/*.json — authority: CPO, approved in chat, 2026-10-18; content: the new landing.json links 285 matches, of which ten moved date since the committed sample was exported, so their committed pages sit at the old address. The whole committed sample (the Matches page days, the Bundesliga payload, the fixture payloads their rows link to, the teams) is refreshed from one export, the README's set procedure; Home commits no fixture payload of its own and links a row where the shared sample has its page (the thin set, also approved in chat, 2026-10-18).
  - 2026-10-18: + tests/test_no_decision_history_in_code.py — authority: the test's own rule that its pin moves down when the tree holds fewer flagged lines; content: the pin is lowered to the count the rewritten Home components and tests leave.
  - 2026-10-18: + tests/test_no_decision_history_in_docs.py, tests/test_sentence_length_in_docs.py — authority: the same pins-move-down rule; content: the pinned counts of 10_home.md and site_v2/src/data/README.md are lowered to what the rewritten passages leave.
  - 2026-10-18: + docs/site_architecture.md, site_v2/src/styles/system.css — authority: review round 1 (scope-auditor, bi-analyst-reviewer) and the standing rule that a document is edited in the same MR as what it describes; content: the Landing row of the payload table names the reads the export now makes; the fold's divider sits on whatever first follows its summary, a row or a date heading, so no line falls between a date heading and its first match.
  - 2026-10-18: + .pre-commit-config.yaml — authority: CPO, approved in chat, 2026-10-18; content: the added-large-files check's limit rises from its 500 KB default to 1024 KB, the size the committed team payloads already reach, so the board-linked team payload of 716 KB can be committed.
