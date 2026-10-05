# Task contract — delete the escalations log

objective: >
  Delete `.claude/task/escalations.log`: it carries the CPO's chat words in a public repository.

refs: >
  #199 (how-we-work documents carry no decision history).

scope_paths:
  - .claude/task/escalations.log
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - docs/tracker/**

decisions_taken: >
  Approved by the CPO in chat, 2026-10-05: delete the file, one file per MR. Readings, under the
  delegation of 2026-10-02:
  - The other files that point to it keep their pointer until each is cleaned in its own MR.
    Nothing reads its content: scripts/report_process_health.py skips a missing file, and the tests
    that name it build their own copy in a temporary repository.
  - The regenerated review patch is not committed: it would carry the deleted file's every line
    as removed lines and publish it again. The reviewer reads it from the working tree.

  Threshold declarations. NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - None.

done_when:
  - The file is gone; pytest (whole suite), ruff and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
