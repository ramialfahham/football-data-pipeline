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
-->


{% docs assists %}
Goal assists.
{% enddocs %}


{% docs assists_per90 %}
Goal assists per 90 minutes played. Minutes-normalised. Null when minutes is zero.
{% enddocs %}


{% docs blocks_per90 %}
Blocks per 90 minutes played. Minutes-normalised. Null when minutes is zero.
{% enddocs %}


{% docs blocks_per_match %}
Average shots blocked per match. Aggregated from player stats; inherits player-stat coverage
gaps.
{% enddocs %}


{% docs cards_red %}
Red cards.
{% enddocs %}


{% docs cards_total %}
Yellow plus red cards (total cards shown). A second yellow is recorded by the provider as a
yellow plus a red, so a two-yellow dismissal counts as 3.
{% enddocs %}


{% docs cards_yellow %}
Yellow cards.
{% enddocs %}


{% docs clean_sheets %}
Matches with zero goals conceded, shown as a count of games played (e.g. 3/5).
{% enddocs %}


{% docs contribution_share %}
Goal-involvement share: the player's goals + assists (scorer_points) as a share of the club's
whole-season goals. Involved in X% of the club's goals. Computed in
int_player_profile__contribution (not a single-leg aggregate). Understates where the player's
match stats are missing, because the denominator is the whole season while the numerator counts
only covered appearances. Null when the club scored 0 that competition-season.
{% enddocs %}


{% docs corner_kicks_per_match %}
Average corner kicks won per match with available team stats.
{% enddocs %}


{% docs corners_against_per_match %}
Average corner kicks conceded per match with available opponent stats.
{% enddocs %}


{% docs danger_zone_ratio %}
Share of shots taken from inside the penalty area. Null when shots_total is zero.
{% enddocs %}


{% docs defensive_actions %}
Tackles plus interceptions plus blocks (combined defensive actions).
{% enddocs %}


{% docs defensive_actions_per90 %}
Defensive actions (tackles + interceptions + blocks) per 90 minutes played. Minutes-normalised.
Null when minutes is zero.
{% enddocs %}


{% docs defensive_actions_per_match %}
Average defensive actions per match: tackles + interceptions + blocks. Aggregated from player
stats; inherits player-stat coverage gaps. Displayed with the T/I/B breakdown.
{% enddocs %}


{% docs deserved_points %}
Points the on-target process deserved across the season. Within each league-season, ordinary
least squares fits points-per-match on sot_difference_per_match; this is that fitted rate
multiplied by the team's own games played. Fitted, not an aggregate of match legs, so it
carries no formula. Domestic leagues only - a group-stage tournament's standing is a within-
group position, not a comparable league table. Null when the league-season is not fittable,
meaning some team lacks full shots-on-target coverage, a league rank or 3 finished games; or
the actual table is not a single ladder (MLS conferences, and the Apertura/Clausura formats
where one season spans two separate tournaments whose points reset, so a season points total is
a figure nobody tracks); or the signal has no spread across the league-season (the slope is
then undefined rather than flat).
{% enddocs %}


{% docs deserved_rank %}
Rank of the team within its league-season by deserved_points (descending; 1 = most points
deserved) - the process-deserved table position. Not aggregated from match legs; computed by
ranking the deserved_points metric, so the position and the points total can never disagree.
Domestic leagues only. Null exactly whenever deserved_points is null - the two appear and
disappear together, so a team never shows one without the other.
{% enddocs %}


{% docs dribbles_attempts %}
Dribble attempts.
{% enddocs %}


{% docs dribbles_past %}
Times dribbled past by an opponent.
{% enddocs %}


{% docs dribbles_success %}
Successful dribbles.
{% enddocs %}


{% docs dribbles_success_pct %}
Dribble success rate. Null when dribbles_attempts is zero.
{% enddocs %}


{% docs dribbles_success_per90 %}
Successful dribbles per 90 minutes played. Minutes-normalised. Null when minutes is zero.
{% enddocs %}


{% docs duels_per_match %}
Average duels contested per match. Aggregated from player stats; inherits player-stat coverage
gaps. Volume context for the duel win rate.
{% enddocs %}


{% docs duels_total %}
Total duels contested.
{% enddocs %}


{% docs duels_won %}
Duels won. A duel is any 1v1 physical contest (ground and aerial pooled).
{% enddocs %}


{% docs duels_won_pct__player %}
Duel win rate. Null when duels_total is zero.
{% enddocs %}


{% docs duels_won_pct__team %}
Duel win rate. Null when duels_total is zero. Aggregated from player stats.
{% enddocs %}


{% docs duels_won_per90 %}
Duels won per 90 minutes played. Minutes-normalised. Null when minutes is zero.
{% enddocs %}


{% docs finishing_efficiency__player %}
Open-play goal conversion: open-play goals (goals minus penalties; goals_total already excludes
own goals) per shot on target. In [0, 1] - penalties are excluded because they are not
finishing the player's own on-target shots. Null when not fully shot-covered or outside [0, 1].
{% enddocs %}


{% docs finishing_efficiency__team %}
Open-play goal conversion: open-play goals (goals minus penalties and own goals) per shot on
goal, counted over the same set of games on both sides of the division. In [0, 1] - penalties
and own goals are excluded because they are not finishing the team's own on-target shots. Null
unless shots-on-target data covers every game counted, or the value would fall outside [0, 1].
{% enddocs %}


{% docs goals %}
Goals scored.
{% enddocs %}


{% docs goals_against %}
Goals conceded by the team while the player was on the pitch (GK-relevant).
{% enddocs %}


{% docs goals_against_per_match %}
Average goals conceded per match.
{% enddocs %}


{% docs goals_open_play__player %}
Open-play goals: total goals minus penalties (goals_total - goals_penalty). The numerator of
finishing_efficiency. (goals_total already excludes own goals.)
{% enddocs %}


{% docs goals_open_play__team %}
Open-play goals: the authoritative scoreline minus penalties and own goals (goals_for -
goals_penalty - goals_own). The numerator of finishing_efficiency.
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


{% docs interceptions_per90 %}
Interceptions per 90 minutes played. Minutes-normalised. Null when minutes is zero.
{% enddocs %}


{% docs interceptions_per_match %}
Average interceptions per match. Aggregated from player stats; inherits player-stat coverage
gaps.
{% enddocs %}


{% docs key_passes_per90 %}
Key passes (passes leading to a shot) per 90 minutes played. Minutes-normalised. Null when
minutes is zero.
{% enddocs %}


{% docs key_passes_per_match %}
Average key passes per match. Aggregated from player stats; inherits player-stat coverage gaps.
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


{% docs offsides %}
Offsides caught.
{% enddocs %}


{% docs pass_accuracy %}
Share of passes successfully completed. Null when passes_total is zero.
{% enddocs %}


{% docs pass_accuracy_pct %}
Pass completion rate: accurate passes over attempted, summed rather than averaged, so a heavier
passing game weighs more. Null when passes_total is zero.
{% enddocs %}


{% docs passes_accurate %}
Accurate passes. Derived as SUM(passes_total × passes_accuracy_percent / 100). Inherits small
per-fixture rounding error.
{% enddocs %}


{% docs passes_key %}
Key passes. API definition: a pass leading directly to a shot.
{% enddocs %}


{% docs passes_per90 %}
Passes attempted per 90 minutes played. Minutes-normalised. Null when minutes is zero.
{% enddocs %}


{% docs passes_per_match %}
Average passes attempted per match with available team stats.
{% enddocs %}


{% docs passes_total %}
Total passes attempted.
{% enddocs %}


{% docs penalty_committed %}
Penalties the player conceded. The provider spells the source field `penalty.commited`, which
is misspelled at source and spelled correctly here.
{% enddocs %}


{% docs penalty_won %}
Penalties won.
{% enddocs %}


{% docs points_capture %}
Share of available points won (points / (3 * games)).
{% enddocs %}


{% docs points_won %}
Total points earned: 3 per win, 1 per draw, 0 per loss.
{% enddocs %}


{% docs save_pct %}
Goalkeeper save percentage. Null when denominator is zero.
{% enddocs %}


{% docs save_ratio %}
Share of shots on target faced that were saved. Self-bounding denominator (saves + goals
conceded in save-covered games). Null when no save-covered games.
{% enddocs %}


{% docs saves %}
Saves made.
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


{% docs shot_accuracy %}
Share of shots that were on target. Total shots include blocked shots. Null when shots_total is
zero.
{% enddocs %}


{% docs shot_share %}
Share of all shots in the team's matches taken by the team. Null when no shots.
{% enddocs %}


{% docs shots_on_goal %}
Shots on target.
{% enddocs %}


{% docs shots_on_goal_against %}
Shots on target faced. Derived as saves + goals conceded.
{% enddocs %}


{% docs shots_on_goal_against_per_match %}
Average shots on target conceded per match. The defensive companion to
sot_difference_per_match. Null when opponent shots-on-target data does not cover every season
game.
{% enddocs %}


{% docs shots_on_goal_per90 %}
Shots on target per 90 minutes played. Minutes-normalised. Null when minutes is zero.
{% enddocs %}


{% docs shots_on_goal_per_match %}
Average shots on target per match, counted over the games whose shots-on-target data is present
rather than every game played.
{% enddocs %}


{% docs shots_per_match %}
Average total shots attempted per match with available team stats. Includes on-target, off-
target and blocked shots.
{% enddocs %}


{% docs shots_total %}
Total shots (on and off target).
{% enddocs %}


{% docs sot_difference_per_match %}
Average shots-on-target difference per match (on target for - against). The best non-outcome
predictor of league position; the deserved process signal behind deserved-vs-actual. Null
unless both own and opponent shots-on-target data cover every season game.
{% enddocs %}


{% docs sot_points_gap %}
Points-space deserved-vs-actual gap: actual season points minus deserved_points. NEGATIVE =
under-performing (fewer points than the on-target process deserved); POSITIVE = over-
performing. Note this sign is inverted relative to the retired sot_rank_gap, where positive
meant under-performing. Fitted, not an aggregate of match legs. Because the fit is least
squares within the league-season the gap is a redistribution: it sums to zero across a balanced
season. Domestic leagues only. Null when the league-season is not fittable, meaning some team
lacks full shots-on-target coverage, a league rank or 3 finished games; or the actual table is
not a single ladder (MLS conferences, and the Apertura/Clausura formats where one season spans
two separate tournaments whose points reset, so a season points total is a figure nobody
tracks); or the signal has no spread across the league-season (the slope is then undefined
rather than flat).
{% enddocs %}


{% docs tackles_blocks %}
Shots blocked.
{% enddocs %}


{% docs tackles_interceptions %}
Interceptions.
{% enddocs %}


{% docs tackles_per90 %}
Tackles per 90 minutes played. Minutes-normalised. Null when minutes is zero.
{% enddocs %}


{% docs tackles_per_match %}
Average tackles per match. Aggregated from player stats; inherits player-stat coverage gaps.
{% enddocs %}


{% docs tackles_total %}
Tackles made.
{% enddocs %}
