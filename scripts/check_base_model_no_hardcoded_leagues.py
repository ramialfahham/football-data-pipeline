"""CI check: cross-league base models must not contain hardcoded league refs.

A base model is "cross-league" if it declares:
    {% set league_codes = var('active_competition_league_codes') %}

Such models must reference staging models only via the Jinja loop:
    ref('stg_apif__' ~ lc | lower ~ '_entity')

NOT as hardcoded refs like:
    ref('stg_apif__bl1_teams')

This enforces the zero-file rule: adding a league to docs/competition_registry.yml
must require zero existing SQL file edits.

League-specific base models (e.g. base_apif__bl1_transfers.sql) do not declare
the loop marker and are not subject to this check.

Usage (from repo root):
    python scripts/check_base_model_no_hardcoded_leagues.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_MODELS_DIR = REPO_ROOT / "dbt_project" / "models" / "2_base"

LOOP_MARKER = "{% set league_codes = var('active_competition_league_codes')"

# Matches a hardcoded single-league ref inside ref(): ref('stg_apif__bl1_teams')
# Does NOT match Jinja dynamic refs:  ref('stg_apif__' ~ lc | lower ~ '_teams')
HARDCODED_REF = re.compile(r"\{\{\s*ref\('stg_apif__[a-z0-9]+_")


def main() -> int:
    failures: list[str] = []
    checked = 0

    for sql_file in sorted(BASE_MODELS_DIR.rglob("*.sql")):
        content = sql_file.read_text(encoding="utf-8")
        if LOOP_MARKER not in content:
            continue  # league-specific model — not subject to this check
        checked += 1
        for lineno, line in enumerate(content.splitlines(), 1):
            if HARDCODED_REF.search(line):
                rel = sql_file.relative_to(REPO_ROOT)
                failures.append(f"  {rel}:{lineno}: {line.strip()}")

    if failures:
        print(
            "check_base_model_no_hardcoded_leagues: FAIL\n"
            "Cross-league base models must use Jinja loops, not hardcoded league refs.\n"
            "Replace ref('stg_apif__XX_entity') with the loop pattern:\n"
            "  ref('stg_apif__' ~ lc | lower ~ '_entity')\n"
            "Violations found:",
            file=sys.stderr,
        )
        for f in failures:
            print(f, file=sys.stderr)
        return 1

    print(
        f"check_base_model_no_hardcoded_leagues: OK "
        f"({checked} cross-league base model(s) checked, no hardcoded refs found)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
