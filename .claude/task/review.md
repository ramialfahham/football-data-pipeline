# Review — chore/gitlab-ci-pipelines — 2026-08-06

branch: chore/gitlab-ci-pipelines
diff_sha256: 5209163cddbee50624a950c2aeffa004a6403646b9821934dbfe01463a816392

rounds: 7
rounds_cap_override: >
  The cap stops LOOPING on unresolved findings. These rounds are not a loop — each
  reviewed material that did not exist when the previous one ran. R1-R3: the CI
  translation and the guard-parity sweep (two specialist FAILs, fixed). R4: a confirming
  pass on the CPO-ruled scope remedy. R5: the credential mechanism, replaced after
  reading what the GitHub workflows actually did. R6-R7: a defect a LIVE CI RUN found
  that no static check could, plus the test pinning it. Shipping any of this on verdicts
  that predate it would be the real defect.

> WHAT A LIVE RUN FOUND THAT SEVEN ROUNDS OF STATIC REVIEW DID NOT. Job 15752046768
> reached `sqlfluff lint` and died: "Could not find profile named
> 'football_data_pipeline'". `.gitlab-ci.yml` had set `DBT_PROFILES_DIR` to a
> project-local directory, but `dbt_project/.sqlfluff` pins `profiles_dir = ~/.dbt`, and
> dbt and sqlfluff resolve the profile by DIFFERENT means — so `dbt deps` passed and the
> next command failed. Three review rounds, a YAML parse check and `glab ci lint` all
> passed over it, because the config was well-formed; it merely disagreed with a file
> none of them cross-referenced. This bounds what every earlier green check was worth:
> they established the config parses, never that it runs.
>
> The contract's stated reason for moving the profile was also FALSE — it claimed the
> runner home directory "does not exist on a GitLab runner image". It does; jobs run as
> root and `~` is `/root`. That claim is replaced, not annotated.

> WHAT IS AND IS NOT PROVEN AT THIS HASH. PROVEN on a live runner: the YAML parses,
> anchors expand, path rules fire, all three credential guards work, and — the headline —
> the WIF exchange SUCCEEDS ("GCP credentials configured via Workload Identity Federation
> (keyless)"), with `dbt deps` then authenticating and installing packages. NOT PROVEN:
> `sqlfluff lint`, `dbt build` and the singular DQ suite have never completed, because
> the profile defect stopped them and the fix has not yet been exercised by a run.
> `done_when` requires a green `data:build:mr` for exactly this reason.

## scope-auditor
VERDICT: PASS
risks_checked:
- The profile fix touches only `.gitlab-ci.yml` and `.claude/task/contract.md`, both
  already in `scope_paths`. No amendment was needed and none was made — the discipline
  this task was ruled on earlier.
- `dbt_project/.sqlfluff` was deliberately NOT edited, and that is the right call: local
  development reads the same file, so a CI-shaped path there would break every
  developer's `sqlfluff lint`. The fix belongs in CI, which is what moved.
- "Corrections replace, never accumulate": the false home-directory claim is replaced by
  the corrected account rather than sitting alongside it.
- Nothing is asserted beyond its evidence. Neither `contract.md` nor this file claims the
  profile fix has been exercised by CI, because at this hash it has not.
- §10: no product, naming, cost or permanence decision was taken; a profile path is an
  implementation detail of the machinery.

## cto-reviewer
VERDICT: PASS
risks_checked:
- (round 5) New-mechanism classification, verified against the four GitHub originals
  rather than the contract's paraphrase: all already used WIF, none a stored key, so the
  GitLab `id_tokens:` + `external_account` construction restores an approved architecture
  rather than introducing one. The service-account key was the deviation.
- (round 5) Secrets: no long-lived credential is introduced or required. The OIDC JWT and
  credential config are written to job-local files, never to a log, an `echo`, a process
  argument, a cache path or an artifact.
- (round 5) Recurring cost: none. No new dependency, job or schedule.
- (round 5) Guard invariant: both data jobs run `*gcp_auth` before any dbt/sqlfluff
  command, and no job's `rules:` consults a credential variable, so the fail-closed guard
  cannot be bypassed by a rules-skip.
- NOT RE-RUN for rounds 6-7, deliberately. Those changed a filesystem path and added a
  test — no mechanism, dependency, cost, secret or guard invariant moved, which is this
  role's entire remit. Recorded rather than silently skipped; a reader who disagrees can
  re-run it against this hash.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Diagnosis confirmed from the files: `.sqlfluff:10` pins `profiles_dir = ~/.dbt`, dbt
  and sqlfluff genuinely resolve the profile differently, and the GitHub original wrote
  to that runner's `~` with no `DBT_PROFILES_DIR` anywhere.
- Completeness: every consumer (`validate:governance`, `data:build:mr`,
  `data:build:main`) expands `*dbt_profile` before touching dbt or sqlfluff; no stale
  executable reference to the removed variable survives.
- Heredoc mechanics re-traced after the path edit for BOTH block scalars: `<<'EOF'`
  correctly quoted (static body), `<<GCPCRED` correctly unquoted (must expand two
  variables), both terminators at column 0 after YAML indentation stripping.
- `~/.dbt` side effects: all profile-writing jobs share `image: python:3.11` running as
  root, so `~` is `/root` and `mkdir -p` cannot hit a permissions wall; no cache path
  touches it; containers are fresh, so no cross-job contamination.
- FAIL 1, fixed: the fix was correct and complete but NOTHING PINNED IT — reverting it
  would not have failed a single test, a guard-the-guard gap on an opus-routed guard
  path, for a mistake the YAML's own comment admits invites a future "cleanup". Now
  pinned by `test_ci_writes_the_dbt_profile_where_sqlfluff_looks_for_it`, which is
  textual (no credentials, no dbt run) and was VERIFIED AGAINST THE REGRESSION: run
  against the pre-fix `.gitlab-ci.yml` at HEAD it failed with the intended message, then
  passed once restored. A pin never seen to fail pins nothing.
- FAIL 2, fixed, and the more instructive one: the completeness check asserted `marker in
  script` — PRESENCE — while its comment and the contract both promised the profile is
  written FIRST. GitLab runs `script:` in list order, so grouping the anchors during a
  tidy-up would break CI with the test still green. Fixed by comparing list INDICES
  (`profile_at < tool_at`) rather than by weakening the claim, since order is the
  guarantee that matters. Verified by mutation: moving `*dbt_profile` below `sqlfluff
  lint models` in `data:build:mr` produced "writes the dbt profile at script step 3 but
  already invokes dbt/sqlfluff at step 1"; the file was restored from the index.
- BLIND SPOT NAMED AT PASS AND THEN CLOSED, recorded because it changed the diff after
  the verdict. The reviewer noted `runs_tool` did not match a parenthesized subshell —
  `.gitlab-ci.yml:390`'s `(cd /tmp/main-src/dbt_project && dbt deps && ...)` — and judged
  it non-live, since the same job's plain `cd dbt_project && dbt deps` anchors the check
  correctly today. It would have become live had a future edit removed that line,
  silently exempting the job. The regex now admits an optional leading `(`; the subshell
  is detected, and enumerating every match across the file confirms no false positive
  (no `echo` line matches). Strictly a tightening of the check the reviewer analysed.
- Translation fidelity re-checked for all five non-data jobs against their GitHub
  originals. 262 tests pass.

## escalations
- question: >
    `scope_paths` was amended four times mid-task — `.claude/task/escalations.log`,
    `.claude/task/TEMPLATE.md`, `docs/roles/platform_reliability.md`,
    `docs/north_star.md` — each amendment citing a reviewer's FAIL as its authority.
    `working_agreement.md:79` says an amendment records the CPO's authority, and the
    2026-06-23 precedent (`escalations.log:145`) had the same reviewer hold the same
    line until the CPO granted it explicitly. Two paths were put to the CPO: (a) confirm
    the amendment, or (b) revert the four files to a follow-up MR — which would merge
    `.gitlab-ci.yml` with the guard counts knowingly stale in four documents, one of them
    `docs/roles/platform_reliability.md`, which is fed to `platform-reviewer` as an Input
    on every future run. Builder recommended (a) with that reasoning stated.
  CPO ANSWER: >
    (a) confirm the amendment — CPO, conversation of 2026-08-06, recorded durably in
    `.claude/task/escalations.log` under "SCOPE AMENDMENT AUTHORITY FOR THE FOUR
    RESTATEMENT FILES". All four paths are authorized into this task's scope; every one
    is the same edit, a count or a list restatement, with no logic or design change. The
    ruling explicitly does NOT excuse the under-scoping: these are one sweep that was
    under-scoped when the contract was first written, not four independently justified
    extensions, since all eleven restatement sites were derivable from the routing table
    before the first edit. The three earlier SCOPE AMENDMENT entries in the log are
    superseded as to authority.
