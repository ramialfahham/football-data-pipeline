#!/usr/bin/env bash
# Assemble GitHub Pages artifact: static UI + JSON exports.
#   /                          → redirect to /match-preview/
#   /match-preview/            → fixture-detail page + matchday insights JSON
#   /team-season/              → per-team season retrospective + team-season insights JSON
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE_OUT="${ROOT}/_site"
mkdir -p "${SITE_OUT}"

# Root redirect
cp -f "${ROOT}/site/index.html" "${SITE_OUT}/"

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

echo "Published tree at ${SITE_OUT} (upload _site as Pages root)."
