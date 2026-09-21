# Review — feat/109-projection-check-wired — 2026-09-21

diff_sha256: 6c982550bfffd3ec8a5e96be1204a2be8abc8ddd826e57013febd069f10e0c81

rounds: 2

Round 2 (delta): the platform reviewer FAILed round 1 on two defects in
`scripts/check_yml_vs_projection.py` — a struct entry was matched on its parent only, while
dbt-bigquery 1.7.2's catalogue reads `INFORMATION_SCHEMA.COLUMN_FIELD_PATHS` and holds the parent
AND every leaf path (the prod artifact for `mart_head_to_head` shows all six), so a mistyped leaf
passed; and a yml block whose model has no `.sql` was skipped silently. Fixed: full-path
case-insensitive match, no struct special case (strictly stronger); an orphan block is a finding
naming yml and model; three tests; the corrected premise recorded in the contract's
`decisions_taken`. Mutations against the real prod catalogue on a scratch copy of the tree: fake
column, `recent_meetings.goals_fro`, `mart_head_to_head.sql` renamed away — each exit 1 naming
the site; restore exit 0; floor exit 1. After round 2 the platform reviewer's non-blocking note
(the artifacts comment "the script ends inside dbt_project/", false after the new last line) was
corrected in the same file; the four verdicts below were given on the round-2 patch and that
one comment line is the only change since.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 2: delta confined to the match predicate, one skip turned into a finding, three tests,
  one contract paragraph. The struct-match deviation from the issue line's "its parent" clause
  is implementation, not a §10 class: the governing rule (§3.5, "every documented column exists
  in the model's projection") is untouched, the clause rested on a false factual premise now
  shown with evidence, the fix is strictly stronger, and it is recorded in `decisions_taken` for
  the MR head. The orphan-block finding is the same rule's letter, replacing a silent skip. No new
  path; no threshold crossing; the prod census (0 of 1,915 absent) still governs. Noted: the
  issue's MR D line still states the parent clause — corrected in place on #109 by the builder.
- Round 1: every file in the patch is in `scope_paths`; the amendment adding the two
  `check_relationships_coverage` files is docstring prose only, correcting text this MR makes
  false; `protected_override` present and pointing at the dated 2026-09-20 approval quoted in
  `decisions_taken`, the two-copy form §11 requires, independently confirmed against the
  tracker snapshot's issue text; `impact_map` non-trivial and evidenced with the measured census;
  no undeclared mechanism or recurring cost — one gate script and two offline CI lines, all named
  in the issue line; no `rules:`, `allow_failure`, image or dependency change; doc-sync done
  (`validate-local` rows, §3.5); no secrets; `escalations.log` untouched. Observation, not a
  breach: a red projection check also drops that merge's docs artifacts (no `when: always`), a
  property the docs line has had since it was added.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Round 2: `.gitlab-ci.yml` blob identical to the one passed in round 1; delta confined to the
  script, its tests and `decisions_taken`; imports unchanged, no new dependency, job, cadence or
  BigQuery work; both fixes TIGHTEN the gate and it still fails closed. The corrected struct
  premise is a gate implemented more strictly than its spec's wording because the wording's
  premise was wrong, declared with evidence, reaching the CPO on the MR head — not an
  escalation.
- Round 1: authority for the protected edit verified independently of the builder's quote
  (the tracker snapshot's issue text names the script, both CI lines, both jobs and "a governance
  MR with `protected_override`"); `impact_map` checked against the file — rules unchanged
  (`*not_on_schedule` first, push-to-main on `*data_paths_prod`, web = manual), the projection
  line sits after build, test and docs so a red is post-build, `deploy:export` has no `needs:`
  on `data:build:main`, `build:nightly-image` `needs:` `validate:governance` as it already did
  for every existing governance line; CI fails CLOSED (exit 1 on findings and every Abort, no
  `allow_failure` anywhere, `dbt docs generate` still exactly once); stdlib + PyYAML, already
  installed by `.python`'s `requirements.txt`; no recurring cost; no credentials. Timing: merging
  this MR does not match `*data_paths_prod`, so the check's first live run is the next model or
  yml merge; the contract's "first run green" rests on the read-only measurement.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 2: fix 1 verified — the orphan block appends a finding; its test cannot pass for another
  reason (catalogue holds only the on-disk model, floors at 1, `listed` is 2) and goes red on the
  reverted `continue`. Fix 2 verified — full-path match with no `split(".")` left in the file;
  the leaf test lists `recent_meetings.goals_fro` against a catalogue holding the parent and
  `goals_for`, red on the reverted logic, and its negative assertion pins the sibling as not
  flagged; the premise checked against a real dbt-bigquery catalogue (both `recent_meetings` and
  `recent_meetings.goals_for` are column keys). Fails closed; `catalog[name]` cannot KeyError
  because the abort already requires models ⊆ catalogue. CI line short-circuits red if the `cd`
  fails and is the last line; both jobs inherit `*python` (python:3.11 + PyYAML). Read-only and
  idempotent. The pin asserts job set, order, the `--catalog` path and the `cd` prefix; the
  real-tree test skips, never fakes. `_skip` keeps `dbt_utils`' ymls out of the orphan rule; no
  `*.yaml`, `enabled: false` or ephemeral model in the tree. No dependency, `rules:`, `image:`,
  credential, site or hosting change. Non-blocking: the artifacts comment was stale — corrected.
- Round 1 (FAIL, resolved): the two defects above.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 2: the round-1 acceptance of the parent-only struct rule rested on a mistaken premise;
  re-verified against the installed `dbt-bigquery` catalogue macro
  (`macros/catalog.sql`, `COLUMN_FIELD_PATHS`, `field_path as column_name`) — full-path matching
  is correct and strictly stronger; the orphan-model finding has safe control flow and its test;
  `enabled: false` confirmed absent from the tree by grep. §3.5's two bullets are byte-identical
  to round 1 and never claimed leaf-level or orphan behaviour, so the text still describes the
  mechanism, no more.
- Round 1: the walk covers every layer (all 20 model-declaring ymls plus `dbt_project.yml`
  found), wider than `declare_missing_columns.py`'s three layers as the contract says; the
  struct convention read from `shared.yml:2237-2248` and `mart_head_to_head.sql` (one
  `ARRAY_AGG(STRUCT(...))` column); case rule matches `declare_missing_columns.py` and BigQuery;
  one-yml-only rule aborts and is tested; CI wiring returns to the repo root and reads the
  catalogue path `dbt docs generate` writes; `validate:governance` and `test:python` both run on
  every MR and on `main`, `data:build:main` post-merge only — matching §3.5's text; no model
  SQL, model yml or seed in the patch.

## escalations
(none)
