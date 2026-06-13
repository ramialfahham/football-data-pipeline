# Review — chore/cleanup-stale-supporting-leagues-430 — 2026-06-13

> #430 — clean up two stale references to the retired supporting_leagues/form_source
> mechanism (follow-up to PR #429, audit F22). Part 1: remove a dead pages-match-preview
> push-trigger line (deleted seed) — covered by the BATCH protected_override (STANDING CPO
> GRANT, escalations.log 2026-06-13). Part 2: replace the four form_source/supporting_leagues
> references in pipeline_architecture_plan.md's locked-rules section with the competition_types
> taxonomy basis — PRODUCT RULES UNCHANGED. Required: scope-auditor (always) + cto-reviewer
> (.github/workflows/**). One cold iteration: both PASS against the hash below.

diff_sha256: cfde0e79fc68c2453078bf59c2e0ee4cc16382dc9cc1928884612ff7709c7e29

## scope-auditor
VERDICT: PASS
risks_checked:
- §10 product-rule preservation (the crux): verified the plan-doc diff changed only the
  mechanism references (form_source/supporting_leagues → competition_types taxonomy
  competition_type→entity_type), and ALL five locked form-window rules (domestic last-5 +
  prior-season fallback; WC no-cap qualifier/cumulative; season boundaries; marts-thin;
  missing-data-null) are byte-identical. No window behaviour, metric, or rule altered.
  CLAUDE.md + memory NOT changed (CLAUDE.md's form rule names neither retired mechanism, so
  it is not stale).
- Authorization + protected path: pages-match-preview.yml is named in the contract's
  protected_override AND backed by the batch grant (escalations.log 2026-06-13); the deleted
  seed wc_supporting_league_codes.csv is confirmed gone (only target/ artifacts remain). The
  removed trigger is inert (deleted-file path can never fire).
- Scope discipline + taxonomy accuracy: only the two enumerated refs + the dead trigger
  changed; club→domestic_league / national→qualifying,world_championship mapping matches
  competition_types.csv; "recency" matches int_form_window__team's recency_rank selection;
  parent_competition correctly described as reserved (not yet consumed by any model).
  docs/player_metrics_catalogue.md's form_source_* hits are output column names (substring
  coincidence), correctly left untouched; the audit doc is historical, untouched.
escalations:
- (none)

## cto-reviewer
VERDICT: PASS
risks_checked:
- Workflow edit surgical + inert: exactly one push-path line removed
  (wc_supporting_league_codes.csv); every other trigger line byte-identical; seed confirmed
  absent from repo; a deleted-file path can never fire → zero runtime change; YAML valid;
  permissions block untouched.
- No protected-path collateral: diff touches only pages-match-preview.yml (protected_override
  present) + docs/pipeline_architecture_plan.md (non-protected); no other workflow, hook,
  settings, or routing file.
- Plan-doc accuracy vs live models: W1 int_form_window__team confirmed entity_type='national'
  no-season-cap recency; competition_types.csv taxonomy confirmed; parent_competition exists
  in the registry YAML but is consumed by zero SQL models, so "reserved for GAP-18" holds in
  substance. (Noted: the "season-to-date" phrasing for the qualifier set is slightly imprecise
  re W2's per-league-per-season grain, but it is a pre-existing doc-level nuance the diff does
  not worsen, and is consistent with the two-window model.)
- No live mechanism left behind: zero form_source/supporting_leagues hits in .sql/.yml/.py/.csv
  source; remaining hits are stale target/ artifacts, the historical audit doc, and the plan
  doc's own past-tense retirement note. No secrets/permission changes; idempotent.
escalations:
- (none)

## escalations
(none — single cold iteration; both reviewers PASS against the locked hash. NOTE on process:
the builder initially mis-read int_form_window__team in isolation and raised a §10 product-rule
concern to the CPO; the CPO clarified the rule is settled (taxonomy + pre/during/post phase +
last-5 / season-to-matchday windows). The escalation was withdrawn and the task correctly
re-scoped to mechanism-name cleanup with the product rules preserved.)
