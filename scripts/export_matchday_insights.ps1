# Regenerate artifacts for the Bundesliga match preview:
# - matchday_insights.json from mart_matchday_insights (dbt show row cap = 9 fixtures per round; league_code D1).
# - metric_glossary.json from seeds/metric_glossary.csv (labels and prose only).
# - _site/match-preview/ for the same tree GitHub Pages deploys (local mirror).
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location (Join-Path $Root "dbt_project")
$raw = Join-Path $Root "artifacts\_show.json"
$out = Join-Path $Root "artifacts\matchday_insights.json"
dbt show --select mart_matchday_insights --limit 9 --output json 2>&1 | Out-File -FilePath $raw -Encoding utf8
python (Join-Path $Root "scripts\extract_show_json.py") $raw $out
python (Join-Path $Root "scripts\build_metric_glossary_json.py")
& (Join-Path $Root "scripts\build_match_preview_site.ps1")
