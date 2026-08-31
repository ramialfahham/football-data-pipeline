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


{% docs assists %}
Goal assists.
{% enddocs %}


{% docs assists_delta_yoy__player %}
Goal assists. The change from the previous season to the current one, compared at the same
point of the campaign: the current value minus the previous one. NULL when there is no prior
season at this club to compare against, which covers a transfer, a first season at this level
and a prior season that was never loaded, and NULL for a competition that carries no
year-on-year comparison at all, such as a cup, a qualifying campaign or an international
tournament.
{% enddocs %}


{% docs assists_per90 %}
Goal assists per 90 minutes played. Minutes-normalised. Null when minutes is zero.
{% enddocs %}


{% docs assists_prev_season__player %}
Goal assists. Value for the season before, through the same number of matches as the current
season has played so far, so the two are compared at the same point of a campaign rather than a
part season against a full one.
{% enddocs %}


{% docs assists_prev_season_full__player %}
Goal assists. The previous season's complete total, with no cutoff. It is context for how large
that season was and is never subtracted from the season in progress, because a part season
against a full one would mislead.
{% enddocs %}


{% docs assists_this_season__player %}
Goal assists. Value for the season now in progress, accumulated through the matches played so
far.
{% enddocs %}


{% docs blocks_per90 %}
Blocks per 90 minutes played. Minutes-normalised. Null when minutes is zero.
{% enddocs %}


{% docs blocks_per_match %}
Average shots blocked per match. Aggregated from player stats; inherits player-stat coverage
gaps.
{% enddocs %}


{% docs blocks_player %}
Shots blocked.
{% enddocs %}


{% docs cards_player %}
Yellow plus red cards (total cards shown). A second yellow is recorded by the provider as a
yellow plus a red, so a two-yellow dismissal counts as 3.
{% enddocs %}


{% docs cards_red_player %}
Red cards.
{% enddocs %}


{% docs cards_yellow_player %}
Yellow cards.
{% enddocs %}


{% docs clean_sheets %}
Matches the team finished without conceding a goal, counted as whole matches. clean_sheets_pct
is the same measurement expressed as a proportion of the matches played.
{% enddocs %}


{% docs clean_sheets_pct %}
The share of matches the team finished without conceding a goal: matches with zero goals
against divided by matches played. clean_sheets is the same measurement expressed as a whole
number of matches.
{% enddocs %}


{% docs clean_sheets_pct_delta_yoy__team %}
The share of matches the team finished without conceding a goal: matches with zero goals
against divided by matches played. clean_sheets is the same measurement expressed as a whole
number of matches. The change from the previous season to the current one, compared at the same
point of the campaign: the current value minus the previous one. NULL when either side is
missing, which covers a competition that carries no year-on-year comparison, a prior season
that was never loaded, and a season whose first matches are not fully stat-covered.
{% enddocs %}


{% docs clean_sheets_pct_prev_season__team %}
The share of matches the team finished without conceding a goal: matches with zero goals
against divided by matches played. clean_sheets is the same measurement expressed as a whole
number of matches. Value for the season before, through the same number of matches as the
current season has played so far, so the two are compared at the same point of a campaign
rather than a part season against a full one.
{% enddocs %}


{% docs clean_sheets_pct_this_season__team %}
The share of matches the team finished without conceding a goal: matches with zero goals
against divided by matches played. clean_sheets is the same measurement expressed as a whole
number of matches. Value for the season now in progress, accumulated through the matches played
so far.
{% enddocs %}


{% docs clean_sheets_sum_season__team %}
Matches the team finished without conceding a goal, counted as whole matches. clean_sheets_pct
is the same measurement expressed as a proportion of the matches played. Totalled over the
season.
{% enddocs %}


{% docs contribution_share %}
Goal-involvement share: the player's goals + assists (scorer_points) as a share of the club's
whole-season goals. Involved in X% of the club's goals. Computed in
int_player_profile__contribution (not a single-leg aggregate). Understates where the player's
match stats are missing, because the denominator is the whole season while the numerator counts
only covered appearances. Null when the club scored 0 that competition-season.
{% enddocs %}


{% docs corners %}
Corner kicks won by the team, taken from the provider's team match statistics rather than from
the scoreline or from player records. The provider does not supply team statistics for every
fixture, so this can be missing, and a total over several fixtures can be understated rather
than null.
{% enddocs %}


{% docs corners_against_per_match %}
Average corner kicks conceded per match with available opponent stats.
{% enddocs %}


{% docs corners_against_per_match_delta_yoy__team %}
Average corner kicks conceded per match with available opponent stats. The change from the
previous season to the current one, compared at the same point of the campaign: the current
value minus the previous one. NULL when either side is missing, which covers a competition that
carries no year-on-year comparison, a prior season that was never loaded, and a season whose
first matches are not fully stat-covered.
{% enddocs %}


{% docs corners_against_per_match_prev_season__team %}
Average corner kicks conceded per match with available opponent stats. Value for the season
before, through the same number of matches as the current season has played so far, so the two
are compared at the same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs corners_against_per_match_this_season__team %}
Average corner kicks conceded per match with available opponent stats. Value for the season now
in progress, accumulated through the matches played so far.
{% enddocs %}


{% docs corners_per_match %}
Average corner kicks won per match with available team stats.
{% enddocs %}


{% docs corners_per_match_delta_yoy__team %}
Average corner kicks won per match with available team stats. The change from the previous
season to the current one, compared at the same point of the campaign: the current value minus
the previous one. NULL when either side is missing, which covers a competition that carries no
year-on-year comparison, a prior season that was never loaded, and a season whose first matches
are not fully stat-covered.
{% enddocs %}


{% docs corners_per_match_prev_season__team %}
Average corner kicks won per match with available team stats. Value for the season before,
through the same number of matches as the current season has played so far, so the two are
compared at the same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs corners_per_match_this_season__team %}
Average corner kicks won per match with available team stats. Value for the season now in
progress, accumulated through the matches played so far.
{% enddocs %}


{% docs defensive_actions_per90 %}
Defensive actions (tackles + interceptions + blocks) per 90 minutes played. Minutes-normalised.
Null when minutes is zero.
{% enddocs %}


{% docs defensive_actions_per_match %}
Average defensive actions per match: tackles + interceptions + blocks. Aggregated from player
stats; inherits player-stat coverage gaps. Displayed with the T/I/B breakdown.
{% enddocs %}


{% docs defensive_actions_per_match_delta_yoy__team %}
Average defensive actions per match: tackles + interceptions + blocks. Aggregated from player
stats; inherits player-stat coverage gaps. Displayed with the T/I/B breakdown. The change from
the previous season to the current one, compared at the same point of the campaign: the current
value minus the previous one. NULL when either side is missing, which covers a competition that
carries no year-on-year comparison, a prior season that was never loaded, and a season whose
first matches are not fully stat-covered.
{% enddocs %}


{% docs defensive_actions_per_match_prev_season__team %}
Average defensive actions per match: tackles + interceptions + blocks. Aggregated from player
stats; inherits player-stat coverage gaps. Displayed with the T/I/B breakdown. Value for the
season before, through the same number of matches as the current season has played so far, so
the two are compared at the same point of a campaign rather than a part season against a full
one.
{% enddocs %}


{% docs defensive_actions_per_match_this_season__team %}
Average defensive actions per match: tackles + interceptions + blocks. Aggregated from player
stats; inherits player-stat coverage gaps. Displayed with the T/I/B breakdown. Value for the
season now in progress, accumulated through the matches played so far.
{% enddocs %}


{% docs defensive_actions_player %}
Tackles plus interceptions plus blocks (combined defensive actions).
{% enddocs %}


{% docs defensive_actions_player_delta_yoy__player %}
Tackles plus interceptions plus blocks (combined defensive actions). The change from the
previous season to the current one, compared at the same point of the campaign: the current
value minus the previous one. NULL when there is no prior season at this club to compare
against, which covers a transfer, a first season at this level and a prior season that was
never loaded, and NULL for a competition that carries no year-on-year comparison at all, such
as a cup, a qualifying campaign or an international tournament.
{% enddocs %}


{% docs defensive_actions_player_prev_season__player %}
Tackles plus interceptions plus blocks (combined defensive actions). Value for the season
before, through the same number of matches as the current season has played so far, so the two
are compared at the same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs defensive_actions_player_prev_season_full__player %}
Tackles plus interceptions plus blocks (combined defensive actions). The previous season's
complete total, with no cutoff. It is context for how large that season was and is never
subtracted from the season in progress, because a part season against a full one would mislead.
{% enddocs %}


{% docs defensive_actions_player_this_season__player %}
Tackles plus interceptions plus blocks (combined defensive actions). Value for the season now
in progress, accumulated through the matches played so far.
{% enddocs %}


{% docs deserved_points %}
Points the on-target process deserved across the season. Within each league-season, ordinary
least squares fits points-per-match on shots_on_goal_difference_per_match; this is that fitted
rate multiplied by the team's own games played. Fitted, not an aggregate of match legs, so it
carries no formula. Domestic leagues only - a group-stage tournament's standing is a
within-group position, not a comparable league table. Null when the league-season is not
fittable, meaning some team lacks full shots-on-target coverage, a league rank or 3 finished
games; or the actual table is not a single ladder (MLS conferences, and the Apertura/Clausura
formats where one season spans two separate tournaments whose points reset, so a season points
total is a figure nobody tracks); or the signal has no spread across the league-season (the
slope is then undefined rather than flat).
{% enddocs %}


{% docs deserved_points_gap %}
Points-space deserved-vs-actual gap: actual season points minus deserved_points. NEGATIVE =
under-performing (fewer points than the on-target process deserved); POSITIVE =
over-performing. Note this sign is inverted relative to the retired sot_rank_gap, where
positive meant under-performing. Fitted, not an aggregate of match legs. Because the fit is
least squares within the league-season the gap is a redistribution: it sums to zero across a
balanced season. Domestic leagues only. Null when the league-season is not fittable, meaning
some team lacks full shots-on-target coverage, a league rank or 3 finished games; or the actual
table is not a single ladder (MLS conferences, and the Apertura/Clausura formats where one
season spans two separate tournaments whose points reset, so a season points total is a figure
nobody tracks); or the signal has no spread across the league-season (the slope is then
undefined rather than flat).
{% enddocs %}


{% docs deserved_rank %}
Rank of the team within its league-season by deserved_points (descending; 1 = most points
deserved) - the process-deserved table position. Not aggregated from match legs; computed by
ranking the deserved_points metric, so the position and the points total can never disagree.
Domestic leagues only. Null exactly whenever deserved_points is null - the two appear and
disappear together, so a team never shows one without the other.
{% enddocs %}


{% docs dribbles_attempts_player %}
Dribble attempts.
{% enddocs %}


{% docs dribbles_past_player %}
Times dribbled past by an opponent.
{% enddocs %}


{% docs dribbles_success_per90 %}
Successful dribbles per 90 minutes played. Minutes-normalised. Null when minutes is zero.
{% enddocs %}


{% docs dribbles_success_player %}
Successful dribbles.
{% enddocs %}


{% docs dribbles_success_player_pct %}
Dribble success rate. Null when dribbles_attempts is zero.
{% enddocs %}


{% docs duels_per_match %}
Average duels contested per match. Aggregated from player stats; inherits player-stat coverage
gaps. Volume context for the duel win rate.
{% enddocs %}


{% docs duels_per_match_delta_yoy__team %}
Average duels contested per match. Aggregated from player stats; inherits player-stat coverage
gaps. Volume context for the duel win rate. The change from the previous season to the current
one, compared at the same point of the campaign: the current value minus the previous one. NULL
when either side is missing, which covers a competition that carries no year-on-year
comparison, a prior season that was never loaded, and a season whose first matches are not
fully stat-covered.
{% enddocs %}


{% docs duels_per_match_prev_season__team %}
Average duels contested per match. Aggregated from player stats; inherits player-stat coverage
gaps. Volume context for the duel win rate. Value for the season before, through the same
number of matches as the current season has played so far, so the two are compared at the same
point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs duels_per_match_this_season__team %}
Average duels contested per match. Aggregated from player stats; inherits player-stat coverage
gaps. Volume context for the duel win rate. Value for the season now in progress, accumulated
through the matches played so far.
{% enddocs %}


{% docs duels_player %}
Total duels contested.
{% enddocs %}


{% docs duels_won_pct %}
Duel win rate. Null when duels_total is zero. Aggregated from player stats.
{% enddocs %}


{% docs duels_won_pct_delta_yoy__team %}
Duel win rate. Null when duels_total is zero. Aggregated from player stats. The change from the
previous season to the current one, compared at the same point of the campaign: the current
value minus the previous one. NULL when either side is missing, which covers a competition that
carries no year-on-year comparison, a prior season that was never loaded, and a season whose
first matches are not fully stat-covered.
{% enddocs %}


{% docs duels_won_pct_prev_season__team %}
Duel win rate. Null when duels_total is zero. Aggregated from player stats. Value for the
season before, through the same number of matches as the current season has played so far, so
the two are compared at the same point of a campaign rather than a part season against a full
one.
{% enddocs %}


{% docs duels_won_pct_this_season__team %}
Duel win rate. Null when duels_total is zero. Aggregated from player stats. Value for the
season now in progress, accumulated through the matches played so far.
{% enddocs %}


{% docs duels_won_per90 %}
Duels won per 90 minutes played. Minutes-normalised. Null when minutes is zero.
{% enddocs %}


{% docs duels_won_player %}
Duels won. A duel is any 1v1 physical contest (ground and aerial pooled).
{% enddocs %}


{% docs duels_won_player_pct %}
Duel win rate. Null when duels_total is zero.
{% enddocs %}


{% docs finishing_efficiency_pct %}
Open-play goal conversion: open-play goals (goals minus penalties and own goals) per shot on
goal, counted over the same set of games on both sides of the division. In [0, 1] - penalties
and own goals are excluded because they are not finishing the team's own on-target shots. Null
unless shots-on-target data covers every game counted, or the value would fall outside [0, 1].
{% enddocs %}


{% docs finishing_efficiency_pct_delta_yoy__team %}
Open-play goal conversion: open-play goals (goals minus penalties and own goals) per shot on
goal, counted over the same set of games on both sides of the division. In [0, 1] - penalties
and own goals are excluded because they are not finishing the team's own on-target shots. Null
unless shots-on-target data covers every game counted, or the value would fall outside [0, 1].
The change from the previous season to the current one, compared at the same point of the
campaign: the current value minus the previous one. NULL when either side is missing, which
covers a competition that carries no year-on-year comparison, a prior season that was never
loaded, and a season whose first matches are not fully stat-covered.
{% enddocs %}


{% docs finishing_efficiency_pct_prev_season__team %}
Open-play goal conversion: open-play goals (goals minus penalties and own goals) per shot on
goal, counted over the same set of games on both sides of the division. In [0, 1] - penalties
and own goals are excluded because they are not finishing the team's own on-target shots. Null
unless shots-on-target data covers every game counted, or the value would fall outside [0, 1].
Value for the season before, through the same number of matches as the current season has
played so far, so the two are compared at the same point of a campaign rather than a part
season against a full one.
{% enddocs %}


{% docs finishing_efficiency_pct_this_season__team %}
Open-play goal conversion: open-play goals (goals minus penalties and own goals) per shot on
goal, counted over the same set of games on both sides of the division. In [0, 1] - penalties
and own goals are excluded because they are not finishing the team's own on-target shots. Null
unless shots-on-target data covers every game counted, or the value would fall outside [0, 1].
Value for the season now in progress, accumulated through the matches played so far.
{% enddocs %}


{% docs finishing_efficiency_player_pct %}
Open-play goal conversion: open-play goals (goals minus penalties; goals_total already excludes
own goals) per shot on target. In [0, 1] - penalties are excluded because they are not
finishing the player's own on-target shots. Null when not fully shot-covered or outside [0, 1].
{% enddocs %}


{% docs goals__player %}
Goals scored.
{% enddocs %}


{% docs goals__team %}
Goals scored by the team, read from the authoritative match scoreline (the score after extra
time where a match went to it) rather than summed from player or event records.
{% enddocs %}


{% docs goals_against__player %}
Goals conceded by the team while the player was on the pitch (GK-relevant).
{% enddocs %}


{% docs goals_against__team %}
Goals conceded by the team, read from the authoritative match scoreline (the score after extra
time where a match went to it) rather than summed from player or event records. Distinct from
the player metric of the same name, which is the provider's count of goals conceded while that
player was on the pitch.
{% enddocs %}


{% docs goals_against_delta_yoy__player %}
Goals conceded by the team while the player was on the pitch (GK-relevant). The change from the
previous season to the current one, compared at the same point of the campaign: the current
value minus the previous one. NULL when there is no prior season at this club to compare
against, which covers a transfer, a first season at this level and a prior season that was
never loaded, and NULL for a competition that carries no year-on-year comparison at all, such
as a cup, a qualifying campaign or an international tournament.
{% enddocs %}


{% docs goals_against_delta_yoy__team %}
Goals conceded by the team, read from the authoritative match scoreline (the score after extra
time where a match went to it) rather than summed from player or event records. Distinct from
the player metric of the same name, which is the provider's count of goals conceded while that
player was on the pitch. The change from the previous season to the current one, compared at
the same point of the campaign: the current value minus the previous one. NULL when either side
is missing, which covers a competition that carries no year-on-year comparison, a prior season
that was never loaded, and a season whose first matches are not fully stat-covered.
{% enddocs %}


{% docs goals_against_per_match %}
Average goals conceded per match.
{% enddocs %}


{% docs goals_against_per_match_delta_yoy__team %}
Average goals conceded per match. The change from the previous season to the current one,
compared at the same point of the campaign: the current value minus the previous one. NULL when
either side is missing, which covers a competition that carries no year-on-year comparison, a
prior season that was never loaded, and a season whose first matches are not fully
stat-covered.
{% enddocs %}


{% docs goals_against_per_match_prev_season__team %}
Average goals conceded per match. Value for the season before, through the same number of
matches as the current season has played so far, so the two are compared at the same point of a
campaign rather than a part season against a full one.
{% enddocs %}


{% docs goals_against_per_match_this_season__team %}
Average goals conceded per match. Value for the season now in progress, accumulated through the
matches played so far.
{% enddocs %}


{% docs goals_against_prev_season__player %}
Goals conceded by the team while the player was on the pitch (GK-relevant). Value for the
season before, through the same number of matches as the current season has played so far, so
the two are compared at the same point of a campaign rather than a part season against a full
one.
{% enddocs %}


{% docs goals_against_prev_season__team %}
Goals conceded by the team, read from the authoritative match scoreline (the score after extra
time where a match went to it) rather than summed from player or event records. Distinct from
the player metric of the same name, which is the provider's count of goals conceded while that
player was on the pitch. Value for the season before, through the same number of matches as the
current season has played so far, so the two are compared at the same point of a campaign
rather than a part season against a full one.
{% enddocs %}


{% docs goals_against_sum_season__player %}
Goals conceded by the team while the player was on the pitch (GK-relevant). Totalled over the
season.
{% enddocs %}


{% docs goals_against_sum_season__team %}
Goals conceded by the team, read from the authoritative match scoreline (the score after extra
time where a match went to it) rather than summed from player or event records. Distinct from
the player metric of the same name, which is the provider's count of goals conceded while that
player was on the pitch. Totalled over the season.
{% enddocs %}


{% docs goals_against_this_season__player %}
Goals conceded by the team while the player was on the pitch (GK-relevant). Value for the
season now in progress, accumulated through the matches played so far.
{% enddocs %}


{% docs goals_against_this_season__team %}
Goals conceded by the team, read from the authoritative match scoreline (the score after extra
time where a match went to it) rather than summed from player or event records. Distinct from
the player metric of the same name, which is the provider's count of goals conceded while that
player was on the pitch. Value for the season now in progress, accumulated through the matches
played so far.
{% enddocs %}


{% docs goals_delta_yoy__player %}
Goals scored. The change from the previous season to the current one, compared at the same
point of the campaign: the current value minus the previous one. NULL when there is no prior
season at this club to compare against, which covers a transfer, a first season at this level
and a prior season that was never loaded, and NULL for a competition that carries no
year-on-year comparison at all, such as a cup, a qualifying campaign or an international
tournament.
{% enddocs %}


{% docs goals_delta_yoy__team %}
Goals scored by the team, read from the authoritative match scoreline (the score after extra
time where a match went to it) rather than summed from player or event records. The change from
the previous season to the current one, compared at the same point of the campaign: the current
value minus the previous one. NULL when either side is missing, which covers a competition that
carries no year-on-year comparison, a prior season that was never loaded, and a season whose
first matches are not fully stat-covered.
{% enddocs %}


{% docs goals_open_play__player %}
Open-play goals: total goals minus penalties (goals_total - goals_penalty). The numerator of
finishing_efficiency_player_pct. (goals_total already excludes own goals.)
{% enddocs %}


{% docs goals_open_play__team %}
Open-play goals: the authoritative scoreline minus penalties and own goals (goals_for -
goals_penalty - goals_own). The numerator of finishing_efficiency_pct.
{% enddocs %}


{% docs goals_own %}
Own goals credited to the team (the opponents' own-goal events in the team's matches), counted
from match events (event_detail = 'Own Goal'). A component of the open-play split.
{% enddocs %}


{% docs goals_penalty__player %}
Goals scored from penalties, counted from match events (event_type = 'Goal', event_detail =
'Penalty'). A component of the open-play split — not the player finishing his own on-target
shots.
{% enddocs %}


{% docs goals_penalty__team %}
Goals scored from penalties, counted from match events (event_type = 'Goal', event_detail =
'Penalty'). A component of the open-play split — not the team finishing its own on-target
shots.
{% enddocs %}


{% docs goals_per90 %}
Goals per 90 minutes played. Minutes-normalised so playing time does not distort the
comparison. Null when minutes is zero.
{% enddocs %}


{% docs goals_per_match %}
Average goals scored per match.
{% enddocs %}


{% docs goals_per_match_delta_yoy__team %}
Average goals scored per match. The change from the previous season to the current one,
compared at the same point of the campaign: the current value minus the previous one. NULL when
either side is missing, which covers a competition that carries no year-on-year comparison, a
prior season that was never loaded, and a season whose first matches are not fully
stat-covered.
{% enddocs %}


{% docs goals_per_match_prev_season__team %}
Average goals scored per match. Value for the season before, through the same number of matches
as the current season has played so far, so the two are compared at the same point of a
campaign rather than a part season against a full one.
{% enddocs %}


{% docs goals_per_match_this_season__team %}
Average goals scored per match. Value for the season now in progress, accumulated through the
matches played so far.
{% enddocs %}


{% docs goals_prev_season__player %}
Goals scored. Value for the season before, through the same number of matches as the current
season has played so far, so the two are compared at the same point of a campaign rather than a
part season against a full one.
{% enddocs %}


{% docs goals_prev_season__team %}
Goals scored by the team, read from the authoritative match scoreline (the score after extra
time where a match went to it) rather than summed from player or event records. Value for the
season before, through the same number of matches as the current season has played so far, so
the two are compared at the same point of a campaign rather than a part season against a full
one.
{% enddocs %}


{% docs goals_prev_season_full__player %}
Goals scored. The previous season's complete total, with no cutoff. It is context for how large
that season was and is never subtracted from the season in progress, because a part season
against a full one would mislead.
{% enddocs %}


{% docs goals_prev_season_full__team %}
Goals scored by the team, read from the authoritative match scoreline (the score after extra
time where a match went to it) rather than summed from player or event records. The previous
season's complete total, with no cutoff. It is context for how large that season was and is
never subtracted from the season in progress, because a part season against a full one would
mislead.
{% enddocs %}


{% docs goals_this_season__player %}
Goals scored. Value for the season now in progress, accumulated through the matches played so
far.
{% enddocs %}


{% docs goals_this_season__team %}
Goals scored by the team, read from the authoritative match scoreline (the score after extra
time where a match went to it) rather than summed from player or event records. Value for the
season now in progress, accumulated through the matches played so far.
{% enddocs %}


{% docs interceptions_per90 %}
Interceptions per 90 minutes played. Minutes-normalised. Null when minutes is zero.
{% enddocs %}


{% docs interceptions_per_match %}
Average interceptions per match. Aggregated from player stats; inherits player-stat coverage
gaps.
{% enddocs %}


{% docs interceptions_player %}
Interceptions.
{% enddocs %}


{% docs last_meeting_goals_against__player %}
Goals conceded by the team while the player was on the pitch (GK-relevant). Taken from the most
recent previous meeting between these two teams.
{% enddocs %}


{% docs last_meeting_goals_against__team %}
Goals conceded by the team, read from the authoritative match scoreline (the score after extra
time where a match went to it) rather than summed from player or event records. Distinct from
the player metric of the same name, which is the provider's count of goals conceded while that
player was on the pitch. Taken from the most recent previous meeting between these two teams.
{% enddocs %}


{% docs league_rank %}
Current league standing. Sourced from standings snapshot; not derived from match legs.
{% enddocs %}


{% docs minutes_per_appearance %}
Average minutes played per appearance (minutes / appearances, where an appearance is a match
the player actually played). A squad-list playing-time read describing role - a regular starter
versus a rotation or impact-sub player - not quality. The mart computes the value inline via
safe_divide; this row registers its meaning.
{% enddocs %}


{% docs offsides_player %}
Offsides caught.
{% enddocs %}


{% docs opponent_shots_inside_box__team %}
Shots the team took from inside the penalty area, taken from the provider's team match
statistics. A component of the team's total shots and the numerator of shots_inside_box_pct.
The provider does not supply team statistics for every fixture, so this can be missing, and a
total over several fixtures can be understated rather than null. Measured for the opposing team
rather than this one.
{% enddocs %}


{% docs passes_accuracy_pct %}
Share of passes successfully completed. Null when passes_total is zero.
{% enddocs %}


{% docs passes_accuracy_pct_delta_yoy__team %}
Share of passes successfully completed. Null when passes_total is zero. The change from the
previous season to the current one, compared at the same point of the campaign: the current
value minus the previous one. NULL when either side is missing, which covers a competition that
carries no year-on-year comparison, a prior season that was never loaded, and a season whose
first matches are not fully stat-covered.
{% enddocs %}


{% docs passes_accuracy_pct_prev_season__team %}
Share of passes successfully completed. Null when passes_total is zero. Value for the season
before, through the same number of matches as the current season has played so far, so the two
are compared at the same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs passes_accuracy_pct_this_season__team %}
Share of passes successfully completed. Null when passes_total is zero. Value for the season
now in progress, accumulated through the matches played so far.
{% enddocs %}


{% docs passes_accuracy_player_pct %}
Pass completion rate: accurate passes over attempted, summed rather than averaged, so a heavier
passing game weighs more. Null when passes_total is zero.
{% enddocs %}


{% docs passes_accurate_player %}
Accurate passes. Derived as SUM(passes_total × passes_accuracy_percent / 100). Inherits small
per-fixture rounding error.
{% enddocs %}


{% docs passes_key_per90 %}
Key passes (passes leading to a shot) per 90 minutes played. Minutes-normalised. Null when
minutes is zero.
{% enddocs %}


{% docs passes_key_per_match %}
Average key passes per match. Aggregated from player stats; inherits player-stat coverage gaps.
{% enddocs %}


{% docs passes_key_per_match_delta_yoy__team %}
Average key passes per match. Aggregated from player stats; inherits player-stat coverage gaps.
The change from the previous season to the current one, compared at the same point of the
campaign: the current value minus the previous one. NULL when either side is missing, which
covers a competition that carries no year-on-year comparison, a prior season that was never
loaded, and a season whose first matches are not fully stat-covered.
{% enddocs %}


{% docs passes_key_per_match_prev_season__team %}
Average key passes per match. Aggregated from player stats; inherits player-stat coverage gaps.
Value for the season before, through the same number of matches as the current season has
played so far, so the two are compared at the same point of a campaign rather than a part
season against a full one.
{% enddocs %}


{% docs passes_key_per_match_this_season__team %}
Average key passes per match. Aggregated from player stats; inherits player-stat coverage gaps.
Value for the season now in progress, accumulated through the matches played so far.
{% enddocs %}


{% docs passes_key_player %}
Key passes. API definition: a pass leading directly to a shot.
{% enddocs %}


{% docs passes_key_player_delta_yoy__player %}
Key passes. API definition: a pass leading directly to a shot. The change from the previous
season to the current one, compared at the same point of the campaign: the current value minus
the previous one. NULL when there is no prior season at this club to compare against, which
covers a transfer, a first season at this level and a prior season that was never loaded, and
NULL for a competition that carries no year-on-year comparison at all, such as a cup, a
qualifying campaign or an international tournament.
{% enddocs %}


{% docs passes_key_player_prev_season__player %}
Key passes. API definition: a pass leading directly to a shot. Value for the season before,
through the same number of matches as the current season has played so far, so the two are
compared at the same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs passes_key_player_prev_season_full__player %}
Key passes. API definition: a pass leading directly to a shot. The previous season's complete
total, with no cutoff. It is context for how large that season was and is never subtracted from
the season in progress, because a part season against a full one would mislead.
{% enddocs %}


{% docs passes_key_player_this_season__player %}
Key passes. API definition: a pass leading directly to a shot. Value for the season now in
progress, accumulated through the matches played so far.
{% enddocs %}


{% docs passes_per90 %}
Passes attempted per 90 minutes played. Minutes-normalised. Null when minutes is zero.
{% enddocs %}


{% docs passes_per_match %}
Average passes attempted per match with available team stats.
{% enddocs %}


{% docs passes_per_match_delta_yoy__team %}
Average passes attempted per match with available team stats. The change from the previous
season to the current one, compared at the same point of the campaign: the current value minus
the previous one. NULL when either side is missing, which covers a competition that carries no
year-on-year comparison, a prior season that was never loaded, and a season whose first matches
are not fully stat-covered.
{% enddocs %}


{% docs passes_per_match_prev_season__team %}
Average passes attempted per match with available team stats. Value for the season before,
through the same number of matches as the current season has played so far, so the two are
compared at the same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs passes_per_match_this_season__team %}
Average passes attempted per match with available team stats. Value for the season now in
progress, accumulated through the matches played so far.
{% enddocs %}


{% docs passes_player %}
Total passes attempted.
{% enddocs %}


{% docs penalty_committed_player %}
Penalties the player conceded. The provider spells the source field `penalty.commited`, which
is misspelled at source and spelled correctly here.
{% enddocs %}


{% docs penalty_won %}
Penalties won.
{% enddocs %}


{% docs points_capture_pct %}
Share of available points won (points / (3 * games)).
{% enddocs %}


{% docs points_won %}
Total points earned: 3 per win, 1 per draw, 0 per loss.
{% enddocs %}


{% docs points_won_sum_season__team %}
Total points earned: 3 per win, 1 per draw, 0 per loss. Totalled over the season.
{% enddocs %}


{% docs save_pct %}
Goalkeeper save percentage. Null when denominator is zero.
{% enddocs %}


{% docs saves__player %}
Saves made.
{% enddocs %}


{% docs saves__team %}
Saves made by the team's goalkeepers, taken from the provider's team-statistics line rather
than summed from the individual goalkeepers' counts; the two need not agree. The provider does
not supply team statistics for every fixture, so this can be missing, and a total over several
fixtures can be understated rather than null.
{% enddocs %}


{% docs saves_pct %}
Share of shots on target faced that were saved. Self-bounding denominator (saves + goals
conceded in save-covered games). Null when no save-covered games.
{% enddocs %}


{% docs saves_pct_delta_yoy__team %}
Share of shots on target faced that were saved. Self-bounding denominator (saves + goals
conceded in save-covered games). Null when no save-covered games. The change from the previous
season to the current one, compared at the same point of the campaign: the current value minus
the previous one. NULL when either side is missing, which covers a competition that carries no
year-on-year comparison, a prior season that was never loaded, and a season whose first matches
are not fully stat-covered.
{% enddocs %}


{% docs saves_pct_prev_season__team %}
Share of shots on target faced that were saved. Self-bounding denominator (saves + goals
conceded in save-covered games). Null when no save-covered games. Value for the season before,
through the same number of matches as the current season has played so far, so the two are
compared at the same point of a campaign rather than a part season against a full one.
{% enddocs %}


{% docs saves_pct_this_season__team %}
Share of shots on target faced that were saved. Self-bounding denominator (saves + goals
conceded in save-covered games). Null when no save-covered games. Value for the season now in
progress, accumulated through the matches played so far.
{% enddocs %}


{% docs saves_per90 %}
Goalkeeper saves per 90 minutes played. Minutes-normalised. Null when minutes is zero.
{% enddocs %}


{% docs scorer_points %}
Goals plus assists (combined goal contributions).
{% enddocs %}


{% docs scorer_points_per90 %}
Goals plus assists per 90 minutes played. Minutes-normalised. Null when minutes is zero.
{% enddocs %}


{% docs shots_inside_box %}
Shots the team took from inside the penalty area, taken from the provider's team match
statistics. A component of the team's total shots and the numerator of shots_inside_box_pct.
The provider does not supply team statistics for every fixture, so this can be missing, and a
total over several fixtures can be understated rather than null.
{% enddocs %}


{% docs shots_inside_box_pct %}
Share of shots taken from inside the penalty area. Null when shots_total is zero.
{% enddocs %}


{% docs shots_inside_box_pct_delta_yoy__team %}
Share of shots taken from inside the penalty area. Null when shots_total is zero. The change
from the previous season to the current one, compared at the same point of the campaign: the
current value minus the previous one. NULL when either side is missing, which covers a
competition that carries no year-on-year comparison, a prior season that was never loaded, and
a season whose first matches are not fully stat-covered.
{% enddocs %}


{% docs shots_inside_box_pct_prev_season__team %}
Share of shots taken from inside the penalty area. Null when shots_total is zero. Value for the
season before, through the same number of matches as the current season has played so far, so
the two are compared at the same point of a campaign rather than a part season against a full
one.
{% enddocs %}


{% docs shots_inside_box_pct_this_season__team %}
Share of shots taken from inside the penalty area. Null when shots_total is zero. Value for the
season now in progress, accumulated through the matches played so far.
{% enddocs %}


{% docs shots_inside_box_sum_season__team %}
Shots the team took from inside the penalty area, taken from the provider's team match
statistics. A component of the team's total shots and the numerator of shots_inside_box_pct.
The provider does not supply team statistics for every fixture, so this can be missing, and a
total over several fixtures can be understated rather than null. Totalled over the season.
{% enddocs %}


{% docs shots_on_goal_against %}
Shots on target faced. Derived as saves + goals conceded.
{% enddocs %}


{% docs shots_on_goal_against_per_match %}
Average shots on target conceded per match. The defensive companion to
shots_on_goal_difference_per_match. Null when opponent shots-on-target data does not cover
every season game.
{% enddocs %}


{% docs shots_on_goal_difference_per_match %}
Average shots-on-target difference per match (on target for - against). The best non-outcome
predictor of league position; the deserved process signal behind deserved-vs-actual. Null
unless both own and opponent shots-on-target data cover every season game.
{% enddocs %}


{% docs shots_on_goal_pct %}
Share of shots that were on target. Total shots include blocked shots. Null when shots_total is
zero.
{% enddocs %}


{% docs shots_on_goal_per90 %}
Shots on target per 90 minutes played. Minutes-normalised. Null when minutes is zero.
{% enddocs %}


{% docs shots_on_goal_per_match %}
Average shots on target per match, counted over the games whose shots-on-target data is present
rather than every game played.
{% enddocs %}


{% docs shots_on_goal_per_match_delta_yoy__team %}
Average shots on target per match, counted over the games whose shots-on-target data is present
rather than every game played. The change from the previous season to the current one, compared
at the same point of the campaign: the current value minus the previous one. NULL when either
side is missing, which covers a competition that carries no year-on-year comparison, a prior
season that was never loaded, and a season whose first matches are not fully stat-covered.
{% enddocs %}


{% docs shots_on_goal_per_match_prev_season__team %}
Average shots on target per match, counted over the games whose shots-on-target data is present
rather than every game played. Value for the season before, through the same number of matches
as the current season has played so far, so the two are compared at the same point of a
campaign rather than a part season against a full one.
{% enddocs %}


{% docs shots_on_goal_per_match_this_season__team %}
Average shots on target per match, counted over the games whose shots-on-target data is present
rather than every game played. Value for the season now in progress, accumulated through the
matches played so far.
{% enddocs %}


{% docs shots_on_goal_player %}
Shots on target.
{% enddocs %}


{% docs shots_on_goal_player_delta_yoy__player %}
Shots on target. The change from the previous season to the current one, compared at the same
point of the campaign: the current value minus the previous one. NULL when there is no prior
season at this club to compare against, which covers a transfer, a first season at this level
and a prior season that was never loaded, and NULL for a competition that carries no
year-on-year comparison at all, such as a cup, a qualifying campaign or an international
tournament.
{% enddocs %}


{% docs shots_on_goal_player_prev_season__player %}
Shots on target. Value for the season before, through the same number of matches as the current
season has played so far, so the two are compared at the same point of a campaign rather than a
part season against a full one.
{% enddocs %}


{% docs shots_on_goal_player_prev_season_full__player %}
Shots on target. The previous season's complete total, with no cutoff. It is context for how
large that season was and is never subtracted from the season in progress, because a part
season against a full one would mislead.
{% enddocs %}


{% docs shots_on_goal_player_this_season__player %}
Shots on target. Value for the season now in progress, accumulated through the matches played
so far.
{% enddocs %}


{% docs shots_per_match %}
Average total shots attempted per match with available team stats. Includes on-target,
off-target and blocked shots.
{% enddocs %}


{% docs shots_per_match_delta_yoy__team %}
Average total shots attempted per match with available team stats. Includes on-target,
off-target and blocked shots. The change from the previous season to the current one, compared
at the same point of the campaign: the current value minus the previous one. NULL when either
side is missing, which covers a competition that carries no year-on-year comparison, a prior
season that was never loaded, and a season whose first matches are not fully stat-covered.
{% enddocs %}


{% docs shots_per_match_prev_season__team %}
Average total shots attempted per match with available team stats. Includes on-target,
off-target and blocked shots. Value for the season before, through the same number of matches
as the current season has played so far, so the two are compared at the same point of a
campaign rather than a part season against a full one.
{% enddocs %}


{% docs shots_per_match_this_season__team %}
Average total shots attempted per match with available team stats. Includes on-target,
off-target and blocked shots. Value for the season now in progress, accumulated through the
matches played so far.
{% enddocs %}


{% docs shots_player %}
Total shots (on and off target).
{% enddocs %}


{% docs shots_share_pct %}
Share of all shots in the team's matches taken by the team. Null when no shots.
{% enddocs %}


{% docs tackles_per90 %}
Tackles per 90 minutes played. Minutes-normalised. Null when minutes is zero.
{% enddocs %}


{% docs tackles_per_match %}
Average tackles per match. Aggregated from player stats; inherits player-stat coverage gaps.
{% enddocs %}


{% docs tackles_player %}
Tackles made.
{% enddocs %}
