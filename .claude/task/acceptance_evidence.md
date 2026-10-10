# Acceptance evidence — the Rankings tab's two blocks get their intro line

Both sites were built from the committed sample data: main in a scratch worktree at gitlab/main, the
branch in site_v2. Each build: 2538 pages, `audit-seo: 2539 built page(s) checked. OK.`,
`check-built-pages: ... 3 rankings page(s) checked. OK.`

criteria_demonstrated:
  - THE TWO INTROS. In the branch build, each Rankings tab page has a `<p class="bsub">` directly after
    each block name (`<div class="sechead"> <span class="eyebrow">Team rankings</span> </div><p
    class="bsub">…`). The lines read, per page: en/bundesliga/stats "The leading teams in Bundesliga
    this season, metric by metric." and "The leading players in Bundesliga this season, metric by
    metric."; de/bundesliga/statistiken "Die besten Mannschaften in der Bundesliga in dieser Saison,
    Kennzahl für Kennzahl." and "Die besten Spieler in der Bundesliga in dieser Saison, Kennzahl für
    Kennzahl."; fi/bundesliga/tilastot "Parhaat joukkueet sarjassa Bundesliga tällä kaudella, tilasto
    kerrallaan." and "Parhaat pelaajat sarjassa Bundesliga tällä kaudella, tilasto kerrallaan." The
    competition is named by inCompetition(), as on the match page.
  - NOTHING ELSE CHANGES. A script compares the visible text of all 2539 built HTML files, with tags,
    scripts, styles and HTML comments removed. 2536 are identical to main. The 3 that differ are the
    Rankings pages above, and on each the only change is the two added lines.
