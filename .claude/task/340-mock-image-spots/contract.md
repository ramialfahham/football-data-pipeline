# Task contract — the mocks adopt the registry's image spots, and the registry measures them

objective: >
  The design mocks show a crest, a league logo and a photo spot with no tile, box, border or filled
  background, as the site does. No mock CSS rule names `.crest` or `.pphoto`: the mocks' placeholder
  glyph and layout rules move onto the mocks' own class names. The component registry gains the
  measured row `Image spot` on `.crest, .pphoto` (a transparent background and a 0px border on every
  page the design check renders), and the crest, small and photo parts no longer say the rule is
  unmeasured.
refs: "#340, #36 (the comment on how crests and placeholders look)"

scope_paths:
  - design-mocks/rows.py
  - design-mocks/gen_top_players.py
  - design-mocks/gen_top_teams.py
  - design-mocks/gen_block_standard.py
  - design-mocks/gen_competition_hub.py
  - design-mocks/gen_interaction.py
  - design-mocks/gen_matches.py
  - design-mocks/gen_match_page.py
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json
  - tests/test_design_inventory.py
  - .claude/task/340-mock-image-spots/contract.md
  - .claude/task/340-mock-image-spots/review.md
  - .claude/task/340-mock-image-spots/review_input.patch

protected_override: >
  The coordinating session's message of 2026-11-22 under #340 orders the measured row in the
  component registry, on the CPO's ruling of 2026-11-22 on how crests and placeholders look
  (approved in chat, 2026-11-22, #36), with the pins and tests green. The test
  `test_a_class_the_component_registry_lists_is_not_counted_as_unknown` uses `crest` as its example
  of a class no registry row lists; once the registry lists `crest` it must use another gap class,
  so the same message covers that one-word edit in `tests/test_design_inventory.py`. The MR head
  declares `docs/design/components.yml` and `tests/test_design_inventory.py` as locked files; the
  CPO's merge is the approval.

impact_map: >
  writers: none. No table or model is written; the change is mock generators, registry text and
  pinned counts.
  downstream: `docs/design/components.yml` is read by `scripts/check_component_registry.py`, which
  generates `docs/wireframes/block_standard.md` and pins counts in
  `tests/fixtures/component_registry/baseline.json`; by `scripts/design_inventory.py` and
  `scripts/check_design_inventory.py` (the measured check, jobs `validate:ui` and the MR design job,
  against `tests/fixtures/design_inventory/baseline*.json`); and by `scripts/check_page_css.py`
  (the CSS lint, which guards every class a measured row names against mock restyling, over
  `design-mocks/gen_*.py` and the files they import). The mock generators import
  `design-mocks/rows.py`; the mock render checks (`check_mock_css.py`, `check_row_consistency.py`)
  read the generated mock HTML. The published `design-mocks/renders/*.html` are snapshots and are
  not regenerated.
  guard_trace_test: `tests/test_design_inventory.py` runs the design check on a probe page and
  asserts which classes count as unlisted. Its probe class `crest` becomes listed with this change,
  so the probe moves to `xs`, which the registry still records as a gap part. The assertion keeps
  its meaning: a class a registry lists is not counted as unknown, and a class a different registry
  does not list is.
  guard_trace: the new row `Image spot` is measured on every built page and mock the design check
  renders. If the row were wrong it would fail every page that renders a crest or a photo spot; the
  CSS lint then guards `crest` and `pphoto` against any mock rule that names them, so a mock cannot
  bring the tile back. If the row were dropped, nothing would hold the rule.
  layer_rules: none apply. `check_layer_contract.py` reads `dbt_project/models/**` only.
  deploy_order: independent.
  blast_radius: the mock placeholder glyph keeps its size and colour; only its selector changes
  (a class on the glyph, not the registry class). The mock layout rules for the player row and the
  stacked match header keep their effect through structural selectors.

depends_on:
  - none: the merged crest-fill MR is on main; no open MR's code is needed
shared_files:
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json

decisions_taken: >
  The CPO's ruling of 2026-11-22 (approved in chat, 2026-11-22, #36): the rule on how crests and
  placeholders look holds for every image spot, mocks included. The coordinating session's message
  of 2026-11-22 under #340 orders the mocks to adopt the spots and the measured row to follow, with
  the pins and tests green. The placeholder ink is stated per spot in the row's rule: `ink` on a
  crest, `muted` on a player spot. No new dependency, no cost.

decisions_reserved:
  - "none: the CPO ruled the rule; this change makes the mocks and the registry follow it"

approved_design:
  - none: no page output changes; the change touches mocks, the registry and pinned counts only

done_when:
  - "`python scripts/check_component_registry.py`, `python scripts/check_page_css.py` and `python -m pytest tests/test_design_inventory.py -q` pass."
  - "`python scripts/ci_local.py --mr` passes."

amendments: (none)
