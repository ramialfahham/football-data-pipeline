import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DBT_MODELS = REPO_ROOT / "dbt_project" / "models"
BASE_DIR = DBT_MODELS / "2_base"
CORE_DIR = DBT_MODELS / "3_core"
INTERMEDIATE_DIR = DBT_MODELS / "4_intermediate"
MARTS_DIR = DBT_MODELS / "5_marts"
STAGING_API_DIR = DBT_MODELS / "1_staging" / "api_football"
STAGING_DIR = DBT_MODELS / "1_staging"

INTERMEDIATE_FORBIDDEN_MART_REF = re.compile(
    r"""ref\s*\(\s*['"]mart_""",
    re.IGNORECASE,
)

# Base may only ref stg_ or base_ models; a ref() to an upward layer reverses the dependency.
BASE_FORBIDDEN_UPWARD_REF = re.compile(
    r"""ref\s*\(\s*['"](?:dim_|fct_|int_|mart_)""",
    re.IGNORECASE,
)

# Materialization is set once per layer in dbt_project.yml, so a model may carry no per-model
# config(materialized=...); the one exception is `incremental` on a 3_core fact. The config lines,
# quoted here because tests/test_materialisation_policy.py pins them:
#   1_staging: +materialized: table
#   2_base: +materialized: table
PER_MODEL_MATERIALIZED = re.compile(
    r"""materialized\s*=\s*['"]([a-z_]+)['"]""",
    re.IGNORECASE,
)
MATERIALISATION_REF = "See dbt_project/docs/layering.md §Materialisation."

CORE_FORBIDDEN_PATTERNS = (
    re.compile(r"\bjson_value\s*\(", re.IGNORECASE),
    re.compile(r"\bjson_query\s*\(", re.IGNORECASE),
    re.compile(r"\bunnest\s*\(", re.IGNORECASE),
    re.compile(r"\bsafe\.parse_json\s*\(", re.IGNORECASE),
    # Core reads staging only through base.
    re.compile(r"""ref\(\s*['"]stg_""", re.IGNORECASE),
    # Multi-competition union belongs in base only; core reads a single base per endpoint.
    re.compile(r"\bunion_all\s*\(", re.IGNORECASE),
)

CORE_FORBIDDEN_MART_REF = re.compile(
    r"""ref\s*\(\s*['"]mart_""",
    re.IGNORECASE,
)

STAGING_FORBIDDEN_REF = re.compile(
    r"""\bref\s*\(""",
    re.IGNORECASE,
)

# The competition_registry seed is ingest config; dim_league is its only reader.
DBT_PROJECT = REPO_ROOT / "dbt_project"
DBT_TESTS = DBT_PROJECT / "tests"
SCRIPTS_DIR = REPO_ROOT / "scripts"
REGISTRY_SEED_READER = DBT_MODELS / "3_core" / "dim_league.sql"
DBT_SKIP_DIRS = ("target", "dbt_packages", "logs")
REGISTRY_SEED_REF = re.compile(
    r"""ref\s*\(\s*(?:['"][^'"]+['"]\s*,\s*)?['"]competition_registry['"]\s*\)""",
    re.IGNORECASE,
)
REGISTRY_SEED_TABLE = re.compile(r"\.competition_registry\b", re.IGNORECASE)

# The site export reads the marts dataset only: the marts are the data API.
EXPORT_SITE_DATA = SCRIPTS_DIR / "export_site_data.py"
EXPORT_MARTS_DATASET = re.compile(r"""^MARTS_DATASET\s*=\s*['"]marts['"]\s*$""", re.MULTILINE)
EXPORT_NON_MART_READ = (
    re.compile(r"\{GCP_PROJECT\}\.(?!\{MARTS_DATASET\})"),
    re.compile(r"football-data-pipeline-gcp\.(?!marts\.)"),
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

        if BASE_FORBIDDEN_UPWARD_REF.search(content):
            errors.append(
                f"{rel}: base layer must not ref() core/intermediate/mart models "
                f"(matched {BASE_FORBIDDEN_UPWARD_REF.pattern}). Base may only ref stg_* "
                f"or base_* models. {layering_ref}"
            )

        _check_no_per_model_materialisation(
            errors, sql_path, content, "base", MATERIALISATION_REF
        )


def _check_no_per_model_materialisation(
    errors: list[str],
    sql_path: Path,
    content: str,
    layer_label: str,
    layering_ref: str,
) -> None:
    """Flag any per-model materialization, whatever its value, so the layer setting decides."""
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
    """Staging models must not set materialisation per model."""
    if not STAGING_DIR.is_dir():
        return
    for sql_path in sorted(STAGING_DIR.rglob("*.sql")):
        content = sql_path.read_text(encoding="utf-8")
        _check_no_per_model_materialisation(
            errors, sql_path, content, "staging", MATERIALISATION_REF
        )


def check_upper_layer_materialisation(errors: list[str]) -> None:
    """`incremental` is allowed on a 3_core `fct_*` whose source delivers only a per-run delta."""
    for layer_dir, layer_label in (
        (CORE_DIR, "core"),
        (INTERMEDIATE_DIR, "intermediate"),
        (MARTS_DIR, "marts"),
    ):
        if not layer_dir.is_dir():
            continue
        for sql_path in sorted(layer_dir.rglob("*.sql")):
            content = sql_path.read_text(encoding="utf-8")
            if layer_label == "core" and sql_path.name.startswith("fct_"):
                kinds = {m.group(1).lower() for m in PER_MODEL_MATERIALIZED.finditer(content)}
                if kinds <= {"incremental"}:
                    continue
            _check_no_per_model_materialisation(
                errors, sql_path, content, layer_label, MATERIALISATION_REF
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


def check_registry_seed_readers(errors: list[str]) -> None:
    allowed = {REGISTRY_SEED_READER.resolve()}
    dbt_files = [
        path
        for pattern in ("*.sql", "*.yml", "*.yaml")
        for path in DBT_PROJECT.rglob(pattern)
        if not set(path.relative_to(DBT_PROJECT).parts) & set(DBT_SKIP_DIRS)
    ]
    for path in sorted(dbt_files):
        if path.resolve() in allowed:
            continue
        if REGISTRY_SEED_REF.search(path.read_text(encoding="utf-8")):
            rel = path.relative_to(REPO_ROOT).as_posix()
            errors.append(
                f"{rel}: reads the competition_registry seed; read dim_league instead. "
                "dim_league is the seed's only reader (dbt_project/docs/layering.md §3_core)."
            )
    for path in sorted(SCRIPTS_DIR.glob("export_*.py")):
        if REGISTRY_SEED_TABLE.search(path.read_text(encoding="utf-8")):
            rel = path.relative_to(REPO_ROOT).as_posix()
            errors.append(
                f"{rel}: queries the competition_registry seed; read a mart instead "
                "(dbt_project/docs/layering.md §3_core)."
            )


def check_export_reads_marts_only(errors: list[str]) -> None:
    if not EXPORT_SITE_DATA.is_file():
        return
    rel = EXPORT_SITE_DATA.relative_to(REPO_ROOT).as_posix()
    source = EXPORT_SITE_DATA.read_text(encoding="utf-8")
    if not EXPORT_MARTS_DATASET.search(source):
        errors.append(f'{rel}: MARTS_DATASET must be "marts".')
    for number, line in enumerate(source.splitlines(), start=1):
        if any(pattern.search(line) for pattern in EXPORT_NON_MART_READ):
            errors.append(
                f"{rel}:{number}: reads outside the marts dataset; read a mart instead "
                "(dbt_project/docs/layering.md §3_core)."
            )


def check_staging_inventory(errors: list[str]) -> None:
    # Generic staging models sit directly under api_football/; adding a league adds no SQL file.
    for subdir in sorted(STAGING_API_DIR.iterdir()):
        if subdir.is_dir():
            rel = subdir.relative_to(REPO_ROOT).as_posix()
            errors.append(
                f"{rel}/: per-competition staging subdirectory must not exist. "
                "Generic staging models read all leagues from unified raw tables via league_code. "
                "To add a competition, update docs/competition_registry.yml only."
            )


# --- Staging purity -----------------------------------------------------------
# Staging is latest-snapshot selection plus a 1:1 flatten; deduplication, aggregation and joins
# belong in base.
_SQL_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_SQL_LINE_COMMENT = re.compile(r"--[^\n]*")

# Captures a window's `partition by` columns, up to ORDER BY or the closing paren of OVER(...).
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


# These aggregates may return a different value on each build of the same data.
NONDETERMINISTIC_AGGREGATE = re.compile(r"\b(any_value|approx_quantiles)\s*\(", re.IGNORECASE)
_JINJA_COMMENT = re.compile(r"\{#.*?#\}", re.DOTALL)


def check_no_nondeterministic_aggregates(errors: list[str]) -> None:
    files = [
        path
        for path in DBT_PROJECT.rglob("*.sql")
        if not set(path.relative_to(DBT_PROJECT).parts) & set(DBT_SKIP_DIRS)
    ]
    for path in sorted(files):
        sql = _strip_sql_comments(_JINJA_COMMENT.sub(" ", path.read_text(encoding="utf-8")))
        for match in NONDETERMINISTIC_AGGREGATE.finditer(sql):
            rel = path.relative_to(DBT_PROJECT.parent).as_posix()
            errors.append(
                f"{rel}: {match.group(1)}() may return a different value on each build; pick by a "
                "stated order, or use min/max where the group holds one value."
            )


def check_staging_purity(errors: list[str]) -> None:
    layering_ref = "See dbt_project/docs/layering.md §1_staging."
    for sql_path in sorted(STAGING_API_DIR.glob("*.sql")):
        rel = sql_path.relative_to(REPO_ROOT).as_posix()
        sql = _strip_sql_comments(sql_path.read_text(encoding="utf-8"))

        for match in _PARTITION_BY.finditer(sql):
            cols = re.sub(r"\s+", " ", match.group(1)).strip().rstrip(",").lower()
            if cols != "league_code":
                errors.append(
                    f"{rel}: forbidden window `partition by {cols}` in staging. Only the "
                    "append-log snapshot selection `partition by league_code` is allowed; "
                    f"entity-grain deduplication belongs in base. {layering_ref}"
                )

        if _GROUP_BY.search(sql):
            errors.append(
                f"{rel}: forbidden `group by` in staging (aggregation/pivot is business "
                f"reshaping and belongs in base). {layering_ref}"
            )

        if _DISTINCT.search(sql):
            errors.append(
                f"{rel}: forbidden `distinct` in staging (deduplication belongs in base). "
                f"{layering_ref}"
            )

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
    check_registry_seed_readers(errors)
    check_export_reads_marts_only(errors)
    check_no_nondeterministic_aggregates(errors)
    check_staging_inventory(errors)
    check_staging_purity(errors)
    check_staging_no_refs(errors)
    check_staging_materialisation(errors)
    check_upper_layer_materialisation(errors)

    if errors:
        print("Layer contract checks failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print("Layer contract checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
