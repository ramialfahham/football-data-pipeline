"""Tests for `scripts/sync_metric_docs_blocks.py`.

The point is not that the generator runs on today's seed. It does, and a test
asserting only that would stay green while the thing quietly stopped matching
anything — this repo's dominant failure (#904).

So each test drives the script against a synthetic catalogue and asserts one
thing it MUST refuse, or one property of what it emits. The refusals matter most:
this generator's whole reason for existing is that a definition written by hand
drifts from the seed, and its central risk is deciding something it has no key to
decide. Six columns were wired to the wrong meaning of `league_code` in #82 MR3
by a tool that assumed one name means one thing.
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
    """`denominator_expr` is the catalogue's own marker of a rate or ratio, and the
    generator refuses to TOTAL one. Empty by default, so a plain `_row` is a count."""
    return {"metric_id": metric_id, "entity": entity, "description": description,
            "denominator_expr": denominator_expr}


def _seed(tmp_path, rows, name="metric_catalogue.csv"):
    """A catalogue CSV holding exactly the rows given."""
    path = tmp_path / name
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    return path


def _filler(n, start=0):
    """Rows that are valid and uninteresting, to clear the MIN_METRICS floor."""
    return [_row(f"filler_{i:03d}") for i in range(start, start + n)]


def _models(tmp_path, columns, model="some_model"):
    """A models/ tree holding one yml that declares exactly these column names."""
    root = tmp_path / "models"
    root.mkdir(parents=True, exist_ok=True)
    entries = "\n".join(f"      - name: {c}" for c in columns)
    (root / "schema.yml").write_text(
        f"version: 2\nmodels:\n  - name: {model}\n    columns:\n{entries}\n",
        encoding="utf-8")
    return root


@pytest.fixture(autouse=True)
def _point_at_tmp(monkeypatch, tmp_path):
    """Each test supplies a handful of rows, so the real floor of 50 would fire on
    every one of them and mask what is being checked. It keeps its real value in
    `test_the_row_floor_fires_on_a_truncated_read`, which is the only place it is
    asserted, and the script runs it at full strength for real.

    `MODELS` and `MIN_DERIVED` are pointed the same way and for the same reason:
    the generator's second input is the project's own column names, and a test
    that left it pointed at the real `models/` tree would be asserting against
    500-odd real columns instead of the two it declares."""
    monkeypatch.setattr(gen, "MIN_METRICS", 1)
    monkeypatch.setattr(gen, "MIN_DERIVED", 0)
    monkeypatch.setattr(gen, "MODELS", _models(tmp_path, []))
    monkeypatch.setattr(gen, "OUT", tmp_path / "out" / "metric_columns.md")


def _run(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["sync_metric_docs_blocks.py", *args])
    return gen.main()


# ---------------------------------------------------------------- reading the seed

def test_the_row_floor_fires_on_a_truncated_read(monkeypatch, tmp_path, capsys):
    """The floor keeps its REAL value here and nowhere else. A moved seed or a
    parser change leaves the read matching almost nothing, and a generator that
    emits an empty file "successfully" deletes every definition on the next run."""
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
    """An empty slot here becomes an empty description on every column of that
    name, which is worse than no block at all: it looks authoritative."""
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
    """`goals_open_play` is the scoreline minus penalties AND own goals for a team,
    and total goals minus penalties for a player. The catalogue's real key is
    (metric_id, entity). Emitting one block would force every caller to point at a
    definition that is wrong for half of them."""
    rows = [_row("goals_open_play", "team", "Team meaning."),
            _row("goals_open_play", "player", "Player meaning.")]

    assert gen._blocks(rows) == {
        "goals_open_play__team": "Team meaning.",
        "goals_open_play__player": "Player meaning.",
    }


def test_disagreeing_rows_sharing_an_entity_are_refused(tmp_path):
    """THE GUARD THAT MATTERS. When entity does not separate the rows there is no
    key to split on, and picking one would repeat exactly the defect this script
    was written after — a tool assuming one name means one thing."""
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
    # ⚠ The three below are the ones an enumerated phrase list MISSES.
    # `finishing_efficiency_pct` said "share the window" and "the window is not fully
    # shot-covered" and slipped through, and the MR's own verification used the
    # same narrow pattern as the guard, so it could only ever agree with it.
    "and both sides share the window",
    "null when the window is incomplete",
    "over a fully covered window",
])
def test_a_definition_describing_a_window_is_refused(monkeypatch, tmp_path, capsys, phrase):
    """The seed declares itself window-free: the window is applied where the metric
    is computed, never in the catalogue. These blocks land on PER-MATCH core
    columns, where a window claim is simply false. 35 descriptions contradicted
    the seed's own contract and were corrected; this keeps them corrected."""
    rows = _filler(2) + [_row("windowed", "team", f"Average goals {phrase}.")]
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, rows))

    assert _run(monkeypatch, "--check") == 1
    err = capsys.readouterr().err
    assert "still describe a window" in err
    assert "windowed" in err


def test_the_same_definition_without_the_window_phrase_is_accepted(monkeypatch, tmp_path):
    """A rule that fires on everything is as useless as one that fires on nothing."""
    rows = _filler(2) + [_row("clean", "team", "Average goals scored per match.")]
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, rows))

    assert _run(monkeypatch) == 0


# ---------------------------------------------------------------- what it emits

@pytest.mark.parametrize("endings", [b"\r\n", b"\n"])
def test_a_rerun_keeps_the_line_endings_the_file_already_has(monkeypatch, tmp_path, endings):
    """⚠ THE TEST THIS REPLACES ASSERTED CRLF UNCONDITIONALLY, and that is what hid
    the defect. The repo STORES LF; a Windows checkout materialises CRLF and a
    Linux checkout (CI) materialises LF, so there is no single correct byte
    sequence. Rendering CRLF and comparing bytes exactly meant `--check` could only
    pass on Windows and failed on every CI run — found by CI on the very MR that
    proposed wiring this check into CI, not by the test that claimed to cover it.

    Writing the wrong endings is not cosmetic either: it rewrites every line while
    `git diff` shows nothing, because git normalises. That is the silent rewrite
    that cost MR2 a review round."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(3)))
    assert _run(monkeypatch) == 0

    # Force the file into the endings a checkout on that platform would produce.
    canonical = gen.OUT.read_bytes().replace(b"\r\n", b"\n")
    gen.OUT.write_bytes(canonical.replace(b"\n", endings))

    # In sync regardless of endings — this is the half that broke CI.
    assert _run(monkeypatch, "--check") == 0
    # And a no-op run writes nothing at all.
    assert _run(monkeypatch) == 1


@pytest.mark.parametrize("endings", [b"\r\n", b"\n"])
def test_a_REAL_rewrite_keeps_the_line_endings_the_file_already_has(
        monkeypatch, tmp_path, endings):
    """⚠ THE TEST ABOVE DOES NOT REACH THE WRITE PATH, and I did not notice.

    It re-encodes the same content, so the run short-circuits on "already up to
    date" and returns before `_to_disk` is ever called. Deleting `_to_disk`'s
    CRLF-preservation branch entirely left all 30 tests green — found by hand-mutating
    it, after the branch this one replaces had been found untested for the same reason.

    So this test forces GENUINE drift by changing the seed, which is the everyday
    workflow: edit a definition on a CRLF checkout and regenerate. Without the
    branch, every line of a tracked file silently flips to LF and `git diff` hides
    it — the MR2 defect, reintroduced by the fix for a different line-ending bug."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(3) + [_row("before", "team", "Old.")]))
    assert _run(monkeypatch) == 0

    canonical = gen.OUT.read_bytes().replace(b"\r\n", b"\n")
    gen.OUT.write_bytes(canonical.replace(b"\n", endings))

    # Real content drift, so the generator must actually rewrite the file.
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
    """git's stored form. A Windows checkout converts it on its own; hard-coding
    CRLF here is what made the check platform-dependent."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(3)))
    assert not gen.OUT.exists()

    assert _run(monkeypatch) == 0

    assert b"\r\n" not in gen.OUT.read_bytes()


def test_blocks_are_sorted_so_a_rerun_reproduces_the_file(monkeypatch, tmp_path):
    """The output must be a pure function of the seed. If ordering followed the
    CSV, a reordered seed would produce a large meaningless diff and the file
    could not be regenerated byte for byte — the reproducibility property the
    script promises."""
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
    """Without this, the first person to improve a definition edits the output and
    loses the change on the next run, while the seed and the warehouse quietly
    disagree about what the metric means."""
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
    """The point of the check: the seed is edited and the file is not regenerated.
    Naming the block makes the failure actionable without a diff tool."""
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
    """Someone adds a metric and does not regenerate. This is one of the two most
    likely real drift events for a catalogue, and it was untested until the
    mutation was hand-run and nothing went red: the
    "changed:" branch alone still satisfied the older assertion, because the exit
    code comes from a byte comparison in `main()`, not from `_describe_drift`."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(3)))
    assert _run(monkeypatch) == 0
    capsys.readouterr()

    monkeypatch.setattr(gen, "SEED",
                        _seed(tmp_path, _filler(3) + [_row("newcomer")], "grown.csv"))

    assert _run(monkeypatch, "--check") == 1
    out = capsys.readouterr().out
    assert "missing block: newcomer" in out


def test_check_names_a_metric_REMOVED_from_the_seed(monkeypatch, tmp_path, capsys):
    """The other half. A block left behind after its metric is deleted is worse
    than a missing one: it still renders into the warehouse, describing something
    the catalogue no longer defines."""
    monkeypatch.setattr(gen, "SEED",
                        _seed(tmp_path, _filler(3) + [_row("doomed")]))
    assert _run(monkeypatch) == 0
    capsys.readouterr()

    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(3), "shrunk.csv"))

    assert _run(monkeypatch, "--check") == 1
    out = capsys.readouterr().out
    assert "block no longer in the seed: doomed" in out


def test_check_reports_pure_formatting_drift(monkeypatch, tmp_path, capsys):
    """The fallback: same blocks, same text, different bytes. Without it the
    failure would name nothing at all and read as a bug in the checker.

    ⚠ THIS TEST USED TO MANGLE LINE ENDINGS, which is no longer drift — the
    checkout decides those, and treating them as drift is what made `--check` fail
    on every CI run. The header is the honest way to reach this branch now."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(3)))
    assert _run(monkeypatch) == 0
    capsys.readouterr()

    # Blocks untouched; only the generated header is mangled.
    gen.OUT.write_bytes(gen.OUT.read_bytes().replace(b"DO NOT EDIT", b"do not edit"))

    assert _run(monkeypatch, "--check") == 1
    out = capsys.readouterr().out
    assert "the blocks all match but the bytes do not" in out


def test_check_fails_when_the_file_is_absent(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(2)))

    assert _run(monkeypatch, "--check") == 1
    assert "does not exist" in capsys.readouterr().out


def test_check_writes_nothing(monkeypatch, tmp_path):
    """A checker that repairs what it checks always passes, and the drift it was
    built to surface never reaches a human."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(2)))

    assert _run(monkeypatch, "--check") == 1
    assert not gen.OUT.exists()


# ---------------------------------------------------------------- writing

def test_a_run_with_nothing_to_do_is_loud_not_silently_green(monkeypatch, tmp_path, capsys):
    """The `declare_missing_columns.py` precedent. A generator reporting success
    while doing nothing is how a broken read passes for a working one."""
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
# The defect these exist for, in one sentence: a stem with ONE catalogue row says
# nothing about which entity the columns carrying its derived name belong to, so
# composing a block from the metric alone put one entity's definition into the
# other's column. 21 of 76 derived names had that shape. It was caught by reading
# the output, by nothing automatic.
# ⚠ The worked example was `goals_against` — defined for a PLAYER ("while the player
# was on the pitch") while the columns of that name lived on TEAM models. Step 4 of
# the naming programme renamed the player metric to `goals_against_player`, so THAT
# EXAMPLE IS HISTORICAL; the fixtures below keep using it because they exercise the
# mechanism, which is not.

def test_a_derived_block_is_ALWAYS_entity_suffixed(monkeypatch, tmp_path):
    """The whole safety property. A bare `goals_this_season` block is a block any
    column of that name can point at, whatever entity it belongs to — which is how
    a player's definition reaches a team column. There must be no bare form to
    point at, even when the metric has exactly one entity and no ambiguity at all.
    """
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [_row("goals", entity="player")]))
    monkeypatch.setattr(gen, "MODELS", _models(tmp_path, ["goals_this_season"]))

    assert _run(monkeypatch) == 0
    text = gen.OUT.read_text(encoding="utf-8")
    assert "{% docs goals_this_season__player %}" in text
    assert "{% docs goals_this_season %}" not in text


def test_only_the_entities_the_catalogue_defines_get_a_derived_block(monkeypatch, tmp_path):
    """A metric the catalogue never defined for an entity has NO block for it, so
    a column of that entity has nothing to point at and stays blank and VISIBLE.
    That is the intended outcome, not a gap: 48 real team columns are in exactly
    this position, and blank-and-visible beats documented-and-wrong."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [_row("goals", entity="player")]))
    monkeypatch.setattr(gen, "MODELS", _models(tmp_path, ["goals_sum_season"]))

    assert _run(monkeypatch) == 0
    text = gen.OUT.read_text(encoding="utf-8")
    assert "goals_sum_season__player" in text
    assert "goals_sum_season__team" not in text


def test_the_most_specific_metric_wins_when_a_name_decomposes_two_ways(
        monkeypatch, tmp_path):
    """`goals_per_match_this_season` is `goals` + "per match, this season" AND
    `goals_per_match` + "this season". Both render a true sentence, so neither
    fails loudly — but only the second carries the definition the catalogue wrote
    for that rate, null policy included. The composed form silently drops it.

    ⚠ THIS TEST REPLACES A VACUOUS ONE. Its first version asserted "the longest
    AFFIX wins" using `duels_won_pct_this_season`, and survived a mutation that
    reversed the affix order — because `_decompose` tries every affix and only
    accepts a stem that is a real metric, so ordering is irrelevant unless TWO
    decompositions are valid. Mutation testing is the only reason that was found,
    and it also showed the rule itself was wrong: longest-affix-first picks the
    LESS specific metric here."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [
        _row("goals", description="Goals scored."),
        _row("goals_per_match", description="Goals per match. Null when no games."),
    ]))
    monkeypatch.setattr(gen, "MODELS", _models(tmp_path, ["goals_per_match_this_season"]))

    assert _run(monkeypatch) == 0
    body = _parse(gen.OUT.read_text(encoding="utf-8"))["goals_per_match_this_season__team"]
    assert body.startswith("Goals per match. Null when no games.")
    assert "Divided by matches played" not in body


def test_a_per_match_affix_beats_the_plain_season_affix(monkeypatch, tmp_path):
    """`goals_against_per_match_this_season` has no metric `goals_against_per_match`
    in this seed, so it must strip the COMPOSITE affix and land on `goals_against`.
    Trying `_this_season` first would leave `goals_against_per_match`, match
    nothing, and emit no block at all — a silent hole rather than a wrong answer,
    but still a hole."""
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
    """Nested fields are spelled `recent_meetings.goals_against` and cannot be
    blocks: dbt matches `\\w+` in both the docs tag and `doc()`.

    ⚠ NO GUARD IS NEEDED FOR THIS AND THE FIRST VERSION HAD ONE ANYWAY. It filtered
    dotted column names before decomposing, and a mutation deleting that filter
    changed nothing — a dotted name cannot decompose at all, because the dot always
    lands in the stem and no metric id contains one. The guard was dead and its
    test could not fail. This asserts the PROPERTY, and the reachable guard is
    tested separately below."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [_row("goals_against")]))
    monkeypatch.setattr(gen, "MODELS", _models(
        tmp_path, ["recent_meetings.goals_against", "goals_against_sum_season"]))

    assert _run(monkeypatch) == 0
    text = gen.OUT.read_text(encoding="utf-8")
    assert "recent_meetings" not in text
    assert "goals_against_sum_season__team" in text          # the sibling still works


def test_an_affix_containing_a_dot_is_refused_at_the_output(monkeypatch, tmp_path, capsys):
    """The reachable half. An affix with a dot in it — `recent_meetings.` was one,
    and was removed — makes an emitted name dbt cannot address. Unlike the input
    filter this replaces, deleting the check makes this test fail."""
    monkeypatch.setattr(gen, "DERIVED_AFFIXES",
                        (("recent_meetings.", "prefix", "From a recent meeting."),))
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [_row("goals_against")]))
    monkeypatch.setattr(gen, "MODELS",
                        _models(tmp_path, ["recent_meetings.goals_against"]))

    assert _run(monkeypatch, "--check") == 1
    assert "not addressable by dbt" in capsys.readouterr().err


def test_the_derived_floor_fires_when_the_column_read_stops_matching(
        monkeypatch, tmp_path, capsys):
    """The second input needs the same floor as the first. A moved directory or a
    parser change leaves the walk matching nothing, and quietly emitting no derived
    blocks would blank every column that referenced one on the next build."""
    monkeypatch.setattr(gen, "MIN_DERIVED", 5)
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [_row("goals")]))
    monkeypatch.setattr(gen, "MODELS", _models(tmp_path, ["goals_this_season"]))

    assert _run(monkeypatch, "--check") == 1
    assert "floor 5" in capsys.readouterr().err


def test_an_unparseable_model_yml_is_refused_not_silently_skipped(
        monkeypatch, tmp_path, capsys):
    """A file that will not parse means the column set is INCOMPLETE, and an
    incomplete set silently drops blocks. Skipping it would make "no block for that
    column" look like "that column does not exist"."""
    root = _models(tmp_path, ["goals_this_season"])
    (root / "broken.yml").write_text("models: [ unterminated\n", encoding="utf-8")
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [_row("goals")]))
    monkeypatch.setattr(gen, "MODELS", root)

    assert _run(monkeypatch, "--check") == 1
    assert "incomplete" in capsys.readouterr().err


def test_a_derived_block_colliding_with_a_metric_block_is_refused(
        monkeypatch, tmp_path, capsys):
    """Two producers, one name: one would overwrite the other in the dict and the
    output would be correct-looking and wrong. Reachable when a metric is literally
    named like a derived column AND is entity-split."""
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
    """`clean_sheets` is the RATIO clean-sheet games over games played, and its
    catalogue text carries that ratio's display convention ("e.g. 3/5"). The column
    `clean_sheets_sum_season` is the raw count. Composing the two produced one
    fluent sentence asserting the value is both a small fraction and a season
    total. It shipped past every guard: the block resolved, the length was fine,
    dbt parsed. Only a human reading it could catch it.

    The test is the catalogue's own `denominator_expr`, so it is the CLASS and not
    the one name."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [
        _row("clean_sheets", description="Clean sheets, shown as e.g. 3/5.",
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
    """The refusal must be narrow. "This season's clean-sheet rate" is a perfectly
    good sentence; only TOTALLING a rate is a different quantity. Twelve real rate
    metrics take `_this_season` / `_prev_season` / `_delta_yoy` and must keep them.
    """
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [
        _row("clean_sheets", description="Clean sheets, shown as e.g. 3/5.",
             denominator_expr="count(*)")]))
    monkeypatch.setattr(gen, "MODELS", _models(
        tmp_path, ["clean_sheets_this_season", "clean_sheets_sum_season"]))

    assert _run(monkeypatch) == 0
    text = gen.OUT.read_text(encoding="utf-8")
    assert "clean_sheets_this_season__team" in text
    assert "clean_sheets_sum_season__team" not in text


def test_the_yoy_null_cause_differs_by_entity(monkeypatch, tmp_path):
    """"A gap in statistical coverage" is a real NULL cause for a TEAM and an
    impossible one for a PLAYER: a player's null per-match stat MEANS ZERO, so a
    running sum never goes null for coverage, and the player model names only the
    absent prior season at that club. Shipping the team sentence on four player
    columns was a false claim in the warehouse."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [
        _row("goals", entity="player", description="Goals scored."),
        _row("clean_sheets", entity="team", description="Clean sheets."),
    ]))
    monkeypatch.setattr(gen, "MODELS",
                        _models(tmp_path, ["goals_delta_yoy", "clean_sheets_delta_yoy"]))

    assert _run(monkeypatch) == 0
    blocks = _parse(gen.OUT.read_text(encoding="utf-8"))
    assert "stat-covered" in blocks["clean_sheets_delta_yoy__team"]
    assert "stat-cover" not in blocks["goals_delta_yoy__player"]
    assert "no prior season at this club" in blocks["goals_delta_yoy__player"]
    # ⚠ AND THE CAUSE THE FIRST FIX DROPPED. Removing the false coverage clause
    # also removed a true one: the block is reused at `mart_player_profile`, which
    # carries cup and tournament seasons where there is no year-on-year comparison
    # at all. A shared block is only as true as its widest call site.
    for entity in ("goals_delta_yoy__player", "clean_sheets_delta_yoy__team"):
        assert "no year-on-year comparison" in blocks[entity], entity


def test_an_entity_with_no_phrase_is_refused_rather_than_given_another_ones(
        monkeypatch, tmp_path, capsys):
    """The reachable half of the entity-specific phrasing. A third entity, or a
    renamed one, must stop the run rather than quietly take the team sentence."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [
        _row("goals", entity="squad", description="Goals scored.")]))
    monkeypatch.setattr(gen, "MODELS", _models(tmp_path, ["goals_delta_yoy"]))

    assert _run(monkeypatch, "--check") == 1
    assert "another entity's sentence" in capsys.readouterr().err


def _parse(text):
    import re
    return {m.group(1): " ".join(m.group(2).split()) for m in re.finditer(
        r"\{%\s*docs\s+(\w+)\s*%\}(.*?)\{%\s*enddocs\s*%\}", text, re.S)}


# ---------------------------------------------------------------- the real repo

def test_no_line_breaks_a_hyphenated_word(monkeypatch, tmp_path):
    """`textwrap.wrap` defaults to `break_on_hyphens=True` and split "year-on-year"
    into "year-on-" / "year". This text is not laid out for a reader of the file:
    `persist_docs` pushes it into the warehouse, where the newline collapses and it
    renders as "year-on- year". Five such breaks were already live on main before
    this MR, from the previous one."""
    import re

    # ⚠ A DELIBERATELY UNBREAKABLE-EXCEPT-AT-THE-HYPHEN TOKEN. The first version of
    # this test used a natural sentence with "year-on-year" in it and SURVIVED the
    # mutation, because at width 95 the wrapper never happened to choose that
    # hyphen. One hyphenated token longer than the wrap width leaves it no other
    # break point, so the mutation has nowhere to hide.
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, [
        _row("goals", description="x" * 60 + "-" + "y" * 60 + ".")]))
    monkeypatch.setattr(gen, "MODELS", _models(tmp_path, ["goals_this_season"]))

    assert _run(monkeypatch) == 0
    broken = [ln for ln in gen.OUT.read_text(encoding="utf-8").splitlines()
              if re.search(r"\w-$", ln)]
    assert not broken, "a hyphenated word was split across lines: " + repr(broken)


def test_the_real_file_breaks_no_hyphenated_word():
    """The same property on the SHIPPED file, because the synthetic one above can
    only prove the wrapper was called correctly for text this test chose."""
    import re

    import importlib
    fresh = importlib.reload(gen)
    broken = [ln for ln in fresh.OUT.read_text(encoding="utf-8").splitlines()
              if re.search(r"\w-$", ln)]
    assert not broken, (
        "these lines end mid-word, so the rendered warehouse description reads "
        "with a stray space inside the term: " + repr(broken))


def test_the_real_repo_emits_no_bare_derived_block():
    """The safety property, asserted against the ACTUAL generated file rather than
    a synthetic one. Every block whose name ends in a known affix must carry an
    entity suffix; a bare one is a block a column of the wrong entity can point at.
    """
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
    """Run at FULL strength against the actual repo, with no monkeypatching of the
    floor or the paths. This is the one that fails if someone edits the seed and
    forgets to regenerate — which is the whole reason the script has a --check."""
    import importlib

    fresh = importlib.reload(gen)
    try:
        rows = fresh._read_rows()
        expected = fresh._render(rows, fresh._column_names())
    except fresh.Abort as exc:                                  # pragma: no cover
        pytest.fail(f"the real catalogue does not render: {exc}")

    assert fresh.OUT.exists(), "the generated file is missing from the repo"
    # `_same`, not `==`: the checkout decides the line endings, so a byte-exact
    # comparison here passes on Windows and fails on every Linux CI run. That is
    # precisely how this test failed in CI on the MR that introduced it.
    assert fresh._same(fresh.OUT.read_bytes(), expected), (
        "dbt_project/models/docs/metric_columns.md has drifted from the seed. "
        "Run: python scripts/sync_metric_docs_blocks.py"
    )
    assert len(rows) >= fresh.MIN_METRICS
