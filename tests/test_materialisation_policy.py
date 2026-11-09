"""Pin the per-layer materialisation policy, and pin every document to it.

Each policy site must quote the config line verbatim (`2_base: +materialized: <value>`), so a reword cannot defeat the check.
"""

from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DBT_PROJECT = ROOT / "dbt_project" / "dbt_project.yml"
BASE_MODELS = ROOT / "dbt_project" / "models" / "2_base"
STAGING_MODELS = ROOT / "dbt_project" / "models" / "1_staging"


def _load_layer_contract():
    """Import `scripts/check_layer_contract.py` as a module, shared by the base and staging guard tests."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "check_layer_contract", ROOT / "scripts" / "check_layer_contract.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

EXPECTED = {
    "1_staging": "table",    # a view stores nothing, so every test re-executes the raw JSON parse
    "2_base": "table",       # stored once a night so tests stop re-scanning the raw JSON
    "3_core": "table",
    "4_intermediate": "table",
    "5_marts": "table",
}

# Every file that states a layer's materialisation, per layer; a file quoting the token but missing
# here fails `test_the_policy_site_list_covers_every_file_that_quotes_the_token`.
# dbt_project.yml is absent because YAML splits the key and value across two lines, so EXPECTED pins it.
# The rule is stated once in layering.md; the check script and the layer hook quote the lines they enforce.
POLICY_SITES = {
    "2_base": (
        "dbt_project/docs/layering.md",
        "scripts/check_layer_contract.py",
        ".claude/hooks/dbt_layer_gate.py",
    ),
    "1_staging": (
        "dbt_project/docs/layering.md",
        "scripts/check_layer_contract.py",
    ),
    "3_core": ("dbt_project/docs/layering.md",),
    "4_intermediate": ("dbt_project/docs/layering.md",),
    "5_marts": ("dbt_project/docs/layering.md",),
}

# The prose form of the claim, "<layer> ... is a <materialisation>", for the repo-wide sweep.
# Past-tense wording ("they were views") is deliberately not matched.
PROSE_SUBJECT = {
    "2_base": r"base",
    "1_staging": r"staging",
}


def _configured_materialisations() -> dict[str, str]:
    """Read `+materialized:` per layer out of dbt_project.yml, by regex so a malformed file fails loudly."""
    text = DBT_PROJECT.read_text(encoding="utf-8")
    found: dict[str, str] = {}
    for layer in EXPECTED:
        block = re.search(
            rf"^\s*{re.escape(layer)}:\s*$(.*?)(?=^\s*\d_[a-z_]+:\s*$|^\S)",
            text,
            re.MULTILINE | re.DOTALL,
        )
        assert block, f"{layer} not found in dbt_project.yml"
        mat = re.search(r"\+materialized:\s*([a-z_]+)", block.group(1))
        assert mat, f"{layer} has no +materialized in dbt_project.yml"
        found[layer] = mat.group(1)
    return found


def test_layer_materialisation_matches_the_policy():
    """A changed layer materialisation needs EXPECTED and every file in POLICY_SITES updated with it."""
    assert _configured_materialisations() == EXPECTED


def test_base_models_never_override_materialisation_per_model():
    """The offline twin of the `scripts/check_layer_contract.py` rule that the layer decides."""
    offenders = [
        p.relative_to(ROOT).as_posix()
        for p in sorted(BASE_MODELS.rglob("*.sql"))
        if re.search(r"""materialized\s*=\s*['"]""", p.read_text(encoding="utf-8"), re.IGNORECASE)
    ]
    assert offenders == [], f"base models overriding materialisation: {offenders}"


def test_every_policy_site_quotes_the_configured_layer_materialisation():
    """Each site must quote the live config line verbatim, and none may still quote the superseded one."""
    configured = _configured_materialisations()
    missing, stale = [], []

    for layer, sites in POLICY_SITES.items():
        actual = configured[layer]
        current = f"{layer}: +materialized: {actual}"
        superseded = [f"{layer}: +materialized: {v}" for v in ("view", "table") if v != actual]
        for rel in sites:
            text = (ROOT / rel).read_text(encoding="utf-8")
            if current not in text:
                missing.append(f"{rel} -> missing {current!r}")
            stale += [f"{rel} -> {tok!r}" for tok in superseded if tok in text]

    assert not missing, (
        f"these state a layer materialisation but do not quote the live config line: {missing}. "
        "Quote it verbatim, on ONE line, so drift is detectable — a token split across a "
        "markdown line wrap reads fine and matches nothing."
    )
    assert not stale, f"these still quote a superseded materialisation: {stale}"


def test_check_layer_contract_rejects_any_per_model_materialisation(tmp_path, monkeypatch):
    mod = _load_layer_contract()

    fake = tmp_path / "base_apif__fake.sql"
    fake.write_text(
        "{{ config(materialized='view') }}\n"
        "select * from {{ ref('stg_apif__teams') }}\n",
        encoding="utf-8",
    )
    # The script reports paths with `relative_to(REPO_ROOT)`, so REPO_ROOT must move with BASE_DIR.
    monkeypatch.setattr(mod, "BASE_DIR", tmp_path)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    errors: list[str] = []
    mod.check_base_layer(errors)

    assert any("materializ" in e.lower() for e in errors), (
        "check_base_layer accepted a per-model materialized='view' override. That was the OLD rule; "
        f"the layer default is now {EXPECTED['2_base']!r} and no per-model override is allowed. "
        f"errors={errors}"
    )


def test_staging_models_never_override_materialisation_per_model():
    """One staging model opting back into `view` would reinstate the raw JSON rescan for its own tests."""
    offenders = [
        p.relative_to(ROOT).as_posix()
        for p in sorted(STAGING_MODELS.rglob("*.sql"))
        if re.search(r"""materialized\s*=\s*['"]""", p.read_text(encoding="utf-8"), re.IGNORECASE)
    ]
    assert offenders == [], f"staging models overriding materialisation: {offenders}"


def test_check_layer_contract_rejects_a_staging_per_model_override(tmp_path, monkeypatch):
    """Points the script's STAGING_DIR at a staging model carrying an override and requires an error."""
    mod = _load_layer_contract()
    (tmp_path / "stg_apif__probe.sql").write_text(
        "{{ config(materialized='view') }}\nselect 1 as x\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "STAGING_DIR", tmp_path)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    errors: list[str] = []
    mod.check_staging_materialisation(errors)

    assert any("materializ" in e.lower() for e in errors), (
        "check_staging_materialisation accepted a per-model materialized='view' override. The "
        f"layer default is {EXPECTED['1_staging']!r} and no per-model override is allowed. "
        f"errors={errors}"
    )


UPPER_LAYERS = ("3_core", "4_intermediate", "5_marts")


def test_upper_layer_models_never_override_materialisation_per_model():
    """Core, intermediate and marts follow the layer too; `incremental` on a core fact is the one exception."""
    offenders = []
    for layer in UPPER_LAYERS:
        for p in sorted((ROOT / "dbt_project" / "models" / layer).rglob("*.sql")):
            kinds = set(
                re.findall(
                    r"""materialized\s*=\s*['"]([a-z_]+)['"]""",
                    p.read_text(encoding="utf-8"),
                    re.IGNORECASE,
                )
            )
            allowed = {"incremental"} if layer == "3_core" and p.name.startswith("fct_") else set()
            if kinds - allowed:
                offenders.append(f"{p.relative_to(ROOT).as_posix()} -> {sorted(kinds)}")
    assert offenders == [], f"models overriding their layer's materialisation: {offenders}"


def test_check_layer_contract_rejects_upper_layer_overrides_and_allows_core_incremental(
    tmp_path, monkeypatch
):
    mod = _load_layer_contract()
    dirs = {name: tmp_path / name for name in ("core", "intermediate", "marts")}
    for d in dirs.values():
        d.mkdir()
    (dirs["core"] / "fct_probe_delta.sql").write_text(
        "{{ config(materialized='incremental', unique_key='k') }}\nselect 1 as k\n",
        encoding="utf-8",
    )
    (dirs["core"] / "dim_probe.sql").write_text(
        "{{ config(materialized='view') }}\nselect 1 as x\n", encoding="utf-8"
    )
    (dirs["core"] / "dim_probe_delta.sql").write_text(
        "{{ config(materialized='incremental', unique_key='k') }}\nselect 1 as k\n",
        encoding="utf-8",
    )
    (dirs["intermediate"] / "int_probe.sql").write_text(
        "{{ config(materialized='table') }}\nselect 1 as x\n", encoding="utf-8"
    )
    (dirs["marts"] / "mart_probe.sql").write_text(
        "{{ config(materialized='view') }}\nselect 1 as x\n", encoding="utf-8"
    )
    monkeypatch.setattr(mod, "CORE_DIR", dirs["core"])
    monkeypatch.setattr(mod, "INTERMEDIATE_DIR", dirs["intermediate"])
    monkeypatch.setattr(mod, "MARTS_DIR", dirs["marts"])
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    errors: list[str] = []
    mod.check_upper_layer_materialisation(errors)

    flagged = {e.split(":", 1)[0] for e in errors}
    assert flagged == {
        "core/dim_probe.sql",
        "core/dim_probe_delta.sql",
        "intermediate/int_probe.sql",
        "marts/mart_probe.sql",
    }, f"expected every override rejected and only the core incremental FACT allowed: {errors}"


def _is_bookkeeping(rel: str) -> bool:
    """Files that legitimately hold both the old and new wording, so neither walk may judge them."""
    return (
        rel.startswith(".claude/task/")
        # The product stream's handover is not editable from the pipeline worktree.
        or rel == ".claude/active_work.md"
        # The generated tracker backup quotes old issue bodies verbatim and has one writer.
        or rel.startswith("docs/tracker/")
        or rel == "tests/test_materialisation_policy.py"
    )


def _tracked_files() -> list[pathlib.Path]:
    """Files git tracks, so ignored trees (dbt_packages, node_modules, target, .venv) need no skip-list."""
    import subprocess

    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True, check=True
    ).stdout.split("\n")
    return [ROOT / rel for rel in out if rel.strip()]


def test_the_policy_site_list_covers_every_file_that_quotes_the_token():
    """Any tracked file quoting a layer's `+materialized:` token must be in POLICY_SITES."""
    unpinned = []
    for layer, sites in POLICY_SITES.items():
        token = f"{layer}: +materialized:"
        found = set()
        for path in _tracked_files():
            try:
                if token in path.read_text(encoding="utf-8"):
                    found.add(path.relative_to(ROOT).as_posix())
            except (UnicodeDecodeError, OSError):
                continue
        found = {r for r in found if not _is_bookkeeping(r)}
        unpinned += [f"{layer}: {r}" for r in sorted(found - set(sites))]
    assert not unpinned, f"these quote a policy token but are not in POLICY_SITES: {unpinned}"


def test_no_tracked_file_anywhere_states_the_superseded_materialisation():
    """A file can quote the token and still contradict it in a sentence that quotes nothing, so every tracked file is swept."""
    configured = _configured_materialisations()
    offenders = []

    for layer, subject in PROSE_SUBJECT.items():
        actual = configured[layer]
        superseded = {"table": "view", "view": "table"}[actual]
        claim = re.compile(
            rf"{subject}\s+(models?\s+)?(are\s+|is\s+|as\s+|materiali[sz]es?\s+as\s+)?"
            rf"(a\s+)?{superseded}s?\b"
            rf"|{subject}\s+{superseded}s\s*\+",
            re.IGNORECASE,
        )
        for path in _tracked_files():
            rel = path.relative_to(ROOT).as_posix()
            if _is_bookkeeping(rel):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            hit = claim.search(text)
            if hit:
                offenders.append(f"{rel} -> {hit.group(0)!r} (says {layer} is a {superseded})")

    assert not offenders, (
        f"these contradict the configured materialisation in dbt_project.yml: {offenders}"
    )
