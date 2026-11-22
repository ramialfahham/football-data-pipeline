# Task contract — a crest fills its spot, with no tile behind it

objective: >
  A crest, a league logo and a photo spot show the image as large as the spot allows, with no tile,
  box, border or filled background behind it, in light and dark mode. A spot with no image (a
  placeholder) shows its initials in ink on the same bare background. The stylesheet applies the
  rule to every image spot the site has: `.crest`, `.crest.xs` and `.pphoto`. The component
  registry records the rule as text on the crest and photo parts and names #340, which makes the
  mocks adopt the spots and adds the measured row.
refs: "#36 (the comment on how crests and placeholders look), #340 (the mocks adopt the spots; the measured row)"

scope_paths:
  - site_v2/src/styles/system.css
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - tests/fixtures/component_registry/baseline.json
  - .claude/task/36-crest-fill/contract.md
  - .claude/task/36-crest-fill/review.md
  - .claude/task/36-crest-fill/review_input.patch
  - .claude/task/36-crest-fill/acceptance_evidence.md
  - .claude/task/36-crest-fill/rendered_page_evidence.md

protected_override: >
  The coordinating session's message of 2026-11-22 under #36 puts the rule in the component
  registry as text on the crest and photo parts, on the CPO's ruling of 2026-11-22 on how crests
  and placeholders look (approved in chat, 2026-11-22, #36). The MR head declares
  `docs/design/components.yml` as a locked file; the CPO's merge is the approval.

impact_map: >
  writers: none. No table or model is written; the change is a stylesheet and registry text.
  downstream: `docs/design/components.yml` is read by `scripts/check_component_registry.py`, which
  generates `docs/wireframes/block_standard.md` and pins counts in
  `tests/fixtures/component_registry/baseline.json`; by `scripts/design_inventory.py` and
  `scripts/check_design_inventory.py` (the measured check, jobs `validate:ui` and the MR design
  job); and by `scripts/check_page_css.py` (the CSS lint, which guards every class a measured row
  names against mock restyling). The change adds text to existing parts and no measured row, so
  the guarded set is unchanged. `site_v2/src/styles/system.css` is imported by the layout and read
  by every built page. The `.crest`, `.crest.xs` and `.pphoto` classes are rendered only by
  `Crest.astro` and `PlayerRow.astro` (grep over `site_v2/src`: no other component writes them);
  no other stylesheet in `site_v2/src` sets them.
  guard_trace: the registry edit adds a `note` to parts the registry already records as a
  `mock-css` gap; no selector, no measured value and no table row changes. If the text were
  wrong, no check would fail, which is why #340 adds the measured row.
  layer_rules: none apply. `check_layer_contract.py` reads `dbt_project/models/**` only.
  deploy_order: independent.
  blast_radius: every page that shows a crest, a league logo or a placeholder: the crest loses its
  tile (background and 1px border) and the placeholder loses its fill. Page geometry is unchanged:
  the spot keeps its width and height.

depends_on:
  - none: the change reads the stylesheet and the registry; no open MR's code is needed
shared_files:
  - tests/fixtures/component_registry/baseline.json

decisions_taken: >
  The CPO's ruling of 2026-11-22 (approved in chat, 2026-11-22, #36): a crest fills its space with
  no tile, box, border or dark background, and a placeholder has no dark or filled background
  either; the same rule holds for every image spot, mocks included. The coordinating session's
  message of 2026-11-22 decides the placeholder's visual detail to the design standard: the
  initials keep their ink (`ink` on a crest, `muted` on a player spot) and lose the fill, the
  border and the rounded corners. It also decides the route: the rule is registry text now, and
  the measured row lands with the mock MR (#340), because the CSS lint guards every class a
  measured row names and nine mock rules still restyle `.crest` and `.pphoto`.
  No new dependency, no cost.

decisions_reserved:
  - "none: the CPO ruled the rule; the placeholder's ink is the existing ink of each spot, a visual detail the coordinating agent decides against the design standard"

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
  - statistics: #139

acceptance_criteria:
  - "On the built pages, every `.crest`, `.crest.xs` and `.pphoto` has a transparent background colour and a 0px border, in light and dark mode, at 280px and 375px."
  - "A crest image fills its spot: the `img` box equals the spot's box, with the badge contained and not cropped."
  - "A spot with no image shows its initials, with no filled background behind them, in both themes."
  - "The registry records the rule on the crest and photo parts and names #340, which adds the measured row."

done_when:
  - "`python scripts/check_component_registry.py` and `python scripts/check_page_css.py` pass."
  - "`python scripts/ci_local.py --mr` passes."

amendments: (none)
