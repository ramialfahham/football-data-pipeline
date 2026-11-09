# Verification — one term list: one meaning, one key, one word

Read from the built site (`npm run build` in site_v2, sample data, 757 pages per language).

criteria_demonstrated:
  - **Standings head:** `/en/bundesliga/` reads # | P | W | D | L | Goals | GD | Points; `/de/bundesliga/` reads # | Sp. | S | U | N | Tore | Diff. | Punkte; `/fi/bundesliga/` reads # | O | V | T | H | Maalit | ME | Pisteet.
  - **Match header:** Arminia Bielefeld vs VfL Osnabrück reads "# 10 · 8 points · GD -1" in English, "# 10 · 8 Punkte · Diff. -1" in German and "# 10 · 8 pistettä · ME −1" in Finnish: points in full, goal difference short.
  - **Line-up minutes:** across all match pages the minute unit after a number is "min" 129 times in English, "Min." 129 times in German and "min" 129 times in Finnish, and nothing else.
  - **Home or away:** 2,504 result rows per language on match and team pages read home/away, Heim/Auswärts and koti/vieras; no row shows H, A, K or V.
  - **Player row:** German rows read "5 Tore · 1 Vorlage" and "Vorlagen" for more (1,717 rows), a goalkeeper row reads "Paraden" (5 rows); Finnish rows read maalisyöttö (1,717 rows) and the Finnish stats page heads the board Maalisyötöt.
  - **Menu and squad:** the English menu reads Competitions, Matches, Teams, Players, Table, Statistics; the Finnish Team page of 1. FC Köln heads its squad Pelaajisto, and no Finnish team page shows Kokoonpano.
  - **Positions:** player rows on every page read Forward, Midfielder, Defender, Goalkeeper in English, Stürmer, Mittelfeldspieler, Verteidiger, Torhüter in German and Hyökkääjä, Keskikenttäpelaaja, Puolustaja, Maalivahti in Finnish; 23 rows per language have no position in the data and show none.
  - **Retired words:** the term test's retired-word list, run over every built page's text, title and description, finds none in German or Finnish; in English the one hit is the club name "Defence Force" (Trinidad and Tobago) on the Teams page, a name from the data, not a term.
  - **Build fails on a repeat or a wrong form:** `site_v2/scripts/check-term-list.test.mjs` runs in `npm test` (192 of 192 pass) and fails on two keys holding one text, a retired word, a short form without its full form, and a component reading a form the registry does not give it; `check_copy_gate.py` passes only the identical texts listed in APPROVED_IDENTICAL.
