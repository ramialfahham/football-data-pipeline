{% docs cleaning_rules %}
How the provider's match values become the cleaned values every metric reads. Results are exact;
match stats are good enough.

- Blank rule. A blank count is a zero only where the provider counted that stat in the match or a
  second source proves the zero; every other blank stays blank. Counted in the match: for a team,
  the other team's line has a value for it; for a player, another player in the match has one,
  and for a goalkeeper's saves and goals conceded, another goalkeeper. The score proves it: a team
  that scored none means its players scored and assisted none, and a team that conceded none means
  its players conceded none. The match events prove it: every goal listed and none assisted means
  no assists, goals that are all own goals by the opponent mean the team's players scored none, no
  penalty awarded means none won or committed, and no card event means no cards. The team's line
  proves it: 0 shots, shots on target, saves or offsides means its players had none, and an
  opponent with no shot on target means the team made no saves. A player who did something in the
  match keeps a blank minutes figure. Possession is a share, not a count, so a blank possession
  stays blank.
- Results. A team's goals are the score. Its penalty and own goals come from its goal events where
  those add up to its score, penalty shoot-outs left out. A player's goals come from the per-player
  count or the goal events, whichever adds up to the score.
- A player's team. Where his statistics row and his match events, own goals aside, name different
  teams of the match, the squad list for the season decides, and his other matches decide where it
  names both teams or neither; the side it contradicts, his row or his events, moves to the team
  it names. Where nothing decides, both stay where the provider put them.
- Accurate passes are a count in every match. Where a match's values add up to more than its
  passes, the provider sent a percentage, and it is converted once.
- Contradictions. A match stat that contradicts a result, a stat that passes its own check, or its
  own total is corrected to the nearest value consistent with it when the gap is at most 2. It is
  left blank when the gap is larger or when neither side passes its check. Results are never
  corrected.
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
  cards and one red card); limited_to_team_goals (a player's assists at most the team's goals
  minus the player's own); own_goals_left_out (shots inside the box less the own goals the
  provider counted as the team's shots); split_does_not_add_up (a split of shots that does not add
  up to the total, left blank, shots on target excepted).
- A test fails the build when a competition-season's share of corrected or blanked values passes
  its limit.
{% enddocs %}

{% docs stat_corrections_cleaned_value %}
The value this model carries; NULL where the stat was left blank.
{% enddocs %}

{% docs stat_corrections_rule %}
The rule that changed it, by its name in this table's description.
{% enddocs %}
