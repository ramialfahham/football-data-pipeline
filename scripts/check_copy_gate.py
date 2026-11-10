"""Mechanical gate on the strings in `strings.ts`; it reports defects and never approves copy."""
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
# Unit symbols that are the same word in more than one language.
UNIT_SYMBOLS = frozenset({"min"})
# Floor under the extraction: anything below it means the regex broke rather than the copy shrank.
MIN_KEYS = 20
# Floor for the metric-label maps, tripping if the quoted-dotted-key regex breaks.
MIN_METRIC_KEYS = 15
# The seeds whose `label_i18n_key` column names a key a page will resolve through `t()`.
SEED_LABEL_FILES = (
    REPO_ROOT / "dbt_project" / "seeds" / "competition_types.csv",
    REPO_ROOT / "dbt_project" / "seeds" / "confederations.csv",
    REPO_ROOT / "dbt_project" / "seeds" / "round_names.csv",
)

# Terms the validated corpus settles: locale -> [(wrong, right, why)].
TERMINOLOGY = {
    "fi": [("muoto", "kunto", "football Finnish uses `kunto` for form; `muoto` is shape/format")],
}

# A dictionary literal `const EN: Dict = { key: "value", ... };`; values are always double-quoted.
_DICT_RE = re.compile(r"^const\s+([A-Z]{2}):\s*Dict\s*=\s*\{(.*?)^\};", re.S | re.M)
_ENTRY_RE = re.compile(r'^\s*([A-Za-z0-9_-]+):\s*"((?:[^"\\]|\\.)*)"', re.M)

# The only way past the untranslated-value check: (locale, key) -> (exact value, approval note).
# Text identical to English is a translation call for the product owner, so a comment in strings.ts
# can never exempt it, and a changed value fails again.
APPROVED_IDENTICAL: dict[tuple[str, str], tuple[str, str]] = {
    ("de", "seoFixtureTitle"): ("{home} – {away}, {date}", "#243 note 4185014476"),
    ("fi", "seoFixtureTitle"): ("{home} – {away}, {date}", "#243 note 4185014476"),
    ("fi", "minutesShort"): ("min", "#243 note 4180302090"),
}

# Metric display names: `METRIC_TERMS` maps a `label_i18n_key` to its term and `PER_90` lists the
# keys that add the per-90 word. Their keys are quoted and dotted, which `_ENTRY_RE` cannot match.
_METRIC_TERMS_RE = re.compile(
    r"^const\s+METRIC_TERMS:\s*Record<string,\s*string>\s*=\s*\{(.*?)^\};", re.S | re.M)
_PER_90_RE = re.compile(r"^const\s+PER_90\s*=\s*new Set\(\[(.*?)\]\);", re.S | re.M)
# Any quoted dotted key, because player metrics live in a second namespace such as `playerMetrics.`.
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
    """`label_i18n_key` values per seed file, in file order, skipping blank cells."""
    keys: dict[str, list[str]] = {}
    for path in (paths or SEED_LABEL_FILES):
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            # Fail closed: a missing column must not read as "no keys to check".
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

    # `_DICT_RE` can match while `_ENTRY_RE` matches nothing, which would pass over zero strings.
    thin = {loc: len(dicts[loc]) for loc in LOCALES if len(dicts[loc]) < MIN_KEYS}
    if thin:
        print(f"FAIL: extracted too few strings {thin} (floor {MIN_KEYS} per locale). "
              "The entry regex has stopped matching — a gate over zero strings "
              "always passes. Check that every dictionary value is DOUBLE-quoted.")
        return 1

    # Metric labels get the same checks; keys cannot collide because chrome keys are bare
    # identifiers and metric keys are dotted and quoted.
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

    for loc in LOCALES:
        for key, val in dicts[loc].items():
            if "—" in val:
                findings.append(
                    f"em dash in shipped copy: {loc}.{key} = {val!r}. The CPO has flagged "
                    "em dashes twice as an AI tell, in prose and in product copy."
                )

    en_keys = set(dicts["en"])
    for loc in LOCALES:
        if loc == "en":
            continue
        for key in sorted(en_keys - set(dicts[loc])):
            findings.append(f"key missing from {loc}: {key} (present in en)")
        for key in sorted(set(dicts[loc]) - en_keys):
            findings.append(f"key present in {loc} but not in en: {key}")

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

    for loc in LOCALES:
        if loc == "en":
            continue
        for key, val in dicts[loc].items():
            en_val = dicts["en"].get(key)
            if en_val is None or val != en_val:
                continue
            # Exempt: no lowercase word (numbers, symbols, abbreviations) or a single brand token.
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

    # Any seed read failure becomes a FAIL line rather than a traceback.
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
