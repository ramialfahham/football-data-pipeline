# In-App Anonymous Feedback Setup

This prototype collects app-level feedback inside the UI (no redirect) with exactly three questions:

1. Ease of use (1-5)
2. Clarity of insights (1-5)
3. One thing to improve first (free text)

The flow stores only anonymous product feedback (no name/email/user account).

## 1) Configure frontend placeholders

Update these constants in `artifacts/matchday_style_clash.html`:

- `FEEDBACK_ENDPOINT`: your deployed Google Apps Script Web App URL
- `FEEDBACK_TOKEN`: optional shared token (same value as backend script). Leave empty if not using token check.

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
