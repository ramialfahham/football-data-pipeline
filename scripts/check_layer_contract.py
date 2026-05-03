import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DBT_MODELS = REPO_ROOT / "dbt_project" / "models"
CORE_DIR = DBT_MODELS / "3_core"
STAGING_API_DIR = DBT_MODELS / "1_staging" / "api_football"

CORE_FORBIDDEN_PATTERNS = (
    re.compile(r"\bjson_value\s*\(", re.IGNORECASE),
    re.compile(r"\bjson_query\s*\(", re.IGNORECASE),
    re.compile(r"\bunnest\s*\(", re.IGNORECASE),
    re.compile(r"\bsafe\.parse_json\s*\(", re.IGNORECASE),
    # Core must not ref staging directly — go through base layer
    re.compile(r"""ref\(\s*['"]stg_""", re.IGNORECASE),
)

EXPECTED_STAGING_MODELS = {
    "stg_apif__bl1_fixture_events.sql",
    "stg_apif__bl1_fixture_players.sql",
    "stg_apif__bl1_fixture_statistics.sql",
    "stg_apif__bl1_fixtures_next.sql",
    "stg_apif__bl1_injuries.sql",
    "stg_apif__bl1_leagues.sql",
    "stg_apif__bl1_lineups.sql",
    "stg_apif__bl1_players.sql",
    "stg_apif__bl1_predictions.sql",
    "stg_apif__bl1_rounds.sql",
    "stg_apif__bl1_standings.sql",
    "stg_apif__bl1_teams.sql",
    "stg_apif__bl1_transfers.sql",
}


def check_core_forbidden_patterns(errors: list[str]) -> None:
    for sql_path in sorted(CORE_DIR.glob("*.sql")):
        content = sql_path.read_text(encoding="utf-8")
        for pattern in CORE_FORBIDDEN_PATTERNS:
            if pattern.search(content):
                rel = sql_path.relative_to(REPO_ROOT).as_posix()
                errors.append(
                    f"{rel}: contains forbidden pattern in core: {pattern.pattern}"
                )


def check_staging_inventory(errors: list[str]) -> None:
    actual = {path.name for path in STAGING_API_DIR.glob("*.sql")}
    unexpected = sorted(actual - EXPECTED_STAGING_MODELS)
    missing = sorted(EXPECTED_STAGING_MODELS - actual)

    for name in unexpected:
        errors.append(
            f"Unexpected staging model in api_football: {name} "
            "(only stg_apif__bl1_*.sql inventory is allowed)."
        )

    for name in missing:
        errors.append(f"Missing required staging model in api_football: {name}")


def main() -> int:
    errors: list[str] = []
    check_core_forbidden_patterns(errors)
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
