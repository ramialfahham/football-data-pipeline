# Task contract — the Rankings tab's two blocks get their intro line (#166)

objective: >
  The competition page's Rankings tab shows one intro line, the block explainer, under Team
  rankings and under Player rankings, as every board carries one.

refs: >
  #166 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/166), the match page
  build; its line "Intros per content block type", decided on #132. The plan and the wording:
  approved in chat, 2026-10-10.

scope_paths:
  - site_v2/src/i18n/strings.ts
  - site_v2/src/components/competition/RankingsBlock.astro
  - site_v2/src/pages/?lang?/?competition?/?stats?/index.astro
  - site_v2/src/specs/competition/stats/index.spec.json
  - site_v2/src/styles/system.css
  - design-mocks/gen_competition_teams.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: none; no mart, model or export changes. The two strings live in strings.ts.
  downstream: the Rankings tab page ([lang]/[competition]/[stats]/index.astro) is the only page
  that renders RankingsBlock (`grep -rn "RankingsBlock" site_v2/src` lists that page and the
  component). Leaf change: copy, and one CSS rule whose selector pair (`.bsub + .fxgroup`) occurs
  only on the Rankings tab pages in the build.
  layer_rules: the page renders served data and copy; the competition name comes from the payload.
  deploy_order: none; a site build.
  blast_radius: every built Rankings tab page gains two lines of text; no other page changes.

acceptance_criteria:
  - On every built Rankings tab page, a block explainer line sits directly under the Team rankings name and one under the Player rankings name, reading the approved wording for the page's language with its competition named as the match page names it.
  - Every other built page's visible text equals main's.

decisions_taken: >
  The wording, approved in chat, 2026-10-10. Team rankings: "The leading teams {in} this season,
  metric by metric." · "Die besten Mannschaften {in} in dieser Saison, Kennzahl für Kennzahl." ·
  "Parhaat joukkueet {in} tällä kaudella, tilasto kerrallaan." Player rankings: "The leading
  players {in} this season, metric by metric." · "Die besten Spieler {in} in dieser Saison,
  Kennzahl für Kennzahl." · "Parhaat pelaajat {in} tällä kaudella, tilasto kerrallaan." {in} is
  inCompetition(), as on the match page.

  The result-row spacing and the club-in-its-cell lines of #166 are already built
  (site_v2/src/styles/system.css, the two rules after the meeting row); this change builds nothing
  for them.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - Home's intros (#127) and the Metric Glossary links (#168).

done_when:
  - npm test in site_v2 passes; pytest tests/ passes.
  - The criteria are shown in .claude/task/acceptance_evidence.md from the built output.

amendments: >
  After round 1 of the review. With the explainer between the block name and the first metric
  group, the group kept its own 34px top margin. block_standard.md's Block heading gap row (a group
  opening the block carries no space of its own) applies to the group after the explainer too, as
  the match page's `.mp .bsub + .rsplit` rule already does: system.css gains `.bsub + .fxgroup`
  with no top margin, so the explainer's own 8px separates them, as on the Deserved points table.
  The Rankings tab's design mock (design-mocks/gen_competition_teams.py) gains the two approved
  intro lines (EN and FI, Bundesliga), so the mock and the built page agree.

  After round 2: the gap is the CPO's ruling, not a reading. Approved in chat, 2026-10-10: the
  explainer's own 8px is the whole gap to the block's first line, which carries no space of its
  own; the rule, the mock edit and block_standard.md's Block explainer row rest on it.

  After round 3: the approved Form comparison keeps 22px under its intro (render 74), so the row
  names what the 8px holds for. Its Rule column reads, exact text approved in chat, 2026-10-10:
  "the one sentence under a block name, 13px muted; 8px under it to a list, table or group, which
  carries no space of its own". A fourth review round: approved in chat, 2026-10-10.

  After round 4: the approved Head to head list with meetings also keeps its own space under its
  intro, so no general sentence holds. The block_standard.md edit is undone and the file leaves
  the scope; the 8px ruling for the Rankings tab stands as recorded above: approved in chat,
  2026-10-10.
