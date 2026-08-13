"""Pin three CI data-job invariants that can be broken while every pipeline stays GREEN.

WHY THIS EXISTS
---------------
The first two properties were repaired on 2026-08-08 under GitLab #33, and both share the shape
this repo keeps getting caught by: breaking them produces no red anywhere.

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

  * `git worktree prune` must run before `git worktree add` (GitLab #65, 2026-08-13). The
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
A guard that only read script text would miss the most idiomatic way to reintroduce the flag
(platform-reviewer, round 1).

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
