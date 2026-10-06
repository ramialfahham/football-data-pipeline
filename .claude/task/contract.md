# Task contract — the six remaining core documents state the current state only

objective: >
  Replace six core documents with the text approved in chat, 2026-10-06: current state only,
  every line checked against the code, no history, rules pointed to their owner, and the three
  writing standards of working_agreement.md section 9.

refs: >
  The cleanup of the core documents, approved in chat, 2026-10-06.

scope_paths:
  - docs/working_agreement.md
  - docs/north_star.md
  - docs/site_architecture.md
  - docs/content_architecture.md
  - docs/metrics_context_model.md
  - docs/ui_design_brief.md
  - .cursor/rules/agent-behavior.mdc
  - tests/test_no_decision_history_in_docs.py
  - tests/test_sentence_length_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  The six documents are the approved text, nothing else. Approved with them:
  - working_agreement.md section 10 reads "anything a published page displays" for shipped
    numbers, and the metric catalogue row drops its parenthetical.
  - north_star.md names the shots-from-the-box metric by its catalogue label.
  - Corrections against the code: league_code is the competition discriminator; a missing value
    shows as an en dash; the site is Astro on Firebase.
  Companions that follow from the text:
  - .cursor/rules/agent-behavior.mdc mirrors working_agreement.md section 8, so its line says
    competition discriminator too.
  - The six documents have no history line and no long sentence left, so their rows leave both
    pin tests.

  Threshold declarations. NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - None. The places where code and documents disagree stay as written and go to one GitLab
    issue after the merge.

done_when:
  - Each document equals its approved draft.
  - pytest (whole suite) and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
