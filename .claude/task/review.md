# Review — chore/retire-dead-form-source — 2026-06-12

> Retire the dead supporting_leagues/form_source mechanism + orphaned
> wc_supporting_league_codes seed. Two review cycles.
>
> Cycle 1: scope-auditor returned a FAIL (stale references to the deleted
> seed/mechanism in docs/competitions/wc26.md and the onboard SKILL.md template,
> plus the protected workflow trigger). Escalated to the CPO, who approved fixing
> wc26.md + SKILL.md in this branch (contract amendment A1) and DEFERRING the inert
> protected workflow trigger to a follow-up issue. Cycle 2 (this artifact): the doc
> fixes are in; scope-auditor PASSes on the expanded diff. data-engineer and
> analytics-engineer PASSed in cycle 1; their slices (registry.py, competition_
> registry.yml, seeds) are byte-identical in the cycle-2 diff, so their verdicts
> stand.

diff_sha256: 0f8ad7102eac96798ea8be9e575e5a55ec97c9e0da8fce151438053de0a19737

## scope-auditor
VERDICT: PASS
risks_checked:
- Stale registry fields silently discarded: removing the form_source/supporting_
  leagues parsing means any legacy YAML entry carrying them is ignored without error
  (PyYAML/dataclass tolerate unknown keys) — safe, no crash; the correct behavior is
  to ignore dead fields, not validate them. The diff also removed the registry's own
  form_source legend + every entry's form_source line, so no stragglers remain. Held.
- Inert workflow trigger deferral: `.github/workflows/pages-match-preview.yml:34`
  still lists the deleted seed path, but a deleted-file path can never trigger; this
  is recorded as DEFERRED in contract amendment A1 (CPO-approved), not silently
  decided. (Also noted: docs/pipeline_architecture_plan.md still references the old
  mechanism — a design plan outside scope; folded into the same follow-up.) Held.
- Scope + reserved decisions: all 6 changed files are within the amended scope_paths;
  A1 carries recorded CPO authority; the diff only removes dead code + fixes docs —
  it does NOT begin building the GAP-18 parent-child dim or tournament-window form.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Dead-code confirmation: `Competition.form_source` and `.supporting_leagues` have
  zero live consumers in ingestion/, dbt_project/models/, or scripts/. The former
  consumer `int_matchday__team_form_metrics` exists only in dbt_project/target/ build
  artifacts (no source model) — confirming #321 retirement. The removed fields were
  structurally inert.
- Guard deadness: no registry entry carries `competition_type: "international_
  tournament"` (actual values: world_championship, qualifying, domestic_league,
  domestic_cup, continental_*). The removed guard's condition was permanently false;
  removing it drops no validation that was ever active at runtime.
- Sample-fixture rule scoping: registry.py parses the registry YAML (config), not API
  response payloads; the CPO sample-fixture rule targets response-parsing/merge logic.
  No ingestion write path, WRITE_TRUNCATE, history/cadence knob, or provider ID is
  touched. The rule does not apply to this config-parse removal.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Deletion integrity: both halves are present — the .csv is gone from
  dbt_project/seeds/ and the schema.yml entry is removed without breaking the
  surrounding YAML seed block (clean transition to wc_team_market_value_snapshot).
- Zero live refs (config-as-code): grep of `wc_supporting_league_codes` across
  dbt_project/models, macros, dbt_project.yml seeds config, scripts/, ingestion/
  returns nothing; the seed drives nothing that compiles. dbt parse passes.
- Lossless removal: the WC→qualifier relationship is preserved via
  `parent_competition: "WC"` on all seven WCQ codes (reserved for GAP-18); the seed's
  qualifier_season_api_year was only consumed by the retired supporting_leagues path.

## escalations
- question (cycle 1): scope-auditor FAILed on stale references to the deleted
  seed/mechanism outside the original scope (wc26.md doc, onboard SKILL.md template,
  and the protected pages-match-preview.yml trigger). Fix all in-branch (expand scope +
  gate-lift the workflow), or fix the docs and defer the inert workflow trigger?
  CPO ANSWER (2026-06-12): fix wc26.md + SKILL.md in this branch (contract amendment
  A1); leave the inert workflow trigger and file a follow-up issue — do NOT gate-lift
  the protected workflow for one harmless stale line.
