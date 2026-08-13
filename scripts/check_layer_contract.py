import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DBT_MODELS = REPO_ROOT / "dbt_project" / "models"
BASE_DIR = DBT_MODELS / "2_base"
CORE_DIR = DBT_MODELS / "3_core"
INTERMEDIATE_DIR = DBT_MODELS / "4_intermediate"
STAGING_API_DIR = DBT_MODELS / "1_staging" / "api_football"
STAGING_DIR = DBT_MODELS / "1_staging"

# Intermediate must not depend on marts (DAG flows int → mart only).
INTERMEDIATE_FORBIDDEN_MART_REF = re.compile(
    r"""ref\s*\(\s*['"]mart_""",
    re.IGNORECASE,
)

# Base sits below core/intermediate/marts in the DAG: it may only ref staging
# (stg_) or other base (base_) models. A ref() to any upward layer reverses the
# dependency direction. See dbt_project/docs/layering.md §2_base.
BASE_FORBIDDEN_UPWARD_REF = re.compile(
    r"""ref\s*\(\s*['"](?:dim_|fct_|int_|mart_)""",
    re.IGNORECASE,
)

# Materialization is set once, per LAYER, in dbt_project.yml:
#   1_staging: +materialized: table
#   2_base: +materialized: table
# (base since #547, staging since #33 items 9/10 — see dbt_project/docs/layering.md
# for the measurements behind both; tests/test_materialisation_policy.py pins these
# lines against the config).
# A model in either layer must not carry a per-model
# config(materialized=...) AT ALL, whatever the value: the point is that one
# place decides, so the layer can be re-costed by editing one line. Before #547
# this check allowed `view` and rejected everything else, which silently became
# wrong the moment the layer default changed — which is exactly why the rule is
# "no override", not "no override to the wrong value".
PER_MODEL_MATERIALIZED = re.compile(
    r"""materialized\s*=\s*['"]([a-z_]+)['"]""",
    re.IGNORECASE,
)

CORE_FORBIDDEN_PATTERNS = (
    re.compile(r"\bjson_value\s*\(", re.IGNORECASE),
    re.compile(r"\bjson_query\s*\(", re.IGNORECASE),
    re.compile(r"\bunnest\s*\(", re.IGNORECASE),
    re.compile(r"\bsafe\.parse_json\s*\(", re.IGNORECASE),
    # Core must not ref staging directly — go through base layer
    re.compile(r"""ref\(\s*['"]stg_""", re.IGNORECASE),
    # Multi-competition union belongs in base only; core reads a single base per endpoint.
    re.compile(r"\bunion_all\s*\(", re.IGNORECASE),
)

# Core must not ref marts — mart → core is the correct direction.
CORE_FORBIDDEN_MART_REF = re.compile(
    r"""ref\s*\(\s*['"]mart_""",
    re.IGNORECASE,
)

# Staging must not ref() any dbt model — it reads only from source().
# Cross-layer rule: staging is strictly isolated to raw sources.
STAGING_FORBIDDEN_REF = re.compile(
    r"""\bref\s*\(""",
    re.IGNORECASE,
)

def check_core_forbidden_patterns(errors: list[str]) -> None:
    for sql_path in sorted(CORE_DIR.glob("*.sql")):
        content = sql_path.read_text(encoding="utf-8")
        rel = sql_path.relative_to(REPO_ROOT).as_posix()
        for pattern in CORE_FORBIDDEN_PATTERNS:
            if pattern.search(content):
                errors.append(
                    f"{rel}: contains forbidden pattern in core: {pattern.pattern}"
                )
        if CORE_FORBIDDEN_MART_REF.search(content):
            errors.append(
                f"{rel}: core layer must not ref() mart_* models "
                f"(matched {CORE_FORBIDDEN_MART_REF.pattern}). "
                "Core is upstream of marts; ref direction must be mart → core, not core → mart. "
                "See dbt_project/docs/layering.md §cross-layer-consumption-rule."
            )


def check_staging_no_refs(errors: list[str]) -> None:
    """Staging reads only from source() — never ref() another dbt model."""
    if not STAGING_DIR.is_dir():
        return
    layering_ref = "See dbt_project/docs/layering.md §cross-layer-consumption-rule."
    for sql_path in sorted(STAGING_DIR.rglob("*.sql")):
        content = sql_path.read_text(encoding="utf-8")
        if STAGING_FORBIDDEN_REF.search(content):
            rel = sql_path.relative_to(REPO_ROOT).as_posix()
            errors.append(
                f"{rel}: staging layer must not ref() any dbt model "
                f"(matched {STAGING_FORBIDDEN_REF.pattern}). "
                f"Staging reads only from source(). {layering_ref}"
            )


def check_base_layer(errors: list[str]) -> None:
    if not BASE_DIR.is_dir():
        return
    layering_ref = "See dbt_project/docs/layering.md §2_base."
    for sql_path in sorted(BASE_DIR.rglob("*.sql")):
        content = sql_path.read_text(encoding="utf-8")
        rel = sql_path.relative_to(REPO_ROOT).as_posix()

        # 1. No upward refs — base may only read staging or other base models.
        if BASE_FORBIDDEN_UPWARD_REF.search(content):
            errors.append(
                f"{rel}: base layer must not ref() core/intermediate/mart models "
                f"(matched {BASE_FORBIDDEN_UPWARD_REF.pattern}). Base may only ref stg_* "
                f"or base_* models. {layering_ref}"
            )

        # 2. Materialization is a LAYER decision, so a base model must not set it at all.
        _check_no_per_model_materialisation(errors, sql_path, content, "base", layering_ref)


def _check_no_per_model_materialisation(
    errors: list[str],
    sql_path: Path,
    content: str,
    layer_label: str,
    layering_ref: str,
) -> None:
    """One rule, applied to every layer whose materialisation is set centrally.

    Shared rather than duplicated per layer: the staging case (#33 item 10) is the same rule as
    the base case (#547), and a second copy is how the two drift apart. The check is on the
    PRESENCE of a per-model config(), not on its value — a model pinned to the layer's current
    value is still wrong, because it silently stops moving when the layer is re-costed.
    """
    rel = sql_path.relative_to(REPO_ROOT).as_posix()
    for match in PER_MODEL_MATERIALIZED.finditer(content):
        kind = match.group(1).lower()
        errors.append(
            f"{rel}: {layer_label} model sets materialization to '{kind}' per model. "
            f"{layer_label.capitalize()} materialization is decided once for the layer in "
            f"dbt_project.yml; a per-model override is how one model drifts off the policy and "
            f"stops being re-costed with the rest. Remove the config(). {layering_ref}"
        )


def check_staging_materialisation(errors: list[str]) -> None:
    """Staging models must not set materialisation per model (#33 item 10).

    Staging became a table on 2026-08-12 for the same measured reason base did on 2026-08-02:
    a view stores nothing, so all 59 staging tests re-executed the raw JSON parse. That saving
    only survives if the layer keeps deciding centrally — one model opting back into `view`
    reinstates the rescan for its own tests, invisibly, because nothing fails.
    """
    if not STAGING_DIR.is_dir():
        return
    layering_ref = "See dbt_project/docs/layering.md §1_staging."
    for sql_path in sorted(STAGING_DIR.rglob("*.sql")):
        content = sql_path.read_text(encoding="utf-8")
        _check_no_per_model_materialisation(errors, sql_path, content, "staging", layering_ref)


def check_intermediate_no_mart_refs(errors: list[str]) -> None:
    if not INTERMEDIATE_DIR.is_dir():
        return
    for sql_path in sorted(INTERMEDIATE_DIR.rglob("*.sql")):
        content = sql_path.read_text(encoding="utf-8")
        if INTERMEDIATE_FORBIDDEN_MART_REF.search(content):
            rel = sql_path.relative_to(REPO_ROOT).as_posix()
            errors.append(
                f"{rel}: intermediate layer must not ref() mart_* models "
                f"(matched {INTERMEDIATE_FORBIDDEN_MART_REF.pattern})"
            )


def check_staging_inventory(errors: list[str]) -> None:
    # Generic staging models live directly under api_football/ (unified raw table architecture).
    # Per-competition subdirectories are no longer permitted — the zero-file rule means adding
    # a league requires zero SQL file changes; only the registry entry changes.
    for subdir in sorted(STAGING_API_DIR.iterdir()):
        if subdir.is_dir():
            rel = subdir.relative_to(REPO_ROOT).as_posix()
            errors.append(
                f"{rel}/: per-competition staging subdirectory must not exist. "
                "Generic staging models read all leagues from unified raw tables via league_code. "
                "To add a competition, update docs/competition_registry.yml only."
            )


# --- Staging purity -----------------------------------------------------------
# Staging = latest-snapshot selection (`partition by league_code` only, across an
# append-only raw log) + faithful 1:1 flatten (rename, cast, unnest). Entity-grain
# deduplication, aggregation, pivots, and cross-domain joins are business logic and
# belong in base. See dbt_project/docs/layering.md §1_staging.
_SQL_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_SQL_LINE_COMMENT = re.compile(r"--[^\n]*")

# Capture the columns of a window's `partition by`, stopping at ORDER BY or the
# closing paren of OVER(...). The only partition allowed in staging is league_code.
_PARTITION_BY = re.compile(
    r"partition\s+by\s+(.+?)(?:\border\s+by\b|\))",
    re.IGNORECASE | re.DOTALL,
)
_GROUP_BY = re.compile(r"\bgroup\s+by\b", re.IGNORECASE)
_DISTINCT = re.compile(r"\bdistinct\b", re.IGNORECASE)
_JOIN = re.compile(r"\bjoin\b", re.IGNORECASE)
# A lateral UNNEST flatten is the only allowed join in staging.
_JOIN_UNNEST = re.compile(r"\bjoin\s+unnest\b", re.IGNORECASE)


def _strip_sql_comments(sql: str) -> str:
    return _SQL_LINE_COMMENT.sub("", _SQL_BLOCK_COMMENT.sub(" ", sql))


def check_staging_purity(errors: list[str]) -> None:
    layering_ref = "See dbt_project/docs/layering.md §1_staging."
    for sql_path in sorted(STAGING_API_DIR.glob("*.sql")):
        rel = sql_path.relative_to(REPO_ROOT).as_posix()
        sql = _strip_sql_comments(sql_path.read_text(encoding="utf-8"))

        # 1. Window deduplication: any partition that is not exactly `league_code`.
        for match in _PARTITION_BY.finditer(sql):
            cols = re.sub(r"\s+", " ", match.group(1)).strip().rstrip(",").lower()
            if cols != "league_code":
                errors.append(
                    f"{rel}: forbidden window `partition by {cols}` in staging. Only the "
                    "append-log snapshot selection `partition by league_code` is allowed; "
                    f"entity-grain deduplication belongs in base. {layering_ref}"
                )

        # 2. Aggregation / pivot.
        if _GROUP_BY.search(sql):
            errors.append(
                f"{rel}: forbidden `group by` in staging (aggregation/pivot is business "
                f"reshaping and belongs in base). {layering_ref}"
            )

        # 3. distinct.
        if _DISTINCT.search(sql):
            errors.append(
                f"{rel}: forbidden `distinct` in staging (deduplication belongs in base). "
                f"{layering_ref}"
            )

        # 4. Cross-domain joins (lateral `join unnest(...)` flattening is allowed).
        for match in _JOIN.finditer(sql):
            if not _JOIN_UNNEST.match(sql, match.start()):
                errors.append(
                    f"{rel}: forbidden `join` in staging. Cross-domain joins belong in base; "
                    f"only `join unnest(...)` lateral flattening is allowed. {layering_ref}"
                )
                break


def main() -> int:
    errors: list[str] = []
    check_base_layer(errors)
    check_core_forbidden_patterns(errors)
    check_intermediate_no_mart_refs(errors)
    check_staging_inventory(errors)
    check_staging_purity(errors)
    check_staging_no_refs(errors)
    check_staging_materialisation(errors)

    if errors:
        print("Layer contract checks failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print("Layer contract checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
