# Review — claude/fix-268-apos-names-a05dbf — 2026-11-09

diff_sha256: 1f2621bbd362e5d26c557ea345d0ad068ab9a893dd85ea5ba2560874b7daa766

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- All 19 changed files are in scope_paths; no amendments.
- decisions_reserved: the diff decodes only the seven mapped entities and leaves others for the guard, so it decides nothing reserved.
- Recurring cost of the guard test (414 MB a night, about $0.08 a month) is declared in decisions_taken with its measurement and the CPO approval; the macro follows the translit_latin pattern, no new mechanism.
- impact_map carries lineage evidence, measured prod counts and the player-slug change; no coverage cut.
- No secrets, no site_v2/src or export file touched; approved_design none holds.
- Appendix A: no invented metric, no product text in docs, no frontend logic.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Decoding transport escaping per column in staging is source cleanup under layering.md §1_staging, not a business rule.
- check_layer_contract.py: no staging file gains group by, distinct, ref() or a non-league_code partition; the macro's join is to a literal map and its aggregate runs over one value's pieces.
- Macro read for bare ampersands, double escapes, unknown entities, empty strings, NULL and piece ordering; no defect.
- Guard test's 42 (model, column) pairs match every decoded column.
- base_apif__lineups.player_name is the only name parsed from staging JSON outside staging, and it is decoded.
- No seed key, persist_docs description or export script depends on an entity-bearing value.
- Non-blocking: standings group_name / group_description and fixtures_next round_name are provider text outside the name and place scope; no entity in them today.

## escalations
(none)
