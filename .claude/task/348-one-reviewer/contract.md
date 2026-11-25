# Task contract — review effort weighted by risk: tiers and the two-reviewer cap (#348, MR A)

objective: >
  Review effort follows risk. Text, copy and docs get no AI reviewer; a territory path (site pages,
  dbt, scripts, tests, the site build, the mock scripts) gets its one owner; a risk path (gates and
  their inputs, hooks, CI, cost, prod writes, ingestion) gets the owner and one specialist; no
  branch needs more than two reviewers. A
  branch's own tests and baselines add no reviewer. The commit gate and its CI backstop check the
  tiers; the CI backstop also checks the diff against scope_paths, the scope-auditor's first item.
refs: "#348, MR A of two; MR B (the proof rule, closing a finding, the round cap of 2) follows after this merges; #349 is separate and not built here"

scope_paths:
  - .claude/review_routing.json
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
  - docs/agent_guardrails.md
  - docs/north_star.md
  - docs/roles/platform_reliability.md
  - .claude/task/REVIEW_TEMPLATE.md
  - .claude/task/TEMPLATE.md
  - tests/test_review_tiers.py
  - tests/test_reviewer_standard.py
  - tests/test_governance_hooks.py
  - tests/test_governance_doc_parity.py
  - tests/test_sentence_length_in_docs.py
  - tests/test_no_decision_history_in_docs.py
  - tests/test_task_folders.py
  - tests/test_hooks_resolve_worktree.py
  - .claude/task/348-one-reviewer/contract.md
  - .claude/task/348-one-reviewer/review.md
  - .claude/task/348-one-reviewer/review_input.patch

protected_override: >
  .claude/review_routing.json, .claude/agents/*.md and .claude/hooks/git_discipline.py: the
  redesign in issue #348, approved in chat, 2026-11-24. The MR head lists the three as locked
  files; the merge is the approval.

impact_map: >
  writers: none; no table or model. The protected paths are `.claude/review_routing.json`, four
  reviewer briefs (bi-analyst, cto, platform, scope-auditor) and `.claude/hooks/git_discipline.py`.
  downstream: `review_routing.json` is read by `git_discipline._load_routing` (commit gate, every
  Bash PreToolUse via `.claude/settings.json`), `scripts/check_task_artifacts.py` (CI job
  `validate:governance` in `.gitlab-ci.yml`), `scripts/report_process_health.py` (read-only
  report, uses `always` and `paths` with `.get`, so an empty `always` is valid) and the tests
  `test_governance_hooks.py`, `test_governance_doc_parity.py`, `test_task_folders.py`,
  `test_hooks_resolve_worktree.py`, `test_research_fix_merge_hook.py`, `test_tracker_snapshot.py`
  (`grep -rln "review_routing\|import git_discipline" --include=*.py`). `git_discipline` is imported
  by `task_contract_gate.py` (`_base_commit` only) and `check_task_artifacts.py`. The new
  `_tier_gate` and `_is_companion` are called by `_commit_gate` and `check_task_artifacts.main`
  (through `_required_reviewers`); nothing else changes. The briefs are read only when a reviewer
  is spawned; `test_reviewer_standard.py`, `test_governance_doc_parity.py` and the two doc pins
  parse them.
  layer_rules: the hook fails open on its own exceptions (existing handler) and on a routing file
  without `tiers` or `max_reviewers`; the CI backstop fails closed. `tests/test_review_tiers.py`
  pins both keys on the real routing file, so dropping one fails CI.
  deploy_order: `glab mr list` shows no open MR. Branches in progress meet the new rules on their
  next commit: a branch needing three reviewers (for example a page, its export and a mart) is
  refused and split; a branch whose diff leaves `scope_paths` reddens `validate:governance`.
  blast_radius: every future review round and every MR's CI. No data, model, page or cost change
  beyond the reviewer spawns in decisions_taken.

depends_on:
  - "none: gitlab/main b3722fd5, no open MR"

shared_files:
  - "none: no design baseline or shared fixture changes"

approved_design:
  - "none: no page output changes"

tier_map: >
  The tier of a path is the highest tier glob it matches in `tiers` of review_routing.json; a path
  matching none is text. Reviewers come from `paths` (fnmatch, union of matching rows). Checked
  against every tracked file by tests/test_review_tiers.py (`git ls-files`, full output).

  | Tier | Paths | Reviewers |
  |---|---|---|
  | risk | 13 of the 14 protected paths | platform-reviewer + cto-reviewer |
  | risk | `docs/design/components.yml`, the component registry a page registers its parts in | bi-analyst-reviewer + cto-reviewer |
  | risk (dependencies, lint) | `*requirements*.txt`, `site_v2/package.json`, `site_v2/package-lock.json`, `.python-version`, `.nvmrc`, `.ruff-ci.toml` | platform + cto |
  | risk (dependencies, lint) | `dbt_project/packages.yml`, `dbt_project/package-lock.yml`, `dbt_project/.sqlfluff` | analytics-engineer + cto |
  | risk (gates) | `scripts/check_*.py`, `scripts/security/**`, `scripts/merge_ready.py`, `site_v2/scripts/check-*.mjs`, and the scripts CI runs as a check or a data-build guard: `scripts/sync_metric_docs_blocks.py`, `scripts/sync_dbt_vars.py` (the registry check imports it), `scripts/get_new_league_codes.py`, `scripts/wait_for_nightly.py`, `scripts/stale_prod_nodes.py` | platform + cto |
  | risk (gate input) | `.claude/skills/research-provider-errors/SKILL.md`: its site table is the host allowlist of `scripts/check_research_fix_mr.py`, the self-merge route for correction seeds | analytics-engineer + cto |
  | risk (design gate inputs) | `docs/wireframes/block_standard.md` and `docs/wireframes/approved_designs.yml` (read by the mock and page checks), `design-mocks/check_*.py` | bi-analyst + cto |
  | risk (CI, deploy) | `scripts/ci_local.py`, `deploy/**`, `Dockerfile`, `.dockerignore`, `.gcloudignore`, `.gitleaks.toml`, `.gitleaksignore` (untracked today; gitleaks reads it), `.pre-commit-config.yaml`, `.githooks/**` | platform + cto |
  | risk (prod writes) | `scripts/drop_*.py`, `scripts/diagnostics/**`, `scripts/cleanup_orphan_relations.py`, `scripts/clear_apif_ingest_lock.py`, `scripts/refetch_from_provider.py`, `scripts/compare_fixture_statistics_live.py`, `scripts/nightly_site_deploy.py`, `scripts/sync_crests.py` | platform + cto |
  | risk (prod writes) | `scripts/export_*.py` | analytics-engineer + platform |
  | risk (ingestion) | `ingestion/**` (`ingestion/*.py` row; its `requirements.txt` by the requirements row) | data-engineer + cto |
  | risk (cost) | `docs/competition_registry.yml`, `dbt_project/seeds/competition_registry.csv` | data-engineer + analytics-engineer |
  | risk (metric definitions) | `dbt_project/seeds/metric_catalogue.csv` | analytics-engineer + football-analytics-expert |
  | territory | `site_v2/src/**`, `design-mocks/*.py` | bi-analyst |
  | territory | `dbt_project/**` | analytics-engineer |
  | territory | `scripts/**`, `tests/**`, the rest of `site_v2/**`, `.sqlfluff`, `.gitattributes`, `.gitignore` | platform |
  | text | everything else: `docs/**` but the three above, `design-mocks/**` but its scripts, `site/**` (the frozen legacy site; its CI jobs check JSON syntax and i18n keys, and nothing deploys it), `.claude/skills/**` but the research skill, `.claude/task/**`, `.claude/launch.json`, `.cursor/rules/**`, `.github/**` but workflows, `.gitlab/**`, `.vscode/**`, root `*.md`, `LICENSE`, `.env.example`, `.gate-verification-touchfile` | none |

  Companions (`companion_paths`): `tests/**`, `dbt_project/tests/**`, `site_v2/**/*.test.mjs`. A
  companion adds no reviewer to a branch whose other paths need one; a branch of only companions
  and text needs their owners. A companion in the risk tier (`tests/test_design_inventory.py`,
  `site_v2/scripts/check-*.test.mjs`) keeps its reviewers. Every other test is a companion, a
  gate's or hook's own test included: changed beside its gate it adds no reviewer, and changed
  alone platform-reviewer reviews it, as on main.

edge_cases: >
  One test per case, in tests/test_review_tiers.py.
  Paths and tiers: E1 every tracked file's reviewer count equals its tier's; E2 a path under a
  territory root with no row (0 reviewers) is refused; E3 a path in both a risk and a territory
  glob is risk; E4 no tracked file gets three reviewers (the ingestion requirements file is the
  case); E5 fnmatch `*` crosses `/`: `scripts/check_*.py` misses `scripts/security/check_no_secrets.py`
  (own row), `site_v2/scripts/check-*.mjs` takes the gates' own `.test.mjs` files, `ingestion/*.py`
  takes nested loaders, `Dockerfile`, `.gitignore` and `.sqlfluff` match the root only
  (`deploy/site/Dockerfile`, `site_v2/.gitignore`, `dbt_project/.sqlfluff` have their own rows);
  E6 a rename counts both its old and new path (`--no-renames`), so moving a hook into `docs/`
  keeps its reviewers; E7 a deleted path keeps its tier; E8 a Windows backslash path is
  normalised; E9 a branch needing three reviewers is refused with the split rule; E10 a text-only
  branch commits and passes CI with no review.md; E11 a text plus territory branch needs only the
  owner; E12 the gate uses the cumulative branch paths, so a staged text-only commit on a branch
  with reviewed code still needs review; E13 a routing file without `tiers`, or without
  `max_reviewers`, skips the tier check in the hook and is refused by the real-routing test;
  E14 a contract-only branch is text and needs no reviewer; E15 an untracked routed path
  (`.cursor/mcp.json`, `.gitleaksignore`) is checked against its row although no file exists;
  E16 a research-skill change with its dbt macros (the provider-check MRs) needs
  analytics-engineer and cto, two, not three; E17 every tracked file named by an exact path in
  gate code (`.claude/hooks/*.py`, `scripts/check_*.py`, `design-mocks/check_*.py`,
  `.gitlab-ci.yml`) is a risk path or is listed in `NOT_GATE_INPUTS` with its reason, and an
  entry no gate names any more fails the test.
  Companions: T1 a page with its Python tests, its `.test.mjs` and its design baselines needs only
  bi-analyst; T2 a model with its dbt test and a Python test needs only analytics-engineer, in the
  gate and in CI; T3 a tests-only branch needs platform, and a text plus baseline branch too;
  T4 a page with `tests/test_design_inventory.py` or a gate's `.test.mjs` keeps cto and platform;
  T5 a page with its component registry row and the registry baseline needs bi-analyst and cto.
  Scope (CI): S1 a changed path outside scope_paths is refused; S2 the task folder is exempt;
  S3 a directory entry with a trailing `/` covers its files.

decisions_taken: >
  The rules are issue #348's list, approved in chat, 2026-11-24; the changed sentences of
  working_agreement.md, agent_guardrails.md, north_star.md and the briefs are quoted in the MR head
  for approval by the merge. The split into MR A and MR B is the coordinator's call under the
  400-line rule.
  No new mechanism: `_tier_gate` and the companion rule are checks inside the existing commit gate
  and its CI backstop, named in the issue's How step 2; `tiers`, `max_reviewers` and
  `companion_paths` are keys in the existing routing file (How step 1).
  RECURRING COST, down: scope-auditor leaves `always`, so every MR spawns one reviewer fewer and a
  docs-only MR spawns none; a branch's tests no longer add platform-reviewer. Up, on rare paths:
  platform-reviewer joins cto-reviewer at opus on the six protected paths it was absent from (the
  agents, commands, settings, routing, the two MCP files), which the issue's "owner plus one
  specialist" requires; bi-analyst-reviewer joins cto-reviewer at opus on components.yml;
  cto-reviewer joins the gate, gate input, CI, deploy, prod-write and ingestion rows at sonnet;
  bi-analyst-reviewer takes the mock scripts. Net per MR: the reviewer count is equal or lower,
  except a branch on `design-mocks/check_*.py`, the research skill, the CI-run guard scripts,
  the dependency pins or the lint rulesets, which goes from one (scope-auditor) to two; the two
  wireframe standards stay at two with other reviewers. The model tier rises on seven paths (the
  six protected paths and components.yml).
  Known gap, a follow-up on the issue: an inline `gitleaks:allow` comment on a text path silences
  `validate:secrets` with no reviewer; `--ignore-gitleaks-allow` would close it.
  Measured on the last 60 merged MRs (`git log --merges --first-parent -n 60 gitlab/main`, task
  folders left out): none needs no reviewer, 23 one, 14 two, 23 three or more. The 23 combine a
  page with a gate, a mock check, an export or a mart, or a mart with ingestion; under this
  routing they are split.
  Beyond the issue's words, each quoted in the MR head: the tier map above (which path is which
  tier, and who is owner and specialist on each, the gate inputs and the mock scripts included);
  the companion rule, a gate's own test included; the metric catalogue and the
  competition registry keep two reviewers as risk paths; "never more than two" applies to the
  whole branch, so a branch needing three is split; a text-only branch needs no review.md; the
  gate counts a rename on both sides; the CI backstop refuses a changed path outside scope_paths
  (the scope-auditor's first item); the 400-line rule stands in §2 with no gate, since "about" is
  no threshold.
  The scope-auditor's other items (§10 classes, doc-sync, decisions_reserved, impact-map honesty
  on territory paths, undeclared thresholds on territory paths, the approved_design `none` line)
  need judgment, not a gate; they go to the issue as a follow-up comment.

decisions_reserved:
  - "none: the tier map, the companion rule and the sentences beyond the issue are declared above and quoted in the MR head; the CPO approves them by the merge"

acceptance_criteria:
  - "AC1 Text, copy and docs: a branch whose paths match no tier glob needs no AI reviewer; the commit gate and CI pass without review.md. Tests: tests/test_review_tiers.py::test_a_text_only_branch_commits_without_review and ::test_ci_passes_a_text_only_branch."
  - "AC2 Site pages and dbt models: every tracked `site_v2/src/**` file routes to bi-analyst-reviewer alone and every `dbt_project/**` file outside the risk rows (two seeds, the package manifests, the lint config) to analytics-engineer-reviewer alone. Test: ::test_every_tracked_file_matches_its_tier."
  - "AC3 Gates, hooks, CI, cost, prod writes, ingestion: every tracked risk file routes to exactly two reviewers, the owner and one specialist, per the tier map; every file a gate names is a risk path or a listed non-input. Tests: ::test_every_tracked_file_matches_its_tier, ::test_the_risk_pairs_are_the_tier_map, ::test_every_file_a_gate_names_is_a_risk_path."
  - "AC4 The gate and CI refuse a changed path whose reviewer count is not its tier's, and a branch that needs more than two reviewers; a rename counts both paths. Tests: ::test_gate_refuses_a_path_without_its_reviewers, ::test_gate_refuses_three_reviewers, ::test_ci_refuses_three_reviewers, ::test_a_rename_keeps_its_reviewers, ::test_a_staged_text_commit_on_a_reviewed_branch_needs_review."
  - "AC5 A branch's own tests and baselines add no reviewer; a tests-only branch needs their owner; a risk-tier test keeps its reviewers. Tests: ::test_a_branch_s_own_tests_add_no_reviewer, ::test_a_model_and_its_test_need_only_the_owner, ::test_a_tests_only_branch_needs_their_owner, ::test_ci_passes_a_model_and_its_test_with_only_the_owner."
  - "AC6 §2 states that an MR changes at most about 400 lines, tests and generated files not counted. Test: tests/test_reviewer_standard.py::test_section_2_states_the_size_rule."
  - "AC7 §2 states the tiers. Test: tests/test_reviewer_standard.py::test_section_2_states_the_tiers."
  - "AC8 CI refuses a changed path outside the contract's scope_paths; the task folder is exempt. Tests: tests/test_review_tiers.py::test_ci_refuses_a_path_outside_scope, ::test_ci_exempts_the_task_folder."

done_when:
  - "`python -m pytest tests/test_review_tiers.py` passes; run before the code, the new tests fail."
  - "`python -m pytest` (full suite) passes."
  - "`python scripts/ci_local.py --mr` passes."

amendments: (none)
