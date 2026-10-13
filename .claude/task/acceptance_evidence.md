# Verification — researched line-ups, batch 5: the elite pool and the World Cup

26 current-season matches of the elite pool and the World Cup were on the line-up research list:
La Liga 3, Serie A 3, Ligue 1 5, Liga Portugal 6, Eredivisie 5, World Cup 4. 23 are now researched
from each competition's official match record; three stay out.

- **Sources** (each competition's own site and the data its pages load): laliga.com match pages,
  legaseriea.it line-ups, ligue1.com match sheets, ligaportugal.pt match data, eredivisie.nl match
  data, fifa.com match centre. Each gives both team sheets with the full bench, shirt numbers, the
  formation and every substitution with its minute, the player on and the player off.
- **How each match was checked:** every official player matched to the provider's player by team,
  shirt number and name; 41 matched by shirt only, the provider using another form of the name,
  and every one is confirmed by the provider's full name (e.g. Yusi is Youssef Enríquez, E. Mbondo
  is Emmanuel Alexi Koum Mbondo, Dunga is Nabil Emad). Each match's number of substitutions equals
  the official one.
- **Differences from the provider, the rows following the official record:** 21 substitutions
  without the player replaced, 2 substitutions missing, 33 minutes; five players the provider's
  sheets leave out take the id the provider gives them at their club in 2026 (Kostić, M. L. Ndiaye,
  Simakha and Kamissoko from its squad lists, Jemide from its own Alverca sheet of another match).
- **Formations and pitch positions** are the provider's; New Zealand and Czechia, for whom the
  provider has none, take FIFA's.
- **Left out**, their players having no provider id at the club in 2026: Telstar-ADO Den Haag
  (Álex Pozo), Stade Rennais-AJ Auxerre (Youssef Khoudda), FC Arouca-Moreirense (Rodrigo Soares).
- **On prod data** (the branch's base_apif__lineups with all 171 researched matches, session-only
  copy): every one comes out researched; assert_lineup_researched_matches_hold, the substitution
  pairing and the eleven-starters tests return no rows; of these competitions only the three
  matches above are left on the research list; 851 matches remain overall; every researched
  player is in dim_player.
- **The seed:** 1,056 new rows (7,105 in all), no duplicate key, every source official and https,
  one formation per team; the earlier rows unchanged.
