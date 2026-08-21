# Review — feat/description-persist-docs — 2026-08-21

> MR6 of the description-drift programme: `persist_docs` on for every model and seed, and
> `dbt docs generate --static` published from `data:build:main`.
>
> ⚠ EVERY VERDICT BELOW WAS RETURNED BY THE NAMED REVIEWER. None is written on their behalf.
> MR5's own escalations.log entry records that its `review.md` asserted PASS for two reviewers who
> had returned FAIL — "a governance signature that did not exist". This branch sent a real confirm
> to each reviewer whose reviewed state had changed and waited for the answer.

diff_sha256: f0efe10a94beb1482bd4487fb3bd4872fa54cf776e7ac8931aef027d51d06539

rounds: 3

> ⚠ REBOUND after `!88` merged, and NOT because anything reviewed changed. The reviewed value was
> `71e151df…`. `!88` landing moved `merge-base HEAD gitlab/main` from `b378be5` to `7c5c420`, which
> is the same mechanism that made `!88`'s own hash go stale — recorded there too, and now hit twice
> in one day, so it is a property of split-merging rather than an accident.
>
> WHAT THE REBASE ACTUALLY MERGED, since a rebind is not a licence to change content:
>   · `dbt_project.yml`, `.gitlab-ci.yml`, `CLAUDE.md`, `tests/test_persist_docs_policy.py` and
>     `acceptance_evidence.md` — taken UNCHANGED from the reviewed commit. `!88` never touched them.
>   · `engineering_standards.md` — auto-merged, and checked by hand afterwards: it now carries BOTH
>     `!88`'s "capped at BigQuery's own maxima" rule AND this MR's "Who reads these" section, with
>     the superseded flat-600 bullet gone. This MR deliberately never edited those length bullets,
>     which is why the two changes did not collide.
>   · `escalations.log` — took `!88`'s version and APPENDED this MR's entry, so both survive: 5
>     entries, including `!88`'s fabricated-verdicts defect and this branch's protected-path record.
>   · `active_work.md` — rebuilt from `!88`'s handover rather than overwriting it, so its trap 6
>     ("never write a reviewer's verdict") and its #82/#83 scoping survive alongside MR6's state.
>   · `contract.md`, `review.md` — this MR's, superseding MR5's.
>
> No reviewed code changed. The gates were re-run on the merged tree and all five pass, now against
> `!88`'s STRICTER description gate: "618 descriptions … 9 docs blocks resolved, rendered lengths
> within 1024/16384".

## scope-auditor
VERDICT: PASS
> Returned at round 2, on the AMENDED contract. Its round-1 PASS was superseded because
> `contract.md` gained a scope path and two amendments after it, and a stale PASS over a changed
> contract is exactly what this file must not carry.
risks_checked:
- Checked every file in the diff against `scope_paths`, including the two excluded from the patch
  by `review_exclude_paths` and read from disk instead — no scope violation.
- Checked the `protected_override` for `.gitlab-ci.yml` against the `2026-08-21` entry in
  `escalations.log`: the approval is recorded BEFORE the edit per GitLab #28, and the actual diff
  is exactly the single claimed edit, with `rules:` and every other job byte-identical.
- Checked amendment 1 (the pinning test) is implementation completion under existing authority
  rather than scope drift needing its own MR: it touches only files already in scope, adds no new
  mechanism, and follows the pre-existing sibling pattern.
- Checked both amendment entries describe honestly what happened, including amendment 2 correcting
  a REVIEWER rather than only my own errors.
- Read all of `tests/test_persist_docs_policy.py` directly and confirmed its assertions match what
  the evidence claims was driven red.
- Confirmed #82 and #83 are still not started, and that the orphaned-views finding was filed
  separately rather than folded in.

## analytics-engineer-reviewer
VERDICT: PASS
> Returned at round 1. Not re-sent: its territory — `dbt_project/dbt_project.yml` and
> `dbt_project/docs/engineering_standards.md` — is byte-identical to the state it reviewed, which
> platform-reviewer independently re-verified at rounds 2 and 3. The later rounds added a file
> under `tests/` and prose in `.claude/task/`, neither of which is this role's territory.
risks_checked:
- Checked the seed-relocation hazard: the new `seeds:` block carries only `+persist_docs` and no
  `+schema`, and `macros/generate_schema_name.sql` plus the absence of any other seed-config change
  rules out a dataset move.
- Checked `+persist_docs` cascade: one project-level declaration, no per-model or per-layer
  override anywhere under `dbt_project/`, and confirmed from the installed dbt-bigquery adapter
  that `persist_docs` fires from `table.sql`, `view.sql` AND `incremental.sql`, so the three
  incremental facts are covered on ordinary runs and not only on full refresh.
- Checked the rendered-length measurement for paths it could miss: no source or snapshot
  `persist_docs`, no nested/RECORD dotted columns, and no `var()`/`env_var()` in any description
  that could render to a different length per target.
- Checked the layer contract: no model SQL, no `ref()` graph and no consumption file touched.
- Checked the new §2 prose line by line against the actual diffs — no inaccurate claim.

## cto-reviewer
VERDICT: PASS
> Returned at round 1. Not re-sent: `.gitlab-ci.yml`, the `protected_override` and the
> `decisions_taken` block are byte-identical to the state it reviewed. The subsequent amendments
> were re-checked for authority by scope-auditor at round 2.
risks_checked:
- Checked the protected-path edit against the override's claimed scope: exactly one hunk inside
  `data:build:main`'s `script:` plus one new `artifacts:` key, with no pre-existing `artifacts:`
  on that job to clobber.
- Checked both CPO approvals are quoted verbatim and recorded before the edit, satisfying GitLab
  #28's non-self-certifying requirement.
- Checked by grep that `dbt docs generate` was added to exactly one job, confirming `data:nightly`
  and `data:build:mr` were genuinely excluded rather than the exclusion merely being claimed.
- Checked the disclosed guard gap directly in `check_description_hygiene.py:37-40,82` — the length
  rule is waived for a bare `{{ doc() }}` reference — and judged that shipping while `!88` is open
  is acceptable BECAUSE the risk is disclosed and the merge order is put to the CPO as a
  recommendation rather than decided unilaterally.
- Checked no new dependency or mechanism enters: both features are native to the pinned dbt.
- Checked `allow_failure` is absent, and that the retired GitHub precedent it is contrasted
  against really does carry `continue-on-error: true`.

## platform-reviewer
VERDICT: PASS
> FAILED at round 1 with two findings, both acted on. Returned PASS at round 2 after the pinning
> test landed, and PASS again at round 3 on the final state after `contract.md`'s bytes-per-column
> figure was corrected. The round-1 FAIL is recorded here rather than hidden: finding 1 was fully
> correct and is why `tests/test_persist_docs_policy.py` exists.
risks_checked:
- Round 1, FINDING 1, CORRECT AND FIXED: no test anywhere pinned any invariant this MR
  establishes, so the whole change could be reverted with the suite green. Verified independently
  (the grep returned zero files) and closed by a 10-assertion sibling test whose every guarded
  invariant was then driven RED by a realistic regression and restored.
- Round 1, FINDING 2, HALF CORRECT: the artifact-size premise was wrong — `manifest.json` is a
  parse artifact already at full project scale — but the missing estimate and limit check were a
  fair hit, now closed with figures from free BigQuery metadata.
- Round 2: traced all 10 assertions against the live YAML, confirming they check properties via
  parsed YAML rather than spelling via text grep, and confirmed no mutation residue survived.
- Round 2: verified the working directory of the new CI step, the artifact paths relative to
  `CI_PROJECT_DIR`, that auth and profile are still valid at that point, and that `data:build:main`
  cannot change when it runs.
- Round 2: confirmed the pinning tests in `test_materialisation_policy.py` and
  `test_ci_data_job_invariants.py` are unaffected, including that the new `seeds:` block does not
  interfere with `_configured_materialisations()`'s regex.
- Round 3: recomputed the corrected arithmetic independently (47,511/112 = 424.2 against
  47,511/78 = 609.1) and confirmed 424 is right, that the safety conclusion holds under either,
  and that nothing else in `contract.md` moved.

## escalations
(none)

<!--
Two decisions were taken by the CPO in chat BEFORE the work, and are recorded in
`.claude/task/escalations.log` rather than here, because neither was a blinded escalation raised
out of review:
  - 2026-08-20, "Both" — turn on persist_docs AND publish dbt docs generate.
  - 2026-08-21, the docs rebuild after each merge to main, which is also the protected_override.

One thing is OUTSTANDING FOR THE CPO and is deliberately not an escalation, because it is a merge
decision and he merges: `!88` should merge before this MR. MR6 is what makes an over-long
description build-breaking, and the gate now in main skips the length check entirely on a bare
{{ doc() }} reference. MR6 is safe either way — the measured over-limit count is zero — so this is
a recommendation, not a blocker.
-->
