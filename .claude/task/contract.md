# Task contract — README states only what is true today

objective: >
  README.md: every line checked against the code; wrong and stale lines fixed or deleted; copies of
  rules another document owns replaced by a link.

refs: >
  #199 (how-we-work documents), its README findings. The CPO's go, 2026-10-05: "the README MR (branch
  docs/readme-current): one file, every line checked against the code, nothing left stale."

scope_paths:
  - README.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - docs/tracker/**

decisions_taken: >
  Readings, under the delegation of 2026-10-02:
  - Deleted as copies of their owners, with a link left: the guardrail mechanics
    (docs/agent_guardrails.md), the BigQuery layout and the layer contract (layering.md), the
    profile-location reasons (profiles.example.yml).
  - Deleted as stale with nothing to link: the competition list and the layer inventory, the "Data
    Quality" workflow (`dbt build`, `dbt snapshot`; CLAUDE.md forbids the first, no snapshot exists).
  - Highlights that repeat a design decision or the status line are removed.

  Threshold declarations. NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - None: no product, metric, naming or rule change.

done_when:
  - Every line of README.md checked against the code; pytest, ruff and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
