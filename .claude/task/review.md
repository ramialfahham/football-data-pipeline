# Review — chore/84-orphan-relation-cleanup — 2026-08-21

diff_sha256: 313f91e8302e59266a4b0fe02aa52a6f2ae8bd5a97f08b2089b231a66ff09c45

rounds: 2

Round 1 returned FAIL from BOTH required reviewers. Both findings were verified against the repo
before being acted on, and both were real. One of them (scope-auditor's) exposed a false negative in
my own earlier check: I had grepped `escalations.log` for `#84` and read 8 hits as corroboration,
but the pattern was matching `#845` and `#846`. A precise search returned nothing, which is exactly
what the reviewer said. The verdicts below are round 2, returned by the same two agents resuming
their own round-1 context, and are recorded as they returned them.

## scope-auditor
VERDICT: PASS
risks_checked:
- Re-verified the round-1 finding against the regenerated patch: `.claude/task/escalations.log` now
  carries a `2026-08-21 chore/84-orphan-relation-cleanup` entry recording the CPO's three actual
  chat turns verbatim (the opening brief's "Do NOT drop anything unilaterally," "file the issue
  first," and "open the MR with the cleanup script"), what each authorizes and what it explicitly
  withholds (`--confirm` runs, CI wiring). `contract.md`'s `refs:` now points at this entry rather
  than asserting the quote itself, `scope_paths` now includes `escalations.log`, and a new
  `amendments:` bullet records the scope extension and its authority (my FAIL). The entry honestly
  flags itself as written after the branch rather than before, which is the correct disclosure
  rather than a backdating attempt. This closes the authority-verification gap I FAILed on.
- Checked the platform-reviewer-driven snapshot fix (`config.target_schema` vs `config.schema` for
  snapshot nodes, plus its two new tests) against my territory: it is a bug fix confined to
  `scripts/cleanup_orphan_relations.py` and `tests/test_cleanup_orphan_relations.py`, both already
  in `scope_paths`; it introduces no new mechanism, no CI wiring, no schedule, and `snapshots`
  remains outside `ALLOWED_DATASETS`, so it does not cross any of the four thresholds and creates no
  new §10 decision.
- Re-checked the threshold declarations and `impact_map` claims against the unchanged script logic
  (dry-run default, manifest floor, allowlist fence, dataset-key sourcing) — nothing here has moved
  since round 1, and they still hold.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Re-verified the round-1 defect against the fix: `scripts/cleanup_orphan_relations.py:151-153` now
  branches `config.get("target_schema") if resource_type == "snapshot" else config.get("schema")`,
  which matches `dbt_project/dbt_project.yml:170-172`'s `+target_schema: snapshots` and the comment
  above it stating the value bypasses `generate_schema_name.sql`. The docstring (lines 22-34) now
  states the two keys separately, names the DEFAULT_DATASET-misfile consequence, and is honest that
  it's inert today because no snapshot exists and `snapshots` isn't in `ALLOWED_DATASETS` — no
  remaining factually-false claim.
- Read the two new tests (`tests/test_cleanup_orphan_relations.py:207-248`):
  `test_a_snapshot_is_keyed_on_target_schema_not_schema` asserts `("snapshots", "snap_thing") in
  expected` and `(DEFAULT_DATASET, "snap_thing") not in expected`;
  `test_a_snapshot_relation_is_never_orphaned_by_a_wrong_dataset` asserts a live
  `("snapshots", "snap_thing")` relation is not returned by `find_orphans`. Both would go red
  against a bare `config.get("schema")` revert (confirmed by the coordinator's mutation pass, and
  independently traceable by hand: reverting collapses `expected` to only
  `(DEFAULT_DATASET, "snap_thing")`, failing test 1's second assert and making test 2's relation
  show up in `find_orphans`'s output since it's absent from `expected`). Not vacuous.
- Checked for a new defect introduced by the diff itself: `resource_type` is now bound to a local
  variable and reused consistently at both the resource_type filter and the ternary; the
  ephemeral-materialized check still runs before the schema branch and is unaffected
  (`materialized: "snapshot"` in the test fixture is not `"ephemeral"`); no other line in
  `load_expected` changed. No regression found.
- Re-scanned `.claude/task/escalations.log`'s new 2026-08-21 `chore/84-orphan-relation-cleanup`
  entry for anything in my territory (credentials, CI/hook changes, dependency or guard edits) — it
  is authority/scope bookkeeping (scope-auditor's territory), touches no path of mine, contains no
  secret material.
- Re-confirmed the rest of round 1's PASS-worthy findings still hold on disk (MANIFEST_FLOOR
  placement, dry-run default, dataset allowlist fence, phase disjointness/coverage, `resolves()`
  transitivity) — unchanged by this delta, not re-litigated.

## escalations
(none)
