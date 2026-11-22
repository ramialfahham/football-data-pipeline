# Review — claude/36-crest-hosting — 2026-11-22

diff_sha256: 56b38dd3a7c435e4e51f0a1cdb21b5ec3d5bbdba8a24a219ddd0db028fa74bb2

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is in scope_paths and the contract reserves the path, the bucket name, the mechanism, the provider downloads and Pillow for the MR head and the CPO's merge; nothing else crosses §10.
- The empty state table is a prod DDL write by the CPO, recorded as deploy_order step 0 and in the runbook, not a builder action.
- Round 3 delta: the copy-then-commit state entry, the skip reason and one doc word add no mechanism, call or cost.

## cto-reviewer
VERDICT: PASS
risks_checked:
- The private bucket, the raw state table, the crest phase and the site sync step are declared mechanisms; the added dependency Pillow and the direct pin of google-cloud-storage are pinned in both requirements files.
- Recurring cost is declared in the contract (a nightly BigQuery read of about 266 MB, about 475 image requests a night, Firebase transfer measured after the first fill); the two gcloud commands grant one role on one private bucket.
- No change in this reviewer's territory since its round 2 PASS: the later changes are error handling inside the declared phase.

## platform-reviewer
VERDICT: PASS
risks_checked:
- sync_crests.py fails closed on any error but a missing bucket, the site job runs the sync between the export and the build, firebase.json adds the 7-day cache, and the built-pages check fails a full export whose crest paths are not files.
- Round 3 delta: the failed-write test pins the old entry kept and the unreadable-counter test pins the skip reason; each fails if its behaviour is reverted.
- Pins match across both requirements files and the GcsStore class is tested with a fake client.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- The phase never fails the ingest, skips on an exhausted API quota, a missing bucket or an unreadable counter, records the pre-flight only after at least five answered images and a readable counter, and isolates each image's failure.
- The state is one appended whole snapshot written in a finally, a failed write keeps the old entry, and the state table is created before the bucket check; docs/data_contract.md documents the payload.
- Round 3 delta: the copy-then-commit change holds on the missing, unchanged and stored paths.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Staging reads the declared source plainly and the base model filters to stored objects; dim_team and dim_league publish a site path only where an object is stored, with no fan-out and null before the first fill.
- The singular test and the two provider-host tests are present, and the stale crest and logo descriptions say path on this site.
- No change in this reviewer's territory since its round 2 PASS.

## escalations
(none)
