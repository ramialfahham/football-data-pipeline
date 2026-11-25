# Review — claude/348-one-reviewer-a82b34 (MR A of #348)

diff_sha256: 9035f7921c21a0f509c34f783d807270a6db45ed8fd977552e38f9a6908656c6

rounds: 3

Round 1 (cumulative diff): cto-reviewer FAIL, platform-reviewer PASS. Round 1 started before the full local tests had finished; from round 2 on, the full tests and ci_local finished green before any reviewer started. Round 2 (diff-only): cto-reviewer FAIL, platform-reviewer PASS. Round 3 (diff-only, the last round): both PASS, recorded below. The flaky test `test_gate_refuses_three_reviewers` passed 20 of 20 runs idle, 15 and 30 runs beside ci_local, and every full run since, so no test change was made for it.

## cto-reviewer
VERDICT: PASS
findings:
- [nit] cost-declaration: `.claude/task/348-one-reviewer/contract.md` decisions_taken, the "goes from one (scope-auditor) to two" sentence — the five CI-run guard scripts and the three dbt manifests and lint config already had two reviewers on main (owner plus scope-auditor) and keep two; only `design-mocks/check_*.py`, the research skill, `.python-version`, `.nvmrc` and `.ruff-ci.toml` go from one to two. The sentence overstates the increase, the safe direction.
risks_checked:
- Round-2 finding 1 resolved: the research skill is risk, analytics-engineer + cto, pinned in PINNED_CASES, TIER_MAP and the skill-plus-macro case. The pairing holds on authority: the site table is a data-provenance call (analytics-engineer), widening the self-merge route is a guard change (cto), the parser stays platform + cto, and `check_research_fix_mr.py:153` reads the skill from the merge base, so a branch cannot loosen its own check.
- Round-2 nits 2 and 3 resolved: the wireframe standards stay at two; the dbt manifests are analytics-engineer + cto.
- Every NOT_GATE_INPUTS entry checked: none changes what a gate lets through. The templates are matched by path only; the docs appear only in messages; `site/i18n/*.json` only fills the corroborated text of a finding reported anyway; the `changes:` entries add jobs; the remaining entries are territory or companions. The stale-entry check keeps the list current.
- The test's blind spots checked by hand (`Path /` and `os.path.join` reads, gate code outside GATE_CODE): none leaves a tracked text-tier gate input today; gate code outside the scan is itself risk tier.
- The allowlist cannot bypass the test without a risk-tier change: an entry is exempt only while gate code names it.
- No new mechanism, no fail-open inversion, no dependency entry, no credential, no widened CI permission; recurring cost declared; protected edits under the contract's protected_override.

## platform-reviewer
VERDICT: PASS
findings:
- [nit] test-coverage blind spot: tests/test_review_tiers.py:202-211 (`_gate_named_files`) — the token scan sees only a path written as one string literal, not one joined with `Path /` or `os.path.join`; every such read today is risk tier, a subject the check inspects, a companion baseline or untracked, so no case fails now. Collapsing join chains before matching is a follow-up.
risks_checked:
- Round-2 nit 1 resolved: the vacuous case is gone; the new skill-plus-macro-plus-test case fails if the companion rule is reverted.
- Round-2 nit 2 resolved: `test_the_risk_pairs_are_the_tier_map` runs `_tier_gate` on every UNTRACKED path, so dropping `.gitleaksignore` from the risk tier fails.
- The new test fails when a gate input drops to text or territory, and when a NOT_GATE_INPUTS entry goes stale or becomes risk.
- Deterministic on Windows and Linux: `git ls-files` paths, UTF-8 read, `\r` outside the token class; sub-second run time; read-only.
- Every new routing row pinned in TIER_MAP and PINNED_CASES; doc counts match (54 CTO rows, parity tests).
- No matcher, hook or CI code changed in the delta; no dependency, credential, build or hosting change.

## fixes
- gate input routed as text | sweep: tests/test_review_tiers.py derives every tracked file named by an exact path in `.claude/hooks/*.py`, `scripts/check_*.py`, `design-mocks/check_*.py` and `.gitlab-ci.yml`; it lists 60 below risk on main's routing, 14 on round 1's, 10 on round 2's and none now; 34 non-inputs sit in NOT_GATE_INPUTS, each with its reason | test: tests/test_review_tiers.py::test_every_file_a_gate_names_is_a_risk_path
- rule text overstates the routing of a gate's own test | sweep: every sentence on tests and companions in working_agreement.md, agent_guardrails.md, north_star.md, the briefs, the routing `_doc` and the contract, found by grep for "own test", "companion" and "tests and baselines" | test: tests/test_reviewer_standard.py::test_section_2_states_the_tiers

## escalations
(none)
