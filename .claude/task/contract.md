# Task contract — handover: the ingest silent-failure cluster, then cost

> Written on a clean tree before any file was touched. Branch `chore/handover-ingest-and-cost` from
> `main` at `bb61a51`. No protected path in scope, so no `protected_override`. No structural path in
> scope, so no `impact_map`. No `site_v2/src/` path, so no `acceptance_criteria`.

objective: >
  Hand over with no gaps so a fresh chat continues without re-investigation. The CPO's stated order
  is: fix the ingest silent-failure cluster first, then resume cost optimisation.

  This session found that the nightly ingest has been dropping API calls since 2026-07-16 on 10 of 18
  runs, every one reported green, and that an empty response DELETES previously good rows while the
  table row count goes UP. That is filed as #896/#897/#898. The cost work is filed on #547 with the
  corrections that three independent analyses produced, including one proposal of mine that would
  have destroyed live data.

  The detail belongs in the tracker, not here. This rewrite points at it and keeps only what a fresh
  chat cannot derive: what is decided, what is verified versus inferred, and the traps.

refs: >
  #896, #897, #898 (the ingest cluster, all filed this session). #547 (cost programme, with a
  comment carrying the full state). #892, #895 (cost items, both corrected this session).
  #845 + #882 (the CPO's next decision). Bookkeeping only — no decision is taken here.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log

decisions_taken: >
  None. This records state that already exists. Every ruling it references is already in
  `escalations.log` or on a GitHub issue with its authority.

  THRESHOLD DECLARATIONS. NEW MECHANISM: none. RECURRING COST: none — the diff contains no executable
  line, which is the one case where "none" is safe without a figure.

decisions_reserved:
  - none: the handover states what was decided and by whom and decides nothing. Where a question is
    open (#845 with #882, the threshold policy in #898, the pacing fix's protected-path route in
    #897) it is recorded as open rather than resolved.

done_when:
  - `.claude/active_work.md` is under 16,000 CHARACTERS, measured in characters (`wc -c` counts bytes
    and over-reports on this file).
  - It names, for a cold reader: current main, that nothing is in flight, the ingest cluster as the
    next work with its order, and that transfers healing is UNVERIFIED.
  - Every claim that was corrected this session is stated in its corrected form only, with no "this
    used to say" narration, per the standing correction-replaces rule.
  - The commit touches only artifact paths. NOTE: it still requires a scope audit, because
    `contract.md` is never artifact-exempt (F10/#409) — the artifact exemption does not apply.

amendments: (none)
