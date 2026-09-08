# Task contract — product work is no longer blocked; say so in the handover

objective: >
  `.claude/active_work.md` says *"BLOCKED ON THE CPO: GitLab #110 — one question, and until it is
  answered 463 team-seasons show no statistics. Do not start it."* That is now false. The rule was
  already decided on 2026-06-25 and `!161` states it in `docs/metric_layer.md`; #110 is a narrow
  defect, not a decision. A cold session reading the handover today would stand still waiting for an
  answer that is not owed. Correct it, and record the two new issues.

refs: >
  Bookkeeping. Triggered by the handover write-out gate after `!161` merged. No issue.
  Standing instruction on volume, already logged in `escalations.log`
  (`DO NOT ASK FOR MECHANICS`, and `THIS LOG IS A LEDGER, NOT A LOOKUP`): the top of the file stays
  two sentences and process detail stays out of it.

scope_paths:
  - .claude/task/contract.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log
  - .claude/active_work.md

impact_map: >
  writers: none. One tracked document.
  layer_rules: not applicable.
  downstream: read by a fresh session at start and by `handover_in.py`, which enforces a
  16,000-CHARACTER cap — Python `len()`, never `wc -c`.
  deploy_order: none.
  blast_radius: one document. The risk is a session standing still because the handover says it is
  blocked when it is not.

acceptance_criteria:
  - The "BLOCKED ON THE CPO" line is gone. #40 MR B is stated as the next action with no
    precondition attached to it.
  - #110 is described as what it now is — a narrow defect where the provider labels a forfeit `FT` —
    not a decision anyone is waiting on.
  - **GitLab #111 is recorded**: no test checks a metric's value against the formula the catalogue
    publishes. It did not exist when the handover was last written.
  - A session about to touch metric behaviour is pointed at `docs/metric_layer.md` first, which is
    where the incomplete-data rule now lives.
  - Header facts re-derived: `main` SHA, MR range, whether anything is open.
  - Under 16,000 characters, and no trap dropped for space.

decisions_taken: >
  ⭐ **THE CORRECTION IS THE POINT, NOT THE BOOKKEEPING.** A handover that says "blocked, do not
  start" when nothing is blocked costs a whole session. I wrote that line this morning in good faith
  and `!161` made it false — which is exactly the failure the handover exists to prevent, so it is
  fixed the same day rather than left for the next reader to trip over.
  ⛔ **#110 IS RESTATED, NOT DELETED.** It is still real: forfeits the provider labels `FT` blank 18
  of 19 Süper Lig team-seasons. What changed is its TYPE — a defect to fix, not a question to answer.
  Deleting it would lose a measured finding; leaving it as "blocked on the CPO" would keep the stall.
  ⚠ **NO PROVENANCE IN THE FILE.** No dates, no quotes, no round counts. Settled; not relitigated.

decisions_reserved: >
  - **GitLab #110** — the forfeit-labelled-`FT` defect. Unchanged, unfixed, now correctly typed.
  - **GitLab #111** — no test compares a metric to its catalogue formula. Filed, not built; the
    scope questions are on the issue.
  - **`metrics_context_model.md` §8.1** still restates the player half of the NULL rule and should
    defer to `docs/metric_layer.md`. Outside scope here.
  - **The round-cap precedent** — still unresolved, unchanged by this MR.
