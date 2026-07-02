# Task contract — handover refresh (post-#621)

> Written on a CLEAN tree (branch chore/handover-refresh-621 off main @ 46719fb).
> Bookkeeping only — no code/model/doc-of-record change. Records the accumulated state since #620:
> the Stats-percentile track pick, the PARKED Player Stats wireframe (stash), #530(b) merged (#621),
> and the percentile display contract. See docs/working_agreement.md §2. Handover refreshes skip plan mode.

objective: >
  Bring .claude/active_work.md current after #621 (#530(b), MERGED, main @ 46719fb). Since the last
  refresh (#620) the CPO picked the Stats-percentile screen track; the Player Stats wireframe was DRAFTED
  then PARKED (stashed) when a catalogue-integrity gap surfaced; #530(b) fixed that gap (finishing_efficiency
  + duels_won_pct player rows completed). Record all of it — especially the FRAGILE parked stash + its
  rework list — so a fresh chat can recover and resume. Set NEXT = resume the Player Stats wireframe.

refs: >
  main @ 46719fb (#621 #530b). Parked: stash@{0} on docs/391-player-stats-percentile-spec ("wip:
  12_player_stats wireframe"). Percentile display contract banked in memory
  [[feedback-percentile-display-phrasing]]. Prior refresh #620 (post-#619). Also record #620 itself in the
  "main carries" list (the GAP-20 close-out doc-sync, which the #620-era handover didn't self-list).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Bookkeeping only. Update the header (2026-07-02, main @ 46719fb, #530b merged); append #620 + #621 to the
  "main carries" line; refresh FIRST STEPS/NEXT to "resume the Player Stats wireframe (recover the stash +
  rework)"; add a PARKED-WIREFRAME callout (stash location + rework list, each item STATUS-tagged: the
  uniform top/[median word]/bottom STRUCTURE settled, finishing_efficiency + duels_won_pct now catalogued
  higher_better via #530b, restore Top-scorers link = SETTLED; the median WORD "middle" = PROVISIONAL
  (CPO-to-confirm per the memory); naked-% denominators for save%/duels%/dribbles% = OPEN); add a
  Stats-percentile track entry + #530b to the backlog; record the percentile display contract pointer;
  prepend #620 + #621 to RECENT PRs. Records the session's CPO decisions + faithfully marks the still-open /
  provisional items as such — invents no new product/UX/metric/naming decision.

decisions_reserved:
  - The Player Stats wireframe rework itself — its own continuation (plan mode), next.
  - Flagged follow-ups: season-model single-source repoint; remaining #530(b) rows (goals_penalty,
    goals_open_play metrics, now unblocked). Career screen spec; Phase C / Phase D.

done_when:
  - active_work.md records: main @ 46719fb / #530b merged; the parked Player Stats wireframe stash + rework
    list; the percentile display contract; NEXT = resume the wireframe; #620/#621 in RECENT PRs.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds; CPO merges.

amendments: (none)
