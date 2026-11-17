# Review — claude/243-parts-rows — 2026-11-17

diff_sha256: 8ee0e0a60f4c55257c25fa142bba95b88254de382d7df52f609af00227a1caa4

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1: every file in the patch sits inside scope_paths; the components.yml edit is the one protected_override names (file, links-to, the table-row, index-row and row-list components; no text style, value, rule or measurement change); no wording, label, URL, block order or metric change; links rebuilt from the same word and slug functions, traced row by row; approved_design names every changed page; block_standard.md regenerated in the same branch; the two non-zero row counts are named in acceptance_evidence.md.
- Round 2 (delta): `_rises` exempts only a count group absent from main's raw baseline; a group main holds empty stays pinned; both cases tested; no new mechanism or §10 decision.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 1: the ui/ components render only fields the old markup rendered; no src/data or export change; table cell order unchanged for standings, deserved points, boards and last season; dashes for missing counts, the goalkeeper saves split, singular and plural choice and the trend's role and aria-label unchanged; every t() key is the one the old markup used; each component's link derivation matches the removed code; data attributes pass through; 0 href differences over 14,661 links in the evidence.
- Round 2 (delta): no site_v2 file changed since round 1; the TeamSquad initials-in-a-span difference noted in round 1 is now listed in rendered_page_evidence.md.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1: markup_counts, template_classes, own_classes and link_failures fail closed (a wrong file raises the count; compare fails a rise and a fall); LINK_BUILDERS match each row component's links-to; .ui_paths already runs the check in validate:ui; no dependency change; builtPlayers and hasPlayerPage are memoised. Finding: `_rises` exempted a group main holds empty, so a rise from 0 in such a group passed.
- Round 2 (delta): `_rises(now, was, measured)` exempts only a group missing from main's raw baseline; `test_no_pin_rises_above_mains` passes `set(base)`; `test_a_rise_in_a_group_main_holds_empty_is_reported` would fail under the round-1 filter. Finding fixed.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Round 1 (opus): protected_override describes the components.yml edit as written and names its approval and the link rule; impact_map names the registry's readers; every rule row of the generated table survives; the new key, count groups and link check live inside the existing registry check, a CI step already; the check only adds failures; no dependency, credential or recurring cost.
- Round 2 (delta, opus): the narrowed `_rises` exemption tightens the test relaxation named in round 1; calling it without `measured` exempts nothing; test-only, no imports, no CI change.

## escalations
(none)
