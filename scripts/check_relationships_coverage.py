"""Gate that every foreign-key `_sk` column has a `relationships` test or a declared soft link."""
from __future__ import annotations

import pathlib
import re
import sys

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
MODELS_DIR = REPO_ROOT / "dbt_project" / "models"

# Floors well under what the repo has, so ordinary deletion never trips them but a broken walk does.
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
    """(models, unparseable) for every yml under the models tree."""
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
    owners: dict[str, str] = {}
    for m in models:
        if m.layer != CORE_LAYER:
            continue
        for c in m.columns:
            if SK_RE.search(c.name) and c.unique:
                owners[c.name] = m.name
    return owners


def resolve(column: str, keys: dict[str, str]) -> str | None:
    if column in keys:
        return column
    if column in ALIASES:
        return ALIASES[column]
    entities = {k[:-3] for k in keys}
    for key in keys:
        if column.endswith("_" + key):
            prefix = column[: -len(key) - 1]
            # An entity prefix (`team_season_sk`) makes a composite key of its own, not a role.
            if prefix.split("_")[0] in entities:
                return None
            return key
    return None


def classify(models: list[Model]) -> tuple[list[str], list[str], dict[str, int]]:
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
