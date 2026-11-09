"""Pins the ruff lint configuration, read from parsed TOML and YAML, never grepped from text.

`select` must equal ruff's default set exactly, so narrowing or widening it is a deliberate edit.
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

# Ruff's own default set.
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
    """Without the override ruff exempts every underscore-prefixed name from F811/F841."""
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
    """The config is passed explicitly; an auto-discovered one would be a second, silent source."""
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
    """An entry here can disable a whole rule for a whole directory, invisibly."""
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
    """`--select` on the command line overrides the config file wholesale."""
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
