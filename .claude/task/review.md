# Review — fix/897-pace-production-ingest — 2026-08-03

branch: fix/897-pace-production-ingest
diff_sha256: 19be579ebea19c09b24353fadf976f715ab0eadac61db5f7e37db9b75f52cbe3

rounds: 1
# Required reviewer set computed from `.claude/review_routing.json` for the staged paths:
# `ingestion/**` routes `data-engineer-reviewer`, `tests/**` routes `platform-reviewer`, and
# `scope-auditor` is always-on. No routing row matches `docs/operations_guide.md` or
# `docs/api_football_ingestion_blueprint.md`. The commit is NOT artifact-exempt, because
# `contract.md` is never artifact-exempt (F10/#409).

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope containment: every file in the diff is listed in `scope_paths`; no file outside it was edited.
- Cost decision (§10): one RECURRING COST declared and approved with measured evidence (wall-clock
  1.55x, ~3.4x headroom under GitHub's 6h default, daily freshness preserved, API budget at 10% of
  quota). CPO authority recorded in `escalations.log` dated 2026-08-03.
- `impact_map` requirement for the structural surface `ingestion/api_football/settings.py`: present
  as an evidenced SHORT FORM with a complete call trace (one read site, one caller, one call site, no
  dbt lineage). Not a claim of triviality.
- Doc-sync: both touched docs are updated in the same branch to match the code.
- Scope drift: confirmed the out-of-scope edit to the blueprint cost-model bullet was reverted, and
  the stale "20-50 API calls total" estimate appears as unchanged context in the diff, not as an
  added line.
- Test pinning: the new tests reproduce production exactly and fail on the pre-fix value.
- Appendix A anti-patterns A1 to A6: none detected. No invented metric, no new mechanism, no
  coverage-cut masquerading as a fix, no credential in the diff.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- `settings.py` changes only the `full`-profile `API_FOOTBALL_REQUEST_PAUSE_MS` default from `"0"` to
  `"250"`; no other entry in the setdefault bundle moved, and `os.environ.setdefault` semantics are
  preserved so an explicitly set value still wins.
- Re-traced the consumer chain independently of the contract's claim: `quota.py:99`
  `_request_pause_seconds` to `quota.py:108` `_throttle` to `http_client.py:51`, called once per
  successful `fetch_json` response. Matches the `impact_map` exactly; no other read site exists.
- Economy profile genuinely untouched: `_apply_ingest_profile_defaults` returns early for
  `default`/`economy`/`free`, so the variable stays unset and the 6.6s free-tier fallback stands.
- `docs/operations_guide.md`, the profile docstring and the profile log line all now say 250 and none
  still says 0, so no stale doc/code contradiction survives the diff.
- Blueprint §4: the new Ultra row is stated as measured from response headers rather than asserted,
  and the 250ms/240-per-minute arithmetic is consistent with `quota.py`'s actual pause value.
- Confirmed no workflow sets `API_FOOTBALL_INGEST_PROFILE` or `API_FOOTBALL_REQUEST_PAUSE_MS`, so
  production really does inherit the default by omission, and no `timeout-minutes` is set.
- Data-loss potential: the diff adds a `time.sleep()` and touches no writer, no BigQuery call, no
  parse or merge logic, no schema and no grain. It cannot duplicate, truncate or drop rows.
  Completeness only improves as provider rejections fall.
- Confirmed only the new test file calls `_apply_ingest_profile_defaults()` directly, so the
  module-local autouse fixture fully contains the env leak and no other test file needs it.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Independently re-derived the "4 of 7 fail on revert" claim from the code rather than trusting the
  narration: with the default back at `"0"`, `test_production_config_is_paced`,
  `test_explicit_full_profile_gets_the_blueprint_pause`,
  `test_profile_aliases_get_the_blueprint_pause` and `test_sets_the_documented_millisecond_value`
  fail, while the three override and economy tests correctly stay green because they do not depend on
  the default.
- Override and economy paths are both covered and match the real branching in `settings.py` and
  `quota.py`.
- Env-var leak checked for scope, not just presence: the autouse fixture is file-local, and no
  `tests/conftest.py` exists, which is correct because the leak path was module-boundary leakage via
  `os.environ.setdefault`. Also checked `python-ci.yml` and `requirements.txt` for a random-order
  plugin that would break the file-order assumption behind the bug: none present, so the fix holds in
  CI too.
- Operational consequence: `dbt-scheduled.yml` sets neither profile variable at its ingestion step,
  so production inherits the new 250ms default as claimed, and no `timeout-minutes` exists anywhere in
  that file. `ci-data-build.yml`'s ingestion steps inherit the same default but are bounded to newly
  added leagues, so no material risk.
- Re-run and interruption safety: no script, hook or workflow step changed. The pause is read fresh
  via `os.getenv` on every call with no cached or on-disk state, so double-run and mid-run-death
  behaviour is unaffected.

## escalations
(none)
