# Review — feat/metric-layer-integrity-tests — 2026-06-29

> Machine-checked review artifact (G3). FINAL round on the complete diff vs main (the commit was
> collapsed to one via `reset --soft` after a CI-driven fix). The resolvability test's empty-result
> fallback was FROM-less (`select ... where 1 = 0`) — a BigQuery error that surfaced only in
> data-build (validate parses; the offline python checked resolution logic, not rendered SQL).
> Fixed to select `from {{ ref('metric_catalogue') }} where 1 = 0`. All three required reviewers
> PASS on a fresh blinded run against the staged diff below.

diff_sha256: de64d4f00dd7853a1b1d6661ab8f5ee2c36b5f4de1c8cde13c1347016c0de029

## scope-auditor
VERDICT: PASS
risks_checked:
- Resolvability test layer-dependency: the `adapter.get_columns_in_relation` calls on the 3 leg models are guarded by `{% if execute %}` + the `-- depends_on:` comments (CI build order), so they resolve correctly; a missing leg would error (not false-pass). Scope is within scope_paths; no §10 decision beyond decisions_taken; no data-availability encoded in any *_expr (none edited).
- Completeness test blank-handling: the dual NULL-and-`trim()=''` guard correctly covers CSV's ambiguous blank representation (unquoted→NULL, quoted→''); the only residual edge (a future author quoting an intended-null as "") is low-risk and requires a separate authoring mistake. The interpretation copy is §10 wording, contract-declared CPO-approved + consumer-inert.
findings:
- none

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Token resolution against the real aliased leg columns: verified the team-from-players exprs (defensive_actions/tackles/interceptions/blocks_per_match) resolve against the ALIASED names (`sum(tackles_total) as tackles`, etc.), not the source names; all 106 exprs resolve; quoted literals ('W'/'D') stripped before tokenizing; `count(*)`/numeric literals produce no spurious token.
- BigQuery validity of both branches + mechanics: the empty/pass branch (`from {{ ref('metric_catalogue') }} where 1 = 0`) is valid and the compile-time render is the same valid fallback; the non-empty branch is a UNION ALL of FROM-less constant selects (valid, no WHERE); run_query row index alignment (0..4) matches the SELECT; completeness test operator precedence is correctly parenthesised (player-exempt scope intact). Seed: 3 atoms direction=higher_better + interpretation, no *_expr changed, CSV 14 fields.
findings:
- none

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Direction soundness: all three atoms are goals FOR the team (additive to the scoreline) → higher_better is correct; goals_own is the for-version (opponents' own goals in the team's favour), disambiguated by the description + interpretation; the "pressure-forced" copy is hedged with "often", not overclaiming a skill signal.
- Coherence + no formula change: lower_is_better=false aligns with higher_better on all three; confirmed by direct diff inspection that only direction (col 13) + interpretation (col 14) changed — no numerator_expr/denominator_expr/base_relation touched; formula-vs-availability ruling structurally untouched.
findings:
- none

## escalations
- question: Filling `direction` (higher_better) + `interpretation` copy on the 3 team component atoms (goals_penalty, goals_own, goals_open_play) is a §10 metric-meaning/wording decision. Approved, and with what direction?
  CPO ANSWER: Approved this session. The CPO directed all three = higher_better (they are goals for the team — they help the result and often reflect attacking pressure; goals_own is the for-version), and approved the interpretation strings as shown. Recorded here for the audit trail.
