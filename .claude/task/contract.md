# Task contract — the scale rule: value decides what is built, scale is never the argument

objective: >
  Write into the north star the founding requirement the repo never stated for the site: whether
  something is built is decided by its value to the fan; how many pages, rows or competitions it
  produces is never an argument for or against it; the engineering carries whatever the product
  decides, and a build that cannot is the defect. Point at it from `CLAUDE.md`'s non-negotiable
  list so every session reads it. Raised by the CPO on 2026-09-16 during the Matchdays tab review
  on #129, when the agent argued against a feature from its page count.

refs: >
  #129 (the note of 2026-09-16 on what a Matchdays row leads to); `docs/north_star.md` "Scale
  ambition"; `CLAUDE.md` "Scalability rules" (the warehouse half of the same requirement, already
  written and machine-checked).

scope_paths:
  - docs/north_star.md
  - CLAUDE.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  The wording is the CPO's, put to him in chat on 2026-09-16 and confirmed ("good"): "Whether
  something is built is decided by its value to the fan. How many pages, rows or competitions it
  produces is never an argument for or against it; the engineering is there to carry whatever the
  product decides, and a build that cannot is the defect." Home for it: the north star's "Scale
  ambition", the section that already says "built to be big". `CLAUDE.md` gets one pointer line
  in the non-negotiable list, no second copy of the rule.

decisions_reserved:
  - Filing the site build's out-of-memory at full scale as a defect against this requirement, and
    the page-count check on the build: both go on the Matchdays build issue when it is filed, not
    in this MR.

done_when:
  - The north star carries the paragraph; `CLAUDE.md` carries the pointer; nothing else changes.
  - `python -m pytest tests -q -k "handover or tracker or fingerprint"` green; the stop gates green.
  - The MR merges with the two documents and this contract only.

amendments: (none)
