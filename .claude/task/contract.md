# Task contract — the Matches hub: a proposal the CPO can see

objective: >
  Put a design for the Matches hub (#130, what the Matches menu item lands on) in front of the CPO
  as a render he can open: the page as it would have read on the morning of Saturday 19 September
  2026, built from the real fixtures and kick-off times of that day, composed only of elements the
  site already has. Design only. Nothing under `site_v2/` changes; no mart, export or route.

refs: >
  #130 (the design issue; "nothing gets built until I approve a design"). The plan the CPO approved
  on 2026-09-23 carries the content boundary and the proposed composition this render draws:
  the hub answers "what is on today, everywhere", one calendar day, every competition playing,
  every match; Home's Next matches block and the competition page's Matchdays tab group by round
  and are unchanged; the days behind the hub are #131; the match page is #132.
  #127's approved design records "filter buttons by competition and date ... belong to the
  Matches page". north_star.md: "Open the app, instantly see what's on today across competitions,
  tap a match".
  Measured before planning: 152 matches in 19 competitions on 2026-09-19; 33 in 5 on 2026-09-26
  (an international break), from `marts.mart_competition_fixtures`.

scope_paths:
  - design-mocks/gen_matches_hub.py
  - design-mocks/matches_2026-09-19.json
  - design-mocks/renders/matches-hub_*.html
  - design-mocks/README.md
  - docs/wireframes/block_standard.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  Composition from the approved plan, every part an element the site already has, reused as is:
  the breadcrumb and page heading of the Competitions page; its two filter rows (Clubs / National
  teams, region); the Matchdays tab's picker with a date as its title; one block named with the
  Matchdays tab's existing "Schedule" copy, holding the competition group head (crest, name,
  chevron) and the match row. No new element, no new label, no CSS of the mock's own beyond its
  harness: `system.css` is inlined verbatim and `scripts/check_page_css.py` holds that.

  The data is real: one `bq` pull of `mart_competition_fixtures` for 2026-09-19 joined to
  `mart_competition_index`, committed beside the generator the way the #129 pulls were. The day
  is rendered as it read that morning, so every row shows its kick-off and none its score; the
  kick-offs, teams, competitions and order are the warehouse's. Times in UTC with the label, as
  the built site shows them until #146.

  Two renders, and the difference between them is the reserved question below, drawn so he can
  answer it by looking rather than decided here. The real Saturday has 77 FA Cup qualifying ties
  sorting second, so every competition after them starts about 80 rows down. Render 01 is the
  plan's "every match, no fold"; render 02 is the same page with Home's fold, the element and
  label the site already ships (`.fxmore`, copy `homeShowAll`, three rows then "Show all {n}").
  One generator draws both; `MATCHES_HUB_FOLD=3` selects the fold, and the README names it as the
  variant for this ruling, not a settled feature. Whichever he picks, the other goes.

  The render is named by `design-mocks/render.py` and is a file of record once sent. The mock is
  added to the block standard's Pages table so the measured check covers it like every other mock.

  Threshold declarations: no new mechanism, no recurring cost (one read of about 200 rows).

decisions_reserved:
  - Everything the page shows: each of the four parts (breadcrumb and heading, filters, day line,
    Schedule block) is the CPO's to keep, change or strike, on #130.
  - Which day the hub shows (the build day, else the next day with a match), and that it carries
    no "Today" label.
  - All matches with no fold, versus Home's three and a fold.
  - The order of competitions within the day (the shared key: region rank, then kick-off, then
    code).
  - The day pages behind the hub, how far each way, and past days with scores (#131).
  - The national-team variant (an international weekend), rendered only after the first is ruled.

done_when:
  - "`python design-mocks/render.py gen_matches_hub.py matches-hub` writes `design-mocks/renders/matches-hub_2026-09-23_01.html` (every match), and the same command with `MATCHES_HUB_FOLD=3` writes `_02` (Home's fold)."
  - "`python scripts/check_page_css.py` exits 0 with the new generator listed in the Pages table."
  - "`python scripts/check_design_inventory.py --no-built --pages \"matches hub\"` exits 0 at 375 and 700 px, EN and FI."
  - "`python -m pytest tests/test_design_mock_renders.py tests/test_design_inventory.py -q` passes."
  - "Every row in the render is one of the 152 fixtures of 2026-09-19 in the committed pull, and every competition heading is one of its 19 competitions."
  - "The render is sent to the CPO and the proposal posted on #130."

amendments:
  - 2026-09-23 (before the first commit): the second render and its switch declared in
    decisions_taken and done_when. Authority: the reserved question "All matches with no fold,
    versus Home's three and a fold" is his, and a render of each side is how it is put to him
    (a ruling request names its variants file by file). No path added; both renders were already
    inside `design-mocks/renders/matches-hub_*.html`. Raised by scope-auditor round 1.
