# Review — fix/official-results — a result that differs from the league's official decision is corrected to it, with its source

diff_sha256: d30d868dda4af3435c38c360e74803e3437e11f694e28e963fe76ecd68439718

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every changed file, the four amendment paths included, is in scope_paths; the amendment records its authority and content and was written on a clean tree.
- Section 10: the 8 match corrections and 4 table rows follow #194's approved checklist; the readings (awarded_to_team_id for a match awarded with no score, AWD with 'Technical loss', source_kind official / match_reports) are declared under the 2026-10-02 delegation; no user-visible name, label, URL or composition changes.
- Thresholds: NEW MECHANISM none (the fixture_team_id_overrides pattern), RECURRING COST two small seeds, two joins and one test; no model, hook, library, workflow step or cadence added.
- Reserved decisions held: no catalogue, formula or window change; awarded-match display untouched; no stat or event corrected.
- Doc-sync: cleaning_rules' "Results are never corrected" replaced by the issue's sentence; the standings texts that called every value the provider's row as published now say the league's official row; base, core and seed descriptions cover every new column.
- Impact map evidenced (pasted lineage, 69 models, 29 marts, measured blast radius); no coverage cut; no secret, credential or permission change; no escalations.log entry.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: corrections applied once in base from seeds; fct_fixture only casts the new key; W/D/L stays decided in int_legs__team_match; no materialisation set, no new model.
- Second result derivation: the only other goal comparison, mart_player_match_log, reads FT/AET/PEN only, so an awarded match never reaches it; every result reader takes result from int_legs__team_match.
- Grain and tests: join keys are unique-tested on both seeds; base grain tests untouched; awarded_to_team_sk carries a relationships test to dim_team; the new singular test covers not applied, winner not valid, not sourced and no longer needed, its case order and null paths traced.
- Competition-agnostic: no competition identifier in model or test SQL; no catalogue, ratio or consumption change.
- Round 2: the mart, layering and content-architecture texts and the base, core and mart column descriptions now state the league's official standings row, the provider's except where corrected; the contract's source_kind matches the seeds; R7 holds unchanged.

## escalations
(none)
