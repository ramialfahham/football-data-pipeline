# Review — feat/matches-page — #160 part 2

diff_sha256: 5d91ebd234da62887069a889e45b52dfe0b8824106adb917d459fc5d141bd457

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 (FAIL, fixed): the new `matches/*.json` bullet in site_v2/src/data/README.md had been inserted inside the `fixtures/*.json` bullet, so that bullet's continuation (the landing sample's CPO quote and its four fixture ids) read as describing the Matches sample.
- Round 1 otherwise: every changed file in scope_paths; no credential-shaped string (one false positive, "Slovakia"); THRESHOLD DECLARATIONS match the diff (the matches entity is in no scheduled job, .gitlab-ci.yml untouched); the architecture, overview and block standard documents updated; the title and description copy left to the CPO on the MR head; impact_map specific and counted.
- Round 2 delta: the `matches/*.json` bullet now follows the fixtures bullet and is self-contained; no wording or other file changed.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Every rendered field traced to a mart column through the export's existing helpers; the committed day files are producible by the export and match the README's accounting (58 days, 628 fixture payloads); the new inventory rows' selectors match the markup, and the fold and filter rows are byte-identical reuse of Home and the Competitions page; the design check on the built site (165 renders, 0 failures, mutation red then green) read as built-output evidence; the built structure matches the render of record matches-hub_2026-09-23_02; no number rendered twice; a score only with both goals present, a competition without a slug unlinked; the new copy flagged for the CPO on the MR head.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The export's writes are deterministic and the matches entity always exports the whole reach, so day neighbours never point at an uncommitted day; an empty opening day yields no pages and the design check would fail on it; tests pin the export's grouping and its no-selection SQL, and the Python and JS address-word copies change together with tests on both; the spec entity enum change is exercised by the build; no hook, workflow or CI file and no dependency change; no credential; the .gitignore allowlist expansion quantified and spot-checked against the committed files; no new third-party origin.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The export selects, joins, groups and passes mart columns through existing helpers, computing nothing; the site's only arithmetic is the ruled fold slice and counts for copy, and the competition order is the shared existing module #130 names; the join on mart_match_days' tested fixture_sk grain cannot fan out; the SQL-shape test pins no WHERE/ORDER/LIMIT; no metric; no hardcoded league outside test data; no dbt file touched; test coverage adequate for the new export surface.

## escalations
- question: What should the Matches page's committed sample hold, and does the opening day also get a dated address?
  CPO ANSWER: Every competition; the opening day lives only at /matches/ (answered in plan mode; recorded in contract.md decisions_taken).
