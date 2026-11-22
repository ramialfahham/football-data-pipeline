# Review — claude/169-player-page-rule-b028ed — 2026-11-22

diff_sha256: 82a8ebf29e281d1a4853d6afbbf39671aa3c287472c042d689db97f2a686df6a

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope paths against the diff: every changed file is inside scope_paths, the amendments list is empty.
- The National team tab audience and the edition placing against the ruling on #169 (note 4294939008, approved in chat, 2026-11-22): the diff implements that and nothing broader.
- New mechanism or recurring cost: one intermediate model of an existing class, no run, dependency or cost added.
- Impact map evidenced with the dbt ls lineage and a measured blast radius; the benchmarks sentence now agrees with the lineage.
- Doc sync: has_player_page doc block, shared.yml and int_player_page.yml descriptions updated; no remaining "and a tab" text.
- Approved design: no site_v2 or export file touched; contract names player: #136.
- Round 2: the known-national-tab check in assert_player_has_page uses the same date guard as the known-player check; the contract done_when matches the diff.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL (answer-key seed rows that fail from 2027-07-01) resolved: the seed rows are gone and assert_player_has_page checks the two players' tab under the same date guard.
- Contract blast_radius sentence on mart_player_competition_benchmarks checked against the mart lines that read the window seasons, accurate.
- int_player_page.yml description of int_player_page__window_seasons checked against the model SQL, no contradiction.
- Grain of int_player_page__window_seasons: squad and earned branches are exclusive on national_tab_basis, the earned branch is distinct.
- Layer placement, competition-agnostic logic and tests moved with the semantics, no defect.

## escalations
(none)

## after the first pipeline
The test national_tab_basis_follows_the_tab moved from the column to the model in
int_player_page.yml, because a column-level expression_is_true prefixes the column name to the
expression. Its compiled SQL was read, and run against the new profile logic on prod data: 0
failing rows. The change is that one test, so the verdicts above stand.
