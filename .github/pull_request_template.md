## Summary

- 
- 

## Why this change

- 

## Layer impact

- [ ] 1_staging
- [ ] 2_base
- [ ] 3_core
- [ ] 4_intermediate
- [ ] 5_marts
- [ ] ingestion
- [ ] docs

## Data quality / contract impact

- [ ] New/updated model descriptions
- [ ] New/updated column descriptions
- [ ] New/updated tests
- [ ] Data dictionary updated (if definitions changed)
- [ ] No breaking change
- [ ] Breaking change (describe below)

### Breaking change notes (if any)

- 

## Validation run

Commands executed:

- [ ] `dbt deps --project-dir .\dbt_project`
- [ ] `dbt parse --project-dir .\dbt_project`
- [ ] `dbt build --project-dir .\dbt_project --selector staging`
- [ ] `dbt build --project-dir .\dbt_project --selector base`
- [ ] Ingestion syntax check (if ingestion changed)

## SQL performance/readability gate (for dbt SQL changes)

- [ ] No `select *` in `2_base` / `3_core` / `4_intermediate` / `5_marts`
- [ ] Dedup/top-1 patterns use `QUALIFY` when rank is not reused
- [ ] No repeated heavy expressions when a reusable CTE can centralize logic
- [ ] Materialization choice (`view` vs `table`) explained for heavy models
- [ ] Grain and key tests still reflect model intent after SQL changes

## Public repo safety checklist

- [ ] No secrets/API keys committed
- [ ] No `.env` or credential files committed
- [ ] `dbt_project/.user.yml` not committed

## Follow-up tasks

- 
