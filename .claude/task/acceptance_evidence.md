# Verification — researched line-ups of the 26 matches behind the blank squads

30 matches with no player rows blanked 41 squads. 26 are now researched from the competition's
official match record; four stay out: Coppa Italia 1564791 and 1564792, Copa del Rey 1644342 and
1644358.

- **Sources:** resultados.rfef.es 6 (Copa del Rey), uefa.com 11 (Champions League 4, Europa League 3, Conference League 4), veikkausliiga.com 4, kleague.com 5. Each row carries its match's link.
- **How each match was checked:** every official player matched to the provider's player by team, shirt number and name; both sheets and every substitution compared with the official record.
- **Against the provider's sheets (the 1,088 rows it holds for these matches):** 21 matches failed the substitution check and 5 the squad lists. The rows add one player and his substitution (A. L. Elvebu, Tromsø, 570211, the id the provider gives him on its Tromsø squad list of 2026), carry the official minute in 47 substitutions and the official pair in 39.
- **On prod data** (the branch's base_apif__lineups and base_apif__fixture_players_from_lineups with all 197 researched matches, session-only copy, 1.06 GB): every one comes out researched; assert_lineup_researched_matches_hold and assert_players_from_lineups_goals_add_up return no rows; every team of the 26 matches gets its player rows with no blank goals and no blank minutes; the five Copa del Rey matches that fail the squad lists are outranked by their official source, as the test allows.
- **The research list:** the branch's base_apif__lineups against prod's built table (session-only, 0.46 GB): 26 matches change state, exactly these 26.
- **Formations and positions** equal the provider's on every row it holds, but three position codes the provider leaves blank (A. Drina and T. Gudelj in 1589428, Ieltsin Camoes in 1607628), which take the official record's. Where a row is blank, the provider's is too, the Floriana keeper in 1589428 included.
- **The seed:** 1,089 new rows (8,194 in all), none removed, no duplicate key, every source https and official, one formation per team, eleven starters per team, 253 substitutions each paired with a player leaving on the same sheet.
- **Cards stay blank for two teams:** in 1645578 the provider's Sevilla yellow at 38' names no player, and in 1623421 its Lincoln Red Imps yellow at 90' sits on 527680, the provider's second id for N. Pinto (551172 on every sheet). The fill leaves that team's cards blank, as the Cards rule says, until a card row or the id pair lands.
