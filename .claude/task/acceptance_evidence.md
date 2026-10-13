# Verification — researched line-ups, batch 3: MLS

66 MLS matches of 2025 and 2026 were on the line-up research list. 64 are now researched from the
league's official match data, the data the mlssoccer.com line-up and match feed pages show; two
stay out.

- **What was wrong at the provider:** in 52 matches a substitution named the player who came on
  but not the player replaced (53 substitutions); in 11 playoff matches each team's sheet was filed
  under the other team; 2 substitutions were missing from the sheets entirely; in 2 matches a
  player was on no squad list of his club, and the official sheets confirm the provider's.
- **How each match was checked:** the official data's two sheets, starters and bench with shirt
  numbers, and every substitution with its minute, the player on and the player off. Each official
  player was matched to the provider's player by team, shirt number and name; six matched by shirt
  only, the provider using another form of the name, and five of those are confirmed by the
  provider's full names (Zanka is Mathias Jørgensen, Pedrinho is Pedro Martins, N. Mercau is
  Nicolás Fernández Mercau, D. D'Avilla is Dje D'Avilla, Casemiro is Carlos Casimiro); A. Gomez,
  Orlando's #3, is the starter in the official Adrián Marín's place and shirt, whose full surname is
  Marín Gómez. Each match's number of substitutions equals the official one.
- **Differences from the provider, the rows following the official data:**
  - two matches with substitutions paired differently: New England-D.C. United, Atlanta-Sporting
    Kansas City;
  - 17 substitutions a minute or two off;
  - St. Louis-LA Galaxy (2026): J. Klauss, whom the provider's sheet leaves out, came on for
    Furuhashi at 11'; the row takes his id from the club's 2026 squad list;
  - D.C. United-Philadelphia (2025): the provider's bench also lists J. Hopkins, whom the official
    sheet does not name; he has no row.
  - Half-time substitutions keep the provider's 46', and the one substitution in the break before
    extra time (Vancouver-LAFC) its 91': the official data gives them no minute.
  - Formations and pitch positions are the provider's.
- **Left out:**
  - New York Red Bulls-San Diego (2026): D. Mimbang and Pedrinho Castro are on no provider squad
    list of their clubs in 2026.
  - Austin-LAFC (2025 playoffs): the provider's statistics put I. Sánchez, who started for Austin,
    under LAFC; the fix is #213.
- **On prod data** (the branch's base_apif__lineups with all 122 researched matches, session-only
  copy): every one comes out researched; assert_lineup_researched_matches_hold, the substitution
  pairing and the eleven-starters tests return no rows; the two MLS matches above are left on the
  research list; 898 matches remain overall; every researched player is in dim_player.
- **The seed:** 2,547 new rows (4,864 in all), no duplicate key, every source official and https,
  one formation per team; the earlier rows unchanged.
