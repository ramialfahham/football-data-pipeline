# Review — claude/329-declare-staging-columns-5661af

diff_sha256: d47f93e434c05dc68bde2776fae3861307bf01838d1e49ae67da4007350667b8

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Changed files against scope_paths: stg_apif__generic.yml, shared_columns.md, tests/test_staging_columns_declared.py and the task folder; the shared_columns.md addition is recorded in the contract.
- The 12 new `<name>__provider` blocks follow the existing team_name__provider pattern and are required by check_description_hygiene.py, so no new mechanism, dependency or recurring cost.
- decisions_taken names the approval by date without quoting; decisions_reserved is none and nothing in the diff decides a CPO-class item.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL (passes_accuracy_percent stated a percent unit; cleaned-value blocks reused on staging columns) resolved: 12 columns reference provider-level blocks whose text matches the staging SQL.
- Every JSON path in the 169 added descriptions was compared with the final select of all 16 stg_apif__*.sql; no wrong path, and the decode wording appears only where decode_html_entities is applied.
- Every doc() reference resolves; no deleted lines in the diff. Pre-existing descriptions on team_deliveries.team_country, fixtures_next.shootout_home/away and teams.team_name are outside this diff and stay a follow-up.

## platform-reviewer
VERDICT: PASS
risks_checked:
- output_columns fails closed on a wildcard, a set expression or an unparsable segment, and reads aliases, bare and qualified columns, backticks and jinja calls.
- The test runs offline in test:python with the pinned sqlfluff 4.1.0, with no CI change; paths and encodings are portable.
- Removing a column or a model entry from the YAML fails a parametrised case, and the self-test shows an undeclared column is reported.

## escalations
(none)
