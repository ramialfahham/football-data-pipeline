"""Pin three CI data-job invariants that can be broken while every pipeline stays GREEN.

WHY THIS EXISTS
---------------
The first two properties were repaired under GitLab #33, and both share the shape this repo
keeps getting caught by: breaking them produces no red anywhere.

  * `API_FOOTBALL_SKIP_INGEST_LOCK=1` sat in three CI ingest invocations and disabled the BigQuery
    ingest lease. `docs/operations_guide.md:149` forbids it — "Local debugging only; never
    production" — and these ingests ARE production: `ingestion/api_football/settings.py:31`
    defaults the raw dataset to `raw` and `API_FOOTBALL_BIGQUERY_DATASET` is set nowhere in CI. So
    an MR pipeline wrote production raw from an unmerged branch with the lock off, and nothing
    failed. Re-adding the flag would restore that silently.

  * `.data_paths_prod` decides whether a push to main rebuilds the prod warehouse. Drop one entry —
    `dbt_project/models/**/*`, say — and `data:build:main` stops firing on model merges. Prod goes
    quietly stale, and because every MR build defers to prod with `--defer --favor-state`, the
    staleness propagates into MR validation with nothing red anywhere. The single `.data_paths`
    anchor used to make MR/prod drift structurally impossible; splitting it traded that guarantee
    for a comment, so the guarantee is re-established here as an assertion.

  * `git worktree prune` must run before `git worktree add` (GitLab #65). The
    self-hosted runner keeps the project directory between jobs but gives each job a fresh `/tmp`,
    so a worktree registration in the persisted `.git/worktrees/` outlives the directory it points
    at and the next `add` dies with "missing but already registered worktree". Delete the prune and
    the damage is delayed, not immediate: the next pipeline on a given runner slot passes (it
    creates the registration) and the one after it fails. That delay is what puts it in this
    module — the breakage does not show up in the pipeline that caused it.

HOW IT IS SHAPED, AND WHY
-------------------------
Values come from PARSED YAML, never from raw file text. That matters concretely: the
`.gitlab-ci.yml` comment block documenting the lock fix NAMES `API_FOOTBALL_SKIP_INGEST_LOCK`, so a
text grep would flag the documentation of the defect as the defect.

The lock check reads `variables:` as well as script lines. An env var set through a `variables:`
mapping — global, `default:`, or per job — reaches the ingest exactly as an inline assignment does,
and `orchestrator.py:95` literally tells the operator to set that variable when the lease is held.
A guard that only read script text would miss the most idiomatic way to reintroduce the flag.

WHAT IS DELIBERATELY *NOT* PINNED HERE
--------------------------------------
Singular tests run twice on the prod build — once inside each `dbt build --selector`, once in the
trailing `dbt test` step. #33 item 3 proposed removing that duplication; it was WITHDRAWN after
review, because `dbt build` adds test edges (`dbt/task/build.py:134`) and skips a failed test's
dependents (`build.py:80`), so the in-build run is a write-blocking gate and the trailing run is a
post-write report. An earlier version of this module asserted the "de-duplicated" arrangement was
safe, which would have certified the regression rather than caught it. The reasoning now lives in a
comment at the `dbt build --selector` lines, where someone about to optimise will read it.
"""

from __future__ import annotations

import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
CI_FILE = ROOT / ".gitlab-ci.yml"

# The inputs that can change what dbt COMPILES. A push to main touching any of these
# must rebuild the prod warehouse, so .data_paths_prod has to keep covering them.
DBT_COMPILE_INPUTS = frozenset(
    {
        "dbt_project/models/**/*",
        "dbt_project/macros/**/*",
        "dbt_project/seeds/**/*",
        "dbt_project/snapshots/**/*",
        "dbt_project/tests/**/*",
        "dbt_project/*.yml",
    }
)


def _ci_config() -> dict:
    return yaml.safe_load(CI_FILE.read_text(encoding="utf-8"))


def _script_lines(config: dict) -> list[str]:
    lines: list[str] = []
    for node in config.values():
        if not isinstance(node, dict):
            continue
        for section in ("before_script", "script", "after_script"):
            for entry in node.get(section) or []:
                if isinstance(entry, str):
                    # A `|` block scalar arrives as one multi-line string.
                    lines.extend(entry.splitlines())
    return lines


def _script_lines_by_job(config: dict) -> dict[str, list[str]]:
    """Same extraction as `_script_lines`, but keeping the job boundary.

    Ordering within a job is the whole point for the worktree check — a `prune` sitting in some
    OTHER job would satisfy a flattened scan while fixing nothing.
    """
    per_job: dict[str, list[str]] = {}
    for name, node in config.items():
        if not isinstance(node, dict):
            continue
        lines: list[str] = []
        for section in ("before_script", "script", "after_script"):
            for entry in node.get(section) or []:
                if isinstance(entry, str):
                    lines.extend(entry.splitlines())
        if lines:
            per_job[name] = lines
    return per_job


def _declared_variables(config: dict) -> list[tuple[str, str]]:
    """Every (name, value) from a `variables:` mapping — global, `default:`, or per job."""
    found: list[tuple[str, str]] = []

    def collect(where: str, block) -> None:
        if isinstance(block, dict):
            for name, value in block.items():
                found.append((f"{where}.{name}", str(value)))

    collect("<global>", config.get("variables"))
    for key, node in config.items():
        if isinstance(node, dict):
            collect(key, node.get("variables"))
    return found


def test_ci_never_disables_the_ingest_lock():
    """#33 item 4. The flag is local-debugging-only and CI ingests write production raw."""
    config = _ci_config()

    offenders = [
        line.strip()
        for line in _script_lines(config)
        if "API_FOOTBALL_SKIP_INGEST_LOCK" in line
    ]
    offenders += [
        f"variables: {name}={value}"
        for name, value in _declared_variables(config)
        if "API_FOOTBALL_SKIP_INGEST_LOCK" in name
    ]

    assert offenders == [], (
        "API_FOOTBALL_SKIP_INGEST_LOCK is set in .gitlab-ci.yml. It disables the BigQuery "
        "ingest lease, and docs/operations_guide.md:149 restricts it to local debugging. CI "
        "ingests write the production `raw` dataset (ingestion/api_football/settings.py:31), so "
        f"this is production. Offending: {offenders}"
    )


def test_the_prod_trigger_still_covers_every_dbt_compile_input():
    """#33 item 2. Splitting the anchor removed the structural no-drift guarantee; restore it.

    Two directions, because the split can fail either way:
      * too NARROW -> a model merge stops rebuilding prod, silently.
      * wider than the MR anchor -> the prod build fires on something the MR build never
        validated, which is the drift the single anchor originally prevented.
    """
    config = _ci_config()
    mr_paths = config.get(".data_paths_mr")
    prod_paths = config.get(".data_paths_prod")

    assert isinstance(mr_paths, list) and mr_paths, ".data_paths_mr is missing or not a list"
    assert isinstance(prod_paths, list) and prod_paths, ".data_paths_prod is missing or not a list"

    missing = DBT_COMPILE_INPUTS - set(prod_paths)
    assert not missing, (
        f".data_paths_prod no longer covers {sorted(missing)}. A push to main touching those "
        "would not rebuild the prod warehouse, so prod goes stale — and every MR build defers to "
        "prod as its baseline, so the staleness spreads with nothing turning red."
    )

    wider = set(prod_paths) - set(mr_paths)
    assert not wider, (
        f".data_paths_prod contains {sorted(wider)}, which .data_paths_mr does not. The prod "
        "build would then fire on a change the MR build never validated."
    )


def test_every_worktree_add_is_preceded_by_a_prune():
    """#65. The runner persists the project dir but not /tmp, so registrations go stale.

    Written to the CLASS, not to the one line that broke: any job that adds a worktree must prune
    first, in its own script. A second worktree call added later is covered without touching this
    test — a list of known offenders is precisely what has holed guards here before.

    Read from parsed YAML rather than file text on purpose. The fix carries a comment naming both
    `worktree` and `prune`, so a text scan would match the documentation of the fix and pass
    whether or not the command is actually there.
    """
    offenders = []
    for job, lines in _script_lines_by_job(_ci_config()).items():
        add_at = next(
            (i for i, line in enumerate(lines) if "git worktree add" in line), None
        )
        if add_at is None:
            continue
        prune_at = next(
            (i for i, line in enumerate(lines) if "git worktree prune" in line), None
        )
        if prune_at is None or prune_at > add_at:
            offenders.append(
                f"{job}: `git worktree add` at script index {add_at}, prune "
                + ("absent" if prune_at is None else f"at {prune_at} (too late)")
            )

    assert offenders == [], (
        "A job adds a git worktree without pruning stale registrations first. The self-hosted "
        "runner keeps the project directory between jobs while each job gets a fresh /tmp, so the "
        "registration in .git/worktrees/ outlives its directory and `git worktree add` exits 128 "
        "with 'missing but already registered worktree' (GitLab #65). This does not fail the "
        "pipeline that removes the prune — it fails the NEXT one on that runner slot. "
        f"Offending: {offenders}"
    )


def test_mr_data_build_never_ingests():
    """GitLab #73. `data:build:mr` must never run the API-Football ingest.

    An ingest from an MR pipeline writes the PRODUCTION `raw` dataset
    (`ingestion/api_football/settings.py:31` defaults it, and `API_FOOTBALL_BIGQUERY_DATASET` is
    set nowhere in CI) from an UNMERGED branch. `.gitlab-ci.yml` flagged that as open under #33
    item 13; #73 closed it for the MR path by deleting the bootstrap step.

    NOTHING IS LOST BY THE DELETION, which is why re-adding it is pure regression rather than a
    trade: `data:build:main` runs the identical `get_new_league_codes.py` + ingest sequence before
    its dbt builds, on a protected branch that legitimately holds `API_FOOTBALL_API_KEY`.

    This is pinned rather than left to prose because the failure is INVISIBLE. Re-adding the step
    turns the pipeline red only when the protected variable is withheld; on any branch that DOES
    receive the key it would silently write prod again. The repo's own record is that prose-only
    corrections recur (33 of 50) and mechanised ones do not.

    Asserted per JOB, not across the file: `data:build:main` and `data:nightly` legitimately
    contain both tokens, so a file-wide grep would be wrong in both directions.
    """
    jobs = _script_lines_by_job(_ci_config())
    assert "data:build:mr" in jobs, (
        "data:build:mr not found in .gitlab-ci.yml. If the job was renamed, update this test "
        f"rather than deleting it. Jobs seen: {sorted(jobs)}"
    )

    forbidden = ("ingestion.api_football.main", "get_new_league_codes")
    offenders = [
        line.strip()
        for line in jobs["data:build:mr"]
        if any(token in line for token in forbidden)
    ]

    assert offenders == [], (
        "data:build:mr invokes the API-Football ingest. That writes the PRODUCTION `raw` dataset "
        "from an unmerged branch — the hazard #73 removed and #33 item 13 named. The post-merge "
        "`data:build:main` job already ingests any new league, so nothing needs this here. "
        f"Offending: {offenders}"
    )


def _mr_dbt_invocations() -> tuple[str, str]:
    """`data:build:mr`'s (build, test) dbt invocations, as single strings.

    Both are `>-` folded scalars in the YAML, so each arrives as ONE line with its flags
    space-separated — which is why matching on substrings here is safe rather than fragile.
    """
    jobs = _script_lines_by_job(_ci_config())
    assert "data:build:mr" in jobs, (
        "data:build:mr not found in .gitlab-ci.yml. If the job was renamed, update this test "
        f"rather than deleting it. Jobs seen: {sorted(jobs)}"
    )
    lines = [" ".join(line.split()) for line in jobs["data:build:mr"]]
    builds = [ln for ln in lines if ln.startswith("dbt build ")]
    tests = [ln for ln in lines if ln.startswith("dbt test ")]
    assert len(builds) == 1, f"expected exactly one `dbt build` in data:build:mr, saw {builds}"
    assert len(tests) == 1, f"expected exactly one `dbt test` in data:build:mr, saw {tests}"
    return builds[0], tests[0]


def test_the_mr_singular_test_gate_reads_the_branch_not_prod() -> None:
    """`--favor-state` belongs on data:build:mr's BUILD line and must never return to its TEST line.

    THE DEFECT THIS PINS (GitLab #92). Both invocations carried
    `--defer --favor-state`. `--favor-state` resolves every `ref()` to the DEFERRED (prod) relation
    even when the current run has just built that model. On the `dbt build` line that is correct and
    load-bearing — a model being BUILT must take its upstreams from prod rather than from a
    superseded table, and a node dbt is building is not deferred anyway. (That reason is narrower
    since the per-merge-request datasets landed: "another MR's leftovers" cannot occur any more, but
    an EARLIER PIPELINE OF THE SAME merge request can leave a superseded table — build a model, then
    revert it to match main and it drops out of `state:modified+` — and `--defer` alone would prefer
    it.) On the `dbt test`
    line nothing is being built, so the identical flag threw away the MR's own models and pointed
    all 30 singular tests at PRODUCTION. The DQ gate was green because prod was healthy, not because
    the branch was.

    WHY IT IS PINNED HERE. This module exists for invariants that can be broken while every pipeline
    stays GREEN, and this is one: re-adding `--favor-state` to the test line restores the whole
    defect with pytest, sqlfluff, every offline gate and the pipeline itself all still green — the
    tests simply go back to reporting on the wrong database. Before this assertion the only thing
    standing in the way was a comment, and a confident comment is precisely what let the defect
    survive in the first place (the paragraph above the line asserted the isolation the flag
    prevented).

    BOTH HALVES ARE ASSERTED, deliberately. Pinning only the test line would let someone "restore
    symmetry" by stripping the flag from the BUILD line instead — which breaks isolation in the
    other direction, is a different bug, and would pass a one-sided guard.

    Reproduction, one job, ninety seconds apart: pipeline 2796272877 job 16145201830 created
    `ci_marts.mart_team_season_insights` with a renamed column, PASSed
    `assert_mart_team_season_insights_metric_consistency` against it inside the build, then failed
    the SAME test in the trailing run with "Unrecognized name: points_capture_pct; Did you mean
    points_capture?" — a column that exists only in prod.
    """
    build, test = _mr_dbt_invocations()

    assert "--favor-state" not in test, (
        "data:build:mr's `dbt test` line carries --favor-state again. That resolves every ref() to "
        "PRODUCTION even for models this run just built, so the 30 singular tests stop testing the "
        "branch and re-report on prod — green because prod is healthy, not because the change is "
        "(GitLab #92). It also makes any column rename unmergeable: prod gains the column only "
        f"after the merge, so the gate can never go green first. Line: {test}"
    )
    for flag in ("--defer", "--state /tmp/main-state"):
        assert flag in test, (
            f"data:build:mr's `dbt test` line lost `{flag}`. Deferral itself must STAY — without it "
            "an upstream this MR did not build resolves to nothing instead of to prod. Only "
            f"--favor-state was removed. Line: {test}"
        )

    assert "--favor-state" in build, (
        "data:build:mr's `dbt build` line lost --favor-state. It is correct THERE and the asymmetry "
        "with the test line is the whole of #92's first half. A model being built must take its "
        "upstreams from prod rather than from a superseded table — an earlier pipeline of THIS "
        "merge request can leave one (build a model, then revert it to match main and it drops "
        "out of state:modified+), and --defer alone would prefer it. Do not make the two lines "
        f"match. Line: {build}"
    )


def test_each_merge_request_builds_into_its_own_datasets() -> None:
    """No merge request may read another one's tables. #92 second half.

    THE DEFECT THIS PINS, which only became reachable once the half above landed. Every merge
    request used to build into ONE shared set of `ci_*` datasets. While the singular tests read
    PRODUCTION that was invisible; the moment they read the ci datasets instead, a merge request
    that rebuilt nothing began reading whatever another branch had left there. One merge request
    that changed no models went red on THREE tests against tables a sibling had built an hour
    earlier — headline error "Unrecognized name: points_capture; Did you mean
    points_capture_pct?", the exact mirror of the failure that started #92.

    BOTH HALVES OF THE ISOLATION ARE ASSERTED, and the second is not decoration.
    `macros/generate_schema_name.sql` prefixes a model that HAS a custom schema with `target.name`,
    so the per-MR target name isolates the four layer datasets. But it returns BARE `target.schema`
    for a model with NO `+schema` — which is the whole `2_base` layer and EVERY seed,
    `metric_catalogue` among them. Their isolation rests entirely on the profile's `dataset:` line.
    Pinning only the target name would let someone revert `dataset:` to a shared literal and put the
    base tables and the seed back in one shared dataset, silently, reinstating that failure on
    the very relation two dbt guards were rewritten to depend on — an omission an earlier version
    of this test had.

    A literal `--target ci` anywhere in the job, or a `DBT_CI_TARGET` that does not carry the merge
    request id, restores the shared workspace with every test and the whole pipeline still green —
    the same invisible-breakage shape as this module's siblings, which is why it is pinned here
    rather than left to the comments in the YAML.
    """
    config = _ci_config()
    jobs = _script_lines_by_job(config)
    assert "data:build:mr" in jobs, (
        "data:build:mr not found in .gitlab-ci.yml. If the job was renamed, update this test "
        f"rather than deleting it. Jobs seen: {sorted(jobs)}"
    )
    lines = [" ".join(line.split()) for line in jobs["data:build:mr"]]

    # Asserted on the DERIVATION, not on a literal name, so reformatting the export does not break
    # this — but dropping the merge-request id from it does, and that is the property.
    derivations = [ln for ln in lines if "DBT_CI_TARGET=" in ln]
    assert derivations, (
        "data:build:mr no longer derives DBT_CI_TARGET. Without it every merge request builds into "
        "the same datasets and one branch's tables become another's upstreams (#92)."
    )
    assert any("CI_MERGE_REQUEST_IID" in ln for ln in derivations), (
        "DBT_CI_TARGET is set without CI_MERGE_REQUEST_IID, so it is the same for every merge "
        f"request — the shared workspace is back. Derivation seen: {derivations}"
    )

    shared = [ln for ln in lines if ln.startswith("dbt ") and "--target ci" in ln]
    assert shared == [], (
        "a dbt invocation in data:build:mr targets a literal shared `ci` target. Every dbt command "
        'in this job must use "$DBT_CI_TARGET" so the merge request writes its own datasets. '
        f"Offending: {shared}"
    )
    for line in [ln for ln in lines if ln.startswith("dbt ")]:
        assert "$DBT_CI_TARGET" in line, (
            f"a dbt invocation in data:build:mr does not use $DBT_CI_TARGET: {line}"
        )

    # The profile's `dataset:` is the OTHER half — base models and seeds carry no +schema and ride
    # bare target.schema, so they are isolated by this line alone.
    profile = "\n".join(_script_lines(config))
    dataset_lines = [
        " ".join(ln.split()) for ln in profile.splitlines()
        if ln.strip().startswith("dataset:")
    ]
    assert "dataset: ${DBT_CI_TARGET}" in dataset_lines, (
        "the CI profile's `dataset:` is not ${DBT_CI_TARGET}. The base models and every seed "
        "(metric_catalogue included) have no +schema, so generate_schema_name gives them bare "
        "target.schema — this line is the only thing isolating them per merge request. "
        f"dataset: lines seen: {dataset_lines}"
    )
