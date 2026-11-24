"""A team-season whose results disagree with the provider's standings is withheld and listed.

The macro team_seasons_off_standings finds the team-seasons whose counts differ from a standings row
that counts the same games, or whose games played fall below the most any standings row counts.
int_team_season__metrics holds the flag counts_withheld and blanks every season value where it is
true, mart_team_leaderboards counts a withheld team-season as having played, and the research list
carries its matches as team_season_off_standings. The tests of the disagreement derive it from
the legs and fct_standings, never from the flag, and stay at error.
Each pin fails when its wiring is undone.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DBT = ROOT / "dbt_project"
MACROS = DBT / "macros"
TESTS = DBT / "tests"
SEASON = DBT / "models" / "4_intermediate" / "domestic_league" / "team_season"
MART = DBT / "models" / "5_marts" / "shared"

KEYS = (
    "team_season_sk",
    "team_sk",
    "league_sk",
    "season_sk",
    "league_code",
    "season_api_year",
    "entity_type",
    "counts_withheld",
)


def _sql(path):
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"\{#.*?#\}", " ", text, flags=re.DOTALL)
    text = re.sub(r"--[^\n]*", " ", text)
    return re.sub(r"\s+", " ", text)


def _macro(file, name):
    text = _sql(MACROS / f"{file}.sql")
    return text.split(f"macro {name}", 1)[1].split("endmacro", 1)[0].rsplit("{%", 1)[0]


def _stays_at_error(text):
    softened = (
        "error_if",
        "warn_if",
        "severity = 'warn'",
        'severity = "warn"',
        "where =",
        "limit =",
        "enabled =",
        "fail_calc",
    )
    return "severity = 'error'" in text and not any(word in text for word in softened)


def _yml_block(path, model):
    text = path.read_text(encoding="utf-8")
    return text.split(f"- name: {model}\n", 1)[1].split("\n  - name: ", 1)[0]


def test_the_macro_finds_counts_that_differ_where_the_standings_count_the_same_games():
    body = _macro("team_seasons_off_standings", "team_seasons_off_standings")
    assert body.lstrip().startswith("(counts, standings, adjustments) -%}")
    assert (
        "off_adjusted as ( select league_code, season, team_id, trim(group_name) as group_name, "
        "sum(points_taken) as points_taken from {{ adjustments }} "
        "group by league_code, season, team_id, trim(group_name) )"
    ) in body
    assert (
        "off_same_games as ( select distinct o.team_sk, o.season_sk, 'counts_differ' as reason "
        "from {{ counts }} as o inner join {{ standings }} as t on o.team_sk = t.team_sk "
        "and o.season_sk = t.season_sk and o.season_games_played = t.played "
        "left join off_adjusted as a on t.league_code = a.league_code and t.season_api_year = a.season "
        "and t.team_api_id = a.team_id and trim(t.group_name) = a.group_name "
        "where o.wins is distinct from t.wins or o.draws is distinct from t.draws "
        "or o.losses is distinct from t.losses or o.goals is distinct from t.goals_scored "
        "or o.goals_against is distinct from t.goals_conceded "
        "or o.points_won is distinct from t.points + coalesce(a.points_taken, 0) )"
    ) in body


def test_the_macro_finds_games_played_below_the_most_any_standings_row_counts():
    body = _macro("team_seasons_off_standings", "team_seasons_off_standings")
    assert (
        "off_most_played as ( select team_sk, season_sk, max(played) as played "
        "from {{ standings }} group by team_sk, season_sk )"
    ) in body
    assert (
        "off_short as ( select distinct o.team_sk, o.season_sk, 'games_short' as reason "
        "from {{ counts }} as o inner join off_most_played as s on o.team_sk = s.team_sk "
        "and o.season_sk = s.season_sk where s.played is not null and o.season_games_played < s.played )"
    ) in body
    assert body.rstrip().endswith(
        "select * from off_same_games union all select * from off_short"
    )


def test_the_macro_that_counts_from_the_legs_follows_the_season_rules():
    body = _macro("team_season_counts_from_legs", "team_season_counts_from_legs")
    assert body.lstrip().startswith("(legs) -%}")
    assert (
        "select team_sk, season_sk, count(*) as season_games_played, countif(result = 'W') as wins, "
        "countif(result = 'D') as draws, countif(result = 'L') as losses, "
        "if(logical_and(goals is not null), sum(goals), null) as goals, "
        "if(logical_and(goals_against is not null), sum(goals_against), null) as goals_against, "
        "sum(case result when 'W' then 3 when 'D' then 1 else 0 end) "
        "+ if(logical_and(is_table_shootout_win is not null), countif(is_table_shootout_win), null) as points_won "
        "from {{ legs }} group by team_sk, season_sk"
    ) in body


def test_the_model_flags_the_disagreeing_team_seasons_and_blanks_every_value():
    text = _sql(SEASON / "int_team_season__metrics.sql")
    assert (
        "season_counts as ( select team_sk, season_sk, season_games_played, wins_sum_season as wins, "
        "draws_sum_season as draws, losses_sum_season as losses, goals, goals_against, points_won "
        "from season_final )"
    ) in text
    assert (
        "off_standings as ( {{ team_seasons_off_standings('season_counts', ref('fct_standings'), "
        "ref('standings_points_adjustments')) }} )"
    ) in text
    assert "withheld as ( select distinct team_sk, season_sk from off_standings )" in text
    assert "w.team_sk is not null as counts_withheld" in text
    assert (
        "left join withheld as w on sf.team_sk = w.team_sk and sf.season_sk = w.season_sk )"
    ) in text
    assert text.rstrip().endswith("from season_row")
    assert " select * replace ( " in text


def test_the_model_blanks_exactly_the_columns_the_yml_declares_but_the_keys_and_the_flag():
    text = _sql(SEASON / "int_team_season__metrics.sql")
    replaced = re.findall(r"if\(counts_withheld, null, (\w+)\) as (\w+)", text)
    assert replaced
    assert all(left == right for left, right in replaced)
    names = [left for left, _ in replaced]
    assert len(names) == len(set(names))
    block = _yml_block(SEASON / "int_team_season.yml", "int_team_season__metrics")
    block = block.split("\n  - name: ", 1)[0]
    declared = re.findall(r"^      - name: (\w+)$", block, flags=re.MULTILINE)
    assert set(declared) - set(KEYS) == set(names)
    assert set(KEYS) <= set(declared)
    assert text.count("if(counts_withheld, null,") == len(names)


def test_the_flag_is_declared_without_a_hiding_filter_and_the_blankable_values_carry_no_not_null():
    yml = (SEASON / "int_team_season.yml").read_text(encoding="utf-8")
    block = yml.split("- name: int_team_season__metrics\n", 1)[1].split("\n  - name: ", 1)[0]
    flag = block.split("- name: counts_withheld", 1)[1].split("\n      - name: ", 1)[0]
    assert "tests: [not_null]" in flag
    games = block.split("- name: season_games_played", 1)[1].split("\n      - name: ", 1)[0]
    assert "not_null" not in games
    season = (MART / "shared.yml").read_text(encoding="utf-8")
    record = season.split("- name: mart_team_season\n", 1)[1].split("\n  - name: ", 1)[0]
    for column in (
        "played",
        "wins",
        "draws",
        "losses",
        "goals_for",
        "goals_against",
        "goal_diff",
        "points",
        "clean_sheets",
    ):
        body = record.split(f"- name: {column}\n", 1)[1].split("\n      - name: ", 1)[0]
        assert "not_null" not in body, column
    games_record = season.split("- name: mart_team_season_record\n", 1)[1].split("\n  - name: ", 1)[0]
    assert "not_null" not in games_record.split("- name: games_played\n", 1)[1].split("\n      - name: ", 1)[0]
    insights = (DBT / "models" / "5_marts" / "domestic_league" / "domestic_league.yml").read_text(encoding="utf-8")
    block = insights.split("- name: season_games_played\n", 1)[1].split("\n      - name: ", 1)[0]
    assert "not_null" not in block


def test_a_withheld_team_season_stays_in_the_field_of_teams_that_played():
    text = _sql(MART / "mart_team_leaderboards.sql")
    assert (
        "from {{ ref('int_team_season__metrics') }} where season_games_played >= 1 or counts_withheld ), "
    ) in text
    assert (
        "field as ( select league_code, season_api_year, count(*) as teams_played from season "
        "group by league_code, season_api_year )"
    ) in text
    assert "teams_with_value = teams_played" in text
    assert (
        "latest_season as ( select league_code, max(season_api_year) as latest_season_api_year "
        "from field group by league_code )"
    ) in text
    assert "inner join latest_season as ls on l.league_code = ls.league_code" in text
    assert "season_api_year = latest_season_api_year as is_current_season" in text
    assert "order by season_api_year desc ) = 1 as is_current_season" not in text
    coverage = _sql(TESTS / "assert_mart_team_leaderboards_boards_cover_every_team.sql")
    assert "where season_games_played >= 1 or counts_withheld group by league_code, season_api_year" in coverage


def test_the_research_list_carries_every_finished_match_of_a_withheld_team_season():
    text = _sql(MART / "mart_competition_research_list.sql")
    assert (
        "off_standings_items as ( select 'team_season_off_standings' as check_name, 'none' as seed, "
        "r.fixture_sk, r.team_sk, cast(null as string) as correction, cast(null as int64) as provider_team_id "
        "from {{ ref('int_team_season_record') }} as r inner join {{ ref('int_team_season__metrics') }} as m "
        "on r.team_sk = m.team_sk and r.season_sk = m.season_sk where m.counts_withheld )"
    ) in text
    assert (
        "from off_standings_items as s inner join fixtures as f on s.fixture_sk = f.fixture_sk union all"
    ) in text
    shared = (MART / "shared.yml").read_text(encoding="utf-8")
    assert shared.count('"team_season_off_standings", "lineup_duplicate_withheld", "null_key_line_withheld", "correction_no_longer_needed"]') == 1
    assert shared.count('"fixture_lineup_corrections", "none"]') == 1


def test_the_two_disagreement_tests_derive_the_disagreement_from_the_legs_and_stay_at_error():
    for name, reason in (
        ("assert_team_season_equals_league_table", "counts_differ"),
        ("assert_team_season_games_not_short_of_standings", "games_short"),
    ):
        text = _sql(TESTS / f"{name}.sql")
        assert _stays_at_error(text), name
        assert (
            "with leg_counts as ( {{ team_season_counts_from_legs(ref('int_legs__team_match')) }} ), "
            "disagreeing as ( {{ team_seasons_off_standings('leg_counts', ref('fct_standings'), "
            "ref('standings_points_adjustments')) }} ) select"
        ) in text, name
        assert (
            "from disagreeing as d left join {{ ref('int_team_season__metrics') }} as m "
            "on d.team_sk = m.team_sk and d.season_sk = m.season_sk "
            f"where d.reason = '{reason}' and ( m.team_sk is null or not coalesce(m.counts_withheld, false) "
            "or m.season_games_played is not null or m.wins_sum_season is not null "
            "or m.draws_sum_season is not null or m.losses_sum_season is not null "
            "or m.goals is not null or m.goals_against is not null or m.points_won is not null )"
        ) in text, name
        assert "where counts_withheld" not in text
        assert "from {{ ref('int_team_season__metrics') }} where" not in text


def test_the_reverse_test_holds_the_flag_the_values_the_marts_and_the_listing_to_the_disagreement():
    text = _sql(TESTS / "assert_team_season_blank_exactly_when_withheld.sql")
    assert _stays_at_error(text)
    assert (
        "with leg_counts as ( {{ team_season_counts_from_legs(ref('int_legs__team_match')) }} ), "
        "disagreeing as ( select distinct team_sk, season_sk from ( "
        "{{ team_seasons_off_standings('leg_counts', ref('fct_standings'), "
        "ref('standings_points_adjustments')) }} ) ), "
        "season as ( select m.*, d.team_sk is not null as disagrees "
        "from {{ ref('int_team_season__metrics') }} as m left join disagreeing as d "
        "on m.team_sk = d.team_sk and m.season_sk = d.season_sk )"
    ) in text
    assert "where counts_withheld and not disagrees" in text
    assert "where disagrees and not counts_withheld" in text
    assert "'withheld and holds a value' as failure from season where counts_withheld and ( {% for column in values %}" in text
    assert "where not counts_withheld and season_games_played is null" in text
    for model in ("mart_team_season", "mart_team_season_insights", "mart_team_season_record"):
        assert f"'{model}' as model" in text, model
    assert "where l.check_name = 'team_season_off_standings' and d.team_sk is null" in text
    assert "and l.check_name = 'team_season_off_standings' where l.fixture_sk is null" in text
    assert "raise_compiler_error" in text
    assert "{% if values | length == 0 %} {{ exceptions.raise_compiler_error(" in text
    assert (
        "{% set kept = [ 'team_season_sk', 'team_sk', 'league_sk', 'season_sk', 'league_code', "
        "'season_api_year', 'entity_type', 'counts_withheld' ] %}"
    ) in text
    assert "{{ column }} is not null{% if not loop.last %} or{% endif %}" in text
    assert (
        "where s.counts_withheld != ( t.played is null and t.wins is null and t.draws is null "
        "and t.losses is null and t.goals_for is null and t.goals_against is null and t.goal_diff is null "
        "and t.points is null and t.clean_sheets is null ) or ( not s.counts_withheld and ( t.played is null "
        "or t.wins is null or t.draws is null or t.losses is null or t.goals_for is null "
        "or t.goals_against is null or t.goal_diff is null or t.points is null or t.clean_sheets is null ) )"
    ) in text
    assert (
        "where (s.counts_withheld and i.season_games_played is not null) "
        "or (not s.counts_withheld and i.season_games_played is null)"
    ) in text
    assert (
        "where (s.counts_withheld and r.games_played is not null) "
        "or (not s.counts_withheld and r.games_played is null)"
    ) in text


def test_the_tests_that_read_the_record_and_the_current_season_follow_the_withheld_team_season():
    form = _sql(TESTS / "assert_team_form_window_follows_the_rule.sql")
    assert _stays_at_error(form)
    assert (
        "with leg_counts as ( {{ team_season_counts_from_legs(ref('int_legs__team_match')) }} ), "
        "disagreeing as ( select distinct team_sk, season_sk from ( "
        "{{ team_seasons_off_standings('leg_counts', ref('fct_standings'), "
        "ref('standings_points_adjustments')) }} ) ), upcoming as ("
    ) in form
    assert (
        "logical_or(l.season_api_year = s.season_api_year and d.team_sk is not null) as this_season_withheld, "
        "logical_or(l.season_api_year = s.season_api_year - 1 and d.team_sk is not null) as previous_season_withheld"
    ) in form
    assert "left join disagreeing as d on l.team_sk = d.team_sk and l.season_sk = d.season_sk" in form
    assert (
        "where e.window_type is distinct from m.window_type or e.games_played is distinct from m.games_played )"
    ) in form
    assert (
        "if( legs_this_season > 0, if(this_season_withheld, null, legs_this_season), "
        "if(previous_season_withheld, null, legs_previous_season) ) as games_played"
    ) in form
    leaders = _sql(TESTS / "assert_mart_team_leaderboards_one_leader_per_league.sql")
    assert (
        "leg_counts as ( {{ team_season_counts_from_legs(ref('int_legs__team_match')) }} ), "
        "disagreeing as ( select distinct team_sk, season_sk from ( "
        "{{ team_seasons_off_standings('leg_counts', ref('fct_standings'), "
        "ref('standings_points_adjustments')) }} ) ), "
        "latest_seasons as ( select league_code, max(season_api_year) as latest_season "
        "from {{ ref('int_team_season__metrics') }} group by league_code ), "
        "withheld_latest as ( select distinct l.league_code from latest_seasons as l "
        "inner join {{ ref('int_team_season__metrics') }} as m on l.league_code = m.league_code "
        "and l.latest_season = m.season_api_year inner join disagreeing as d "
        "on m.team_sk = d.team_sk and m.season_sk = d.season_sk )"
    ) in leaders
    assert (
        "left join withheld_latest as h on p.league_code = h.league_code group by p.league_code, h.league_code "
        "having if( h.league_code is not null, countif(p.flagged_rows > 0) > 0, "
        "countif(p.flagged_rows > 0) != 1 or max(case when p.flagged_rows > 0 then p.season_api_year end) "
        "!= max(p.season_api_year) or countif(p.flagged_rows > 0 and p.flagged_rows != p.season_rows) > 0 ) )"
    ) in leaders
    doc = (DBT / "models" / "docs" / "shared_columns.md").read_text(encoding="utf-8")
    block = doc.split("{% docs season_games_played__whole_season %}", 1)[1].split("{% enddocs %}", 1)[0]
    block = " ".join(block.split())
    assert "NULL only where the team-season is withheld" in block
    assert "Never NULL" not in block
    metrics = _yml_block(SEASON / "int_team_season.yml", "int_team_season__metrics")
    blanked = {
        left for left, _ in re.findall(r"if\(counts_withheld, null, (\w+)\) as (\w+)", _sql(SEASON / "int_team_season__metrics.sql"))
    }
    pairs = re.findall(r"- name: (\w+)\n\s+description: \"\{\{ doc\('(\w+)'\) \}\}", metrics)
    used = [doc_name for column, doc_name in pairs if column in blanked]
    assert "season_matchdays_used" in used and "wins_sum_season" in used
    every_doc = "\n".join(path.read_text(encoding="utf-8") for path in (DBT / "models" / "docs").glob("*.md"))
    for name in used:
        text = every_doc.split("{% docs " + name + " %}", 1)[1].split("{% enddocs %}", 1)[0]
        assert "never null" not in text.lower(), name


def test_the_recompute_tests_expect_a_blank_value_where_the_legs_disagree_and_the_hand_worked_key_does_not():
    key = _sql(TESTS / "assert_team_season_answer_key.sql")
    assert _stays_at_error(key)
    assert "team_seasons_off_standings" not in key and "counts_withheld" not in key
    assert "case when k.numerator is null then null when c.denominator_expr is not null then" in key
    formula = _sql(TESTS / "assert_team_metrics_follow_catalogue_formula.sql")
    assert _stays_at_error(formula)
    assert "'grain': ['team_sk', 'season_sk'], 'windowed': false, 'off_standings': true}" in formula
    assert (
        "off_standings_seasons as ( select distinct team_sk, season_sk from ( "
        "{{ team_seasons_off_standings('leg_counts', ref('fct_standings'), "
        "ref('standings_points_adjustments')) }} ) )"
    ) in formula
    assert "if(d.team_sk is not null, null, cast(e.{{ m.metric }} as float64))" in formula
    assert (
        "left join off_standings_seasons as d on coalesce(e.team_sk, m.team_sk) = d.team_sk "
        "and coalesce(e.season_sk, m.season_sk) = d.season_sk"
    ) in formula
    assert formula.count("'off_standings': true") == 1


def test_the_flag_is_no_metric_of_the_catalogue():
    text = _sql(TESTS / "assert_no_uncatalogued_season_metric.sql")
    assert "'games_expecting_team_stats', 'entity_type', 'counts_withheld'," in text


def test_the_answer_key_of_the_macro_runs_both_reasons_and_the_cases_beside_them():
    text = _sql(TESTS / "assert_team_season_off_standings_answer_key.sql")
    assert _stays_at_error(text)
    assert "{{ team_seasons_off_standings('counts', 'standings', 'adjustments') }}" in text
    assert (
        "expected as ( select * from unnest([ struct(2 as team_sk, 'S1' as season_sk, 'counts_differ' as reason), "
        "(3, 'S1', 'counts_differ'), (4, 'S1', 'counts_differ'), (5, 'S1', 'counts_differ'), "
        "(6, 'S1', 'counts_differ'), (7, 'S1', 'counts_differ'), (9, 'S1', 'counts_differ'), "
        "(10, 'S1', 'counts_differ'), (14, 'S1', 'games_short'), (16, 'S1', 'games_short'), "
        "(17, 'S1', 'counts_differ'), (18, 'S1', 'counts_differ'), (20, 'S1', 'counts_differ'), "
        "(20, 'S1', 'games_short') ]) )"
    ) in text
    assert (
        "from found as f full outer join expected as e on f.team_sk = e.team_sk and f.season_sk = e.season_sk "
        "and f.reason = e.reason where f.team_sk is null or e.team_sk is null"
    ) in text
    assert "('XX', 2025, 11, 'Main ', 3)," in text
    assert "(18, 'S1', 10, 5, 3, 2, cast(null as int64), 9, 18)," in text
    assert "('XX', 2025, 23, 'Main', 3), ('XX', 2025, 23, 'Main ', 3) ])" in text
    assert "(23, 'S1', 'XX', 2025, 23, 'Main', 10, 5, 3, 2, 16, 9, 12) ])" in text


def test_the_published_table_test_leaves_out_only_the_withheld_team_seasons():
    text = _sql(TESTS / "assert_team_table_equals_published_tables.sql")
    assert _stays_at_error(text)
    assert (
        "with leg_counts as ( {{ team_season_counts_from_legs(ref('int_legs__team_match')) }} ), "
        "withheld_team_seasons as ( select distinct team_sk, season_sk from ( "
        "{{ team_seasons_off_standings('leg_counts', ref('fct_standings'), "
        "ref('standings_points_adjustments')) }} ) ), snapshots as ("
    ) in text
    assert (
        "w.team_sk is not null as is_withheld from corrected as c inner join league_seasons as ls "
        "on c.league_code = ls.league_code and c.season_api_year = ls.season_api_year "
        "left join {{ ref('dim_competition_season') }} as cs on c.league_code = cs.league_code "
        "and c.season_api_year = cs.season_api_year left join withheld_team_seasons as w "
        "on c.team_sk = w.team_sk and cs.season_sk = w.season_sk"
    ) in text
    assert "from ({{ published_table_mismatches('compared') }}) union all" in text
    assert "countif(cp.is_comparable) as comparable_rows" in text
    assert "table_rank_mismatches" not in text
    body = _macro("published_table_mismatches", "published_table_mismatches")
    assert body.lstrip().startswith("(compared) -%}")
    assert "with section_teams as ( select * from {{ compared }} where is_comparable )," in body
    assert (
        "t.published_rank - countif(w.team_sk is not null and w.published_rank < t.published_rank) "
        "as published_place, "
        "t.rebuilt_rank - countif(w.team_sk is not null and w.rebuilt_rank < t.rebuilt_rank) "
        "as rebuilt_place from section_teams as t left join section_teams as w on "
        "t.league_code = w.league_code and t.season_api_year = w.season_api_year "
        "and t.group_name = w.group_name and t.ingested_at = w.ingested_at and w.is_withheld group by"
    ) in body
    assert "rank()" not in body
    assert (
        "from place_counted where not is_withheld and published_place != rebuilt_place "
        "and not is_place_not_compared union distinct"
    ) in body
    assert body.rstrip().endswith(
        "from section_teams where not is_withheld and rebuilt_points != published_points"
    )


def test_a_withheld_team_does_not_decide_whether_a_published_section_is_comparable():
    text = _sql(TESTS / "assert_team_table_equals_published_tables.sql")
    assert (
        "logical_and(w.team_sk is not null or r.played is not null and c.played = r.played) over ("
    ) in text


def test_the_answer_key_of_the_published_table_comparison_runs_the_macro_on_its_own_rows():
    text = _sql(TESTS / "assert_published_table_mismatches_answer_key.sql")
    assert _stays_at_error(text)
    assert "{{ published_table_mismatches('compared') }}" in text
    assert "in ('C:3', 'D:3', 'M:2', 'Q:1', 'R:1') as is_withheld from compared_rows" in text
    assert (
        "expected as ( select * from unnest([ struct('B' as group_name, 1 as team_sk), ('B', 2), ('D', 1), "
        "('D', 2), ('H', 2), ('I2', 1), ('I2', 2), ('K', 4), ('L', 2), ('O', 1), ('P', 1) ]) )"
    ) in text
    assert (
        "('XX', 2025, 'P', timestamp('2025-01-16'), 1, 1, 3, 9, 9, false, true), "
        "('XX', 2025, 'P', timestamp('2025-01-16'), 2, 2, cast(null as int64), 9, 9, false, true), "
        "('XX', 2025, 'P', timestamp('2025-01-16'), 3, 3, cast(null as int64), 9, 9, false, true), "
        "('XX', 2025, 'P', timestamp('2025-01-16'), 4, 4, 4, 3, 3, false, true), "
        "('XX', 2025, 'Q', timestamp('2025-01-17'), 1, 1, 3, 9, 3, false, true), "
        "('XX', 2025, 'Q', timestamp('2025-01-17'), 2, 2, 1, 6, 6, false, true), "
        "('XX', 2025, 'Q', timestamp('2025-01-17'), 3, 3, 2, 3, 3, false, true), "
        "('XX', 2025, 'R', timestamp('2025-01-18'), 1, 1, 1, 9, 3, false, true), "
        "('XX', 2025, 'R', timestamp('2025-01-18'), 2, 1, 2, 9, 9, false, true), "
        "('XX', 2025, 'R', timestamp('2025-01-18'), 3, 3, 3, 3, 3, false, true) ]) ),"
    ) in text
    assert (
        "('XX', 2025, 'L', timestamp('2025-01-12'), 2, 2, 2, 6, 5, false, true), "
        "('XX', 2025, 'L', timestamp('2025-01-12'), 3, 3, 3, 3, 3, false, true), "
        "('XX', 2025, 'M', timestamp('2025-01-13'), 1, 1, 1, 9, 9, false, true), "
        "('XX', 2025, 'M', timestamp('2025-01-13'), 2, 2, 2, 6, 5, false, true), "
    ) in text
    assert (
        "('XX', 2025, 'N', timestamp('2025-01-14'), 2, 2, 2, 6, 5, false, false), "
    ) in text
    assert "('XX', 2025, 'O', timestamp('2025-01-15'), 1, cast(null as int64), 1, 9, 8, false, true), " in text
    assert (
        "('XX', 2025, 'K', timestamp('2025-01-11'), 2, 2, 3, 6, 6, true, true), "
        "('XX', 2025, 'K', timestamp('2025-01-11'), 3, 3, 4, 6, 6, true, true), "
        "('XX', 2025, 'K', timestamp('2025-01-11'), 4, 4, 2, 4, 4, false, true), "
    ) in text
    assert (
        "('XX', 2025, 'J', timestamp('2025-01-10'), 1, cast(null as int64), 3, 9, 9, false, true), "
        "('XX', 2025, 'J', timestamp('2025-01-10'), 2, 1, 1, 9, 9, false, true), "
        "('XX', 2025, 'J', timestamp('2025-01-10'), 3, 2, 2, 6, 6, false, true), "
    ) in text
    assert (
        "from found as f full outer join expected as e on f.group_name = e.group_name and f.team_sk = e.team_sk "
        "where f.team_sk is null or e.team_sk is null"
    ) in text


def test_the_cleaning_rule_names_the_withheld_team_season():
    text = (DBT / "models" / "docs" / "cleaning_rules.md").read_text(encoding="utf-8")
    assert (
        "- A team-season whose results disagree with the provider's standings has every season value\n"
        "  withheld. Its matches stand on mart_competition_research_list."
    ) in text


def test_the_research_skill_does_not_research_the_row_kind():
    text = (ROOT / ".claude" / "skills" / "research-provider-errors" / "SKILL.md").read_text(encoding="utf-8")
    assert "`team_season_off_standings` row is not researched" in text
