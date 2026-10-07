# Review — feature/177-metric-names — 2026-10-07

diff_sha256: 864291028e9f939abaa87b5d53ef9f8b8c0ad1c25f8633dce26547bebb94a61f

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every file is in scope_paths; each addition (wireframes, mock generators, pin tests, prose) has a dated CPO amendment.
- Impact map: the label_en readers listed file by file; the reviewer's own grep agrees.
- Form comparison caption removal recorded with its authority (#166 "no Defending sub-label").
- Old names left only in struck or superseded history rows of metrics_display.md and 10_home.md.
- No secrets, no new mechanism, no recurring cost; order, direction and format untouched.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Rendered evidence is this task's: geometry at 375/700/1010px in DE and FI for hero tiles, Performance rows, board titles and Form comparison rows; 0 overflow, only the documented 375px Performance-row breaks.
- Every wireframe line naming a metric now uses its key and a pointer to strings.ts.
- Locked team rows, order and tiers unchanged; the percentage and per-match rules hold.
- Every new or changed string traces to a contract amendment or decisions_taken.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The Home mock generators build titles as the site does and run; check_teams and check_players pass.
- A test binds the site's per-match flags, hero tiles and share list to the catalogue; the export's per_match excludes shares by the same rule.
- The catalogue loses only label_en; its schema entry and tests go with it; no model reads it.
- No layer, competition or same-window issue.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Row by row, every catalogue field other than label_en is unchanged; no formula, description or direction moves.
- No dangling reader of the catalogue's label_en.
- label_i18n_key keeps not_null and unique.

## platform-reviewer
VERDICT: PASS
risks_checked:
- gen_top_teams and gen_top_players no longer depend on the sigil; the importing generators and check_teams follow.
- The new site test fails on a wrong per-match flag or share entry.
- No dependency, credential, workflow, hosting or build-size change.

## escalations
(none)
