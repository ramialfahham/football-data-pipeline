# Task contract — onboard-competition must check the country string (#69)

objective: >
  Onboarding a competition can introduce a country the pipeline has never seen, and nothing
  catches it. `base_apif__leagues` LEFT JOINs `country_name_overrides` and coalesces, so an
  unmatched provider string falls through to the page unchanged — silently. Add the check to
  `onboard-competition` at DISCOVERY, where the provider payload is already open and the override
  row can ship in the same MR as the registry entry, plus a confirmation in the post-merge list.
refs: GitLab #69 (the naming rulings and the seed), `!54` (the 67-row seed this checks against)

scope_paths:
  - .claude/skills/onboard-competition/SKILL.md
  - .claude/active_work.md

impact_map: >
  Leaf/documentation short-form. `.claude/skills/**` is instructions an agent reads, not code any
  job executes: `grep -rn "skills/" .gitlab-ci.yml scripts/ dbt_project/` returns nothing, so no
  pipeline, model or test depends on this file. It is NOT a protected path — the protected list is
  `.claude/hooks/`, `.claude/agents/`, `.claude/commands/`, `.claude/settings.json`,
  `.claude/review_routing.json`, `.mcp.json`, `.cursor/mcp.json`, `.github/workflows/`,
  `.gitlab-ci.yml` — and it is not in `review_routing.json`'s `paths`, so scope-auditor is the only
  required reviewer. Blast radius: the next person who onboards a competition reads one more step.

decisions_taken: >
  CPO instruction, 2026-08-16, in this conversation: "now add the country check to the onboard
  skill" — after I reported that the approach is NOT prepared for new countries and named this
  file as the cheap mitigation.

  MEASURED, the defect this prevents: `!50` onboarded the Süper Lig on 2026-08-16. The provider
  sends `Turkey` on the leagues surface and `Türkiye` on the player and coach surfaces (455
  players, 105 coaches). The page reads the leagues surface, so the clean spelling landed there
  BY LUCK. Had it been the other way round, `Türkiye` would have rendered and no guard would have
  fired.

  PLACEMENT, and why it is not the post-merge list alone: caught at Step 0b the override row ships
  in the SAME MR as the registry entry, so the page is never wrong. Caught after merge, the page is
  wrong until somebody looks. The post-merge item is a confirmation, not the control.

  ⚠ This is a MITIGATION, not the fix. The real mechanism is #69's foreign key to `dim_country`,
  where an unknown country fails the key instead of rendering. A skill step is a prose rule and
  this repo has measured that prose rules recur (#30: 33 of 50 corrections were prose-only, 22
  recurred). Recorded in the skill itself so the next reader does not mistake it for the guard.

  NEW MECHANISM: none — a step in an existing skill.
  RECURRING COST: none.

decisions_reserved:
  - Whether `.claude/skills/**` should join the protected-path list. `.claude/commands/**` is
    protected because a command file can embed shell; a skill file can carry shell too, and this
    one does. That is a governance question and the CPO's, not something to decide inside an
    unrelated task. NOT raised as a blocker — the current list is explicit and skills are not on it.

done_when:
  - Step 0b gains a numbered check with a runnable command that prints what the provider sends and
    whether the seed already maps it.
  - The step states the rule (English, everyday short form, no diacritics) and says the override
    row belongs in the SAME MR.
  - It states plainly that nothing catches a missing row today, and names #69's FK as the real fix.
  - The post-merge list gains a confirmation item.
  - No other section of the skill changes.

amendments: (none)
