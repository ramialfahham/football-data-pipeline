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
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import sync_metric_docs_blocks as gen  # noqa: E402


FIELDS = ["metric_id", "entity", "description"]


def _row(metric_id, entity="team", description="A definition."):
    return {"metric_id": metric_id, "entity": entity, "description": description}


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


@pytest.fixture(autouse=True)
def _point_at_tmp(monkeypatch, tmp_path):
    """Each test supplies a handful of rows, so the real floor of 50 would fire on
    every one of them and mask what is being checked. It keeps its real value in
    `test_the_row_floor_fires_on_a_truncated_read`, which is the only place it is
    asserted, and the script runs it at full strength for real."""
    monkeypatch.setattr(gen, "MIN_METRICS", 1)
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
    # `finishing_efficiency` said "share the window" and "the window is not fully
    # shot-covered" and slipped through, and the MR's own verification used the
    # same narrow pattern as the guard, so it could only ever agree with it.
    # Found by football-analytics-expert-reviewer.
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

def test_the_output_is_crlf(monkeypatch, tmp_path):
    """Every tracked file here is CRLF. Writing LF would rewrite the whole file on
    the first run, and `git diff` would HIDE it because it normalises line
    endings — a defect that cost a review round in MR2."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(3)))

    assert _run(monkeypatch) == 0

    raw = gen.OUT.read_bytes()
    assert raw.count(b"\r\n") > 0
    assert raw.count(b"\n") == raw.count(b"\r\n"), "a bare LF slipped in"


def test_blocks_are_sorted_so_a_rerun_reproduces_the_file(monkeypatch, tmp_path):
    """The output must be a pure function of the seed. If ordering followed the
    CSV, a reordered seed would produce a large meaningless diff and the file
    could not be regenerated byte for byte — the reproducibility property
    platform-reviewer required in MR3."""
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
    likely real drift events for a catalogue, and it was untested until
    platform-reviewer hand-ran the mutation and found nothing went red: the
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
    failure would name nothing at all and read as a bug in the checker."""
    monkeypatch.setattr(gen, "SEED", _seed(tmp_path, _filler(3)))
    assert _run(monkeypatch) == 0
    capsys.readouterr()

    # Same content, LF instead of CRLF.
    gen.OUT.write_bytes(gen.OUT.read_bytes().replace(b"\r\n", b"\n"))

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


# ---------------------------------------------------------------- the real repo

def test_the_real_seed_and_the_real_file_are_in_sync():
    """Run at FULL strength against the actual repo, with no monkeypatching of the
    floor or the paths. This is the one that fails if someone edits the seed and
    forgets to regenerate — which is the whole reason the script has a --check."""
    import importlib

    fresh = importlib.reload(gen)
    try:
        rows = fresh._read_rows()
        expected = fresh._render(rows)
    except fresh.Abort as exc:                                  # pragma: no cover
        pytest.fail(f"the real catalogue does not render: {exc}")

    assert fresh.OUT.exists(), "the generated file is missing from the repo"
    assert fresh.OUT.read_bytes() == expected, (
        "dbt_project/models/docs/metric_columns.md has drifted from the seed. "
        "Run: python scripts/sync_metric_docs_blocks.py"
    )
    assert len(rows) >= fresh.MIN_METRICS
