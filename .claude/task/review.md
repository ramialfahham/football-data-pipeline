# Review — docs/metric-layer-rules — every metric rule stated once and shown in BigQuery on the table that carries it

diff_sha256: eedc8222ee18ee44264d1a5800771ac037c1ec3328125b71ccd97273e7771a7f

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every changed path is in scope_paths; the two year-over-year model headers and the base player cleaning test came in by amendments made on a clean tree, with their authority dated.
- Rule removal: docs/metric_layer.md keeps #129's rule that provider facts and catalogue metrics never mix in one block, word for word, with its R7 part as a pointer; "A group is defined once" is main's text, which the locked metrics_display.md links. The test that rule names is missing and is filed as #192, linked to #190 and #129.
- Logic: every SQL and macro hunk is a comment, every yml hunk a description, a doc reference or a comment; no test, config or value changes.
- decisions_reserved: metrics_display.md changes at lines 249-253 only; no new mechanism, recurring cost, secret or §10 class.
- R1 to R7 in the catalogue block match #190 word for word; the ranking block follows the code it replaces; the #94 id pattern enters with #94's renames, as the contract's reading records.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The cleaning block's blank rule against the code: counted in the match per entity (the other team's line; another player; another goalkeeper for a keeper's saves and goals conceded), the score, event and team-line proofs including saves where the opponent had no shot on target, and blank minutes for a player who did something.
- No rule copy left: a sweep of every model yml, doc block and seed yml finds R4 and R6 wording only on playing-time facts (R7) and in the deserved model's own method; the year-over-year copies in mart_team_profile and its competition_type column are gone.
- The 51 hand-described or renamed metric columns reference blocks that exist and are window-free; the two points columns that left-join mart_team_season keep their own null sentence, checked against the SQL joins.
- The window-free rule and the formula contract are in the catalogue block's intro; engineering_standards.md section 2 lists a window among what a description leaves out.
- No logic, test, seed or dbt_project.yml change; the catalogue CSV is untouched.

## platform-reviewer
VERDICT: PASS
risks_checked:
- scripts/sync_metric_docs_blocks.py: RATE_NULL_SENTENCE and the entity-split phrasing are gone with no dead code left; WINDOW_PHRASING and every code line are unchanged by the round-2 comment edit, whose pointer matches the catalogue block.
- tests/test_sync_metric_docs_blocks.py: the replaced tests pin the new output exactly and fail on a revert; the removed tests guarded code that is gone.
- metric_columns.md is what the script produces: no block added or dropped, only the appended null sentences removed; the CI --check step is untouched and still fails closed.
- Given in round 2; the round-3 delta touches only three dbt ymls, outside this territory.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- metrics_display.md changes at lines 249-253 only; no row, label, order, tier, format or null-as-dash rule moves, and the pointer leads to the catalogue row and the catalogue table's rules, which state the same thing.
- The link metrics_display.md relies on, "A group is defined once" in docs/metric_layer.md, exists with main's text.
- The matchday-insights and points column descriptions change BigQuery text only; no page binding or export field moves.
- Given in round 2; the round-3 delta touches no wireframe, site_v2 or i18n file.

## escalations
(none)
