# Mirror scripts/build_match_preview_site.sh for Windows.
#   /                          → landing (competition overview + entry hub)
#   /fixture-list/             → upcoming fixtures (empty during off-season)
#   /match-preview/            → fixture-detail page + matchday insights JSON
#   /team-season/              → per-team season retrospective + team-season insights JSON
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$SiteRoot = Join-Path $Root "_site"
New-Item -ItemType Directory -Force -Path $SiteRoot | Out-Null

# Landing AT root (replaces the previous redirect-to-match-preview pattern)
Copy-Item (Join-Path $Root "site\landing\index.html") (Join-Path $SiteRoot "index.html") -Force

# /fixture-list/
$FlOut = Join-Path $SiteRoot "fixture-list"
New-Item -ItemType Directory -Force -Path $FlOut | Out-Null
Copy-Item (Join-Path $Root "site\fixture-list\index.html") $FlOut -Force

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

Write-Host "Published tree at $SiteRoot (serve _site and open /, /fixture-list/, /match-preview/, or /team-season/)."
