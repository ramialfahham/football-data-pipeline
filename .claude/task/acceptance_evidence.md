# Verification — researched line-ups, batch 1: Premier League

25 Premier League matches of the 2025-26 and 2026-27 seasons were on the line-up research list.
All 25 are now researched from the official premierleague.com match pages. None was left out.

- **What was missing:** in every match, one substitution named the player who came on but not the
  player replaced (two in Tottenham Hotspur-Liverpool). Everything else on the provider's sheets
  had passed the checks.
- **How each match was checked:** the official line-ups page, read in the built-in browser,
  compared with the provider's sheets for every starter and bench player by shirt number, and
  for every substitution minute. The missing outgoing player is the player of that team the page
  shows going off at that minute; in 25 of the 26 missing substitutions that player had come on
  earlier, so the provider loses the outgoing player mostly when he was a substitute himself.
- **Differences from the provider beyond the missing player:**
  - Leeds United-Sunderland: the provider has Sunderland's substitutions at 55' and 56' the other
    way round; the rows carry the official minutes.
  - The official page marks half-time substitutions at 45', the provider at 46'; the rows keep the
    provider's 46' (the CPO's decision).
  - Wolverhampton-West Ham: the provider's substitution event gives T. Edozie a different player id
    from its team sheet; the rows use the team sheet's id, which the official sheet confirms by
    shirt number.
- **On prod data** (the branch's base_apif__lineups with the new rows, session-only copy):
  - all 25 matches come out researched;
  - assert_lineup_researched_matches_hold, the substitution pairing and the eleven-starters tests
    return no rows;
  - the research list holds no Premier League match of 2025-26 or 2026-27 (995 matches remain
    overall);
  - every researched player is in dim_player.
- **The seed:** 999 rows, no duplicate key, no missing required value, every source official and
  https, one formation per team.
- **Time:** after a one-time setup to read the page structure, each match took one page load and
  one automated comparison, about a minute.
