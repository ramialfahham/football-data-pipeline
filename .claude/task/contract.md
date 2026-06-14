# Task contract — new skill: onboard-endpoint (evaluate + ingest a new API endpoint)

> CPO-directed this session (2026-06-14): codify the repeatable routine we ran twice (the four
> player endpoints, then transfers) for bringing a NEW API endpoint / data type into the
> pipeline — check-if-already-ingested, throwaway verification calls, cost estimate, the
> CPO cost-approval gate, then the build. Complements onboard-competition (add a league) and
> verify-competition-ingest (post-ingest health). A guide/checklist skill — not a protected
> guard. See docs/working_agreement.md §2/§10, docs/agent_guardrails.md.

objective: >
  Add a new skill `.claude/skills/onboard-endpoint/SKILL.md` that walks an agent through
  evaluating and ingesting an API-Football endpoint we don't currently take:
  (0) check whether we already ingest it (codebase + raw tables);
  (1) make a few THROWAWAY verification calls (auth from .env, mask the key, pick the cheap
      axis e.g. by-team vs by-player, summarize response shape + data quality on real examples);
  (2) estimate cost (cheapest axis, backfill size, ongoing amortized, against the /status daily
      quota);
  (3) the CPO COST-APPROVAL gate — never enable a recurring pull without explicit CPO approval
      (cost-non-negotiable); (4) CPO history-depth decision; (5) build (RAW_APIF_{entity} raw
      table, generic staging, base, a loads/ module, coverage/completeness wiring), each piece
      through the normal contract → review → PR governance. Mirror onboard-competition's format
      and its Step-0a cost-gate discipline.

refs: CPO direction (this conversation, 2026-06-14); the player-data ingestion plan
  (C:\Users\Rami\.claude\plans\player_data_ingestion_plan.md, §1–§5); existing skills
  onboard-competition + verify-competition-ingest.

scope_paths:
  - .claude/skills/onboard-endpoint/SKILL.md
  - .claude/task/contract.md

decisions_taken: >
  CPO directed creating this skill (conversation 2026-06-14, "go ahead"). The name follows the
  existing `onboard-*` convention (a codified naming pattern, not a new product-naming decision).
  Scope: a guide/checklist ONLY — it documents steps + project specifics (auth, key masking,
  cost sizing, the cheap-axis idea). It must NOT auto-fire API calls or auto-enable ingestion;
  the cost-approval and history-depth decisions stay with the CPO (mirrors onboard-competition
  Step 0a). No code, no model, no protected-guard change — a single new markdown file.

decisions_reserved:
  - The skill must route every §10 decision (cost approval, history depth, any NEW mechanism) to
    the CPO — it may not present any of them as auto-grantable. If drafting surfaces a need to
    touch a protected guard (.claude/hooks, .claude/agents, settings.json, review_routing.json,
    .github/workflows) or to assert a product/metric rule, STOP and surface it.
  - The skill name (`onboard-endpoint`) is user-facing; if a reviewer reads it as a §10 naming
    decision rather than convention-following, flag it for the CPO rather than guessing an
    alternative.

done_when:
  - `.claude/skills/onboard-endpoint/SKILL.md` exists with valid frontmatter (name + description)
    and a stepwise procedure: check-if-ingested -> throwaway verification calls -> cost estimate
    -> CPO cost-approval gate -> history-depth -> build -> caveats/known-issues, mirroring
    onboard-competition's structure and cost-gate discipline.
  - The skill explicitly states it is a guide (no auto-ingest, no auto-cost-approval) and points
    at onboard-competition / verify-competition-ingest for adjacent workflows.
  - reviewers: scope-auditor (always) + cto-reviewer (tooling/process) PASS.

amendments: (none)
