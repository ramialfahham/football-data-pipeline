"""Declare columns that EXIST in the warehouse but appear in no `.yml`.

#82 MR2. `check_description_hygiene.py` checks the CONTENT of descriptions that
exist, and object-level PRESENCE since `!91`. Neither can see a column that is
declared nowhere at all: there is no yml entry to look at. Measured against
production on 2026-08-23, that was 979 columns across 40 models — more than the
1,236-column gap the issue reported, most of it invisible to every check we had.

This script writes their NAMES down, with no descriptions, so the real surface
becomes visible and the shared definitions can be wired into it. A name with no
text is an honest empty slot. Inventing text to fill it is the "thin filler" the
CPO ruled against on 2026-08-21, and it would be far harder to find and replace
later than an empty slot is.

APPEND-ONLY, AND THAT IS THE WHOLE POINT. It adds `- name:` entries and never
edits, reorders or reformats a line that is already there. That constraint is
what separates it from a general yml formatter, which is why insertion is done on
LINES and not by re-serialising YAML — every round-trip library reformats
something, and a diff nobody can read is a diff nobody can review. The guarantee
is checked twice before anything is written to disk (see `_verify`), and again by
the reviewer, for whom the acceptance test is simply that the diff has zero
deleted lines.

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

# The CPO's coverage scope, ruled 2026-08-21: "core, intermediate and marts ->
# business meaning starts in core downstream." Staging and base are deliberately
# out. Directory names, because that is what the layer contract is expressed in.
IN_SCOPE_DIRS = ("3_core", "4_intermediate", "5_marts")

# Floor under the DISCOVERY, same precedent as `check_description_hygiene.py`'s
# MIN_DESCRIPTIONS. A renamed directory or a changed layout could leave the walk
# matching nothing, and "no missing columns" would then be trivially true — the
# exact false-green this script exists to avoid producing. Set well under the 66
# models measured and well over zero.
MIN_IN_SCOPE_MODELS = 40

MODEL_LINE = re.compile(r"^  - name:\s+(\S+)\s*$")
COLUMNS_KEY = re.compile(r"^    columns:\s*$")
# Any `columns:` that is NOT a bare key — an inline list, a comment, anything.
# We do not know where the end of such a list is, so we refuse to touch it.
COLUMNS_KEY_ODD = re.compile(r"^    columns:\s*\S.*$")
INDENT_2_ITEM = re.compile(r"^  - ")
COLUMN_ENTRY_INDENT = "      "


class Abort(Exception):
    """A guard tripped. Nothing is written."""


def _rel(path: pathlib.Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _newline(text: str, rel: str) -> str:
    """The file's OWN line terminator, so writing back does not convert it.

    `core.autocrlf=true` on this machine and `.gitattributes` pins only `*.sh` and
    `Dockerfile`, so these ymls are CRLF in the working tree and LF in the object
    store. Reading with universal newlines and writing "\\n" therefore rewrites
    every terminator in the file, which is reformatting every line — and
    `git diff` shows it as zero deletions either way, so the one place you would
    look for it is blind to it.

    Not hypothetical here: `.gitattributes` exists because a CRLF working copy
    shipped a `\\r` into a container shebang under #39 and killed the 04:00 run,
    after passing every test and building a clean image.
    """
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
    """Model names taken from the FILES, not from an artifact.

    The repo is the authority on which models exist and which layer they are in;
    the catalogue is the authority on what the warehouse holds. Keeping those two
    questions on their own sources is what lets the catalogue guard below mean
    something — if both came from the same artifact it could only ever agree with
    itself.
    """
    names: set[str] = set()
    for layer in IN_SCOPE_DIRS:
        for path in (MODELS_DIR / layer).rglob("*.sql"):
            if "/target/" in f"/{_rel(path)}" or "/dbt_packages/" in f"/{_rel(path)}":
                continue
            names.add(path.stem)
    return names


def _declared() -> dict[str, tuple[pathlib.Path, list[str]]]:
    """model name -> (yml that declares it, column names already declared).

    Every project yml is searched, not only the ones under the in-scope layers: a
    model's schema file is conventionally beside it but nothing enforces that, and
    guessing the path would silently re-declare a column that is already there.
    """
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
    """model name -> column names, in the warehouse's own column order."""
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

    # THE PARTIAL-CATALOGUE GUARD, and it is the one that matters most in practice.
    # `dbt_project/target/catalog.json` on a dev machine is whatever the last local
    # `dbt docs generate` produced — on this machine that was 10 relations in
    # `dev_staging`/`dev_scratch`. Running against it would declare almost nothing
    # and report success.
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
    """Return `lines` with `new_columns` appended to `model`'s column list.

    Line-level on purpose — see the module docstring. Every shape this does not
    recognise aborts instead of guessing, because a wrong guess here rewrites a
    file nobody asked it to touch.
    """
    starts = [i for i, line in enumerate(lines) if (m := MODEL_LINE.match(line)) and m.group(1) == model]
    if len(starts) != 1:
        raise Abort(f"expected exactly one `- name: {model}` line, found {len(starts)}")
    start = starts[0]

    # The block runs to the next model entry at indent 2, or the next top-level
    # key, or the end of the file.
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
        # Insert after the last non-blank line of the existing list, so trailing
        # blank lines that separate models stay where the author put them.
        last = max(
            (i for i in range(keys[0] + 1, end) if lines[i].strip()),
            default=keys[0],
        )
    else:
        # No column list at all: create one at the end of the model block.
        last = max((i for i in range(start, end) if lines[i].strip()), default=start)
        entries = ["    columns:"] + entries

    return lines[: last + 1] + entries + lines[last + 1 :]


def _verify(before: str, after: str, additions: dict[str, list[str]], rel: str,
            newline: str) -> None:
    """Two independent proofs that nothing but an addition happened.

    They are deliberately different in kind. The first is textual and catches a
    reformat, a reorder or a dropped line even when the parsed result is
    equivalent. The second is structural and catches an addition landing under the
    wrong model, which the text check alone would happily accept.
    """
    ops = difflib.SequenceMatcher(
        None, before.split(newline), after.split(newline), autojunk=False
    ).get_opcodes()
    bad = [op for op in ops if op[0] not in ("equal", "insert")]
    if bad:
        raise Abort(
            f"{rel}: refusing to write, the change is not append-only. "
            f"{len(bad)} non-insert edit(s), first is {bad[0][0]} at line {bad[0][1] + 1}."
        )

    old_doc = yaml.safe_load(before)
    new_doc = yaml.safe_load(after)
    expected = yaml.safe_load(before)
    for model in expected.get("models") or []:
        extra = additions.get(model.get("name"))
        if extra:
            model.setdefault("columns", [])
            model["columns"].extend({"name": c} for c in extra)
    if new_doc != expected:
        raise Abort(
            f"{rel}: refusing to write, the parsed result is not the old file plus "
            f"exactly the new names. Something moved."
        )
    if old_doc == new_doc:
        raise Abort(f"{rel}: refusing to write, nothing changed, but additions were planned.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--catalog",
        type=pathlib.Path,
        default=DBT_DIR / "target" / "catalog.json",
        help="dbt catalog.json describing the PRODUCTION warehouse (a CI artifact).",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Report what would be added; write nothing."
    )
    args = parser.parse_args()

    try:
        plan = _plan(args.catalog)
    except Abort as exc:
        print(f"declare_missing_columns: {exc}", file=sys.stderr)
        return 1

    total = sum(len(cols) for _, cols in plan.values())
    if not total:
        # Loud, not green. See the module docstring.
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

    for path in sorted(by_file):
        additions = by_file[path]
        # newline="" so the file's own terminators reach us untranslated; see
        # `_newline`. Reading with the default would hide a CRLF file from us and
        # we would silently convert it. `open()` rather than `read_text`, which
        # only accepts `newline` from Python 3.13 and this project pins 3.11.
        with path.open(encoding="utf-8", newline="") as fh:
            before = fh.read()
        try:
            nl = _newline(before, _rel(path))
            lines = before.split(nl)
            # Name order, purely so a re-run produces an identical diff. It does
            # NOT matter to correctness: `_insert` re-locates its model in the
            # lines it is handed, so an earlier insertion cannot shift a later
            # one's anchor. An earlier version ordered these bottom-up and said
            # in a comment that it had to; mutation testing flipped the order and
            # every test stayed green, which is what showed the comment was false.
            for model in sorted(additions):
                lines = _insert(lines, model, additions[model])
            after = nl.join(lines)
            _verify(before, after, additions, _rel(path), nl)
        except Abort as exc:
            print(f"declare_missing_columns: {_rel(path)}: {exc}", file=sys.stderr)
            return 1
        # ATOMIC PER FILE. `path.open("w")` truncates at open time and the write
        # that follows is not one operation, so a crash between the two leaves a
        # TRACKED yml half-written. `_verify` cannot see that failure — it compares
        # two in-memory strings and has already returned by this point — so the
        # module's "nothing is written unless every model verifies" is true of a
        # guard tripping and says nothing about the write itself. That gap was
        # platform-reviewer's round-1 FAIL, and it is the one failure mode the
        # append-only promise is least able to survive.
        # Write a sibling temp, flush it all the way to disk, then rename over the
        # original: `os.replace` is atomic on POSIX and on Windows, and a sibling
        # shares the directory so the rename never crosses a filesystem. The temp
        # name ends `.tmp`, which `_declared()`'s `*.yml` glob cannot match, so a
        # leftover from a crash is inert rather than parsed as a schema file.
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

    print(f"\nWrote {total} column entries. `git diff --numstat` must show 0 deletions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
