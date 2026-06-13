# Task contract — remove dead per-competition path triggers from pages-match-preview.yml (#422)

> Audit F13: .github/workflows/pages-match-preview.yml lists per-competition staging path
> triggers (pl/pd/bl2/sa/l1/vl) that the zero-file rule forbids and that do not exist —
> permanently dead, and they falsely imply a per-competition architecture. Remove them.
> Touches a PROTECTED path (.github/workflows/) → protected_override below.
> See docs/working_agreement.md §2.

objective: >
  Remove the six dead per-competition staging path triggers from the push.paths list of
  .github/workflows/pages-match-preview.yml:
    dbt_project/models/1_staging/api_football/{pl,pd,bl2,sa,l1,vl}/**
  These directories cannot exist under the zero-file rule (staging is generic, one model
  per entity, no per-competition subdirs — enforced by check_layer_contract.py). The
  generic trigger `dbt_project/models/1_staging/**` already above them covers any real
  staging change, so removing the six is a pure no-op to the workflow's actual behaviour.

refs: #422 (audit F13).

protected_override: >
  CPO approval 2026-06-13 (conversation): "Option 1 granted" — explicit authorization to
  edit the protected .github/workflows/ path for #422 (remove the dead per-competition
  staging path triggers from pages-match-preview.yml).

scope_paths:
  - .github/workflows/pages-match-preview.yml
  - .claude/task/contract.md
  - .claude/active_work.md

decisions_taken: >
  CPO-approved (audit ruling 2026-06-12: file; protected_override granted 2026-06-13). Pure
  removal of permanently-dead trigger globs. STRICTLY scoped to the six per-competition
  staging path triggers (F13) — other stale-looking triggers (e.g. the retired
  wc_supporting_league_codes.csv seed) belong to #430, NOT this task; leave them untouched.

decisions_reserved:
  - None. The change is behaviour-preserving: the generic 1_staging/** trigger already
    fires on any staging change, so removing the per-competition globs cannot change which
    pushes trigger the workflow. If a reviewer finds these dirs DO exist (they must not,
    per the zero-file rule), STOP and escalate rather than remove.

done_when:
  - the six `.../1_staging/api_football/{pl,pd,bl2,sa,l1,vl}/**` lines are removed from the
    push.paths list; every other trigger line is unchanged.
  - the workflow YAML still parses (valid YAML; trigger block intact).
  - grep confirms no remaining per-competition staging path glob in the workflow.
  - reviewers: scope-auditor (always) + cto-reviewer (.github/workflows/**) — PASS.

amendments: (none)
