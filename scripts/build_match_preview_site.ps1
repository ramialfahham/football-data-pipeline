# Mirror scripts/build_match_preview_site.sh for Windows: copy static UI + JSON into _site/match-preview/.
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Out = Join-Path $Root "_site\match-preview"
New-Item -ItemType Directory -Force -Path $Out | Out-Null
Copy-Item (Join-Path $Root "site\match-preview\index.html") $Out -Force
Copy-Item (Join-Path $Root "artifacts\matchday_insights.json") $Out -Force
Copy-Item (Join-Path $Root "artifacts\metric_glossary.json") $Out -Force
Write-Host "Published tree at $Out (serve _site and open /match-preview/)."
