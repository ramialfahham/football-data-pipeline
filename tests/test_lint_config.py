"""Pin the lint configuration, because every way of breaking it leaves the build GREEN.

WHY THIS EXISTS
---------------
`.ruff-ci.toml` was added on 2026-08-07 after `platform-reviewer` at opus spent ~125k tokens on
!19 finding a duplicate module-level function name. Three review rounds on that change surfaced
five defects, and every one of them shares a shape: the lint setup keeps failing in ways that
report success.

  * The ruleset can be narrowed and nothing goes red — it just stops finding things.
  * `dummy-variable-rgx` can be deleted and the violation count does not move, because the repo
    currently has no violation of the rule it restores.
  * The config can be made auto-discoverable and the only symptom is that a DIFFERENT tool, the
    pre-commit hook, quietly changes behaviour.
  * `per-file-ignores` can grow an entry that disables a whole rule for a whole directory.
  * The CI job can add `--select`, which overrides the config file wholesale, and every test here
    would still pass while the config stops mattering.

Each of those is a guard that looks strong and is nearly inert — the failure
`tests/test_materialisation_policy.py` was written about.

HOW IT IS SHAPED, AND WHY
-------------------------
Values are read from parsed TOML and YAML, never grepped from file text. A guard that matches
prose is defeated by a reword, which is that same file's other lesson.

`select` is asserted to equal ruff's DEFAULT set exactly, and that is deliberate in both
directions. Narrower means CI enforces less than the local pre-commit hook already does — a
backstop that backs nothing. Wider adopts a new class of enforced opinion across the whole tree.
Either is a decision, not a tidy-up.
"""

from __future__ import annotations

import pathlib
import re
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
CI_CONFIG = ROOT / ".ruff-ci.toml"
GITLAB_CI = ROOT / ".gitlab-ci.yml"

# Ruff's own default. Changing this constant is the deliberate act; changing the config alone is not.
RUFF_DEFAULT_SELECT = ["E4", "E7", "E9", "F"]

# The three names ruff auto-discovers by walking up from each linted file.
AUTO_DISCOVERED = ("ruff.toml", ".ruff.toml", "pyproject.toml")


def _config() -> dict:
    return tomllib.loads(CI_CONFIG.read_text(encoding="utf-8"))


def test_select_is_exactly_ruffs_default_set():
    """Narrowing enforces less than the local hook; widening is a new class of opinion."""
    select = _config()["lint"]["select"]

    assert sorted(select) == sorted(RUFF_DEFAULT_SELECT), (
        f"`select` is {select}, not ruff's default {RUFF_DEFAULT_SELECT}. Narrower means the CI "
        "backstop enforces less than .pre-commit-config.yaml already does locally; wider adopts "
        "style/import-order/complexity rules across the whole tree. Both are decisions."
    )


def test_the_dummy_variable_override_survives():
    """Its removal is invisible: the violation count is unchanged and the build stays green.

    Ruff's default exempts ALL underscore-prefixed names from F811/F841. Measured 2026-08-07:
    `f` and `review_patch` are flagged for redefinition; `_f`, `_review_patch` and `__x` are not.
    """
    rgx = _config()["lint"].get("dummy-variable-rgx")

    assert rgx is not None, (
        "`dummy-variable-rgx` is gone. On ruff's default, F811/F841 exempt every underscore-"
        "prefixed name, and every test helper in this repo is underscore-prefixed — so the linter "
        "goes inert against the class it was added for, with no count change to reveal it. "
        "(If this fires unexpectedly, check the key has not been reparented under a later "
        "[table] header: TOML keys belong to the last table declared.)"
    )
    compiled = re.compile(rgx)
    assert compiled.fullmatch("_"), "bare `_` must stay exempt (`for _ in range(3)`)"
    assert compiled.fullmatch("__"), "bare `__` must stay exempt"
    assert not compiled.fullmatch("_review_patch"), (
        f"`{rgx}` still exempts named underscore-prefixed helpers, which is the default behaviour "
        "this setting exists to override"
    )


def test_the_ci_config_is_not_auto_discoverable():
    """The filename is the whole mechanism keeping CI and the pre-commit hook independent.

    Ruff walks up for `ruff.toml` / `.ruff.toml` / `pyproject.toml`. If this config becomes one of
    those, `.pre-commit-config.yaml`'s ruff hook silently adopts it: narrowing `select` would then
    switch rules off on every local commit, and "just align the versions" drags `ruff-format`,
    which reformats 75 files. Neither symptom appears in CI.
    """
    assert CI_CONFIG.name not in AUTO_DISCOVERED, (
        f"{CI_CONFIG.name} is one of ruff's auto-discovered names, so the pre-commit hook now "
        "reads it too"
    )
    for name in AUTO_DISCOVERED:
        candidate = ROOT / name
        if name == "pyproject.toml" and candidate.exists():
            assert "[tool.ruff]" not in candidate.read_text(encoding="utf-8"), (
                "a root pyproject.toml now carries [tool.ruff]; the pre-commit hook will adopt it"
            )
            continue
        assert not candidate.exists(), (
            f"{name} exists at the repo root. Ruff auto-discovers it, so the pre-commit hook "
            "silently adopts its settings — the coupling .ruff-ci.toml's filename exists to avoid."
        )


def test_per_file_ignores_only_exempt_e402_in_the_shim_scripts():
    """An entry here can disable a whole rule for a whole directory, invisibly.

    `"tests/*" = ["F811"]` would switch off the coverage this config was added for, while every
    other test in this file passes and `ruff check` stays green.
    """
    ignores = _config()["lint"].get("per-file-ignores", {})

    for pattern, rules in ignores.items():
        assert rules == ["E402"], (
            f"per-file-ignores exempts {rules} for `{pattern}`. Only E402 is justified here, and "
            "only for scripts that must extend sys.path before importing. Any other rule or any "
            "broader pattern disables coverage without a single test going red."
        )
        assert pattern.startswith("scripts/") and pattern.endswith(".py"), (
            f"`{pattern}` is not a single script under scripts/. Directory-wide patterns turn a "
            "declared exemption into a silent hole."
        )


def test_the_ci_job_passes_the_config_and_no_select_override():
    """`--select` on the command line OVERRIDES the config file wholesale.

    Round 3 of this change found the acceptance criterion itself naming
    `ruff check . --select F,E9`, which would have passed on a tree where E4/E7 were red or where
    the config failed to load at all. The same mistake in the CI job would make every other test
    in this file meaningless.
    """
    text = GITLAB_CI.read_text(encoding="utf-8")
    invocations = re.findall(r"^\s*-\s*(ruff check .*)$", text, re.M)

    assert invocations, "no `ruff check` invocation found in .gitlab-ci.yml"
    for cmd in invocations:
        assert "--config .ruff-ci.toml" in cmd, (
            f"`{cmd}` does not pass `--config .ruff-ci.toml`. Without it ruff finds no config at "
            "all (the filename is deliberately not auto-discovered) and silently falls back to "
            "its defaults, losing dummy-variable-rgx and the per-file-ignores."
        )
        assert "--select" not in cmd and "--ignore" not in cmd, (
            f"`{cmd}` overrides the config from the command line. A CLI --select/--ignore replaces "
            "the config's ruleset, so .ruff-ci.toml stops governing what CI enforces."
        )
