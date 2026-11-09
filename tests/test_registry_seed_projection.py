"""Pin the registry→seed projection."""

from __future__ import annotations

import csv
import pathlib

import yaml

from scripts import check_registry_var_sync as guard
from scripts.check_registry_var_sync import SEED_COLUMNS as GUARD_COLUMNS
from scripts.check_registry_var_sync import _registry_seed_rows as guard_expected_rows
from scripts.check_registry_var_sync import _seed_rows as guard_actual_rows
from scripts.sync_dbt_vars import SEED_COLUMNS as WRITER_COLUMNS
from scripts.sync_dbt_vars import _normalise

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "competition_registry.yml"
SEED = ROOT / "dbt_project" / "seeds" / "competition_registry.csv"


def _seed_rows() -> list[dict[str, str]]:
    with SEED.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _registry_rows() -> list[dict]:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    return [r for r in (data.get("competitions") or []) if isinstance(r, dict)]


def test_writer_and_guard_share_one_column_list():
    """The guard imports SEED_COLUMNS from the writer, and the import is what could silently regress."""
    assert WRITER_COLUMNS is GUARD_COLUMNS, (
        "check_registry_var_sync no longer shares sync_dbt_vars' SEED_COLUMNS. Import it rather "
        "than restating it: a guard that checks a different column set from the one written is "
        "the silent-coverage-loss #62 names. "
        f"writer={WRITER_COLUMNS} guard={GUARD_COLUMNS}"
    )


def test_guard_catches_whitespace_corruption_in_the_seed(tmp_path, monkeypatch):
    """The guard reads the seed verbatim, so a trailing space fails instead of being normalised away."""
    expected = guard_expected_rows()
    assert guard_actual_rows() == expected, (
        "precondition: the committed seed must match the registry"
    )

    corrupted_text = "\n".join(
        line.replace(",UEFA,", ",UEFA ,") if line.startswith("BL1,") else line
        for line in SEED.read_text(encoding="utf-8").splitlines()
    ) + "\n"
    assert ",UEFA ," in corrupted_text, "the mutation did not apply — the probe would prove nothing"

    corrupted_path = tmp_path / "competition_registry.csv"
    corrupted_path.write_text(corrupted_text, encoding="utf-8")
    monkeypatch.setattr(guard, "REGISTRY_SEED_PATH", corrupted_path)

    assert guard_actual_rows() != expected, (
        "check_registry_var_sync accepted a seed whose confederation carries a trailing space. "
        "The seed side must be read verbatim; normalisation belongs in sync_dbt_vars._normalise, "
        "so that corruption introduced AFTER generation actually fails."
    )


def test_seed_header_matches_the_declared_columns():
    """The committed file must actually have the shape both scripts believe it has."""
    with SEED.open(encoding="utf-8", newline="") as f:
        header = tuple((csv.reader(f).__next__()))
    assert header == WRITER_COLUMNS, (
        "competition_registry.csv's header does not match SEED_COLUMNS. Regenerate it with "
        f"`python scripts/sync_dbt_vars.py`. header={header} expected={WRITER_COLUMNS}"
    )


def test_tier_is_declared_exactly_for_domestic_leagues():
    """`tier` is structurally N/A off a league, so it is checked in both directions on the committed seed."""
    league_without_tier = []
    non_league_with_tier = []
    for row in _seed_rows():
        is_league = row["competition_type"] == "domestic_league"
        has_tier = bool((row.get("tier") or "").strip())
        if is_league and not has_tier:
            league_without_tier.append(row["league_code"])
        if not is_league and has_tier:
            non_league_with_tier.append((row["league_code"], row["competition_type"]))

    assert not league_without_tier, (
        "domestic_league competitions with no `tier` in the seed: "
        f"{sorted(league_without_tier)}. Every league declares its division in "
        "docs/competition_registry.yml; a blank here means the projection dropped it."
    )
    assert not non_league_with_tier, (
        "non-league competitions carrying a `tier`: " f"{sorted(non_league_with_tier)}. "
        "A cup or tournament has no division, so `tier` must be empty. If a competition type "
        "genuinely gains divisions, change this rule deliberately rather than widening it."
    )


COMPETITION_GROUPS = frozenset(
    {"elite", "europe", "international", "calendar", "secondary"}
)


def test_competition_group_is_declared_exactly_for_domestic_leagues():
    """A blank group is legitimate off a league, so `not_null` is wrong and both directions are checked here."""
    league_without_group = []
    non_league_with_group = []
    for row in _seed_rows():
        is_league = row["competition_type"] == "domestic_league"
        has_group = bool((row.get("competition_group") or "").strip())
        if is_league and not has_group:
            league_without_group.append(row["league_code"])
        if not is_league and has_group:
            non_league_with_group.append((row["league_code"], row["competition_type"]))

    assert not league_without_group, (
        "domestic_league competitions with no `competition_group` in the seed: "
        f"{sorted(league_without_group)}. A league with no group is selected by no surface and "
        "fails silently — nothing renders to reveal it. Assign one in "
        "docs/competition_registry.yml and re-run scripts/sync_dbt_vars.py."
    )
    assert not non_league_with_group, (
        f"non-league competitions carrying a `competition_group`: {sorted(non_league_with_group)}. "
        "Groups rank leagues against each other; a cup or tournament is not a candidate, so this "
        "must be empty."
    )


def test_competition_group_uses_only_the_declared_names():
    """A typo'd group passes the completeness check and still selects nothing."""
    unknown = sorted(
        {
            (row["league_code"], row["competition_group"])
            for row in _seed_rows()
            if (row.get("competition_group") or "").strip()
            and row["competition_group"] not in COMPETITION_GROUPS
        }
    )
    assert not unknown, (
        f"competitions with an unrecognised `competition_group`: {unknown}. "
        f"Permitted: {sorted(COMPETITION_GROUPS)}."
    )


def test_projection_is_faithful_to_the_registry():
    """Every projected column equals what the registry declares, for every competition."""
    seed_by_code = {r["league_code"]: r for r in _seed_rows()}
    mismatches = []
    for reg in _registry_rows():
        code, ctype = reg.get("league_code"), reg.get("competition_type")
        if not (code and ctype):
            continue
        row = seed_by_code.get(str(code))
        assert row is not None, f"{code} is in the registry but missing from the seed"
        for col in WRITER_COLUMNS:
            # The seed side is read verbatim so a stray space is not hidden.
            expected = _normalise(reg.get(col))
            actual = row.get(col) or ""
            if actual != expected:
                mismatches.append((code, col, expected, actual))

    assert not mismatches, (
        "seed values differ from the registry (code, column, registry, seed): "
        f"{sorted(mismatches)[:10]}. Run `python scripts/sync_dbt_vars.py`."
    )


def test_country_is_not_projected():
    """Country is provider data in `dim_league`, not registry data."""
    assert "country" not in WRITER_COLUMNS, (
        "`country` was added to the projection. It is deliberately excluded (#69): dim_league "
        "already carries league_country and country_flag_url from the provider, and the "
        "registry's copy holds 'Europe'/'International' for multi-country competitions. "
        "Countries get their own seed and dim under #69."
    )
    with SEED.open(encoding="utf-8", newline="") as f:
        assert "country" not in (csv.reader(f).__next__())
