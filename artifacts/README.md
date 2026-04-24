# Shareable Matchday Output

This folder contains a lightweight shareable artifact for today's D1 upcoming matchday:

- `matchday_insights.json`: exported `dbt show` sample from `mart_matchday_insights`
- `matchday_style_clash.html`: bold-social card view with metric explanations

Feedback collection (anonymous, in-app modal):

- Frontend modal lives in `matchday_style_clash.html`
- Backend template lives in `scripts/feedback_webapp.gs`
- Setup guide: `docs/feedback_collection.md`

## Open locally

Run a local static server from the repo root, then open the page:

```powershell
.\.venv\Scripts\python.exe -m http.server 8000
```

Then visit:

`http://localhost:8000/artifacts/matchday_style_clash.html`
