"""The Cloud Run entrypoint must run the same ordered steps as the `data:nightly` CI job.

It compares ordered command lists, never the files as strings, because their wording differs.
"""

from __future__ import annotations

import json
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

# The steps that define the nightly, in order, each a regex over a command line from either
# source; commands matching none (echo, cd, export, gate plumbing) differ legitimately.
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
    """The `data:nightly` script lines, parsed as YAML with unknown tags ignored."""
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
    """Run the entrypoint with stubbed `python` and `dbt` and return what they were invoked with."""
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
    """`new_data=false` must exit before dbt, so a quiet night costs nothing."""
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
    """The mirror case: without it a gate that always exits early would pass the test above."""
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
    """The container ships only the prod profile, so any other target would fail at 04:00."""
    text = ENTRYPOINT.read_text(encoding="utf-8")
    stray = re.findall(r"--target\s+(\w+)", text)
    assert stray and set(stray) == {"prod"}, (
        f"entrypoint targets {sorted(set(stray))}; only 'prod' is shipped in "
        "deploy/nightly/profiles.yml, so anything else fails in production."
    )


def test_the_alert_policies_carry_only_fields_the_api_accepts():
    """Comment keys must start with `_` so the runbook strips them; any other unknown field 400s."""
    raw = json.loads((REPO / "deploy" / "nightly" / "alert-policy.json").read_text(encoding="utf-8"))

    def strip(o):
        if isinstance(o, dict):
            return {k: strip(v) for k, v in o.items() if not k.startswith("_")}
        if isinstance(o, list):
            return [strip(v) for v in o]
        return o

    policies = strip(raw)["policies"]
    assert policies, "alert-policy.json declares no policies"

    ALLOWED_POLICY_KEYS = {
        "displayName", "documentation", "combiner", "conditions",
        "alertStrategy", "notificationChannels", "enabled", "severity", "userLabels",
    }
    ALLOWED_CONDITION_KEYS = {
        "displayName", "conditionThreshold", "conditionAbsent",
        "conditionMonitoringQueryLanguage", "conditionMatchedLog", "name",
    }

    for p in policies:
        unknown = sorted(set(p) - ALLOWED_POLICY_KEYS)
        assert not unknown, (
            f"{p.get('displayName')!r} carries policy fields the Monitoring API does not "
            f"accept: {unknown}. Comments must start with `_` so the runbook's stripper removes "
            "them; anything else 400s the create call."
        )
        for c in p["conditions"]:
            unknown = sorted(set(c) - ALLOWED_CONDITION_KEYS)
            assert not unknown, (
                f"condition {c.get('displayName')!r} carries unknown fields: {unknown}."
            )


def test_no_policy_refers_to_another_policy_by_a_name_that_does_not_exist():
    """A backticked `fdp...` name in the policy file must be a declared policy or an exception."""
    path = REPO / "deploy" / "nightly" / "alert-policy.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    declared = {p["displayName"] for p in raw["policies"]}

    # Deployed but deliberately absent from the file, so re-applying it cannot recreate it.
    KNOWN_UNVERSIONED = {"fdp-nightly stale (no success in 25h)"}

    # Cloud Run job names are a separate namespace from policy names and appear in runbook commands.
    JOB_NAMES = {"fdp-nightly", "fdp-freshness"}

    referenced: set[str] = set()
    for match in re.finditer(r"`(fdp[^`]*)`", path.read_text(encoding="utf-8")):
        referenced.add(match.group(1))

    unknown = sorted(referenced - declared - KNOWN_UNVERSIONED - JOB_NAMES)
    assert not unknown, (
        f"alert-policy.json refers to policy name(s) that do not exist: {unknown}.\n"
        f"declared: {sorted(declared)}\n"
        "A renamed policy left a stale reference behind. These strings render on the Cloud "
        "Monitoring incident page, so this sends an on-call engineer after a policy that is "
        "not there."
    )


def test_the_shipped_profile_has_only_the_prod_target():
    """A second target would turn a mistyped --target into a write to the wrong dataset."""
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
