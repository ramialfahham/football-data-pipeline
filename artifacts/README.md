# Pages export artifacts

This folder stores JSON exports used to assemble the GitHub Pages app:

- `data/{league}/matchday_insights.json` and `data/{league}/team_season_insights.json`
- `pages_export_manifest.json` (landing + route wiring contract)
- legacy BL1 compat copies (`matchday_insights.json`, `team_season_insights.json`)

Metric labels/descriptions come from [`site/i18n/de.json`](../site/i18n/de.json) and [`site/i18n/en.json`](../site/i18n/en.json) under `metrics.<metric_id>`. Column bindings come from [`dbt_project/seeds/metric_definitions.csv`](../dbt_project/seeds/metric_definitions.csv) and are exported into `site/match-preview/metric_definitions.json` by `scripts/export_metric_definitions_json.py`.

Feedback collection (anonymous, in-app modal):

- Frontend lives in `site/match-preview/index.html`
- Backend template lives in `scripts/feedback_webapp.gs`
- Setup guide: `docs/feedback_collection.md`

## Open locally (same state as GitHub Pages)

1. Build/export data using `scripts/export_matchday_insights.ps1` (Windows) or the equivalent Linux/macOS commands from `docs/feedback_collection.md`.
2. Assemble the static app with `scripts/build_match_preview_site.ps1` (Windows) or `scripts/build_match_preview_site.sh` (Linux/macOS).
3. Serve `_site/` and open `http://localhost:8000/`.

`artifacts/matchday_style_clash.html` is a legacy prototype and is not used by the deployed app.
