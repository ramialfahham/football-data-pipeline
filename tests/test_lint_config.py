"""Pin the lint configuration, because every way of breaking it leaves the build GREEN.

WHY THIS EXISTS
---------------
`.ruff-ci.toml` was added after a review spent ~125k tokens finding a duplicate module-level
function name that a linter should have found. The change that added it surfaced five defects,
and every one of them shares a shape: the lint setup keeps failing in ways that report success.

  * The ruleset can be narrowed and nothing goes red — it just stops finding things.
  * `dummy-variable-rgx` can be deleted and the violation count does not move, because the repo
    currently has no violation of the rule it restores.
  * The config can be made auto-discoverable and the only symptom is that bare `ruff check` and
    editors quietly change behaviour.
  * `per-file-ignores` can grow an entry that disables a whole rule for a whole directory.
  * The hook can add `--select`, which overrides the config file wholesale, and every test here
    would still pass while the config stops mattering.

CI's `lint:python` runs `pre-commit run --all-files`, so the ruff hook in `.pre-commit-config.yaml`
is the one place ruff is invoked, locally and in CI.

Each of those is a guard that looks strong and is nearly inert — the failure
`tests/test_materialisation_policy.py` was written about.

HOW IT IS SHAPED, AND WHY
-------------------------
Values are read from parsed TOML and YAML, never grepped from file text. A guard that matches
prose is defeated by a reword, which is that same file's other lesson.

`select` is asserted to equal ruff's DEFAULT set exactly, and that is deliberate in both
directions. Narrower means CI enforces less than ruff's own baseline. Wider adopts a new class of
enforced opinion across the whole tree. Either is a decision, not a tidy-up.
"""

from __future__ import annotations

import pathlib
import re
import tomllib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
CI_CONFIG = ROOT / ".ruff-ci.toml"
GITLAB_CI = ROOT / ".gitlab-ci.yml"
PRE_COMMIT = ROOT / ".pre-commit-config.yaml"
REQUIREMENTS_DEV = ROOT / "requirements-dev.txt"

# Ruff's own default. Changing this constant is the deliberate act; changing the config alone is not.
RUFF_DEFAULT_SELECT = ["E4", "E7", "E9", "F"]

# The three names ruff auto-discovers by walking up from each linted file.
AUTO_DISCOVERED = ("ruff.toml", ".ruff.toml", "pyproject.toml")


def _config() -> dict:
    return tomllib.loads(CI_CONFIG.read_text(encoding="utf-8"))


def test_select_is_exactly_ruffs_default_set():
    """Narrowing enforces less than ruff's baseline; widening is a new class of opinion."""
    select = _config()["lint"]["select"]

    assert sorted(select) == sorted(RUFF_DEFAULT_SELECT), (
        f"`select` is {select}, not ruff's default {RUFF_DEFAULT_SELECT}. Narrower means CI "
        "enforces less than ruff's own baseline; wider adopts style/import-order/complexity "
        "rules across the whole tree. Both are decisions."
    )


def test_the_dummy_variable_override_survives():
    """Its removal is invisible: the violation count is unchanged and the build stays green.

    Ruff's default exempts ALL underscore-prefixed names from F811/F841. Measured:
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
    """The config is passed explicitly; an auto-discovered one would be a second, silent source.

    Ruff walks up for `ruff.toml` / `.ruff.toml` / `pyproject.toml`. A root file of that name is
    adopted by bare `ruff check` and by editors, which then disagree with the hook CI runs, and
    nothing in CI shows it.
    """
    assert CI_CONFIG.name not in AUTO_DISCOVERED, (
        f"{CI_CONFIG.name} is one of ruff's auto-discovered names, so bare `ruff check` now "
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
            f"{name} exists at the repo root. Ruff auto-discovers it, so bare `ruff check` and "
            "editors silently adopt its settings — the drift .ruff-ci.toml's filename exists to avoid."
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


def _ruff_hooks() -> list[tuple[str, dict]]:
    config = yaml.safe_load(PRE_COMMIT.read_text(encoding="utf-8"))
    return [
        (repo.get("rev", ""), hook)
        for repo in config["repos"]
        for hook in repo["hooks"]
        if hook["id"] == "ruff-check"
    ]


def test_the_ruff_hook_passes_the_config_and_no_select_override():
    """`--select` on the command line OVERRIDES the config file wholesale.

    The acceptance criterion of the change that added the config itself once named
    `ruff check . --select F,E9`, which would have passed on a tree where E4/E7 were red or where
    the config failed to load at all. The same mistake in the hook would make every other test
    in this file meaningless.
    """
    hooks = _ruff_hooks()

    assert len(hooks) == 1, f"expected exactly one ruff hook in .pre-commit-config.yaml, found {len(hooks)}"
    args = hooks[0][1].get("args", [])
    assert "--config" in args and args[args.index("--config") + 1] == ".ruff-ci.toml", (
        f"the ruff hook's args {args} do not pass `--config .ruff-ci.toml`. Without it ruff finds "
        "no config at all (the filename is deliberately not auto-discovered) and silently falls "
        "back to its defaults, losing dummy-variable-rgx and the per-file-ignores."
    )
    assert not any(a.startswith(("--select", "--ignore", "--extend-select")) for a in args), (
        f"the ruff hook's args {args} override the config from the command line, so "
        ".ruff-ci.toml stops governing what CI enforces."
    )


def test_the_ruff_hook_runs_the_pinned_ruff_version():
    """Two pins of one tool drift apart unless something compares them."""
    pinned = re.search(r"^ruff==(\S+)$", REQUIREMENTS_DEV.read_text(encoding="utf-8"), re.M)

    assert pinned, "requirements-dev.txt has no exact ruff pin"
    assert _ruff_hooks()[0][0] == f"v{pinned.group(1)}", (
        f"the ruff hook runs {_ruff_hooks()[0][0]} but requirements-dev.txt pins ruff "
        f"{pinned.group(1)}; local and CI lint would disagree with a direct `ruff check`"
    )


def test_ci_lint_runs_pre_commit_on_all_files():
    """CI and the local hook are one config only while CI actually runs it."""
    ci = yaml.safe_load(GITLAB_CI.read_text(encoding="utf-8"))
    script = " ".join(ci["lint:python"]["script"])

    assert "pre_commit run --all-files" in script or "pre-commit run --all-files" in script, (
        f"lint:python runs `{script}`, not pre-commit on all files, so CI and the local hooks "
        "can drift apart again"
    )
