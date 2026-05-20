# Back-compat wrapper: regenerate the full GitHub Pages preview tree locally.
# Produces the same artifact contract as pages-match-preview.yml:
# - artifacts/data/{league}/matchday_insights.json
# - artifacts/data/{league}/team_season_insights.json
# - artifacts/pages_export_manifest.json
# - site/match-preview/metric_definitions.json
# - _site/ (serve and open `/` for the same entry flow as production)
#
# Prerequisite: ADC auth for BigQuery queries (same as scripts/export_pages_data.py).
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root
python (Join-Path $Root "scripts\export_pages_data.py")
python (Join-Path $Root "scripts\export_metric_definitions_json.py")
& (Join-Path $Root "scripts\build_match_preview_site.ps1")
