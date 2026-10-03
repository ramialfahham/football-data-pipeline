<!--
GENERATED FILE - DO NOT EDIT BY HAND.

Every block below is produced from dbt_project/seeds/metric_catalogue.csv by
scripts/sync_metric_docs_blocks.py. To change a definition, change the seed's
`description` and regenerate; an edit made here is overwritten and, until it is,
makes the seed and the warehouse disagree about what a metric means.

    python scripts/sync_metric_docs_blocks.py

A metric whose team and player rows define it differently gets one block per
entity, suffixed __team / __player, so no caller has to guess which meaning it is
pointing at.

Blocks are also emitted for DERIVED column names - a metric with one standard
affix on it, such as goals_against_sum_season or duels_won_pct_this_season. Those
are the seed's definition followed by the affix's own sentence, and they exist for
exactly the column names the model YAML contains, so adding a column shaped that
way and forgetting to regenerate fails the drift check in CI.
-->


{% docs assists_per90 %}
Goals the player set up for a teammate per 90 minutes played.
{% enddocs %}


{% docs assists_player %}
Goals the player set up for a teammate.
{% enddocs %}


{% docs assists_player_delta_yoy__player %}
Goals the player set up for a teammate. The change from the previous season to the current one,
compared at the same point of the campaign: the current value minus the previous one.
{% enddocs %}


{% docs assists_player_prev_season__player %}
Goals the player set up for a teammate. Value for the season before, through the same number of
matches as the current season has played so far, so the two are compared at the same point of a
campaign rather than a part season against a full one.
{% enddocs %}


{% docs assists_player_prev_season_full__player %}
Goals the player set up for a teammate. The previous season's complete total, with no cutoff.
It is context for how large that season was and is never subtracted from the season in
progress, because a part season against a full one would mislead.
{% enddocs %}


{% docs assists_player_this_season__player %}
Goals the player set up for a teammate. Value for the season now in progress, accumulated
through the matches played so far.
{% enddocs %}


{% docs blocks_per90 %}
Shots the player blocked per 90 minutes played.
{% enddocs %}


{% docs blocks_per_match %}
Average number of shots the team's players blocked per match.
{% enddocs %}


{% docs blocks_player %}
Shots the player blocked.
{% enddocs %}


{% docs cards_player %}
Yellow and red cards the player received.
{% enddocs %}


{% docs cards_red %}
Red cards the team's players received.
{% enddocs %}


{% docs cards_red_player %}
Red cards the player received.
{% enddocs %}


{% docs cards_yellow %}
Yellow cards the team's players received.
{% enddocs %}


{% docs cards_yellow_player %}
Yellow cards the player received.
{% enddocs %}


{% docs clean_sheets %}
Matches in which the team conceded no goal.
{% enddocs %}


{% docs clean_sheets_pct %}
Matches in which the team conceded no goal, as a share of all its matches.
{% enddocs %}


{% docs clean_sheets_pct_delta_yoy__team %}
Matches in which the team conceded no goal, as a share of all its matches. The change from the
previous season to the current one, compared at the same point of the campaign: the current
value minus the previous one.
{% enddocs %}


{% docs clean_sheets_pct_prev_season__team %}
Matches in which the team conceded no goal, as a share of all its matches. Value for the season
before, through the same number of matches as the current season has played so far, so the two
are compared at the same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs clean_sheets_pct_this_season__team %}
Matches in which the team conceded no goal, as a share of all its matches. Value for the season
now in progress, accumulated through the matches played so far.
{% enddocs %}


{% docs contribution_player_pct %}
The player's goals plus assists as a share of the goals the club scored on the pitch in that
competition season.
{% enddocs %}


{% docs corners %}
Corner kicks the team won.
{% enddocs %}


{% docs corners_against_per_match %}
Average number of corner kicks the team conceded per match.
{% enddocs %}


{% docs corners_against_per_match_delta_yoy__team %}
Average number of corner kicks the team conceded per match. The change from the previous season
to the current one, compared at the same point of the campaign: the current value minus the
previous one.
{% enddocs %}


{% docs corners_against_per_match_prev_season__team %}
Average number of corner kicks the team conceded per match. Value for the season before,
through the same number of matches as the current season has played so far, so the two are
compared at the same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs corners_against_per_match_this_season__team %}
Average number of corner kicks the team conceded per match. Value for the season now in
progress, accumulated through the matches played so far.
{% enddocs %}


{% docs corners_per_match %}
Average number of corner kicks the team won per match.
{% enddocs %}


{% docs corners_per_match_delta_yoy__team %}
Average number of corner kicks the team won per match. The change from the previous season to
the current one, compared at the same point of the campaign: the current value minus the
previous one.
{% enddocs %}


{% docs corners_per_match_prev_season__team %}
Average number of corner kicks the team won per match. Value for the season before, through the
same number of matches as the current season has played so far, so the two are compared at the
same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs corners_per_match_this_season__team %}
Average number of corner kicks the team won per match. Value for the season now in progress,
accumulated through the matches played so far.
{% enddocs %}


{% docs defensive_actions_per90 %}
Tackles, interceptions and blocks the player made per 90 minutes played.
{% enddocs %}


{% docs defensive_actions_per_match %}
Average number of tackles, interceptions and blocks the team's players made per match.
{% enddocs %}


{% docs defensive_actions_per_match_delta_yoy__team %}
Average number of tackles, interceptions and blocks the team's players made per match. The
change from the previous season to the current one, compared at the same point of the campaign:
the current value minus the previous one.
{% enddocs %}


{% docs defensive_actions_per_match_prev_season__team %}
Average number of tackles, interceptions and blocks the team's players made per match. Value
for the season before, through the same number of matches as the current season has played so
far, so the two are compared at the same point of a campaign rather than a part season against
a full one.
{% enddocs %}


{% docs defensive_actions_per_match_this_season__team %}
Average number of tackles, interceptions and blocks the team's players made per match. Value
for the season now in progress, accumulated through the matches played so far.
{% enddocs %}


{% docs defensive_actions_player %}
Tackles, interceptions and blocks the player made.
{% enddocs %}


{% docs defensive_actions_player_delta_yoy__player %}
Tackles, interceptions and blocks the player made. The change from the previous season to the
current one, compared at the same point of the campaign: the current value minus the previous
one.
{% enddocs %}


{% docs defensive_actions_player_prev_season__player %}
Tackles, interceptions and blocks the player made. Value for the season before, through the
same number of matches as the current season has played so far, so the two are compared at the
same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs defensive_actions_player_prev_season_full__player %}
Tackles, interceptions and blocks the player made. The previous season's complete total, with
no cutoff. It is context for how large that season was and is never subtracted from the season
in progress, because a part season against a full one would mislead.
{% enddocs %}


{% docs defensive_actions_player_this_season__player %}
Tackles, interceptions and blocks the player made. Value for the season now in progress,
accumulated through the matches played so far.
{% enddocs %}


{% docs deserved_points %}
Points the team would have won if its points per match followed its shots-on-target difference
per match, as the two relate across its league season.
{% enddocs %}


{% docs deserved_points_gap %}
The points the team won in its played matches minus its deserved points.
{% enddocs %}


{% docs deserved_points_gap_rank %}
The team's position in its league when the teams are ordered by deserved-points gap, the most
negative first.
{% enddocs %}


{% docs deserved_rank %}
The team's position in its league when the teams are ordered by deserved points, most first.
{% enddocs %}


{% docs dribbles_attempts_player %}
Times the player tried to dribble past an opponent.
{% enddocs %}


{% docs dribbles_past_player %}
Times an opponent dribbled past the player.
{% enddocs %}


{% docs dribbles_success_per90 %}
Dribbles in which the player got past an opponent, per 90 minutes played.
{% enddocs %}


{% docs dribbles_success_player %}
Dribbles in which the player got past an opponent.
{% enddocs %}


{% docs dribbles_success_player_pct %}
Dribbles in which the player got past an opponent, as a share of the player's attempts to
dribble past one.
{% enddocs %}


{% docs duels_per_match %}
Average number of one-on-one challenges for the ball, on the ground or in the air, that the
team's players contested per match.
{% enddocs %}


{% docs duels_per_match_delta_yoy__team %}
Average number of one-on-one challenges for the ball, on the ground or in the air, that the
team's players contested per match. The change from the previous season to the current one,
compared at the same point of the campaign: the current value minus the previous one.
{% enddocs %}


{% docs duels_per_match_prev_season__team %}
Average number of one-on-one challenges for the ball, on the ground or in the air, that the
team's players contested per match. Value for the season before, through the same number of
matches as the current season has played so far, so the two are compared at the same point of a
campaign rather than a part season against a full one.
{% enddocs %}


{% docs duels_per_match_this_season__team %}
Average number of one-on-one challenges for the ball, on the ground or in the air, that the
team's players contested per match. Value for the season now in progress, accumulated through
the matches played so far.
{% enddocs %}


{% docs duels_player %}
One-on-one challenges for the ball, on the ground or in the air, that the player contested.
{% enddocs %}


{% docs duels_won_pct %}
One-on-one challenges for the ball, on the ground or in the air, that the team's players won,
as a share of those they contested.
{% enddocs %}


{% docs duels_won_pct_delta_yoy__team %}
One-on-one challenges for the ball, on the ground or in the air, that the team's players won,
as a share of those they contested. The change from the previous season to the current one,
compared at the same point of the campaign: the current value minus the previous one.
{% enddocs %}


{% docs duels_won_pct_prev_season__team %}
One-on-one challenges for the ball, on the ground or in the air, that the team's players won,
as a share of those they contested. Value for the season before, through the same number of
matches as the current season has played so far, so the two are compared at the same point of a
campaign rather than a part season against a full one.
{% enddocs %}


{% docs duels_won_pct_this_season__team %}
One-on-one challenges for the ball, on the ground or in the air, that the team's players won,
as a share of those they contested. Value for the season now in progress, accumulated through
the matches played so far.
{% enddocs %}


{% docs duels_won_per90 %}
One-on-one challenges for the ball, on the ground or in the air, that the player won, per 90
minutes played.
{% enddocs %}


{% docs duels_won_player %}
One-on-one challenges for the ball, on the ground or in the air, that the player won.
{% enddocs %}


{% docs duels_won_player_pct %}
One-on-one challenges for the ball, on the ground or in the air, that the player won, as a
share of those the player contested.
{% enddocs %}


{% docs finishing_efficiency_pct %}
Goals the team scored, not counting penalties and opponents' own goals, as a share of its shots
on target.
{% enddocs %}


{% docs finishing_efficiency_pct_delta_yoy__team %}
Goals the team scored, not counting penalties and opponents' own goals, as a share of its shots
on target. The change from the previous season to the current one, compared at the same point
of the campaign: the current value minus the previous one.
{% enddocs %}


{% docs finishing_efficiency_pct_prev_season__team %}
Goals the team scored, not counting penalties and opponents' own goals, as a share of its shots
on target. Value for the season before, through the same number of matches as the current
season has played so far, so the two are compared at the same point of a campaign rather than a
part season against a full one.
{% enddocs %}


{% docs finishing_efficiency_pct_this_season__team %}
Goals the team scored, not counting penalties and opponents' own goals, as a share of its shots
on target. Value for the season now in progress, accumulated through the matches played so far.
{% enddocs %}


{% docs finishing_efficiency_player_pct %}
Goals the player scored, not counting penalties, as a share of the player's shots on target.
{% enddocs %}


{% docs goals %}
Goals the team scored.
{% enddocs %}


{% docs goals_against %}
Goals the team conceded.
{% enddocs %}


{% docs goals_against_delta_yoy__team %}
Goals the team conceded. The change from the previous season to the current one, compared at
the same point of the campaign: the current value minus the previous one.
{% enddocs %}


{% docs goals_against_per_match %}
Average number of goals the team conceded per match.
{% enddocs %}


{% docs goals_against_per_match_delta_yoy__team %}
Average number of goals the team conceded per match. The change from the previous season to the
current one, compared at the same point of the campaign: the current value minus the previous
one.
{% enddocs %}


{% docs goals_against_per_match_prev_season__team %}
Average number of goals the team conceded per match. Value for the season before, through the
same number of matches as the current season has played so far, so the two are compared at the
same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs goals_against_per_match_this_season__team %}
Average number of goals the team conceded per match. Value for the season now in progress,
accumulated through the matches played so far.
{% enddocs %}


{% docs goals_against_player %}
Goals the team conceded while the player was in goal.
{% enddocs %}


{% docs goals_against_prev_season__team %}
Goals the team conceded. Value for the season before, through the same number of matches as the
current season has played so far, so the two are compared at the same point of a campaign
rather than a part season against a full one.
{% enddocs %}


{% docs goals_against_sum_season__team %}
Goals the team conceded. Totalled over the season.
{% enddocs %}


{% docs goals_against_this_season__team %}
Goals the team conceded. Value for the season now in progress, accumulated through the matches
played so far.
{% enddocs %}


{% docs goals_open_play %}
Goals the team scored, not counting penalties and opponents' own goals.
{% enddocs %}


{% docs goals_open_play_player %}
Goals the player scored, not counting penalties.
{% enddocs %}


{% docs goals_own %}
Own goals by the team's opponents, which count for the team.
{% enddocs %}


{% docs goals_penalty %}
Goals the team scored from penalties, not counting penalty shoot-outs.
{% enddocs %}


{% docs goals_penalty_player %}
Goals the player scored from penalties, not counting penalty shoot-outs.
{% enddocs %}


{% docs goals_per90 %}
Goals the player scored, penalties included and own goals not, per 90 minutes played.
{% enddocs %}


{% docs goals_per_match %}
Average number of goals the team scored per match.
{% enddocs %}


{% docs goals_per_match_delta_yoy__team %}
Average number of goals the team scored per match. The change from the previous season to the
current one, compared at the same point of the campaign: the current value minus the previous
one.
{% enddocs %}


{% docs goals_per_match_prev_season__team %}
Average number of goals the team scored per match. Value for the season before, through the
same number of matches as the current season has played so far, so the two are compared at the
same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs goals_per_match_this_season__team %}
Average number of goals the team scored per match. Value for the season now in progress,
accumulated through the matches played so far.
{% enddocs %}


{% docs goals_player %}
Goals the player scored, penalties included and own goals not.
{% enddocs %}


{% docs goals_player_delta_yoy__player %}
Goals the player scored, penalties included and own goals not. The change from the previous
season to the current one, compared at the same point of the campaign: the current value minus
the previous one.
{% enddocs %}


{% docs goals_player_prev_season__player %}
Goals the player scored, penalties included and own goals not. Value for the season before,
through the same number of matches as the current season has played so far, so the two are
compared at the same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs goals_player_prev_season_full__player %}
Goals the player scored, penalties included and own goals not. The previous season's complete
total, with no cutoff. It is context for how large that season was and is never subtracted from
the season in progress, because a part season against a full one would mislead.
{% enddocs %}


{% docs goals_player_this_season__player %}
Goals the player scored, penalties included and own goals not. Value for the season now in
progress, accumulated through the matches played so far.
{% enddocs %}


{% docs interceptions_per90 %}
Opponents' passes the player intercepted per 90 minutes played.
{% enddocs %}


{% docs interceptions_per_match %}
Average number of opponents' passes the team's players intercepted per match.
{% enddocs %}


{% docs interceptions_player %}
Opponents' passes the player intercepted.
{% enddocs %}


{% docs last_meeting_goals_against__team %}
Goals the team conceded. Taken from the most recent previous meeting between these two teams.
{% enddocs %}


{% docs league_rank %}
The team's position in its league table.
{% enddocs %}


{% docs minutes_per_appearance %}
Average minutes the player was on the pitch per match in which the player played.
{% enddocs %}


{% docs offsides_player %}
Times the player was caught offside.
{% enddocs %}


{% docs passes_accuracy_pct %}
The team's passes that reached a teammate, as a share of all its passes.
{% enddocs %}


{% docs passes_accuracy_pct_delta_yoy__team %}
The team's passes that reached a teammate, as a share of all its passes. The change from the
previous season to the current one, compared at the same point of the campaign: the current
value minus the previous one.
{% enddocs %}


{% docs passes_accuracy_pct_prev_season__team %}
The team's passes that reached a teammate, as a share of all its passes. Value for the season
before, through the same number of matches as the current season has played so far, so the two
are compared at the same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs passes_accuracy_pct_this_season__team %}
The team's passes that reached a teammate, as a share of all its passes. Value for the season
now in progress, accumulated through the matches played so far.
{% enddocs %}


{% docs passes_accuracy_player_pct %}
The player's passes that reached a teammate, as a share of all the player's passes.
{% enddocs %}


{% docs passes_accurate_player %}
The player's passes that reached a teammate.
{% enddocs %}


{% docs passes_key_per90 %}
The player's passes that led directly to a teammate's shot, per 90 minutes played.
{% enddocs %}


{% docs passes_key_per_match %}
Average number of passes per match by the team's players that led directly to a teammate's
shot.
{% enddocs %}


{% docs passes_key_per_match_delta_yoy__team %}
Average number of passes per match by the team's players that led directly to a teammate's
shot. The change from the previous season to the current one, compared at the same point of the
campaign: the current value minus the previous one.
{% enddocs %}


{% docs passes_key_per_match_prev_season__team %}
Average number of passes per match by the team's players that led directly to a teammate's
shot. Value for the season before, through the same number of matches as the current season has
played so far, so the two are compared at the same point of a campaign rather than a part
season against a full one.
{% enddocs %}


{% docs passes_key_per_match_this_season__team %}
Average number of passes per match by the team's players that led directly to a teammate's
shot. Value for the season now in progress, accumulated through the matches played so far.
{% enddocs %}


{% docs passes_key_player %}
The player's passes that led directly to a teammate's shot.
{% enddocs %}


{% docs passes_key_player_delta_yoy__player %}
The player's passes that led directly to a teammate's shot. The change from the previous season
to the current one, compared at the same point of the campaign: the current value minus the
previous one.
{% enddocs %}


{% docs passes_key_player_prev_season__player %}
The player's passes that led directly to a teammate's shot. Value for the season before,
through the same number of matches as the current season has played so far, so the two are
compared at the same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs passes_key_player_prev_season_full__player %}
The player's passes that led directly to a teammate's shot. The previous season's complete
total, with no cutoff. It is context for how large that season was and is never subtracted from
the season in progress, because a part season against a full one would mislead.
{% enddocs %}


{% docs passes_key_player_this_season__player %}
The player's passes that led directly to a teammate's shot. Value for the season now in
progress, accumulated through the matches played so far.
{% enddocs %}


{% docs passes_per90 %}
Passes the player attempted per 90 minutes played.
{% enddocs %}


{% docs passes_per_match %}
Average number of passes the team attempted per match.
{% enddocs %}


{% docs passes_per_match_delta_yoy__team %}
Average number of passes the team attempted per match. The change from the previous season to
the current one, compared at the same point of the campaign: the current value minus the
previous one.
{% enddocs %}


{% docs passes_per_match_prev_season__team %}
Average number of passes the team attempted per match. Value for the season before, through the
same number of matches as the current season has played so far, so the two are compared at the
same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs passes_per_match_this_season__team %}
Average number of passes the team attempted per match. Value for the season now in progress,
accumulated through the matches played so far.
{% enddocs %}


{% docs passes_player %}
Passes the player attempted.
{% enddocs %}


{% docs penalty_committed_player %}
Penalties the player gave away.
{% enddocs %}


{% docs penalty_won_player %}
Penalties awarded for fouls on the player.
{% enddocs %}


{% docs points_capture_pct %}
Points the team won as a share of the 3 points per match it could have won.
{% enddocs %}


{% docs points_won %}
Points the team won: 3 for a win, 1 for a draw, none for a defeat.
{% enddocs %}


{% docs points_won_sum_season__team %}
Points the team won: 3 for a win, 1 for a draw, none for a defeat. Totalled over the season.
{% enddocs %}


{% docs saves %}
Shots on target the team's goalkeepers saved.
{% enddocs %}


{% docs saves_pct %}
The team's saves as a share of its saves plus the goals it conceded, own goals not counted.
{% enddocs %}


{% docs saves_pct_delta_yoy__team %}
The team's saves as a share of its saves plus the goals it conceded, own goals not counted. The
change from the previous season to the current one, compared at the same point of the campaign:
the current value minus the previous one.
{% enddocs %}


{% docs saves_pct_prev_season__team %}
The team's saves as a share of its saves plus the goals it conceded, own goals not counted.
Value for the season before, through the same number of matches as the current season has
played so far, so the two are compared at the same point of a campaign rather than a part
season against a full one.
{% enddocs %}


{% docs saves_pct_this_season__team %}
The team's saves as a share of its saves plus the goals it conceded, own goals not counted.
Value for the season now in progress, accumulated through the matches played so far.
{% enddocs %}


{% docs saves_per90 %}
Shots on target the player saved in goal per 90 minutes played.
{% enddocs %}


{% docs saves_player %}
Shots on target the player saved in goal.
{% enddocs %}


{% docs saves_player_pct %}
The player's saves as a share of the player's saves plus the goals conceded while the player
was in goal.
{% enddocs %}


{% docs scorer_points_per90 %}
The player's goals plus assists per 90 minutes played.
{% enddocs %}


{% docs scorer_points_player %}
The player's goals plus assists.
{% enddocs %}


{% docs shots_inside_box %}
Shots the team took from inside the penalty area.
{% enddocs %}


{% docs shots_inside_box_pct %}
The team's shots from inside the penalty area as a share of all its shots.
{% enddocs %}


{% docs shots_inside_box_pct_delta_yoy__team %}
The team's shots from inside the penalty area as a share of all its shots. The change from the
previous season to the current one, compared at the same point of the campaign: the current
value minus the previous one.
{% enddocs %}


{% docs shots_inside_box_pct_prev_season__team %}
The team's shots from inside the penalty area as a share of all its shots. Value for the season
before, through the same number of matches as the current season has played so far, so the two
are compared at the same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs shots_inside_box_pct_this_season__team %}
The team's shots from inside the penalty area as a share of all its shots. Value for the season
now in progress, accumulated through the matches played so far.
{% enddocs %}


{% docs shots_inside_box_sum_season__team %}
Shots the team took from inside the penalty area. Totalled over the season.
{% enddocs %}


{% docs shots_on_goal_against_per_match %}
Average number of shots on target the team's opponents had per match.
{% enddocs %}


{% docs shots_on_goal_against_player %}
Shots on target the player faced in goal: the player's saves plus the goals conceded while the
player was in goal.
{% enddocs %}


{% docs shots_on_goal_difference_per_match %}
Average per match of the team's shots on target minus its opponents' shots on target.
{% enddocs %}


{% docs shots_on_goal_pct %}
The team's shots on target as a share of all its shots.
{% enddocs %}


{% docs shots_on_goal_per90 %}
Shots on target the player had per 90 minutes played.
{% enddocs %}


{% docs shots_on_goal_per_match %}
Average number of shots on target the team had per match.
{% enddocs %}


{% docs shots_on_goal_per_match_delta_yoy__team %}
Average number of shots on target the team had per match. The change from the previous season
to the current one, compared at the same point of the campaign: the current value minus the
previous one.
{% enddocs %}


{% docs shots_on_goal_per_match_prev_season__team %}
Average number of shots on target the team had per match. Value for the season before, through
the same number of matches as the current season has played so far, so the two are compared at
the same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs shots_on_goal_per_match_this_season__team %}
Average number of shots on target the team had per match. Value for the season now in progress,
accumulated through the matches played so far.
{% enddocs %}


{% docs shots_on_goal_player %}
Shots on target the player had.
{% enddocs %}


{% docs shots_on_goal_player_delta_yoy__player %}
Shots on target the player had. The change from the previous season to the current one,
compared at the same point of the campaign: the current value minus the previous one.
{% enddocs %}


{% docs shots_on_goal_player_prev_season__player %}
Shots on target the player had. Value for the season before, through the same number of matches
as the current season has played so far, so the two are compared at the same point of a
campaign rather than a part season against a full one.
{% enddocs %}


{% docs shots_on_goal_player_prev_season_full__player %}
Shots on target the player had. The previous season's complete total, with no cutoff. It is
context for how large that season was and is never subtracted from the season in progress,
because a part season against a full one would mislead.
{% enddocs %}


{% docs shots_on_goal_player_this_season__player %}
Shots on target the player had. Value for the season now in progress, accumulated through the
matches played so far.
{% enddocs %}


{% docs shots_per_match %}
Average number of shots the team took per match.
{% enddocs %}


{% docs shots_per_match_delta_yoy__team %}
Average number of shots the team took per match. The change from the previous season to the
current one, compared at the same point of the campaign: the current value minus the previous
one.
{% enddocs %}


{% docs shots_per_match_prev_season__team %}
Average number of shots the team took per match. Value for the season before, through the same
number of matches as the current season has played so far, so the two are compared at the same
point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs shots_per_match_this_season__team %}
Average number of shots the team took per match. Value for the season now in progress,
accumulated through the matches played so far.
{% enddocs %}


{% docs shots_player %}
Shots the player took.
{% enddocs %}


{% docs shots_share_pct %}
The team's shots as a share of all shots in its matches.
{% enddocs %}


{% docs tackles_per90 %}
Tackles the player made per 90 minutes played.
{% enddocs %}


{% docs tackles_per_match %}
Average number of tackles the team's players made per match.
{% enddocs %}


{% docs tackles_player %}
Tackles the player made.
{% enddocs %}
