"""Mechanical gate over dbt `description:` fields: banned phrasing, length and coverage.

Patterns match annotation forms, not ordinary verbs, and length is measured on the rendered text.
"""
from __future__ import annotations

import pathlib
import re
import sys

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DBT_DIR = REPO_ROOT / "dbt_project"

# Floors under the extraction: a walk that matches nothing would otherwise pass green.
MIN_DESCRIPTIONS = 400

# Floors under the coverage discovery, so "everything is described" cannot become trivially true.
MIN_MODELS = 50
MIN_SOURCE_TABLES = 5
MIN_LISTED_COLUMNS = 800

# BigQuery's own maxima; exceeding either rejects the DDL once `persist_docs` is on.
MAX_COLUMN_CHARS = 1024
MAX_RELATION_CHARS = 16384

DOC_REF_RE = re.compile(r"\{\{\s*doc\(\s*['\"](\w+)['\"]\s*\)\s*\}\}")
# The body must not span another opener, or a stray `{% docs x %}` swallows the next real block.
DOC_BLOCK_RE = re.compile(
    r"\{%\s*docs\s+(\w+)\s*%\}((?:(?!\{%\s*docs\s).)*?)\{%\s*enddocs\s*%\}", re.S
)
_MAX_DOC_DEPTH = 5

RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "issue reference",
        re.compile(r"(?:(?<![A-Za-z0-9])#\d+|\bGAP-\d+|(?<![A-Za-z0-9])![0-9]+)"),
        "a tracker id points at a decision, not at the data; most point at the "
        "unreachable GitHub tracker and are already dead links",
    ),
    (
        "ISO date",
        re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
        "git holds history losslessly; a hand-copied date starts rotting at once",
    ),
    (
        "dated update stamp",
        # Annotation form only; `corrections` and `corrected` as ordinary verbs must not match.
        re.compile(r"\b(?:UPDATED|CORRECTED|SUPERSEDED)\b|\b(?:updated|corrected)\s+20\d\d"),
        "an update stamp is a changelog entry; the changelog is git",
    ),
    (
        "decision language",
        # No bare `ruled`/`ruling`: "goal ruled out for offside" is football, not a decision log.
        re.compile(r"\bCPO\b|\bSLATED FOR\b|\ban earlier (?:version|draft)\b"
                   r"|\bused to say\b"),
        "rulings belong in .claude/task/escalations.log, open questions in the "
        "tracker, design rationale in layering.md",
    ),
    (
        "downstream-consumer claim",
        # A class of phrasings: "has NO consumer today" must match like "no dbt model reads this".
        re.compile(
            r"\b(?:only|single|sole)\s+(?:reader|consumer)s?\b"
            r"|\b(?:no|zero)\s+(?:dbt\s+model\s+|downstream\s+)?(?:reader|consumer)s?\b"
            r"|\bno dbt model reads\b"
            r"|\bnothing\s+downstream\b"
            r"|\bdownstream of this\b"
            r"|\bREAD by\b"
            # "feeds <identifier>" with a snake_case target catches a named model or column,
            # not ordinary prose such as `feeds the calculation`.
            r"|\b(?:feeds|enriches|powers)\s+(?:the\s+)?[a-z]+_[a-z_]+",
            re.IGNORECASE,
        ),
        "upstream is fixed in the SQL; downstream changes whenever anyone adds a "
        "model and nobody updates the prose. Three such claims were false at once. "
        "`dbt ls --select <model>+` answers it correctly and for free",
    ),
    (
        "severity emoji",
        re.compile(r"[⚠⛔⭐✅\U0001F300-\U0001FAFF]"),
        "a description states what the data means; it is not an annotated argument",
    ),
)


def _docs_blocks() -> dict[str, str]:
    """Every `{% docs %}` block under `models/`, the only path dbt resolves blocks from."""
    # Derived from DBT_DIR at call time so monkeypatching DBT_DIR alone repoints the whole gate.
    blocks: dict[str, str] = {}
    for path in sorted((DBT_DIR / "models").rglob("*.md")):
        rel = _rel(path)
        if "/target/" in f"/{rel}" or "/dbt_packages/" in f"/{rel}":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for name, body in DOC_BLOCK_RE.findall(text):
            blocks[name] = " ".join(body.split())
    return blocks


def _render(flat: str, blocks: dict[str, str]) -> tuple[str, list[str]]:
    """The description as persist_docs stores it, plus unresolved names; blocks may nest."""
    missing: list[str] = []
    text = flat
    for _ in range(_MAX_DOC_DEPTH):
        if not DOC_REF_RE.search(text):
            break

        def _sub(match: re.Match[str]) -> str:
            name = match.group(1)
            if name not in blocks:
                missing.append(name)
                return ""          # dropped, so the loop terminates
            return blocks[name]

        text = DOC_REF_RE.sub(_sub, text)
    else:
        if DOC_REF_RE.search(text):
            missing.append("<circular or deeper than %d>" % _MAX_DOC_DEPTH)

    return " ".join(text.split()), missing


def _rel(path: pathlib.Path) -> str:
    """Repo-relative path, or the absolute one when it is not under the repo."""
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _walk(node: object, where: str, is_column: bool,
          out: list[tuple[str, str, bool]]) -> None:
    """Collect (path, description, is_column) for every description in a tree."""
    if isinstance(node, dict):
        name = node.get("name")
        here = f"{where}/{name}" if isinstance(name, str) else where
        for key, value in node.items():
            if key == "description" and isinstance(value, str):
                out.append((here, value, is_column))
            elif key == "columns":
                _walk(value, here, True, out)
            else:
                _walk(value, here, is_column, out)
    elif isinstance(node, list):
        for item in node:
            _walk(item, where, is_column, out)


def _on_disk() -> tuple[set[str], set[str]]:
    """Model and seed names from the files, shared by the coverage check and the census line."""
    def keep(path: pathlib.Path) -> bool:
        rel = f"/{_rel(path)}"
        return "/target/" not in rel and "/dbt_packages/" not in rel

    models = {p.stem for p in (DBT_DIR / "models").rglob("*.sql") if keep(p)}
    seeds = {p.stem for p in (DBT_DIR / "seeds").rglob("*.csv") if keep(p)}
    return models, seeds


def _ambiguous_names(docs: list[tuple[str, pathlib.Path, object]]) -> dict[str, set[str]]:
    """Column names referencing more than one block; kept in step with `declare_missing_columns`."""
    seen: dict[str, set[str]] = {}
    for _rel, _path, doc in docs:
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


def _shared_block_coverage(docs: list[tuple[str, pathlib.Path, object]],
                           blocks: dict[str, str]) -> list[str]:
    """A column named like a docs block must reference some block; ambiguous names are skipped."""
    ambiguous = _ambiguous_names(docs)
    findings: list[str] = []
    for rel, _path, doc in docs:
        if not isinstance(doc, dict):
            continue
        for model in doc.get("models") or []:
            if not isinstance(model, dict):
                continue
            for column in model.get("columns") or []:
                if not isinstance(column, dict):
                    continue
                name = column.get("name")
                if not isinstance(name, str) or name not in blocks:
                    continue
                if name in ambiguous:
                    continue
                text = (column.get("description") or "").strip()
                if not text:
                    findings.append(
                        f"{rel} :: {model.get('name')}.{name} - blank, but a shared "
                        f"definition for {name!r} exists\n"
                        f"    fix: description: \"{{{{ doc('{name}') }}}}\""
                    )
                elif not DOC_REF_RE.search(text):
                    findings.append(
                        f"{rel} :: {model.get('name')}.{name} - restates a shared "
                        f"definition instead of referencing it\n"
                        f"    why banned: restated definitions drift apart, which is how "
                        f"league_code came to be documented 76 times in 22 wordings"
                    )
    return findings


def _object_coverage(docs: list[tuple[str, pathlib.Path, object]]) -> list[str]:
    """Every model, seed and source table must have a description.

    Models and seeds come from the files on disk, so one missing from every yml is still caught;
    source tables come from the yml, since a source has no file.
    """
    findings: list[str] = []

    described_models: dict[str, str] = {}
    described_seeds: dict[str, str] = {}
    source_tables: dict[str, str] = {}

    for _rel_path, _path, doc in docs:
        if not isinstance(doc, dict):
            continue
        for key, sink in (("models", described_models), ("seeds", described_seeds)):
            for entry in doc.get(key) or []:
                if isinstance(entry, dict) and isinstance(entry.get("name"), str):
                    sink[entry["name"]] = str(entry.get("description") or "").strip()
        for source in doc.get("sources") or []:
            if not isinstance(source, dict):
                continue
            for table in source.get("tables") or []:
                if isinstance(table, dict) and isinstance(table.get("name"), str):
                    source_tables[table["name"]] = str(table.get("description") or "").strip()

    on_disk_models, on_disk_seeds = _on_disk()

    if len(on_disk_models) < MIN_MODELS or len(source_tables) < MIN_SOURCE_TABLES:
        findings.append(
            f"discovery looks broken: {len(on_disk_models)} model .sql files "
            f"(floor {MIN_MODELS}) and {len(source_tables)} source tables "
            f"(floor {MIN_SOURCE_TABLES})\n"
            "    why banned: a coverage check that finds nothing always passes"
        )
        return findings

    for name in sorted(on_disk_models):
        if not described_models.get(name):
            why = "declared in no yml" if name not in described_models else "description is empty"
            findings.append(
                f"model {name} - NO DESCRIPTION ({why})\n"
                "    why banned: engineering_standards.md section 2 requires one on every "
                "model, and persist_docs pushes it to BigQuery where people read it"
            )
    for name in sorted(on_disk_seeds):
        if not described_seeds.get(name):
            why = "declared in no yml" if name not in described_seeds else "description is empty"
            findings.append(
                f"seed {name} - NO DESCRIPTION ({why})\n"
                "    why banned: engineering_standards.md section 2 requires one on every seed"
            )
    for name in sorted(source_tables):
        if not source_tables[name]:
            findings.append(
                f"source {name} - NO DESCRIPTION\n"
                "    why banned: engineering_standards.md section 2 requires one on every source "
                "table; a raw table nobody has described is where the pipeline starts"
            )
    return findings


def _column_coverage(docs: list[tuple[str, pathlib.Path, object]]) -> list[str]:
    """Every column listed under a model's `columns:` must have a description or a doc reference."""
    findings: list[str] = []
    listed = 0
    for rel, _path, doc in docs:
        if not isinstance(doc, dict):
            continue
        for model in doc.get("models") or []:
            if not isinstance(model, dict) or not isinstance(model.get("name"), str):
                continue
            for column in model.get("columns") or []:
                if not isinstance(column, dict) or not isinstance(column.get("name"), str):
                    continue
                listed += 1
                if not str(column.get("description") or "").strip():
                    findings.append(
                        f"{rel} :: {model['name']}.{column['name']} - NO DESCRIPTION\n"
                        "    why banned: engineering_standards.md section 3.1 - a listed column "
                        "matters enough to test, so it says what it is or when it is NULL"
                    )
    if listed < MIN_LISTED_COLUMNS:
        findings.append(
            f"discovery looks broken: {listed} listed columns (floor {MIN_LISTED_COLUMNS})\n"
            "    why banned: a coverage check that finds nothing always passes"
        )
    return findings


def _parse_ymls() -> tuple[list[tuple[str, pathlib.Path, object]], list[str]]:
    """Parse every project .yml once, since PyYAML's loader dominates the gate's runtime."""
    docs: list[tuple[str, pathlib.Path, object]] = []
    unparseable: list[str] = []
    for path in sorted(DBT_DIR.rglob("*.yml")):
        rel = _rel(path)
        # dbt's compiled artifacts and installed packages are not ours to police.
        if "/target/" in f"/{rel}" or "/dbt_packages/" in f"/{rel}":
            continue
        # `read_text` is inside the try because a non-UTF-8 .yml raises UnicodeDecodeError.
        try:
            docs.append((rel, path, yaml.safe_load(path.read_text(encoding="utf-8"))))
        except (yaml.YAMLError, UnicodeDecodeError, OSError) as exc:
            unparseable.append(f"{rel}: {exc.__class__.__name__}")
    return docs, unparseable


def _collect(docs: list[tuple[str, pathlib.Path, object]]
             ) -> list[tuple[str, str, str, bool]]:
    """Every description in the parsed files. (file, path-within-file, text, is_column)."""
    found: list[tuple[str, str, str, bool]] = []
    for rel, path, doc in docs:
        collected: list[tuple[str, str, bool]] = []
        _walk(doc, path.stem, False, collected)
        found.extend((rel, where, text, is_col) for where, text, is_col in collected)
    return found


def main() -> int:
    # A finding can quote an emoji that a cp1252 console cannot encode; tests capture stdout.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    docs, unparseable = _parse_ymls()
    found = _collect(docs)
    findings: list[str] = []

    # Before the floor, which would otherwise blame the walk instead of the broken file.
    if unparseable:
        print(f"FAIL: {len(unparseable)} file(s) could not be parsed, so their "
              "descriptions are unchecked:")
        for bad in unparseable:
            print(f"  - {bad}")
        return 1

    # Before the floor, which would otherwise report a broken walk when nothing was written.
    coverage = _object_coverage(docs)
    if coverage:
        print(f"DESCRIPTION COVERAGE: {len(coverage)} object(s) with no description\n")
        for finding in coverage:
            print(f"  - {finding}")
        print("\nThe standard is dbt_project/docs/engineering_standards.md section 2.")
        return 1

    blocks = _docs_blocks()

    # Before the floor, which would otherwise report a broken walk for an unreferenced definition.
    shared = _shared_block_coverage(docs, blocks)
    if shared:
        print(f"SHARED DEFINITIONS: {len(shared)} column(s) not pointing at the "
              f"definition that already exists for their name\n")
        for finding in shared:
            print(f"  - {finding}")
        print("\nThe standard is dbt_project/docs/engineering_standards.md section 2, Form.")
        return 1

    # After the shared rule, so a blank column with a definition is told which one to reference.
    columns = _column_coverage(docs)
    if columns:
        print(f"COLUMN COVERAGE: {len(columns)} listed column(s) with no description\n")
        for finding in columns:
            print(f"  - {finding}")
        print("\nThe standard is dbt_project/docs/engineering_standards.md section 3.1.")
        return 1

    if len(found) < MIN_DESCRIPTIONS:
        print(f"FAIL: found only {len(found)} descriptions under {_rel(DBT_DIR)} "
              f"(floor {MIN_DESCRIPTIONS}). The walk has stopped matching - a gate "
              "over zero descriptions always passes.")
        return 1

    for rel, where, text, is_column in found:
        flat = " ".join(text.split())
        # Rules run on the rendered text so a banned phrase cannot hide inside a shared block.
        rendered, missing = _render(flat, blocks)

        for name in missing:
            findings.append(
                f"{rel} :: {where} - unresolved docs block: {name!r}\n"
                f"    why banned: dbt cannot compile a doc() reference with no block, "
                f"and the stored length cannot be known"
            )

        for name, pattern, why in RULES:
            hit = pattern.search(rendered)
            if hit:
                # `ascii()` keeps an emoji match printable.
                findings.append(
                    f"{rel} :: {where} - {name}: {ascii(hit.group(0))}\n"
                    f"    why banned: {why}"
                )

        limit = MAX_COLUMN_CHARS if is_column else MAX_RELATION_CHARS
        if len(rendered) > limit:
            kind = "column" if is_column else "model/seed"
            via_block = " (after expanding its docs block)" if len(rendered) != len(flat) else ""
            findings.append(
                f"{rel} :: {where} - over length: {len(rendered)} chars{via_block} "
                f"({kind} limit {limit})\n"
                f"    why banned: BigQuery rejects it, so persist_docs fails the build"
            )

    if findings:
        print(f"DESCRIPTION HYGIENE: {len(findings)} finding(s) "
              f"across {len(found)} descriptions\n")
        for finding in findings:
            print(f"  - {finding}")
        print("\nThe standard is dbt_project/docs/engineering_standards.md section 2.")
        return 1

    # Names exempt from the which-block rule are printed every run so the exemption stays visible.
    skipped = _ambiguous_names(docs)
    if skipped:
        print(f"NOT POLICED for WHICH block: {len(skipped)} column name(s) mean more than one "
              f"thing, so each site references the definition it carries by hand; every site "
              f"is still required to have one.")
        for name, refs in sorted(skipped.items()):
            print(f"  - {name}: {', '.join(sorted(refs))}")

    files = len({rel for rel, _, _, _ in found})
    cols = sum(1 for _, _, _, is_col in found if is_col)
    on_disk_models, on_disk_seeds = _on_disk()
    models, seeds = len(on_disk_models), len(on_disk_seeds)
    print(f"DESCRIPTION HYGIENE ok: {len(found)} descriptions across {files} files "
          f"({cols} column, {len(found) - cols} model/seed), {len(RULES)} rules, "
          f"{len(blocks)} docs blocks resolved, rendered lengths within "
          f"{MAX_COLUMN_CHARS}/{MAX_RELATION_CHARS}; "
          f"every one of {models} models and {seeds} seeds on disk is described, "
          f"and every listed model column")
    return 0


if __name__ == "__main__":
    sys.exit(main())
