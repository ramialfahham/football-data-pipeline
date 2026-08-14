# Task contract — handover: #62 step 3 is blocked, and a premise I gave is false

objective: >
  `.claude/active_work.md` tells the next session to start on #62 step 3 and states that
  `dim_league` carries country and flag. Measured 2026-08-14 against prod: `dim_league` has 45 rows
  and **0** with `league_country`, **0** with `country_flag_url`. The columns exist and staging
  extracts them; every value is NULL.

  That premise was mine, it is what the #69 country ruling was decided on, and it blocks step 3 —
  the region sub-line's `single_country: true` branch now has no source in either the seed or the
  warehouse. A fresh session must not start building the mart on it.

  Two further claims are corrected by the same query: all 45 competitions HAVE fixtures, and all 45
  HAVE logos.

refs: >
  GitLab #62 note 2026-08-14 carries the full measurement and is the authority; this only makes the
  handover agree with it. #54's five notes remain the page design. #69 is the country entity.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  1. The handover's country sentence is REPLACED, not annotated. It currently asserts a fact that
     is false; leaving it with a caveat attached would leave a fresh session reading the false half
     first. This is the "a correction replaces everywhere" rule the same file states.

  2. The measurement goes in the handover as NUMBERS (45 rows / 0 country / 0 flag / 45 logo, and
     all 45 with fixtures), not as "verify this". A fresh session must not have to re-run a billed
     query to learn what is already known.

  3. NOT decided here, and deliberately left open: where the 21 single-country competitions get
     their country from. Three candidates are named in the #62 note (fix the ingestion, project the
     registry field after all, or #69's countries seed). Choosing is a design call on evidence that
     does not exist yet — the cheap next step is finding out WHY the column is null.

done_when:
  - The handover names the blocker, the numbers, and the cheap next step, and no longer claims
    `dim_league` supplies country.
  - Under 16,000 CHARACTERS by Python `len()`; NEXT numbering unique; no conflict markers.

amendments: []
