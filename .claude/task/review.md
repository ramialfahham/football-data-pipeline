# Review — chore/gitlab-ci-phase3 — 2026-08-06

branch: chore/gitlab-ci-phase3
diff_sha256: e8da723d13739f0f24fb47e4ab98972aa291ba2be7286afade7d631861f9743f

rounds: 2

> THREE REAL DEFECTS, NONE FOUND BY A TEST OR A LINTER. `glab ci lint` passed, the YAML
> parsed, and the suite was green while all three were present. Recorded together because
> the pattern is the finding: static validation establishes that a config is well-formed,
> never that it works.
>
> 1. `data:nightly`, `deploy:export` and `deploy:site-v2` all expanded `*gcp_auth` without
>    declaring `id_tokens:`. GitLab populates `$GITLAB_OIDC_TOKEN` only for a job that
>    declares that block ITSELF — not inherited from `default:`, not implied by the
>    anchor. All three would have died at the auth guard before doing any work, so the
>    nightly would have failed EVERY night once a schedule existed.
> 2. Both deploy jobs were `when: manual` with no source restriction. That excludes
>    schedules and nothing else, so a Firebase deploy play button appeared on every
>    merge-request and every push-to-main pipeline — one click from deploying whatever
>    that branch built. `deploy-site-v2.yml`'s only GitHub trigger was `workflow_dispatch`,
>    which never attached the job to a push or a PR at all.
> 3. The contract declared cost effects citing a CPO instruction recorded nowhere a
>    reviewer could check — the same defect that failed MR !4's round 1.

## scope-auditor
VERDICT: PASS
risks_checked:
- The cost-instruction record: `escalations.log` now carries the CPO's verbatim wording,
  what triggered it, and its effect on how this contract argues cost; the contract cites
  it as a pointer, matching MR !4's corrected pattern. The earlier FAIL is acknowledged in
  the entry rather than quietly fixed.
- §10, judged per workflow rather than as a block. `board-request-sync.yml` and
  `ci-failure-watchdog.yml` are clean implementation calls — you cannot sync a board that
  does not exist, and you do not rebuild a notification the platform sends natively.
  `pages-match-preview.yml` is "§10-ADJACENT": the retirement is documented at
  `north_star.md:37` and verified, and the CPO said "finish migration" rather than "revive
  the MVP", but the inference that a retired product stays retired is the builder's.
  Accepted as defensible with the risk NAMED, not waved through — and surfaced to the CPO
  in conversation rather than left inside a passing verdict.
- All corrections stayed inside `scope_paths`; no amendment was made or needed.
- The contract reads as current state — the `done_when` line that named the wrong job as
  carrying the manual gate is corrected once, not kept alongside its old form.
- Nothing is asserted beyond its evidence: no schedule exists, the deploy is manual, and
  nothing here has run on a real pipeline.

## cto-reviewer
VERDICT: PASS
risks_checked:
- The cost trap, checked against the merged file rather than the diff: `.not_on_schedule`
  is first on every job that could otherwise match, including `data:build:main`. Confirmed
  independently that GitLab really does evaluate `changes:` as true on non-push pipelines,
  so the risk being mitigated is real rather than a strawman.
- Recurring cost: the nightly restores an absent GitHub job rather than adding spend; not
  porting `pages-match-preview.yml` removes a daily unconditional rebuild; the deploy is
  manual. Declining to run the cost tooling is acceptable HERE specifically because this
  task starts no spend — the number matters at schedule-creation time, which is reserved.
- New mechanisms: both the schedule trigger and the Firebase deploy already ran on GitHub,
  so porting them introduces no new capability.
- The three non-ports verified against source, not the contract's paraphrase — including
  reading `north_star.md:37` directly and confirming `pages-match-preview.yml`'s 07:30 UTC
  unconditional rebuild.
- Secrets: nothing introduced or exposed; the two WIF identifiers are pre-existing and
  non-secret.
- FLAGGED AND FIXED: `done_when` claimed `deploy:site-v2` carries `when: manual`, but the
  gate sits on `deploy:export`. The guarantee held via `needs:`, so this was imprecision
  rather than a hole — corrected rather than left, since a contract that names the wrong
  job teaches the next reader the wrong thing.

## platform-reviewer
VERDICT: PASS
risks_checked:
- FAIL 1, fixed: the deploy reachability defect above. Both jobs are now scoped
  `if: $CI_PIPELINE_SOURCE == "web"` with a `when: never` fallback, stated on BOTH rather
  than letting `deploy:site-v2` inherit safety from `needs:` — so a future `needs:` edit
  cannot silently widen where a deploy can appear. Verified by mutation: restoring the
  bare `when: manual` form made the new pin fail naming `merge_request_event`.
- FAIL 2, fixed: `dbt deps` ran before the `new_data` gate while the contract claimed a
  quiet night runs nothing. Now inside the gate, matching `dbt-scheduled.yml:74-76`. Fixed
  rather than argued down — the amount is small, but a claim that does not match the code
  is the defect regardless of the amount.
- The schedule guard, re-verified after the deploy jobs stopped using the shared anchor:
  the pin was rewritten from a POSITIONAL check (`rules[0]` equals the guard) to a
  SEMANTIC one that evaluates each job's rules against a simulated scheduled pipeline.
  The positional form would have failed a job that became correctly schedule-safe a
  different way. Traced by the reviewer against all ten jobs.
- NOTED AT PASS AND THEN FIXED, recorded because it changed the diff after the verdict:
  the recogniser matched `if:` conditions by exact string, so an equivalent-but-differently
  spelled condition (`$CI_COMMIT_BRANCH == "main"`, single quotes, extra whitespace) would
  fall through as "does not match" and could report an unsafe job as safe. That mattered
  more once the deploy jobs' safety rested entirely on hand-written conditions. Unknown
  conditions now RAISE with a remediation instead of being assumed harmless, and quotes
  and whitespace are normalised first. Verified by mutation with
  `$CI_PIPELINE_SOURCE == "api"`.
- Artifact plumbing, `.gcp_auth` working on the Node image, no custom-domain step, and the
  absence of dependency or secret changes — all checked.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- FAIL, fixed: the `id_tokens` defect above, which this reviewer found. The declaration is
  now a single `.gcp_job` anchor merged into every consumer — `.data_build_base` included,
  so the file holds ONE definition instead of a copy per job. Reviewer confirmed all five
  auth-using jobs carry it, that no sixth was missed, and that `.data_build_base`'s merged
  behaviour is unchanged by the refactor. Verified by mutation before acceptance.
- The rename `write_github_output` -> `write_ci_output` is complete across the package;
  the `new_data` semantic (`ctx.tables_loaded > 0`) is untouched.
- Failure direction on a quiet night: ingestion runs, `new_data != true` exits 0 before
  `dbt deps`, `dbt seed` or `dbt build` — genuinely no warehouse spend, and the safe
  direction for an unattended job. Re-traced after `dbt deps` moved inside the gate.
- `write_step_summary_if_configured` deliberately NOT renamed: it feeds an optional
  markdown rendering with no GitLab analogue and gates nothing.
- Also caught: `$0` in a log message would have shell-expanded to the interpreter path
  instead of printing "a $0 night". Escaped.

## escalations
(none — the two CPO decisions this task rests on were made in conversation and are
recorded in `.claude/task/escalations.log` under the 2026-08-06 Phase 3 entry: the
instruction not to run the cost tooling, and the decision not to create the nightly
schedule while nothing reads the data. Neither was an escalation raised by a reviewer.)
