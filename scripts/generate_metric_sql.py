"""Write each player surface's metric SQL from `metric_catalogue.csv`, and check it matches.

The catalogue is the one place a metric's numerator and denominator are written. A model that
computes a player metric does not carry its own copy: this script writes the catalogue formula
into the model, between two marker lines, applied to the rows of that model's own window. The
window (which matches) and the per-row completeness flag stay hand-written in the model; the
formula never does.

Every aggregate in a formula is written with the eligibility rule around it: it is NULL unless
the window is complete (`window_is_complete`, supplied by the model for every row) and every row
of the window has its input. So one missing input anywhere in the window makes the metric NULL,
and a ratio is never divided over the matches we happen to have.

One `_render()` serves both modes, so the file on disk and the check can never compute two
different answers. The drift check is `tests/test_generate_metric_sql.py`, which runs in
`test:python`.

Usage:

    python scripts/generate_metric_sql.py            # rewrite the generated blocks
    python scripts/generate_metric_sql.py --check    # fail if a block has drifted
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import re
import sys
from dataclasses import dataclass

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SEED = REPO_ROOT / "dbt_project" / "seeds" / "metric_catalogue.csv"
MODELS = REPO_ROOT / "dbt_project" / "models"

BASE_RELATION = "int_legs__player_match"
BEGIN = "-- metric sql generated from metric_catalogue.csv by scripts/generate_metric_sql.py; edit the catalogue"
END = "-- end of generated metric sql"
INDENT = "    "
MAX_LINE = 120

# A floor under the read, so a moved seed or a renamed column fails loudly instead of emitting
# empty blocks.
MIN_FORMULAS = 40

AGGREGATE = re.compile(r"\b(sum|countif)\(([^()]*)\)")

COUNTS = (
    "goals_player", "goals_penalty_player", "assists_player", "shots_player", "shots_on_goal_player",
    "passes_player", "passes_key_player", "passes_accurate_player", "tackles_player",
    "interceptions_player", "blocks_player", "duels_player", "duels_won_player",
    "dribbles_attempts_player", "dribbles_success_player", "dribbles_past_player", "offsides_player",
    "cards_yellow_player", "cards_red_player", "penalty_won_player", "penalty_committed_player",
    "saves_player", "goals_against_player",
)
COMPOSITES = (
    "goals_open_play_player", "scorer_points_player", "defensive_actions_player", "cards_player",
    "shots_on_goal_against_player",
)
RATIOS = (
    "passes_accuracy_player_pct", "duels_won_player_pct", "dribbles_success_player_pct",
    "saves_player_pct", "finishing_efficiency_player_pct",
)
PER90 = (
    "goals_per90", "assists_per90", "scorer_points_per90", "shots_on_goal_per90", "passes_key_per90",
    "dribbles_success_per90", "passes_per90", "tackles_per90", "interceptions_per90", "blocks_per90",
    "defensive_actions_per90", "duels_won_per90", "saves_per90",
)
WINDOW_COUNTS = (
    "goals_player", "assists_player", "goals_against_player", "saves_player", "shots_player",
    "shots_on_goal_player", "passes_player", "passes_key_player", "passes_accurate_player",
    "tackles_player", "blocks_player", "interceptions_player", "duels_player", "duels_won_player",
    "dribbles_attempts_player", "dribbles_success_player", "dribbles_past_player", "offsides_player",
    "cards_yellow_player", "cards_red_player", "penalty_won_player", "penalty_committed_player",
)
WINDOW_RATIOS = (
    "saves_player_pct", "dribbles_success_player_pct", "passes_accuracy_player_pct",
    "duels_won_player_pct",
)
POSITION_COUNTS = (
    "goals_player", "goals_penalty_player", "assists_player", "shots_on_goal_player", "passes_player",
    "passes_accurate_player", "passes_key_player", "tackles_player", "interceptions_player",
    "blocks_player", "duels_player", "duels_won_player", "dribbles_attempts_player",
    "dribbles_success_player", "saves_player", "goals_against_player",
)


@dataclass(frozen=True)
class Surface:
    model: str
    metrics: tuple[str, ...]
    windowed: bool = False


SURFACES = (
    Surface("4_intermediate/shared/int_player_club_season__metrics.sql",
            COUNTS + ("minutes_per_appearance",)),
    Surface("4_intermediate/domestic_league/team_season/int_player_season__metrics.sql",
            COUNTS + COMPOSITES + RATIOS + PER90),
    Surface("4_intermediate/shared/int_player_season_position__metrics.sql",
            POSITION_COUNTS + ("scorer_points_player", "defensive_actions_player") + RATIOS + PER90),
    Surface("4_intermediate/shared/int_player_momentum__metrics.sql",
            WINDOW_COUNTS + WINDOW_RATIOS),
    Surface("4_intermediate/shared/int_player_season_record.sql",
            WINDOW_COUNTS + ("defensive_actions_player",) + WINDOW_RATIOS, windowed=True),
    Surface("4_intermediate/shared/int_player_profile__contribution.sql",
            ("scorer_points_player",)),
    Surface("5_marts/shared/mart_player_fixture_stats.sql",
            ("passes_accuracy_player_pct",), windowed=True),
    Surface("5_marts/shared/mart_player_match_log.sql",
            ("passes_accuracy_player_pct",), windowed=True),
)


class Abort(Exception):
    pass


def _read_formulas(seed: pathlib.Path = SEED) -> dict[str, tuple[str, str]]:
    """metric_id -> (numerator_expr, denominator_expr) for every player expression row."""
    with open(seed, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    formulas: dict[str, tuple[str, str]] = {}
    for row in rows:
        if (row["entity"].strip() != "player" or row["computation_kind"].strip() != "expression"
                or row["base_relation"].strip() != BASE_RELATION):
            continue
        metric = row["metric_id"].strip()
        if metric in formulas:
            raise Abort(f"{metric} is defined twice for the player entity")
        numerator = row["numerator_expr"].strip()
        if not numerator:
            raise Abort(f"{metric} has no numerator_expr")
        formulas[metric] = (numerator, row["denominator_expr"].strip())
    if len(formulas) < MIN_FORMULAS:
        raise Abort(f"read {len(formulas)} player formulas from {_rel(seed)} (floor {MIN_FORMULAS})")
    return formulas


def _pieces(expression: str, windowed: bool) -> list:
    """The expression split into plain text and gated aggregates, each aggregate as (inline, broken).

    A gated aggregate is NULL unless the window is complete and every row has its input."""
    over = " over w" if windowed else ""
    pieces: list = []
    position = 0
    for match in AGGREGATE.finditer(expression):
        function, inner = match.group(1), match.group(2).strip()
        subject = f"({inner})" if re.search(r"\W", inner) else inner
        condition = f"logical_and(window_is_complete and {subject} is not null){over}"
        value = f"{function}({inner}){over}"
        pieces.append(expression[position:match.start()])
        pieces.append((f"if({condition}, {value}, null)",
                       ["if(", INDENT + condition + ",", INDENT + value + ",", INDENT + "null", ")"]))
        position = match.end()
    if len(pieces) == 0:
        raise Abort(f"no sum() or countif() in `{expression}`")
    pieces.append(expression[position:])
    return pieces


def _inline(pieces: list) -> str:
    return "".join(piece if isinstance(piece, str) else piece[0] for piece in pieces)


def _broken(pieces: list) -> list[str]:
    lines = [""]
    for piece in pieces:
        if isinstance(piece, str):
            lines[-1] += piece
        else:
            lines[-1] += piece[1][0]
            lines.extend(piece[1][1:])
    return lines


def _fits(lines: list[str], margin: str) -> bool:
    return all(len(margin + line) + 1 <= MAX_LINE for line in lines)


def _metric_lines(metric: str, numerator: str, denominator: str, windowed: bool,
                  margin: str) -> list[str]:
    """The most compact layout of the metric whose every line fits the lint's line length."""
    top = _pieces(numerator, windowed)
    if not denominator:
        layouts = [[f"{_inline(top)} as {metric}"], _broken(top)]
        layouts[1][-1] += f" as {metric}"
    else:
        bottom = _pieces(denominator, windowed)
        layouts = [
            [f"safe_divide({_inline(top)}, {_inline(bottom)}) as {metric}"],
            ["safe_divide(", INDENT + _inline(top) + ",", INDENT + _inline(bottom), f") as {metric}"],
            (["safe_divide("] + [INDENT + line for line in _broken(top)]),
        ]
        layouts[2][-1] += ","
        layouts[2] += [INDENT + line for line in _broken(bottom)] + [f") as {metric}"]
    for layout in layouts:
        if _fits(layout, margin):
            return layout
    raise Abort(f"{metric}: no layout fits {MAX_LINE} characters")


def _block(surface: Surface, formulas: dict[str, tuple[str, str]], margin: str) -> list[str]:
    """The generated select-list lines, indented to `margin`, the begin marker's own indentation."""
    missing = [m for m in surface.metrics if m not in formulas]
    if missing:
        raise Abort(f"{surface.model}: no player expression formula for {', '.join(missing)}")
    if len(set(surface.metrics)) != len(surface.metrics):
        raise Abort(f"{surface.model}: a metric is listed twice")
    lines = [margin + BEGIN]
    for position, metric in enumerate(surface.metrics):
        numerator, denominator = formulas[metric]
        rendered = [margin + line for line in _metric_lines(metric, numerator, denominator,
                                                              surface.windowed, margin)]
        if position < len(surface.metrics) - 1:
            rendered[-1] += ","
        lines.extend(rendered)
    lines.append(margin + END)
    return lines


def _apply(text: str, surface: Surface, formulas: dict[str, tuple[str, str]]) -> str:
    lines = text.replace("\r\n", "\n").split("\n")
    starts = [i for i, line in enumerate(lines) if line.strip() == BEGIN]
    ends = [i for i, line in enumerate(lines) if line.strip() == END]
    if len(starts) != 1 or len(ends) != 1 or ends[0] < starts[0]:
        raise Abort(f"{surface.model}: needs exactly one pair of generated-block markers")
    begin = lines[starts[0]]
    margin = begin[:len(begin) - len(begin.lstrip())]
    return "\n".join(lines[:starts[0]] + _block(surface, formulas, margin) + lines[ends[0] + 1:])


def _render(models: pathlib.Path = MODELS, seed: pathlib.Path = SEED) -> dict[pathlib.Path, str]:
    """Path -> the model text with its generated block as the catalogue says it must be."""
    formulas = _read_formulas(seed)
    rendered: dict[pathlib.Path, str] = {}
    for surface in SURFACES:
        path = models / surface.model
        if not path.exists():
            raise Abort(f"{surface.model} does not exist")
        rendered[path] = _apply(path.read_text(encoding="utf-8"), surface, formulas)
    return rendered


def _same(a: str, b: str) -> bool:
    return a.replace("\r\n", "\n") == b.replace("\r\n", "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--check", action="store_true",
                        help="Verify every generated block matches the catalogue. Writes nothing; "
                             "exits 1 on drift.")
    args = parser.parse_args(argv)
    try:
        expected = _render()
    except Abort as exc:
        print("generate_metric_sql: " + str(exc), file=sys.stderr)
        return 1

    drifted = [path for path, text in expected.items()
               if not _same(path.read_text(encoding="utf-8"), text)]
    if args.check:
        if drifted:
            print("FAIL: the generated metric SQL has drifted from " + _rel(SEED) + " in:")
            for path in drifted:
                print("  - " + _rel(path))
            print("\nThe catalogue is the source. Do not edit a generated block: run\n"
                  "  python scripts/generate_metric_sql.py")
            return 1
        print(f"OK: {len(expected)} player surfaces match {_rel(SEED)}.")
        return 0

    for path in drifted:
        existing = path.read_bytes()
        text = expected[path]
        if b"\r\n" in existing:
            text = text.replace("\n", "\r\n")
        path.write_bytes(text.encode("utf-8"))
        print("WROTE " + _rel(path))
    if not drifted:
        print("generate_metric_sql: already up to date. Nothing written.")
    return 0


def _rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


if __name__ == "__main__":
    sys.exit(main())
