import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DBT_MODELS = REPO_ROOT / "dbt_project" / "models"
CORE_DIR = DBT_MODELS / "3_core"
INTERMEDIATE_DIR = DBT_MODELS / "4_intermediate"
STAGING_API_DIR = DBT_MODELS / "1_staging" / "api_football"

# Intermediate must not depend on marts (DAG flows int → mart only).
INTERMEDIATE_FORBIDDEN_MART_REF = re.compile(
    r"""ref\s*\(\s*['"]mart_""",
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
    # Staging models must live in a per-competition subdirectory, never at the root level.
    root_sql = sorted(STAGING_API_DIR.glob("*.sql"))
    for path in root_sql:
        rel = path.relative_to(REPO_ROOT).as_posix()
        errors.append(
            f"{rel}: staging SQL must live in a per-competition subdirectory "
            "(e.g. bl1/ or wc/), not directly under api_football/."
        )


def main() -> int:
    errors: list[str] = []
    check_core_forbidden_patterns(errors)
    check_intermediate_no_mart_refs(errors)
    check_staging_inventory(errors)

    if errors:
        print("Layer contract checks failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print("Layer contract checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
