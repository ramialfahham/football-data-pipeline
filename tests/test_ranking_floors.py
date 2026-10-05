"""The ranking and benchmark floors are dbt vars, and the ranking_rules doc block says the same numbers.

The doc block is what a reader sees in BigQuery and in the dbt docs; the vars are what the models
apply. Nothing else ties the two, so a floor changed in one place and not the other would publish a
rule the numbers do not follow. Values are read from parsed YAML and from the doc block's text.
"""

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
DBT = REPO / "dbt_project"
FLOORS = {
    "player_min_minutes": r"\bminutes",
    "player_min_shots_on_target": r"\bshots_on_goal_player",
    "team_min_matches": r"games_played",
}


def _vars():
    return yaml.safe_load((DBT / "dbt_project.yml").read_text(encoding="utf-8"))["vars"]


def _ranking_rules():
    text = (DBT / "models" / "docs" / "metric_rules.md").read_text(encoding="utf-8")
    match = re.search(r"{% docs ranking_rules %}(.*?){% enddocs %}", text, re.S)
    assert match, "the ranking_rules doc block is missing from models/docs/metric_rules.md"
    return " ".join(match.group(1).split())


def _ranking_models():
    for layer in ("4_intermediate", "5_marts"):
        yield from (DBT / "models" / layer).rglob("*.sql")


def test_every_floor_is_a_whole_number_var():
    v = _vars()
    for name in FLOORS:
        assert isinstance(v.get(name), int) and v[name] > 0, f"dbt_project.yml var {name} is not a positive integer"


def test_ranking_rules_words_state_the_vars():
    v = _vars()
    words = _ranking_rules()
    assert words.count(f"from {v['player_min_minutes']} minutes") == 2, words
    assert words.count(f"{v['player_min_shots_on_target']} shots on target") == 2, words
    assert f"from {v['team_min_matches']} finished matches" in words, words
    numbers = {int(n) for n in re.findall(r"\b\d+\b", words)}
    assert numbers == {v[name] for name in FLOORS}, f"ranking_rules states numbers {numbers} that are not the floor vars"


def test_every_floor_var_is_read_by_a_model():
    sql = "\n".join(p.read_text(encoding="utf-8") for p in _ranking_models())
    for name in FLOORS:
        assert re.search(rf"var\(\s*['\"]{name}['\"]\s*\)", sql), f"no model reads var('{name}')"


def test_no_model_writes_a_floor_as_a_number():
    found = []
    for path in _ranking_models():
        text = path.read_text(encoding="utf-8")
        for name, column in FLOORS.items():
            for m in re.finditer(rf"{column}\w*\s*>=\s*(\d+)", text):
                if int(m.group(1)) > 1:
                    found.append(f"{path.relative_to(REPO)}: {m.group(0)} (use var('{name}'))")
    assert not found, "\n".join(found)
