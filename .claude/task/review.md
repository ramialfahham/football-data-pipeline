# Review — chore/pin-requirements — 2026-06-13

> Issue #425 (audit F20): pin the used dep + remove dead deps from root
> requirements.txt. Required reviewers for requirements*.txt: scope-auditor +
> cto-reviewer. Two cold blinded iterations: iteration-1 scope-auditor FAIL (the
> contract asserted a CPO ruling that was not recorded in any durable artifact);
> resolved by recording the ruling in .claude/task/escalations.log (entry
> 2026-06-13) and citing it in decisions_taken — NOT by escalation, since the
> ruling genuinely exists (CPO chose "Pin + remove dead", incl. pandas, this
> session). Iteration-2: both reviewers PASS against the hash below.

diff_sha256: 5b6d79ee9aa03da0c7ee99fae4ef4b748629175aa5d0134c40da53250c0455c6

## scope-auditor
VERDICT: PASS
risks_checked:
- CPO authority for the scope (esp. pandas, NOT named in F20): verified the ruling
  is recorded in `.claude/task/escalations.log` (2026-06-13 entry, question 1) and
  that it genuinely approves removing pandas — the question context and chosen option
  both named pandas explicitly, so the removal is CPO-approved, not a silent §10 act.
  Scope_paths limited to requirements.txt + contract.md; no protected path touched;
  nothing smuggled beyond the declared scope.
- functions-framework removal safety boundary: confirmed `ingestion/api_football/main.py`
  (try/except ImportError, ~lines 36-41) makes functions-framework optional and falls
  back gracefully, so the removal is structurally sound; the only live importer is the
  ingestion entrypoint, which keeps its own declaration. Removed deps (bs4, pandas)
  verified unused by grep across all repo .py (zero imports / DataFrame).

## cto-reviewer
VERDICT: PASS
risks_checked:
- functions-framework isolation: `ingestion/api_football/main.py` is the sole importer;
  `ingestion/api_football/requirements.txt` retains functions-framework undisturbed; no
  CI workflow (python-ci, ci-data-build, ci-validate, dbt-scheduled) installs root +
  ingestion requirements in the same pip invocation (each uses exactly one `-r`), so
  dropping the root entry cannot reach the ingestion entrypoint.
- requests==2.33.1 transitive compatibility: read dist-info METADATA — google-cloud-bigquery
  3.25.0 (`requests<3.0.0,>=2.21.0`), google-api-core 2.30.3 (`<3.0.0,>=2.20.0`),
  dbt-core 1.7.19 (`<3.0.0`) all satisfied by 2.33.1; the pinned version matches the
  installed/tested venv. bs4/pandas confirmed zero direct imports (transitive-only in
  .venv). pyarrow left unpinned is a CPO-recorded, intentional deferral (decisions_reserved
  + escalations.log), not an oversight — out of this task's scope.

## escalations
(none — iteration-1 FAIL resolved by recording the existing CPO ruling; both reviewers PASS in iteration-2.)
