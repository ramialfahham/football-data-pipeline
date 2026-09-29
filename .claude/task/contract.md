# Task contract — #132: the match page review renders, states 1 to 3

objective: >
  Put the match page in front of the CPO for the #132 review, one state at a time: the next matchday
  (state 1), a match further out (state 2) and a played match (state 3). A design mock generated from
  the BUILT page where one exists, with a "Built today" / "Proposed" switch, every proposed change
  marked and numbered, each block's data source shown on a toggle, and the approved instance of each
  element beside the block that uses it; filed as renders of record through design-mocks/render.py.
  No site change.

refs: >
  #132 (the review issue: block by block, data sources, links), its decision comments "State 1 — the
  next matchday: decided", "State 2 — the future match page: decided" and "State 3 — the played
  match's page: decided"; the reference mock d70aae67 ("Fixture page — clean design");
  docs/wireframes/01_fixture_page.md; the CPO's go in chat for each state.

scope_paths:
  - design-mocks/gen_match_page.py
  - design-mocks/renders/*
  - design-mocks/README.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

decisions_taken: >
  The renders show the built page unchanged under "Built today" and, under "Proposed", only changes
  made of elements the site already ships or elements the CPO approved in the review, each with its
  approved instance shown beside it. Every decision is the CPO's, made block by block in chat and
  recorded in his words on #132; the renders record them, the build issues filed from them
  (#166, #167, #94, #174 to #181) carry them to the site.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none (a design-mock generator, the established pattern).
  RECURRING COST: none.

decisions_reserved:
  - Which played matches get a page, and its cost: #174, the CPO's.
  - The name of the mart that serves a match as a window of one: the CPO's, at build (#176).
  - The German name of shots on target ("Torschüsse" or "Schüsse aufs Tor"): the CPO's, with #177's
    German names.
  - Player-name links: player pages exist only for players on the rankings boards; whether every
    player gets a page is #169's.

done_when:
  - python design-mocks/render.py gen_match_page.py match-page (and future-match-page,
    played-match-page with MATCH_STATE future, future-unmet, played, played-pen) writes a render of
    record, after npm run build for the states with a built page.
  - python scripts/check_design_inventory.py --no-built --no-mocks --page on each decided render
    reports only the failures #167 changes (the competition group head's left edge) and the prose
    links #166 changes.
  - python scripts/check_page_css.py reports 0 findings; pytest tests/test_design_mock_renders.py
    passes.
  - Each render is sent to the CPO; the decisions are recorded on #132.

amendments:
  - 2026-09-29: + states 2 and 3 (renders future-match-page_*, played-match-page_*; the generator's
    MATCH_STATE future, future-unmet, played and played-pen), inside the existing scope_paths —
    authority: #132 "State 2 — the future match page: decided" (CPO, 2026-09-27); CPO in chat:
    "Continue #132, the match page review, state 3 of 3" and "yes, state 3 decided, post on #132";
    content: objective, refs, decisions_taken, decisions_reserved and done_when cover all three states.
