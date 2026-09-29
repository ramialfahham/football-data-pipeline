# Review — design/match-page-review — #132 states 1 to 3

diff_sha256: f826f3c8e04723544917b25e0d33ae1bce957624941765b8f185e28940edfb05

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: 149 files in the patch; three are not renders (`.claude/task/contract.md`, `design-mocks/README.md`, `design-mocks/gen_match_page.py`) and 146 are `design-mocks/renders/*`, all inside the contract's scope_paths; no diff header under site*, dbt_project, ingestion, scripts, docs or tests.
- Amendment authority: the 2026-09-29 amendment adding states 2 and 3 quotes dated CPO wording (the #132 state 2 decision comment, the CPO's chat "yes, state 3 decided"); recorded authority, no unrecorded scope growth.
- Impact map: none of ingestion/**, dbt_project/models/**, scripts/export_*.py or site*/ is touched, so none is required; no coverage-cut pattern in a design-mock-only change.
- Doc sync: design-mocks/README.md gains the gen_match_page.py row with its MATCH_STATE variants; no layering, guardrail, wireframe or metrics_display content changes.
- Secrets: the whole patch grepped for key, token, password, bearer, private-key and provider-key patterns: none; the only URLs are the media.api-sports.io image URLs the built site emits; the generator imports no network, subprocess or BigQuery module.
- Thresholds: "NEW MECHANISM: none, RECURRING COST: none" matches the diff (a generator and static HTML reading only local site_v2/dist and site_v2/src/data).
- Reserved decisions (#174, the #176 mart name, the German name of shots on target, player-name links) are stated as open and not resolved; the stand-ins (SEASON_PLAYERS, FORM_STANDIN, H2H_HOME) are named as gaps in the legend, not presented as served values.
- §10 and Appendix A: the proposals are attributed to the CPO's decisions on #132; no bare product decision presented as agreed (A2); nothing computed in the site's frontend (A5); no new escalations.log entry.
- Renders: headers and first diffs sampled; generated HTML with the stable naming pattern, no non-render content.
- Round 2 delta: the pre-commit ruff check (F841) refused the commit; the one unused assignment `codes = …` at design-mocks/gen_match_page.py:920 was deleted. No other use of the variable remains, the render output is unchanged, and no mechanism, dependency, cost, file or scope changed; the round-1 findings stand.
- Rebound after rebasing onto main (#165's merge, which touched only its own docs and the task files): the same 149 files with the same content; the hash changed because the base's task files did.

## escalations
(none)
