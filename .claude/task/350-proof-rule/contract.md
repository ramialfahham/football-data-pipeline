# Task contract — a review finding blocks only when proven; round cap of 2 (#350)

objective: >
  A reviewer's blocking finding names its proof: a failing test or a reproduction command. An
  unproven finding is a nit. The builder may close a finding it cannot reproduce under
  `## closed`, with the reason. After two rounds the approach is rethought and the work split; a
  further round is the CPO's. The commit gate and its CI backstop check each rule.
refs: "#350, the last piece of #348 (split off at its round cap); #349 follows separately"

scope_paths:
  - .claude/agents/analytics-engineer-reviewer.md
  - .claude/agents/bi-analyst-reviewer.md
  - .claude/agents/cto-reviewer.md
  - .claude/agents/data-engineer-reviewer.md
  - .claude/agents/football-analytics-expert-reviewer.md
  - .claude/agents/platform-reviewer.md
  - .claude/agents/scope-auditor.md
  - .claude/agents/seo-expert-reviewer.md
  - .claude/hooks/git_discipline.py
  - scripts/check_task_artifacts.py
  - docs/working_agreement.md
  - .claude/task/REVIEW_TEMPLATE.md
  - tests/test_reviewer_standard.py
  - tests/test_governance_hooks.py
  - tests/test_sentence_length_in_docs.py
  - tests/test_governance_doc_parity.py
  - tests/test_no_decision_history_in_docs.py
  - .claude/task/350-proof-rule/contract.md
  - .claude/task/350-proof-rule/review.md
  - .claude/task/350-proof-rule/review_input.patch

protected_override: >
  .claude/agents/*.md and .claude/hooks/git_discipline.py: the review-process redesign of issue
  #345, approved in chat, 2026-11-24, built as issue #350. The MR head lists both as locked
  files; the merge is the approval.

impact_map: >
  writers: none; no table or model. The protected paths are the eight reviewer briefs and
  `.claude/hooks/git_discipline.py`.
  downstream: `git_discipline._commit_gate` runs on every Bash PreToolUse (`.claude/settings.json`)
  and denies `git commit`; `scripts/check_task_artifacts.py` imports `git_discipline` and runs the
  same `_findings_gate`, now with `_closure_gate`, in CI job `validate:governance`
  (`.gitlab-ci.yml`). Other readers of review.md: `scripts/report_process_health.py` reads only
  `rounds:`; `.claude/hooks/stop_gate.py` and `.claude/hooks/host_fingerprint_gate.py` mention it
  in comments only (`grep -rln "review\.md\|VERDICT" --include=*.py`). `ROUND_CAP` is read by
  `_rounds_gate`, which `check_task_artifacts._rounds_error` calls. The briefs are read only when
  a reviewer is spawned; `tests/test_reviewer_standard.py` and `tests/test_governance_doc_parity.py`
  parse them, and `tests/test_sentence_length_in_docs.py` pins their long sentences.
  layer_rules: the hook fails open on its own exceptions (existing handler); the CI backstop
  fails closed. The removed global `VERDICT: FAIL` check is replaced per section, with a count
  backstop for a section a duplicate `## <name>` header hides.
  deploy_order: `glab mr list` shows no open MR. A branch whose review.md says `rounds: 3` meets
  the cap of 2 on its next commit and needs a recorded override.
  blast_radius: every future review round and every MR's CI. No data, model, page or cost change.

depends_on:
  - "none: gitlab/main e34b1683 carries !535, no open MR"

shared_files:
  - "none: no design baseline or shared fixture changes"

approved_design:
  - "none: no page output changes"

edge_cases: >
  One test per case, in tests/test_reviewer_standard.py unless named.
  Proof: P1 a blocking finding ending `| proof: <test file>::<test>` (a Python test, a dbt test
  file, a `.test.mjs`) passes the format check; P2 one ending `| proof: \`<command>\`` passes;
  P3 no proof, an empty proof, a `<placeholder>`, `none`, prose, a non-test path and a test id
  followed by prose are refused;
  P3b a placeholder in backticks is refused; P4 a nit needs no proof.
  Closing: P5 a `## closed` entry `- <reviewer> | <class> | <reason>` closes that reviewer's
  blocking finding of that class, and a FAIL whose blocking findings are all closed commits;
  P6 a FAIL with one of two classes closed is refused; P7 a closure naming no blocking finding
  of that reviewer, or of that class, is refused; P8 a closure with a placeholder reason, or not
  in the entry form, is refused; P9 a closed finding needs no proof; P10 the CI backstop agrees on
  P5 and P6; P11 a FAIL section hidden by a second section of the same name is refused, in the
  gate and in CI; P12 a `VERDICT: FAIL` written under `## closed` or `## fixes` is refused.
  Cap (tests/test_governance_hooks.py and tests/test_reviewer_standard.py): C1 `rounds: 2`
  commits; C2 `rounds: 3` without an override is refused and names the cap of 2; C3 with an
  override it commits.

decisions_taken: >
  The rules are issue #350's list, approved in chat, 2026-11-24; the changed sentences of
  working_agreement.md, the briefs and REVIEW_TEMPLATE.md are quoted in the MR head for approval
  by the merge.
  No new mechanism: the proof check and `## closed` are checks inside the existing commit gate
  and its CI backstop, named in the issue's How step 2.
  RECURRING COST: none. Fewer rounds per MR is the intent.
  Beyond the issue's words, each quoted in the MR head: the proof's form,
  `| proof: <test file>::<test>` or a command in backticks; the closure's form,
  `- <reviewer> | <class> | <reason>`; an unproven blocking finding is refused at commit until
  the builder records it as a nit or closes it; a FAIL hidden by a second section of the same
  name is refused, and §2's commit-gate list says so.
  The 400-line rule already stands in §2 from !535; this MR changes it not.

decisions_reserved:
  - "none: the sentences beyond the issue are declared above and quoted in the MR head; the CPO approves them by the merge"

acceptance_criteria:
  - "AC1 A blocking finding without a proof (a test file and test, or a command in backticks) is refused; a nit needs none. Tests: tests/test_reviewer_standard.py::test_a_blocking_finding_without_proof_is_refused, ::test_a_blocking_finding_with_proof_passes_the_format_check, ::test_a_nit_needs_no_proof."
  - "AC2 The builder closes a finding it cannot reproduce under `## closed` with the reason; a FAIL whose blocking findings are all closed commits, otherwise it is refused, in the gate and in CI. Tests: ::test_a_closed_fail_commits, ::test_a_closed_finding_needs_no_proof, ::test_a_partly_closed_fail_is_refused, ::test_a_bad_closure_is_refused, ::test_ci_backstop_agrees_on_closures, ::test_a_hidden_fail_is_refused, ::test_a_fail_outside_a_reviewer_section_is_refused."
  - "AC3 After two rounds the approach is rethought and the work split; a further round is the CPO's. The gate's cap is 2, and §2 and §10 say so. Tests: ::test_the_cap_is_one_rule, ::test_round_two_commits_and_round_three_needs_the_cpo."
  - "AC4 §2 and every brief's identical Reviewer standard state the proof rule and closing. Tests: ::test_section_2_states_every_rule, ::test_every_brief_ends_with_the_identical_standard, ::test_the_template_examples_pass_the_gate."

done_when:
  - "`python -m pytest tests/test_reviewer_standard.py tests/test_governance_hooks.py` passes; run before the code, the new tests fail."
  - "`python -m pytest` (full suite) passes."
  - "`python scripts/ci_local.py --mr` passes."

amendments: (none)
