# Verification — the Home fallback intros

Read from the dev server (`preview_start` name `v2`) on the committed sample. The fallback render
used a temporary `"fallback_season": "2025/26"` at the top of `site_v2/src/data/landing.json`; the
file was restored and is not in the diff. Text read from the rendered `<p>` elements of `/en/`,
`/de/` and `/fi/`.

criteria_demonstrated:
  - **Top players, fallback:** EN "The top player from each league in the rankings of the last completed season, 2025/26: La Liga, Serie A, Liga Portugal, Bundesliga, Eredivisie, Ligue 1, Premier League." DE "Der Top-Spieler jeder Liga in den Ranglisten der letzten abgeschlossenen Saison 2025/26: La Liga, …". FI "Kunkin sarjan kärkipelaaja viimeisimmän päättyneen kauden 2025/26 rankingeissa: La Liga, …".
  - **Top teams, fallback:** EN "The top team from each league in the rankings of the last completed season, 2025/26: La Liga, Eredivisie, Bundesliga, Serie A, Liga Portugal, Premier League, Ligue 1." DE "Die Top-Mannschaft jeder Liga in den Ranglisten der letzten abgeschlossenen Saison 2025/26: La Liga, …". FI "Kunkin sarjan kärkijoukkue viimeisimmän päättyneen kauden 2025/26 rankingeissa: La Liga, …".
  - **In season, unchanged:** with no `fallback_season` in the payload the six intros read as before, e.g. EN "The top player from each league in this season's rankings: La Liga, …", DE "… in den Ranglisten dieser Saison: …", FI "… tämän kauden rankingeissa: …".
  - **Leagues named in order:** the league list after the colon is identical in season and in fallback, for players (La Liga, Serie A, Liga Portugal, Bundesliga, Eredivisie, Ligue 1, Premier League) and for teams (La Liga, Eredivisie, Bundesliga, Serie A, Liga Portugal, Premier League, Ligue 1), in all three locales.
  - **Checks:** `node site_v2/scripts/check-page-specs.mjs` OK (13 pages), `node --test` in site_v2 239 pass, `check_copy_gate.py` OK, `check_ui_i18n_metrics.py` OK.
