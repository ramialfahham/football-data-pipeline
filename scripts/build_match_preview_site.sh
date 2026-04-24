#!/usr/bin/env bash
# Assemble GitHub Pages artifact: static UI + JSON exports under match-preview/.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${ROOT}/site/match-preview"
OUT="${ROOT}/_site/match-preview"
mkdir -p "${OUT}"
cp -f "${SRC}/index.html" "${OUT}/"
cp -f "${ROOT}/artifacts/matchday_insights.json" "${OUT}/"
cp -f "${ROOT}/artifacts/metric_glossary.json" "${OUT}/"
echo "Published tree at ${OUT} (upload _site as Pages root)."
