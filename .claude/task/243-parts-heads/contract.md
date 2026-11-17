# Task contract — parts library, tab band, chip, group head and chevron heading link

objective: >
  Issue #243, the component-library step, second group: the tab band, the result chip, the
  chevron, the chevron heading link, the group (its container, its head and its date heading)
  each exist once as an Astro component in site_v2/src/components/ui/, and every page that shows
  one places the component instead of its own copy of the markup. A group head builds its own link
  from the entity it names (a competition to the competition page, a nation to the nation page); a
  metric group heading carries the Statistics board it will lead to, and leads nowhere until those
  boards exist. docs/design/components.yml maps each of these parts to its one component file. No
  look change: a refactor of markup ownership, not a redesign.

refs: >
  #243 (component system), note 4249336961 (one form per part) and note 4253999647 (the sitewide
  link rule); #139 and #140 (the Statistics boards). Visual details and engineering calls are the
  coordinating agent's under docs/design/design_standard.md.

scope_paths:
  - .claude/task/243-parts-heads/
  - site_v2/src/components/*/*.astro
  - site_v2/src/pages/[[]lang]/*.astro
  - site_v2/src/pages/[[]lang]/*/*.astro
  - site_v2/src/pages/[[]lang]/*/*/*.astro
  - site_v2/src/pages/[[]lang]/*/*/*/*.astro
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - scripts/check_component_registry.py
  - scripts/parts_page.py
  - tests/test_check_component_registry.py
  - tests/test_parts_page.py
  - tests/test_phone_fixes_231.py
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json

protected_override: >
  docs/design/components.yml: the tab band's, the chip's, the chevron's, the chevron heading
  link's, the group's, the group head's and the date heading's `file` each become one component
  file; the chip, chevron, group head and date heading become components of their own, taking their
  parts from the result row, the competition row, the chevron heading link and the group; the group
  head names the page types it links to (`links-to`); no text style, value, rule or measurement
  changes. The component-library step of #243 (each part built once as a component, every built
  page moved onto it with no change in look), approved in chat, 17 Nov 2026; links per the #243
  link rule (issue #243 note 4253999647); visual details and engineering calls are the coordinating
  agent's under docs/design/design_standard.md, approved in chat, 16 Nov 2026.

impact_map: >
  writers: none; the component and page templates of site_v2 (markup moves into components), the
  component registry, its generated table, its check and the parts page's part kinds. No dbt
  model, export script, data file or stylesheet rule.
  downstream: site_v2/dist only. leaf: consumption layer, no computation added or changed.
  guard: docs/design/components.yml is read by scripts/check_component_registry.py (the registry
  check and the block standard's generated table), scripts/check_design_inventory.py and
  scripts/design_inventory.py (the design check measures each part by its class and selector),
  scripts/parts_page.py and site_v2/scripts/check-term-list.test.mjs (a component's short terms by
  its file). Classes and selectors do not change, so what the design check measures does not
  change; only `file` and the component a part sits under change. A wrong `file` makes the markup
  count rise and the check fail.
  layer_rules: not applicable; no computation.
  deploy_order: none; deploy:site-v2 is manual.
  blast_radius: none on what a visitor sees; every pixel and DOM difference is listed in
  rendered_page_evidence.md with its reason. Registry and design-inventory pins only go down.

acceptance_criteria:
  - Every tab band, result chip, chevron, chevron heading link, group, group head and date heading on the built site is drawn by its one component in site_v2/src/components/ui/, and scripts/check_component_registry.py counts 0 markup outside each of those components, except any listed in acceptance_evidence.md with its reason.
  - A group head links to the competition page or the nation page it names and to no other type of page; the registry's `links-to` says so and the check verifies it; a metric group heading carries its Statistics board and leads nowhere today.
  - The parts page (scripts/parts_page.py against the local dev server), before and after, shows for every part the same number of forms or fewer, and no new form.
  - On Home, Matches, Competitions, Teams, Players, the Bundesliga overview, matches and stats pages, /teams/bayern-munchen/, /teams/germany/, a played match, an upcoming match and a player page, at 375px and 1280px in EN, DE and FI, every tab, the rendered page is pixel-identical before and after, except where two copies of one part differed before and now take one form; every pixel and DOM difference is listed with its reason in rendered_page_evidence.md.
  - Every link leads to the same page as before.
  - No block, block order, wording or value changes on any approved page.

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
  - none: the work is on main alone, after !473 merged

shared_files:
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json

decisions_taken: >
  The library stays in site_v2/src/components/ui/. A part a block shows is placed as its
  component; the block passes data, never a destination. A competition group head without a page
  shows the competition's crest and name without the chevron, the one form of the two the site had
  for it. Decided by the coordinating agent under docs/design/design_standard.md. No new
  mechanism, dependency or recurring cost.

decisions_reserved:
  - none: no look, wording or block changes; any question goes to the coordinating session.

done_when:
  - python scripts/parts_page.py --base http://localhost:4327 before and after; forms per part equal or fewer.
  - The before/after capture of the pages in acceptance_criteria reports pixel-identical screenshots; every difference listed.
  - python scripts/check_component_registry.py passes; baseline pins do not rise.
  - Full pytest and the site's node tests pass.
  - python scripts/ci_local.py --mr --full-scope is green.

amendments: (none)
