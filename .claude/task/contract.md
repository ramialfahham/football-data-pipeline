# Task contract — #41: the Top teams block, the home page's last module

objective: >
  Build the Home page's Top teams block — the third and final module of the composition
  (next matches, Top players, Top teams). Four boards, one metric each, top 7, one team per league
  across the `elite` pool, board names from the metric catalogue, a board with no data omitted
  entirely. The warehouse half merged as `!167`; this is the consumption half.
refs: >
  GitLab #41. `docs/wireframes/10_home.md` §0 — the CPO's composition and the locked board set
  (goals, shots on goal, passes, duels, all per match, CPO 2026-08-10).
  `.claude/task/escalations.log` 2026-09-09 — Ruling 1 (all ranking and ordering lives in the
  warehouse) and the team tie-break ruling (no sporting criterion; `team_sk`, meaningless).
  `docs/metric_layer.md` — the catalogue is the only source of a metric's label and format.
  Precedent: #40's Top players block, merged `!166`. Warehouse: `!164`, `!165`, `!167`.
  GitLab #114 — a better team tie-break, LOW, deferred.

scope_paths:
  - scripts/export_site_data.py
  - tests/test_export_landing.py
  - site_v2/src/components/home/TopTeams.astro
  - site_v2/src/pages/*/index.astro
  - site_v2/src/specs/index.spec.json
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/types.ts
  - site_v2/src/data/landing.json
  - site_v2/src/data/competitions.json
  - site_v2/src/data/README.md
  - site_v2/src/data/teams/*.json
  - .gitignore
  - site_v2/scripts/check-metric-labels.test.mjs
  - docs/wireframes/metrics_display.md
  - docs/wireframes/10_home.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/escalations.log
  - .claude/active_work.md

impact_map: >
  writers: NO dbt model, seed, macro or test is in scope. `mart_team_leaderboards` is READ and not
    modified; its three serving columns merged in `!167` and are live in prod.

  downstream: this is the LEAF end of the chain — a consumption change with nothing downstream of
    it. The mart's own lineage was evidenced on `!167`
    (`dbt ls --select mart_team_leaderboards+` -> 22 nodes, the model plus 21 tests, ZERO downstream
    models) and this branch does not touch it.

  layer_rules: `check_layer_contract.py` is not engaged — no `dbt_project/models/**` path in scope.
    The CONSUMPTION contract is the one that binds: the export may select, filter, group and rename,
    never derive. Every part of the selection and the order is a served column
    (`is_current_season`, `league_leader_order`, `board_leader_order`), so this file compares
    nothing — the shape #40 MR B took three review rounds to reach, adopted here from the start.

  deploy_order: none owed. `!167` merged and `data:build:main` ran, so the columns are live in prod
    and the export can query them today — verified before writing any code.
    `site_v2/src/data/landing.json` is a COMMITTED build input (`deploy:export` regenerates only
    `--entities teams,fixtures`), so the payload lands in this commit and the site build is
    self-contained.

  blast_radius: NO mart, model or number changes. What changes: (1) `landing.json` gains a
    `top_teams` key; (2) the Home page gains its last block; (3) EVERY ROW LINKS OUT, so 20 team
    payloads and their `.gitignore` allowlist entries are committed; (4) no new ROUTE —
    `[lang]/teams/[team].astro` already exists, unlike #40 which had to build a player stub.
    ⚠ `audit-seo.mjs` CHECK 8 IS NEWLY LIVE ON THIS BRANCH. The block emits 28 new internal hrefs
    per locale, so the dead-link check is engaged and is what proves the 20 committed payloads are
    the right ones. Measured on the build: team pages go 3 -> 60 (20 teams x 3 locales) and the
    audit reports `307 built page(s) checked. OK.`
    ⚠ THE COMPETITION DISPLAY NAME CHANGES ON EVERY SURFACE THAT SHOWS ONE, not only this block.
    `competitions.json` gains the 11 corrected names (`site_v2/src/data/competitions.json`, 0 slug
    changes), and its readers are `TeamHeader.astro`, `[lang]/teams/[team].astro` and
    `[lang]/[competition]/matches/[fixture].astro`. That is not spillover: two of the twenty team
    pages this branch newly builds are BL1 clubs (157 Bayern München, 182 1. FC Union Berlin), so
    the wrong name renders in the header of pages that exist only because of this MR.

    ⛔ THIS PARAGRAPH SAID THE OPPOSITE UNTIL ROUND 2 — "these rows do not link", "check 8 stays
    where it is because this block emits no new internal hrefs" — and `scope-auditor` FAILed it.
    The rows-link correction was made in `decisions_taken` and NOT here, so the one section whose
    whole job is to state the real blast radius carried the pre-correction claim. That is the
    accumulate-instead-of-replace failure the repo has recorded nine times: I swept the section I
    remembered writing and left its contradiction standing two hundred lines up.

acceptance_criteria:
  - Each of the four boards renders at most one row per league_code, and every board that renders
    covers all seven elite leagues; shown from the committed landing.json.
  - The block's intro sentence names exactly the leagues that appear on the boards.
  - Re-running the export twice over unchanged data produces a byte-identical landing.json.
  - Every board title renders a non-empty localised string in de, en and fi in the built HTML.
  # ⭐ THE NEXT TWO WERE ADDED AT ROUND 2, and are a STRENGTHENING rather than a softening: they are
  # what #41 actually requires, and the original list never mentioned either because it was drafted
  # before the design was read. Nothing already listed is weakened or removed.
  # ⚠ A COMMENT, NOT A LIST ITEM. It was written as a bullet and the ACCEPTANCE GATE counted it as
  # an eleventh criterion with no evidence line, blocking the commit — correctly, since a criterion
  # without evidence is an unverified claim. The fix is to stop it claiming to be a criterion, NOT
  # to write a fake evidence line for a note.
  - Every team board title SPELLS THE RATE OUT in each locale — "Goals per match", "Tore pro Spiel",
    "Maalit ottelua kohden" — with no Ø left in any of them, read from the built HTML. A metric ROW
    label elsewhere on the site keeps the sigil, which `metrics_display.md` locks.
  - Every team row LINKS OUT (#41: "That is why the block exists") and every link resolves to a page
    the build emitted, shown by audit-seo's check 8 passing with the team page count risen.
  - The two decimal_1 boards render one decimal place and the two decimal_0 boards render none,
    read from the built HTML, not from the catalogue.
  - At 375px width every board row is at least 44px tall and a board stacks as a whole.
  - astro build completes with audit-seo reporting no issues and no new dead internal link.

decisions_taken: >
  ⭐ THE TOP PLAYERS INTRO CHANGED TOO, AT THE CPO'S INSTRUCTION — "now talk about the top players
  copy as well. we have to change it", then "Approved" on the proposal. Both home blocks now read
  the same shape, and all six strings are his:
      EN  "Current season. The top player / team from each league in the rankings: {leagues}."
      DE  "Aktuelle Saison. Der Top-Spieler / Die Top-Mannschaft jeder Liga in den Ranglisten: …"
      FI  "Tämä kausi. Kunkin sarjan kärkipelaaja / kärkijoukkue ranking-listoilla: …"
  ⚠ THIS IS A SCOPE ADDITION HE ASKED FOR, not a tidy-up I extended from the teams ruling. I had
  explicitly declined to extend it — the previous version of this contract said the players line was
  "his to raise" — and he raised it.
  WHAT "totals" COST AND WHY DROPPING IT IS SAFE: the old players line said "Season totals to date",
  which was accurate (player boards are counts, team boards are rates). The distinction survives in
  the BOARD HEADINGS, which is where #41 already put it — the team headings say "per match", the
  player headings are bare nouns, and #41's own reasoning is that a bare noun reads as a season
  total. Saying it twice bought nothing.

  ⛔ A FUTURE BLOCKER, RAISED BY THE CPO IN THE SAME BREATH AND RECORDED SO IT IS NOT REDISCOVERED:
  *"If we ever include women's football teams we have to change it properly (at least in German)."*
  He is right, and the scope is narrower than "German": it is ONE word.
    · DE `Der Top-Spieler` is grammatically masculine and would be wrong for a women's competition
      (`Die Top-Spielerin`), and a mixed set has no correct singular in this construction.
    · DE `Die Top-Mannschaft` is NOT affected — `Mannschaft` is the standard German word for a
      women's team too (`Frauen-Nationalmannschaft`), whatever its etymology.
    · EN `player` and FI `kärkipelaaja` are unaffected: Finnish has no grammatical gender.
  So onboarding a women's competition is blocked on the DE players string alone. Not fixed here —
  no women's competition is in `docs/competition_registry.yml`, and inventing a form for a case that
  does not exist would be authoring copy he has not been asked to rule on.

  ⛔ I BUILT THIS BLOCK WITHOUT READING ITS DESIGN, AND THE FIRST VERSION WAS WRONG IN THREE PLACES.
  `design-mocks/README.md` names **GitLab #41** as the design authority for Top teams; I worked from
  `10_home.md` §0's composition and the mart instead, and discovered #41 only when the CPO said "we
  have a mockup". What that cost, all three already answered in the issue:
    · ROWS LINK. #41: *"Every row links out. That is why the block exists."* I had shipped them
      unlinked and labelled it my own call — a decision the design had already taken. Corrected: the
      rows are anchors, and the 20 team payloads they link to are committed, which is the procedure
      `site_v2/src/data/README.md` already sets out ("the committed sample is a SET"). The fixture
      rows work the same way. The CPO's "deliberately thin" ruling was about the FIXTURE set.
    · THE BOARD TITLE SPELLS THE RATE OUT. #41 rules `Ø Goals` renders as `Goals per match`, per
      locale, derived from the localised label: the sigil reads badly as a heading, and a bare noun
      reads as a season total. I was rendering the raw catalogue label.
    · THE INTRO COPY WAS ALREADY DRAFTED in `10_home.md`, and I wrote my own — using "leading", the
      exact word the CPO rejected for these blocks on 2026-08-08 ("leader" collides with captaincy
      and translates awkwardly). Replaced with his draft verbatim.

  ⛔ THE EXPORT WAS READING THE COMPETITION NAME FROM THE REGISTRY, AND THE REGISTRY IS INPUT.
  The CPO read `1. Fußball-Bundesliga` in the Top players intro on the rendered page. The rule is
  already settled and written down — "the site consumes from a mart; an entity row carries its NAME
  only" — and the WAREHOUSE half was done: `mart_competition_index.competition_name` has carried the
  standardised names all along. What was never done is the export reading them. `meta` has been
  built from `docs/competition_registry.yml` since 452332a (2026-08-18), so this predates both board
  blocks and the fixtures hero's group headings carried it too.

  SWEPT ACROSS THE WHOLE REGISTRY, NOT THE POOL THAT MADE IT VISIBLE — a two-sided count:
  **37 names identical, 11 DIFFERENT.** BL1 -> `Bundesliga`, BL2 -> `2. Bundesliga`,
  UECL -> `UEFA Conference League`, all seven WCQ* -> `World Cup Qualification <x>`, and
  WC `FIFA World Cup 2026` -> `FIFA World Cup`. That last one is why this is a rule and not a
  preference: a YEAR INSIDE A NAME is a defect, and the registry would have shown
  `FIFA World Cup 2026` for the whole of 2027.
  ⚠ 37 of 48 being identical IS THE ANSWER to "how is that possible" — the wrong source looks right
  until it meets a competition standardisation actually changed, and six of the seven elite leagues
  are in the identical 37.

  ONE HELPER, BOTH CONSUMERS. `_warehouse_competition_meta(client)` holds the rule and both
  `fetch_landing_payload`'s `meta` and `_competitions_index` overlay it. The rule living at two call
  sites is what let one of them drift; a third surface would now inherit it rather than re-derive it.
  The SLUG is still the registry's — an assigned identifier, not a display string.

  ⛔ THE BOARD HEADING USED TO CLASSIFY THE METRIC FROM ITS ID, AND THAT WAS WRONG TWICE.
  `boardTitle()` read `metricId.endsWith("_per_match")` before expanding `Ø Goals` into
  `Goals per match`; the guard existed so a per-90 label would not become "Ø Goals per 90 per
  match". `analytics-engineer-reviewer` FAILed it, and both halves of the FAIL hold:
    · MISPLACED. Deciding what KIND of metric a row is, is a taxonomy judgement, which
      `layering.md` §Consumption layer keeps out of the frontend. Its own test settles it: a second
      frontend reading the same mart would have to re-implement the regex to render the heading.
    · UNSOUND, which is the worse half and is mine, not the reviewer's to have found. An id's
      SPELLING is not a fact about the metric, and this catalogue is the proof — the branch's own
      `decisions_taken` already records that `shots_on_goal_per_match` carries the label key
      `metrics.shots_on_target_per_match.label`, a mismatch `metrics_display.md` says caused a
      defect in #370. I cited that mismatch as a reason to READ the label key, then built a
      different guard on the very naming I had just called unreliable.
  THE CATALOGUE STATES THE DISTINCTION IN DATA: a per-match rate has `denominator_expr = count(*)`,
  a per-90 has `sum(minutes_played)`. So `boardTitle(lang, labelKey)` now formats a served label and
  branches on nothing — the same class as `formatValue` switching on a served `format` — and the
  premise is asserted where the catalogue can be read:
  `test_the_team_board_set_is_all_per_match_rates` fails if any board in `_HOME_TEAM_BOARDS` is not
  a `count(*)` rate. Mutation-proven: swapping `duels_per_match` for `duels_won_pct` turns it RED.

  THE SINGLE SOURCE FOR HOW A METRIC IS DISPLAYED IS `docs/wireframes/metrics_display.md`, LOCKED
  2026-06-11, and it is consulted rather than re-derived: its team table gives the labels
  (`Ø Goals`, `Ø Shots on goal`, `Ø Passes`, `Ø Duels`). #41 is later and narrower — it governs the
  board HEADING only, where the sigil expands. A metric ROW anywhere else keeps the locked label.

  ⚠ THE `per match` WORDING IS NOT NEW COPY. `heroVerdictUnder`/`heroCaption` already ship
  "per match", "pro Spiel" and "ottelua kohden" in the three locales; `perMatch` keys the same
  words so the heading can reuse them. Nothing was authored.

  ⚠ THE LABEL KEY IS READ, NEVER INFERRED. The catalogue's team metric id is
  `shots_on_goal_per_match` while its label key is `metrics.shots_on_target_per_match.label` — a
  legacy name `metrics_display.md` records as having already caused a defect in #370, where the key
  was read as a metric id, judged dangling, and replaced with one the catalogue does not declare.
  This branch reads both from the seed.

  THE FORMAT IS SERVED PER BOARD, because the four boards do NOT share one. `goals_per_match` and
  `shots_on_goal_per_match` are `decimal_1`; `passes_per_match` and `duels_per_match` are
  `decimal_0` — read from `metric_catalogue.csv`. Hardcoding either would render one pair wrong, so
  the export carries the catalogue's `format` and `formatValue` dispatches on it. Same principle as
  the label: the catalogue is the only source, and nothing is hand-typed in the component.

  EVERY PART OF THE SELECTION AND THE ORDER IS A SERVED COLUMN — `is_current_season`,
  `league_leader_order = 1`, `order by board_leader_order`. The export compares nothing and sorts
  nothing. This is the end state #40 reached only after four failed review rounds; adopting it from
  the start is the whole value of having done that work.

  THRESHOLD — NEW MECHANISM: none. One component built from the existing board CSS, one export
  shaper mirroring `shape_home_top_players`, one payload key. No new ROUTE, no new gate, no new
  dependency, no new export entity — `[lang]/teams/[team].astro` already existed, unlike #40 which
  had to build a player stub.

  THRESHOLD — RECURRING COST: one additional BigQuery read in the nightly export, over a VIEW, of
  the same shape as the Top players query measured at 29.8 MB.
  THE SITE BUILD DOES GROW: **team pages 3 -> 60, so +57 pages** (20 linked teams x 3 locales, less
  the 3 already built for team 33), and the audit goes 250 -> 307 built pages checked. That is not
  a new route — it is more entities on an existing one, which is exactly what a programmatic site
  is meant to do — but it is growth, and it is ~1.7 MB of committed payload.
  ⛔ THIS PARAGRAPH CLAIMED "No new pages are built, so the site build does not grow at all", and
  `platform-reviewer` FAILed it: `blast_radius`, two hundred lines up in this same file, already
  said "team pages go 3 -> 60". A document that contradicts itself on build growth understates it
  wherever a reader stops first. The mechanism paragraph above carried the same false "no new page"
  clause and is corrected in the same pass rather than only the sentence that was quoted.
  ⚠ SWEPT, TWO-SIDED, rather than patching the two the reviewer named: every changed file was
  grepped for the pre-correction claims ("do not link", "no slug", "unlinked", "0 anchors", "no new
  page", "does not grow", "250 built", "deliberately thin"). **Three were genuinely stale** — these
  two, plus `shape_home_top_teams`'s own docstring in `scripts/export_site_data.py`, which still
  said "NO SLUG AND NO LINK" seven lines above the code that sets the slug. **About fourteen other
  matches are correct historical narration** — sentences whose whole job is to record that the claim
  USED to be the opposite — and are deliberately left standing.
  ⚠ ONE FALSE CLAIM FOUND AND NOT FIXED, because it is not this branch's: `export_site_data.py:207`
  documents the squad-member shaper as emitting "no slug (the frontend slugifies)", which contradicts
  #852 (slugs are assigned in the warehouse, never derived in a frontend). Pre-existing, untouched
  here, a different surface. Recorded rather than swept in.

decisions_reserved:
  - Whether the `elite` group stays the pool. `competition_group = 'elite'` is a literal in the
    export and deliberately temporary — #101 chooses it per nightly build by weighted random. Its
    own MR; not attempted here, and this block inherits whatever that lands.
  - A meaningful team tie-break — #114, LOW, explicitly deferred by the CPO.
  - WHEN the committed sample set rolls forward. Unchanged from #40: `upcoming` still points at the
    2026-09-01 matchday while the board payloads are current, and rolling the set forward is
    periodic maintenance whose new fixture set is the CPO's to choose.

done_when:
  - python -m pytest tests/test_export_landing.py — all pass, including tests that the shaper
    preserves the served order and caps at 7.
  - The order-preservation test is mutation-tested: putting a sort into the shaper turns it RED.
  - cd site_v2 && npm test && npm run build — prebuild runs check-page-specs.mjs, the build runs
    audit-seo.mjs; the page-count driver must show NO new route.
  - The committed landing.json is produced by the shipped code against prod, and two consecutive
    export runs are byte-identical.
  - Browser pane at 375px and desktop: row height, per-board stacking, value-column alignment, and
    the decimal places actually rendered per board.

amendments:
  - 2026-09-09: + `site_v2/src/data/teams/*.json`, + `.gitignore` — authority: **GitLab #41**, the
    design authority for this block, which states "Every row links out. That is why the block
    exists." Committing the payloads those rows link to is the procedure
    `site_v2/src/data/README.md` already documents for a committed sample that is a SET; the four
    linked fixtures are committed for exactly the same reason. Content: the 20 team payloads the
    boards link to, plus their `.gitignore` allowlist entries. Not a scope widening for convenience
    — without it the rows cannot link, and #41 says they must.
    ⚠ The earlier contract text called "rows do not link" MY decision. It was not mine to take; the
    design had taken it. That paragraph is replaced rather than softened.
  - 2026-09-09: + `site_v2/src/data/competitions.json` — authority: **the CPO, in this session**,
    RECORDED IN `escalations.log` under `2026-09-09 feat/41-top-teams-block` with his words
    verbatim: "We have standardized the names. These standardized names should find their way to
    the frontend."
    ⛔ THAT LOG ENTRY DID NOT EXIST WHEN THIS AMENDMENT WAS FIRST WRITTEN, and `scope-auditor`
    FAILed the branch for it — correctly, and as the FOURTH recorded instance of the same failure:
    I quote a ruling into the contract, which the next task overwrites, and never write it into the
    log, which is the only file a reviewer can verify against. The log entry is the authority; this
    line is a pointer to it. Backed by the settled rule *registry is input, the warehouse displays*,
    so nothing here is a new NAMING decision — the standardised names already exist and are already
    his; what changed is which source the export reads. Content: the 11 corrected
    competition names (0 slug changes), regenerated by the shipped code.
    NOT a widening for tidiness: `TeamHeader.astro` reads this file, and two of the twenty team
    pages this branch builds are BL1 clubs, so without it this MR ships `1. Fußball-Bundesliga` on
    pages it created. Fixing `landing.json` alone would have fixed the instance the CPO happened to
    look at and left the same wrong string on the pages the block links to.
  - 2026-09-10: + `docs/wireframes/10_home.md` — authority: **the CPO, in this session**, recorded
    in `escalations.log` under `2026-09-10 feat/41-top-teams-block`. `bi-analyst-reviewer` FAILed
    the branch because this file marks the Top teams intro "Proposed, NOT yet approved" and the
    branch shipped that draft anyway. He has now ruled on it — rejecting "Season to date" outright
    and giving the second half verbatim in all three locales — so the marker is stale, and leaving
    a "NOT yet approved" flag standing over copy he has since dictated is the
    accumulate-instead-of-replace failure this repo has recorded nine times. Content: replace the
    draft with what he ruled and mark it, exactly as the sibling Top players line already is.
    ⭐ THE WINDOW PHRASE IS NOW APPROVED TOO — "approved", 2026-09-10, on being shown the rendered
    sentence. So all three locales of `homeTopTeamsIntro` are his: the second half dictated by him,
    the window phrase proposed by me at his instruction and confirmed by him. Recorded as RULING 3
    in the same `escalations.log` entry.
    ⛔ IT WAS IN THE BUILD BEFORE HE APPROVED IT, and BOTH `scope-auditor` and `bi-analyst-reviewer`
    FAILed round 2 for exactly that — independently, and correctly. I marked the proposal "shipped
    pending his confirmation" in three artifacts and shipped it anyway, which is the same
    disclosure-is-not-approval defect round 1 FAILed on, one clause later in the same sentence. The
    approval closes the finding but does not vindicate the method: had he named different words,
    unapproved §10 copy would have been in the built HTML for a whole round. An unapproved
    user-visible string belongs in `decisions_reserved` and out of the build, full stop.
  - 2026-09-10: + `docs/wireframes/metrics_display.md` — authority: THAT FILE'S OWN CHARTER, plus
    GitLab #41. `analytics-engineer-reviewer` FAILed the branch a second time for a record gap
    rather than a code defect: this contract names `metrics_display.md` the single source for how a
    metric is displayed, yet #41's board-heading rule lived only in code comments and a tracker
    issue. The file's header says it "records the **display** rulings … until they are codified as
    catalogue columns (GAP-09)", so a display ruling belongs in it by its own terms.
    Content: one entry recording that a board HEADING expands the sigil while a metric ROW keeps it,
    and that the boundary is a per-block property, not a per-metric one.
    ⚠ NOT a change to the LOCKED tables. The team-table and player-row labels are untouched; this
    adds the heading case the locked tables never covered. A locked ruling is not being reopened.
  - 2026-09-09: + `site_v2/scripts/check-metric-labels.test.mjs` — authority: STANDING RULE, not a
    CPO answer. `boardTitle()` is new behaviour implementing #41's expansion rule, and the repo's
    own rule is that a behaviour no test pins is unpinned. This is where metric-label behaviour is
    already tested. Content: that the title expands per LOCALE (deriving from the English label
    would title a Finnish board in English, which #41 warns about by name), and that it expands only
    for a `_per_match` id — the per-90 guard #41 gives as the reason the metric id drives it.
