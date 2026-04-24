# Shareable Matchday Output

This folder contains a lightweight shareable artifact for the upcoming **Bundesliga** matchday (internal `league_code` D1 in the warehouse):

- `matchday_insights.json`: exported `dbt show` from `mart_matchday_insights` with `--limit 9` (one row per fixture; nine is the maximum fixtures per Bundesliga round). Rows include `league_name` **Bundesliga** for display.
- `metric_glossary.json`: built from [`dbt_project/seeds/metric_glossary.csv`](../dbt_project/seeds/metric_glossary.csv) via `scripts/build_metric_glossary_json.py` — `metric_key`, `label`, and `description` only; run `scripts/export_matchday_insights.ps1` to refresh both files.
- `matchday_style_clash.html`: bold-social card view with metric explanations

Feedback collection (anonymous, in-app modal):

- Frontend modal lives in `matchday_style_clash.html`
- Backend template lives in `scripts/feedback_webapp.gs`
- Setup guide: `docs/feedback_collection.md`

## Open locally

**Bundled carousel under `artifacts/`** — run a static server from the repo root, then open:

`http://localhost:8000/artifacts/matchday_style_clash.html`

**Same experience as GitHub Pages** — after `.\scripts\export_matchday_insights.ps1` and `.\scripts\build_match_preview_site.ps1`, serve the `_site` folder and open `/match-preview/`. Automated deploy: see the [Shareable Bundesliga match preview](../docs/operations_guide.md#shareable-bundesliga-match-preview-github-pages) section in the operations guide.
