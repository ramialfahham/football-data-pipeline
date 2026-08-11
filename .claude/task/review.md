# Review — feat/39-nightly-freshness-alert — 2026-08-10

diff_sha256: 93a4870de38230c01920a43165ece741009ac3b14ea802afeb614f6ffe60c456

rounds: 5

rounds_cap_override: CPO authorised twice, explicitly and separately — "run round 4" and then
"run round 5" — each time so a live platform-reviewer FAIL could be fixed and re-verified rather
than accepted on the builder's word. The cap exists to stop grinding; here every extra round was
paid for by a real defect the reviewer found and the builder had missed, including one the
builder's own sweep was structurally incapable of seeing.

<!--
Round history. Every FAIL was the builder's, and the design changed mid-task on a CPO ruling.
  r1  scope-auditor FAIL · platform FAIL · cto PASS
  r2  all three FAIL — the same defect, found independently
  r3  scope-auditor PASS · cto PASS · platform FAIL
  r4  scope-auditor PASS · platform FAIL          (cap override #1)
  r5  platform PASS                                (cap override #2)

`cto-reviewer` is NOT routed to these paths by .claude/review_routing.json — no row covers
`deploy/**` or a monitoring surface. Spawned deliberately because this task declares a NEW
MECHANISM and touches recurring cost, which are its thresholds and which no routing row finds.

Verdicts below are each reviewer's LAST, all against the final diff:
  scope-auditor r4 · cto r3 · platform r5.
cto's r3 PASS predates two later changes, both confined to `deploy/nightly/README.md` and
`alert-policy.json` documentation strings and a new test — no cost claim, no mechanism, nothing
in its remit moved. Stated rather than glossed, because the hash binds all three to this diff.
-->

## scope-auditor
VERDICT: PASS
risks_checked:
- Round-2 finding (contract and README describing a reverted mechanism as shipped) re-checked against current text: `contract.md` objective, impact_map and cost profile, and `README.md` "Operating it" all now state the entrypoint is untouched, and cite `git diff main -- deploy/nightly/entrypoint.sh` being empty as the check. Confirmed no hunk in `review_input.patch` touches that file. Cured.
- §10/§11 authority chain for the mid-task design change: `contract.md` `decisions_taken` and the 2026-08-10 `escalations.log` entry both record a proper escalation with three paths and a recommendation, and the CPO's contrary choice ("Build a BigQuery-backed check instead"). The `amendments:` entry cites that ruling for the two added scope paths.
- Recurring-cost claim verified against implementation: `table_age_hours()` calls only `client.get_table()`, a metadata call with no query job — the "free" claim holds.
- Numeric claims against source of truth: "warn 30h / error 54h on 8 of the 11 sources" checked against `sources.yml` — exactly 8 tables carry a `freshness:` block. Consistent across contract, README, JSON comments and the script docstring.
- Doc/JSON consistency after the rename: README's quick-reference table and its `display_name` curl filter both match `alert-policy.json`'s actual `displayName`; the bridge policy `fdp-nightly stale (no success in 25h)` is disclosed as deployed-but-unversioned rather than papering over drift.
- Scope: every file in the patch is listed in `scope_paths`; the delta stayed inside it.
- Credentials sweep across the full diff: only `gcloud auth print-access-token` (a dynamic fetch, not a stored secret) and Secret Manager references by name. Nothing credential-shaped introduced.

## cto-reviewer
VERDICT: PASS
risks_checked:
- All five round-2 defect locations re-read verbatim and confirmed corrected: `objective` (no in-pipeline half), `impact_map` "what changes in the pipeline" (NOTHING, with the empty-diff check named), `impact_map` cost profile and `decisions_taken` RECURRING COST (nightly cost unchanged, quiet night still $0), and `done_when` (break-it list now matches assertions that exist).
- The "11 vs 8" discrepancy: 11 sources total, 8 with thresholds, 3 deliberately without — arithmetically consistent everywhere it is stated; no surviving place asserts a conflicting total.
- Recurring cost now verifiable from the contract's own words without re-deriving from code: ~24 Cloud Run executions/day of a few seconds at 1 vCPU / 512 MiB, metadata calls unbilled, policies and Scheduler free. One number, stated identically in both places it appears.
- New mechanism authority: the second Cloud Run Job and its hourly schedule were escalated and answered by the CPO, so the mechanism and cost thresholds were declared with authority rather than smuggled.
- Proportionality: Cloud Monitoring is native to the GCP project already in use since Stage 1 — no third-party paging service introduced. The "watcher's watcher" regress is explicitly declined at one level, which is the right boundary rather than an infinite chain.
- IAM: the `run.invoker` binding is resource-scoped to the `fdp-freshness` job, not project-wide, consistent with the restraint established in Stage 1. No new dependency; `requirements.txt` untouched.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round-4 defect re-read verbatim at `alert-policy.json:131`: the sibling policy is now named correctly ("or uncheckable") and the "users affected" claim is attributed to exit 1 only, with exit 2 stated separately as "lost the ability to tell". Confirmed by direct read, not from the builder's report.
- Fourth-instance sweep: `README.md` in full (all `fdp-*` occurrences), `entrypoint.sh`, `scripts/check_raw_freshness.py`, `.gitlab-ci.yml` and `.github/workflows/` — zero surviving references to any stale policy name. No fourth instance exists.
- The new guard is real, not decoration: hand-derived its backtick-extraction regex against the actual JSON bytes — exactly two spans exist file-wide, both correctly classified. Reinstating the round-4 wording changes the captured string to one absent from all three allowlists, failing the assertion.
- `JOB_NAMES` allowlist examined as a hiding spot: it matches only by exact full-string equality to a bare job name, so it could mask only a reference truncated to exactly `fdp-nightly` or `fdp-freshness`. No such reference exists. A narrow, currently-inert gap — named rather than manufactured into a finding.
- `KNOWN_UNVERSIONED` checked against the one place that string appears (`README.md`), matching exactly; the JSON deliberately omits that policy as documented.
- (r3, still standing) The masked "cannot check" test is cured: `_install_healthy_bigquery` stubs the client so `main()` can only return 2 via the branch under test. Traced the named regression by hand — with the stub it returns 0 and the assertion fails, with or without GCP credentials in CI.
- (r3, still standing) The sentinel's silent failure modes each have a test that goes red under a single production edit: staleness comparison disabled, "nothing to check" returning 0, `SOURCES_YML` rebound as an import-time default, and an unreadable table treated as fresh.
- (r3, still standing) `evaluate()`'s stale/warn/boundary split verified — warn does not escalate to a failure, and the boundary is strictly greater-than, so an exactly-at-threshold age does not page daily.

## escalations
- question: The CPO chose a 30h staleness threshold. Cloud Monitoring rejects it — `conditionAbsent` caps at 23h30m, MQL `absent_for` at 1d1h, and for a daily job anything at or below 24h fires before every run. Three paths were put to the CPO: (A) keep 25h, the platform ceiling, with ~1h of drift tolerance — the builder's recommendation; (B) disable staleness detection until #33 item 14 shrinks the run; (C) build a BigQuery-backed check that measures data age directly and is not subject to the cap.
  CPO ANSWER: "Build a BigQuery-backed check instead." — path C, against the builder's recommendation. Recorded in `.claude/task/escalations.log`, 2026-08-10.
