"""Editorial and Localisation gate — MECHANICAL checks on user-visible strings.

Editorial and Localisation exists as a mechanical gate, not a copy approver.
Wording stays the product owner's: Growth owns the title's shape, Editorial owns
its words.

Why a gate and not a reviewer agent. An agent cannot validate Finnish better than
the builder can — same model, same text — so a copy-approving role would
manufacture a signature. What it CAN do is mechanical, and that is all this file
does. One release shipped nine user-visible strings of which four were wrong, and
the product owner wrote the Finnish himself. Every check here is one of those
four defect classes made unrepeatable. Judgement about whether a sentence reads
naturally stays with him, permanently.

The checks, each traceable to a real defect:
  1. EM DASHES in shipped copy — an AI tell, in prose AND in product copy; one
     release shipped 14. Mechanical, zero false positives.
  2. LOCALE COMPLETENESS. A key present in one locale and missing in another;
     the live instance was the other direction (a value never translated).
  3. TERMINOLOGY drift against the 381-string validated corpus in `site/i18n/`
     (127 leaf strings per locale, verified). Football Finnish says `kunto` for
     form, not `muoto`; a string that uses a term the validated corpus contradicts
     is flagged with both spellings so a human can settle it.
  4. UNTRANSLATED VALUES. A non-EN locale carrying a value byte-identical to EN
     for a key whose EN value contains a lowercase alphabetic word. Numbers,
     symbols, brand names, pure abbreviations and the unit symbols in UNIT_SYMBOLS
     are exempt, because those are legitimately identical across locales.
  5. SEED KEYS RESOLVABLE. Every `label_i18n_key` the warehouse seeds publish
     (competition kinds, confederations, round names) exists in every locale. Check 2 sees
     only keys that are already in EN, and check 1-4 see only keys the pages
     show today; a kind with no competition yet had an English label in the
     seed and nothing in `strings.ts`, so its heading would have rendered in
     English on the DE and FI pages the day one was onboarded (six such kinds
     when this check was added). The seed is the list of keys that can reach a
     page; this check reads it, not the pages.

Exit 1 on any finding, and on an absent or unparseable `strings.ts`. Fails CLOSED,
as a CI check should.

Runs in `.gitlab-ci.yml` `validate:governance` and in the `validate-local` skill.

It was deliberately unwired for its first weeks, and the reason is worth keeping: it
exited 1 on `main` with 16 findings (14 em dashes, `fi.secForm` = `Muotovertailu`,
`fi.footerDataSource` left in English), and every one of those fixes is copy, which
is the product owner's alone (§10) — so the builder could not green it. Wiring it
then would have reddened CI on strings only he could touch. Once his rulings had
cleared all 16, wiring was a one-line change. That sequencing was the point: fix,
then wire, so the default branch never goes red.

The interval is the lesson, not the exception. A guard that runs nowhere is
indistinguishable from no guard, and this repo already carries that failure with
the SEO review role, which exists and is routed nowhere. "Not wired yet" is only
honest while it is temporary and someone is counting the days.
"""
from __future__ import annotations

import csv
import json
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
STRINGS = REPO_ROOT / "site_v2" / "src" / "i18n" / "strings.ts"
CORPUS_DIR = REPO_ROOT / "site" / "i18n"
LOCALES = ("en", "de", "fi")
# Unit symbols that are the same word in more than one language. Each entry is the product owner's
# decision; the list is the only way in.
UNIT_SYMBOLS = frozenset({"min"})
# Floor under the extraction, enforced in the gate itself (see main()). The fixture
# page alone needs about two dozen labels, so anything under this means the regex
# broke rather than the copy shrank.
MIN_KEYS = 20
# Floor for the metric-label maps (#370). 18 metrics get a name today; 15 leaves room for a row to be
# retired without a false alarm, while still tripping if the quoted-dotted-key regex breaks.
MIN_METRIC_KEYS = 15
# The seeds whose `label_i18n_key` column names a key a page will resolve through `t()`.
SEED_LABEL_FILES = (
    REPO_ROOT / "dbt_project" / "seeds" / "competition_types.csv",
    REPO_ROOT / "dbt_project" / "seeds" / "confederations.csv",
    REPO_ROOT / "dbt_project" / "seeds" / "round_names.csv",
)

# Terms the validated corpus settles. term -> (wrong, right, why)
# Only entries evidenced by the corpus or by a correction the product owner made belong here.
TERMINOLOGY = {
    "fi": [("muoto", "kunto", "football Finnish uses `kunto` for form; `muoto` is shape/format")],
}

# A dictionary literal: `const EN: Dict = { key: "value", ... };`
# Values are ALWAYS double-quoted by contract — strings.ts says so at its head,
# because check-page-specs.mjs extracts keys on the double quote.
_DICT_RE = re.compile(r"^const\s+([A-Z]{2}):\s*Dict\s*=\s*\{(.*?)^\};", re.S | re.M)
_ENTRY_RE = re.compile(r'^\s*([A-Za-z0-9_-]+):\s*"((?:[^"\\]|\\.)*)"', re.M)

# NO COMMENT-BASED EXEMPTION. Check 4 skips a value with no `[a-z]{3,}` word (numbers, symbols,
# abbreviations) and a single capitalised token (brand names). Any other text identical to English
# is a translation call, the product owner's alone (§10), so a comment in strings.ts can never pass
# it. The one way past check 4 is APPROVED_IDENTICAL: each entry names the locale, the key, the
# exact value and the issue note that approved it, and a changed value fails again.
APPROVED_IDENTICAL: dict[tuple[str, str], tuple[str, str]] = {
    ("de", "seoFixtureTitle"): ("{home} – {away}, {date}", "#243 note 4185014476"),
    ("fi", "seoFixtureTitle"): ("{home} – {away}, {date}", "#243 note 4185014476"),
    ("fi", "minutesShort"): ("min", "#243 note 4180302090"),
}

# A SECOND string class this gate has to see: metric display names. `METRIC_TERMS` maps the
# catalogue's `label_i18n_key` to the term that names the metric, and `PER_90` lists the keys that
# add the per-90 word; a missing `PER_90` fails like a missing map. Their keys are QUOTED and DOTTED, which `_ENTRY_RE` above cannot match by
# design — it requires a bare identifier. This parser resolves each metric's name in every locale,
# so a term a locale lacks shows as a missing metric name.
_METRIC_TERMS_RE = re.compile(
    r"^const\s+METRIC_TERMS:\s*Record<string,\s*string>\s*=\s*\{(.*?)^\};", re.S | re.M)
_PER_90_RE = re.compile(r"^const\s+PER_90\s*=\s*new Set\(\[(.*?)\]\);", re.S | re.M)
# ANY quoted dotted key, not just `metrics.*.label`. The catalogue's PLAYER metrics live in a
# second namespace (`playerMetrics.scorerPoints.goals`), and while this was anchored on `metrics\.`
# those labels skipped all four checks below — a Finnish board title missing from the map would have
# rendered BLANK (metricLabel falls back to English, then to "") and this gate would have printed a
# clean pass. Widened with #40 MR B, the change that first rendered one, in step with the two JS
# parsers named in the comment above.
_METRIC_ENTRY_RE = re.compile(
    r'^\s*"([A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+)":\s*"((?:[^"\\]|\\.)*)"', re.M)


def _dicts(text: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for m in _DICT_RE.finditer(text):
        out[m.group(1).lower()] = dict(_ENTRY_RE.findall(m.group(2)))
    return out


def _metric_labels(text: str) -> dict[str, dict[str, str]]:
    block = _METRIC_TERMS_RE.search(text)
    per90_block = _PER_90_RE.search(text)
    if not block or not per90_block:
        return {}
    terms = dict(_METRIC_ENTRY_RE.findall(block.group(1)))
    per90 = set(re.findall(r'"([^"]+)"', per90_block.group(1)))
    out: dict[str, dict[str, str]] = {}
    for loc, words in _dicts(text).items():
        out[loc] = {key: words[term] + (f" {words['per90']}" if key in per90 else "")
                    for key, term in terms.items()
                    if term in words and (key not in per90 or "per90" in words)}
    return out


def _seed_label_keys(paths=None) -> dict[str, list[str]]:
    """`label_i18n_key` values per seed file, in file order; a blank cell is skipped (the
    seeds' own not_null tests own that defect; in round_names a blank key is a round that shows
    no name, which its warn test reports). Reads `SEED_LABEL_FILES` at call time so a test can
    point it at a fixture."""
    keys: dict[str, list[str]] = {}
    for path in (paths or SEED_LABEL_FILES):
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            # Fail closed: a renamed or missing column must not read as "no keys to check" — a
            # gate over zero keys always passes (the same floor MIN_KEYS holds on the strings side).
            if "label_i18n_key" not in (reader.fieldnames or []):
                raise KeyError(f"{path.name}: no label_i18n_key column (header: {reader.fieldnames})")
            rows = list(reader)
        keys[path.name] = [r["label_i18n_key"] for r in rows if (r["label_i18n_key"] or "").strip()]
    return keys


def _corpus_leaves(obj) -> list[str]:
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in _corpus_leaves(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in _corpus_leaves(v)]
    return [obj] if isinstance(obj, str) else []


def main() -> int:
    if not STRINGS.is_file():
        print(f"FAIL: {STRINGS.relative_to(REPO_ROOT)} not found")
        return 1
    text = STRINGS.read_text(encoding="utf-8")
    dicts = _dicts(text)
    findings: list[str] = []

    missing_locales = [loc for loc in LOCALES if loc not in dicts]
    if missing_locales:
        print(f"FAIL: strings.ts has no dictionary for {missing_locales}")
        return 1

    # A FLOOR INSIDE THE GATE, not only in the test suite. `_DICT_RE` can still
    # match while `_ENTRY_RE` matches nothing — exactly the fragility strings.ts's
    # own header warns about, a value rewritten as a backtick template or single
    # quoted. Every locale would then be present but EMPTY, all four checks below
    # would iterate nothing, and this would print a clean pass over zero strings.
    # The repo's precedent for a floor in the checker is
    # `site_v2/scripts/check-page-specs.mjs`'s MIN_EXPECTED_KEYS.
    thin = {loc: len(dicts[loc]) for loc in LOCALES if len(dicts[loc]) < MIN_KEYS}
    if thin:
        print(f"FAIL: extracted too few strings {thin} (floor {MIN_KEYS} per locale). "
              "The entry regex has stopped matching — a gate over zero strings "
              "always passes. Check that every dictionary value is DOUBLE-quoted.")
        return 1

    # Metric labels (#370): same four checks, own parser, own floor. Merged into `dicts` because a
    # metric name is a user-visible string like any other — an em dash in one is still an em dash, a
    # locale missing one is still a hole. Keys cannot collide: chrome keys are bare identifiers,
    # metric keys are dotted and quoted.
    metrics = _metric_labels(text)
    missing_metric_locales = [loc for loc in LOCALES if loc not in metrics]
    if missing_metric_locales:
        print(f"FAIL: strings.ts has no METRIC_TERMS block for {missing_metric_locales}")
        return 1
    thin_metrics = {loc: len(metrics[loc]) for loc in LOCALES if len(metrics[loc]) < MIN_METRIC_KEYS}
    if thin_metrics:
        print(f"FAIL: extracted too few metric labels {thin_metrics} (floor {MIN_METRIC_KEYS} per "
              "locale). The METRIC_TERMS entry regex has stopped matching, which would let every "
              "metric name skip this gate.")
        return 1
    metric_count = sum(len(metrics[loc]) for loc in LOCALES)
    for loc in LOCALES:
        dicts[loc].update(metrics[loc])

    # 1. em dashes in shipped copy
    for loc in LOCALES:
        for key, val in dicts[loc].items():
            if "—" in val:
                findings.append(
                    f"em dash in shipped copy: {loc}.{key} = {val!r}. The CPO has flagged "
                    "em dashes twice as an AI tell, in prose and in product copy."
                )

    # 2. locale completeness, in both directions
    en_keys = set(dicts["en"])
    for loc in LOCALES:
        if loc == "en":
            continue
        for key in sorted(en_keys - set(dicts[loc])):
            findings.append(f"key missing from {loc}: {key} (present in en)")
        for key in sorted(set(dicts[loc]) - en_keys):
            findings.append(f"key present in {loc} but not in en: {key}")

    # 3. terminology settled by the validated corpus
    corpus: dict[str, list[str]] = {}
    for loc in LOCALES:
        path = CORPUS_DIR / f"{loc}.json"
        if path.is_file():
            corpus[loc] = _corpus_leaves(json.loads(path.read_text(encoding="utf-8")))
    for loc, rules in TERMINOLOGY.items():
        if loc not in dicts:
            continue
        for wrong, right, why in rules:
            for key, val in dicts[loc].items():
                if re.search(rf"\b{re.escape(wrong)}\w*", val, flags=re.I):
                    corroborated = any(
                        re.search(rf"\b{re.escape(right)}", s, flags=re.I)
                        for s in corpus.get(loc, [])
                    )
                    findings.append(
                        f"terminology: {loc}.{key} uses `{wrong}` where the corpus uses "
                        f"`{right}` — {why}. Corroborated by site/i18n/{loc}.json: "
                        f"{corroborated}. Value: {val!r}"
                    )

    # 4. untranslated values
    for loc in LOCALES:
        if loc == "en":
            continue
        for key, val in dicts[loc].items():
            en_val = dicts["en"].get(key)
            if en_val is None or val != en_val:
                continue
            # exempt: no lowercase word at all (numbers, symbols, abbreviations),
            # or a single token that is a brand/abbreviation
            if not re.search(r"[a-z]{3,}", en_val) or en_val in UNIT_SYMBOLS:
                continue
            if len(en_val.split()) == 1 and en_val[0].isupper():
                continue
            if APPROVED_IDENTICAL.get((loc, key), ("",))[0] == val:
                continue
            findings.append(
                f"untranslated: {loc}.{key} is byte-identical to en ({en_val!r}). "
                "Translate it, or — if sameness is genuinely correct for this locale — "
                "that is a §10 wording call: take it to the CPO. Only his approval adds it "
                "to APPROVED_IDENTICAL; see the note above it."
            )

    # 5. every seed-published label key resolves in every locale
    # Any read failure (absent file, renamed column, non-UTF-8 bytes, malformed CSV) is the gate's
    # own FAIL line — the `check_competition_type_seed.py` pattern — never a bare traceback.
    try:
        seed_keys = _seed_label_keys()
    except Exception as e:  # noqa: BLE001
        print(f"FAIL: cannot read the seed label keys: {type(e).__name__}: {e}")
        return 1
    for seed_name, keys in seed_keys.items():
        for key in keys:
            for loc in LOCALES:
                if key not in dicts[loc]:
                    findings.append(
                        f"seed key unresolvable: {seed_name} publishes label_i18n_key `{key}` "
                        f"and {loc} has no such string. A page resolves the heading by this key "
                        "the day a competition of that kind is onboarded; add it in every locale."
                    )

    if findings:
        print(f"COPY GATE: {len(findings)} finding(s)\n")
        for f in findings:
            print(f"  - {f}")
        print("\nWording is the CPO's call (§10). This gate only reports mechanical "
              "defects; it never approves copy.")
        return 1

    total = sum(len(dicts[loc]) for loc in LOCALES)
    print(f"COPY GATE ok: {total} strings across {len(LOCALES)} locales "
          f"({total - metric_count} chrome + {metric_count} metric labels), "
          f"{sum(len(v) for v in corpus.values())} corpus strings consulted, "
          f"{sum(len(v) for v in seed_keys.values())} seed label keys resolvable in every locale")
    return 0


if __name__ == "__main__":
    sys.exit(main())
