"""Pins the invariants that make `persist_docs` safe, because breaking them produces no red.

Values come from parsed YAML, never raw file text, and assert properties rather than nesting.
"""

from __future__ import annotations

import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
DBT_PROJECT = ROOT / "dbt_project" / "dbt_project.yml"
CI_FILE = ROOT / ".gitlab-ci.yml"
MODELS_DIR = ROOT / "dbt_project" / "models"

WANT = {"relation": True, "columns": True}


def _dbt_project() -> dict:
    return yaml.safe_load(DBT_PROJECT.read_text(encoding="utf-8"))


def _ci() -> dict:
    return yaml.safe_load(CI_FILE.read_text(encoding="utf-8"))


def _walk(node):
    """Yield every mapping nested anywhere under `node`, including `node` itself."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


# --------------------------------------------------------------------------------------------
# dbt_project.yml
# --------------------------------------------------------------------------------------------

def test_persist_docs_is_enabled_for_models():
    project = _dbt_project()
    block = project["models"]["football_data_pipeline"]
    assert block.get("+persist_docs") == WANT, (
        "models.football_data_pipeline must set +persist_docs {relation: true, columns: true}; "
        f"found {block.get('+persist_docs')!r}. Without it every description stops reaching "
        "BigQuery and the field goes back to having no reader."
    )


def test_persist_docs_is_enabled_for_seeds():
    project = _dbt_project()
    assert "seeds" in project, (
        "dbt_project.yml has no `seeds:` block. It exists to carry +persist_docs — seeds held 38% "
        "of the contaminated text the description audit measured."
    )
    block = project["seeds"]["football_data_pipeline"]
    assert block.get("+persist_docs") == WANT, (
        "seeds.football_data_pipeline must set +persist_docs {relation: true, columns: true}; "
        f"found {block.get('+persist_docs')!r}."
    )


def test_the_seeds_block_never_sets_a_schema():
    """Seeds ride `target.schema` via `generate_schema_name`, so a `+schema` would relocate them."""
    project = _dbt_project()
    offenders = [
        key
        for mapping in _walk(project["seeds"])
        for key in mapping
        if key in ("+schema", "schema")
    ]
    assert offenders == [], (
        f"the seeds: block sets {offenders} — it must carry +persist_docs and nothing else. "
        "Seeds ride target.schema; setting a schema here silently relocates every seed."
    )


def test_no_model_overrides_persist_docs_per_model():
    """The layer/project decides; a per-model override lets one model drift off the policy."""
    offenders = [
        path.relative_to(ROOT).as_posix()
        for path in sorted(MODELS_DIR.rglob("*.sql"))
        if "persist_docs" in path.read_text(encoding="utf-8")
    ]
    assert offenders == [], f"models setting persist_docs themselves: {offenders}"


def test_no_layer_turns_persist_docs_off():
    """Enabled at the top is worth nothing if a layer below disables it."""
    project = _dbt_project()
    disabled = [
        mapping["+persist_docs"]
        for mapping in _walk(project["models"]["football_data_pipeline"])
        if "+persist_docs" in mapping and mapping["+persist_docs"] != WANT
    ]
    assert disabled == [], (
        f"a nested block overrides +persist_docs with {disabled!r}. It must stay "
        "{relation: true, columns: true} everywhere it appears."
    )


# --------------------------------------------------------------------------------------------
# .gitlab-ci.yml
# --------------------------------------------------------------------------------------------

def _jobs_running(command_fragment: str) -> list[str]:
    ci = _ci()
    hits = []
    for name, job in ci.items():
        if not isinstance(job, dict) or "script" not in job:
            continue
        script = job["script"]
        lines = script if isinstance(script, list) else [script]
        if any(command_fragment in str(line) for line in lines):
            hits.append(name)
    return sorted(hits)


def test_docs_are_generated_exactly_once_and_only_on_main():
    """Docs content comes from the repo, so the nightly would republish identical pages, and the MR
    build's catalog covers only what one branch changed."""
    jobs = _jobs_running("dbt docs generate")
    assert jobs == ["data:build:main"], (
        f"`dbt docs generate` runs in {jobs}; it must run in data:build:main and nowhere else. "
        "data:nightly and data:build:mr were both explicitly rejected."
    )


def test_the_docs_command_is_static_and_targets_prod():
    """`--static` yields the single self-contained page; prod is the only complete catalog."""
    job = _ci()["data:build:main"]
    line = next(ln for ln in job["script"] if "dbt docs generate" in str(ln))
    assert "--static" in line, f"docs generate must pass --static; found: {line}"
    assert "--target prod" in line, f"docs generate must pass --target prod; found: {line}"


def test_the_docs_step_may_not_fail_silently():
    """The step runs after prod is built and tested, so a failure costs signal, never data."""
    job = _ci()["data:build:main"]
    assert not job.get("allow_failure", False), (
        "data:build:main must not set allow_failure — a silently skipped docs build is the "
        "'green but did nothing' shape of #904."
    )


def test_the_catalog_is_published():
    """`catalog.json` alone shows a column that exists in BigQuery but in no .yml."""
    job = _ci()["data:build:main"]
    paths = job.get("artifacts", {}).get("paths", [])
    assert any(p.endswith("catalog.json") for p in paths), (
        f"data:build:main must publish catalog.json; artifacts.paths = {paths}. GitLab #82 "
        "depends on it."
    )
    assert any(p.endswith("static_index.html") for p in paths), (
        f"data:build:main must publish static_index.html; artifacts.paths = {paths}."
    )


def test_the_projection_check_runs_in_that_job_after_the_docs_line():
    """The check reads the catalog.json the docs line just wrote, complete only in this job."""
    assert _jobs_running("check_yml_vs_projection.py") == ["data:build:main"], (
        "check_yml_vs_projection.py must run in data:build:main and nowhere else."
    )
    script = [str(ln) for ln in _ci()["data:build:main"]["script"]]
    docs = next(i for i, ln in enumerate(script) if "dbt docs generate" in ln)
    check = next(i for i, ln in enumerate(script) if "check_yml_vs_projection.py" in ln)
    assert check > docs, "the projection check must come AFTER dbt docs generate writes catalog.json"
    assert "--catalog dbt_project/target/catalog.json" in script[check], (
        f"the check must read the catalogue the docs line wrote; found: {script[check]}"
    )
    assert script[check].startswith('cd "$CI_PROJECT_DIR"'), (
        "the script ends inside dbt_project/, so the line must return to the repo root first"
    )


def test_the_pins_are_not_vacuous():
    """An empty parse would make every assertion above pass for the wrong reason."""
    project = _dbt_project()
    ci = _ci()
    assert project.get("name") == "football_data_pipeline"
    assert "models" in project and "seeds" in project
    jobs = [k for k, v in ci.items() if isinstance(v, dict) and "script" in v]
    assert len(jobs) >= 10, f"only parsed {len(jobs)} CI jobs — the parse is broken"
    assert len(list(MODELS_DIR.rglob("*.sql"))) >= 50, "model tree looks empty — the walk is broken"
