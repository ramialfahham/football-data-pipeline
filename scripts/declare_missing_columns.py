"""Declare columns that EXIST in the warehouse but appear in no `.yml`.

`check_description_hygiene.py` checks the CONTENT of descriptions that exist, and
object-level PRESENCE. Neither can see a column that is declared nowhere at all:
there is no yml entry to look at. Measured against production when this was
written, that was 979 columns across 40 models — most of it invisible to every
check we had.

This script writes their NAMES down, with no descriptions, so the real surface
becomes visible and the shared definitions can be wired into it. A name with no
text is an honest empty slot. Inventing text to fill it is "thin filler", and it
would be far harder to find and replace later than an empty slot is.

IT NEVER REORDERS OR REFORMATS A LINE THAT IS ALREADY THERE, AND THAT IS THE
WHOLE POINT. That constraint is what separates it from a general yml formatter,
which is why every edit is done on LINES and not by re-serialising YAML — every
round-trip library reformats something, and a diff nobody can read is a diff
nobody can review. The guarantee is checked twice before anything is written to
disk (see `_verify`), and again by the reviewer.

THREE OF THE FOUR MODES ARE STRICTLY APPEND-ONLY: they add `- name:` entries or a
`description:` line and delete nothing, so the reviewer's acceptance test is
simply that the diff has zero deleted lines.

⚠ `--promote-shared-docs` IS THE EXCEPTION, and it is narrow by construction. It
replaces ONE line — a `description:` that restates a docs block — with a reference
to that block, and it may do so only where the block's text EQUALS the text being
replaced, so the rendered result does not change at all. `_verify` is not relaxed
for it: it is handed the exact set of lines the run planned to swap, refuses a
`replace` touching anything else, and behaves identically to the old rule when
that set is empty, which is what every other mode passes. The acceptance test for
that mode is therefore "exactly N deletions, one per planned replacement, and no
others" rather than zero.
⛔ AND THE CHECK IT CANNOT DO: it proves the sentence is unchanged where it
already existed. It cannot know whether that sentence is TRUE at the blank sites
the block is then pointed at. Five names were pulled from the first promotion for
that reason. Read every model a block will reach before adding it.

WHY IT IS SAFE TO EDIT THESE FILES BY LINE, checked rather than assumed:
`columns:` is the last key in every model block in all 18 project ymls, indent is
4 for `columns:` and 6 for `- name:`, and there are no tabs, anchors or document
markers. Anything that does not match that shape makes the script ABORT rather
than guess.

THE CATALOGUE IS A CI ARTIFACT, not a repo file — `dbt_project/target/` is
ignored, and the copy on a dev machine is usually a stale partial one. Pointed at
a partial catalogue this script aborts rather than silently declaring almost
nothing. Get the real one from the most recent `data:build:main`:

    glab api "projects/rami.al-fahham%2Ffootball-data-pipeline/jobs?scope=success" \
      | python -c "import json,sys; print([j['id'] for j in json.load(sys.stdin) \
        if j['name']=='data:build:main'][0])"
    glab api "projects/rami.al-fahham%2Ffootball-data-pipeline/jobs/<id>/artifacts" > a.zip
    #  then extract dbt_project/target/catalog.json from it

Usage:

    python scripts/declare_missing_columns.py --catalog path/to/catalog.json
    python scripts/declare_missing_columns.py --catalog path/to/catalog.json --dry-run

Exit 1 on any guard failure AND when there is nothing to add. A bulk-edit script
that reports success while matching nothing is this repo's dominant failure shape
(#904), so "no work" is loud rather than green.

Fails CLOSED, in both of the senses that matter: nothing is written unless every
model verifies, AND each file is committed by an atomic rename, so a crash during
the write cannot leave a tracked yml truncated. The second half is not a
restatement of the first — `_verify` compares two strings in memory and has
already returned by the time the bytes move.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import pathlib
import re
import sys

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DBT_DIR = REPO_ROOT / "dbt_project"
MODELS_DIR = DBT_DIR / "models"

# Business meaning starts in core and flows downstream, so staging and base are out of scope.
IN_SCOPE_DIRS = ("3_core", "4_intermediate", "5_marts")

# Floor under the discovery: an empty walk would make "no missing columns" trivially true.
MIN_IN_SCOPE_MODELS = 40

MODEL_LINE = re.compile(r"^  - name:\s+(\S+)\s*$")
COLUMNS_KEY = re.compile(r"^    columns:\s*$")
# A `columns:` that is not a bare key has an unknown list end, so it is refused.
COLUMNS_KEY_ODD = re.compile(r"^    columns:\s*\S.*$")
INDENT_2_ITEM = re.compile(r"^  - ")
COLUMN_ENTRY_INDENT = "      "

# The indent is captured so a description lines up with whatever the file uses.
COLUMN_NAME_LINE = re.compile(r"^(\s+)- name:\s+(\S+)\s*$")

# Matches `{% docs %}` blocks as dbt does: a closing `{% enddocs %}` is required, and the body
# must not span another opener, or a stray opener would swallow the next real block.
DOC_BLOCK_RE = re.compile(
    r"{%\s*docs\s+(\w+)\s*%}(?:(?!{%\s*docs\s).)*?{%\s*enddocs\s*%}", re.S
)


DOC_REF_RE = re.compile(r"\{\{\s*doc\(\s*['\"](\w+)['\"]\s*\)\s*\}\}")


def _doc_reference(block: str) -> str:
    """The description pointing at a shared block; concatenated because `str.format` eats `{{`."""
    return "{{ doc('" + block + "') }}"


class Abort(Exception):
    """A guard tripped. Nothing is written."""


def _rel(path: pathlib.Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _newline(text: str, rel: str) -> str:
    """The file's own line terminator, so writing back does not convert every line."""
    crlf = text.count("\r\n")
    bare_lf = text.count("\n") - crlf
    if crlf and bare_lf:
        raise Abort(
            f"{rel}: mixed line endings ({crlf} CRLF, {bare_lf} LF). There is no "
            f"existing terminator to preserve, so writing either one would rewrite "
            f"half the file. Normalise it first, in its own commit."
        )
    return "\r\n" if crlf else "\n"


def _in_scope_models() -> set[str]:
    """Model names from the files, so the catalogue guard compares against an independent source."""
    names: set[str] = set()
    for layer in IN_SCOPE_DIRS:
        for path in (MODELS_DIR / layer).rglob("*.sql"):
            if "/target/" in f"/{_rel(path)}" or "/dbt_packages/" in f"/{_rel(path)}":
                continue
            names.add(path.stem)
    return names


def _declared() -> dict[str, tuple[pathlib.Path, list[str]]]:
    """model name -> (yml that declares it, declared column names), searching every project yml."""
    found: dict[str, tuple[pathlib.Path, list[str]]] = {}
    for path in sorted(DBT_DIR.rglob("*.yml")):
        rel = f"/{_rel(path)}"
        if "/target/" in rel or "/dbt_packages/" in rel:
            continue
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, UnicodeDecodeError, OSError) as exc:
            raise Abort(f"{_rel(path)}: cannot parse ({exc.__class__.__name__})") from exc
        if not isinstance(doc, dict):
            continue
        for model in doc.get("models") or []:
            if not isinstance(model, dict) or not isinstance(model.get("name"), str):
                continue
            name = model["name"]
            if name in found:
                raise Abort(
                    f"model {name!r} is declared twice: in {_rel(found[name][0])} "
                    f"and in {_rel(path)}. Refusing to guess which one to add to."
                )
            cols = [
                c["name"] for c in (model.get("columns") or [])
                if isinstance(c, dict) and isinstance(c.get("name"), str)
            ]
            found[name] = (path, cols)
    return found


def _catalog_columns(catalog_path: pathlib.Path) -> dict[str, list[str]]:
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        raise Abort(f"{catalog_path}: cannot read ({exc.__class__.__name__})") from exc
    out: dict[str, list[str]] = {}
    for uid, node in (catalog.get("nodes") or {}).items():
        if not uid.startswith("model."):
            continue
        cols = sorted((node.get("columns") or {}).values(), key=lambda c: c.get("index", 0))
        out[uid.rsplit(".", 1)[-1]] = [c["name"] for c in cols]
    return out


def _plan(catalog_path: pathlib.Path) -> dict[str, tuple[pathlib.Path, list[str]]]:
    """What to add, per model. Every guard that can refuse the run lives here."""
    models = _in_scope_models()
    if len(models) < MIN_IN_SCOPE_MODELS:
        raise Abort(
            f"found only {len(models)} models under {'/'.join(IN_SCOPE_DIRS)}, "
            f"expected at least {MIN_IN_SCOPE_MODELS}. The layout has moved, or this "
            f"is not the repo root. Refusing to run against a broken walk."
        )

    declared = _declared()
    catalog = _catalog_columns(catalog_path)

    # A partial dev catalogue would declare almost nothing and still report success.
    absent = sorted(models - catalog.keys())
    if absent:
        raise Abort(
            f"the catalogue is missing {len(absent)} of {len(models)} in-scope models, "
            f"so it does not describe this warehouse: {', '.join(absent[:5])}"
            f"{' ...' if len(absent) > 5 else ''}\n"
            f"  This is almost always a stale or dev-target catalog.json. Fetch the "
            f"artifact from the most recent data:build:main, see the module docstring."
        )

    undeclared = sorted(models - declared.keys())
    if undeclared:
        raise Abort(
            f"{len(undeclared)} in-scope models are in no yml at all: "
            f"{', '.join(undeclared)}\n"
            f"  Object-level coverage is #82 MR1's rule and check_description_hygiene.py "
            f"enforces it. Add the model with a description first."
        )

    plan: dict[str, tuple[pathlib.Path, list[str]]] = {}
    for name in sorted(models):
        path, already = declared[name]
        have = {c.lower() for c in already}
        missing = [c for c in catalog[name] if c.lower() not in have]
        if missing:
            plan[name] = (path, missing)
    return plan


def _insert(lines: list[str], model: str, new_columns: list[str]) -> list[str]:
    """Return `lines` with `new_columns` appended to `model`'s column list; unknown shapes abort."""
    starts = [i for i, line in enumerate(lines) if (m := MODEL_LINE.match(line)) and m.group(1) == model]
    if len(starts) != 1:
        raise Abort(f"expected exactly one `- name: {model}` line, found {len(starts)}")
    start = starts[0]

    end = len(lines)
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if not line.strip():
            continue
        if INDENT_2_ITEM.match(line) or (line[:1].strip() and not line.startswith(" ")):
            end = i
            break

    odd = [i for i in range(start, end) if COLUMNS_KEY_ODD.match(lines[i])]
    if odd:
        raise Abort(
            f"{model}: `columns:` at line {odd[0] + 1} is not a bare key "
            f"({lines[odd[0]].strip()!r}). Refusing to guess where its list ends."
        )

    keys = [i for i in range(start, end) if COLUMNS_KEY.match(lines[i])]
    if len(keys) > 1:
        raise Abort(f"{model}: {len(keys)} `columns:` keys in one model block")

    entries = [f"{COLUMN_ENTRY_INDENT}- name: {c}" for c in new_columns]

    if keys:
        # After the last non-blank line, so blank lines separating models stay put.
        last = max(
            (i for i in range(keys[0] + 1, end) if lines[i].strip()),
            default=keys[0],
        )
    else:
        last = max((i for i in range(start, end) if lines[i].strip()), default=start)
        entries = ["    columns:"] + entries

    return lines[: last + 1] + entries + lines[last + 1 :]


def _shared_blocks() -> set[str]:
    """Every `{% docs %}` block name under `models/`, the only path dbt resolves by default.

    A block found elsewhere would render as literal `{{ doc(...) }}` text in the warehouse.
    """
    blocks: set[str] = set()
    for path in sorted(MODELS_DIR.rglob("*.md")):
        rel = f"/{_rel(path)}"
        if "/target/" in rel or "/dbt_packages/" in rel:
            continue
        try:
            blocks.update(DOC_BLOCK_RE.findall(path.read_text(encoding="utf-8")))
        except (UnicodeDecodeError, OSError) as exc:
            raise Abort(f"{_rel(path)}: cannot read ({exc.__class__.__name__})") from exc
    return blocks


# Derived blocks carry an entity suffix because a metric stem does not say which entity owns it.
# An explicit table, not a name pattern: a wrong entry attaches the wrong definition, and an
# unlisted model aborts rather than defaulting.
MODEL_ENTITY: dict[str, str] = {
    "int_team_profile__yoy": "team",
    "mart_team_profile": "team",
    "int_team_season__metrics": "team",
    "int_team_season__metrics_cumulative": "team",
    "mart_team_season_insights": "team",
    "int_team_momentum_window": "team",
    "int_team_season_record": "team",
    "int_legs__team_match": "team",
    "int_team_season__deserved_vs_actual": "team",
    "mart_head_to_head": "team",
    "int_player_profile__yoy": "player",
    "mart_player_profile": "player",
    "int_player_club_season__metrics": "player",
    "int_player_season_record": "player",
}

_ENTITY_SUFFIXES = ("__team", "__player")


def _metric_wire_plan() -> tuple[dict, dict[str, list[str]]]:
    """Blank derived-metric columns -> their entity's block. file -> model -> col -> block.

    A derived name has only `__team` and/or `__player` blocks, so the block is chosen by the
    model's entity. A model absent from MODEL_ENTITY aborts; a missing entity block leaves the
    column blank and reported.
    """
    blocks = _shared_blocks()
    if not blocks:
        raise Abort(
            f"no {'{%'} docs %{'}'} blocks found under {_rel(MODELS_DIR)}; refusing to "
            f"run against an empty block set, which would make 'nothing to wire' "
            f"trivially true."
        )

    plan: dict[pathlib.Path, dict[str, dict[str, str]]] = {}
    unclassified: set[str] = set()
    no_block: dict[str, list[str]] = {}
    for path in sorted(DBT_DIR.rglob("*.yml")):
        rel = f"/{_rel(path)}"
        if "/target/" in rel or "/dbt_packages/" in rel:
            continue
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, UnicodeDecodeError, OSError) as exc:
            raise Abort(f"{_rel(path)}: cannot parse ({exc.__class__.__name__})") from exc
        if not isinstance(doc, dict):
            continue
        for model in doc.get("models") or []:
            if not isinstance(model, dict) or not isinstance(model.get("name"), str):
                continue
            for column in model.get("columns") or []:
                if not isinstance(column, dict):
                    continue
                name = column.get("name")
                if not isinstance(name, str) or (column.get("description") or "").strip():
                    continue
                if name in blocks:
                    continue        # --wire-shared-docs owns names with a bare block
                if not any(name + s in blocks for s in _ENTITY_SUFFIXES):
                    continue
                entity = MODEL_ENTITY.get(model["name"])
                if entity is None:
                    unclassified.add(model["name"])
                    continue
                block = f"{name}__{entity}"
                if block not in blocks:
                    no_block.setdefault(block, []).append(model["name"])
                    continue
                plan.setdefault(path, {}).setdefault(model["name"], {})[name] = block
    if unclassified:
        raise Abort(
            "these models hold a derived-metric column but are absent from "
            "MODEL_ENTITY, so whether their columns are team- or player-scoped is "
            "unknown and this script will not default: " + ", ".join(sorted(unclassified))
        )
    return plan, no_block


def _block_bodies() -> dict[str, str]:
    """Block name -> whitespace-normalised body, which the promote mode compares to column text."""
    bodies: dict[str, str] = {}
    for path in sorted(MODELS_DIR.rglob("*.md")):
        rel = f"/{_rel(path)}"
        if "/target/" in rel or "/dbt_packages/" in rel:
            continue
        text = path.read_text(encoding="utf-8")
        for match in DOC_BLOCK_RE.finditer(text):
            body = match.group(0)
            body = body[body.index("%}") + 2:]
            body = body[: body.rindex("{%")]
            bodies[match.group(1)] = " ".join(body.split())
    return bodies


def _promote_plan() -> tuple[dict, list[str]]:
    """Sites restating a block inline -> a reference to it. file -> model -> col -> (block, line).

    A site is planned only when the block's whitespace-normalised body equals the description it
    replaces; a differing site would be an edit, so it is reported and skipped. A description
    that is not a single quoted line is skipped too.
    """
    bodies = _block_bodies()
    if not bodies:
        raise Abort(
            f"no {'{%'} docs %{'}'} blocks found under {_rel(MODELS_DIR)}; refusing to "
            f"run against an empty block set, which would make 'nothing to promote' "
            f"trivially true."
        )

    plan: dict[pathlib.Path, dict[str, dict[str, tuple[str, str]]]] = {}
    skipped: list[str] = []
    for path in sorted(DBT_DIR.rglob("*.yml")):
        rel = f"/{_rel(path)}"
        if "/target/" in rel or "/dbt_packages/" in rel:
            continue
        raw = path.read_text(encoding="utf-8")
        try:
            doc = yaml.safe_load(raw)
        except (yaml.YAMLError, UnicodeDecodeError, OSError) as exc:
            raise Abort(f"{_rel(path)}: cannot parse ({exc.__class__.__name__})") from exc
        if not isinstance(doc, dict):
            continue
        lines = raw.split(_newline(raw, _rel(path)))
        for model in doc.get("models") or []:
            if not isinstance(model, dict) or not isinstance(model.get("name"), str):
                continue
            for column in model.get("columns") or []:
                if not isinstance(column, dict):
                    continue
                name = column.get("name")
                text = (column.get("description") or "").strip()
                if not isinstance(name, str) or name not in bodies or not text:
                    continue
                if DOC_REF_RE.search(text):
                    continue
                flat = " ".join(text.split())
                if flat != bodies[name]:
                    skipped.append(
                        f"{_rel(path)} :: {model['name']}.{name} - its text is NOT the "
                        f"block's text, so replacing it would REWRITE, not promote"
                    )
                    continue
                lo, hi = _model_block(lines, model["name"])
                hits = [ln for ln in lines[lo:hi]
                        if (m := DESCRIPTION_LINE.match(ln))
                        and " ".join(m.group(2)[1:-1].split()) == flat]
                if len(hits) != 1:
                    skipped.append(
                        f"{_rel(path)} :: {model['name']}.{name} - its description is not "
                        f"one uniquely identifiable quoted line inside its own model "
                        f"({len(hits)} candidates); a folded scalar is for a human"
                    )
                    continue
                plan.setdefault(path, {}).setdefault(model["name"], {})[name] = (
                    name, hits[0])
    return plan, skipped


def _expect_promoted(before: str, per_model: dict) -> object:
    doc = yaml.safe_load(before)
    for model in doc.get("models") or []:
        if not isinstance(model, dict) or model.get("name") not in per_model:
            continue
        wanted = per_model[model["name"]]
        for column in model.get("columns") or []:
            if isinstance(column, dict) and column.get("name") in wanted:
                column["description"] = _doc_reference(wanted[column["name"]][0])
    return doc


def _ambiguous_names(yml_docs: list[tuple[pathlib.Path, object]]) -> dict[str, set[str]]:
    """Column names that ALREADY reference more than one block, with those blocks.

    Wiring by name assumes one name means one thing; `league_code` is the competition almost
    everywhere but ingest provenance on global player events. No mechanical rule tells them
    apart, so a name already pointing at two blocks is left to a human.
    """
    seen: dict[str, set[str]] = {}
    for _path, doc in yml_docs:
        if not isinstance(doc, dict):
            continue
        for model in doc.get("models") or []:
            if not isinstance(model, dict):
                continue
            for column in model.get("columns") or []:
                if not isinstance(column, dict):
                    continue
                name = column.get("name")
                ref = DOC_REF_RE.search(column.get("description") or "")
                if isinstance(name, str) and ref:
                    seen.setdefault(name, set()).add(ref.group(1))
    return {name: refs for name, refs in seen.items() if len(refs) > 1}


def _wire_plan() -> tuple[dict[pathlib.Path, dict[str, dict[str, str]]], dict[str, set[str]]]:
    """Which blank columns share a block's name. file -> model -> column -> block.

    Returns the plan and the ambiguous names withheld, for the caller to report. Only blank
    columns are planned: a column that already carries text may deliberately point elsewhere.
    """
    blocks = _shared_blocks()
    if not blocks:
        raise Abort(
            f"no {'{%'} docs %{'}'} blocks found under {_rel(MODELS_DIR)}. Either the "
            f"shared definitions have moved or the walk is broken; refusing to run "
            f"against an empty block set, which would make 'nothing to wire' trivially true."
        )

    yml_docs: list[tuple[pathlib.Path, object]] = []
    for path in sorted(DBT_DIR.rglob("*.yml")):
        rel = f"/{_rel(path)}"
        if "/target/" in rel or "/dbt_packages/" in rel:
            continue
        try:
            yml_docs.append((path, yaml.safe_load(path.read_text(encoding="utf-8"))))
        except (yaml.YAMLError, UnicodeDecodeError, OSError) as exc:
            raise Abort(f"{_rel(path)}: cannot parse ({exc.__class__.__name__})") from exc

    ambiguous = _ambiguous_names(yml_docs)

    plan: dict[pathlib.Path, dict[str, dict[str, str]]] = {}
    withheld: dict[str, set[str]] = {}
    for path, doc in yml_docs:
        if not isinstance(doc, dict):
            continue
        for model in doc.get("models") or []:
            if not isinstance(model, dict) or not isinstance(model.get("name"), str):
                continue
            for column in model.get("columns") or []:
                if not isinstance(column, dict):
                    continue
                name = column.get("name")
                if name not in blocks:
                    continue
                if (column.get("description") or "").strip():
                    continue
                if name in ambiguous:
                    withheld[name] = ambiguous[name]
                    continue
                plan.setdefault(path, {}).setdefault(model["name"], {})[name] = name
    return plan, withheld


def _insert_description(lines: list[str], model: str,
                        per_column: dict[str, str]) -> list[str]:
    """Add a `description:` line directly after each named column's `- name:` line."""
    starts = [i for i, line in enumerate(lines)
              if (m := MODEL_LINE.match(line)) and m.group(1) == model]
    if len(starts) != 1:
        raise Abort(f"expected exactly one `- name: {model}` line, found {len(starts)}")
    start = starts[0]

    end = len(lines)
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if not line.strip():
            continue
        if INDENT_2_ITEM.match(line) or (line[:1].strip() and not line.startswith(" ")):
            end = i
            break

    remaining = dict(per_column)
    out = list(lines)
    # Bottom-up, because every insertion shifts the lines after it.
    for i in range(end - 1, start, -1):
        matched = COLUMN_NAME_LINE.match(out[i])
        if not matched:
            continue
        indent, column = matched.group(1), matched.group(2)
        block = remaining.pop(column, None)
        if block is None:
            continue
        out.insert(i + 1, f"{indent}  description: \"{_doc_reference(block)}\"")

    if remaining:
        raise Abort(
            f"{model}: could not find a `- name:` line for "
            f"{', '.join(sorted(remaining))} inside its own block"
        )
    return out


# A `description:` on one physical line; folded, block and wrapped values do not match because
# rewriting those by line mangles the file.
DESCRIPTION_LINE = re.compile(r'^(\s+)description:\s*(".*"|\'.*\')\s*$')


def _model_block(lines: list[str], model: str) -> tuple[int, int]:
    """The half-open line range of one model's entry; descriptions are unique only per model."""
    starts = [i for i, line in enumerate(lines)
              if (m := MODEL_LINE.match(line)) and m.group(1) == model]
    if len(starts) != 1:
        raise Abort(f"expected exactly one `- name: {model}` line, found {len(starts)}")
    start = starts[0]
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if not line.strip():
            continue
        if INDENT_2_ITEM.match(line) or (line[:1].strip() and not line.startswith(" ")):
            return start, i
    return start, len(lines)


def _replace_description(lines: list[str], model: str,
                         per_column: dict[str, tuple[str, str]]) -> list[str]:
    """Swap each named column's `description:` value for a reference to its block.

    `per_column` maps column -> (block, expected line); the line is re-checked before the swap so a
    file changed since planning is refused.
    """
    start, end = _model_block(lines, model)
    remaining = dict(per_column)
    out = list(lines)
    for i in range(start + 1, end):
        matched = COLUMN_NAME_LINE.match(out[i])
        if not matched:
            continue
        indent, column = matched.group(1), matched.group(2)
        planned = remaining.pop(column, None)
        if planned is None:
            continue
        block, expected_line = planned
        # Search the column's own lines, since `tests:` may legally precede `description:`.
        stop = end
        for k in range(i + 1, end):
            if COLUMN_NAME_LINE.match(out[k]):
                stop = k
                break
        found = [k for k in range(i + 1, stop) if out[k] == expected_line]
        if len(found) != 1:
            raise Abort(
                f"{model}.{column}: expected exactly one line matching the description "
                f"this run planned to replace, inside that column's own entry; found "
                f"{len(found)}. Re-run the plan against the current file rather than "
                f"writing over something unexamined."
            )
        out[found[0]] = f"{indent}  description: \"{_doc_reference(block)}\""

    if remaining:
        raise Abort(
            f"{model}: could not find a `- name:` line for "
            f"{', '.join(sorted(remaining))} inside its own block"
        )
    return out


def _verify(before: str, after: str, expected: object, rel: str, newline: str,
            replaceable: frozenset[str] = frozenset()) -> None:
    """Two independent proofs that nothing but the planned change happened.

    The textual one catches a reformat, reorder or dropped line; the structural one catches an
    addition under the wrong model or column. `expected` is the parsed file the caller intends.
    """
    old_lines, new_lines = before.split(newline), after.split(newline)
    ops = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False).get_opcodes()
    bad = []
    for op, i1, i2, j1, j2 in ops:
        if op in ("equal", "insert"):
            continue
        # `replaceable` is the exact set of lines the run planned to swap; empty means append-only.
        # `all`, not `any`: with `any` an unplanned line merged into the same opcode would ride
        # along, and the structural check is blind to a reformat.
        if op == "replace" and all(old_lines[k] in replaceable for k in range(i1, i2)):
            continue
        bad.append((op, i1))
    if bad:
        raise Abort(
            f"{rel}: refusing to write, the change is not append-only and is not one "
            f"of the {len(replaceable)} replacement(s) this run planned. "
            f"{len(bad)} unexpected edit(s), first is {bad[0][0]} at line {bad[0][1] + 1}."
        )

    old_doc = yaml.safe_load(before)
    new_doc = yaml.safe_load(after)
    if new_doc != expected:
        raise Abort(
            f"{rel}: refusing to write, the parsed result is not the old file plus "
            f"exactly the intended change. Something moved."
        )
    if old_doc == new_doc:
        raise Abort(f"{rel}: refusing to write, nothing changed, but work was planned.")


def _expect_declared(before: str, additions: dict[str, list[str]]) -> object:
    expected = yaml.safe_load(before)
    for model in expected.get("models") or []:
        extra = additions.get(model.get("name"))
        if extra:
            model.setdefault("columns", [])
            model["columns"].extend({"name": c} for c in extra)
    return expected


def _expect_wired(before: str, wiring: dict[str, dict[str, str]]) -> object:
    expected = yaml.safe_load(before)
    for model in expected.get("models") or []:
        per_column = wiring.get(model.get("name"))
        if not per_column:
            continue
        for column in model.get("columns") or []:
            block = per_column.get(column.get("name"))
            if block:
                column["description"] = _doc_reference(block)
    return expected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--catalog",
        type=pathlib.Path,
        default=DBT_DIR / "target" / "catalog.json",
        help="dbt catalog.json describing the PRODUCTION warehouse (a CI artifact).",
    )
    parser.add_argument(
        "--wire-shared-docs",
        action="store_true",
        help="Instead of declaring names, point every blank column whose name matches a "
             "{% docs %} block at that block. Needs no catalogue: the repo already holds "
             "both halves.",
    )
    parser.add_argument(
        "--wire-metric-docs",
        action="store_true",
        help="Point every blank DERIVED metric column (a catalogue metric plus a standard "
             "affix) at the generated block for its model's entity. Needs no catalogue.",
    )
    parser.add_argument(
        "--promote-shared-docs",
        action="store_true",
        help="Replace an inline description that RESTATES a docs block with a reference to "
             "it. Refuses any site whose text is not the block's text, so it promotes and "
             "never rewrites.",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Report what would be added; write nothing."
    )
    args = parser.parse_args()

    if args.promote_shared_docs:
        if args.wire_shared_docs or args.wire_metric_docs:
            print("declare_missing_columns: run one mode at a time so each diff is "
                  "attributable.", file=sys.stderr)
            return 1
        return _main_promote(args)
    if args.wire_shared_docs and args.wire_metric_docs:
        print("declare_missing_columns: --wire-shared-docs and --wire-metric-docs are "
              "separate passes over the same files; run them one at a time so each "
              "diff is attributable.", file=sys.stderr)
        return 1
    if args.wire_shared_docs:
        return _main_wire(args)
    if args.wire_metric_docs:
        return _main_metric_wire(args)

    try:
        plan = _plan(args.catalog)
    except Abort as exc:
        print(f"declare_missing_columns: {exc}", file=sys.stderr)
        return 1

    total = sum(len(cols) for _, cols in plan.values())
    if not total:
        print(
            "declare_missing_columns: nothing to add. Every column in core, "
            "intermediate and marts is already declared.\n"
            "  If you expected work, the catalogue is older than the models.",
            file=sys.stderr,
        )
        return 1

    by_file: dict[pathlib.Path, dict[str, list[str]]] = {}
    for model, (path, cols) in plan.items():
        by_file.setdefault(path, {})[model] = cols

    print(f"{total} columns to declare, across {len(plan)} models in {len(by_file)} files:")
    for path in sorted(by_file):
        n = sum(len(c) for c in by_file[path].values())
        print(f"  {n:5d}  {_rel(path)}  ({len(by_file[path])} models)")

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return 0

    return _write_files(by_file, _insert, _expect_declared, "column entries")


def _main_promote(args) -> int:
    """`--promote-shared-docs`: point a site that restates a block at the block."""
    try:
        by_file, skipped = _promote_plan()
    except Abort as exc:
        print(f"declare_missing_columns: {exc}", file=sys.stderr)
        return 1

    if skipped:
        print(f"NOT PROMOTED, {len(skipped)} site(s) this script will not touch:")
        for line in sorted(skipped):
            print(f"  {line}")
        print()

    total = sum(len(c) for payload in by_file.values() for c in payload.values())
    if not total:
        print(
            "declare_missing_columns: nothing to promote. No column restates a block "
            "whose text it matches exactly.",
            file=sys.stderr,
        )
        return 1

    print(f"{total} columns to promote, across {len(by_file)} files:")
    for path in sorted(by_file):
        n = sum(len(c) for c in by_file[path].values())
        print(f"  {n:5d}  {_rel(path)}  ({len(by_file[path])} models)")

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return 0

    return _write_files(by_file, _replace_description, _expect_promoted, "promotions")


def _main_metric_wire(args) -> int:
    """`--wire-metric-docs`: point blank derived columns at their entity's block."""
    try:
        by_file, no_block = _metric_wire_plan()
    except Abort as exc:
        print(f"declare_missing_columns: {exc}", file=sys.stderr)
        return 1

    if no_block:
        left = sum(len(m) for m in no_block.values())
        print(f"LEFT BLANK, {left} column(s): the catalogue does not define these metrics "
              f"for the entity that uses them, so there is no block to point at.")
        for block, models in sorted(no_block.items()):
            print(f"  {block} would be needed by: {', '.join(sorted(set(models)))}")
        print()

    total = sum(len(c) for payload in by_file.values() for c in payload.values())
    if not total:
        print(
            "declare_missing_columns: nothing to wire. Every blank derived metric "
            "column already references its entity's block.",
            file=sys.stderr,
        )
        return 1

    print(f"{total} columns to wire, across {len(by_file)} files:")
    for path in sorted(by_file):
        n = sum(len(c) for c in by_file[path].values())
        print(f"  {n:5d}  {_rel(path)}  ({len(by_file[path])} models)")

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return 0

    return _write_files(by_file, _insert_description, _expect_wired, "doc references")


def _main_wire(args) -> int:
    """`--wire-shared-docs`: point blank shared-name columns at their block."""
    try:
        by_file, withheld = _wire_plan()
    except Abort as exc:
        print(f"declare_missing_columns: {exc}", file=sys.stderr)
        return 1

    if withheld:
        print(f"WITHHELD, {len(withheld)} ambiguous name(s) this script will not guess at:")
        for name, refs in sorted(withheld.items()):
            print(f"  {name} already means {len(refs)} different things: "
                  f"{', '.join(sorted(refs))}")
        print("  Decide these per site and write the reference by hand.\n")

    total = sum(len(c) for payload in by_file.values() for c in payload.values())
    if not total:
        print(
            "declare_missing_columns: nothing to wire. Every column whose name has a "
            "shared definition already references one.",
            file=sys.stderr,
        )
        return 1

    print(f"{total} columns to wire, across {len(by_file)} files:")
    for path in sorted(by_file):
        n = sum(len(c) for c in by_file[path].values())
        print(f"  {n:5d}  {_rel(path)}  ({len(by_file[path])} models)")

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return 0

    return _write_files(by_file, _insert_description, _expect_wired, "doc references")


def _write_files(by_file: dict, insert_fn, expect_fn, noun: str) -> int:
    """Apply one planned change per file, verify it, and commit it atomically, for every mode."""
    for path in sorted(by_file):
        payload = by_file[path]
        # newline="" keeps the file's own terminators; `open()` because `read_text` only accepts
        # `newline` from Python 3.13.
        with path.open(encoding="utf-8", newline="") as fh:
            before = fh.read()
        try:
            nl = _newline(before, _rel(path))
            lines = before.split(nl)
            # The lines this run planned to replace; empty for the append-only modes. The declare
            # payload is model -> list of names, so both payload shapes must be tolerated.
            replaceable = frozenset(
                planned[1]
                for per_column in payload.values() if isinstance(per_column, dict)
                for planned in per_column.values() if isinstance(planned, tuple)
            )
            # Sorted only so a re-run produces an identical diff.
            for model in sorted(payload):
                lines = insert_fn(lines, model, payload[model])
            after = nl.join(lines)
            _verify(before, after, expect_fn(before, payload), _rel(path), nl, replaceable)
        except Abort as exc:
            print(f"declare_missing_columns: {_rel(path)}: {exc}", file=sys.stderr)
            return 1
        # Atomic per file: a sibling temp is fsynced then renamed over the original, so a crash
        # cannot leave a tracked yml truncated. The `.tmp` name is outside the `*.yml` globs.
        tmp = path.with_name(path.name + ".tmp")
        try:
            with tmp.open("w", encoding="utf-8", newline="") as fh:
                fh.write(after)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
        except OSError as exc:
            tmp.unlink(missing_ok=True)
            print(
                f"declare_missing_columns: {_rel(path)}: write failed, the original "
                f"is untouched ({exc.__class__.__name__}: {exc})",
                file=sys.stderr,
            )
            return 1

    written = sum(len(v) for payload in by_file.values() for v in payload.values())
    # A promote run is supposed to show deletions, so the acceptance message differs by mode.
    replaced = sum(
        1
        for payload in by_file.values()
        for per_column in payload.values() if isinstance(per_column, dict)
        for planned in per_column.values() if isinstance(planned, tuple)
    )
    if replaced:
        print(f"\nWrote {written} {noun}. `git diff --numstat` must show EXACTLY "
              f"{replaced} deletion(s), one per replaced description, and no others.")
    else:
        print(f"\nWrote {written} {noun}. `git diff --numstat` must show 0 deletions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
