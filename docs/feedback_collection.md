# In-App Anonymous Feedback Setup

This prototype collects app-level feedback inside the UI (no redirect) with exactly three questions:

1. Ease of use (1-5)
2. Clarity of insights (1-5)
3. One thing to improve first (free text)

The flow stores only anonymous product feedback (no name/email/user account).

## Exact steps to collect feedback (GitHub Pages)

1. **Google Sheet:** Create a spreadsheet. Add a worksheet tab named exactly **`feedback`**. Row 1 can be headers (`ingested_at`, `ease_score`, …) or empty — the script appends rows.
2. **Apps Script:** Go to [script.google.com](https://script.google.com) → New project → paste the full contents of **`scripts/feedback_webapp.gs`**.
3. In that script, set **`SHEET_ID`** to your Sheet’s ID (from the Sheet URL: `docs.google.com/spreadsheets/d/<THIS_PART>/edit`). Leave **`FEEDBACK_TOKEN`** empty unless you want a shared secret (if you set it, set the same string in the HTML `FEEDBACK_TOKEN` constant and in CI you’d need a second secret — optional).
4. **Deploy:** Deploy → New deployment → Type **Web app** → Execute as **Me** → Who has access **Anyone** → Deploy. Copy the **Web app URL** (must end with **`/exec`**).
5. **GitHub:** In the repo → **Settings → Secrets and variables → Actions** → **New repository secret** → Name **`FEEDBACK_APPS_SCRIPT_URL`** → Value = that **`/exec`** URL (full string).
6. **Publish:** Run the workflow **Deploy match preview (GitHub Pages)** on `main` (or push a change that triggers it). The build injects the URL into the page; the **Feedback** button appears and POSTs to your script.
7. **Verify:** Submit feedback from the live site → confirm a new row appears on the **`feedback`** tab.

**Local mirror of the live app:** skip steps 5–6; keep `site/match-preview/index.html` as-is, run `scripts/export_matchday_insights.ps1` (Windows) or `python scripts/export_pages_data.py` + `python scripts/export_wc_pre_tournament_json.py artifacts/wc_pre_tournament_insights.json` + `python scripts/export_metric_definitions_json.py` + `bash scripts/build_match_preview_site.sh` (Linux/macOS), then serve `_site/` and open `/`.

## Does it work end-to-end?

**Yes**, once all of the following are true:

1. Google Sheet exists with tab name **`feedback`** (columns as below).
2. **`scripts/feedback_webapp.gs`** is deployed as a Web App with **`SHEET_ID`** set, **Execute as: Me**, **Who has access: Anyone** (required so anonymous visitors can POST).
3. The deployed **`…/exec`** URL is available to the browser:
   - **GitHub Pages:** add repository secret **`FEEDBACK_APPS_SCRIPT_URL`** with that full URL. The Pages workflow runs `scripts/inject_feedback_endpoint.py` before upload so the built page contains your **`/exec`** URL and **Senden** reaches your script.
   - **Local `_site/` mirror:** run `python scripts/inject_feedback_endpoint.py site/match-preview/index.html "<your_exec_url>"` on a local copy before `scripts/build_match_preview_site.sh` / `scripts/build_match_preview_site.ps1`, then serve `_site/`.

The **Feedback** button is always shown. If the URL is still the placeholder, **Senden** shows a short hint instead of calling Google.

Optional: set **`FEEDBACK_TOKEN`** in both the Apps Script and the HTML constant if you want a shared secret gate; leave both empty to skip.

## 1) Configure frontend placeholders

For **local** `_site/` previews only, edit constants in `site/match-preview/index.html` (or run `scripts/inject_feedback_endpoint.py` before building `_site/`):

- `FEEDBACK_ENDPOINT`: your deployed Web App **`…/exec`** URL
- `FEEDBACK_TOKEN`: optional; must match the script if you enabled the check there

## 2) Create Google Sheet

Create a Google Sheet with tab name `feedback`.

Suggested column order:

1. `ingested_at`
2. `ease_score`
3. `clarity_score`
4. `improvement_text`
5. `language`
6. `fixture_id`
7. `app_version`
8. `submitted_at`

## 3) Deploy Google Apps Script endpoint

Use `scripts/feedback_webapp.gs` in Apps Script:

- Replace `SHEET_ID`
- Set `FEEDBACK_TOKEN` only if you want token-based gatekeeping
- Deploy as Web App (execute as you, access: anyone)

**If the browser shows a CORS / network error when sending:** the match preview page POSTs JSON with `Content-Type: text/plain` on purpose. `application/json` triggers a preflight `OPTIONS` request; Google Apps Script web apps often do not handle that, so the request never reaches `doPost`. Do not change the client back to `application/json` unless you add a proxy that handles CORS.

## 4) Security baseline

- Never commit real tokens, sheet IDs, or deployment URLs if you consider them sensitive.
- Keep `FEEDBACK_TOKEN` private and rotate immediately if exposed.
- Collect only anonymous fields listed above.
- Keep strict numeric bounds for scores (1..5).
- Sanitize comment text and cap length.
- Review unusual spikes weekly and rotate token if abused.

## 5) Review cadence

At least once per week:

- Avg ease score
- Avg clarity score
- Top 3 repeated qualitative themes
- 3 sample comments

Share this digest in chat for improvement planning.

## Incident note (if a token was pushed already)

If a token was ever committed in git history:

1. Rotate token in deployed Apps Script immediately.
2. Update local app config with the new token.
3. Treat old token as compromised permanently.
