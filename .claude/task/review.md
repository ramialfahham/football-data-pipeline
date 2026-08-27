# Review — fix/92-singular-tests-read-the-branch — 2026-08-27

> #92: `--favor-state` removed from `data:build:mr`'s `dbt test` invocation, so the 30 singular
> tests read the BRANCH instead of production. Branched from main `1804a64`.
> PROTECTED path (`.gitlab-ci.yml`) → `cto-reviewer` + `platform-reviewer` at the **opus** floor,
> plus the always-on `scope-auditor`; `dbt_project/**` added `analytics-engineer-reviewer` in
> round 2.

diff_sha256: 29927915ac3f56cebf737b328375ba73420373565608fe4b62a4cd6b3910c7d3

rounds: 3

> ⚠ THIS IS THE ROUND CAP. Past three the working agreement says STOP and bring the open findings to
> the CPO rather than looping. Nothing is open.
>
> ROUND 1 — **two FAILs**, from cto-reviewer and platform-reviewer independently, neither in the CI
> change itself and both in its undisclosed blast radius:
>   (a) two dbt guards (`assert_metric_meaning_complete.sql`,
>       `assert_metric_direction_lower_is_better_agree.sql`) carry CI notes this change makes false,
>       including the standing instruction "Do not try to solve this with a CI workflow change" —
>       corrected in `.gitlab-ci.yml` and left standing there, which is the "corrections replace,
>       never accumulate" failure and the very defect class this task exists to fix.
>   (b) the change was pinned by nothing but a comment: re-adding the flag restored the whole defect
>       with every gate, every test and the pipeline still green.
>   scope-auditor PASSed round 1.
> ROUND 2 — `scope_paths` extended by three files under `amendments:`, both CI notes rewritten, the
>   impact_map extended, and `tests/test_ci_data_job_invariants.py` given
>   `test_the_mr_singular_test_gate_reads_the_branch_not_prod`, asserting BOTH halves of the
>   asymmetry and watched going red both ways. All four reviewers PASS.
> ROUND 3 — contract prose only, **no code file changed**: `impact_map` carried BOTH `714` and
>   `736` for the same line of `.gitlab-ci.yml`. 736 is right. cto-reviewer judged it not worth a
>   round and recommended fixing it in passing; it was fixed and re-audited anyway, because a
>   correction landing in one paragraph and not its neighbour is exactly the accumulation the rule
>   forbids. Only `scope-auditor` was re-spawned; the three specialists' territories
>   (`.gitlab-ci.yml`, the two dbt guards, the pytest module) are byte-identical to round 2.

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope_paths vs. actual diffed files: `.gitlab-ci.yml`, `tests/test_ci_data_job_invariants.py`, both `dbt_project/tests/*.sql` files, `contract.md`, `escalations.log` — all listed, none extra.
- Protected-path override on `.gitlab-ci.yml`: authority is a quoted, dated CPO chat ruling ("do as recommended") committed into `escalations.log` in the same diff, not a bare assertion in contract.md alone.
- Threshold declarations (new mechanism / recurring cost) in `decisions_taken`: checked against the diff — no new job/stage/tag/schedule/file; a flag removed from an existing invocation and an assertion added to an already-existing test module, so "none" for both holds.
- Doc-sync for the two dbt singular-test CI-note comments the flag change falsifies: both rewritten in this same diff (not left stale), and their new text matches the actual post-change flag semantics I verified against `.gitlab-ci.yml`.
- decisions_reserved: the residual "`--defer` may read a stale `ci_*` leftover" hole is explicitly left open, not silently resolved — correctly kept out of `decisions_taken`.
- Round-3 delta accuracy: grepped the live `.gitlab-ci.yml` and confirmed `data:build:main`'s singular-test line is genuinely at 736 (job starts 687), so the 714→736 correction is real, not another unmeasured number.
- Credential/secret sweep across all five non-artifact files touched in the diff: none found.
- Impact-map A6 trigger paths (`ingestion/**`, `dbt_project/models/**`, `scripts/export_*.py`, `site*/`): none touched, so the mandatory-lineage trigger doesn't apply; the protected-path guard-trace impact_map supplied instead is evidenced with concrete line numbers and a real pipeline/job reproduction, not hand-waved.

## cto-reviewer
VERDICT: PASS
> Verdict from ROUND 2, carried forward: round 3 changed contract prose only, and this reviewer's
> territory (`.gitlab-ci.yml`) is byte-identical between rounds 2 and 3. Its residual observation —
> the uncorrected `714` — is what round 3 fixed.
risks_checked:
- **Override real and sufficient for the widened scope.** `.gitlab-ci.yml` is the only protected path in `scope_paths`; `protected_override` names a CPO approval ("do as recommended") and the same commit writes it into `.claude/task/escalations.log` with the recommendation, the disclosed cost and the rejected two-pass alternative alongside it — so the authority and the change travel together rather than resting on the contract's own word. The three files added under `amendments:` are NOT protected paths and need no CPO grant; the amendment correctly cites standing rules rather than manufacturing an approval. Both dbt edits are confined to the `{# ... #}` block — the `select` in each file is byte-unchanged (verified by reading both files, not the diff).
- **New mechanism (A3).** None. The CI change is one flag removed from an existing invocation. The added test is one function plus one helper inside `tests/test_ci_data_job_invariants.py`, reusing `_ci_config()` and `_script_lines_by_job()` which already exist — no new file, module, dependency, CI step, job, stage, tag or selector. Adding a case to a guard that already exists for this exact class is not a new mechanism.
- **Boring technology.** This is the plainest available fix (delete one flag); the exotic alternative (expand/contract two-pass renaming) was put to the CPO and not chosen. Pinning uses the existing pytest module and the existing YAML parse, not a new harness.
- **Guard direction — may it change this way.** Same 30 tests, same `--select test_type:singular --exclude tag:freshness_check`, same exit-code semantics; no `allow_failure`, no `|| true`, no `rules:` change, nothing made conditional. CI still fails CLOSED, and with respect to the branch it fails closed *more* often than before. The disclosed residual hole is strictly narrower than the one removed and is left open on #92 rather than silently absorbed.
- **Gate side effects (the "impact maps miss gates" class).** Checked the #73 KNOWN-AND-ACCEPTED block: the four `_covers_active_competition_var` tests fail on an onboarding MR because the league has no rows, equally true reading `ci_*` or prod, so that accepted-failure note stays accurate. Verified `dbt seed --target ci` really does run before both invocations (`.gitlab-ci.yml:589`), the premise the two rewritten guard notes rest on.
- **Correction sweep completeness — my round-1 finding.** Grepped `favor.state|favor_state` repo-wide. The only non-artifact consumers are the two dbt guards (both rewritten, the old instruction retained only as quoted history and immediately negated), the module docstring at `tests/test_ci_data_job_invariants.py:17-19`, and `dbt_project/docs/layering.md:32`. Both of the latter describe the BUILD line, which still carries `--defer --favor-state`, so both remain true and correctly untouched. No false statement about this flag survives anywhere in the tree.
- **Recurring cost / CFO tripwire.** No job added, no cadence changed, no schedule created, no API call volume changed, no new artifact retention. Only the dataset the queries read changes, and a `ci_*` relation is not larger than its prod twin. Reasoned, not waved.
- **Credentials, secrets, permission widening.** One flag and a comment block. No `variables:` added or changed, no CI/CD variable unprotected, no image, `id_tokens`, `artifacts` or `rules` change, nothing resembling a key or token.
- **Undeclared thresholds (#868).** Compared `decisions_taken:` against the whole diff; the crossings present are declared with their authority, and GUARD WEAKENED is answered honestly as a trade rather than a clean win.

## platform-reviewer
VERDICT: PASS
> Verdict from ROUND 2, carried forward: round 3 changed contract prose only; `.gitlab-ci.yml`,
> the pytest module and the two dbt guards are byte-identical between rounds 2 and 3.
risks_checked:
- **Would the new test fail if the change were reverted — traced through the parser, not the docstring.** `.gitlab-ci.yml:633-635` and `:675-677` are `>-` folded scalars whose continuation lines sit at the same 6-space indent, so each arrives from `yaml.safe_load` as ONE string; the interleaved `#` comment lines at 4-space indent are terminated as comments, not absorbed. `_script_lines_by_job` → `" ".join(line.split())` → `startswith("dbt build ")` / `startswith("dbt test ")` matches exactly one line each. I checked every other script entry of `data:build:mr` for a line that would also match, including the `|` block anchors `.dbt_profile` and `.gcp_auth` which expand to many lines — none begins with `dbt build`/`dbt test`. Re-adding `--favor-state` to the test line fails `tests/test_ci_data_job_invariants.py:310`; removing it from the build line fails `:324`. The revert is caught in both directions.
- **Silent-pass paths in the new helper.** `_mr_dbt_invocations` asserts `len(builds) == 1`, `len(tests) == 1` and that the job exists, so a renamed job, a moved invocation, a wrapped `cd X && dbt test`, or a second invocation makes the test RED rather than vacuously green. The one reformatting that could hide `--favor-state` (moving it onto a more-indented continuation line, which stops folding) also removes `--defer`/`--state /tmp/main-state` from the matched string, so the loop reddens anyway. No vacuous-pass path found.
- **The flag semantics verified against the installed dbt, not against the contract's prose.** `dbt/contracts/graph/manifest.py:1405-1415`: a node is swapped for the state relation only when `unique_id not in selected and (adapter.get_relation(...) is falsy or favor_state)`. That confirms all three claims the change rests on — the test line's `--favor-state` re-aimed every `ref()` at prod even for models just built; without it `--defer` prefers the ci_ relation when it exists and falls back to prod when it does not; and on the build line the flag governs only unselected upstreams, so keeping it there is load-bearing and costs the built nodes nothing. Asserting both halves is right for that reason.
- **The load-bearing claim in the two rewritten dbt guard notes.** `dbt seed --target ci` at `.gitlab-ci.yml:589` is unconditional and unselected, so the branch's `metric_catalogue` relation always exists in the ci target and plain `--defer` resolves `ref('metric_catalogue')` to it. In the sibling `dbt build` invocation the seed is inside `state:modified+` whenever its values change, hence selected, hence unaffected by the retained `--favor-state`. "Catalogue values and a guard that depends on them CAN land in the same PR" is true in both invocations as written.
- **Sweep for statements the change leaves false elsewhere.** Only three other places name the flag: `tests/test_ci_data_job_invariants.py:17` and `dbt_project/docs/layering.md:32` both describe the MR *build* path, unchanged and still true; `.github/workflows/ci-data-build.yml` still carries it on both lines, but that tree is the deliberately-unedited dormant snapshot CLAUDE.md forbids syncing, so leaving it is correct rather than a duplicated-enforcement defect.
- **Fail-closed posture of the gate itself.** No `allow_failure`, no `|| true`, nothing made conditional; the rules block is unchanged; the selection is untouched, and the suite is still 32 singular files minus the 2 freshness-tagged = the stated 30. `data:build:main:736` still runs the same suite `--target prod` with no `--defer`/`--state`, so the post-merge backstop is at full strength and any hole opened in MR validation is still caught on main.
- **Re-run and interruption.** `dbt seed` → `dbt build` (incremental MERGE) → `dbt test` (read-only) are each idempotent on re-run; a killed job leaves a partially-built ci_ table which the *next* MR's tests may now read. That is precisely the residual hole #92 keeps open, it is disclosed in the contract and in the CI comment, and `resource_group` prevents a concurrent writer during the read.
- **Coverage boundaries examined and judged NOT defects in this delta** (recorded rather than manufactured): `--target ci` is not pinned; `--defer`/`--state` are pinned on the test line but not the build line; and `DBT_FAVOR_STATE` / `DBT_FAVOR_STATE_MODE` set the same flag from a `variables:` mapping, which this test does not read. All three break behaviour this branch did not change, none is documented anywhere as the way to do it, and the flag set that DID change is pinned in both directions. Worth a follow-up line in the same test, not a blocker. `favor_state` is not settable from `dbt_project.yml`, so the CLI and env var are the only routes.
- **Remaining hunt items with nothing to report:** no `*requirements*.txt` / `package*.json` / lockfile change; no key, token or permission widening; no site build, `dist/`, `.gitignore`, cache-header, redirect or third-party-origin surface in the diff.

## analytics-engineer-reviewer
VERDICT: PASS
> Verdict from ROUND 2, carried forward: round 3 changed contract prose only; both
> `dbt_project/tests/*.sql` files are byte-identical between rounds 2 and 3.
risks_checked:
- Verified `dbt seed --target ci` (`.gitlab-ci.yml:589`) runs unconditionally, with no `--select`, before both the build and test `dbt` invocations in `data:build:mr`, and targets the same `ci` schema the test invocation later queries — so the branch's `metric_catalogue` seed table exists in that schema before the test step starts.
- Traced dbt-core's `--defer` (favor_state=False) resolution rule for an unselected node: prefer the current-target relation if it exists, else fall back to the deferred/state relation — and confirmed this makes `ref('metric_catalogue')` in `assert_metric_meaning_complete.sql` / `assert_metric_direction_lower_is_better_agree.sql` resolve to the branch's just-seeded row, not main's, once `--favor-state` is removed from the test line. Rewritten CI notes in both files match this mechanism.
- Confirmed the only diff in both `.sql` test files is inside the jinja comment block; the `select` body enforcing the actual assertion is byte-identical, so no test logic weakened.
- Checked `data:build:main` (`.gitlab-ci.yml:695,736`) and `data:nightly` are untouched by this change (no `--defer`, no `--favor-state`, always `--target prod`), so production DQ gating is unaffected.
- Checked the new pytest invariant asserts both halves of the intended asymmetry (`--favor-state` absent from the test line, present on the build line), so the fix is pinned mechanically rather than left to a comment.
- Checked for catalogue-row edits, hardcoded competition identifiers, new `safe_divide`, and consumption-layer computation in this diff — none present; scope is CI config + test-comment provenance only.
- Residual "unmodified-upstream-may-read-stale-`ci_*`-copy" risk is explicitly disclosed in both the contract and the new `.gitlab-ci.yml` comment as an open, CPO-deferred item (#92), not asserted away — treated as an acknowledged trade, not a hidden defect.

## escalations
(none)
