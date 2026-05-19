"""DEPRECATED — do not run.

Per-league mart_matchday_insights_{code} files were removed in favour of a single
mart_matchday_insights with league_code on every row. Onboard new domestic leagues via
the competition registry and vars.active_competition_league_codes only.
"""
from __future__ import annotations

import sys

if __name__ == "__main__":
    print(__doc__, file=sys.stderr)
    raise SystemExit(1)
