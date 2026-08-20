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
