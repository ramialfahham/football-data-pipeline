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


{% docs contributing_competitions %}
Array of distinct league_codes from which the window legs were drawn.
{% enddocs %}


{% docs draws %}
Draws (all).
{% enddocs %}


{% docs fixture_date %}
Kickoff date (UTC).
{% enddocs %}


{% docs goals_diff %}
Goal difference.
{% enddocs %}


{% docs home_team_sk %}
FK to dim_team for the home side.
{% enddocs %}


{% docs is_starter %}
Derived: minutes_played > 0 AND NOT is_substitute.
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


{% docs opponent_team_sk %}
The other side's team_sk; the row carries the team's perspective of the fixture.
{% enddocs %}


{% docs passes_accuracy_percent %}
Pass accuracy as an integer percent (0-100).
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




{% docs round_order %}
Matchday number parsed from round_name (null if non-numeric). For deferred year-over-year
alignment.
{% enddocs %}


{% docs source_code %}
Provenance (e.g. GEMINI_RESEARCH_V1); null when no estimate loaded.
{% enddocs %}


{% docs standings_group_description %}
API standings row description (e.g. group or stage label) from the same fct_standings row as
latest_rank. Null when standings are absent. The provider may reuse the same label across
different physical groups.
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


{% docs wins %}
Wins (all).
{% enddocs %}


{% docs yoy_appearances_cutoff %}
N = appearances this season; the prior season is compared through its first N appearances.
{% enddocs %}


{% docs yoy_games_played_cutoff %}
N = games played this season; the prior season is compared through its first N games.
{% enddocs %}
