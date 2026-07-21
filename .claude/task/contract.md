# Task contract — de-stale the percentile-display rules after the catalogue direction sweep

> Written on a CLEAN tree (branch `fix/metrics-display-percentile-direction` off main @ 7419ce6).
> CPO-directed 2026-07-21. After PR #677 merged (every metric now carries a `direction`), the locked
> percentile-display section of `docs/wireframes/metrics_display.md` asserts two things that are no
> longer true. CPO: "Do I allow inconsistency?" — no; fix it now rather than deferring.
> See docs/working_agreement.md §1, §2, §10; [[feedback-metric-direction-judgement]].

objective: >
  Correct the two now-false statements in `metrics_display.md` §"Percentile display (vs-peers)" so the
  doc matches the merged metric layer and the CPO's ruling on the bar treatment. (1) Rule 3 still splits
  the player benchmark set into "11 higher_better / 7 neutral" and tells the reader that for the neutral
  ones "top" means most, not better — after #677 there are ZERO neutral metrics in that set, so the split
  and the caveat are both wrong. (2) Rule 5 still says the bar carries NO colour, justified by the risk of
  implying a verdict on the neutral metrics — the CPO ruled (2026-07-21, v2 design review) that these bars are
  direction-aware (green when the metric beats the median in its better direction, plain ink otherwise), and
  the original justification is void now that no neutral metrics remain. ONE bar language applies across every
  vs-population screen, player and team alike, so all three affected documents state the identical rule and
  cross-reference each other. DOC PROSE ONLY. No seed, model, test or frontend change.

refs: >
  PR #677 (catalogue-wide direction sweep, merged, main @ 7419ce6) · the v2 player-page design
  conversation 2026-07-21 (bar-language unification) · [[feedback-metric-direction-judgement]] ·
  [[feedback-v2-design-schema-first]]. Flagged by the football-analytics-expert-reviewer during #677 as a
  known follow-up, deliberately kept out of that PR because this file routes to a different reviewer.

scope_paths:
  - docs/wireframes/metrics_display.md
  - docs/wireframes/12_player_stats.md    # AMENDMENT r1 — carries the SAME two stale claims
  - docs/wireframes/14_team_stats.md      # AMENDMENT r2 — the TEAM benchmark screen carries the same defect
  - .claude/task/**
  - .claude/active_work.md

impact_map: >
  writers: none. A wireframe/display-contract DOC change only — no seed, no dbt model, no test, no export,
  no site_v2 code. Zero rows and zero numbers move anywhere.
  downstream: the doc is the build reference for the Player Stats percentile screen (wireframe 12), which
    is NOT yet built in site_v2. Correcting it now means the screen gets built off accurate rules instead
    of a stale contract. `12_player_stats.md` quotes the same rules and is checked for consistency; if it
    also carries the stale claims that is reported, not silently edited (out of scope).
  layer_rules: documentation only; no layer touched.
  deploy_order: nothing to deploy. No CI data impact.
  blast_radius: zero runtime impact. The change is that a future build reads correct rules.

decisions_taken: >
  1. The "11 higher_better / 7 neutral" split is replaced with the post-#677 reality: all 18 benchmark
     metrics are `higher_better`; 0 neutral and 0 lower_better remain in that set. The "top means most,
     not better" caveat is REMOVED because it described the 7 neutral metrics that no longer exist here.
  2. "One bar, no traffic lights / no colour" is replaced by the CPO's ruling (2026-07-21, v2 design
     review): these bars are direction-aware — green when the metric beats the median in its better
     direction, plain ink otherwise — and the SAME rule holds on every vs-population screen, player and
     team alike. NOTE: this must be stated as the ruling itself, never as parity with some pre-existing
     screen; there is no prior team spec carrying this rule (see amendment r2, finding 1). The original
     rationale (colour would wrongly imply a verdict on the neutral metrics) is recorded as VOID, with the
     reason, so a future reader understands why the rule changed instead of thinking it was ignored.
  3. The `lower_better` mirroring rule (position = 1 − percentile) STAYS as written and stays dormant —
     it is still true that 0 of the benchmark metrics are lower_better, so the rule is correct and unused.
  4. Everything else in the section is left alone: the plain-language ladder ("top X%" / "median" /
     "bottom X%", never "Nth percentile"), the median-anchored framing, position-group peers, the sample
     line, and the ratio volume-triple rule are all still accurate and are NOT touched.

decisions_reserved:
  - "The 26 player metric rows that still have a blank `interpretation` — a separate sweep, unrelated to
     this doc fix."

done_when:
  - metrics_display.md §"Percentile display" contains no claim of neutral metrics in the benchmark set and
    no claim that the bar carries no colour.
  - All three documents state the IDENTICAL direction-aware bar-colour rule and cross-reference each other,
    with each superseded rationale recorded rather than deleted silently. No document claims parity with a
    screen or rule that does not exist.
  - No file outside scope_paths is touched; no seed/model/test/frontend change (diff-verified).
  - Required reviewers PASS: scope-auditor + bi-analyst-reviewer (docs/wireframes/**), per
    review_routing.json. review.md diff_sha256 binds; CPO merges (I never merge).
  - Handover bullet added to .claude/active_work.md.

amendments:
  - >
    r1 (2026-07-21, CPO-DIRECTED): the first draft reserved `docs/wireframes/12_player_stats.md` to a
    follow-up ("report, don't edit"). Checking it showed it repeats BOTH stale claims — the "11
    higher_better / 7 neutral" split (lines 119-121) and the "no colour / would wrongly imply a verdict on
    the neutral metrics" bar rule (line 123) — and it is the SCREEN SPEC the percentile page is actually
    built from, so it matters more than the display contract it quotes. The CPO's standing position
    ("Do I allow inconsistency?") makes deferring it wrong: fixing one doc and leaving its own screen spec
    contradicting it is the very inconsistency being corrected. Added to scope_paths. It sits in
    `docs/wireframes/**`, which routes to bi-analyst-reviewer, already the required reviewer for this task,
    so the review gate is UNCHANGED. Still DOC PROSE ONLY.
  - >
    r2 (2026-07-21, REVIEWER-DRIVEN — bi-analyst-reviewer FAIL, 4 findings, all upheld):
    (1) HIGH, FABRICATED PRECEDENT. My r1 wording claimed the new colour rule "speaks the SAME language as
    the team Performance tab". No such spec exists — "Performance tab" is a name coined in the v2 design
    conversation for a MOCKUP, and the real team benchmark spec `14_team_stats.md` says the OPPOSITE ("no
    traffic-light colours ... deferred to #366"). So the doc asserted parity with a rule that both does not
    exist under that name and contradicts the only real team spec. The citation is removed; the ruling is
    grounded in the CPO conversation itself, and the parity is MADE REAL by fixing the team screen in the
    same PR (the reviewer's own option (b)).
    (2) HIGH, MISSED STALENESS. `14_team_stats.md` carries the identical defect: it claims the 16 rendered
    team metrics are "10 higher_better + 5 neutral + 1 lower_better" and calls `corners_against_per_match`
    neutral. Verified against the merged seed the true tally is 14 higher_better / 2 lower_better / 0
    neutral, with `corners_against_per_match` now `lower_better` (so it IS rank-mirrored). Added to scope.
    (3) MEDIUM, SELF-CONTRADICTION. The still-live "Distributional position, not a verdict ... not good/bad"
    framing sits two lines above the new green-when-better rule. Reconciled in both files rather than left
    contradictory.
    (4) LOW-MEDIUM, MISSED SPOT. `12_player_stats.md` §1 Purpose repeats the extinct "for a volume/style
    metric it just reads as a lot" branch. Fixed.
    `14_team_stats.md` is in `docs/wireframes/**`, which routes to bi-analyst-reviewer, already the required
    reviewer, so the gate is UNCHANGED. Still DOC PROSE ONLY — no seed, model, test or frontend change.
