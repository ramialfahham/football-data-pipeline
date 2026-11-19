# Task contract — pages hold on narrow screens, in the shared parts

objective: >
  Issue #231: the breaks a fresh phone sweep of today's main finds at 280–1010px in EN, DE and FI
  are fixed in the shared parts and their registry rules, never per page: a team name stays inside
  its space, a result or meeting row takes its two-line form when it does not fit on one, a table
  takes two lines when a row no longer fits on one, the Deserved points head breaks only between
  words, a score never splits, every filter button keeps a 44px tap area. Pages that are correct
  at 1010px and wider stay unchanged.

refs: >
  #231 (fix approved in chat, 2026-10-23; tap areas, day picker and separator notes approved in
  chat, 2026-11-12); #243 (the parts library, docs/design/components.yml); the design standard
  (visual details decided by the coordinator, approved in chat, 2026-11-16). Measured list:
  B1–B8 and D1–D5 of the coordinator's rulings, 2026-11-18.

scope_paths:
  - .claude/task/231-narrow-screens/
  - site_v2/src/lib/fitBlocks.mjs
  - site_v2/src/lib/fitBlocks.test.mjs
  - site_v2/src/lib/wholeWords.mjs
  - site_v2/src/lib/wholeWords.test.mjs
  - site_v2/src/styles/system.css
  - site_v2/src/components/ui/ResultRow.astro
  - site_v2/src/components/competition/DeservedTable.astro
  - site_v2/src/i18n/strings.ts
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - tests/test_phone_built_pages_231.py
  - tests/test_phone_fixes_231.py
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json
  - tests/fixtures/chart_screenshots/*

protected_override: >
  docs/design/components.yml: the Fitted block rule's selector takes the head-to-head list; the Name
  in whole words rule's text states the match header's three name sizes, and the header team link
  is measured to hold its name and chevron (`fits`); the filter button states and measures its 44px
  tap area (`min-box=44px`); the Deserved points table's rule states its narrow head forms (the
  wording approved in chat, 2026-11-19) and holds each head cell to its column (`fits`); the result
  row's and meeting row's rules state their two-line forms; the matchday picker's
  rule states where the Next tag goes; the table's switch states #231's approved text; the header
  names its icon buttons' 34px floor where three 44px buttons do not fit (approved in chat,
  2026-11-18, as the one exception to the 44px tap area); the unit's text names
  scores. No text style, colour, spacing or corner value is added. #231's fix approved in chat,
  2026-10-23; visual details are the coordinator's under docs/design/design_standard.md, approved in
  chat, 2026-11-16.

impact_map: >
  writers: none; site_v2/src only (one shared script, the stylesheet, one row component, the
  no-break pass of the build) and the component registry with its generated table.
  downstream: site_v2/dist only. fitBlocks.mjs runs on every page with a fitted block (header,
  tables, fact rows, match rows with a tag, result lists, filter bars, cards); wholeWords.mjs runs on
  every built page's body text; ResultRow.astro draws every result, meeting and goal row (match,
  Team and Player pages). leaf: consumption layer, no computation, no data change.
  guard: docs/design/components.yml is read by scripts/check_component_registry.py (which also
  writes the element table of docs/wireframes/block_standard.md), scripts/check_design_inventory.py
  and scripts/design_inventory.py (through block_standard.md), scripts/parts_page.py and
  site_v2/scripts/check-term-list.test.mjs. The changed selectors widen what the design check
  measures (`fit-marked`, `whole-words`, `fits`); no measurement kind is added.
  layer_rules: not applicable; no computation.
  deploy_order: none; deploy:site-v2 is manual.
  blast_radius: line breaks and the one-or-two-line form of rows, tables and the match header's
  names below 1010px, and of result and meeting rows and the Deserved points head where they
  break at 1010px today; no text, link, number or block changes.

acceptance_criteria:
  - A team name never splits inside a word and never runs outside its space, on every approved page, at 280–1010px, in EN, DE and FI.
  - A table row that no longer fits on one line takes two lines; nothing is dropped; a row that fits keeps one line.
  - A block of fact rows keeps label and value side by side while its longest row fits on one line; below that, every row puts its value under its label.
  - Both switches are measured per block and language by one shared script; without the script a page shows the narrow form.
  - The site header fits at 280px.
  - At 1010px and wider every page is unchanged, except a row or head that breaks there today.
  - The block standard states the rules, and the design check measures them.
  - A fresh sweep of the committed sample at 280, 320, 375, 768 and 1010px in EN, DE and FI shows 0 breaks of B1, B2, B4, B6, B7 and B8, with the before and after counts per page type and width.

approved_design:
  - home: #127
  - competitions: #128
  - competition: #129
  - matches: #130
  - match: #132
  - teams: #133
  - team: #134
  - players: #135
  - player: #136

depends_on:
  - none: !482 is merged (main a54adfbf)

shared_files:
  - site_v2/src/styles/system.css
  - docs/design/components.yml
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json
  - tests/fixtures/chart_screenshots/*

decisions_taken: >
  The coordinator's rulings of 2026-11-18 on the measured list. B1: the match header's names take a
  smaller set size where the longest word and the chevron do not fit. B2: the fit script measures a
  result row by how it lays out in its one-line form, so the chip's and score's fixed columns and
  the meta's cap count; a row whose unbreakable word runs past its space does not fit either. B6:
  the Deserved points head breaks between words only. B7: the build keeps a score whole like a
  hyphen-joined word. B8: a filter button is at least 44px wide; `.comp-name` drops its
  `min-width: 0`, which does nothing inside a block parent, so the min-width pin does not rise. The
  match header's 15px form carries no fit mark, as the card block's third form does not; the header
  team link's `fits` measure is its design check. D1: a result
  row in its two-line form keeps its edge; its facts wrap whole. D2: the meeting row's narrow form
  is the score, the home name, the away name, one line each, then the meta. D3: the picker's Next
  tag takes its own line under the title where both do not fit, per the Tag rule. D4: a table takes
  its two-line form when a row's name no longer fits on one line. D5: the header's icon buttons keep
  a 44px tap area, narrowing to 34px wide where three 44px buttons do not fit beside the brand
  (approved in chat, 2026-11-18). No new mechanism, dependency or cost: every switch is the existing fitted block.

decisions_reserved:
  - none: the Deserved points table's narrow head wording is settled, approved in chat, 2026-11-19 (EN "Shots on target margin per match" and "Points minus deserved points"; DE head 1 unchanged and "Punkte minus verdiente Punkte"; FI "Vetoero maalia kohti ottelua kohden" and "Pisteet miinus ansaitut pisteet"; "Deserved points" unchanged).
  - Every rule text that changes in docs/design/components.yml, shown to the coordinator before commit.

done_when:
  - node --test site_v2/src/lib/fitBlocks.test.mjs site_v2/src/lib/wholeWords.test.mjs passes.
  - python scripts/check_component_registry.py passes; no pin rises.
  - The sweep of the committed sample (all pages, every tab, 280/320/375/768/1010, EN/DE/FI) shows 0 breaks of B1, B2, B4, B6, B7 and B8; a 1010px before/after compare differs only on rows or heads that break there today.
  - python scripts/ci_local.py --mr is green.

amendments:
  - 2026-11-18: protected_override aligned with the diff (the match header is measured by its team link's `fits`, not by a selector of the Name or Fitted block rule; the filter button's 44px rule added); Masthead.astro dropped from scope_paths, since no edit needs it — authority: review round 1 findings, within the coordinator's rulings of 2026-11-18.
  - 2026-11-18: D5's header icon-button exception recorded with its approval — authority: approved in chat, 2026-11-18.
  - 2026-11-19: ci_local findings, within the rulings already recorded — the filter button's 44px floor sits on the Filter bar's buttons only (`.fbar > .seg:not(.sel) .seg-btn`), because an explicit `min-width` on a button that can shrink overlaps its text on the legacy mock pages (design check: matches hub overlap 0 to 41); its rule is its own registry part (`button-tap`, `.fbar .seg-btn`, `min-box=44px`) and the Filter button part keeps its earlier text; two rule texts (the result row's, the match header names') are split into sentences of at most 25 words (the sentence-length pin); the rendered pins in baseline.json, baseline_quick.json and baseline_quick_fi.json are lowered from the linux runs (Competition overview split, Match page scroll and split), none raised — authority: the coordinator's rulings of 2026-11-18, the repo's pins only fall.
  - 2026-11-19: + site_v2/src/components/competition/DeservedTable.astro, + site_v2/src/i18n/strings.ts — authority: the narrow head wording of the Deserved points table approved in chat, 2026-11-19; content: the two narrow head strings per language in strings.ts, and the head cells of the table carry the full and the narrow form, the fit script choosing per table and language. Where the narrow forms show, a head cell's left padding goes from 8px to 4px (a spacing-set value), so its 54px holds "Deserved" and "Verdiente".
