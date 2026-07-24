# Task contract — automate model/effort selection (session default + review-fleet effort pins)

> Written on a CLEAN tree (branch `chore/pin-review-fleet-effort` off main at 646e07c).
> Plan: C:\Users\Rami\.claude\plans\rosy-juggling-quill.md (CPO-approved via ExitPlanMode 2026-07-25).

objective: >
  Stop the CPO having to manually switch model + reasoning effort. Two changes: (1) a personal
  standing session default (Opus + high) in the gitignored `.claude/settings.local.json` so ordinary
  work never needs a manual switch; (2) pin per-agent `effort` on the six review-fleet agents so the
  adversarial reviewers self-select their tier deterministically instead of inheriting the session
  effort. Models are already pinned by design and are NOT changed. Matrix (CPO "Balanced"):
  scope-auditor=medium, the five domain/platform reviewers=high.

refs: >
  Claude Code has no per-task model auto-router (confirmed via claude-code-guide this session): the
  main model is a single fixed choice, so "automation" = one good default + per-agent pins. `effort`
  is a valid agent-frontmatter key (low|medium|high|xhigh) and a valid settings key (`effortLevel`).
  Today no agent pins effort, so all six inherit the session effort — once the session is `high` they
  all silently run high, against the "reviews must be economic" rule in cto-reviewer.md.

scope_paths:
  - .claude/settings.local.json
  - .claude/agents/*.md

protected_override: >
  CPO go this session (2026-07-25): "From now on, can we automate model selection in this repo ...
  don't want to sit here and manually switch between models and effort", then AskUserQuestion answers
  "Opus + high, fixed", "Yes, pin their tiers", and effort matrix "Balanced". Plan CPO-approved via
  ExitPlanMode same day. Only the six `.claude/agents/*.md` definitions are touched under the protected
  prefix (adding one `effort:` line each); no hook, command, workflow, routing file or setting.json is
  touched, and no agent `model` value is changed.

impact_map: >
  writers/consumers: the six `.claude/agents/*.md` files are read ONLY by the orchestrator (the main
    loop) when it spawns review subagents in the Blinding step. NOTHING else reads them: no hook parses
    agent frontmatter (the gates parse contract.md / review.md / review_routing.json only), CI never
    reads them, no python/runtime imports them. `review_routing.json` references agents by NAME only,
    not by their frontmatter, so the effort field is invisible to routing.
  downstream (protected guard path — trace what depends on the guard, not table lineage):
    - Adding `effort:` changes only the reasoning effort each reviewer runs at when I spawn it. It does
      NOT change who reviews what (routing), the model floors, or any gate. If a value is wrong, the
      only effect is a reviewer runs at the wrong depth on a future review — no build, pipeline, site,
      CI or gate behaviour changes. cto-reviewer's procedural opus-on-guard-paths override is untouched
      and still applies (model override at spawn is orthogonal to the frontmatter effort).
  layer_rules: none — no dbt/model/export/ingestion path in scope; check_layer_contract unaffected.
  deploy_order: n/a — no warehouse object, no service, no CI trigger changed.
  blast_radius: review token cost/depth ONLY. scope-auditor runs medium on every commit; the five
    reviewers run high when their surface is touched (they are dormant otherwise). `settings.local.json`
    is gitignored (.gitignore:229), affects only the CPO's local session, and is NOT part of the PR diff.

decisions_taken: >
  (1) Session default = Opus + high (CPO AskUserQuestion 2026-07-25), stored LOCAL/gitignored not in
      the checked-in settings.json (personal preference on a public portfolio repo).
  (2) Pin the review fleet's effort; keep every agent's existing `model` unchanged.
  (3) Effort matrix = Balanced: scope-auditor medium; cto-, analytics-engineer-, bi-analyst-,
      data-engineer-, football-analytics-expert-reviewer high (CPO AskUserQuestion 2026-07-25).

decisions_reserved:
  - Whether the procedural opus-on-guard-paths override for cto-reviewer should ALSO raise effort
    (e.g. to xhigh) on guard-path diffs is left open: kept model-only this task, since Opus + high is
    already deep and extending the rule would edit working_agreement.md §2. Raise to the CPO if a future
    guard review misses depth.

done_when:
  - `.claude/settings.local.json` carries top-level `"model": "opus"` and `"effortLevel": "high"` and
    still parses as valid JSON.
  - Each of the six `.claude/agents/*.md` files has one `effort:` line in its frontmatter matching the
    Balanced matrix; each file still parses (valid YAML frontmatter between the `---` fences); no `model`
    value changed.
  - ONE commit; review.md covers the full diff with cto-reviewer (opus, guard-path) + scope-auditor
    PASS; pushed with an explicit refspec; PR opened. The CPO merges.

amendments: (none)
