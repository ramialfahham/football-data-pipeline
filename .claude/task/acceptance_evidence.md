# Verification — the Teams page's rankings

The only site change is one copy key. `round_names.csv` names the Champions League 2024-25 round
the provider calls "Knockout Round Play-offs" with `roundKnockoutPlayoffs`, and the site renders a
round from that key. No committed sample holds a 2024-25 Champions League page, so the name is
shown by the strings file and the copy gate, not by a built page.

criteria_demonstrated:
  - `site_v2/src/i18n/strings.ts` holds `roundKnockoutPlayoffs` as "Knockout phase play-offs" (EN, line 376), "Play-offs der K.-o.-Phase" (DE, line 732) and "Pudotuspelivaiheen playoff" (FI, line 1094). The copy gate reports "COPY GATE ok: 1143 strings across 3 locales, 116 seed label keys resolvable in every locale", so the seed's new key resolves in all three. `node --test src/i18n/strings.test.mjs`: 3 pass, 0 fail.
  - The competition page's header (`CompetitionHeader.astro`) and Matchdays (`MatchdaySchedule.astro`) and the Team page's Competitions block (`TeamCompetitions.astro`) name a round with `roundName` (`site_v2/src/lib/roundName.mjs`), which passes the served `round_label_i18n_key` to `t()`. A round the new `round_names.csv` rows name therefore shows its copy there, as every named round does. `node --test src/lib/roundName.test.mjs`: 3 pass, 0 fail.

pytest: 1,616 passed, 2 skipped. dbt parse, SQLFluff and the fast offline gates pass.
