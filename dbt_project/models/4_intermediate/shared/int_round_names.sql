{#
    int_round_names — every distinct round text of a competition-season named the way the
    competition names it.

    The lower-cased text takes the round_names pattern that matches it: the competition-season's
    own row first (a cup whose early rounds change with each season's format), then the
    competition's own (Veikkausliiga's Mestaruussarja, the Premier League's Matchweek), then the
    general one, each by lowest priority. The row gives the copy key the page names the round by;
    its number and group letter are read from the text with the row's own expressions, and its
    stage kind says whether the round is played for a table, is a final, a third-place match, or
    another round of knockout ties.

    Grain: (league_code, season_api_year, round_name). is_latest_season marks the season the
    competition pages show; assert_every_round_text_resolves fails on a round of that season with
    no name.
#}

with import_fct_fixture as (
    select distinct
        league_code,
        season_api_year,
        round_name
    from {{ ref('fct_fixture') }}
    where round_name is not null
),

import_round_names as (
    select * from {{ ref('round_names') }}
),

latest_seasons as (
    select
        league_code,
        max(season_api_year) as latest_season_api_year
    from import_fct_fixture
    group by league_code
),

matched as (
    select
        rounds.league_code,
        rounds.season_api_year,
        rounds.round_name,
        names.label_i18n_key,
        names.n_regex,
        names.g_regex,
        names.stage_kind
    from import_fct_fixture as rounds
    inner join import_round_names as names
        on
            regexp_contains(lower(trim(rounds.round_name)), names.pattern)
            and (names.league_code is null or rounds.league_code = names.league_code)
            and (names.season_api_year is null or rounds.season_api_year = names.season_api_year)
    qualify row_number() over (
        partition by rounds.league_code, rounds.season_api_year, rounds.round_name
        order by names.season_api_year is null, names.league_code is null, names.priority
    ) = 1
)

select
    rounds.league_code,
    rounds.season_api_year,
    rounds.round_name,
    matched.label_i18n_key as round_label_i18n_key,
    matched.stage_kind as round_stage_kind,
    safe_cast(regexp_extract(lower(trim(rounds.round_name)), matched.n_regex) as int64) as round_number,
    upper(regexp_extract(lower(trim(rounds.round_name)), matched.g_regex)) as round_letter,
    matched.n_regex is not null as needs_number,
    matched.g_regex is not null as needs_letter,
    rounds.season_api_year = latest.latest_season_api_year as is_latest_season
from import_fct_fixture as rounds
inner join latest_seasons as latest
    on rounds.league_code = latest.league_code
left join matched
    on
        rounds.league_code = matched.league_code
        and rounds.season_api_year = matched.season_api_year
        and rounds.round_name = matched.round_name
