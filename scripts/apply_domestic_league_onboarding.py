#!/usr/bin/env python3
"""Apply base/sources/registry patches for PL, PD, BL2 onboarding."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

LEAGUES = [
    ("PL", "pl"),
    ("PD", "pd"),
    ("BL2", "bl2"),
]

ENTITIES = [
    ("fixtures_next", "FIXTURES_NEXT"),
    ("leagues", "LEAGUES"),
    ("standings", "STANDINGS"),
    ("rounds", "ROUNDS"),
    ("teams", "TEAMS"),
    ("transfers", "TRANSFERS"),
    ("lineups", "LINEUPS"),
    ("fixture_events", "FIXTURE_EVENTS"),
    ("fixture_statistics", "FIXTURE_STATISTICS"),
    ("fixture_players", "FIXTURE_PLAYERS"),
    ("predictions", "PREDICTIONS"),
    ("players", "PLAYERS"),
]

FRESHNESS = """        loaded_at_field: ingested_at
        freshness:
          warn_after: {count: 30, period: hour}
          error_after: {count: 54, period: hour}"""


def patch_sources() -> None:
    path = REPO / "dbt_project/models/1_staging/api_football/sources.yml"
    text = path.read_text(encoding="utf-8")
    if "raw_apif_pl_fixtures_next" in text:
        print("sources.yml already patched")
        return
    chunks = []
    for code, folder in LEAGUES:
        for ent_slug, bq_suffix in ENTITIES:
            chunks.append(f"      - name: raw_apif_{folder}_{ent_slug}")
            chunks.append(f"        identifier: RAW_APIF_{code}_{bq_suffix}")
            chunks.append(FRESHNESS)
    insert = "\n".join(chunks) + "\n"
    anchor = "      - name: raw_apif_wc_fixtures_next"
    text = text.replace(anchor, insert + anchor, 1)
    path.write_text(text, encoding="utf-8")
    print("patched sources.yml")


def patch_fixtures_next() -> None:
    path = REPO / "dbt_project/models/2_base/api_football/base_apif__fixtures_next.sql"
    text = path.read_text(encoding="utf-8")
    if "stg_apif__pl_fixtures_next" in text:
        return
    anchor = """    select *
    from {{ ref('stg_apif__wcqoc_fixtures_next') }}
    where fixture_id is not null
)"""
    adds = ""
    for _code, folder in LEAGUES:
        adds += f"""
    union all

    select *
    from {{{{ ref('stg_apif__{folder}_fixtures_next') }}}}
    where fixture_id is not null"""
    text = text.replace(anchor, anchor[:-1] + adds + "\n)", 1)
    path.write_text(text, encoding="utf-8")
    print("patched base_apif__fixtures_next.sql")


def patch_list_model(
    rel_path: str,
    list_var: str,
    cte_suffix: str,
    cte_body: str,
) -> None:
    path = REPO / rel_path
    text = path.read_text(encoding="utf-8")
    if any(f"import_stg_{folder}_{cte_suffix}" in text for _code, folder in LEAGUES):
        print(f"{rel_path} already patched")
        return
    text = text.replace(
        "    'import_stg_wcqoc_" + cte_suffix + "',\n]",
        "    'import_stg_wcqoc_" + cte_suffix + "',\n"
        + "".join(f"    'import_stg_{f}_{cte_suffix}',\n" for _c, f in LEAGUES)
        + "]",
        1,
    )
    anchor = "import_stg_wcqoc_" + cte_suffix + " as ("
    pos = text.rfind(anchor)
    if pos < 0:
        raise SystemExit(f"anchor missing in {rel_path}")
    close = text.find("\n),", pos)
    if close < 0:
        raise SystemExit(f"wcqoc CTE close missing in {rel_path}")
    blocks = ",\n\n".join(cte_body.format(folder=folder) for _code, folder in LEAGUES)
    text = text[:close] + "\n),\n\n" + blocks + text[close:]
    path.write_text(text, encoding="utf-8")
    print(f"patched {rel_path}")


STANDINGS_BODY = """import_stg_{folder}_standings as (
    select
        league_code,
        league_api_id,
        league_name,
        season,
        team_id,
        team_name,
        standing_rank,
        points,
        goals_diff,
        form,
        group_description,
        played_all,
        wins_all,
        draws_all,
        losses_all,
        raw_ingested_at
    from {{{{ ref('stg_apif__{folder}_standings') }}}}
    where
        team_id is not null
        and season is not null
)"""

STATS_BODY = """import_stg_{folder}_fixture_statistics as (
    select
        league_code,
        fixture_id,
        team_id,
        shots_on_goal,
        shots_off_goal,
        shots_total,
        shots_blocked,
        shots_inside_box,
        shots_outside_box,
        fouls,
        corner_kicks,
        offsides,
        ball_possession_percent,
        yellow_cards,
        red_cards,
        goalkeeper_saves,
        passes_total,
        passes_accurate,
        passes_accuracy_percent,
        raw_ingested_at
    from {{{{ ref('stg_apif__{folder}_fixture_statistics') }}}}
    where
        fixture_id is not null
        and team_id is not null
)"""

TEAMS_STG_BODY = """    select
        league_code,
        team_id as team_api_id,
        team_name,
        team_code,
        team_country,
        founded_year as team_founded_year,
        team_logo_url,
        venue_id as venue_api_id,
        venue_name,
        venue_address,
        venue_city,
        venue_capacity,
        season,
        raw_ingested_at
    from {{{{ ref('stg_apif__{folder}_teams') }}}}
    where team_id is not null"""

TEAMS_FX_BODY = """    select
        league_code,
        fixture_id,
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,
        raw_ingested_at
    from {{{{ ref('stg_apif__{folder}_fixtures_next') }}}}"""


def patch_leagues_manual() -> None:
    path = REPO / "dbt_project/models/2_base/api_football/base_apif__leagues.sql"
    text = path.read_text(encoding="utf-8")
    if "stg_apif__pl_leagues" in text:
        return
    anchor = """    from {{ ref('stg_apif__wcqoc_leagues') }}
    where league_api_id is not null and season_api_year is not null
),

deduped as ("""
    block = ""
    for _c, folder in LEAGUES:
        block += f"""
    union all

    select
        league_code,
        league_api_id,
        league_name,
        league_type,
        country as league_country,
        league_logo_url,
        country_flag_url,
        season_api_year,
        season_start_date,
        season_end_date,
        season_is_current,
        has_coverage_fixture_events,
        has_coverage_fixture_lineups,
        has_coverage_fixture_statistics,
        has_coverage_fixture_players,
        has_coverage_standings,
        has_coverage_players,
        has_coverage_top_scorers,
        has_coverage_top_assists,
        has_coverage_top_cards,
        has_coverage_injuries,
        has_coverage_predictions,
        has_coverage_odds,
        raw_ingested_at
    from {{{{ ref('stg_apif__{folder}_leagues') }}}}
    where league_api_id is not null and season_api_year is not null"""
    text = text.replace(anchor, block + "\n),\n\ndeduped as (", 1)
    path.write_text(text, encoding="utf-8")
    print("patched base_apif__leagues.sql")


def patch_teams() -> None:
    path = REPO / "dbt_project/models/2_base/api_football/base_apif__teams.sql"
    text = path.read_text(encoding="utf-8")
    if "stg_apif__pl_teams" in text:
        return
    anchor1 = """    from {{ ref('stg_apif__wcqoc_teams') }}
    where team_id is not null

),

stg_fixtures as ("""
    b1 = ""
    for _c, folder in LEAGUES:
        b1 += "\n    union all\n\n" + TEAMS_STG_BODY.format(folder=folder)
    text = text.replace(anchor1, b1 + "\n\n),\n\nstg_fixtures as (", 1)

    anchor2 = """    from {{ ref('stg_apif__wcqoc_fixtures_next') }}
),

team_keys as ("""
    b2 = ""
    for _c, folder in LEAGUES:
        b2 += "\n    union all\n\n" + TEAMS_FX_BODY.format(folder=folder)
    text = text.replace(anchor2, b2 + "\n\n),\n\nteam_keys as (", 1)
    path.write_text(text, encoding="utf-8")
    print("patched base_apif__teams.sql")


def patch_dbt_project_yml() -> None:
    path = REPO / "dbt_project/dbt_project.yml"
    text = path.read_text(encoding="utf-8")
    if "    - PL\n" in text:
        return
    text = text.replace(
        "    - BL1\n    - WC\n",
        "    - BL1\n    - BL2\n    - PD\n    - PL\n    - WC\n",
    )
    path.write_text(text, encoding="utf-8")
    print("patched dbt_project.yml")


def main() -> None:
    patch_sources()
    patch_fixtures_next()
    patch_list_model(
        "dbt_project/models/2_base/api_football/base_apif__standings.sql",
        "standings_union_ctes",
        "standings",
        STANDINGS_BODY,
    )
    patch_list_model(
        "dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql",
        "fixture_statistics_union_ctes",
        "fixture_statistics",
        STATS_BODY,
    )
    patch_leagues_manual()
    patch_teams()
    patch_dbt_project_yml()


if __name__ == "__main__":
    main()
