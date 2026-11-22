{% docs cleaning_rules %}
How the provider's match values become the cleaned values every metric reads. Results are exact;
match stats are good enough.

- Fetches. A team's match stat is the newest value any fetch's line carried. A card count from an
  earlier fetch must fit the match's events. It is at least the cards certainly of that colour and
  at most those that could be. A player's values come from the match's picked fetch. A stat it
  leaves blank is the newest value of another fetch with the same results for him. Those results
  are goals, assists, cards, minutes, penalties, saves and goals conceded. Shots and shots on target
  are taken only where the team's player total moves no further from the team line. A result never
  comes from another fetch alone. Another fetch can give a player the goals, assists or cards of the
  match's events where the picked fetch does not. Then the events' count is his. Where the picked
  fetch leaves his minutes blank, another fetch's minutes can stand. A substitution must bring him
  on that many minutes before the 90th, the minute of entry counted or not.

- Blank rule. A blank count is a zero only where the provider counted that stat in the match or a
  second source proves the zero; every other blank stays blank. Counted in the match: for a team,
  the other team's line has a value for it; for a player, another player in the match has one,
  and for a goalkeeper's saves, another goalkeeper. A team's blank offsides count is also a zero
  when its own line has fouls and possession and no player of it has an offside. A team's offsides
  count is never 0 while a player of it has an offside. A 0 the provider sent is then blank. A
  blank that the other team's line or its own full line would zero stays blank. A goalkeeper's
  goals conceded come from the
  match. The only goalkeeper of a whole match has all the team conceded. One who came on or went
  off has those between the minute on and off, read from the substitution or a sending-off. That
  value stays blank unless the events hold every goal and none falls in a change's minute. The
  score proves it: a team
  that scored none means its players scored and assisted none, and a team that conceded none means
  its players conceded none. The match events prove it: every goal listed and none assisted means
  no assists, goals that are all own goals by the opponent mean the team's players scored none, no
  penalty awarded means none won or committed, and no card event means no cards. The team's line
  proves it: 0 shots, shots on target, saves or offsides means its players had none, and an
  opponent with no shot on target means the team made no saves. A player who did something in the
  match keeps a blank minutes figure. Possession is a share, not a count, so a blank possession
  stays blank.
- Results. A team's goals are the score. Its penalty and own goals come from its goal events where
  those add up to its score. A shoot-out kick is no goal event: the provider labels most and files
  the rest at a negative minute. A goal event with no scorer id or name is left out where the goal
  events add up to the score only without such events. Where a match's goal events stay wrong, its
  goals come from sourced research in the fixture_goal_corrections seed. A player's goals come from
  the per-player count or the goal events, whichever adds up to the score.
  A result that fails a result check is withheld until sourced research stands in
  fixture_result_corrections. The match has no score, shoot-out or winner, is not played, and
  counts in no form, record or cup round.
  A goal keeps the newest added minute any fetch carried. Its scorer and assister are on the pitch
  at its minute on the line-up; a goal or substitution at 45', 90', 105' or 120' with no added
  minute can fall in that period's added time. A scorer or assister who fails this is withheld
  until sourced research stands in fixture_goal_corrections; the goal and the score stay.
- Withheld values. A value that fails its check and has no sourced correction yet is left blank,
  as line-ups and cards are. Each withheld result, goal list, scorer, assister, card list and
  line-up team's goals stands on mart_competition_research_list, beside every correction the provider
  no longer needs.
- Cards. A player's yellow and red cards are exact. Where his stat line and the card events
  disagree, or a card's player is not on the sheet, the match's cards come from sourced research.
  Research is not needed where another fetch gives the events' count.
- A player's team. Where his statistics row and his match events, own goals aside, name different
  teams of the match, the squad list for the season decides, and his other matches decide where it
  names both teams or neither; the side it contradicts, his row or his events, moves to the team
  it names. Where nothing decides, both stay where the provider put them. Where a match's line-ups
  are researched, the researched sheet decides a player's team, for his statistics and his events.
- Accurate passes are a count in every match. Where a match's values add up to more than its
  passes, the provider sent a percentage, and it is converted once.
- Positions. A player's position in a match is G, D, M or F. A position given in words takes its
  letter; a winger takes the letter of his row on the line-up grid (first row G, second D, last F,
  the rows between M). Any other code is no position.
- Substitutions. A substitution event names the player who went off and, as its assist, the player
  who came on. Where the line-ups name the assist as a starter and the player as not one, the two
  are swapped.
- Line-ups. A match's team sheets are shown when they pass every check below. Otherwise they are
  shown only when researched from an official source, in fixture_lineup_corrections. A researched
  line-up passes every check but the squad lists, which its official source outranks.
  - Two sheets, each with eleven different starters, every starter with a player id.
  - More of a sheet's players are on its team's squad list than on the other team's, and none is
    listed only at the other team. Without a squad list, the club each player last joined decides.
  - No player is on both sheets, and the stat lines put no player on the other team.
  - No team sheet names two people under one player id; one person listed twice keeps his first
    listing.
  - Every substitution brings on a substitute for a player of the same team on the sheets, at the
    minute that player went off.
  - Research covers, in this order: every match of a domestic league in the registry;
    national-team matches; the matches of that season's clubs of those leagues in other
    competitions. The current season comes first. A match not played has no line-ups to research.
- Contradictions. A match stat that contradicts a result, a stat that passes its own check, or its
  own total is corrected to the nearest value consistent with it when the gap is at most 2. It is
  left blank when the gap is larger or when neither side passes its check. The only goalkeeper of
  a whole match is set to the score at any gap. A result is corrected only to the league's
  official decision, with its source; match stats never correct a result.
- Every correction is listed on its row in stat_corrections, under one of these rules:
  goals_from_events (a player's goals taken from the goal events);
  penalty_goals_limited_to_goals; penalties_scored_matched_to_penalty_goals;
  raised_to_open_play_goals (shots on target or shots raised to the open-play goals);
  raised_to_shots_on_target (shots raised to the shots on target);
  matched_to_team_goals_conceded (a keeper's goals conceded set to the team's);
  limited_to_opponent_shots_on_target (saves lowered to the opponent's shots on target plus the
  penalties it missed); opponent_shots_on_target_unverified (saves above that ceiling left blank,
  because the opponent's figure fails its own check); limited_to_whole (a part lowered to its
  whole); raised_to_part (a whole raised to its part); limited_to_card_maximum (at most two yellow
  cards and one red card); cards_need_research (a match's cards left blank until sourced research
  stands); cards_from_research (a match's cards taken from sourced research); limited_to_team_goals (a player's assists at most the team's goals
  minus the player's own); own_goals_left_out (shots inside the box less the own goals the
  provider counted as the team's shots); split_does_not_add_up (a split of shots that does not add
  up to the total, left blank, shots on target excepted).
- A competition-season whose share of corrected or blanked player values passes its limit has its
  player and team boards withheld.
- A line can be filed under a team that did not play the match. This holds for an event, a player
  line and a statistics line. The line is left out of the facts until a fixture_team_id_overrides
  row files it under the right team.
- A line-up team's player goals that do not add up to its score stay blank until sourced research
  stands.
- A player's card events in one match can name two teams. His cards are then withheld, on a stat
  line and on a line-up row, until sourced research stands in fixture_card_corrections.
- A standings section that resolves to a league table beside group or conference tables is
  withheld until a standings_table_kinds pattern names it.
- A team's country that is missing, or that changed between deliveries, is withheld until a
  team_country_corrections row settles it.
- A player's tied records can hold two real birth dates or two real nationalities. That value is
  withheld until a player_bio_corrections row settles it.
{% enddocs %}

{% docs stat_corrections_cleaned_value %}
The value this model carries; NULL where the stat was left blank.
{% enddocs %}

{% docs stat_corrections_rule %}
The rule that changed it, by its name in this table's description.
{% enddocs %}
