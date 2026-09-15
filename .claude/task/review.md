# Review — feat/149-competition-overview — 2026-09-15

diff_sha256: 0e98cb2f7b755f2f7bca8c78dff8445f3b01a6ff8a2cd9b1913434851e9d00a5

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1: every changed path in `scope_paths`; the two amendments carry a dated authority
  (the `.gitignore` sample rule; two #129 rulings); every §10-shaped call traced to a quoted #129
  or in-session CPO authority in `decisions_taken`; the export and `competitionPayload.mjs` only
  select, join identity and order by served columns (A5); `impact_map` pastes a real `dbt ls`
  run; every touched document edited in the same branch; no credential-shaped text; the
  committed sample matches the evidence.
- Round 2 (delta): the third amendment's five paths all in scope; the `deserved_points_gap_rank`
  column matches the CPO's quoted spec; the catalogue diff is one added line; the export sorts by
  the served rank and the page slices the served order, no computation; the two round-1 fixes
  carry no scope change; `decisions_reserved` untouched.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL (two findings): the export ordered the deserved rows by the gap with a name
  tie-break and the page took the ends — ranking in consumption; and the schema test
  `competition_season_summary_biggest_margin_present` was a tautology. The first went to the CPO
  (two written rules in tension: layering.md's "all ranking and ordering in the warehouse" versus
  the competitions index's "sorting need not be decided in the mart"); his answer: the warehouse
  serves a rank. Built as `deserved_points_gap_rank` (row_number over the gap, team_sk
  tie-break, null with the gap) on `int_team_season__deserved_vs_actual` → `mart_team_profile`,
  a catalogue row, two tests; the export selects by it, the page reads the ends. The second
  replaced by `competition_season_summary_referenced_fixtures_carry_their_scores`, which can fail.
- Round 2 (delta) PASS: rank computed once in the warehouse; biconditional null test and a
  total-order uniqueness test; catalogued with a generated docs block; `deservedBoards` slices the
  served order; the pre-existing `sorted()` of the next matchday by kickoff is the same class as
  the standings sort by rank — ordering rows by a served column, not computation — and is not
  held as a defect.
- Round 1 also confirmed: the standings chain is an additive pass-through of a published fact;
  `table_kind` is seed-driven, competition-agnostic and recomputed from core in its test;
  `is_match_that_matters` is warehouse-computed and re-verified from core; the summary mart's
  gaps-and-islands runs traced correct; the facts-versus-metrics split written into
  `docs/metric_layer.md` under the cited #129 ruling.

## platform-reviewer
VERDICT: PASS
risks_checked:
- `.gitignore` sample self-consistency: every team and fixture id the committed competition
  payload links to is allowlisted; the two played fixtures the summary names are correctly not,
  since those rows do not link. Page-count growth from the sample (team pages 60 → 108) is
  disclosed and within the CI heap ceiling.
- The crest URLs are the pre-existing site-wide `Crest.astro` mechanism, not a new external
  fetch. Every new `shape_*` test pins a value that requires the code path; `fetch_*` functions
  untested by the file's existing convention. The seven node tests cover each helper's positive
  and boundary case. The mock check's negative control goes red on the reconstructed defect.
  Comment hygiene: no added line matches the history gate's markers. No guard path touched. No
  credential-shaped text.
- One non-blocking note, fixed in the same branch: the generator docstring advertised `--kind`
  while argv is positional; the docstring now says so.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: `SeasonFacts.astro` invented a German colon for scores (`0:5`) with no authority
  and against the site's own en-dash scores. Fixed: every score renders `home–away` for every
  locale, as `TeamFixtureRow.astro` and `RecentMatch.astro` do; the German render re-read as
  `0–5`.
- Round 2 (delta) PASS: the fix verified in the component and the evidence; the
  `deserved_points_gap_rank` binding traced from the intermediate model through the mart, the
  export, the payload, the type and the page, with no client-side sort; the metric renders
  nowhere as a label, so no label key is owed.
- Round 1 found the rest consistent with the binding rule and the locked display contract: every
  value a served field; the table the provider's row per #129; one link per row; nothing renders
  empty; names never break; every string a key; numbers through the format helpers.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Round 2 FAIL: the new catalogue row `deserved_points_gap_rank` carried `lower_is_better = true`
  beside `direction = neutral`, which `assert_metric_direction_lower_is_better_agree.sql` rejects
  and which contradicted the row's own "an ordering, not good or bad". Fixed to `false`, the
  convention of every neutral row (`deserved_points_gap`, `contribution_player_pct`,
  `minutes_per_appearance`).
- Round 3 (delta) PASS: the single cell changed, the test logic passes the row, the interpretation
  reads correctly, no other field moved. Position by gap is a sound total order; null handling
  and the domestic-league scope inherit the siblings'; the CPO's quoted answer covers the row's
  existence and meaning.

## escalations
- The deserved-boards ordering (round 1, analytics-engineer-reviewer): two written rules in
  tension; put to the CPO in this session with two paths and a recommendation; his answer "The
  warehouse serves a rank" is recorded in the contract's third amendment and built.
- Declined, with reason, in round 2: the next matchday's `sorted()` by kickoff in the export — a
  pre-existing sort by a served column, the same class as the standings sort, held by the
  reviewer as not a defect.
