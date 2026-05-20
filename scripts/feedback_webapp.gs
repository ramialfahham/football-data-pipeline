/**
 * Google Apps Script endpoint for anonymous in-app feedback.
 *
 * Security controls:
 * - Shared token in request payload (feedback_token)
 * - Strict schema validation and bounds checking
 * - Minimal stored fields (no personal identifiers)
 *
 * Setup:
 * 1) Create a Google Sheet and set SHEET_ID below.
 * 2) Set FEEDBACK_TOKEN to a long random string.
 * 3) Deploy as Web App: "Anyone" (required for anonymous app users).
 * 4) Set FEEDBACK_APPS_SCRIPT_URL in GitHub Actions (or inject into
 *    site/match-preview/index.html before building local _site preview).
 *
 * Client must POST JSON with Content-Type: text/plain (not application/json)
 * so browsers skip CORS preflight; Apps Script doPost still reads postData.contents.
 */

const SHEET_ID = "replace_with_google_sheet_id";
const SHEET_NAME = "feedback";
const FEEDBACK_TOKEN = "";

function doGet() {
  return json_(200, { ok: true, message: "feedback endpoint live; use POST to submit" });
}

function doPost(e) {
  try {
    const body = JSON.parse(e.postData && e.postData.contents ? e.postData.contents : "{}");
    const token = String(body.feedback_token || "");
    // Optional token check: enable by setting FEEDBACK_TOKEN to a non-empty value in your deployed script.
    if (FEEDBACK_TOKEN && token !== FEEDBACK_TOKEN) {
      return json_(401, { ok: false, error: "unauthorized" });
    }
    const cleaned = validateAndNormalize_(body);

    const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName(SHEET_NAME);
    if (!sheet) {
      return json_(500, { ok: false, error: "sheet_missing" });
    }

    sheet.appendRow([
      new Date().toISOString(),
      cleaned.ease_score,
      cleaned.clarity_score,
      cleaned.improvement_text,
      cleaned.language,
      cleaned.fixture_id,
      cleaned.app_version,
      cleaned.submitted_at,
    ]);

    return json_(200, { ok: true });
  } catch (err) {
    return json_(400, { ok: false, error: "bad_request" });
  }
}

function validateAndNormalize_(body) {
  const ease = Number(body.ease_score);
  const clarity = Number(body.clarity_score);
  if (!(ease >= 1 && ease <= 5) || !(clarity >= 1 && clarity <= 5)) {
    throw new Error("invalid_score");
  }

  const text = String(body.improvement_text || "").trim();
  const sanitized = text
    .replace(/[<>]/g, "")
    .replace(/javascript:/gi, "")
    .slice(0, 500);

  const lang = String(body.language || "en").toLowerCase();
  const safeLang = lang === "de" ? "de" : "en";

  const fixture = body.fixture_id === null || body.fixture_id === undefined
    ? ""
    : String(body.fixture_id).slice(0, 64);

  const appVersion = String(body.app_version || "").slice(0, 64);
  const submittedAt = String(body.submitted_at || new Date().toISOString()).slice(0, 64);

  return {
    ease_score: ease,
    clarity_score: clarity,
    improvement_text: sanitized,
    language: safeLang,
    fixture_id: fixture,
    app_version: appVersion,
    submitted_at: submittedAt,
  };
}

function json_(status, payload) {
  return ContentService
    .createTextOutput(JSON.stringify({ status, ...payload }))
    .setMimeType(ContentService.MimeType.JSON);
}
