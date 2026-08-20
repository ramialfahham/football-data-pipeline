# Task contract — handover update after the Browse drop merged

objective: >
  Bring `.claude/active_work.md` current after `!80` merged. It still named the pre-merge main
  commit, described Browse as an in-flight thread rather than closed, and carried a NEXT item
  ("build the browse-chip mart once names are clean") that is now moot. Bookkeeping only — no code,
  no behaviour change.
refs: MR !80 (merged, main `9d08edf`); `.claude/task/escalations.log` 2026-08-19 entries.

impact_map: >
  Trivial/leaf, evidenced rather than asserted: the only repo file edited is
  `.claude/active_work.md` (plus this contract). That file is a handover artifact read by humans
  and by the SessionStart hook; it is listed in BOTH `review_exclude_paths` and
  `hash_exclude_paths` in `.claude/review_routing.json` and matches `artifact_only`. No model,
  mart, seed, export, site_v2 or test file is touched. Zero warehouse blast radius, zero build
  impact, nothing downstream reads it.

  ⚠ CORRECTED, and the first version of this line was WRONG in the way this whole session has been
  about: it concluded the commit is "artifact-exempt from the review cycle". It is NOT. Staging
  `contract.md` puts the commit in `artifact_only_never`, so a review round IS required however
  trivial the diff — the commit gate said so by refusing the commit. `active_work.md` alone would
  have been exempt; this contract riding with it is what makes it reviewable. Routing gives
  scope-auditor only (`always`); no path here matches any specialist glob.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md

decisions_taken: >
  CPO, in chat, 2026-08-19: "update the handover". Note the sequence, because it matters for
  authority: I offered, the CPO said "no", and then the CPO asked for it directly. The later
  instruction governs.

decisions_reserved:
  - The two follow-ups this handover RECORDS are not decided by it: (a) whether `nav.json` /
    `build_nav` / `fetch_nav` should be deleted now that they have zero frontend consumers — which
    also gates deleting the `display_group` seed column (#57, whose stated blocker #44 is moot now
    Browse is gone); (b) how far a trending-doc-rot pass should go. Both are written into NEXT as
    work to be picked up, not resolved here.

done_when:
  - `active_work.md` names main `9d08edf` and states no open MRs.
  - Browse reads as merged and closed, not in flight; the moot NEXT item is replaced by the two
    real follow-ups it leaves behind.
  - The session's process lessons are recorded where a cold chat will read them: sweep the CONCEPT
    semantically rather than the feature's name, and the 3-round review-cap breach.
  - Under the 16,000-CHARACTER cap, measured with Python `len()` (not `wc -c`, which counts bytes).
  - Committed; MR opened by the post-commit hook.

amendments:
  - none
