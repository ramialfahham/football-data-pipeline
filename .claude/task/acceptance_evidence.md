# Verification — researched line-ups, batch 4: Argentina's Liga Profesional

26 Liga Profesional matches of the 2026 season were on the line-up research list: 25 with a
substitution the provider could not pair, one with a sheet lacking eleven identified starters. All
26 are now researched from the league's official match sheet on ligaprofesional.ar.

- **How each match was checked:** the official sheet's two team sheets give the starting elevens
  and every substitute who came on, with shirt numbers; its commentary gives every substitution
  with its minute, the player on and the player off. Each official player was matched to the
  provider's player by team, shirt number and surname. Each match's number of substitutions equals
  the official one, and every starting eleven equals the provider's but for the goalkeeper the
  provider holds no id for in River Plate-Estudiantes de Río Cuarto.
- **Names checked against the provider's full names**, the provider using another form: O. Gill is
  Orlando Gill, N. Tripichio is Nicolás Tripichio, S. Rosané is Siro Cabral Rosané, L. Gianetti is
  Lautaro Giannetti, J. Mattar is Jerónimo Gómez Mattar, B. Gallego is Baltasar Gallego Rodríguez.
  J. Freitas wears 35 on the official sheet and 44 at the provider; the row carries 35.
- **Differences from the provider, the rows following the official sheet:**
  - 22 matches lacked the player replaced in one substitution;
  - River Plate-Estudiantes de Río Cuarto: the provider's sheet has no id for the starting
    goalkeeper, Lautaro Herrera, who takes the id of the provider's 2026 squad list of his club;
  - Central Córdoba-Estudiantes de La Plata: the provider's sheet leaves out Tiziano Ramírez, who
    came on for Vera at 67'; he takes the id the provider gives him on its own Deportivo
    Riestra-Central Córdoba sheet of the same season;
  - Deportivo Riestra-Central Córdoba: the provider's sheet lacks Ramírez's substitution at 74';
  - one pairing (Vélez-Platense) and six minutes, two of them on substitutions whose outgoing
    player the provider also lacked.
  - Half-time substitutions keep the provider's 46', and those in the breaks of extra time the
    provider's 91' and 106': the official sheet stamps them with the minute before the break.
  - Formations, pitch positions and unused substitutes are the provider's: the official sheet
    shows none.
- **On prod data** (the branch's base_apif__lineups with all 148 researched matches, session-only
  copy): every one comes out researched; assert_lineup_researched_matches_hold, the substitution
  pairing and the eleven-starters tests return no rows; no Liga Profesional match of 2026 is left
  on the research list; 874 matches remain overall; every researched player is in dim_player.
- **The seed:** 1,185 new rows (6,049 in all), no duplicate key, every source official and https,
  one formation per team; the earlier rows unchanged.
