# Review — fix/84-udf-refs-misread-as-missing-tables — 2026-08-21

diff_sha256: bc6d023a7224411f22bc1176ca2c63a539306a2a0442156bd7f3bb89c22171aa

rounds: 2

Round 1: scope-auditor PASS, platform-reviewer FAIL. The FAIL was real and was verified before
being acted on, by adding a mutation that reverts the two lines it named in `main()` and running
it — the pass reported `STILL GREEN`, confirming that reverting the fix's wiring left the entire
suite passing. One end-to-end test closed it, and the same mutation now reports RED. Both verdicts
below are round 2, returned by the same agents resuming their own round-1 context, recorded as they
returned them.

Worth noting in the artifact itself: this branch exists because the previous review cycle
(`!90`, two reviewers PASS, 8/8 mutations green) shipped a defect that the CPO found by reading the
output list. Round 1 here found a second one of the same shape — a guard tested in isolation but
not where it runs. Testing the unit is not the same as testing the thing people execute.

## scope-auditor
VERDICT: PASS
risks_checked:
- Confirmed the two changed paths (`tests/test_cleanup_orphan_relations.py`,
  `.claude/task/acceptance_evidence.md`) are both already in `contract.md`'s `scope_paths`, and
  `scripts/cleanup_orphan_relations.py` is unchanged — re-verified by reading the new test against
  the code I already reviewed; no production logic moved.
- Read the new test `test_main_does_not_drop_a_udf_calling_view_in_phase_broken` directly: it
  drives `cleanup.main("broken", confirm=True, ...)` against a fake client seeded with one
  genuinely-broken orphan and one UDF-resolving orphan (`mart_fixture_index`), and asserts
  `client.deleted == [("staging", "really_broken")]` while `mart_fixture_index` survives. This
  closes exactly the gap platform-reviewer named (routines fetched/threaded only in `main()`,
  previously untested end-to-end) without introducing any new mechanism, dependency, or threshold —
  it is a test-only addition exercising existing wiring.
- The `routines=` kwarg on `_FakeClient` was already present in the hash I passed (I read it in the
  original diff); this delta only adds a call site that supplies real values instead of relying on
  the default, which is consistent with "no production code changed."
- No change to `contract.md`, `escalations.log`, or any decision field — the §10 reservations
  (whether to drop `mart_fixture_index`, whether to wire a recurring check) and the threshold
  declarations I already checked against the code stand unaltered since the code is byte-identical.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Confirmed `test_main_does_not_drop_a_udf_calling_view_in_phase_broken`
  (tests/test_cleanup_orphan_relations.py:532-572) exists in the file on disk and in the
  regenerated `review_input.patch`, and traced it fully: it builds a `_FakeClient` via the
  constructor's `routines=` kwarg (previously dead in every `main()`-driving test, confirmed dead
  in round 1), sets up a manifest-owned `core.fct_fixture`, an orphan `marts.mart_fixture_index`
  view whose stored SQL references `fct_fixture` plus a `dbt_analytics.url_fixture_slug(...)` call,
  and a genuinely orphan `staging.really_broken` view over a missing raw table — then runs
  `cleanup.main("broken", confirm=True, ...)` and asserts
  `client.deleted == [("staging","really_broken")]` and that `mart_fixture_index` survives.
- Verified this is the correct end-to-end path through the exact lines I flagged in round 1
  (`scripts/cleanup_orphan_relations.py:378-379`, `routines = list_routines(client)` then threading
  `routines` into `classify(...)`): the test's fixture data forces `mart_fixture_index` to be an
  orphan (not manifest-owned) and its UDF reference to matter, so reverting either of those two
  lines would put it in `broken` and it would be dropped by `--phase broken --confirm`, failing the
  `in client.relations` assertion. This is not a call-level unit test of `classify()` or
  `list_routines()` in isolation (which the round-1 gap was about) — it drives the real operator
  entry point.
- Cross-checked the manifest/orphan bookkeeping in the new test: `_model("fct_fixture",
  schema="core")` correctly lands `("core","fct_fixture")` in `expected`, so it is excluded from
  `orphans`, leaving exactly `mart_fixture_index` and `really_broken` as the two orphans
  `classify()` has to split — matching the assertions.
- Counted `def test_` occurrences in the updated test file: 29, matching the reported "29 passed."
- Re-read the regenerated `review_input.patch` diff for `tests/test_cleanup_orphan_relations.py`
  directly (not just trusting the coordinator's description) to confirm the new test's body matches
  what was described, byte for byte, including the docstring's own claim that the same mutation left
  every other test green — consistent with my round-1 finding.
- No other change in this round's delta beyond the one new test and its supporting fixture data;
  the production script (`scripts/cleanup_orphan_relations.py`) is unchanged from the version I
  already reviewed and passed on every other axis (routine/relation separation, `resolves()`
  signature and call sites, dependency pinning, docstring accuracy, dry-run/interruption safety).

## escalations
(none)
