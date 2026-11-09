"""Pin CI data-job invariants that can be broken while every pipeline stays green.

Values come from PARSED YAML, never raw file text, because the `.gitlab-ci.yml` comments name the
flags they document.
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
    """Same as `_script_lines` but keeps the job boundary."""
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
    """The runner keeps the project dir but not /tmp, so a stale registration breaks `add`."""
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
    """An MR ingest would write production `raw` from an unmerged branch; checked per job."""
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
    """`data:build:mr`'s (build, test) dbt invocations; each is a `>-` scalar, so one line."""
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
    """`--favor-state` stays on the build line and off the test line, which must read the branch."""
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
    """Each merge request builds into its own datasets, isolated by target name and `dataset:`.

    `generate_schema_name` gives models with no `+schema` (the base layer and every seed) bare
    `target.schema`, so only the profile's `dataset:` line isolates them.
    """
    config = _ci_config()
    jobs = _script_lines_by_job(config)
    assert "data:build:mr" in jobs, (
        "data:build:mr not found in .gitlab-ci.yml. If the job was renamed, update this test "
        f"rather than deleting it. Jobs seen: {sorted(jobs)}"
    )
    lines = [" ".join(line.split()) for line in jobs["data:build:mr"]]

    # Asserted on the derivation rather than a literal name, so reformatting the export is safe.
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


def test_the_mr_build_rebuilds_every_changed_seed() -> None:
    """dbt fingerprints a seed only up to 1 MB, so a larger changed seed needs a path selector."""
    build, _ = _mr_dbt_invocations()
    lines = [" ".join(line.split()) for line in _script_lines_by_job(_ci_config())["data:build:mr"]]

    def only(prefix: str) -> int:
        found = [i for i, ln in enumerate(lines) if ln.startswith(prefix)]
        assert len(found) == 1, (
            f"data:build:mr no longer has exactly one `{prefix}` line. Without it a changed seed "
            f"over 1 MB is invisible to state:modified+. Lines seen: {lines}"
        )
        return found[0]

    diff_at, seeds_at, build_at = only("SEED_DIFF="), only("CHANGED_SEEDS="), lines.index(build)
    diff, seeds = lines[diff_at], lines[seeds_at]
    for part in ("git diff", "${CI_MERGE_REQUEST_DIFF_BASE_SHA:?}", "dbt_project/seeds/", "|| exit 1"):
        assert part in diff, (
            f"the SEED_DIFF line lost `{part}`: it must list the seeds this merge request changed "
            f"against its diff base and stop the job when that fails. Line: {diff}"
        )
    # A pipe after `git diff` would report the last command's status and hide the failure.
    assert diff.replace("|| exit 1", "").count("|") == 0, (
        f"`git diff` feeds a pipe, so its failure no longer stops the job. Line: {diff}"
    )
    for part in ("$SEED_DIFF", "path:%s+", "${f#dbt_project/}"):
        assert part in seeds, (
            f"the CHANGED_SEEDS line lost `{part}`: each changed seed must become a path selector "
            f"with `+`, or its readers are not rebuilt. Line: {seeds}"
        )
    assert " $CHANGED_SEEDS " in build and '"$CHANGED_SEEDS"' not in build, (
        "data:build:mr's `dbt build` must pass $CHANGED_SEEDS unquoted, one selector per word, "
        f"next to state:modified+. Line: {build}"
    )
    assert "state:modified+" in build
    assert diff_at < seeds_at < build_at, (
        "SEED_DIFF, CHANGED_SEEDS and the `dbt build` that reads them are out of order."
    )


SELECTORS_FILE = ROOT / "dbt_project" / "selectors.yml"


def _selector_paths(criteria: list) -> set[str]:
    return {c["value"] for c in criteria if isinstance(c, dict) and c.get("method") == "path"}


def test_the_staging_stage_excludes_every_layer_the_downstream_stage_builds() -> None:
    """A test joins a stage when any parent does, so the staging stage excludes later layers."""
    main_build = [ln.strip() for ln in _script_lines_by_job(_ci_config())["data:build:main"]]
    stages = [ln.split()[3] for ln in main_build if ln.startswith("dbt build --selector")]
    assert stages == ["staging", "downstream"], (
        f"data:build:main no longer builds the staging stage, then the downstream stage: {stages}"
    )
    selectors = {
        s["name"]: s["definition"]
        for s in yaml.safe_load(SELECTORS_FILE.read_text(encoding="utf-8"))["selectors"]
    }
    downstream = _selector_paths(selectors["downstream"].get("union", []))
    staging = selectors["staging"].get("union", [selectors["staging"]])
    excluded = set().union(*(_selector_paths(c["exclude"]) for c in staging if "exclude" in c))
    assert "models/1_staging" in _selector_paths(staging)
    assert downstream, "the downstream selector builds no path"
    assert downstream <= excluded, (
        f"the staging selector does not exclude {sorted(downstream - excluded)}: a test reading one of "
        "those layers and a staging model would run in the staging stage against the previous build's table"
    )
