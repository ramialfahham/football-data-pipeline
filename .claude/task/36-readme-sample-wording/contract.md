# Task contract — the committed-sample README states how a board row links

objective: >
  `site_v2/src/data/README.md` says a board row without a player page "stays plain text". That is
  false for the committed sample: `check-built-pages` fails a board row that is not a link, so the
  sample must hold every board player. The README states that, and recipe step 6 says the
  `--sample` size must cover the board players. Text only; no payload, no code.
refs: "#36 (follow-up of !530)"

scope_paths:
  - site_v2/src/data/README.md
  - .claude/task/36-readme-sample-wording/contract.md
  - .claude/task/36-readme-sample-wording/acceptance_evidence.md
  - .claude/task/36-readme-sample-wording/review.md
  - .claude/task/36-readme-sample-wording/review_input.patch

impact_map: >
  writers: none; the file is hand-written text beside the committed sample.
  downstream: nothing parses the file. `git grep -n "data/README" -- site_v2 scripts tests docs`
  finds a docstring in `scripts/export_site_data.py` that names it, and two doc tests that count
  its sentences (`tests/test_no_decision_history_in_docs.py`, `tests/test_sentence_length_in_docs.py`),
  which the edit must not push over their pinned counts. Leaf, text-only change; no payload,
  script or page output moves.
  blast_radius: none. The sentences it states were checked against `checkRankingsPage` in
  `site_v2/scripts/check-built-pages.mjs` (a board row that is not a link is an issue) and against
  the 72-player run of !530 that left two board rows unlinked.
  deploy_order: nothing to order.

depends_on:
  - none: !530 is merged

shared_files:
  - none: a README under site_v2/src/data; no locked file, baseline or shared fixture changes

decisions_taken: >
  The coordinating session's message of 2026-11-23 asks for this follow-up. The sweep of the repo
  for the old player cap and for plain-text board rows (README, `.gitignore`, docs, scripts, tests,
  deploy) found one false sentence, in `site_v2/src/data/README.md`; the other hits are unrelated
  numbers or a different statement (Home board titles).

decisions_reserved:
  - "none: text that restates how the build already behaves"

approved_design:
  - none: no page output changes

acceptance_criteria:
  - The README no longer says a board row without a player page stays plain text.
  - The README says the sample must hold every board player and that recipe step 6 needs a `--sample` of at least the number of board players.

done_when:
  - "`git grep -n 'stays plain text' -- site_v2/src/data/README.md` finds no match."
  - "`python scripts/ci_local.py --mr` passes."
