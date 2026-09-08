# Task contract — bring the handover current after !154–!157

objective: >
  Rewrite `.claude/active_work.md` so a cold chat can continue from it. Four MRs merged on
  2026-09-08 (!154, !155, !156, !157), prod was repaired by hand, and the file's stated head
  (`main 3ed9569`, "#40 MR B is the next action") is four merges out of date. It is also at
  **15,706 of its 16,000-character cap**, so this is a rewrite rather than an append — appending
  would silently drop the tail, which is where the traps live.

refs: >
  Bookkeeping, not a code change. No issue. Triggered by the handover write-out gate after !156
  merged, and by the CPO's *"156 merged"*.

scope_paths:
  - .claude/task/contract.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log
  - .claude/active_work.md

impact_map: >
  writers: none. No model, script, seed, test, workflow or site file is touched — this MR changes
  exactly one tracked document plus the task artifacts.
  layer_rules: not applicable; no dbt layer is involved.
  downstream: the file is read by a fresh session at start, and by `handover_in.py`, which enforces
  the 16,000-CHARACTER cap. Measured with Python `len()`, never `wc -c`, which counts BYTES and would
  read ~1,500 short on this file's emoji.
  deploy_order: none.
  blast_radius: one document. The risk is not breakage, it is LOSS — dropping a trap that cost real
  time to learn, or carrying forward a claim that today falsified.

acceptance_criteria:
  - The file is under 16,000 characters, measured with Python `len()` on the final text.
  - Every fact in the header is re-derived rather than carried: `main` SHA, which MRs are merged,
    whether any MR is open. Not one is taken from the previous version.
  - The three claims 2026-09-08 falsified are GONE, not annotated: that `!156` is unmerged, that the
    nightly is failing on a nameless team, and that prod needs an operational fix.
  - Every trap in the previous version is either carried or deliberately dropped, and nothing is
    dropped because it ran out of room before being read.
  - The new incremental-fact trap is recorded with the measurement that makes it checkable, not as a
    slogan — including the `fct_fixture_event` +17 row count, which is the reason NOT to convert
    those facts to tables.

decisions_taken: >
  ⭐ **REWRITE, DO NOT APPEND.** At 15,706 of 16,000 characters the file had ~300 left; `handover_in.py`
  truncates silently at the cap, so an append would have deleted the trap section from the bottom
  while looking like it worked.
  ⭐ **THE NEXT ACTION IS PRESENTED AS TWO CANDIDATES, NOT ONE.** The previous file said "#40 MR B".
  Today's evidence argues for the freshness guard instead — a permanently red nightly hid a second,
  unrelated defect for three nights. Which comes first is a priority call and therefore the CPO's, so
  both are written with the reasoning and a recommendation rather than one being silently promoted.
  ⛔ **THE UNRESOLVED ROUND CAP IS RECORDED AS UNRESOLVED.** !156 merged at round 9 with the question
  put to the CPO and unanswered. Writing "he approved it" would be the fabrication
  `feedback_dont_attribute_repo_practice_to_cpo` exists to stop; writing nothing would leave the next
  session to rediscover it. It is recorded as an open precedent, with his *"you need these
  microdecisions from me???"* alongside it, because the two together are the actual guidance: ask
  about the rule, never about the mechanics.

decisions_reserved: >
  - **The freshness guard** (`assert_fct_fixture_no_stale_live`) is still unfixed. This MR only
    records it; fixing it is its own task.
  - **The order of the two next actions** — the guard versus #40 MR B — is the CPO's and is left open
    in the file rather than decided here.
  - **The parked dbt profile MR** keeps its two open FAILs; nothing here touches them.
