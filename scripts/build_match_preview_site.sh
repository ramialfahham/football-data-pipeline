#!/usr/bin/env bash
# Assemble GitHub Pages artifact: static UI + JSON exports.
#   /                          → landing (competition overview + entry hub)
#   /fixture-list/             → upcoming fixtures (empty during off-season)
#   /data/{league}/              → per-league matchday + team-season JSON (manifest-driven)
#   /match-preview/            → fixture-detail page + legacy BL1 matchday JSON (compat)
#   /team-season/              → per-team season retrospective + legacy BL1 JSON (compat)
#   /pages_export_manifest.json → export contract for multi-league UI wiring
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE_OUT="${ROOT}/_site"
mkdir -p "${SITE_OUT}"

# Landing AT root + shared i18n assets
cp -f "${ROOT}/site/index.html" "${SITE_OUT}/index.html"
cp -f "${ROOT}/site/i18n.js" "${SITE_OUT}/i18n.js"
cp -f "${ROOT}/site/manifest-utils.js" "${SITE_OUT}/manifest-utils.js"
mkdir -p "${SITE_OUT}/i18n"
cp -f "${ROOT}/site/i18n/"*.json "${SITE_OUT}/i18n/"

# /fixture-list/
FL_OUT="${SITE_OUT}/fixture-list"
mkdir -p "${FL_OUT}"
cp -f "${ROOT}/site/fixture-list/index.html" "${FL_OUT}/"

# /match-preview/
MP_OUT="${SITE_OUT}/match-preview"
mkdir -p "${MP_OUT}"
cp -f "${ROOT}/site/match-preview/index.html" "${MP_OUT}/"
if [ -f "${ROOT}/artifacts/data/bl1/matchday_insights.json" ]; then
  cp -f "${ROOT}/artifacts/data/bl1/matchday_insights.json" "${MP_OUT}/matchday_insights.json"
elif [ -f "${ROOT}/artifacts/matchday_insights.json" ]; then
  cp -f "${ROOT}/artifacts/matchday_insights.json" "${MP_OUT}/"
fi
cp -f "${ROOT}/site/match-preview/metric_manifest.json" "${MP_OUT}/"
cp -f "${ROOT}/site/match-preview/metric_definitions.json" "${MP_OUT}/"

# /team-season/
TS_OUT="${SITE_OUT}/team-season"
mkdir -p "${TS_OUT}"
cp -f "${ROOT}/site/team-season/index.html" "${TS_OUT}/"
if [ -f "${ROOT}/artifacts/data/bl1/team_season_insights.json" ]; then
  cp -f "${ROOT}/artifacts/data/bl1/team_season_insights.json" "${TS_OUT}/team_season_insights.json"
elif [ -f "${ROOT}/artifacts/team_season_insights.json" ]; then
  cp -f "${ROOT}/artifacts/team_season_insights.json" "${TS_OUT}/"
fi

# /data/{league}/ + manifest
if [ -d "${ROOT}/artifacts/data" ]; then
  mkdir -p "${SITE_OUT}/data"
  cp -r "${ROOT}/artifacts/data/." "${SITE_OUT}/data/"
fi
if [ -f "${ROOT}/artifacts/pages_export_manifest.json" ]; then
  cp -f "${ROOT}/artifacts/pages_export_manifest.json" "${SITE_OUT}/"
fi

echo "Published tree at ${SITE_OUT} (upload _site as Pages root)."
