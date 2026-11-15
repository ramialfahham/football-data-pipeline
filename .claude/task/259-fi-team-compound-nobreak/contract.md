# Task contract — Finnish team compound stays on one line

objective: >
  main's validate:ui fails with Player pages split 2 against baseline 0 at 320 and 360px. In the Finnish
  Player intro, a team name of several words is written "Team Name -pelaajaan" with an ordinary space
  before the hyphen, and the word "-pelaajaan," starts with a hyphen, which the build step that keeps
  hyphen-joined words whole does not wrap: the line can break before the hyphen and after it. The
  space becomes a no-break space and the hyphen a non-breaking hyphen, in the helper alone. This
  applies the written narrow-screen rule that text breaks only between words.

refs: >
  #259 (Player club and national tabs), #231 (narrow-screen rules). Main pipeline 3069038911, job
  validate:ui.

scope_paths:
  - site_v2/src/lib/teamCompound.mjs
  - site_v2/src/lib/teamCompound.test.mjs
  - site_v2/src/lib/playerPage.ts
  - site_v2/src/components/player/PlayerComparison.astro
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - .claude/task/259-fi-team-compound-nobreak/contract.md
  - .claude/task/259-fi-team-compound-nobreak/acceptance_evidence.md
  - .claude/task/259-fi-team-compound-nobreak/rendered_page_evidence.md
  - .claude/task/259-fi-team-compound-nobreak/review.md
  - .claude/task/259-fi-team-compound-nobreak/review_input.patch

protected_override: >
  docs/design/components.yml is a protected path. The CPO approved extending the rule Name in whole words to the Finnish Player intro and legend compound in chat on 2026-11-14.

rounds_cap_override: >
  Round 3 findings were a missed selector, fixed; the CPO approved a 4th review round, approved in chat, 2026-11-15.

impact_map: >
  Rule text and selector in docs/design/components.yml and its mirror row in docs/wireframes/block_standard.md gain p.bsub.cmp-p; scripts/check_component_registry.py and scripts/check_page_css.py read that file and are run before commit. Leaf cosmetic change in the consumption layer, no dbt model or raw writer involved. Evidence:
  `grep -rn teamBeforeCompound site_v2 tests` returns exactly three files: the helper in playerPage.ts,
  its one importer PlayerComparison.astro, and tests/test_midfield_roles.py, which only asserts the
  call text in the template, which does not change. Blast radius: the Finnish intro and legend text of
  Player pages, two characters (a space to a no-break space, the hyphen to a non-breaking hyphen) for multi-word team names. No build step, middleware or other page changes.

acceptance_criteria:
  - A unit test shows a multi-word team name before the Finnish compound has a no-break space and a non-breaking hyphen (U+2011) instead of a space and a hyphen, and a one-word name and every other language are unchanged.
  - The wording and the baseline pins are unchanged, and no other page or the build step changes.
  - The local design check of the Finnish Player pages at 280 to 375px reports no word on two lines, recorded in rendered_page_evidence.md.

approved_design:
  - player: #136

decisions_taken: >
  The CPO extended the rule Name in whole words to the Finnish Player intro and legend compound, approved in chat on 2026-11-14. The no-break space and non-breaking hyphen apply it.
  No new mechanism, no recurring cost.

decisions_reserved:
  - none: the wording and layout are unchanged; only where a line may break changes.

done_when:
  - npm test in site_v2 is green, including the new test.
  - Full pytest and the offline gates in FAST_GATES pass.
  - The local design check of the Finnish Player pages at 280 to 375px shows split 0.
  - CI's validate:ui is green on the MR.

amendments: (none)
