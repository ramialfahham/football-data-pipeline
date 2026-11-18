# Task contract — the match header's top line on status pages

objective: >
  Issue #294, box 5. The match header's top line reads "Match preview" only while the match is
  still to be played: not started, or postponed. A cancelled, abandoned or awaiting-result match
  page has no top line; its status tag stays in the kick-off line. A played match keeps its status
  word.

refs: >
  #294 note 4265824946 (approved in chat, 2026-11-18). The status tag and unplayed_state came with
  !477.

scope_paths:
  - .claude/task/294-header-top-line/
  - site_v2/src/components/fixture/Masthead.astro

impact_map: >
  Leaf, cosmetic: one condition in site_v2/src/components/fixture/Masthead.astro decides whether the
  header's top line (`.mast .status-word`) is drawn. Writers: none; it reads the served
  unplayed_state that the match payload already carries. Downstream: the match page only
  (`grep -rln "Masthead" site_v2/src` → components/fixture/Masthead.astro and the match route
  pages/[lang]/[competition]/[matches]/[fixture].astro). Layer rules: no computation, the served
  key decides. Deploy order: none; deploy:site-v2 is manual. Blast radius: the pages of matches
  whose unplayed_state is cancelled, abandoned or awaiting_result lose the line; the committed
  sample carries no unplayed_state, so every sample page renders as on main.

acceptance_criteria:
  - The match header's top line reads "Match preview" only while the match is still to be played (not started, postponed). A cancelled, abandoned or awaiting-result match page has no top line; its status stands in the kick-off line.

approved_design:
  - match: #132

depends_on:
  - none: builds on !477 and !479, both merged

shared_files:
  - none: no design baseline changes; the committed sample carries no unplayed_state

decisions_taken: >
  The line is left out of the markup, not hidden, so the kick-off line moves up to where the top
  line stood. A played match keeps its status word; the SEO description is unchanged. No new
  mechanism, dependency or recurring cost.

decisions_reserved:
  - none: the rule is #294 note 4265824946; any question goes to the coordinating session.

done_when:
  - The status pages of each kind (cancelled, abandoned, awaiting result, postponed) in EN, DE and FI, at 280 to 768px, measured on the dev server: the top line present only on the postponed page, the tag in the kick-off line, nothing clipped.
  - A not-started and a played match page show the same top line as on main.
  - python scripts/ci_local.py --mr is green, run when the coordinating session sequences it.
