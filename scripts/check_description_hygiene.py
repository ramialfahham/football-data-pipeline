"""Description hygiene gate — MECHANICAL checks on dbt `description:` fields.

Why this exists. `description:` was used as a decision log: rulings, dated update
stamps, issue numbers, and hand-maintained claims about who reads a column
downstream. An independent dbt audit (2026-08-20) measured 616 descriptions
across 19 files and found five files holding 83% of the contaminated text, with
THREE descriptions provably false — each of them a downstream-consumer claim, the
one kind of statement that cannot be kept true by hand. One asserted a column had
no readers while a live mart filtered on it; acting on it would have broken the
competitions page.

The root cause was not laziness. These fields had NO READER — `persist_docs`
absent, `dbt docs generate` running nowhere — so the field had no feedback loop
and became the cheapest place to dump narrative. The rule already existed
(`engineering_standards.md` §2, "keep descriptions factual and concise") and was
ignored roughly 130 times. This repo's own measurement is that prose-only rules
recur (33 of 50 past corrections were prose-only; 22 recurred) and mechanised
ones do not. Hence a gate.

The standard it enforces is `dbt_project/docs/engineering_standards.md` §2. Each
check below is one contaminated class made unrepeatable:

  1. ISSUE REFS (`#123`, `GAP-04`, `!27`). A tracker id in a description is a
     pointer to a decision, not a fact about the data, and the GitHub tracker
     these mostly point at is unreachable — so they are already dead links.
  2. DATED STAMPS. An ISO date, or an `UPDATED`/`CORRECTED` annotation. Git holds
     history losslessly; a hand-copy of it starts rotting immediately.
  3. DECISION LANGUAGE. `CPO`, `SLATED FOR`, `SUPERSEDED`, "an earlier version
     said". Rulings belong in `.claude/task/escalations.log`, open questions in
     the tracker, design rationale in `layering.md`.
  4. DOWNSTREAM-CONSUMER CLAIMS. "the only reader is X", "no dbt model reads
     this", "Feeds fct_y". Upstream facts are fixed in the SQL and change when the
     SQL changes; downstream facts change whenever anyone adds a model, and nobody
     comes back to update the prose. All three false claims were this shape.
     `dbt ls --select <model>+` answers it correctly and for free.
  5. SEVERITY EMOJI. A description is not an annotated argument.
  6. LENGTH over 600 characters. BigQuery hard-rejects a column description over
     1,024, which would break the nightly build the day `persist_docs` is turned
     on. 600 leaves headroom, and a description nobody finishes reading is one
     nobody checks. Waived for a bare `{{ doc() }}` reference: the block carries
     the text and is checked on its own.

WHAT THIS GATE DELIBERATELY DOES NOT DO. It does not judge whether a description
is GOOD — whether it states grain, or source, or known limits. That is editorial
and it belongs to a human reading it. Every rule here is one a machine can decide
with no taste, which is the same line `check_copy_gate.py` draws.

⚠ THE PATTERNS MATCH ANNOTATION FORMS, NOT ORDINARY VERBS, and that distinction is
measured rather than assumed. On the cleaned MR3/MR4 text a case-insensitive
`CORRECTED` matches six legitimate sentences ("the country corrections from the
seed", "derived from the corrected name"), and a bare ISO-date rule matched
`dim_date`'s calendar range. A gate that fires on correct text is worse than no
gate, because the fix is to weaken it. Every pattern below is anchored to the
shouty or dated form a decision log actually uses.

Exit 1 on any finding, and on an unparseable YAML file. Fails CLOSED.

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

MAX_CHARS = 600

# A description that is ONLY a docs-block reference, optionally with a short
# per-model qualifier after it. The block itself is a separate description and is
# checked in its own right, so the length rule would otherwise punish reuse — the
# exact behaviour the standard asks for.
DOC_REF_RE = re.compile(r"\{\{\s*doc\(\s*['\"][^'\"]+['\"]\s*\)\s*\}\}")

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
        # NO BARE `ruled`/`ruling`. An earlier draft had them, and in a FOOTBALL
        # repo that is a false-positive generator: "goal ruled out for offside",
        # "match ruled void", "fixture ruled a walkover" are all legitimate
        # description prose. It also broke this file's own stated design rule —
        # annotation forms, not ordinary verbs. `\bCPO\b` already catches every
        # real instance in this repo, because a ruling worth logging is always
        # attributed ("CPO ruled", "CPO ruling"). Caught by platform-reviewer.
        re.compile(r"\bCPO\b|\bSLATED FOR\b|\ban earlier (?:version|draft)\b"
                   r"|\bused to say\b"),
        "rulings belong in .claude/task/escalations.log, open questions in the "
        "tracker, design rationale in layering.md",
    ),
    (
        "downstream-consumer claim",
        # Written as a CLASS, not a list of the instances seen so far. The
        # "no/zero consumer" arm was added after the first full-repo sweep found
        # `stg_apif__lineups` claiming "This model has NO consumer today" — the
        # exact shape of the `display_group` claim that started this programme,
        # which the first draft's `no dbt model reads` arm did not match.
        re.compile(
            r"\b(?:only|single|sole)\s+(?:reader|consumer)s?\b"
            r"|\b(?:no|zero)\s+(?:dbt\s+model\s+|downstream\s+)?(?:reader|consumer)s?\b"
            r"|\bno dbt model reads\b"
            r"|\bnothing\s+downstream\b"
            r"|\bdownstream of this\b"
            r"|\bREAD by\b"
            # "feeds <identifier>" where the target is snake_case, so a named model
            # OR a named column is caught (`feeds fct_fixture`, `feeds shot_share`)
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


def _walk(node: object, where: str, out: list[tuple[str, str]]) -> None:
    """Collect (path, description) for every description in a parsed YAML tree."""
    if isinstance(node, dict):
        name = node.get("name")
        here = f"{where}/{name}" if isinstance(name, str) else where
        for key, value in node.items():
            if key == "description" and isinstance(value, str):
                out.append((here, value))
            else:
                _walk(value, here, out)
    elif isinstance(node, list):
        for item in node:
            _walk(item, where, out)


def _collect() -> tuple[list[tuple[str, str, str]], list[str]]:
    """Every description under dbt_project/, and any file that failed to parse."""
    found: list[tuple[str, str, str]] = []
    unparseable: list[str] = []
    for path in sorted(DBT_DIR.rglob("*.yml")):
        rel = _rel(path)
        # dbt writes compiled artifacts and installed packages under the project;
        # they are not ours to police and would swamp the census.
        if "/target/" in f"/{rel}" or "/dbt_packages/" in f"/{rel}":
            continue
        # UnicodeDecodeError and OSError are caught alongside YAMLError, not just
        # YAMLError: `read_text` is inside this try, and a .yml saved in any
        # non-UTF-8 encoding raises UnicodeDecodeError (a ValueError, not a
        # YAMLError). Uncaught, that escapes as a raw traceback instead of the
        # crafted "could not be parsed" report — the gate would still exit
        # non-zero, but it would blame nothing and name no file. Caught by
        # platform-reviewer, who noted the two adjacent failure modes already
        # fixed here and that the input side had been missed.
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, UnicodeDecodeError, OSError) as exc:
            unparseable.append(f"{rel}: {exc.__class__.__name__}")
            continue
        collected: list[tuple[str, str]] = []
        _walk(doc, path.stem, collected)
        found.extend((rel, where, text) for where, text in collected)
    return found, unparseable


def main() -> int:
    # A finding can quote a matched EMOJI, and this gate runs at turn end on a
    # Windows console whose default encoding is cp1252, which cannot encode one.
    # Without this the gate crashes with UnicodeEncodeError *while reporting the
    # defect* — it would fail, but on the wrong error and with the finding lost.
    # Guarded by hasattr because `main()` is called directly from the tests, where
    # stdout is a capture object with no `reconfigure`.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    found, unparseable = _collect()
    findings: list[str] = []

    # REPORTED BEFORE THE FLOOR, and the order is load-bearing. An unparseable file
    # contributes zero descriptions, so it drags the census under the floor and the
    # floor's message ("the walk has stopped matching") would send an operator
    # hunting a broken walk instead of the malformed YAML that actually caused it.
    # A test pinned this after the first version got the order wrong.
    if unparseable:
        print(f"FAIL: {len(unparseable)} file(s) could not be parsed, so their "
              "descriptions are unchecked:")
        for bad in unparseable:
            print(f"  - {bad}")
        return 1

    if len(found) < MIN_DESCRIPTIONS:
        print(f"FAIL: found only {len(found)} descriptions under {_rel(DBT_DIR)} "
              f"(floor {MIN_DESCRIPTIONS}). The walk has stopped matching - a gate "
              "over zero descriptions always passes.")
        return 1

    over_limit = 0
    for rel, where, text in found:
        flat = " ".join(text.split())
        for name, pattern, why in RULES:
            hit = pattern.search(flat)
            if hit:
                # `ascii()` not `!r`: the match may be an emoji, and an escaped
                # ⚠ is still identifiable while never being unprintable.
                findings.append(
                    f"{rel} :: {where} - {name}: {ascii(hit.group(0))}\n"
                    f"    why banned: {why}"
                )
        # Length is waived for a description that is a docs-block reference plus a
        # short qualifier; the block is a description in its own right and is
        # checked above and below like any other.
        if len(flat) > MAX_CHARS and not DOC_REF_RE.search(flat):
            over_limit += 1
            findings.append(
                f"{rel} :: {where} - over length: {len(flat)} chars (limit {MAX_CHARS})\n"
                f"    why banned: BigQuery rejects a column description over 1,024, which "
                f"breaks the nightly build once persist_docs is on"
            )

    if findings:
        print(f"DESCRIPTION HYGIENE: {len(findings)} finding(s) "
              f"across {len(found)} descriptions\n")
        for finding in findings:
            print(f"  - {finding}")
        print("\nThe standard is dbt_project/docs/engineering_standards.md section 2.")
        return 1

    files = len({rel for rel, _, _ in found})
    print(f"DESCRIPTION HYGIENE ok: {len(found)} descriptions across {files} files, "
          f"{len(RULES)} rules, none over {MAX_CHARS} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
