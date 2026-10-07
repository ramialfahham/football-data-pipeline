# Task contract — the match page renders carry every recorded metric decision

objective: >
  Bring the match page renders up to every recorded decision, as the final mockup for the build:
  the Form comparison and Match stats show the same metrics, in the catalogue's order, less the
  Goals group on a played match; the after-penalties render shows every block a played match shows.
  New renders of record; no site change.

refs: >
  #166 (the next match page build) "Form comparison rows" and #175 (the played match page) "Match
  stats", both edited to the one metric list, approved in chat, 2026-10-07; #175 "A played match's
  page shows" (the block list); the step order approved in chat, 2026-10-07.

scope_paths:
  - design-mocks/gen_match_page.py
  - design-mocks/renders/*
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md

decisions_taken: >
  The metric list and the Goals-group exception are the line on #166 and #175, approved in chat,
  2026-10-07. The new values are stand-ins read once from the warehouse (staging team stat lines,
  the player legs, staging line-ups, mart_player_fixture_stats, fct_fixture_event; 537 MB billed
  once, approved in chat, 2026-10-07), the way the existing stand-ins were read. A window value is
  the per-match mean over the window's matches that carry it, and a share is the ratio of the
  window's sums; Bremen's dribbles-completed share follows that rule (49, not 47). A row neither
  side has is left out, as #175 states.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none (the existing design-mock generator). RECURRING
  COST: none.

decisions_reserved:
  - German and Finnish names of the new metrics, and the German name of shots on target: #177, the
    CPO's.
  - Which played matches get a page: #174, the CPO's.

done_when:
  - python design-mocks/render.py gen_match_page.py match-page, future-match-page (MATCH_STATE
    future, future-unmet) and played-match-page (MATCH_STATE played, played-pen) write renders of
    record.
  - The Form comparison of the new next match render and the Match stats of both new played renders
    show the metrics of the approved line, in its order; the played renders less the Goals group.
  - The new after-penalties render shows Goals, Match leaders, Match stats and Line-ups, as the
    full-time render does.
  - pytest tests/test_design_mock_renders.py passes; python scripts/check_page_css.py reports 0
    findings.

amendments: (none)
