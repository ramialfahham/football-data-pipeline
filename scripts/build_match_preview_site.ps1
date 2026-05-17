# Mirror scripts/build_match_preview_site.sh for Windows.
#   /                          → redirect to /match-preview/
#   /match-preview/            → fixture-detail page + matchday insights JSON
#   /team-season/              → per-team season retrospective + team-season insights JSON
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$SiteRoot = Join-Path $Root "_site"
New-Item -ItemType Directory -Force -Path $SiteRoot | Out-Null

# Root redirect
Copy-Item (Join-Path $Root "site\index.html") $SiteRoot -Force

# /match-preview/
$MpOut = Join-Path $SiteRoot "match-preview"
New-Item -ItemType Directory -Force -Path $MpOut | Out-Null
Copy-Item (Join-Path $Root "site\match-preview\index.html") $MpOut -Force
Copy-Item (Join-Path $Root "artifacts\matchday_insights.json") $MpOut -Force
Copy-Item (Join-Path $Root "artifacts\metric_glossary.json") $MpOut -Force

# /team-season/
$TsOut = Join-Path $SiteRoot "team-season"
New-Item -ItemType Directory -Force -Path $TsOut | Out-Null
Copy-Item (Join-Path $Root "site\team-season\index.html") $TsOut -Force
Copy-Item (Join-Path $Root "artifacts\team_season_insights.json") $TsOut -Force

Write-Host "Published tree at $SiteRoot (serve _site and open /match-preview/ or /team-season/)."
