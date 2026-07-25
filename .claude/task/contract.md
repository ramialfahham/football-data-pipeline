# Task contract — handover refresh (Firebase deploy live + verified, export cost measured)

> Written on a CLEAN tree (branch `docs/handover-firebase-live` off main at b15e4fb).
> Bookkeeping: refresh the single handover contract to current state. No code, no model change.

objective: >
  Refresh .claude/active_work.md to the true current state after this session: the Firebase
  Hosting deploy is LIVE and VERIFIED (manual dispatch, `.web.app`, not public) — real team pages
  render distinct real data (Man Utd, Liverpool); the two GCP prerequisites (enable Firebase +
  create the site; grant roles/firebasehosting.admin to the deploy SA github-actions-dbt) are DONE;
  the per-run export scan cost was MEASURED at ~$0.002/run (~0.18 GiB, 15 queries) — negligible and
  within BigQuery's free tier, so the recurring run is unblocked on cost and only its trigger shape
  is left to decide; and PR #822 (per-agent review-fleet effort pins) merged. Keep the file CURRENT
  STATE ONLY and under 16,000 characters.

refs: >
  This session 2026-07-25. Deploy run 30151299421 (success, 12m41s). Live URL
  football-data-pipeline-gcp.web.app. Cost measured via region-eu INFORMATION_SCHEMA.JOBS_BY_PROJECT
  (export = non-dbt-labelled queries under the github-actions-dbt SA; the dbt build+test queries
  that share that SA must be excluded, or the number is off by ~100x).

scope_paths:
  - .claude/active_work.md

decisions_taken: >
  Pure bookkeeping. All facts recorded are already true (deploy succeeded, prereqs done, cost
  measured); this only writes them into the handover. No product, metric, naming or mechanism
  decision is made here.

decisions_reserved:
  - The recurring-run trigger shape (`workflow_run` on dbt-scheduled vs a later cron) and going
    public (custom domain, DNS, announcement) remain the CPO's open decisions — recorded in the
    handover as OPEN, not decided here. Cost is no longer a blocker for the recurring run (measured
    negligible); the trigger-shape choice is what is left.

done_when:
  - .claude/active_work.md reflects: Firebase deploy LIVE + verified; the two GCP prereqs DONE; the
    measured export cost (~$0.002/run, negligible); PR #822 merged. Stays under 16,000 chars.
  - ONE commit; review.md with scope-auditor PASS (the only required reviewer for this path);
    pushed with an explicit refspec; PR opened. The CPO merges.

amendments: (none)
