#!/usr/bin/env python
"""PreToolUse(Edit|Write|MultiEdit) guardrail — dbt layer contract.

Fires when a dbt model .sql file is about to be edited, injecting that layer's
contract *before* the agent writes logic in the wrong layer. This is the
edit-time counterpart to scripts/check_layer_contract.py (which catches the same
violations later, at CI time). Catching it here saves a wasted implementation
pass — the failure mode that produced "dedup in all 73 staging models", later
reverted. Fails open.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _command_utils import emit_context, read_event  # noqa: E402

_LAYER_RE = re.compile(
    r"dbt_project/models/(1_staging|2_base|3_core|4_intermediate|5_marts)/"
)

# Frontend/consumption files (the export scripts and both site trees) — bound by
# the consumption-layer contract in dbt_project/docs/layering.md.
_CONSUMPTION_RE = re.compile(r"/scripts/export_[a-z_]+\.py$|/site(_v2)?/")

_CONSUMPTION_RULE = (
    "CONSUMPTION LAYER (frontend) — CPO ruling: ALL logic and transformation lives in dbt; "
    "the marts are the data API, consumable by any frontend tooling. This file may select, "
    "filter, group, drop keys, rename, format, serialize, route — it may NEVER compute: no "
    "metric math, no window selection, no result/perspective derivation, no business ranking, "
    "no entity affiliation, no slug/identity generation, no taxonomy mapping. Test: would the "
    "value deserve a DQ test, or need to be byte-identical across two frontends? -> dbt. If no "
    "mart serves what the page needs, that is a DATA GAP (register it, ship the mart first) — "
    "never bridge it here. See dbt_project/docs/layering.md §Consumption layer."
)

_LAYER_RULES = {
    "1_staging": (
        "LAYER = staging. ALLOWED only: latest-snapshot select (`partition by league_code` "
        "and nothing else) + faithful 1:1 flatten (rename, cast, `unnest`). FORBIDDEN here: "
        "`distinct`, `group by`, entity-grain dedup, aggregation, pivot, and cross-domain "
        "`join` (only lateral `join unnest(...)` is allowed). All of that belongs in 2_base. "
        "scripts/check_layer_contract.py enforces this at CI. See dbt_project/docs/layering.md §1_staging."
    ),
    "2_base": (
        "LAYER = base — first business logic: deduplication, UNION ALL across sources, entity "
        "alignment. Read generic staging via `ref('stg_apif__<entity>')`; `league_code` flows "
        "through as a column — no per-competition ref(), no UNION-per-league loop. Base models "
        "are VIEWS by design. See dbt_project/docs/layering.md §2_base."
    ),
    "3_core": (
        "LAYER = core — system of record: canonical facts/dims, surrogate keys, grain "
        "enforcement. FORBIDDEN: `ref('stg_*')` (read from base, never staging); "
        "`json_value`/`json_query`/`unnest`/`parse_json` (raw parsing belongs upstream); "
        "`union_all` (multi-competition union belongs in base). CI enforces. "
        "See dbt_project/docs/layering.md §3_core."
    ),
    "4_intermediate": (
        "LAYER = intermediate — complex multi-source transforms / feature engineering. Must NOT "
        "`ref()` any `mart_*` model: the DAG flows intermediate → mart, never back. CI enforces. "
        "See dbt_project/docs/layering.md."
    ),
    "5_marts": (
        "LAYER = marts — consumption: denormalised, app-optimised. `league_code` is the partition "
        "key: never hardcode a competition identifier (D1/BL1/WC/…) in business logic; the mart "
        "must work for any league_code unchanged. See dbt_project/docs/layering.md §5_marts."
    ),
}


def main() -> int:
    event = read_event()
    try:
        file_path = (event.get("tool_input") or {}).get("file_path") or ""
    except Exception:
        return 0
    if not file_path:
        return 0
    norm = file_path.replace("\\", "/")
    if _CONSUMPTION_RE.search(norm):
        emit_context("PreToolUse", _CONSUMPTION_RULE)
        return 0
    if not norm.endswith(".sql"):
        return 0
    m = _LAYER_RE.search(norm)
    if not m:
        return 0
    rule = _LAYER_RULES.get(m.group(1))
    if rule:
        emit_context("PreToolUse", rule)
    return 0


if __name__ == "__main__":
    sys.exit(main())
