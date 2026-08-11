# Review — fix/53-macau-event-attribution — 2026-08-11

diff_sha256: 67086a9ec75509267e1dc9d976a8e15792da1f124c6384ebdacc6df074d4bf8a

rounds: 2

<!--
Round 1 was spent on a defect in the REVIEW MACHINERY, not in the change, and both
reviewers caught it independently. `.claude/hooks/git_discipline.py --review-patch`
writes the patch to STDOUT and accepts no `--base` argument; the builder passed
`--base main` (silently ignored) and never redirected stdout into
`.claude/task/review_input.patch`, so the file the reviewers read was still the
PREVIOUS task's patch (#33 item 14, already merged as c742b96) and contained no hunk
for this branch at all. scope-auditor FAILed on it. analytics-engineer-reviewer
reported it as a process anomaly and reviewed the on-disk files directly instead.
Fixed by regenerating the patch properly; no branch content changed. Round 2 is the
first round in which either reviewer judged this task's actual diff.
-->

## scope-auditor
VERDICT: PASS
risks_checked:
- Compared every file in the regenerated `review_input.patch` against `contract.md`'s
  `scope_paths`: `dbt_project/seeds/fixture_event_team_overrides.csv`,
  `.claude/task/contract.md` and `.claude/task/escalations.log` are the only three
  touched, and all three are declared. No file outside scope appears.
- Checked the CSV edit against the contract's "no model/macro/SQL changes" claim: the
  diff adds exactly one row and no `.sql` file appears anywhere in the diff. Parsed the
  row by hand for the 4-column-with-quoted-comma structure the contract describes —
  RFC 4180-valid, resolves to exactly 4 fields.
- Verified `mode` is `reattribute_if_cohabiting`, not `alias`, matching both
  `contract.md` and the independently-recorded `escalations.log` entry
  "2026-08-11 — #53", which states the CPO ruling verbatim. The ruling is therefore not
  confined to the artefact whose scope it authorises — the rule this project has FAILed
  builders on twice before.
- Checked all four THRESHOLD DECLARATIONS against what the diff actually contains: NEW
  MECHANISM (none — no new file, mode or column), RECURRING COST (none — no job,
  schedule or service touched), GUARD LOOSENED (the guard test is absent from the diff,
  so its `severity` cannot have moved), SHIPPED NUMBERS (declared "yes, 10 rows" and
  quantified in `blast_radius`). All four are honest against the diff.
- Checked `decisions_reserved` for anything nevertheless decided: neither the `dim_team`
  question nor the provider-feed question is touched by the one-row CSV change.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Seed row well-formedness: the new row parses as exactly 4 fields under RFC 4180 —
  the embedded comma sits inside the quoted `note`. CRLF preserved on all 4 lines,
  non-ASCII "ção" consistent with valid UTF-8.
- `dbt_project/seeds/schema.yml` (`fixture_event_team_overrides` block): `unique` on
  `wrong_team_api_id` still holds (4767 is distinct from 2263/6424); `accepted_values`
  on `mode` admits `reattribute_if_cohabiting`; `not_null` holds on all four columns.
  No declared seed test is broken.
- `base_apif__fixture_events.sql:83-127`: traced the `reattribute_if_cohabiting` join —
  fires only when `team_id = wrong_team_api_id` AND `correct_team_api_id` IS a fixture
  participant AND `wrong_team_api_id` is NOT, matching the contract exactly. The
  `unique` constraint on `wrong_team_api_id` prevents fan-out from multiple matches.
- `fct_fixture_event.sql:47-64`: the self-heal incremental predicate re-processes any
  committed fixture whose `team_sk` is not in `(home_team_sk, away_team_sk)`, confirming
  the contract's claim that no `--full-refresh` and no backfill are needed.
- `assert_event_team_in_fixture_participants.sql`: read in full, unchanged, still
  `severity='error'`. The data is corrected so the guard passes; the guard is not moved
  to fit the data.
- `dbt_project/docs/layering.md`: the seed+join pattern this row extends belongs in
  `2_base` (cross-source entity resolution), and no model file changed, so no logic is
  smuggled into another layer.
- Competition-agnostic (§8): the join filters on team ids only, never on `league_code`;
  the `WCQAS` mention in the note is documentation, not a predicate.
- The PROD simulation's substitution of `fct_fixture_event.team_api_id` for the model's
  `recovered.team_id`: core's `team_api_id` is post-EXISTING-override
  (`base_apif__fixture_events.sql:105-109` -> `fct_fixture_event.sql:77`), so the
  substitution is only valid where no existing override could produce the value under
  test. Neither live override row (2263->10124, 6424->25274) keys on or targets 4767 on
  either side, so for the `team_sk=4767` population the two values are provably
  identical. Sound for this measurement.
- The PROD simulation's substitution of `fct_fixture` for `base_apif__fixtures_next` as
  the participant source: `fct_fixture.sql:12-13` casts `home_team_id`/`away_team_id`
  straight through with no intervening join or override, matching the base model's own
  `fixture_participants` CTE; null-handling is equivalent between the guard's WHERE and
  the CTE's filter. No hidden case.

## escalations
(none)
