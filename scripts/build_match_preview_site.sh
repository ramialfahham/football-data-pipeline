#!/usr/bin/env bash
# Assemble GitHub Pages artifact: static UI + JSON exports.
#   /                          → landing (competition overview + entry hub)
#   /fixture-list/             → upcoming fixtures (empty during off-season)
#   /match-preview/            → fixture-detail page + matchday insights JSON
#   /team-season/              → per-team season retrospective + team-season insights JSON
#   /wc-pre-tournament/          → WC qualifier-window team JSON (UI: site/wc-pre-tournament/)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE_OUT="${ROOT}/_site"
mkdir -p "${SITE_OUT}"

# Landing AT root (replaces the previous redirect-to-match-preview pattern)
cp -f "${ROOT}/site/landing/index.html" "${SITE_OUT}/index.html"

# /fixture-list/
FL_OUT="${SITE_OUT}/fixture-list"
mkdir -p "${FL_OUT}"
cp -f "${ROOT}/site/fixture-list/index.html" "${FL_OUT}/"

# /match-preview/
MP_OUT="${SITE_OUT}/match-preview"
mkdir -p "${MP_OUT}"
cp -f "${ROOT}/site/match-preview/index.html" "${MP_OUT}/"
cp -f "${ROOT}/artifacts/matchday_insights.json" "${MP_OUT}/"
cp -f "${ROOT}/artifacts/metric_glossary.json" "${MP_OUT}/"

# /team-season/
TS_OUT="${SITE_OUT}/team-season"
mkdir -p "${TS_OUT}"
cp -f "${ROOT}/site/team-season/index.html" "${TS_OUT}/"
cp -f "${ROOT}/artifacts/team_season_insights.json" "${TS_OUT}/"

# /wc-pre-tournament/ (JSON only until Claude adds index.html)
WC_OUT="${SITE_OUT}/wc-pre-tournament"
mkdir -p "${WC_OUT}"
if [ -f "${ROOT}/site/wc-pre-tournament/index.html" ]; then
  cp -f "${ROOT}/site/wc-pre-tournament/index.html" "${WC_OUT}/"
fi
cp -f "${ROOT}/artifacts/wc_pre_tournament_insights.json" "${WC_OUT}/"
cp -f "${ROOT}/artifacts/metric_glossary.json" "${WC_OUT}/"

echo "Published tree at ${SITE_OUT} (upload _site as Pages root)."
