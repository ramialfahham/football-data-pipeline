# Review — ci/main-build-waits-for-nightly

diff_sha256: 63274e85810eee8baf7f642fbaa5234c73bff600c8132c6945bdc1190a5ed336

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- All paths in scope; the wait step is declared as the approved new mechanism, named with its date; no BigQuery cost.
- No product, metric, naming or URL decision; no credential or widened grant; the job comment is corrected in the same diff.
- Round 2 delta: the 90-minute deadline is a narrower reading of "up to the job's timeout", disclosed with its retry consequence; it fails closed.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Authority: protected_override names the approval and matches what was built; the impact map is real.
- Fail-closed: an API error or missing grant exits non-zero before dbt seed, the first prod write; the comment's false claim about the resource group is corrected, not weakened.
- No new dependency (google-auth arrives with the pinned BigQuery client); no recurring spend; runner time only.
- Round 2 delta: the deadline stands under the approval and makes the guard stronger; the request timeout fails closed.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL on the timeout landing during prod writes is closed: the wait exits 1 after 90 minutes, before any write, leaving 30 of the 120 minutes for a ~13-minute build; sleep-only counting drifts under 2 minutes.
- Round 1 FAIL on the unpinned wiring is closed: a test asserts auth < wait < first --target prod in data:build:main and the deadline inside the job timeout.
- Credentials from the gcp_auth file, imports from requirements.txt, the in-progress rule and the first page of executions checked; the script only reads, so re-runs are safe.

## escalations
(none)
