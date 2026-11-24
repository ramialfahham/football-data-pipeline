# Task contract — reviewer standard and round loop (#345, MR 1)

objective: >
  Reviewers judge against a written standard and report every finding in one pass, each with its
  class, every place it occurs and a severity (blocking or nit). The builder fixes the whole class
  with a test that fails before the fix; a re-review after a FAIL sees only the fix diff and the
  reviewer's own findings. The round cap is one rule in working_agreement.md §2 and §10. The
  commit gate and its CI backstop check what a machine can: severity and class on every finding,
  no FAIL from nits, and a `## fixes` entry with its test after round 1.
refs: "#345 (MR 1 of 3: reviewer standard and round loop)"

scope_paths:
  - .claude/agents/analytics-engineer-reviewer.md
  - .claude/agents/bi-analyst-reviewer.md
  - .claude/agents/cto-reviewer.md
  - .claude/agents/data-engineer-reviewer.md
  - .claude/agents/football-analytics-expert-reviewer.md
  - .claude/agents/platform-reviewer.md
  - .claude/agents/scope-auditor.md
  - .claude/agents/seo-expert-reviewer.md
  - docs/working_agreement.md
  - .claude/hooks/git_discipline.py
  - scripts/check_task_artifacts.py
  - .claude/task/REVIEW_TEMPLATE.md
  - tests/test_reviewer_standard.py
  - tests/test_governance_hooks.py
  - tests/test_sentence_length_in_docs.py
  - .claude/task/345-reviewer-standard/contract.md
  - .claude/task/345-reviewer-standard/review.md
  - .claude/task/345-reviewer-standard/review_input.patch
  - .claude/task/345-reviewer-standard/acceptance_evidence.md

protected_override: >
  .claude/agents/*.md and .claude/hooks/git_discipline.py: the redesign in issue #345, MR 1,
  approved in chat, 2026-11-24. The MR head lists both as locked files; the merge is the approval.

impact_map: >
  writers: none; no table or model. The protected paths are the eight reviewer briefs and
  `.claude/hooks/git_discipline.py`.
  downstream: the briefs are read only when a reviewer subagent is spawned (no code parses them
  except `tests/test_governance_hooks.py`, whose identical-section test moves to
  `tests/test_reviewer_standard.py`, and the two doc pins in `tests/test_sentence_length_in_docs.py`
  and `tests/test_no_decision_history_in_docs.py`, which the edits must not raise).
  `git_discipline.py` fires on every Bash PreToolUse (`.claude/settings.json`) and is imported by
  `.claude/hooks/task_contract_gate.py`, `scripts/check_task_artifacts.py` (CI job
  `validate:governance`, `.gitlab-ci.yml` line 458), and three test files
  (`grep -rln "import git_discipline\|git_discipline as"`). The new `_findings_gate` is called by
  `_commit_gate` and by `check_task_artifacts.main`; nothing else changes.
  layer_rules: the hook fails open on its own exceptions (existing handler); the CI backstop fails
  closed. The new check reuses one function in both, like `_rounds_gate`.
  deploy_order: none; `glab mr list` shows no open MR. A branch that merges main after this
  lands is checked by the new rules on its next commit and pipeline: a `review.md` finding without
  `[blocking]`/`[nit]`, or `rounds:` above 1 without `## fixes`, is refused.
  blast_radius: every future review round. No data, model, page or cost changes.

depends_on:
  - "none: gitlab/main f78a3cf5, no open MR"

shared_files:
  - "none: no design baseline or shared fixture changes"

approved_design:
  - "none: no page output changes"

decisions_taken: >
  The rule text is the MR 1 list of issue #345, approved in chat, 2026-11-24; the changed
  working_agreement.md sentences are quoted in the MR head for approval by the merge.
  No new mechanism: `_findings_gate` is a new check inside the existing commit gate and its CI
  backstop, both named in the issue's How step 1. No recurring cost. The `rounds_cap_override:`
  key stays; it now records the CPO's approval of a further round. The cap across sessions is a
  procedural rule; no gate counts rounds across folders.
  Sentences beyond the issue's own words, each there to make the approved rules agree, and each
  quoted in the MR head for the CPO's approval by the merge: a checklist item that says FAIL is
  blocking only when its breach falls in one of the five classes; a verdict with only nits is a
  PASS whose nits go on the issue; a wording rule a gate checks is the gate's, any other wording
  breach a nit; a new session or branch for the same work continues the count; at the cap the rest
  is split off into its own issue; the override reads `approved in chat, <date>`; a round that
  followed only PASS verdicts records `- none: <why>` under `## fixes`; a fix test lives where the
  repo runs tests: `tests/**/test_*.py`, `dbt_project/tests/**.sql` or `site_v2/**/*.test.mjs`
  (swept with `git ls-files`; dbt schema tests and `unit_tests:` are not fix tests). The after-PASS
  re-review and the too-large refusal restate the existing §2 rule.

decisions_reserved:
  - "none: the rule text is the approved MR 1 design; any sentence beyond it goes to the coordinator"

acceptance_criteria:
  - "AC1 Every reviewer brief ends with one identical `## Reviewer standard` section that binds §2 Cross-Examination, and no brief keeps the open-hunt sentence. Test: tests/test_reviewer_standard.py::test_every_brief_ends_with_the_identical_standard and ::test_no_brief_keeps_the_open_hunt."
  - "AC2 §2 states the standard: acceptance criteria, checklist and Appendix A; one pass; class and every place; blocking or nit with the five blocking classes; a nit never fails a round; the whole class fixed with a test that fails before the fix; a re-review after a FAIL gets only the fix diff and the reviewer's own findings; a new blocking finding on an unchanged line needs a concrete failing case or becomes a follow-up issue. Test: ::test_section_2_states_every_rule."
  - "AC3 §2 and §10 state one cap rule: rounds per issue across sessions, split at the cap, a further round the CPO's; the old 'bring the open findings to the CPO' sentence is gone. Test: ::test_the_cap_is_one_rule."
  - "AC4 The scope-auditor's writing-standards item makes a breach a nit. Test: ::test_a_wording_breach_is_a_nit."
  - "AC5 The commit gate and the CI backstop refuse a finding without `[blocking]` or `[nit]` and a class. Tests: ::test_gate_refuses_a_finding_without_severity_and_class (a missing separator included), ::test_ci_backstop_refuses_the_same_review, ::test_gate_refuses_when_the_branch_paths_cannot_be_listed."
  - "AC6 A PASS may carry nits; a PASS with a blocking finding is refused; a FAIL with only nits is refused with the nit rule. Tests: ::test_a_pass_with_nits_commits, ::test_a_pass_with_a_blocking_finding_is_refused, ::test_a_fail_of_nits_is_refused_with_the_nit_rule."
  - "AC7 With `rounds:` above 1, `review.md` needs `## fixes` entries, each naming a test file the branch changes (`tests/**/test_*.py`, `dbt_project/tests/**.sql` or `site_v2/**/*.test.mjs`), or the one entry `- none: <why>` for a round that followed only PASS verdicts; otherwise refused. Tests: ::test_a_fix_naming_a_file_that_is_not_a_test_is_refused, ::test_every_test_location_the_repo_runs_is_a_fix_test, ::test_a_fix_test_the_branch_does_not_change_is_refused, ::test_a_round_after_a_pass_commits_with_a_none_entry, ::test_a_none_entry_beside_a_fix_is_refused, ::test_round_two_without_fixes_is_refused, ::test_a_fix_whose_test_is_not_in_the_branch_is_refused, ::test_round_two_with_a_tested_fix_commits, ::test_a_fixes_entry_without_its_sweep_is_refused, ::test_a_fix_test_missing_on_disk_is_refused, ::test_ci_backstop_accepts_a_tested_fix."
  - "AC8 The review template's finding and fixes lines pass the gate. Test: ::test_the_template_examples_pass_the_gate."

done_when:
  - "`python -m pytest tests/test_reviewer_standard.py` passes; run before the code, it fails."
  - "`python -m pytest` (full suite) passes."
  - "`python scripts/ci_local.py --mr` passes."

amendments:
  - "2026-11-24: + tests/test_sentence_length_in_docs.py — authority: that test's own rule (the pin only moves down); content: each reviewer brief's pin drops by one, since one replaced sentence in each was over the limit."
  - "2026-11-24: AC5 and AC7 — authority: the round-1 FAIL verdicts (fix-test location, unpinned gate conditions, a round after a PASS); content: AC7 names the test locations and the `none:` entry, AC5 and AC7 list the added tests."
  - "2026-11-24: AC7 — authority: the round-2 FAIL verdicts (the test locations left out the site's node tests); content: AC7 adds `site_v2/**/*.test.mjs` and its test. The rule sentences these amendments add are declared in decisions_taken for the CPO's approval by the merge."
