# Verification — researched line-ups, batch 2: Bundesliga and 2. Bundesliga

34 Bundesliga and 2. Bundesliga matches of 2025-26 and 2026-27 were on the line-up research list.
33 are now researched from the official bundesliga.com pages; one stays out.

- **What was missing:** in 32 matches one substitution named the player who came on but not the
  player replaced; in 2 the player who came on had no id.
- **How each match was checked:** the official line-up page for both starting elevens (by name,
  accents and spelling variants matched by hand) and the formations; the official live ticker for
  every substitution, with its minute, the player on and the player off. Each match's number of
  substitutions equals the ticker's.
- **Left out:** 1. FC Union Berlin-SV Elversberg (2026-27): the incoming M. Gray has no provider id
  that a squad list confirms, so the match stays not available.
- **Differences from the provider, the rows following the ticker:**
  - three pairings: 1. FC Heidenheim-Bayer Leverkusen (two players named Conteh), Karlsruher
    SC-Preußen Münster, SC Paderborn-Eintracht Braunschweig;
  - 1. FC Nürnberg-VfL Wolfsburg: the provider's sheet leaves out A. Ceresoli, who came on for
    Porstner at 81'; the row takes his id from the club's 2026 squad list; the provider's sheet
    also lacked the 90+8' change of Haugen for Zoma that the ticker and the provider's own events
    record;
  - about 15 substitutions one minute off.
  - Half-time substitutions keep the provider's 46'; the ticker stamps them with the break time
    (45' plus the minutes of the break).
- **On prod data** (the branch's base_apif__lineups with all 58 researched matches, session-only
  copy): every one comes out researched; assert_lineup_researched_matches_hold, the substitution
  pairing and the eleven-starters tests return no rows; one Bundesliga match of 2025-26 or
  2026-27 is left on the research list, Union Berlin-Elversberg; 962 matches remain overall; every
  researched player is in dim_player.
- **The seed:** 1,318 new rows (2,317 in all), no duplicate key, no missing required value, every
  source official and https, one formation per team; the Premier League rows unchanged.
