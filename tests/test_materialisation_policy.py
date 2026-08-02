"""Pin the per-layer materialisation policy, and pin every document to it (#547).

WHY THIS EXISTS
---------------
On 2026-05-25 a cost fix landed and Thread 1 of docs/product_direction_threads.md was closed with
"architecture signed off". On 2026-05-27, two days later, an unrelated refactor rewrote the same
models and the optimisation went with them. Nothing failed, because all ~865 dbt tests ask whether
a NUMBER is correct and none asks whether something became expensive. The regression was invisible
until the bill arrived, and it stayed invisible for two months.

WHAT THIS PINS, AND WHY IT IS SHAPED THIS WAY
---------------------------------------------
The first version of this file hunted the phrase "base models materialise as <value>". That was a
guard that looked strong and was nearly inert: edits made in the same commit changed two of the
three files to different wording, so the regex could no longer match them. A guard that names its
targets in prose is not a guard.

So the contract here is mechanical instead. Every file that states the base materialisation must
quote the config line VERBATIM — `2_base: +materialized: <value>`. That token is the interface:

  * adding a policy site is one line in POLICY_SITES, not a fresh grep;
  * changing the policy fails every site at once until each is updated;
  * a site cannot drift by being reworded, because the token is checked, not the sentence.

The cost figures behind the current policy are in dbt_project/docs/layering.md, reproducible with
`python scripts/report_bq_cost.py`.
"""

from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DBT_PROJECT = ROOT / "dbt_project" / "dbt_project.yml"
BASE_MODELS = ROOT / "dbt_project" / "models" / "2_base"

# The policy. Changing a value here is the deliberate act; changing dbt_project.yml alone is not.
EXPECTED = {
    "1_staging": "view",     # light cleanup; cheap to re-run, and its consumers are stored
    "2_base": "table",       # #547: stored once a night so tests stop re-scanning the raw JSON
    "3_core": "table",
    "4_intermediate": "table",
    "5_marts": "table",
}

# Every file that tells a human or an agent what the base materialisation is. Seven sites exist for
# one rule; the first attempt at this task found four, because it grepped docs/ and the dbt project
# and never looked in the hooks or the role briefs. If you state the rule somewhere new, add it here
# — and the last test in this file fails if you forget.
# NOTE dbt_project.yml is deliberately absent: it IS the config, and YAML splits the key and the
# value across two lines so it cannot contain the one-line token. It is pinned by EXPECTED instead.
POLICY_SITES = (
    "dbt_project/docs/layering.md",
    "CLAUDE.md",
    "scripts/check_layer_contract.py",
    ".claude/hooks/dbt_layer_gate.py",
    "docs/roles/analytics_engineer.md",
)


def _configured_materialisations() -> dict[str, str]:
    """Read `+materialized:` per layer out of dbt_project.yml.

    Parsed by regex rather than yaml so the test does not depend on a yaml library being present in
    whatever environment runs it, and so a malformed file fails loudly here.
    """
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
    """dbt_project.yml must match EXPECTED above.

    If this fails you changed a layer's materialisation. That is allowed, and it is a cost decision:
    update EXPECTED, update every file in POLICY_SITES, and record the measured reason. Do not just
    make the test green.
    """
    assert _configured_materialisations() == EXPECTED


def test_base_models_never_override_materialisation_per_model():
    """The layer decides, so no base model may set its own.

    A per-model override is how one model drifts off the policy and stops being re-costed with the
    rest of its layer. `scripts/check_layer_contract.py` enforces the same rule in CI; this is the
    offline twin so it also fails in the fast suite.
    """
    offenders = [
        p.relative_to(ROOT).as_posix()
        for p in sorted(BASE_MODELS.rglob("*.sql"))
        if re.search(r"""materialized\s*=\s*['"]""", p.read_text(encoding="utf-8"), re.IGNORECASE)
    ]
    assert offenders == [], f"base models overriding materialisation: {offenders}"


def test_every_policy_site_quotes_the_configured_base_materialisation():
    """The May 2026 regression, in one assertion.

    The config changed and the prose did not, so the repo described a rule it no longer followed and
    every reader after that was misled, including an agent reading it two months later. Each site
    must quote the live config line verbatim, and none may still quote the superseded one.
    """
    actual = _configured_materialisations()["2_base"]
    current = f"2_base: +materialized: {actual}"
    superseded = [f"2_base: +materialized: {v}" for v in ("view", "table") if v != actual]

    missing, stale = [], []
    for rel in POLICY_SITES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        if current not in text:
            missing.append(rel)
        stale += [f"{rel} -> {tok!r}" for tok in superseded if tok in text]

    assert not missing, (
        f"these state the base materialisation but do not quote {current!r}: {missing}. "
        "Quote the config line verbatim so drift is detectable."
    )
    assert not stale, f"these still quote a superseded materialisation: {stale}"


def test_check_layer_contract_rejects_any_per_model_materialisation(tmp_path, monkeypatch):
    """Pin the CI check's rule, which nothing exercised before.

    It used to allow `materialized='view'` and reject everything else. Once the layer default became
    `table` that was actively wrong: it would have rejected a model for matching the default and
    accepted one pinned to the superseded value. The rule is now "no per-model materialisation at
    all", and reverting it must fail here — otherwise the revert is free, since no base model sets
    one today and CI would look identical either way.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "check_layer_contract", ROOT / "scripts" / "check_layer_contract.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    fake = tmp_path / "base_apif__fake.sql"
    fake.write_text(
        "{{ config(materialized='view') }}\n"
        "select * from {{ ref('stg_apif__teams') }}\n",
        encoding="utf-8",
    )
    # The script reports paths with `relative_to(REPO_ROOT)`, so REPO_ROOT has to move with BASE_DIR
    # or it raises on a tmp path outside the repo.
    monkeypatch.setattr(mod, "BASE_DIR", tmp_path)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    errors: list[str] = []
    mod.check_base_layer(errors)

    assert any("materializ" in e.lower() for e in errors), (
        "check_base_layer accepted a per-model materialized='view' override. That was the OLD rule; "
        f"the layer default is now {EXPECTED['2_base']!r} and no per-model override is allowed. "
        f"errors={errors}"
    )


def _is_bookkeeping(rel: str) -> bool:
    """Files that legitimately hold BOTH the old and new wording, so neither walk may judge them.

    `.claude/task/**` is the review's own paperwork: `review_input.patch` is a generated diff and
    therefore contains the before-text by construction, and `escalations.log` is the durable record
    of what changed and must stay writable. `product_direction_threads.md` records Thread 1 as it
    was closed in May, which is history, not a live claim. This file constructs the tokens it hunts.
    """
    return (
        rel.startswith(".claude/task/")
        or rel == "docs/product_direction_threads.md"
        or rel == "tests/test_materialisation_policy.py"
    )


def _tracked_files() -> list[pathlib.Path]:
    """Files git tracks. Uses git rather than rglob so ignored trees (dbt_packages, node_modules,
    target, .venv) are excluded by definition instead of by a skip-list I have to keep current —
    the same class of hand-maintained list that caused this whole task."""
    import subprocess

    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True, check=True
    ).stdout.split("\n")
    return [ROOT / rel for rel in out if rel.strip()]


def test_the_policy_site_list_covers_every_file_that_quotes_the_token():
    """POLICY_SITES must not silently fall behind the repo.

    Closes the failure that produced it: a list written from a partial grep. Any tracked file
    quoting `2_base: +materialized:` must be pinned, so a new site cannot appear unguarded.
    """
    token = "2_base: +materialized:"
    found = set()
    for path in _tracked_files():
        try:
            if token in path.read_text(encoding="utf-8"):
                found.add(path.relative_to(ROOT).as_posix())
        except (UnicodeDecodeError, OSError):
            continue
    found = {r for r in found if not _is_bookkeeping(r)}
    unpinned = sorted(found - set(POLICY_SITES))
    assert not unpinned, f"these quote the policy but are not in POLICY_SITES: {unpinned}"


def test_no_tracked_file_anywhere_states_the_superseded_materialisation():
    """The hole the token check cannot see, closed repo-wide.

    A file can quote the current token AND still contradict it in a sentence that quotes nothing —
    which is exactly what `layering.md` did after the first attempt, and what
    `profiles.example.yml` did while not being in POLICY_SITES at all. So this does not consult the
    site list: it asserts across every tracked file that nothing says base is a view while the
    config says table. Written from a real search (`git grep -inE ...`), not from memory, because
    guessing the site list is the mistake this task made three times.

    Past-tense history ("they were views") is deliberately NOT matched — the record of the change
    has to stay writable, and `escalations.log` is where it lives.
    """
    actual = _configured_materialisations()["2_base"]
    superseded = {"table": "view", "view": "table"}[actual]
    claim = re.compile(
        rf"base\s+(models?\s+)?(are\s+|as\s+|materiali[sz]es?\s+as\s+)?{superseded}s?\b"
        rf"|base\s+{superseded}s\s*\+",
        re.IGNORECASE,
    )
    offenders = []
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
            offenders.append(f"{rel} -> {hit.group(0)!r}")
    assert not offenders, (
        f"these say base is a {superseded} while dbt_project.yml says {actual}: {offenders}"
    )
