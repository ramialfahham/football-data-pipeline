"""Pin the invariants that make `persist_docs` safe, because breaking them produces no red.

WHY THIS EXISTS
---------------
Turning on `persist_docs` is the change in this repo's history that most directly couples a prose
field to a production build: every `description:` is pushed to BigQuery as table and column
metadata, and BigQuery HARD-REJECTS a column description over 1,024 characters or a relation
description over 16,384. A rejection fails the model, and in `data:build:main` that fails the prod
build. Bracketed live against a dev table: 1,024 accepted, 1,025 rejected with an
HTTP 400, 16,384 accepted, 16,385 rejected. It is a rejection, not a truncation.

Every invariant below could previously be reverted with the entire suite still green:

  * delete `+persist_docs` and descriptions silently stop reaching BigQuery — the whole point of
    the description programme, whose root-cause finding was that the field had NO READER;
  * add a `+schema` to the `seeds:` block and every seed silently moves dataset, because seeds
    declare no custom schema and ride `target.schema` through `macros/generate_schema_name.sql`
    (`dbt_analytics` on prod). Every `ref()` to a seed then resolves somewhere else;
  * delete the `dbt docs generate` step, or move it to `data:nightly` / `data:build:mr`, both of
    which are explicitly rejected — the first re-publishes identical pages for
    recurring cost, the second produces a catalog covering only what one branch changed;
  * restore `allow_failure: true` and the docs step becomes the "green but did nothing" shape that
    GitLab #904 names as this repo's dominant failure. The retired GitHub workflow did exactly
    that (`.github/workflows/pages-match-preview.yml`, `continue-on-error: true`).

That is the same "breaking it produces no red anywhere" shape as `test_materialisation_policy.py`
and `test_ci_data_job_invariants.py`, on the same two files, and this module is their sibling. The
programme's own founding measurement is why it is a test rather than a paragraph: of 50 past
corrections 33 were prose-only and 22 recurred, while every rule that got a machine check stopped
recurring.

HOW IT IS SHAPED, AND WHY
-------------------------
Values come from PARSED YAML, never from raw file text — the same rule
`test_ci_data_job_invariants.py` sets out, and for the same reason: the comment blocks in both
files NAME the things being guarded against ("allow_failure", "+schema"), so a text grep would flag
the documentation of the defect as the defect.

The properties are asserted, not the spelling. `+persist_docs` is set once at project level today,
but the invariant is "every model gets it and nothing below turns it off" — asserting the current
nesting instead is how a correct refactor starts failing a test for no reason.
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
    """Descriptions must reach BigQuery for models. This is the reader the programme was about."""
    project = _dbt_project()
    block = project["models"]["football_data_pipeline"]
    assert block.get("+persist_docs") == WANT, (
        "models.football_data_pipeline must set +persist_docs {relation: true, columns: true}; "
        f"found {block.get('+persist_docs')!r}. Without it every description stops reaching "
        "BigQuery and the field goes back to having no reader."
    )


def test_persist_docs_is_enabled_for_seeds():
    """Seeds were the audit's worst offender and had no config block at all before MR6."""
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
    """THE silent-relocation hazard, and the one way this MR could break every ref() to a seed.

    Seeds declare no custom schema, so they ride `target.schema` — the profile's `dataset:`, which
    is `dbt_analytics` on prod — through `macros/generate_schema_name.sql`. A `+schema` here moves
    all nine somewhere else and nothing about it looks wrong in review.
    """
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
    """The layer/project decides. A per-model override is how one model drifts off the policy.

    Same rule and same reason as `test_base_models_never_override_materialisation_per_model`.
    """
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
    """The cadence: after each merge to main, and nowhere else.

    `data:nightly` was rejected because a description's content comes from the repo, not the data,
    so a nightly run re-publishes identical pages for recurring cost. `data:build:mr` was rejected
    because it builds `state:modified+` into that merge request's own `ci_mr<IID>_*` datasets, so
    its catalog would cover only what one branch changed — a partial column list presented as the
    column list.
    ⚠ That rationale used to say "the shared ci_* datasets". There is no shared CI workspace any
    more (#92) — each merge request writes its own — but the reason this job is still
    the wrong place to generate docs is UNCHANGED and if anything stronger: a per-merge-request
    dataset holds even less of the warehouse than the shared one did.
    """
    jobs = _jobs_running("dbt docs generate")
    assert jobs == ["data:build:main"], (
        f"`dbt docs generate` runs in {jobs}; it must run in data:build:main and nowhere else. "
        "data:nightly and data:build:mr were both explicitly rejected."
    )


def test_the_docs_command_is_static_and_targets_prod():
    """`--static` is what produces the single self-contained page; prod is the only complete catalog."""
    job = _ci()["data:build:main"]
    line = next(ln for ln in job["script"] if "dbt docs generate" in str(ln))
    assert "--static" in line, f"docs generate must pass --static; found: {line}"
    assert "--target prod" in line, f"docs generate must pass --target prod; found: {line}"


def test_the_docs_step_may_not_fail_silently():
    """#904, in one assertion.

    The retired GitHub step carried `continue-on-error: true`. This one runs after prod is already
    built AND tested, so a failure costs signal, never data — and a docs build that silently does
    nothing is exactly the failure this repo keeps shipping.
    """
    job = _ci()["data:build:main"]
    assert not job.get("allow_failure", False), (
        "data:build:main must not set allow_failure — a silently skipped docs build is the "
        "'green but did nothing' shape of #904."
    )


def test_the_catalog_is_published():
    """`catalog.json` is the load-bearing artifact, not `static_index.html`.

    It is the only place a column that exists in BigQuery but is declared in no .yml can be seen,
    which is the entire basis of GitLab #82. Publishing the pretty page and dropping the catalog
    would look fine and remove the reason the step exists.
    """
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
    """`check_yml_vs_projection.py` reads the catalog.json the docs line just wrote.

    It belongs here and nowhere else (#109 step 3, MR D): this is the one job where the catalogue
    is the whole prod warehouse, and it runs after prod is built and tested, so a red costs signal,
    never data. Anywhere earlier in the script the file does not exist yet; in any other job it
    would be partial, and the script's own abort would make the job red for the wrong reason.
    """
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
    """Anti-vacuous floor, per `check_copy_gate.py`'s MIN_KEYS precedent.

    If the parse silently returns something empty, every assertion above passes for the wrong
    reason. This fails loudly instead.
    """
    project = _dbt_project()
    ci = _ci()
    assert project.get("name") == "football_data_pipeline"
    assert "models" in project and "seeds" in project
    jobs = [k for k, v in ci.items() if isinstance(v, dict) and "script" in v]
    assert len(jobs) >= 10, f"only parsed {len(jobs)} CI jobs — the parse is broken"
    assert len(list(MODELS_DIR.rglob("*.sql"))) >= 50, "model tree looks empty — the walk is broken"
