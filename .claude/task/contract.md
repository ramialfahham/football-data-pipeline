# Task contract — retire dead supporting_leagues / form_source mechanism

> Cleanup of dead, unconsumed code surfaced by the G4 audit (F22 reclassified).
> Form is recency-based (`int_form_window__team`, #320/#323); the old form-source
> path's only consumer (`int_matchday__team_form_metrics`) was retired in #321, so
> `supporting_leagues`, `form_source`, and the `wc_supporting_league_codes` seed are
> vestigial. See docs/working_agreement.md §2/§5/§10, Appendix A.

objective: >
  Retire the dead supporting_leagues / form_source form mechanism. Form is computed
  via cross-competition recency (int_form_window__team); this path drives nothing.
  Remove the WC supporting_leagues block, the form_source field, the buggy
  competition_type guard, and the orphaned wc_supporting_league_codes seed. KEEP
  parent_competition as curated intent reserved for GAP-18 (it is the clean general
  representation of the parent-child relationship; it makes the deleted seed
  redundant).
refs: G4 audit F22 (#414 — reclassified: NOT a live form bug; the impact claim was
  overstated, form comes from recency). GAP-18 = the deferred consumer.

scope_paths:
  - ingestion/api_football/registry.py
  - docs/competition_registry.yml
  - dbt_project/seeds/wc_supporting_league_codes.csv
  - dbt_project/seeds/schema.yml
  - docs/competitions/wc26.md                       # amendment A1: doc-sync (stale seed ref)
  - .claude/skills/onboard-competition/SKILL.md     # amendment A1: stale form_source boilerplate
  - .claude/active_work.md   # artifact-only: handover write-out at close

decisions_taken: >
  CPO approval this session (2026-06-12): remove the dead supporting_leagues +
  form_source mechanism entirely (both unconsumed; form_source removal explicitly
  approved). KEEP parent_competition (reserved for GAP-18) with a clarifying comment.
  Delete wc_supporting_league_codes.csv (redundant with parent_competition) + its
  schema.yml entry.

decisions_reserved:
  - The parent-child Core dim (parent_league_code) and the WC tournament-window form
    rule (cumulative from Group-Stage MD2) are GAP-18 — NOT in scope; do not build.
  - If removing form_source surfaces an unforeseen live consumer, STOP and escalate
    (§11) rather than work around it.

done_when:
  - grep shows zero remaining references to `supporting_leagues`, `form_source`, and
    `wc_supporting_league_codes` across ingestion/, dbt_project/models|seeds, scripts/
    (excluding target/ build artifacts and .pyc caches).
  - parent_competition retained in the registry with a reserved-for-GAP-18 comment.
  - `python -c "import ingestion.api_football.registry"` succeeds; the existing
    registry test suite passes; validate-local (offline gates) green.
  - reviewers: scope-auditor (always) + data-engineer-reviewer (registry/ingestion +
    competition_registry.yml) + analytics-engineer-reviewer (seeds) — all PASS or
    answered ESCALATE.

amendments:
  - 2026-06-12 (A1): + docs/competitions/wc26.md, + .claude/skills/onboard-competition/SKILL.md
    — authority: CPO approval this session. The scope-auditor FAILed review cycle 1 on
    stale references to the deleted seed/mechanism in these two files (doc-sync). CPO
    approved fixing both in this branch. The protected workflow trigger
    (.github/workflows/pages-match-preview.yml:34, deleted-seed path) is INERT (two
    reviewers confirmed a deleted-file path can never trigger) and is DEFERRED to a
    follow-up issue per CPO — NOT gate-lifted here.
# On amendment (clean tree only):
#   - <date>: + <path> — authority: <CPO answer / standing rule>; content: <what>
