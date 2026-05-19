# Mirror scripts/build_match_preview_site.sh for Windows.
#   /                          → landing (competition overview + entry hub)
#   /fixture-list/             → upcoming fixtures (empty during off-season)
#   /data/{league}/              → per-league matchday + team-season JSON
#   /match-preview/            → fixture-detail page + legacy BL1 matchday JSON (compat)
#   /team-season/              → per-team season retrospective + legacy BL1 JSON (compat)
#   /pages_export_manifest.json → export contract for multi-league UI
#   /wc-pre-tournament/        → WC qualifier-window team JSON (UI: site/wc-pre-tournament/)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$SiteRoot = Join-Path $Root "_site"
New-Item -ItemType Directory -Force -Path $SiteRoot | Out-Null

# Landing AT root + shared i18n assets
Copy-Item (Join-Path $Root "site\index.html") (Join-Path $SiteRoot "index.html") -Force
Copy-Item (Join-Path $Root "site\i18n.js") (Join-Path $SiteRoot "i18n.js") -Force
$I18nOut = Join-Path $SiteRoot "i18n"
New-Item -ItemType Directory -Force -Path $I18nOut | Out-Null
Copy-Item (Join-Path $Root "site\i18n\*.json") $I18nOut -Force

# /fixture-list/
$FlOut = Join-Path $SiteRoot "fixture-list"
New-Item -ItemType Directory -Force -Path $FlOut | Out-Null
Copy-Item (Join-Path $Root "site\fixture-list\index.html") $FlOut -Force

# /match-preview/
$MpOut = Join-Path $SiteRoot "match-preview"
New-Item -ItemType Directory -Force -Path $MpOut | Out-Null
Copy-Item (Join-Path $Root "site\match-preview\index.html") $MpOut -Force
$Bl1Matchday = Join-Path $Root "artifacts\data\bl1\matchday_insights.json"
$LegacyMatchday = Join-Path $Root "artifacts\matchday_insights.json"
if (Test-Path $Bl1Matchday) {
    Copy-Item $Bl1Matchday (Join-Path $MpOut "matchday_insights.json") -Force
} elseif (Test-Path $LegacyMatchday) {
    Copy-Item $LegacyMatchday $MpOut -Force
}
Copy-Item (Join-Path $Root "site\match-preview\metric_manifest.json") $MpOut -Force
Copy-Item (Join-Path $Root "site\match-preview\metric_definitions.json") $MpOut -Force

# /team-season/
$TsOut = Join-Path $SiteRoot "team-season"
New-Item -ItemType Directory -Force -Path $TsOut | Out-Null
Copy-Item (Join-Path $Root "site\team-season\index.html") $TsOut -Force
$Bl1Team = Join-Path $Root "artifacts\data\bl1\team_season_insights.json"
$LegacyTeam = Join-Path $Root "artifacts\team_season_insights.json"
if (Test-Path $Bl1Team) {
    Copy-Item $Bl1Team (Join-Path $TsOut "team_season_insights.json") -Force
} elseif (Test-Path $LegacyTeam) {
    Copy-Item $LegacyTeam $TsOut -Force
}

$DataSrc = Join-Path $Root "artifacts\data"
if (Test-Path $DataSrc) {
    $DataOut = Join-Path $SiteRoot "data"
    New-Item -ItemType Directory -Force -Path $DataOut | Out-Null
    Copy-Item (Join-Path $DataSrc "*") $DataOut -Recurse -Force
}
$Manifest = Join-Path $Root "artifacts\pages_export_manifest.json"
if (Test-Path $Manifest) {
    Copy-Item $Manifest $SiteRoot -Force
}

$WcOut = Join-Path $SiteRoot "wc-pre-tournament"
New-Item -ItemType Directory -Force -Path $WcOut | Out-Null
$WcHtml = Join-Path $Root "site\wc-pre-tournament\index.html"
if (Test-Path $WcHtml) {
    Copy-Item $WcHtml $WcOut -Force
}
Copy-Item (Join-Path $Root "artifacts\wc_pre_tournament_insights.json") $WcOut -Force

Write-Host "Published tree at $SiteRoot (serve _site and open /, /fixture-list/, /match-preview/, /team-season/, or /wc-pre-tournament/)."
