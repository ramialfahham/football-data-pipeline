"""Description hygiene gate — MECHANICAL checks on dbt `description:` fields.

Enforces `dbt_project/docs/engineering_standards.md` §2, which is the authority;
this file is only the machine half of it. Descriptions had been used as a decision
log, and three were provably false — all three downstream-consumer claims, the one
kind of statement nobody keeps true by hand.

It checks only what a machine can decide without taste: issue refs, dated stamps,
decision language, downstream-consumer claims, severity emoji, and length. Whether
a description is any GOOD — grain, source, known limits — is a human's call.

Patterns match ANNOTATION forms, not ordinary verbs. A case-insensitive
`CORRECTED` hits "the country corrections from the seed"; a bare `ruled` hits
"goal ruled out for offside". A gate that fires on correct text gets weakened
rather than obeyed.

Length is measured on the RENDERED string, because `persist_docs` expands a
`{{ doc() }}` block into what it stores.

Exit 1 on any finding, and on a file it cannot read. Fails CLOSED.

Wired in `.gitlab-ci.yml` `validate:governance`, in `stop_gate.py`'s FAST_GATES
(so it fires at turn end, while the text is still in the file), and documented in
the `validate-local` skill. Those three are pinned against each other by
`test_fast_gates_and_validate_local_agree`.
"""
from __future__ import annotations

import pathlib
import re
import sys

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DBT_DIR = REPO_ROOT / "dbt_project"

# Floor under the extraction, enforced in the gate itself and not only in the
# tests. A YAML rename, a moved directory or a parser change could leave the walk
# matching nothing, and a gate over zero descriptions always passes green. Set
# well under the 616 the audit measured so ordinary deletion never trips it, and
# well over zero so a broken walk always does. Same precedent as
# `check_copy_gate.py`'s MIN_KEYS.
MIN_DESCRIPTIONS = 400

# Floors under the COVERAGE discovery, for the same reason as MIN_DESCRIPTIONS: if
# the file walk stops finding models or the yml walk stops finding source tables,
# "everything is described" becomes trivially true. Set well under the 97 models
# and 11 source tables measured, and well over zero.
MIN_MODELS = 50
MIN_SOURCE_TABLES = 5

# BigQuery's own maxima. Exceeding either rejects the DDL and fails the build once
# `persist_docs` is on. This rule exists to prevent that, nothing else — keeping a
# description short enough to read is a judgement, not something to fake with a
# threshold.
MAX_COLUMN_CHARS = 1024
MAX_RELATION_CHARS = 16384

# Blocks live in .md files, so this walk never sees them as descriptions; they are
# resolved into their call sites instead, and checked there.
DOC_REF_RE = re.compile(r"\{\{\s*doc\(\s*['\"](\w+)['\"]\s*\)\s*\}\}")
# ⚠ THE BODY MUST NOT SPAN ANOTHER OPENER, and a plain `(.*?)` does. A stray
# `{% docs x %}` with no closing tag matches lazily all the way to the NEXT
# block's `{% enddocs %}`, which both invents a block named `x` and swallows the
# real block behind it. That is not hypothetical: `engineering_standards.md:112`
# carries the literal text `{% docs name %}` inside a sentence explaining the
# syntax. It is inert today only because that file has no `{% enddocs %}` at all.
DOC_BLOCK_RE = re.compile(
    r"\{%\s*docs\s+(\w+)\s*%\}((?:(?!\{%\s*docs\s).)*?)\{%\s*enddocs\s*%\}", re.S
)
_MAX_DOC_DEPTH = 5

# Each rule is (name, compiled pattern, why it is banned). The reason travels with
# the rule so a future reader can judge it without archaeology, as
# `check_copy_gate.py` does.
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
        # ANNOTATION form only: shouty UPDATED/CORRECTED, or the same followed by a
        # year. `corrections` and `corrected` as ordinary verbs are NOT matched —
        # six legitimate uses exist in the cleaned text.
        re.compile(r"\b(?:UPDATED|CORRECTED|SUPERSEDED)\b|\b(?:updated|corrected)\s+20\d\d"),
        "an update stamp is a changelog entry; the changelog is git",
    ),
    (
        "decision language",
        # No bare `ruled`/`ruling` — "goal ruled out for offside" is football, not a
        # decision log. A recorded ruling is attributed to the owner's title, which
        # the first alternative catches.
        re.compile(r"\bCPO\b|\bSLATED FOR\b|\ban earlier (?:version|draft)\b"
                   r"|\bused to say\b"),
        "rulings belong in .claude/task/escalations.log, open questions in the "
        "tracker, design rationale in layering.md",
    ),
    (
        "downstream-consumer claim",
        # A class, not a list of instances seen so far: "has NO consumer today" is
        # the same defect as "no dbt model reads this" and must match too.
        re.compile(
            r"\b(?:only|single|sole)\s+(?:reader|consumer)s?\b"
            r"|\b(?:no|zero)\s+(?:dbt\s+model\s+|downstream\s+)?(?:reader|consumer)s?\b"
            r"|\bno dbt model reads\b"
            r"|\bnothing\s+downstream\b"
            r"|\bdownstream of this\b"
            r"|\bREAD by\b"
            # "feeds <identifier>" where the target is snake_case, so a named model
            # OR a named column is caught (`feeds fct_fixture`, `feeds shots_share_pct`)
            # while ordinary prose is not (`feeds the calculation`, `feeds into`).
            # Requiring a model prefix instead was tried and silently dropped a real
            # column-level claim.
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
    """Every `{% docs %}` block dbt can resolve, whitespace-collapsed.

    Needed because `persist_docs` renders a block into the description it pushes,
    so the length that reaches BigQuery is the RESOLVED one.

    ⚠ RESTRICTED TO `models/`, WHICH IS WHERE dbt LOOKS. `docs-paths` is unset in
    `dbt_project.yml`, so it defaults to `['models']` and `dbt_project/docs/` is
    invisible to dbt. An earlier version walked all of `dbt_project/`, which could
    find a block dbt cannot resolve — and a reference to one renders as literal
    `{{ doc(...) }}` text in the warehouse rather than failing loudly. The gate
    and dbt must agree on what a block IS, or the gate polices a different project.
    """
    # Derived from DBT_DIR at call time, not bound at import: the tests point the
    # whole gate at a tmp project by monkeypatching DBT_DIR alone, and a constant
    # captured at import would keep reading the real repo underneath them.
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
    """The description as persist_docs would store it, plus any unresolved names.

    Substitutes REPEATEDLY, because a block may itself reference another. A single
    pass would leave the inner tag literal, understating the length and never
    checking the nested block's own text. No such nesting exists today; the bound
    is what stops a cycle spinning.
    """
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
    """Repo-relative path, or the absolute one when it is not under the repo.

    `Path.relative_to` RAISES rather than returning the input, and that is not a
    hypothetical: the tests point `DBT_DIR` at a tmp directory, and a worktree or a
    symlinked checkout does the same in ordinary use. A gate that dies while
    formatting a path reports nothing at all.
    """
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _walk(node: object, where: str, is_column: bool,
          out: list[tuple[str, str, bool]]) -> None:
    """Collect (path, description, is_column) for every description in a tree.

    `is_column` tracks whether we are inside a `columns:` list, because BigQuery's
    limits differ by kind — see MAX_COLUMN_CHARS. It is set on descent into
    `columns:` and inherited from there down, so a column's nested keys stay
    column-scoped.
    """
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
    """Model and seed names taken from the FILES, with one set of exclusions.

    Defined once and used by both the coverage check and the census line it
    prints, so the number reported can never drift from the number enforced —
    a separate glob for the census can quietly drop the `dbt_packages/` exclusion.
    """
    def keep(path: pathlib.Path) -> bool:
        rel = f"/{_rel(path)}"
        return "/target/" not in rel and "/dbt_packages/" not in rel

    models = {p.stem for p in (DBT_DIR / "models").rglob("*.sql") if keep(p)}
    seeds = {p.stem for p in (DBT_DIR / "seeds").rglob("*.csv") if keep(p)}
    return models, seeds


def _ambiguous_names(docs: list[tuple[str, pathlib.Path, object]]) -> dict[str, set[str]]:
    """Column names that already reference MORE THAN ONE block, with those blocks.

    Kept deliberately identical in behaviour to `declare_missing_columns._ambiguous_names`,
    and pinned to it by `test_the_two_ambiguity_rules_agree`, because the generator and
    the gate must hold the same opinion about which names a machine may decide. If the
    generator refuses to fill a name in, the gate must not then demand that it be filled.
    """
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
    """A column whose NAME is a docs block must reference a docs block.

    Enforces `engineering_standards.md` section 2, Form: "a column documented in
    more than one model gets ONE docs block, referenced from each. Do not restate
    it." That rule was written down and enforced nowhere; measured when this was
    added, 195 columns whose name had a definition sitting in
    `models/docs/shared_columns.md` were blank, against 99 that referenced theirs.
    Hand-referencing does not hold at this scale, which is why docs blocks are
    allowed only with a mechanism behind them.

    ⚠ IT DOES NOT POLICE *WHICH* BLOCK, deliberately, and that is what removes the
    need for an exemption list. A column named `league_code` that actually carries
    ingest provenance references `league_code_ingest_provenance` and passes — two
    such sites already exist. The opt-out is to write a second block and point at
    it, which is visible in review and self-documenting, rather than an entry in a
    list nobody re-reads.

    ⚠ AND IT SKIPS A NAME THAT ALREADY MEANS TWO THINGS. Demanding a reference for
    a name whose meaning is site-dependent would force a guess, and a guess is
    exactly what went wrong: six `league_code` columns were pointed at the wrong
    one of its two meanings during #82 MR3, found over three review rounds. The
    generator refuses those names; the gate must not then demand them, or the two
    halves of the same rule contradict each other. Skipped names are COUNTED and
    printed, never silently dropped, and GitLab #87 is the fix at the source.
    """
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
    """Every model, seed and source table must HAVE a description.

    WHY THIS IS SEPARATE FROM THE RULES ABOVE. Those judge the CONTENT of a
    description that exists. An object with no description at all never reaches
    them, so for the whole life of this project the coverage half of
    `engineering_standards.md` section 2 was written down and enforced nowhere.
    Measured when this was added: 11 of 11 source tables had none.

    ⚠ IT WALKS THE FILES ON DISK, NOT THE YAML ENTRIES, and that distinction is
    the whole point. `int_team__market_value_latest` had no description because
    it appeared in NO yml at all — a check that only read yml entries would have
    seen nothing to complain about and passed it green. So the model set comes
    from the .sql files and the seed set from the .csv files; a missing yml entry
    is then just the extreme case of a missing description.

    Source tables are the exception: a source is not a file, so its declaration
    in the yml IS its existence.
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

    # Anti-vacuous floor, same reasoning as MIN_DESCRIPTIONS: if the discovery
    # stops finding files, every assertion below passes for the wrong reason.
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


def _parse_ymls() -> tuple[list[tuple[str, pathlib.Path, object]], list[str]]:
    """Parse every project .yml ONCE. Returns (rel, path, doc) plus unparseable.

    ⚠ PARSED ONCE ON PURPOSE. The coverage check and the description walk both need
    every file, and PyYAML's pure-Python loader is the gate's dominant cost on the
    large prose schema files — parsing twice measured 3.7s of pure waste and more
    than doubled the whole test suite, in a gate that also runs at the end of every
    turn. Sharing the PARSE does not weaken the floor below: the two consumers still
    extract independently (`_walk` versus reading `models:`/`seeds:`/`sources:`), so
    a broken description walk is still caught by MIN_DESCRIPTIONS while coverage
    keeps working.
    """
    docs: list[tuple[str, pathlib.Path, object]] = []
    unparseable: list[str] = []
    for path in sorted(DBT_DIR.rglob("*.yml")):
        rel = _rel(path)
        # dbt writes compiled artifacts and installed packages under the project;
        # they are not ours to police and would swamp the census.
        if "/target/" in f"/{rel}" or "/dbt_packages/" in f"/{rel}":
            continue
        # `read_text` is inside the try: a non-UTF-8 .yml raises UnicodeDecodeError,
        # not YAMLError, and uncaught it escapes as a traceback naming no file.
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
    # A finding can quote an emoji, and a cp1252 console cannot encode one — the
    # gate would crash while reporting the defect. hasattr: tests capture stdout.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    docs, unparseable = _parse_ymls()
    found = _collect(docs)
    findings: list[str] = []

    # Before the floor check: an unparseable file contributes zero descriptions, so
    # the floor would fire first and blame the walk instead of the broken file.
    if unparseable:
        print(f"FAIL: {len(unparseable)} file(s) could not be parsed, so their "
              "descriptions are unchecked:")
        for bad in unparseable:
            print(f"  - {bad}")
        return 1

    # BEFORE the floor, and for the same reason the unparseable check is: an object
    # with no description contributes no description, so the floor would fire first
    # and report a broken walk when the real defect is that nothing was written.
    # The two checks read the yml independently, so a genuinely broken extraction
    # still reaches the floor below and is still diagnosed correctly.
    coverage = _object_coverage(docs)
    if coverage:
        print(f"DESCRIPTION COVERAGE: {len(coverage)} object(s) with no description\n")
        for finding in coverage:
            print(f"  - {finding}")
        print("\nThe standard is dbt_project/docs/engineering_standards.md section 2.")
        return 1

    blocks = _docs_blocks()

    # Before the floor, for the same reason object coverage is: a blank column
    # contributes no description, so the floor would fire first and report a broken
    # walk when the real defect is a definition that exists and is not referenced.
    shared = _shared_block_coverage(docs, blocks)
    if shared:
        print(f"SHARED DEFINITIONS: {len(shared)} column(s) not pointing at the "
              f"definition that already exists for their name\n")
        for finding in shared:
            print(f"  - {finding}")
        print("\nThe standard is dbt_project/docs/engineering_standards.md section 2, Form.")
        return 1

    if len(found) < MIN_DESCRIPTIONS:
        print(f"FAIL: found only {len(found)} descriptions under {_rel(DBT_DIR)} "
              f"(floor {MIN_DESCRIPTIONS}). The walk has stopped matching - a gate "
              "over zero descriptions always passes.")
        return 1

    for rel, where, text, is_column in found:
        flat = " ".join(text.split())
        # Rules run on the RENDERED text too, so a banned phrase cannot hide inside
        # a shared block and reach every call site unnoticed.
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
                # `ascii()` not `!r`: the match may be an emoji, and an escaped
                # ⚠ is still identifiable while never being unprintable.
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

    # Say what is NOT policed, every run. A rule that quietly exempts a name is a
    # hole nobody sees; the count and the reason belong in the success line.
    skipped = _ambiguous_names(docs)
    if skipped:
        blanks = sum(
            1
            for _rel, _path, doc in docs if isinstance(doc, dict)
            for model in (doc.get("models") or []) if isinstance(model, dict)
            for column in (model.get("columns") or []) if isinstance(column, dict)
            and column.get("name") in skipped
            and not (column.get("description") or "").strip()
        )
        print(f"NOT POLICED: {len(skipped)} column name(s) mean more than one thing, so no "
              f"machine can say which definition is right for a given site. "
              f"{blanks} column(s) are blank on that account and are tracked in GitLab #87.")
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
          f"every one of {models} models and {seeds} seeds on disk is described")
    return 0


if __name__ == "__main__":
    sys.exit(main())
