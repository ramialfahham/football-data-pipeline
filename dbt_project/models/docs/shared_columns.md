{% docs league_code %}
The competition a row belongs to, as this pipeline's internal code (`BL1`, `PL`, `PD`, …),
matching `docs/competition_registry.yml`. Slice by this to get one competition's rows; use
`league_name` for anything a reader sees.

It is a discriminator, not a BigQuery partition or cluster key — no model declares either.
{% enddocs %}


{% docs league_code_ingest_provenance %}
Which tracked league's pull surfaced this row, pinned deterministically.

This is ingest provenance, **not** the competition the event belongs to. Transfers are global
player events, so filtering by this and expecting a complete picture of a player's or a club's
moves will silently give a partial answer.
{% enddocs %}


{% docs league_sk %}
Competition identity key: `league_api_id` cast to INT64, globally unique in API-Football.
It is `dim_league`'s own key, and the join key to `dim_league` from anywhere else.
{% enddocs %}


{% docs season_api_year %}
The provider's season year, which is the year the season starts. A 2024/25 season is 2024.
{% enddocs %}


{% docs season_sk %}
Competition-season identity key, built from (`league_api_id`, `season_api_year`), so it identifies
one competition in one season rather than a season on its own. It is
`dim_competition_season`'s own key, and the join key to it from anywhere else.
{% enddocs %}


{% docs team_sk %}
Team identity key: `team_api_id` cast to INT64, globally unique in API-Football. It is
`dim_team`'s own key, and the join key to `dim_team` from anywhere else.
{% enddocs %}


{% docs player_sk %}
Player identity key: `player_api_id` cast to INT64, globally unique in API-Football. It is
`dim_player`'s own key, and the join key to `dim_player` from anywhere else.
{% enddocs %}


{% docs fixture_sk %}
Fixture identity key: `fixture_api_id` cast to INT64, globally unique in API-Football. It is
`fct_fixture`'s own key, and the join key to `fct_fixture` from anywhere else.
{% enddocs %}


{% docs raw_ingested_at %}
UTC timestamp of the raw row this row was derived from. Lineage, not an event time — it records
when the payload was ingested, not when anything happened on a pitch.
{% enddocs %}


<!-- PROMOTED, NOT AUTHORED. Every block below is the sentence these columns already
     carried at the site that had one, moved here verbatim so the name is defined once
     instead of once per model. Nothing was rewritten: `--promote-shared-docs` refuses to
     write unless the text a block resolves to equals the text it replaced.

     ⛔ AND THAT REFUSAL IS NOT ENOUGH ON ITS OWN. It proves the sentence is unchanged
     where it already existed; it says nothing about whether the sentence is TRUE at the
     blank sites the block is then pointed at. SIX names were pulled from this set for
     exactly that reason:
       · `is_home` said "the upcoming fixture" while reaching four models grained on a
         finished one;
       · `opponent_shots_total` said "cumulative" while one of its models holds the
         per-match value;
       · `games_with_opp_stats`, `games_with_player_stats` and
         `goals_against_in_save_games` said "window legs" while reaching a
         season-cumulative model;
       · `result` claimed to come from `int_legs__team_match` while `mart_player_match_log`
         never reads that model and recomputes the value itself.
     ⛔ THE LAST ONE IS THE WARNING. A block that names its SOURCE model makes a claim
     about provenance, and provenance is checkable only in the SQL — reading the sentence
     is not enough, and a sweep that read sentences marked it safe. **Before adding a block
     here, open every model it will reach and read the SQL.** -->


{% docs appearances_prev_full %}
The prior season's TOTAL appearances at this club (full-season reference; >= appearances_prev).
NULL when no prior season.
{% enddocs %}


{% docs as_of_date %}
Snapshot date for market_value_eur; null when no estimate loaded.
{% enddocs %}


{% docs away_team_sk %}
FK to dim_team for the away side.
{% enddocs %}


{% docs ball_possession_percent %}
Ball possession as an integer percent (0-100).
{% enddocs %}


{% docs coach_sk %}
Coach identity key: `coach_api_id` cast to INT64. It is `dim_coach`'s own key, and the join
key to `dim_coach` from anywhere else.
{% enddocs %}


{% docs coach_api_id %}
The provider's own identifier for a coach, unique across API-Football and stable across the
clubs a coach works at, so the same person keeps one id through their career. `coach_sk` is
this value cast to INT64; both are carried so a row can be joined on either.
{% enddocs %}


{% docs contributing_competitions %}
Array of distinct league_codes from which the window legs were drawn.
{% enddocs %}


{% docs draws %}
Draws (all).
{% enddocs %}


{% docs fixture_date %}
Kickoff date (UTC).
{% enddocs %}


{% docs goal_diff %}
Goals scored minus goals conceded across the season's finished matches. Computed from this
pipeline's own match records rather than read from a competition's published table, so it is
the difference over the matches held here rather than the one that table shows.
{% enddocs %}


{% docs fouls_drawn %}
Fouls suffered - the times an opponent fouled this player - from the provider's per-player
match statistics. On a row grained to a team rather than a player it is the total over that
team's players in that match, so it counts only the players the statistics feed covers.
{% enddocs %}


{% docs fouls_committed %}
Fouls committed, from the provider's per-player match statistics. On a row grained to a team
rather than a player it is the total over that team's players in that match, so it counts only
the players the statistics feed covers.
{% enddocs %}


{% docs fouls %}
Fouls this team committed in the match, as the provider's team match statistics report them.
NULL rather than zero when the competition supplies no team statistics for the fixture, so a
NULL means unknown and not a clean afternoon.
{% enddocs %}


{% docs goals_diff %}
Goal difference.
{% enddocs %}


{% docs home_away %}
Which side the team played on in this match: `home` or `away`, never anything else. It follows
the provider's nominal home side, so a match played at a neutral venue still has one team
marked `home`.
{% enddocs %}


{% docs home_team_sk %}
FK to dim_team for the home side.
{% enddocs %}


{% docs is_captain %}
True when the provider recorded this player as captain for the match. NULL where the feed says
nothing, which is not the same as false.
{% enddocs %}


{% docs is_starter %}
Derived: minutes_played > 0 AND NOT is_substitute.
{% enddocs %}


{% docs is_substitute %}
True when the provider listed the player among the substitutes for this match. It is a bench
SELECTION, not an appearance: a substitute who is never brought on is still true here and has
zero minutes, so counting appearances from this column alone overstates them badly.
{% enddocs %}


{% docs kickoff_datetime %}
Full kickoff timestamp.
{% enddocs %}


{% docs last_kickoff_at %}
The player's latest match at this club that competition-season (max kickoff, from
int_player_club_season__metrics); a career-log ordering signal (within-club season order), not
a displayed metric.
{% enddocs %}


{% docs latest_form %}
Recent-form string from fct_standings (e.g. WDLWW). Null when standings are absent for that
season.
{% enddocs %}


{% docs latest_rank %}
Rank from fct_standings for the team's standings row (after deduping multiple fct rows per
team-season). Not unique across teams in the same league-season: qualifiers and tournaments
reuse rank numbers across parallel groups or phases, and the API may repeat the same
group_description label for different groups.
{% enddocs %}


{% docs losses %}
Losses (all).
{% enddocs %}


{% docs minutes_played %}
Minutes the provider credits this player with in the match, from its per-player statistics.
NULL where the competition supplies no player statistics for the fixture, and zero for a named
substitute who was not brought on.
{% enddocs %}


{% docs opponent_team_sk %}
The other side's team_sk; the row carries the team's perspective of the fixture.
{% enddocs %}


{% docs passes_accuracy_percent %}
Pass accuracy as an integer percent (0-100).
{% enddocs %}


{% docs penalty_scored %}
Penalties this player scored in the match, from the provider's per-player statistics. It is
the provider's own count on the player's statistics line, which is a different source from the
match event feed.
{% enddocs %}


{% docs penalty_saved %}
Penalties this player saved in the match, from the provider's per-player statistics. It is the
goalkeeper's side of a penalty - not a penalty this player took and missed.
{% enddocs %}


{% docs penalty_missed %}
Penalties this player took and did not score in the match, from the provider's per-player
statistics.
{% enddocs %}


{% docs player_api_id %}
API-Football player id.
{% enddocs %}


{% docs player_first_name %}
Player first name.
{% enddocs %}


{% docs player_last_name %}
Player last name.
{% enddocs %}




{% docs red_cards %}
Red cards shown to this team in the match, from the provider's team match statistics. It is
the team's own statistics line rather than a sum of its players' cards, and it is NULL rather
than zero when the competition supplies no team statistics for the fixture.
{% enddocs %}


{% docs prompt_version %}
Version of the research prompt or ingest job (e.g. wc_squad_value_v1).
{% enddocs %}


{% docs round_order %}
Matchday number parsed from round_name (null if non-numeric). For deferred year-over-year
alignment.
{% enddocs %}


{% docs shots_outside_box %}
Shots this team took from outside the penalty area, from the provider's team match statistics.
NULL rather than zero when the competition supplies no team statistics for the fixture.
{% enddocs %}


{% docs shots_off_goal %}
Shots by this team that missed the target, from the provider's team match statistics. NULL
rather than zero when the competition supplies no team statistics for the fixture.
{% enddocs %}


{% docs shots_blocked %}
Shots by this team that were blocked before reaching the goal, from the provider's team match
statistics. It counts the team's OWN attempts that an opponent blocked - not blocks this team
made. NULL rather than zero when the competition supplies no team statistics for the fixture.
{% enddocs %}


{% docs shirt_number %}
The number this player wore in this match, from the provider's per-player statistics. It is
recorded per match rather than as a squad registration, so it can differ between matches in
the same season.
{% enddocs %}


{% docs source_code %}
Provenance (e.g. GEMINI_RESEARCH_V1); null when no estimate loaded.
{% enddocs %}


{% docs standings_group_description %}
API standings row description (e.g. group or stage label) from the same fct_standings row as
latest_rank. Null when standings are absent. The provider may reuse the same label across
different physical groups.
{% enddocs %}


{% docs starts %}
Matches this player started - not named among the substitutes, and with recorded playing time.
Counted over the matches the row covers, so a player who changed clubs mid-season has one row
per club at the finest grain and those are re-summed at season grain.
{% enddocs %}


{% docs status_short %}
API-Football short status code.
{% enddocs %}


{% docs team_api_id %}
API-Football team id.
{% enddocs %}


{% docs team_code %}
Short team code (3-4 letters) from API-Football.
{% enddocs %}


{% docs team_goals_season %}
The club's whole-season goals_for (the denominator).
{% enddocs %}


{% docs team_slug %}
The team's permanent, locale-independent URL segment, derived in base_apif__teams_global from
the corrected name. It carries no provider id except in the terminal collision case, the only
place an id appears in any URL. BOTH tests are load-bearing. `unique`: two teams on one slug
means two pages resolving to one path, and in a static build one silently overwrites the other.
`not_null`: the ladder yields NULL rather than invent a stranger URL, so that test IS the
escalation path — it stops the build and names the team for a human to resolve.
{% enddocs %}


{% docs upcoming_fixture_sk %}
The not-yet-played fixture these figures are prepared for. It is a `fixture_sk`, so it joins to
the fixture like any other; it is what makes a row a preview of one specific match rather than
a standing summary of the team or player.
{% enddocs %}


{% docs wins %}
Wins (all).
{% enddocs %}


{% docs yellow_cards %}
Yellow cards shown to this team in the match, from the provider's team match statistics. It is
the team's own statistics line rather than a sum of its players' cards, and it is NULL rather
than zero when the competition supplies no team statistics for the fixture.
{% enddocs %}


{% docs yoy_appearances_cutoff %}
N = appearances this season; the prior season is compared through its first N appearances.
{% enddocs %}


{% docs yoy_games_played_cutoff %}
N = games played this season; the prior season is compared through its first N games.
{% enddocs %}


{% docs fixture_api_id %}
API-Football's numeric id for the fixture, as the provider returns it at `$.fixture.id`.
{% enddocs %}

{% docs league_api_id %}
API-Football's own numeric id for the competition, matching `provider_league_id` in
`docs/competition_registry.yml`. Stable for a given competition across seasons; use
`league_code` to slice by this pipeline's own competition identifier instead.
{% enddocs %}

{% docs team_name__provider %}
The team's name as this endpoint's payload returns it, before the `team_name_overrides`
corrections that `base_apif__teams_global` applies to produce the settled `dim_team.team_name`.
The provider's own label can be short, ambiguous, or a stale sponsor name — for a display-ready
name see `dim_team.team_name` or a mart already joined to it.
{% enddocs %}

{% docs team_season_sk %}
Surrogate key over (team_sk, season_sk): one team's one competition-season. Generated once in
int_team_season__metrics and carried unchanged everywhere else it appears.
{% enddocs %}

{% docs season_games_played__whole_season %}
Finished matches the team played in the season: games_played at the season's final matchday
(the last row of int_team_season__metrics_cumulative for this team-season). Never NULL — a
team-season row exists only once the team has played at least one match.
{% enddocs %}

{% docs stat_coverage_season_games %}
Games this season with a shots-on-target stat line present for the team — the coverage count
the shots-on-target rates are gated on and divide by, instead of games played. At most
season_games_played, and fewer wherever the provider's stat line is missing or the match was
awarded rather than played. Never NULL.
{% enddocs %}

{% docs player_stat_coverage_season_games %}
Games this season with a player-derived team stat line present (at least one player row for the
team that match) — the coverage count the player-derived team rates divide by
(passes_key_per_match, tackles_per_match, interceptions_per_match, blocks_per_match,
defensive_actions_per_match, duels_per_match, duels_won_pct). At most season_games_played.
Never NULL.
{% enddocs %}

{% docs games_with_team_stats__season %}
Games in the season that carry a team statistics line — at most games played, and fewer
wherever a match was awarded (a technical loss or walkover has no stat line and never will) or
the provider sent none. The denominator of the team-feed per-match rates on the same row,
exposed so a rate can be multiplied back out. Never NULL.
{% enddocs %}

{% docs wins_sum_season %}
Matches the team has won this season, counted from the match result. Totalled over the season;
never NULL.
{% enddocs %}

{% docs draws_sum_season %}
Matches the team has drawn this season, counted from the match result. Totalled over the
season; never NULL.
{% enddocs %}

{% docs losses_sum_season %}
Matches the team has lost this season, counted from the match result. Totalled over the season;
never NULL.
{% enddocs %}

{% docs goals_for_sum_season %}
Goals scored by the team, read from the authoritative match scoreline (the score after extra
time where a match went to it) rather than summed from player or event records. Totalled over
the season.
{% enddocs %}

{% docs total_shots_sum_season %}
Total shots the team took, taken from the provider's team match statistics and summed over the
team's finished matches. NULL for the whole season unless that stat is present for every one of
the team's non-awarded matches; the provider not supplying it for one match blanks the season
total rather than understating it.
{% enddocs %}

{% docs opponent_total_shots_sum_season %}
Total shots the team's opponents took, taken from the provider's team match statistics on the
opposing side and summed over the team's finished matches. NULL for the whole season unless
that stat is present for every one of the team's non-awarded matches; the provider not
supplying it for one match blanks the season total rather than understating it.
{% enddocs %}

{% docs shots_on_goal_sum_season %}
Shots on target the team took, taken from the provider's team match statistics and summed over
the team's finished matches. NULL for the whole season unless that stat is present for every
one of the team's non-awarded matches; the provider not supplying it for one match blanks the
season total rather than understating it.
{% enddocs %}

{% docs opponent_corner_kicks_sum_season %}
Corner kicks the team's opponents won, taken from the provider's team match statistics on the
opposing side and summed over the team's finished matches. NULL for the whole season unless
that stat is present for every one of the team's non-awarded matches; the provider not
supplying it for one match blanks the season total rather than understating it.
{% enddocs %}

{% docs passes_accurate_sum_season %}
Accurate passes completed by the team, taken from the provider's team match statistics and
summed over the team's finished matches. NULL for the whole season unless that stat is present
for every one of the team's non-awarded matches; the provider not supplying it for one match
blanks the season total rather than understating it.
{% enddocs %}

{% docs passes_total_sum_season %}
Total passes attempted by the team, taken from the provider's team match statistics and summed
over the team's finished matches. NULL for the whole season unless that stat is present for
every one of the team's non-awarded matches; the provider not supplying it for one match blanks
the season total rather than understating it.
{% enddocs %}

{% docs corner_kicks_sum_season %}
Corner kicks the team won, taken from the provider's team match statistics and summed over the
team's finished matches. NULL for the whole season unless that stat is present for every one of
the team's non-awarded matches.
{% enddocs %}

{% docs goalkeeper_saves_sum_season %}
Saves the team's goalkeeper made, taken from the provider's team match statistics and summed
over the team's finished matches. NULL for the whole season unless that stat is present for
every one of the team's non-awarded matches.
{% enddocs %}

{% docs shots_inside_box_sum_season %}
Shots the team took from inside the penalty area, taken from the provider's team match
statistics and summed over the team's finished matches. NULL for the whole season unless that
stat is present for every one of the team's non-awarded matches.
{% enddocs %}

{% docs season_matchdays_used %}
Count of distinct matchday labels (round_name) among the team's finished matches this season,
from int_legs__team_match. Can differ from season_games_played where more than one of the
team's matches shares a round_name. Never NULL for a team-season with at least one finished
match.
{% enddocs %}

{% docs unbeaten_run %}
The team's current run of consecutive matches without a loss, counting back from its most
recent match this season and stopping at the first loss. Equals matches_in_season if the team
has not lost all season. Never NULL.
{% enddocs %}

{% docs win_run %}
The team's current run of consecutive wins, counting back from its most recent match this
season and stopping at the first non-win (draw or loss). Equals matches_in_season if the team
has won every match this season. Never NULL.
{% enddocs %}

{% docs winless_run %}
The team's current run of consecutive matches without a win, counting back from its most recent
match this season and stopping at the first win. Equals matches_in_season if the team has not
won all season. Never NULL.
{% enddocs %}

{% docs clean_sheet_run %}
The team's current run of consecutive matches without conceding, counting back from its most
recent match this season and stopping at the first match it conceded in. Equals
matches_in_season if the team has not conceded all season. Never NULL.
{% enddocs %}

{% docs scoring_run %}
The team's current run of consecutive matches in which the team scored, counting back from its
most recent match this season and stopping at the first match it failed to score in. Equals
matches_in_season if the team has scored in every match this season. Never NULL.
{% enddocs %}

{% docs played__team_season %}
Finished matches from mart_team_season; NULL when no standings rollup exists for the
team-season.
{% enddocs %}

{% docs points__team_season %}
Points won this season (3 per win, 1 per draw), from mart_team_season. NULL when no standings
rollup exists for the team-season.
{% enddocs %}

{% docs round_name %}
The provider's round label for this match (for example 'Regular Season - 12' or
'Quarter-finals'), carried unchanged from fct_fixture. Free text whose shape varies by
competition, so it reads well and sorts badly — never parsed into a value here.
{% enddocs %}

{% docs competition_type %}
The competition's type (domestic_league, domestic_cup, continental_cup, world_championship, …),
resolved from league_code through the competition_registry seed; joins competition_types.
{% enddocs %}

{% docs entity_type %}
Whether the competition this row belongs to is club or national-team football: `club` or
`national`, resolved from league_code through the competition_registry and competition_types
seeds. Never NULL for a tracked competition, since every active league_code is in the registry
and every registry type maps to one of the two; a NULL would mean the registry does not know
the row's competition, which the not_null tests on the match-leg and form models treat as a
defect rather than a value.
{% enddocs %}

{% docs result %}
The match outcome from this row's team's perspective: W (win), D (draw), or L (loss), compared
from the match's own final scoreline.
{% enddocs %}

{% docs market_value_eur %}
The team's estimated market value in whole EUR as of the row's as_of_date: a point-in-time
estimate carrying a source and a snapshot date, not a transfer fee and not a price. NULL when
no estimate is loaded.
{% enddocs %}

{% docs opponent_corner_kicks__leg %}
Corner kicks won by the opponent in this match, from the provider's team match statistics for
the opposing side — the mirror of the team's own corner_kicks. NULL when the competition
supplies no team statistics for the fixture.
{% enddocs %}

{% docs opponent_shots_on_goal__leg %}
Shots on target by the opponent in this match, from the provider's team match statistics for
the opposing side — the mirror of the team's own shots_on_goal. NULL when the competition
supplies no team statistics for the fixture.
{% enddocs %}

{% docs team_name %}
The team's display name: the provider's value with the team_name_overrides corrections already
applied in base, as dim_team publishes it. Every copy of this column elsewhere carries that
same value for the row's team.
{% enddocs %}

{% docs team_logo_url %}
The team's crest URL as dim_team publishes it, copied unchanged wherever a team is shown. NULL
when no crest is ingested for the team.
{% enddocs %}

{% docs team_country %}
The country the team is registered in, canonicalised and reconciled against dim_country in
base, as dim_team publishes it. NULL when the provider row carried none.
{% enddocs %}

{% docs player_name %}
The player's display name as the provider gives it and dim_player publishes it, copied
unchanged wherever a player is shown.
{% enddocs %}

{% docs player_photo_url %}
The player's photo URL as dim_player publishes it, copied unchanged wherever a player is shown.
NULL when no photo is ingested for the player.
{% enddocs %}

{% docs player_nationality %}
The player's nationality as dim_player publishes it: the provider's string, not a coded value.
NULL when none is ingested for the player.
{% enddocs %}

{% docs player_birth_date %}
The player's birth date as dim_player publishes it, parsed from the provider's birth date
field. NULL when that field was missing or not parseable; age is derived at render time and
never stored.
{% enddocs %}

{% docs opponent_name %}
The opposing team's display name for this row's fixture, denormalised from dim_team via
opponent_team_sk.
{% enddocs %}

{% docs opponent_logo_url %}
The opposing team's crest URL for this row's fixture, denormalised from dim_team via
opponent_team_sk. NULL when the opponent has no crest ingested.
{% enddocs %}

{% docs goals_total__leg %}
Goals this player scored in this match, the provider's own per-player count (statistics
goals.total). Includes penalties scored and excludes own goals, which the provider does not
credit to a player. NULL when the provider's statistics line for this player omitted the goals
object.
{% enddocs %}

{% docs goals_assists__leg %}
Assists this player registered in this match, the provider's own per-player count (statistics
goals.assists), by the provider's own definition of an assist. NULL when the provider's
statistics line for this player omitted the goals object.
{% enddocs %}

{% docs shots_on__leg %}
Shots on target this player took in this match, the provider's own per-player count
(statistics shots.on). NULL when the provider's statistics line for this player omitted the
shots object.
{% enddocs %}

{% docs position_code__leg %}
The player's position for this match, as reported by the provider (e.g. G, D, M, F). Free-form
and kept as the provider sends it, to track codes not yet catalogued; NULL when the provider
supplied none.
{% enddocs %}

{% docs is_home__own_fixture %}
True when team_sk is the home side of this row's own fixture, following the provider's nominal
home/away assignment — a match played at a neutral venue still has one side marked home.
{% enddocs %}

{% docs window_type__season_record %}
Which season this row's cumulative record is drawn from: `season_to_date` for the
competition-season the row belongs to, or `prev_season` where a mart falls back to the previous
season because the team or player has not yet played in this one. The intermediate season
records carry only `season_to_date`.
{% enddocs %}

{% docs appearances__season_to_date %}
Finished matches the player actually played (minutes greater than 0) in this
competition-season, summed across every club the player turned out for that season. A squad
member named but never brought on counts 0 rather than being excluded.
{% enddocs %}

{% docs minutes__season_to_date %}
Total minutes played in this competition-season, summed across every club the player turned out
for that season.
{% enddocs %}

{% docs substitute_appearances %}
Appearances that came off the bench: matches where the player was listed as a substitute and
still recorded minutes greater than 0. Excludes a named substitute never brought on, so
substitute_appearances plus starts accounts for every appearance.
{% enddocs %}
