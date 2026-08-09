"""The Cloud Run entrypoint must stay a faithful port of `data:nightly` (GitLab #39 Stage 1).

WHY THIS EXISTS
---------------
Stage 1 moves the nightly out of GitLab CI onto Cloud Run, and deliberately leaves the CI job
in place as a fallback until the new path has proven itself. That means TWO copies of the
nightly exist for a while, and they can drift.

Drift here is silent and expensive. If a step is added to one and not the other — a new
contract check, a seed, a different dbt target — the nightly keeps exiting 0 while quietly
doing less than it claims. That is the same failure shape as the two outages this whole change
exists to prevent: nothing turns red, the data is just wrong or stale.

Both this file and the CI job are deleted together in the follow-up governance MR that removes
`data:nightly` from `.gitlab-ci.yml` (a protected path, so it needs its own task).

HOW IT IS SHAPED
----------------
It compares the ORDERED list of meaningful commands, extracted from each source, rather than
matching text. A text match would fail on indentation, `$CI_PROJECT_DIR` vs `/tmp`, and the
`[nightly]` log prefixes — none of which are drift. What it asserts is that both run the same
things in the same order.

The one thing it must NOT do is compare the two files as strings; they are legitimately
different in wording, and a test that fails on wording gets deleted rather than fixed.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

import yaml

REPO = Path(__file__).resolve().parents[1]
ENTRYPOINT = REPO / "deploy" / "nightly" / "entrypoint.sh"
CI_CONFIG = REPO / ".gitlab-ci.yml"

# The steps that define what the nightly DOES, in the order it must do them. Each entry is a
# regex matched against a command line from either source. Anything not matching one of these
# (echo, cd, export, the gate plumbing) is not a step and is ignored — those legitimately
# differ between a CI runner and a container.
STEPS = [
    ("ingest", r"python -m ingestion\.api_football\.main"),
    ("layer contract check", r"python scripts/check_layer_contract\.py"),
    ("registry sync check", r"python scripts/check_registry_var_sync\.py"),
    ("dbt deps", r"^dbt deps"),
    ("dbt seed prod", r"^dbt seed --target prod"),
    ("dbt build prod", r"^dbt build --target prod"),
]


def _commands(text: str) -> list[str]:
    """Flatten a shell script (or a YAML script block) to stripped, non-comment lines."""
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out


def _ci_nightly_script() -> list[str]:
    """The `data:nightly` script block, read from the real .gitlab-ci.yml.

    Parsed as YAML rather than sliced by line number, so the test does not break the first time
    somebody adds a line above the job. The `!reference`/anchor tags in this file are not
    resolvable by safe_load, so unknown tags are ignored — the anchors carry auth and profile
    setup, not pipeline steps.
    """
    class _Ignore(yaml.SafeLoader):
        pass

    _Ignore.add_multi_constructor("!", lambda loader, suffix, node: None)
    doc = yaml.load(CI_CONFIG.read_text(encoding="utf-8"), Loader=_Ignore)
    job = doc.get("data:nightly")
    assert job, "data:nightly is gone from .gitlab-ci.yml — delete this test with it (#39)."
    lines: list[str] = []
    for entry in job.get("script") or []:
        if isinstance(entry, str):
            lines.extend(_commands(entry))
    return lines


def _ordered_steps(lines: list[str]) -> list[str]:
    found = []
    for line in lines:
        for name, pattern in STEPS:
            if re.search(pattern, line):
                found.append(name)
                break
    return found


@pytest.mark.skipif(not CI_CONFIG.exists(), reason="no .gitlab-ci.yml")
def test_entrypoint_runs_the_same_steps_in_the_same_order_as_ci():
    entry_steps = _ordered_steps(_commands(ENTRYPOINT.read_text(encoding="utf-8")))
    ci_steps = _ordered_steps(_ci_nightly_script())

    assert entry_steps == ci_steps, (
        "the Cloud Run entrypoint and .gitlab-ci.yml data:nightly have DRIFTED.\n"
        f"  entrypoint: {entry_steps}\n"
        f"  gitlab ci : {ci_steps}\n"
        "While both exist they must run the same steps in the same order. A step present in "
        "one and not the other means the nightly silently does less than it claims, and exits "
        "0 while doing it."
    )
    assert entry_steps == [name for name, _ in STEPS], (
        f"the nightly's step list changed: {entry_steps}. If that is intended, update STEPS "
        "in this file — but check BOTH copies were changed."
    )


def _run_entrypoint(tmp_path, new_data: str) -> list[str]:
    """RUN the entrypoint with `python` and `dbt` stubbed out, and return what it invoked.

    Executing it is the point. An earlier version of this test asserted the ORDER of three
    regex matches in the file — gate before `exit 0` before `dbt build` — and a reviewer showed
    it was decoration: changing the condition to `if [ "$NEW_DATA" != "true" ] || true; then`
    makes the gate fire on EVERY run, silently killing the nightly build forever, while all
    three markers keep their positions and the test stays green. Textual position cannot see
    boolean structure. This runs the real script and observes what it actually does.

    Nothing real executes: the stubs log their arguments and exit 0, and the `python` stub is
    what writes the `new_data` signal, exactly as `write_ci_output()` does in production.
    """
    bindir = tmp_path / "bin"
    bindir.mkdir()
    trace = tmp_path / "trace.log"
    step_output = tmp_path / "step-output"

    (bindir / "python").write_text(
        '#!/usr/bin/env bash\n'
        'echo "python $*" >> "$TRACE"\n'
        'case "$*" in\n'
        '  *ingestion.api_football.main*) echo "new_data=$FAKE_NEW_DATA" >> "$CI_STEP_OUTPUT" ;;\n'
        'esac\n'
        'exit 0\n',
        encoding="utf-8", newline="\n",
    )
    (bindir / "dbt").write_text(
        '#!/usr/bin/env bash\necho "dbt $*" >> "$TRACE"\nexit 0\n',
        encoding="utf-8", newline="\n",
    )
    for stub in ("python", "dbt"):
        (bindir / stub).chmod(0o755)

    env = {
        **os.environ,
        "PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}",
        "TRACE": str(trace),
        "CI_STEP_OUTPUT": str(step_output),
        "FAKE_NEW_DATA": new_data,
    }
    proc = subprocess.run(
        [shutil.which("bash"), str(ENTRYPOINT)],
        cwd=REPO, env=env, capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, (
        f"entrypoint exited {proc.returncode} with new_data={new_data}.\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    return trace.read_text(encoding="utf-8").splitlines() if trace.exists() else []


@pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash to execute the entrypoint")
def test_a_quiet_night_exits_before_dbt(tmp_path):
    """`new_data=false` must cost nothing. This is the `$0 night` contract — the difference
    between a cheap no-op and a full prod warehouse build every 24h."""
    invoked = _run_entrypoint(tmp_path, "false")

    assert any("ingestion.api_football.main" in line for line in invoked), (
        f"ingestion did not run at all; the test is not exercising the entrypoint. {invoked}"
    )
    assert not [line for line in invoked if line.startswith("dbt ")], (
        f"a quiet night reached dbt. Every night would build the warehouse. Invoked: {invoked}"
    )
    assert not [line for line in invoked if "check_layer_contract" in line], (
        f"a quiet night ran the contract checks it claims to skip. Invoked: {invoked}"
    )


@pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash to execute the entrypoint")
def test_new_data_runs_the_full_prod_build(tmp_path):
    """The mirror case. Without it, a gate that ALWAYS exits early would pass the test above —
    which is exactly the regression that made the previous version of this test decoration."""
    invoked = _run_entrypoint(tmp_path, "true")

    joined = "\n".join(invoked)
    for expected in (
        "ingestion.api_football.main",
        "check_layer_contract.py",
        "check_registry_var_sync.py",
        "dbt deps",
        "dbt seed --target prod",
        "dbt build --target prod",
    ):
        assert expected in joined, (
            f"new_data=true did not reach `{expected}`. The nightly would silently do less "
            f"than it claims. Invoked:\n{joined}"
        )


def test_the_entrypoint_never_targets_a_non_prod_dataset():
    """The container ships only the prod profile, so a stray `--target ci` would fail at 04:00
    rather than at build time. Cheaper to catch here."""
    text = ENTRYPOINT.read_text(encoding="utf-8")
    stray = re.findall(r"--target\s+(\w+)", text)
    assert stray and set(stray) == {"prod"}, (
        f"entrypoint targets {sorted(set(stray))}; only 'prod' is shipped in "
        "deploy/nightly/profiles.yml, so anything else fails in production."
    )


def test_the_shipped_profile_has_only_the_prod_target():
    """If a `ci` or `dev` target ever appears in the image's profile, a mistyped --target stops
    failing loudly and starts writing the wrong dataset instead."""
    profile = yaml.safe_load(
        (REPO / "deploy" / "nightly" / "profiles.yml").read_text(encoding="utf-8")
    )
    outputs = profile["football_data_pipeline"]["outputs"]
    assert set(outputs) == {"prod"}, (
        f"the shipped profile carries targets {sorted(outputs)}. Ship prod ONLY — a second "
        "target is a path to writing ci_* or dev_* from the production nightly."
    )
    assert profile["football_data_pipeline"]["target"] == "prod"
    assert outputs["prod"]["dataset"] == "dbt_analytics"
    assert outputs["prod"]["location"] == "EU"
