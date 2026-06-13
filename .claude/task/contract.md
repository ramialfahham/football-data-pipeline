# Task contract — #430 stale supporting_leagues/form_source cleanup

> Follow-up to PR #429 (retire the dead supporting_leagues/form_source mechanism, audit
> F22). Two stale references the CPO deferred at the time. Both are doc/config hygiene with
> NO runtime effect and NO product-rule change. Part 1 (a dead workflow trigger) is covered
> by the BATCH protected_override in the STANDING CPO GRANT (escalations.log 2026-06-13);
> part 2 (the plan doc) is non-protected, within the standing autonomous backlog grant.
> See docs/working_agreement.md §2.

objective: >
  Part 1 — remove the dead `push` path-trigger line in
  .github/workflows/pages-match-preview.yml that lists the DELETED seed
  dbt_project/seeds/wc_supporting_league_codes.csv (inert; a deleted-file path can never
  trigger). Surgical: remove only that one line, touch nothing else in the workflow.
  Part 2 — in docs/pipeline_architecture_plan.md "Step 3" locked-rules section, update the
  four stale references (lines ~185/189/190/207) to the RETIRED `form_source`/
  `supporting_leagues` registry mechanism. The PRODUCT RULES (the form windows) are
  unchanged and stay exactly as written — only the mechanism by which a competition is
  classified is corrected: classification is now the competition_types taxonomy
  (competition_type → entity_type club/national), and a national team's qualifier legs are
  selected by `entity_type = 'national'` recency/season-to-date (int_form_window__team W1 +
  int_season_to_date__team W2), not an enumerated `supporting_leagues` registry list. Note
  that an explicit WC↔qualifier parent link is reserved for GAP-18 (`parent_competition`).

refs: #430; PR #429 (mechanism retirement); audit F22; docs/competition_types taxonomy.

protected_override:
  approval: CPO BATCH override in the STANDING CPO GRANT (escalations.log 2026-06-13) —
    "removing dead/stale entries from .github/workflows/ flagged by the G4 audit … covers
    #430's pages-match-preview stale trigger". This is exactly that dead trigger line.
  - .github/workflows/pages-match-preview.yml  # part 1: remove one dead path-trigger line

scope_paths:
  - .github/workflows/pages-match-preview.yml
  - docs/pipeline_architecture_plan.md
  - .claude/task/contract.md

decisions_taken: >
  Doc/config hygiene only, within the standing grant (part 1 batch override; part 2
  non-protected). NO product-rule change: the locked form-window rules (last-5 W1 +
  season-to-matchday W2, pre/during/post-competition phase, season boundaries) are intact
  and unchanged. CLAUDE.md's form-window rule names neither retired mechanism, so it does
  not change. Only the retired registry-field references in the plan doc are corrected to
  the live taxonomy basis. Verified: form_source/supporting_leagues exist only in stale
  build artifacts (target/, .pyc), the seed is deleted, and competition_types.csv carries
  the entity_type taxonomy.

decisions_reserved:
  - Keep it surgical. Do NOT alter the form-window product rules, the window models, the
    other pages-match-preview triggers, or CLAUDE.md/memory. If a reviewer finds the plan
    doc's rule TEXT (not the mechanism names) is itself wrong vs the implementation, STOP and
    surface it rather than rewriting the rule here — that would be a §10 product question.

done_when:
  - pages-match-preview.yml no longer lists wc_supporting_league_codes.csv; every other
    trigger line is byte-identical; YAML still valid.
  - the plan doc no longer references form_source/supporting_leagues as live; the four spots
    describe the competition_types taxonomy + the live window models instead; the form-window
    RULES are unchanged; no remaining source reference to the retired mechanism (stale
    build artifacts in target/ excepted).
  - reviewers: scope-auditor (always) + cto-reviewer (.github/workflows/**) — PASS.

amendments: (none)
