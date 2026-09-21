"""Key-graph coverage gate — every foreign-key `_sk` column carries a `relationships` test.

Enforces `dbt_project/docs/engineering_standards.md` §3.1 ("`relationships` to the parent for
every foreign key — the whole key graph, not where someone remembered") and is the mechanism
§3.5 names for it. Measured when this was written: 80 foreign keys had no test, of 205 `_sk`
columns.

How a column is classified, from the model ymls alone:

- A CORE KEY is a `3_core` column ending in `_sk` with a `unique` test. Its name is the key's
  name everywhere (`team_sk`, `fixture_sk`, `season_sk`, …) and its model is the parent.
- A column RESOLVES to a core key by its exact name, by a role prefix (`opponent_team_sk`,
  `upcoming_fixture_sk`, `biggest_margin_home_team_sk` → the entity after the prefix), or by
  one of the two spelled aliases (`team_in_sk`, `team_out_sk` → `team_sk`). An ENTITY prefix
  does not resolve: `team_season_sk` is not a season key with a role, it is a composite key
  of its own (`team` is itself an entity), and the same for `player_season_sk`,
  `player_club_season_sk`.
- A model's OWN KEY is a `_sk` column that is `unique` in that model, or part of its
  `unique_combination_of_columns`, when it has no core parent — or the core key in its own
  parent model. It needs no `relationships`.
- Everything else that ends in `_sk` is a FOREIGN KEY and must carry `relationships`
  (`dbt_utils.relationships_where` counts) or a declared SOFT LINK: `meta: soft_link: "<why>"`
  on the column, for a key into a universe wider than the warehouse's dimensions (transfers
  and coaching careers name clubs the tracked competitions never include). A soft link is
  printed in the census on every run so it stays visible; it is never silent.
- A `_sk` that resolves to nothing and is not its model's own key is a finding too: the key
  is undeclared, and the fix is to declare the parent or the grain, not to rename the column.

Floors against an empty walk, as `check_description_hygiene.py` does: if the yml walk finds
fewer models or fewer foreign keys than the repo plainly has, the gate fails rather than
passing on nothing. Exit 1 on any finding, on an unparseable file, and below a floor. Fails
CLOSED.

Run twice on every merge request: as a line of `validate:governance`, beside the other yml
rules, and by `tests/test_check_relationships_coverage.py`, whose last test runs this gate on
the real tree inside `test:python`.
"""
from __future__ import annotations

import pathlib
import re
import sys

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
MODELS_DIR = REPO_ROOT / "dbt_project" / "models"

# Floors, set well under what the repo has (about 100 models, 15 core keys, 180 foreign keys)
# and well over zero, so ordinary deletion never trips them and a broken walk always does.
MIN_MODELS = 50
MIN_CORE_KEYS = 8
MIN_FOREIGN_KEYS = 60

CORE_LAYER = "3_core"
ALIASES = {"team_in_sk": "team_sk", "team_out_sk": "team_sk"}
RELATIONSHIP_TESTS = ("relationships", "dbt_utils.relationships_where")
SK_RE = re.compile(r"_sk$")


class Column:
    __slots__ = ("model", "name", "tests", "meta", "rel")

    def __init__(self, model: str, entry: dict) -> None:
        self.model = model
        self.name = str(entry.get("name"))
        raw = entry.get("tests") or entry.get("data_tests") or []
        self.tests = [t if isinstance(t, str) else next(iter(t)) for t in raw if t]
        self.meta = entry.get("meta") if isinstance(entry.get("meta"), dict) else {}
        self.rel = any(t in RELATIONSHIP_TESTS for t in self.tests)

    @property
    def unique(self) -> bool:
        return "unique" in self.tests

    @property
    def soft_link(self) -> str:
        value = self.meta.get("soft_link")
        return value.strip() if isinstance(value, str) else ""


class Model:
    __slots__ = ("name", "layer", "rel", "columns", "grain")

    def __init__(self, name: str, layer: str, rel: str, entry: dict) -> None:
        self.name = name
        self.layer = layer
        self.rel = rel
        self.columns = [Column(name, c) for c in entry.get("columns") or []
                        if isinstance(c, dict) and isinstance(c.get("name"), str)]
        self.grain: set[str] = set()
        for t in entry.get("tests") or entry.get("data_tests") or []:
            if isinstance(t, dict) and "dbt_utils.unique_combination_of_columns" in t:
                combo = (t["dbt_utils.unique_combination_of_columns"] or {}).get("combination_of_columns") or []
                self.grain.update(str(c) for c in combo)


def _rel(path: pathlib.Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_models(models_dir: pathlib.Path) -> tuple[list[Model], list[str]]:
    """Every model entry in every yml under the models tree. (models, unparseable)."""
    models: list[Model] = []
    unparseable: list[str] = []
    for path in sorted(models_dir.rglob("*.yml")):
        rel = _rel(path)
        if "/target/" in f"/{rel}" or "/dbt_packages/" in f"/{rel}":
            continue
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, UnicodeDecodeError, OSError) as exc:
            unparseable.append(f"{rel}: {exc.__class__.__name__}")
            continue
        if not isinstance(doc, dict):
            continue
        parts = path.relative_to(models_dir).parts
        layer = parts[0] if len(parts) > 1 else ""
        for entry in doc.get("models") or []:
            if isinstance(entry, dict) and isinstance(entry.get("name"), str):
                models.append(Model(entry["name"], layer, rel, entry))
    return models, unparseable


def core_keys(models: list[Model]) -> dict[str, str]:
    """key column name -> the core model that owns it."""
    owners: dict[str, str] = {}
    for m in models:
        if m.layer != CORE_LAYER:
            continue
        for c in m.columns:
            if SK_RE.search(c.name) and c.unique:
                owners[c.name] = m.name
    return owners


def resolve(column: str, keys: dict[str, str]) -> str | None:
    """The core key a column points at, or None when it names no core key."""
    if column in keys:
        return column
    if column in ALIASES:
        return ALIASES[column]
    entities = {k[:-3] for k in keys}
    for key in keys:
        if column.endswith("_" + key):
            prefix = column[: -len(key) - 1]
            # `opponent_team_sk` has a role prefix; `team_season_sk` has an entity prefix and
            # is a composite key of its own, not a season key
            if prefix.split("_")[0] in entities:
                return None
            return key
    return None


def classify(models: list[Model]) -> tuple[list[str], list[str], dict[str, int]]:
    """(findings, soft links, census)."""
    keys = core_keys(models)
    findings: list[str] = []
    soft: list[str] = []
    census = {"models": len(models), "core_keys": len(keys), "foreign_keys": 0,
              "covered": 0, "soft_links": 0, "own_keys": 0}
    for m in models:
        for c in m.columns:
            if not SK_RE.search(c.name):
                continue
            key = resolve(c.name, keys)
            if key == c.name and keys.get(key) == m.name:
                census["own_keys"] += 1
                continue
            if key is None:
                if c.unique or c.name in m.grain:
                    census["own_keys"] += 1
                else:
                    findings.append(
                        f"{m.name}.{c.name} ({m.rel}) - UNDECLARED KEY: names no core key and is "
                        f"not this model's own key (no `unique`, not in its "
                        f"unique_combination_of_columns)\n"
                        "    why banned: a `_sk` nobody can place is either a foreign key with no "
                        "parent or a grain nobody wrote down; declare one or the other"
                    )
                continue
            census["foreign_keys"] += 1
            if c.rel:
                census["covered"] += 1
            elif c.soft_link:
                census["soft_links"] += 1
                soft.append(f"{m.name}.{c.name} -> {keys[key]}.{key}: {c.soft_link}")
            else:
                findings.append(
                    f"{m.name}.{c.name} ({m.rel}) - FOREIGN KEY WITHOUT relationships: "
                    f"expected `relationships: {{to: ref('{keys[key]}'), field: {key}}}` "
                    f"or a declared `meta: soft_link:`\n"
                    "    why banned: engineering_standards.md section 3.1 - every foreign key "
                    "carries relationships to its parent, the whole key graph"
                )
    return findings, soft, census


def main(models_dir: pathlib.Path = MODELS_DIR) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    models, unparseable = load_models(models_dir)
    if unparseable:
        print(f"FAIL: {len(unparseable)} file(s) could not be parsed, so their keys are unchecked:")
        for bad in unparseable:
            print(f"  - {bad}")
        return 1

    findings, soft, census = classify(models)

    if (census["models"] < MIN_MODELS or census["core_keys"] < MIN_CORE_KEYS
            or census["foreign_keys"] < MIN_FOREIGN_KEYS):
        print(f"FAIL: discovery looks broken - {census['models']} models (floor {MIN_MODELS}), "
              f"{census['core_keys']} core keys (floor {MIN_CORE_KEYS}), "
              f"{census['foreign_keys']} foreign keys (floor {MIN_FOREIGN_KEYS}) under "
              f"{_rel(models_dir)}. A coverage check that finds nothing always passes.")
        return 1

    status = "KEY GRAPH" if findings else "OK"
    print(f"{status}: {census['foreign_keys']} foreign keys, {census['covered']} with relationships, "
          f"{census['soft_links']} declared soft links, {census['own_keys']} own keys, "
          f"{census['core_keys']} core keys, {census['models']} models")
    for line in soft:
        print(f"  soft link: {line}")

    if findings:
        print(f"\n{len(findings)} `_sk` column(s) without relationships\n")
        for finding in findings:
            print(f"  - {finding}")
        print("\nThe standard is dbt_project/docs/engineering_standards.md section 3.1.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
