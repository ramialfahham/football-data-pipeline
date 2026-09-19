# Review — feat/109-range-tests-and-key-graph — 2026-09-19

diff_sha256: f329caa32e4a64ded701694683c611564a62a4b43a03d28ff878281a5a3d67f9

rounds: 2

Round 2 (delta): three round-1 findings resolved. (1) `engineering_standards.md` §3.1 states the
declared soft link and §3.5 names the script — the rule's own document edited in the same MR
(verdict then: FAIL by the scope-auditor). (2) The three player provider-subset ratios on
`int_player_season_position__metrics` and `mart_player_momentum` are bounded >= 0, not [0,1]
(verdict then: FAIL by the warehouse reviewer). (3) The script prints its soft links on a red run
too, with a test for the mixed case; the "not wired into CI" claim corrected in the contract, the
script and the test file — the pytest's last test enforces the rule in `test:python` on every MR
(verdict then: FAIL by the platform reviewer).

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 2: `engineering_standards.md` diff is two hunks only — the "declared soft link" paragraph
  under §3.1 and §3.5's last bullet; nothing else in the file moved. The amendment cites
  `working_agreement.md` §11 and the round-1 finding, no invented CPO quote. The four
  `meta: soft_link:` declarations in `core.yml` match the contract's paragraph and the real-tree
  test's "4 declared soft links". The CI-wiring correction is declared as a correction in the
  contract's NEW MECHANISM paragraph, the script and the test docstrings — no silent widening.
  The >= 0 bounds on the three ratios carry a one-line why in both files; `saves_player_pct`
  stays [0,1]. Only `contract.md` and the standards file carry new content beyond round 1.
- Round 1: all 18 changed paths inside `scope_paths`; exactly 4 soft links added and none of the
  four also carries `relationships`; the one comment-clause rewrite in `int_team_profile.yml` is
  true of the test beneath it; the signed-difference citation exists unchanged in
  `int_team_season.yml`; no `.sql` in the diff; no `relationships` at `warn` anywhere.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 2: `saves_player_pct = saves / (saves + goals_against)` is bounded by construction on
  both surfaces (`int_player_season_position__metrics.sql:151-154`, `mart_player_momentum.sql:68`),
  so [0,1] stands; the other three divide two independently reported provider counts, so >= 0 is
  the right bound and [0,1] was wrong — the asymmetry in the fix matches the formulas. §3.1's
  soft-link paragraph is narrow and accurate and matches `classify()` / `main()` line by line;
  soft links print before the findings branch; the mixed-case test exists. Noted, not acted on:
  `int_team_season.yml:535,538` (the pre-existing season-grain player test) still bounds the same
  three ratios [0,1] — outside this delta and this MR.
- Round 1: every [0,1]-bounded mart pct in `domestic_league.yml` and `shared.yml` is a
  pass-through from `int_team_season__metrics` (whole-season, already [0,1]); the year-over-year
  columns traced to `int_team_season__metrics_cumulative` and given the same split that model
  makes; every `relationships` parent/field spot-checked (league, season, role-prefixed team keys,
  the two fixture roles, `mart_roster.player_team_season_sk`); `resolve()`'s prefix rule traced
  against its tests and the shipped ymls, no misclassification; the market-value tests are a
  vacuous pass on an empty view and say so; the four soft links carry non-empty rationale.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 2: the script's and the test file's docstrings now say the pytest's last test enforces
  the rule in `test:python` on every MR until the `validate:governance` line lands — verified
  against `.gitlab-ci.yml:564-571` and against `test_materialisation_policy.py` /
  `test_persist_docs_policy.py`, the same real-tree shape. `main()` order: unparseable → floor →
  census + soft links (unconditional) → findings; a red run prints the soft links. The mixed-case
  test pins the fix (under the old ordering its soft-link assertion would fail). The mutation in
  `done_when` still holds; the floor and real-tree tests read consistently with the new output.
- Round 1: read-only script, safe to re-run; fail-closed on unparseable yml before the floor;
  non-dict documents and nameless columns skipped as the hygiene script does; a bare `null` in a
  `tests:` list filtered; floors comfortably under the real tree and over zero; a yml directly
  under `models/` yields `layer=""`, no crash; sorted walks, explicit UTF-8, posix paths in
  messages; ruff-clean by reading under `.ruff-ci.toml`.

## escalations
(none)
