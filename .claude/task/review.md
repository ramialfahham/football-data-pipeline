# Review — perf/33-item9-staging-as-table — 2026-08-12

diff_sha256: 23db5a935eb88f4edf77ebfb00cb0fb08b8a9b91d498c640fd272011a2f15725

rounds: 3

<!--
⚠ REBOUND AFTER A REBASE, and the cause is worth recording because it will recur.
The first binding was `f8238905…`, computed on base `a2b4184`. CI recomputed a different value
and `validate:governance` FAILed. Not a builder error and not the documented multi-commit trap:
`#63` (`fix/63-review-hash-content-identity`) merged to `main` WHILE this branch was in review
and CHANGED THE HASH ALGORITHM ITSELF — from hashing the rendered patch text to hashing content
identity (`git diff --raw`), in both `.claude/hooks/git_discipline.py` and
`scripts/check_task_artifacts.py`. This branch predated it, so the local side used the old
algorithm and the merged-result pipeline used the new one. They could not agree.
Resolved by rebasing onto `b4b2414`, recomputing with the new algorithm, and collapsing to one
commit. THE REVIEWED CONTENT DID NOT CHANGE: `git diff --staged --name-only main` is the same 12
paths the four reviewers passed, and none of #63's files appear in this branch's diff. So the
verdicts below stand and were not re-run — only the binding moved.
-->


<!--
Round 1: scope-auditor PASS (but flagged the drift-guard gap as a follow-up rather than a
         defect); analytics-engineer FAIL and platform FAIL, independently, on the SAME thing —
         only the per-model-override half of the guard was extended to staging, leaving the
         doc-drift half hardcoded to 2_base, in a task whose thesis is that this exact
         regression class needs mechanical enforcement. Platform additionally found the new
         policy token in layering.md split across a markdown line wrap, which would have
         silently defeated the check being added.
Round 2: guards generalised per layer. On its FIRST run the generalised sweep found three stale
         claims the manual done_when sweep had walked past — two ingestion comments and
         .claude/active_work.md. analytics-engineer, platform and data-engineer PASS.
         scope-auditor FAIL: the active_work.md exclusion cited a GitLab issue a blinded
         reviewer cannot read, while suppressing a real finding.
Round 3: the ownership ruling recorded verbatim in escalations.log, the exclusion comment
         rewritten to disclose what it suppresses and how to reverse it, the staleness reported
         to the owning stream on #33, and the cosmetically misnamed test renamed. All four PASS.
-->

## scope-auditor
VERDICT: PASS
risks_checked:
- Patch file set matches `scope_paths` at every round; no `dbt_project/models/**` edit, no
  ingestion behaviour change, and item 15 correctly NOT bundled.
- CPO authority for items 9+10 ("definitely") recorded in `escalations.log` before `contract.md`
  cited it, together with the premise check the CPO demanded — that staging was never previously
  a table, evidenced by replaying the config block at every commit from `1f422c0` to `4899025`.
- RECURRING COST declaration attacked for honesty: it states a MEASURED net reduction, discloses
  that the figure is SMALLER than the issue it cites claims (`RAW_APIF_TRANSFERS` 6.99 GiB ->
  0.178 GiB post item-8b), and no site oversells it.
- Both `amendments:` entries checked against the diff for undisclosed widening — the break-test
  method change widened nothing, and the two-file ingestion growth is confined to comment text
  and cites the 2026-08-08 standing rule, verified present in the log.
- ⚠ FAILED round 2 on the `.claude/active_work.md` exclusion: a real stale claim suppressed on an
  authority a blinded reviewer could not read. Re-verified at round 3 that the ruling is now
  quoted verbatim in `escalations.log`, that the exclusion comment names the offender it
  suppresses and the condition for reversing it, and that the narrowing is disclosed rather than
  hidden.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Staging-as-table correctness: read representative models (`stg_apif__player_profiles`,
  `stg_apif__players`, `stg_apif__fixtures_next`). Snapshot-selection and
  incremental-accumulation patterns are unaffected — a view and a table over the same SELECT
  return the same rows, staging is not incremental, so no `--full-refresh` and no grain hazard.
- Mid-run ordering hazard: read `deploy/nightly/entrypoint.sh` — ingestion completes before
  `dbt build` starts, so raw is not written during the build and a stored staging table cannot
  serve staler data than a view would have. No hazard.
- "No lineage change" verified by construction, not assertion: zero `dbt_project/models/**/*.sql`
  files appear in the diff.
- Zero per-model materialisation overrides exist in `1_staging` today, so the new guard is not
  retroactively firing on anything undisclosed.
- Cost reasoning cross-checked across `contract.md`, `escalations.log`, `dbt_project.yml`,
  `layering.md` — consistent, and the stale-#33-figures caveat is stated in all of them.
- ⚠ FAILED round 1 on the asymmetric guard; re-verified at round 2 that `POLICY_SITES`,
  `PROSE_SUBJECT` and all three drift tests now loop per layer with no base-only mechanism left.
- Prose regex traced by hand against the past-tense history that must stay writable
  ("Staging and base were BOTH views", "Both were views", `report_bq_cost.py:77`) — none match,
  because the intervening `were`/`BOTH` break the alternation. No false positives.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The base path is behaviourally identical after the refactor: with `layer_label="base"`,
  `.capitalize()` reproduces the original message byte-for-byte, and `check_base_layer` calls the
  extracted helper with the same arguments.
- `BASE_MATERIALIZED` -> `PER_MODEL_MATERIALIZED` rename: grepped the tree; no live reference to
  the old name survives.
- The new guard is not decoration — verified against the contract's recorded break test, which
  ran the real function over the real body of `stg_apif__teams.sql` in three states and produced
  0 errors only for the unmodified one.
- ⚠ FAILED round 1 on two counts: base-only drift guards, and a policy token split across a
  markdown line wrap in `layering.md` (a live instance of the "line-based grep misses a phrase
  straddling a line break" hazard). Both fixed and re-verified.
- `POLICY_SITES` becoming a dict: traced every consumer; both tests iterate `.items()` and use
  the per-layer tuple. No stale flat-tuple assumption survives.
- Confirmed `.claude/hooks/dbt_layer_gate.py` and `docs/roles/analytics_engineer.md` are
  genuinely silent on staging materialisation, so registering them for `1_staging` would be
  incorrect rather than merely omitted.
- The dual-token case traced through the loop: a file quoting the `1_staging` token while
  registered only under `2_base` is still caught on the `1_staging` pass.
- Test rename verified as a pure rename — no `pytest -k` selector, doc or other test references
  the old name.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Read the actual diff hunks for both ingestion files: each changes exactly one word inside a
  `#` comment; no code, logic or config line is touched.
- `bigquery.py:121`'s reasoning concerns the RAW table's partition-filter permissiveness, not
  staging's own materialisation, so it holds unchanged under table materialisation.
- `loads/teams.py:63`'s justification for injecting `(league.id, league.season)` at ingest time
  describes SELECT-level extraction behaviour, identical whether the result persists as a view or
  a table.
- Swept `ingestion/**` case-insensitively for any other place assuming staging is a view — only
  the two edited lines; no missed site.
- Confirmed the registry/onboarding path (`docs/competition_registry.yml`, `data_contract.md`,
  `.gitlab-ci.yml`, `deploy/nightly/**`) is absent from the diff, and that nothing here drops the
  `/injuries` ingest or table — item 15 remains a separate, deliberately unstarted task.

## escalations
(none — the two CPO rulings this task rests on, "definitely" for items 9+10 and the
`.claude/active_work.md` ownership ruling, are recorded in `.claude/task/escalations.log` and were
verified there by `scope-auditor`. No question was put to the CPO during the review cycle.)
