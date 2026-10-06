# Task contract — validate:ui takes Node from Playwright, not apt

objective: >
  On the CI runner, apt in the validate:ui container rejects every Ubuntu mirror's signature, so
  nodejs never installs and the job's JavaScript syntax check fails on every UI MR. The same mirror
  index verifies from the dev machine, so the fault is on the box. The job already installs
  Playwright 1.63.0, which bundles a Node binary; put that on PATH instead of installing nodejs.

refs: >
  The red validate:ui on the merge request that strips the CPO's quotes from the non-core files.

acceptance_criteria:
  - validate:ui passes on the CI runner without apt

scope_paths:
  - .gitlab-ci.yml
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

protected_override: >
  Approved by the CPO in chat, 2026-10-06: validate:ui drops its apt-get line and puts the Node
  that Playwright already bundles on PATH, with the exact edit shown to him. Reading: the job's
  header comment, which says where its Node comes from, is corrected with it, so the file states
  the current setup.

impact_map: >
  writers: none; this is one before_script line of one CI job, validate:ui.
  readers: the job's own steps. Only the `node --check` loop calls node; Playwright and the design
  inventory run their own bundled driver either way (`grep -n "node" .gitlab-ci.yml` in the job).
  Nothing else in .gitlab-ci.yml, the hooks or the tests names the apt line
  (`git grep -n "apt-get install -y -qq nodejs"` returns only this line).
  when it runs: merge-request and main pipelines that change a UI path, and web pipelines;
  .gitlab-ci.yml is itself a UI path, so this MR's pipeline runs the job.
  what changes: the Node that checks syntax, from the apt nodejs package to Playwright's bundled
  Node (v24.21.0 on the dev machine; the same wheel version in CI). `node --check` only parses.
  deploy_order: none; no warehouse, data job or deployment is touched.
  blast_radius: validate:ui alone. If the path were wrong, `node` is not found and the job fails
  exactly as it fails today; no other job, dataset or page is affected.

decisions_taken: >
  Readings, under the delegation of 2026-10-02:
  - The PATH export sits in before_script, which runs in the same shell as script, so the
    syntax loop finds node without any other change.

  Threshold declarations. NEW MECHANISM: none; the job keeps its steps and loses one network
  dependency. RECURRING COST: none.

decisions_reserved:
  - None.

done_when:
  - validate:ui passes on this MR's pipeline on ci-runner-01.
  - pytest (whole suite) and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
