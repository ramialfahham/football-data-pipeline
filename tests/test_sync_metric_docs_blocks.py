"""Tests for `scripts/sync_metric_docs_blocks.py`, driven against synthetic catalogues.

Each test asserts one thing the generator must refuse, or one property of what it emits.
"""
from __future__ import annotations

import csv
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import sync_metric_docs_blocks as gen  # noqa: E402


FIELDS = ["metric_id", "entity", "description", "denominator_expr"]


def _row(metric_id, entity="team", description="A definition.", denominator_expr=""):
    """`denominator_expr` marks a rate or ratio, which the generator refuses to total; empty means a count."""
    return {"metric_id": metric_id, "entity": entity, "description": description,
            "denominator_expr": denominator_expr}


def _seed(tmp_path, rows, name="metric_catalogue.csv"):
    path = tmp_path / name
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    return path


def _filler(n, start=0):
    """Valid rows that clear the MIN_METRICS floor."""
    return [_row(f"filler_{i:03d}") for i in range(start, start + n)]


def _models(tmp_path, columns, model="some_model"):
    root = tmp_path / "models"
    root.mkdir(parents=True, exist_ok=True)
    entries = "\n".join(f"      - name: {c}" for c in columns)
    (root / "schema.yml").write_text(
        f"version: 2\nmodels:\n  - name: {model}\n    columns:\n{entries}\n",
        encoding="utf-8")
    return root


@pytest.fixture(autouse=True)
def _point_at_tmp(monkeypatch, tmp_path):
    """The real floor and the real `models/` tree would mask what each test checks, so both are replaced.

    The metric map has its own tests in test_metric_map.py; here it renders as a bare header.
    """
    monkeypatch.setattr(gen, "MIN_METRICS", 1)
    monkeypatch.setattr(gen, "MIN_DERIVED", 0)
    monkeypatch.setattr(gen, "MODELS", _models(tmp_path, []))
    monkeypatch.setattr(gen, "OUT", tmp_path / "out" / "metric_columns.md")
    monkeypatch.setattr(gen, "MAP_OUT", tmp_path / "out" / "metric_map.csv")
    monkeypatch.setattr(gen, "_render_map",
                        lambda rows, names: (",".join(gen.MAP_FIELDS) + "\n").encode("utf-8"))


def _run(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["sync_metric_docs_blocks.py", *args])
    return gen.main()


# ---------------------------------------------------------------- reading the seed

def test_the_row_floor_fires_on_a_truncated_read(monkeypatch, tmp_path, capsys):
    """The floor keeps its real value here; a generator that emits an empty file deletes every definition."""
    monkeypatch.setattr(gen, "MIN_METRICS", 50)
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(3)))

    assert _run(monkeypatch, "--check") == 1
    assert "floor 50" in capsys.readouterr().err


def test_a_missing_seed_is_refused(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(gen, "SEED", tmp_path / "absent.csv")

    assert _run(monkeypatch, "--check") == 1
    assert "seed not found" in capsys.readouterr().err


@pytest.mark.parametrize("field", ["metric_id", "entity", "description"])
def test_an_empty_required_field_is_refused(monkeypatch, tmp_path, capsys, field):
    """An empty slot becomes an empty description on every column of that name, which looks authoritative."""
    bad = _row("half_defined")
    bad[field] = "   "
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(2) + [bad]))

    assert _run(monkeypatch, "--check") == 1
    assert "empty " + field in capsys.readouterr().err


# ---------------------------------------------------------------- one name, two meanings

def test_rows_that_agree_produce_one_block(tmp_path):
    rows = [_row("shots_total", "team", "Total shots."),
            _row("shots_total", "player", "Total shots.")]
    assert gen._blocks(rows) == {"shots_total": "Total shots."}


def test_rows_that_disagree_produce_one_block_per_entity(tmp_path):
    """The catalogue's key is (metric_id, entity); one block would be wrong for half its callers."""
    rows = [_row("goals_open_play", "team", "Team meaning."),
            _row("goals_open_play", "player", "Player meaning.")]

    assert gen._blocks(rows) == {
        "goals_open_play__team": "Team meaning.",
        "goals_open_play__player": "Player meaning.",
    }


def test_disagreeing_rows_sharing_an_entity_are_refused(tmp_path):
    """When entity does not separate the rows there is no key to split on, so picking one is refused."""
    rows = [_row("ambiguous", "team", "One meaning."),
            _row("ambiguous", "team", "A different meaning.")]

    with pytest.raises(gen.Abort) as exc:
        gen._blocks(rows)
    assert "no key to tell them apart" in str(exc.value)
    assert "will not choose one" in str(exc.value)


# ---------------------------------------------------------------- the window rule

@pytest.mark.parametrize("phrase", [
    "in the form window",
    "in the window",
    "same-window",
    # The three below are the ones an enumerated phrase list misses.
    "and both sides share the window",
    "null when the window is incomplete",
    "over a fully covered window",
])
def test_a_definition_describing_a_window_is_refused(monkeypatch, tmp_path, capsys, phrase):
    """The window is applied where the metric is computed, and these blocks land on per-match columns."""
    rows = _filler(2) + [_row("windowed", "team", f"Average goals {phrase}.")]
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, rows))

    assert _run(monkeypatch, "--check") == 1
    err = capsys.readouterr().err
    assert "still describe a window" in err
    assert "windowed" in err


def test_the_same_definition_without_the_window_phrase_is_accepted(monkeypatch, tmp_path):
    rows = _filler(2) + [_row("clean", "team", "Average goals scored per match.")]
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, rows))

    assert _run(monkeypatch) == 0


# ---------------------------------------------------------------- the description standard

@pytest.mark.parametrize("description, shown", [
    ("A" * 201, "201 characters"),
    ("Goals the team scored, as goals_for.", "goals_for"),
    ("Goals the team scored, as xG_total.", "xG_total"),
    ("Goals the player scored per_90 minutes.", "per_90"),
    ("Goals per match. Null when no games.", "Null"),
    ("Shots the provider counted.", "provider"),
    ("Goals taken from the API.", "API"),
    ("Goals displayed as a whole number.", "displayed"),
    ("Goals shown as a whole number.", "shown as"),
    ("The retired count of goals.", "retired"),
    ("The count formerly kept apart.", "formerly"),
    ("Goals normalised to a season.", "normalised"),
    ("Goals aggregated over a season.", "aggregated"),
])
def test_a_description_that_breaks_the_standard_is_refused(
    monkeypatch, tmp_path, capsys, description, shown
):
    """engineering_standards.md section 2: at most 200 characters, no snake_case name, no listed word."""
    rows = _filler(2) + [_row("faulty", "team", description)]
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, rows))

    assert _run(monkeypatch, "--check") == 1
    err = capsys.readouterr().err
    assert "faulty (team)" in err
    assert shown in err


@pytest.mark.parametrize("description", [
    "G" * 199 + ".",
    "Goals annulled by the referee.",
    "Rapid attacks the team made.",
    "Shots-on-target the team had per match.",
])
def test_a_description_within_the_standard_is_accepted(monkeypatch, tmp_path, description):
    """A listed word is refused as a whole word only: "annulled" and "rapid" hold one inside."""
    rows = _filler(2) + [_row("within", "team", description)]
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, rows))

    assert _run(monkeypatch) == 0


# ---------------------------------------------------------------- what it emits

@pytest.mark.parametrize("endings", [b"\r\n", b"\n"])
def test_a_rerun_keeps_the_line_endings_the_file_already_has(monkeypatch, tmp_path, endings):
    """The repo stores LF and a checkout materialises CRLF or LF, so there is no single correct byte sequence."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(3)))
    assert _run(monkeypatch) == 0

    canonical = gen.OUT.read_bytes().replace(b"\r\n", b"\n")
    gen.OUT.write_bytes(canonical.replace(b"\n", endings))

    assert _run(monkeypatch, "--check") == 0
    assert _run(monkeypatch) == 1


@pytest.mark.parametrize("endings", [b"\r\n", b"\n"])
def test_a_REAL_rewrite_keeps_the_line_endings_the_file_already_has(
        monkeypatch, tmp_path, endings):
    """Genuine drift in the seed reaches `_to_disk`; an unchanged rerun short-circuits before it."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(3) + [_row("before", "team", "Old.")]))
    assert _run(monkeypatch) == 0

    canonical = gen.OUT.read_bytes().replace(b"\r\n", b"\n")
    gen.OUT.write_bytes(canonical.replace(b"\n", endings))

    monkeypatch.setattr(gen, "SEED",
                        _seed(tmp_path, _filler(3) + [_row("before", "team", "New.")], "drifted.csv"))
    assert _run(monkeypatch) == 0, "expected a real write, not a no-op"

    raw = gen.OUT.read_bytes()
    assert b"New." in raw, "the rewrite did not happen, so this proves nothing"
    if endings == b"\r\n":
        assert raw.count(b"\n") == raw.count(b"\r\n"), "a CRLF file was silently rewritten to LF"
    else:
        assert b"\r\n" not in raw, "CRLF was forced into an LF file"


def test_a_new_file_is_written_with_LF(monkeypatch, tmp_path):
    """LF is git's stored form; a Windows checkout converts it on its own."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(3)))
    assert not gen.OUT.exists()

    assert _run(monkeypatch) == 0

    assert b"\r\n" not in gen.OUT.read_bytes()


def test_blocks_are_sorted_so_a_rerun_reproduces_the_file(monkeypatch, tmp_path):
    """The output is a pure function of the seed, so a reordered seed reproduces the file byte for byte."""
    rows = [_row("zulu"), _row("alpha"), _row("mike")]
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, rows))
    assert _run(monkeypatch) == 0
    first = gen.OUT.read_bytes()

    gen.OUT.unlink()
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, list(reversed(rows)), "reordered.csv"))
    assert _run(monkeypatch) == 0

    assert gen.OUT.read_bytes() == first
    names = [n for n in ("alpha", "mike", "zulu")]
    body = first.decode("utf-8")
    assert [n for n in names if n in body] == sorted(names)
    assert body.index("{% docs alpha %}") < body.index("{% docs mike %}") < body.index("{% docs zulu %}")


def test_the_generated_file_says_it_is_generated(monkeypatch, tmp_path):
    """Otherwise a definition edited in the output is lost on the next run."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(2)))
    assert _run(monkeypatch) == 0

    head = gen.OUT.read_text(encoding="utf-8")[:400]
    assert "DO NOT EDIT" in head
    assert "metric_catalogue.csv" in head


# ---------------------------------------------------------------- --check

def test_check_passes_when_the_file_matches(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(3)))
    assert _run(monkeypatch) == 0
    capsys.readouterr()

    assert _run(monkeypatch, "--check") == 0
    assert "match" in capsys.readouterr().out


def test_check_fails_and_names_the_block_when_the_seed_moves(monkeypatch, tmp_path, capsys):
    """Naming the drifted block makes the failure actionable without a diff tool."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(2) + [_row("drifter", "team", "Before.")]))
    assert _run(monkeypatch) == 0
    capsys.readouterr()

    monkeypatch.setattr(gen, "SEED",
                        _seed(tmp_path, _filler(2) + [_row("drifter", "team", "After.")], "moved.csv"))

    assert _run(monkeypatch, "--check") == 1
    out = capsys.readouterr().out
    assert "drifted" in out
    assert "drifter" in out


def test_check_names_a_metric_ADDED_to_the_seed(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(3)))
    assert _run(monkeypatch) == 0
    capsys.readouterr()

    monkeypatch.setattr(gen, "SEED",
                        _seed(tmp_path, _filler(3) + [_row("newcomer")], "grown.csv"))

    assert _run(monkeypatch, "--check") == 1
    out = capsys.readouterr().out
    assert "missing block: newcomer" in out


def test_check_names_a_metric_REMOVED_from_the_seed(monkeypatch, tmp_path, capsys):
    """A block left behind after its metric is deleted still renders into the warehouse."""
    monkeypatch.setattr(gen, "SEED",
                        _seed(tmp_path, _filler(3) + [_row("doomed")]))
    assert _run(monkeypatch) == 0
    capsys.readouterr()

    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(3), "shrunk.csv"))

    assert _run(monkeypatch, "--check") == 1
    out = capsys.readouterr().out
    assert "block no longer in the seed: doomed" in out


def test_check_reports_pure_formatting_drift(monkeypatch, tmp_path, capsys):
    """Same blocks, different bytes; line endings are the checkout's choice, so the header is mangled instead."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(3)))
    assert _run(monkeypatch) == 0
    capsys.readouterr()

    gen.OUT.write_bytes(gen.OUT.read_bytes().replace(b"DO NOT EDIT", b"do not edit"))

    assert _run(monkeypatch, "--check") == 1
    out = capsys.readouterr().out
    assert "the blocks all match but the bytes do not" in out


def test_check_fails_when_the_file_is_absent(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(2)))

    assert _run(monkeypatch, "--check") == 1
    assert "does not exist" in capsys.readouterr().out


def test_check_writes_nothing(monkeypatch, tmp_path):
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(2)))

    assert _run(monkeypatch, "--check") == 1
    assert not gen.OUT.exists()


# ---------------------------------------------------------------- writing

def test_a_run_with_nothing_to_do_is_loud_not_silently_green(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(3)))
    assert _run(monkeypatch) == 0
    capsys.readouterr()

    assert _run(monkeypatch) == 1
    assert "already up to date" in capsys.readouterr().err


def test_a_write_creates_the_directory_and_reports_the_count(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(4)))
    assert not gen.OUT.parent.exists()

    assert _run(monkeypatch) == 0

    out = capsys.readouterr().out
    assert "WROTE" in out and "4 blocks" in out
    assert gen.OUT.read_text(encoding="utf-8").count("{% docs ") == 4


# ------------------------------------------------------------- derived columns
#
# A derived name says nothing about which entity its columns belong to, so its block is entity-suffixed.

def test_a_derived_block_is_ALWAYS_entity_suffixed(monkeypatch, tmp_path):
    """A bare block would be pointed at by a column of any entity, even when the metric has one entity."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [_row("goals", entity="player")]))
    monkeypatch.setattr(gen, "MODELS", _models(tmp_path, ["goals_this_season"]))

    assert _run(monkeypatch) == 0
    text = gen.OUT.read_text(encoding="utf-8")
    assert "{% docs goals_this_season__player %}" in text
    assert "{% docs goals_this_season %}" not in text


def test_a_rate_block_is_its_catalogue_sentence_and_nothing_appended(monkeypatch, tmp_path):
    """A rate's block and its derived blocks carry the catalogue sentence and the affix's sentence only."""
    rows = [_row("shots_on_goal_pct", "team", "Share of shots on goal.", "sum(shots_total)"),
            _row("shots_total", "team", "Total shots."),
            _row("saves_player_pct", "player", "Saves share.", "sum(saves + goals_against)")]
    blocks = gen._blocks(rows)
    assert blocks["shots_on_goal_pct"] == "Share of shots on goal."
    assert blocks["shots_total"] == "Total shots."
    assert blocks["saves_player_pct"] == "Saves share."

    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, rows))
    monkeypatch.setattr(gen, "MODELS", _models(tmp_path, ["shots_on_goal_pct_this_season"]))
    assert _run(monkeypatch) == 0
    text = gen.OUT.read_text(encoding="utf-8")
    start = text.index("{% docs shots_on_goal_pct_this_season__team %}")
    block = " ".join(text[start:text.index("{% enddocs %}", start)].split())
    affix_sentence = {a: p for a, _, p in gen.DERIVED_AFFIXES}["_this_season"]
    assert block.endswith("%} Share of shots on goal. " + affix_sentence)
    assert "NULL" not in block


def test_only_the_entities_the_catalogue_defines_get_a_derived_block(monkeypatch, tmp_path):
    """A column of an entity the catalogue never defined has no block to point at and stays visibly blank."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [_row("goals", entity="player")]))
    monkeypatch.setattr(gen, "MODELS", _models(tmp_path, ["goals_sum_season"]))

    assert _run(monkeypatch) == 0
    text = gen.OUT.read_text(encoding="utf-8")
    assert "goals_sum_season__player" in text
    assert "goals_sum_season__team" not in text


def test_the_most_specific_metric_wins_when_a_name_decomposes_two_ways(
        monkeypatch, tmp_path):
    """`goals_per_match_this_season` splits as `goals` + an affix or `goals_per_match` + an affix; only the second carries the rate's definition."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [
        _row("goals", description="Goals scored."),
        _row("goals_per_match", description="Average goals per match."),
    ]))
    monkeypatch.setattr(gen, "MODELS", _models(tmp_path, ["goals_per_match_this_season"]))

    assert _run(monkeypatch) == 0
    body = _parse(gen.OUT.read_text(encoding="utf-8"))["goals_per_match_this_season__team"]
    assert body.startswith("Average goals per match.")
    assert "Divided by matches played" not in body


def test_a_per_match_affix_beats_the_plain_season_affix(monkeypatch, tmp_path):
    """With no `goals_against_per_match` metric, the composite affix must be stripped to land on `goals_against`."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [
        _row("goals_against", description="Goals conceded."),
    ]))
    monkeypatch.setattr(gen, "MODELS",
                        _models(tmp_path, ["goals_against_per_match_this_season"]))

    assert _run(monkeypatch) == 0
    blocks = _parse(gen.OUT.read_text(encoding="utf-8"))
    body = blocks["goals_against_per_match_this_season__team"]
    assert body.startswith("Goals conceded.")
    assert "Divided by matches played" in body


def test_a_dotted_column_name_produces_no_block(monkeypatch, tmp_path):
    """Nested fields like `recent_meetings.goals_against` cannot be blocks: dbt matches `\\w+` in the docs tag and `doc()`."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [_row("goals_against")]))
    monkeypatch.setattr(gen, "MODELS", _models(
        tmp_path, ["recent_meetings.goals_against", "goals_against_sum_season"]))

    assert _run(monkeypatch) == 0
    text = gen.OUT.read_text(encoding="utf-8")
    assert "recent_meetings" not in text
    assert "goals_against_sum_season__team" in text          # the sibling still works


def test_an_affix_containing_a_dot_is_refused_at_the_output(monkeypatch, tmp_path, capsys):
    """An affix with a dot in it makes an emitted name dbt cannot address."""
    monkeypatch.setattr(gen, "DERIVED_AFFIXES",
                        (("recent_meetings.", "prefix", "From a recent meeting."),))
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [_row("goals_against")]))
    monkeypatch.setattr(gen, "MODELS",
                        _models(tmp_path, ["recent_meetings.goals_against"]))

    assert _run(monkeypatch, "--check") == 1
    assert "not addressable by dbt" in capsys.readouterr().err


def test_the_derived_floor_fires_when_the_column_read_stops_matching(
        monkeypatch, tmp_path, capsys):
    """A walk matching nothing would silently emit no derived blocks and blank every column that references one."""
    monkeypatch.setattr(gen, "MIN_DERIVED", 5)
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [_row("goals")]))
    monkeypatch.setattr(gen, "MODELS", _models(tmp_path, ["goals_this_season"]))

    assert _run(monkeypatch, "--check") == 1
    assert "floor 5" in capsys.readouterr().err


def test_an_unparseable_model_yml_is_refused_not_silently_skipped(
        monkeypatch, tmp_path, capsys):
    """A file that will not parse leaves the column set incomplete, which silently drops blocks."""
    root = _models(tmp_path, ["goals_this_season"])
    (root / "broken.yml").write_text("models: [ unterminated\n", encoding="utf-8")
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [_row("goals")]))
    monkeypatch.setattr(gen, "MODELS", root)

    assert _run(monkeypatch, "--check") == 1
    assert "incomplete" in capsys.readouterr().err


def test_a_derived_block_colliding_with_a_metric_block_is_refused(
        monkeypatch, tmp_path, capsys):
    """Two producers of one name would overwrite each other in the dict; reachable when a metric is named like a derived column and is entity-split."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [
        _row("goals", description="Goals scored."),
        _row("goals_this_season", entity="team", description="One meaning."),
        _row("goals_this_season", entity="player", description="Another meaning."),
    ]))
    monkeypatch.setattr(gen, "MODELS", _models(tmp_path, ["goals_this_season"]))

    assert _run(monkeypatch, "--check") == 1
    err = capsys.readouterr().err
    assert "BOTH" in err and "goals_this_season__team" in err


def test_a_totalling_affix_on_a_rate_metric_gets_no_block(monkeypatch, tmp_path, capsys):
    """Totalling a ratio would compose a sentence calling the value both a fraction and a season total; the test is `denominator_expr`."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [
        _row("clean_sheets", description="Matches without a goal conceded, as a share of all.",
             denominator_expr="count(*)"),
        _row("goals", description="Goals scored."),
    ]))
    monkeypatch.setattr(gen, "MODELS",
                        _models(tmp_path, ["clean_sheets_sum_season", "goals_sum_season"]))

    assert _run(monkeypatch) == 0
    text = gen.OUT.read_text(encoding="utf-8")
    assert "clean_sheets_sum_season__team" not in text
    assert "goals_sum_season__team" in text            # a real count still composes
    assert "clean_sheets_sum_season" in capsys.readouterr().out


def test_a_rate_metric_still_takes_the_NON_totalling_affixes(monkeypatch, tmp_path):
    """Only totalling a rate is a different quantity, so `_this_season`, `_prev_season` and `_delta_yoy` stay."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [
        _row("clean_sheets", description="Matches without a goal conceded, as a share of all.",
             denominator_expr="count(*)")]))
    monkeypatch.setattr(gen, "MODELS", _models(
        tmp_path, ["clean_sheets_this_season", "clean_sheets_sum_season"]))

    assert _run(monkeypatch) == 0
    text = gen.OUT.read_text(encoding="utf-8")
    assert "clean_sheets_this_season__team" in text
    assert "clean_sheets_sum_season__team" not in text


def test_no_yoy_block_carries_a_null_condition(monkeypatch, tmp_path):
    """The derived sentence says what the column is, alike for a team and a player."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [
        _row("goals", entity="player", description="Goals scored."),
        _row("clean_sheets", entity="team", description="Clean sheets."),
    ]))
    monkeypatch.setattr(gen, "MODELS",
                        _models(tmp_path, ["goals_delta_yoy", "clean_sheets_delta_yoy"]))

    assert _run(monkeypatch) == 0
    blocks = _parse(gen.OUT.read_text(encoding="utf-8"))
    player = blocks["goals_delta_yoy__player"]
    team = blocks["clean_sheets_delta_yoy__team"]
    assert "NULL" not in player and "NULL" not in team
    assert player.removeprefix("Goals scored. ") == team.removeprefix("Clean sheets. ")


def _parse(text):
    import re
    return {m.group(1): " ".join(m.group(2).split()) for m in re.finditer(
        r"\{%\s*docs\s+(\w+)\s*%\}(.*?)\{%\s*enddocs\s*%\}", text, re.S)}


# ---------------------------------------------------------------- the real repo

def test_no_line_breaks_a_hyphenated_word(monkeypatch, tmp_path):
    """`persist_docs` pushes this text into the warehouse, where a newline after a hyphen renders as "year-on- year"."""
    import re

    # One hyphenated token longer than the wrap width leaves the wrapper no break point but the hyphen.
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [
        _row("goals", description="x" * 60 + "-" + "y" * 60 + ".")]))
    monkeypatch.setattr(gen, "MODELS", _models(tmp_path, ["goals_this_season"]))

    assert _run(monkeypatch) == 0
    broken = [ln for ln in gen.OUT.read_text(encoding="utf-8").splitlines()
              if re.search(r"\w-$", ln)]
    assert not broken, "a hyphenated word was split across lines: " + repr(broken)


def test_the_real_file_breaks_no_hyphenated_word():
    """The same property on the shipped file, since the synthetic text above is of this test's own choosing."""
    import re

    import importlib
    fresh = importlib.reload(gen)
    broken = [ln for ln in fresh.OUT.read_text(encoding="utf-8").splitlines()
              if re.search(r"\w-$", ln)]
    assert not broken, (
        "these lines end mid-word, so the rendered warehouse description reads "
        "with a stray space inside the term: " + repr(broken))


def test_the_real_repo_emits_no_bare_derived_block():
    """Every block whose name ends in a known affix must carry an entity suffix, checked on the generated file."""
    import importlib
    import re

    fresh = importlib.reload(gen)
    text = fresh.OUT.read_text(encoding="utf-8")
    names = set(re.findall(r"\{%\s*docs\s+(\w+)\s*%\}", text))
    metrics = {r["metric_id"].strip() for r in fresh._read_rows()}

    bare = sorted(n for n in names
                  if not n.endswith(("__team", "__player"))
                  and fresh._decompose(n, metrics))
    assert not bare, (
        "these derived blocks carry no entity suffix, so a column of either entity "
        "could point at them: " + ", ".join(bare))
    assert len(names) > fresh.MIN_DERIVED


def test_the_real_seed_and_the_real_file_are_in_sync():
    """Runs against the actual repo with no monkeypatching, so it fails when the seed changes without a regenerate."""
    import importlib

    fresh = importlib.reload(gen)
    try:
        rows = fresh._read_rows()
        expected = fresh._render(rows, fresh._column_names())
    except fresh.Abort as exc:                                  # pragma: no cover
        pytest.fail(f"the real catalogue does not render: {exc}")

    assert fresh.OUT.exists(), "the generated file is missing from the repo"
    # `_same`, not `==`, because the checkout decides the line endings.
    assert fresh._same(fresh.OUT.read_bytes(), expected), (
        "dbt_project/models/docs/metric_columns.md has drifted from the seed. "
        "Run: python scripts/sync_metric_docs_blocks.py"
    )
    assert len(rows) >= fresh.MIN_METRICS
