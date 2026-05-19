#!/usr/bin/env python3
"""Append domestic leagues to sources/base after an initial PL/PD/BL2 onboarding."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Set per run; each tuple is (league_code, staging folder).
LEAGUES = [
    ("VL", "vl"),
]

# Last domestic league already in base unions (anchor for append patches).
ANCHOR_FOLDER = "l1"

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

LEAGUES_UNION = """
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

FIXTURES_UNION = """
    union all

    select *
    from {{{{ ref('stg_apif__{folder}_fixtures_next') }}}}
    where fixture_id is not null"""

TEAMS_FX_UNION = """
    union all

    select
        league_code,
        fixture_id,
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,
        raw_ingested_at
    from {{{{ ref('stg_apif__{folder}_fixtures_next') }}}}"""


def patch_sources() -> None:
    path = REPO / "dbt_project/models/1_staging/api_football/sources.yml"
    text = path.read_text(encoding="utf-8")
    chunks: list[str] = []
    for code, folder in LEAGUES:
        if f"raw_apif_{folder}_fixtures_next" in text:
            continue
        for ent_slug, bq_suffix in ENTITIES:
            chunks.append(f"      - name: raw_apif_{folder}_{ent_slug}")
            chunks.append(f"        identifier: RAW_APIF_{code}_{bq_suffix}")
            chunks.append(FRESHNESS)
    if not chunks:
        print("sources.yml already has SA/L1")
        return
    insert = "\n".join(chunks) + "\n"
    anchor = "      - name: raw_apif_wc_fixtures_next"
    text = text.replace(anchor, insert + anchor, 1)
    path.write_text(text, encoding="utf-8")
    print("patched sources.yml")


def patch_fixtures_next() -> None:
    path = REPO / "dbt_project/models/2_base/api_football/base_apif__fixtures_next.sql"
    text = path.read_text(encoding="utf-8")
    anchor = f"""    from {{{{ ref('stg_apif__{ANCHOR_FOLDER}_fixtures_next') }}}}
    where fixture_id is not null
)"""
    adds = ""
    for _code, folder in LEAGUES:
        if f"stg_apif__{folder}_fixtures_next" in text:
            continue
        adds += FIXTURES_UNION.format(folder=folder)
    if not adds:
        return
    text = text.replace(anchor, anchor[:-1] + adds + "\n)", 1)
    path.write_text(text, encoding="utf-8")
    print("patched base_apif__fixtures_next.sql")


def patch_list_model(rel_path: str, cte_suffix: str, cte_body: str) -> None:
    path = REPO / rel_path
    text = path.read_text(encoding="utf-8")
    list_key = f"'import_stg_{ANCHOR_FOLDER}_{cte_suffix}',"
    if list_key not in text:
        raise SystemExit(f"{ANCHOR_FOLDER} list anchor missing in {rel_path}")
    for _code, folder in LEAGUES:
        cte_name = f"import_stg_{folder}_{cte_suffix}"
        if cte_name in text:
            continue
        text = text.replace(
            list_key,
            list_key + "\n    " + f"'{cte_name}',",
            1,
        )
    union_anchor = f"\nunioned_{cte_suffix.replace('fixture_', '')} as ("
    if cte_suffix == "fixture_statistics":
        union_anchor = "\nunioned_fixture_statistics as ("
    pos = text.find(union_anchor)
    if pos < 0:
        raise SystemExit(f"union anchor missing in {rel_path}")
    blocks = ",\n\n".join(
        cte_body.format(folder=folder)
        for _code, folder in LEAGUES
        if f"import_stg_{folder}_{cte_suffix}" not in text[:pos]
    )
    if blocks:
        text = text[:pos] + ",\n\n" + blocks + text[pos:]
    path.write_text(text, encoding="utf-8")
    print(f"patched {rel_path}")


def patch_leagues() -> None:
    path = REPO / "dbt_project/models/2_base/api_football/base_apif__leagues.sql"
    text = path.read_text(encoding="utf-8")
    anchor = f"""    from {{{{ ref('stg_apif__{ANCHOR_FOLDER}_leagues') }}}}
    where league_api_id is not null and season_api_year is not null
),

deduped as ("""
    adds = ""
    for _code, folder in LEAGUES:
        if f"stg_apif__{folder}_leagues" in text:
            continue
        adds += LEAGUES_UNION.format(folder=folder)
    if not adds:
        return
    text = text.replace(anchor, adds + "\n),\n\ndeduped as (", 1)
    path.write_text(text, encoding="utf-8")
    print("patched base_apif__leagues.sql")


def patch_teams_fixtures() -> None:
    path = REPO / "dbt_project/models/2_base/api_football/base_apif__teams.sql"
    text = path.read_text(encoding="utf-8")
    anchor = """    from {{ ref('stg_apif__bl2_fixtures_next') }}

),

team_keys as ("""
    adds = ""
    for _code, folder in LEAGUES:
        if f"stg_apif__{folder}_fixtures_next" in text:
            continue
        adds += TEAMS_FX_UNION.format(folder=folder)
    if not adds:
        return
    text = text.replace(anchor, adds + "\n\n),\n\nteam_keys as (", 1)
    path.write_text(text, encoding="utf-8")
    print("patched base_apif__teams.sql")


def patch_dbt_project_yml() -> None:
    path = REPO / "dbt_project/dbt_project.yml"
    text = path.read_text(encoding="utf-8")
    if "    - L1\n" not in text:
        text = text.replace("    - BL2\n", "    - BL2\n    - L1\n", 1)
    if "    - SA\n" not in text:
        text = text.replace("    - PL\n", "    - PL\n    - SA\n", 1)
    if "    - VL\n" not in text:
        text = text.replace("    - SA\n", "    - SA\n    - VL\n", 1)
    path.write_text(text, encoding="utf-8")
    print("patched dbt_project.yml")


def main() -> None:
    patch_sources()
    patch_fixtures_next()
    patch_list_model(
        "dbt_project/models/2_base/api_football/base_apif__standings.sql",
        "standings",
        STANDINGS_BODY,
    )
    patch_list_model(
        "dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql",
        "fixture_statistics",
        STATS_BODY,
    )
    patch_leagues()
    patch_teams_fixtures()
    patch_dbt_project_yml()


if __name__ == "__main__":
    main()
