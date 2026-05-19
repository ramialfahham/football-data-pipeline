# Playoff window policy (BL1, BL2, L1)

Evidence for CPO decisions on landing phase and matchday export. Row counts in `pages_export_manifest.json` drive UI routing; `matchday_source_mart` drives relegation labeling (see PR #102 UI).

**Investigation date:** 2026-05-19 (BigQuery, production marts).

---

## Observed data (2025/26 season)

### Upcoming fixtures (`int_matchday__upcoming_round_fixtures`)

| league_code | round_name | status_short | fixture_count |
|-------------|------------|--------------|---------------|
| BL2 | Final | NS | 2 |
| L1 | Final | NS | 2 |

Both leagues expose only **`Final`** play-off legs in the upcoming-round pipeline. No other playoff `round_name` values appear in the unified mart slice today.

### Unified mart (`mart_matchday_insights`)

| league_code | round_name | rows | form notes |
|-------------|------------|------|------------|
| BL2 | Final | 2 | One side often has `home_form_games_played = 0` or `away_form_games_played = 0`; at least one row with null recent metrics |
| L1 | Final | 2 | Mixed form depth (1 vs 5 games on home/away sides) |

### BL1 relegation (reference pattern)

- **Excluded from unified mart:** `round_name` in var `bl1_relegation_round_names` (`Final`, `Relegation Round`).
- **Dedicated surface:** `mart_matchday_insights_bl1_relegation` + export fallback in `scripts/export_pages_data.py`.
- **BL2 promotion tie:** Same fixtures may appear on BL1 relegation path; BL2 unified slice should not duplicate them for landing.

---

## Expert default (recommended)

| League | Window | Recommendation | UI effect after data PR |
|--------|--------|----------------|-------------------------|
| **BL1** | Relegation play-off | Keep current split mart + export fallback | Matchday card + relegation label via `matchday_source_mart` |
| **BL2** | Promotion play-off (`Final`) | **(b)** Exclude `Final` from unified mart; show promotion legs on BL1 relegation path only | BL2 landing → season recap (no JS hack) |
| **L1** | Relegation play-off (`Final`) | **(b)** Exclude `Final` from unified mart first | L1 landing → season recap |
| **L1** | Optional later **(a)** | Add `mart_matchday_insights_l1_relegation` + export fallback (mirror BL1) | Matchday card + relegation label when dedicated mart has rows |

**Out of scope until 3. Liga ingested:** BL2 relegation vs 3. Liga (`round_name` TBD).

---

## CPO sign-off (fill before Phase 3 merge)

- [ ] BL2: exclude `Final` from unified mart — **yes / no**
- [ ] L1: exclude `Final` from unified mart — **yes / no**
- [ ] L1: build dedicated relegation mart **(a)** — **yes / no / defer**

---

## Implementation mapping (Phase 3)

| Var | Values (current API labels) | Macro |
|-----|------------------------------|--------|
| `bl2_playoff_round_names` | `Final` | `bl2_playoff_round_names_in_clause()` |
| `l1_relegation_round_names` | `Final` | `l1_relegation_round_names_in_clause()` |

Extend `mart_matchday_insights.sql` `WHERE` with league-scoped exclusions (same structure as BL1).

---

## SQL references (ad-hoc, not committed)

Re-run in BigQuery when seasons change:

```sql
SELECT league_code, round_name, status_short, COUNT(*) AS n
FROM `football-data-pipeline-gcp.intermediate.int_matchday__upcoming_round_fixtures`
WHERE league_code IN ('BL2', 'L1')
GROUP BY 1, 2, 3;
```
