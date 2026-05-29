import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DBT_MODELS = REPO_ROOT / "dbt_project" / "models"
BASE_DIR = DBT_MODELS / "2_base"
CORE_DIR = DBT_MODELS / "3_core"
INTERMEDIATE_DIR = DBT_MODELS / "4_intermediate"
STAGING_API_DIR = DBT_MODELS / "1_staging" / "api_football"

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

# Base models materialise as views by design (dbt_project.yml `2_base:
# +materialized: view`; CLAUDE.md treats this as non-negotiable). A per-model
# config() that overrides materialization to anything other than `view` breaks
# that contract.
BASE_MATERIALIZED = re.compile(
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

def check_core_forbidden_patterns(errors: list[str]) -> None:
    for sql_path in sorted(CORE_DIR.glob("*.sql")):
        content = sql_path.read_text(encoding="utf-8")
        for pattern in CORE_FORBIDDEN_PATTERNS:
            if pattern.search(content):
                rel = sql_path.relative_to(REPO_ROOT).as_posix()
                errors.append(
                    f"{rel}: contains forbidden pattern in core: {pattern.pattern}"
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

        # 2. Must materialize as a view — no per-model override to table/incremental/etc.
        for match in BASE_MATERIALIZED.finditer(content):
            kind = match.group(1).lower()
            if kind != "view":
                errors.append(
                    f"{rel}: base model overrides materialization to '{kind}'. Base models "
                    f"materialise as views by design; do not override this. {layering_ref}"
                )


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

    if errors:
        print("Layer contract checks failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print("Layer contract checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
