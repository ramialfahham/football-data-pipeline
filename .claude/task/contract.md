# Task contract — Remove decision history from the lint:python comment

objective: >
  The comment above `lint:python` in `.gitlab-ci.yml` carries history (a date, a reviewer, a token
  count, an MR number). Replace it with the one-line reason the job exists. Comment only; no
  behaviour change.
refs: >
  No issue: a comment-only change with no requirement (working_agreement §1 carve-out); the MR head
  says "No behaviour change". The rule it applies is `dbt_project/docs/engineering_standards.md`
  §1.2 (a comment says why; who, when, which reviewer and which MR live in git).

scope_paths:
  - .gitlab-ci.yml
  - .claude/task/**
  - docs/tracker/**

protected_override: >
  `.gitlab-ci.yml` is a protected path. Authority: his go on 2026-09-24 in chat, "do it", to the
  proposal to delete the history line from the `lint:python` comment in a tiny MR. The commit
  message and the MR head repeat this under `Locked files`; his merge is the approval
  (working_agreement §11).

impact_map: >
  writers: none. No raw writer, model, seed, export or site file.
  what fires it: nothing changes what fires; only YAML comment lines change, which GitLab and
  `yaml.safe_load` ignore. Job definitions, rules, scripts, images and anchors are byte-identical.
  what imports it: `tests/test_lint_config.py`, `tests/test_governance_hooks.py`,
  `tests/test_design_inventory.py`, `tests/test_ci_data_job_invariants.py`,
  `tests/test_persist_docs_policy.py` and `scripts/check_task_artifacts.py` parse the file; none
  reads comments.
  what stops being enforced if it is wrong: nothing; a comment enforces nothing.
  failure behaviour: unchanged.
  layer_rules: none. deploy_order: none. blast_radius: none; the parsed YAML is identical before
  and after.

decisions_taken: >
  The replacement keeps the one reason that is still true: ruff settles mechanical defects for
  free, so reviewers are spent on judgement. THRESHOLD DECLARATIONS: no new mechanism, no recurring
  cost.

decisions_reserved:
  - none open: a one-comment change approved as proposed.

done_when:
  - parsed `.gitlab-ci.yml` is identical before and after (`yaml.safe_load` compared)
  - the tests that parse `.gitlab-ci.yml` pass
  - blinded review PASS; MR open with "No behaviour change"; CI green

amendments: (none)
