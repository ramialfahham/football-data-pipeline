# Task contract — the component registry and the Inter font

objective: >
  Issue #243 step 3, first MR: the Inter font, self-hosted, with a check that fails on any
  character the site uses that Inter lacks; docs/design/components.yml in the approved format,
  listing every component the site uses today with its current values, from which the block
  standard's element table is generated; and the six checks of the format note, each counting
  today's gaps and only allowed to fall. Nothing visual changes beyond the font.

refs: >
  #243, the registry format and the font approved in chat, 2026-11-02 (the issue's two notes);
  this MR's plan approved in chat, 2026-11-03. Set values stay today's until #230 decides them.

scope_paths:
  - site_v2/src/assets/fonts/InterVariable.woff2
  - site_v2/src/assets/fonts/OFL.txt
  - site_v2/src/styles/system.css
  - site_v2/src/layouts/Layout.astro
  - site_v2/src/lib/chartMarks.mjs
  - site_v2/src/components/fixture/PlayerRow.astro
  - site_v2/src/components/fixture/RecentMatch.astro
  - site_v2/src/components/fixture/HeadToHead.astro
  - site_v2/scripts/check-font-coverage.mjs
  - site_v2/scripts/check-font-coverage.test.mjs
  - tests/fixtures/font_coverage/*
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - scripts/check_component_registry.py
  - tests/test_check_component_registry.py
  - tests/fixtures/component_registry/*
  - tests/fixtures/design_inventory/baseline.json
  - tests/test_design_inventory.py
  - tests/fixtures/chart_screenshots/*
  - .gitlab-ci.yml
  - .claude/hooks/task_contract_gate.py
  - .claude/review_routing.json
  - .claude/agents/cto-reviewer.md
  - .claude/agents/platform-reviewer.md
  - .claude/task/TEMPLATE.md
  - .claude/skills/validate-local/SKILL.md
  - docs/working_agreement.md
  - docs/north_star.md
  - docs/roles/platform_reliability.md
  - tests/test_governance_doc_parity.py
  - tests/test_governance_hooks.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

protected_override: >
  Approved in chat, 2026-11-03: the CPO approved the #243 step 3 plan for this MR, which adds the
  registry check and the font check to the validate:ui job in .gitlab-ci.yml and makes
  docs/design/components.yml a protected path (task_contract_gate.py, review_routing.json and the
  reviewer briefs that count the guard paths). Approved in chat, 2026-11-04 (#243, with the table):
  tests/test_design_inventory.py's test_no_pin_rises_above_mains allows the nine listed counts that
  rise only because Inter is wider, each only while main still holds its old value.

impact_map: >
  kick-off column: `.fxrow.fit-one:has(.topmatch)` styles only a match row with a Top match tag
  that fitBlocks.mjs marks fit-one (Home, Matches, a competition's Matchdays, the Team page's Next
  matches); its third track becomes `auto`, the track every other match row's kick-off already has.
  narrow rows: `.plrow .pstat` is written by PlayerRow.astro (Players to watch, a match page) and
  MatchLineups.astro (a line-up's minutes, one unit, so unchanged); the goals and assists may wrap
  between their two units. A result row's competition name is written only by RecentMatch.astro
  (a match page's and the Team page's recent matches, the Team page's Matches tab) and HeadToHead.astro (a match
  page's meetings); it loses its never-split `nb`, so it wraps between words while the date stays
  one unit, and the dot after it stays on the competition's line. MatchGoals.astro's markup is
  unchanged, but its timed goal rows are `.resrow.meet`, so the 45% limit below reaches them and a
  goal's minute and assist may wrap between units. Two changes to every result row in system.css:
  on the one-line form the competition and date take at most 45% of the row (`fit-content(45%)`,
  was `auto`), so a long competition no longer covers the name; below the 420px switch the row's
  gaps are `clamp(8px, 3cqw, 20px)`, an existing set value, 8px on the narrowest rows, about 10px at
  375px, at most 12.6px just under the switch, and 11px at and above it as before; no new width.
  pin exception (protected): test_no_pin_rises_above_mains in tests/test_design_inventory.py skips
  nine named rises, each keyed to main's old value. fires_on: validate:ui and test:python, which
  runs the same test on every non-scheduled pipeline. on_failure: any rise outside the nine, or
  one of the nine against a different main value, still fails the test.
  stops_being_enforced_if_wrong: while main holds a listed count's old value, that count may rise
  by any amount and no test caps it; "only because Inter is wider" is checked by no test. The cap
  is review: the commit that lands baseline.json goes back to cto-reviewer and platform-reviewer
  as a delta against the #243 table, all nine must have moved and nothing else may have risen, and
  a figure above that table goes back to the CPO. compare_counts still fails any count off its pin
  in both directions, and a new test proves a rise outside the list and a listed rise on another
  main value both fail. The exception stops matching after the first main pipeline, unless a count
  returns to exactly its old value, which reopens that entry; the next MR removes it.
  scatter label: chartMarks.mjs places the scatter plot's team label against measured text; it
  re-places it once the page's fonts have loaded, as fitBlocks.mjs already re-fits; it runs on
  the Team page's Performance tab only.
  pages: system.css is imported globally by site_v2/src/layouts/Layout.astro, and Layout.astro is
  imported by 11 files under site_v2/src (`grep -rl "layouts/Layout.astro" site_v2/src | wc -l`),
  every page template; so every built page in every language changes font and nothing else. The
  font file is imported by Layout.astro with `?url`, so Vite emits it under _astro/, which
  firebase.json already serves with an immutable cache header; firebase.json is unchanged.
  mocks: the design-mocks generators inline system.css as text; the @font-face's relative URL
  does not resolve from a mock, so mocks keep their fallback font and their counts.
  data: none; no model, export or committed payload changes, no BigQuery query.
  design_check: block_standard.md's element table is regenerated from components.yml; every
  existing row keeps its name and selector, and its rule and measurement except the Match row
  kick-off, Player row and Result row meta rows, which carry the decisions below; new rows are
  ruled with today's measured values, so check_design_inventory.py's counts may only fall.
  baseline.json and the chart screenshot pins take CI's measurement in Inter; a rise is fixed,
  never pinned, except the nine counts of the listed exception.
  ci (protected): validate:ui gains `python scripts/check_component_registry.py`, its pytest and
  `node site_v2/scripts/check-font-coverage.mjs --dist site_v2/dist`; the font check's node test
  runs where every site_v2 node test runs, in build:site-v2's prebuild `npm test`; same images,
  same pins, nothing installed (the font check uses Node's built-in Brotli). fires_on: the
  existing *ui_paths rules; the new scripts, fixtures and docs/design/components.yml join
  *ui_paths. on_failure: the job fails. stops_being_enforced_if_wrong: a check that never runs
  fails open; each new test has a RED proof.
  guards (protected): task_contract_gate.py's PROTECTED_FILES gains docs/design/components.yml;
  its readers are the contract gate itself and stop_gate.py (`_is_protected`), so an edit to the
  registry then needs protected_override and impact_map; review_routing.json routes the path to
  cto-reviewer (opus); the guard-path counts move 13 -> 14 and cto-alone 6 -> 7, pinned by
  tests/test_governance_doc_parity.py across the briefs, the routing _doc, working_agreement.md,
  platform_reliability.md and north_star.md.
  blast_radius: every built page's font; the Player page work (#136, no commits yet) adds its
  components to the protected registry in its own MR; validate:ui gains the static checks (seconds)
  and the measured check's new rows.

approved_design:
  - home: #127
  - competitions: #128
  - competition: #129
  - matches: #130
  - match: #132
  - teams: #133
  - team: #134

acceptance_criteria:
  - "One registry lists every component: its parts, the text style of each part, its narrow form and its unbreakable units. The block standard is generated from it."
  - "Inter, self-hosted under the SIL Open Font License, replaces `system-ui` so every device and CI measure the same letter widths."
  - "A check fails on any character the site uses that Inter lacks."
  - "A page uses only classes a component lists."
  - "Every text matches the set style its part names."
  - "The stylesheet uses only values from the sets."
  - "A component has one wide form and at most one narrow form, at one switch width from the set."
  - "Text breaks only where its part allows; the never-split units are checked at every width in EN, DE and FI."
  - "The file is protected: a new component, part or set value needs the CPO's approval."
  - "Each check counts today's gaps, and each count may only fall; nothing visual changes beyond the font."

decisions_taken: >
  Approved in chat, 2026-11-02 (#243 notes): the registry format and the font. Approved in chat,
  2026-11-03, with this MR's plan: the font file is InterVariable.woff2 from the official Inter 4.1
  release with its licence; the sets hold today's values under neutral value-based names until
  #230; a part may carry `selector`, `rule`, `measured` and `ruled-on` so the generated table keeps
  its columns and every existing row's text, and cross-page rows sit under a top-level `rules:`
  key; checks 1, 2 and 5 run through the generated rows in the existing measured check, checks 3
  and 4 in scripts/check_component_registry.py, check 6 through the protected-path list.
  NEW MECHANISM, approved in chat, 2026-11-03 with the plan: (1) scripts/check_component_registry.py,
  which generates the element table and counts checks 3 and 4; (2)
  site_v2/scripts/check-font-coverage.mjs. No new dependency. RECURRING COST: both checks run in the
  existing validate:ui job on the existing runner; and because docs/design/components.yml becomes a
  guard path, every future MR that edits it routes one cto-reviewer review at opus.

  Approved in chat, 2026-11-04: the font's approval on #243 covers every page, the Player page
  included, and the competition stats page (`[competition]/[stats]/index.astro`) belongs to #129,
  the competition page's design. `approved_design` cannot name the Player page: the gate takes only
  pages in docs/wireframes/approved_designs.yml, which has no Player entry until #136's design is
  approved. This MR changes the Player page's font and nothing else on it.

  Approved in chat, 2026-11-03: the site loads one font file, InterVariable.woff2; italic text is
  slanted by the browser (recorded on #243). The font check counts each missing character per page as
  a pinned gap that may only fall; the garbled player names are their own issue. The core-document
  count edits (working_agreement.md §2 "the other seven"; north_star.md "17 rows: the 14 guard
  paths"). The top-match row's kick-off column, fixed at 41px, sizes to its text as every other
  match row's does, because Inter's "17:30" runs 5px past 41px; the Match row kick-off row asserts
  one-line and fits, and every part that never breaks asserts fits.

  Approved in chat, 2026-11-04 (recorded on #243): Inter's narrow rows — below 375px a player row's
  goals and assists may take two lines, and a result row's opponent and its competition and date
  wrap between words. The scatter label is re-placed once the fonts have loaded. The result row's
  45% limit and its narrow gaps serve that decision and change no approved design; both are listed
  in the MR head.

  Approved in chat, 2026-11-04 (#243, with the table): this MR sets the design check's pins to CI's
  measurement for nine counts that rise only because Inter is wider: Match page scroll, split and
  overflow; Played match page scroll; Team page, Home, Competition overview and Teams page split;
  Competitions index overflow. Every other rise still fails. The exception is removed in the next MR.

decisions_reserved:
  - "The set values (sizes, weights, colours, spacings, switch widths): #230, the CPO's; this MR carries today's values."

done_when:
  - "cd site_v2 && npm test && npm run build pass, and node scripts/check-font-coverage.mjs --dist dist passes on the build."
  - "python scripts/check_component_registry.py passes (table in sync with the registry, counts on their pins), python scripts/check_page_css.py passes, and python -m pytest tests/test_check_component_registry.py tests/test_design_inventory.py tests/test_governance_doc_parity.py tests/test_governance_hooks.py passes, each new test with a RED proof."
  - "The narrow local design check on the Team page and the played match page at 375 and 1010px shows no element miss on the new rows."
  - "On every built match page and Team page in EN, DE and FI, no result row or player row runs past its box at 320, 360, 375, 700 and 1010px, and at 280px no more than on main, measured on one machine against main's build."
  - "The MR pipeline's validate:ui passes with the committed baselines."
  - "An MR is open, never merged."

amendments:
  - 2026-11-04: + site_v2/src/lib/chartMarks.mjs, site_v2/src/components/fixture/PlayerRow.astro, site_v2/src/components/fixture/RecentMatch.astro, site_v2/src/components/fixture/HeadToHead.astro — authority: approved in chat, 2026-11-04 (Inter's narrow rows, recorded on #243; the scatter label's re-placement after the font loads); content: the narrow-row wrapping, the scatter label re-placement, the stated readings of approved_design, the recurring-cost line and the corrected CI line.
  - 2026-11-04: + tests/test_design_inventory.py — authority: approved in chat, 2026-11-04 (the nine-count pin exception, recorded on #243); content: the listed exception in test_no_pin_rises_above_mains, its test, and the result row's 45% limit and narrow gaps in the impact map.
