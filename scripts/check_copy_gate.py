"""Editorial and Localisation gate — MECHANICAL checks on user-visible strings.

CPO ruling 2026-07-31 (#868), in his words: *"Editorial and Localisation exists as
a mechanical gate, not a copy approver. Wording stays yours. Growth owns the
title's shape, Editorial owns its words."*

Why a gate and not a reviewer agent. An agent cannot validate Finnish better than
the builder can — same model, same text — so a copy-approving role would
manufacture a signature. What it CAN do is mechanical, and that is all this file
does. On #867, nine user-visible strings shipped and four were wrong; the CPO
wrote the Finnish himself. Every check here is one of those four defect classes
made unrepeatable. Judgement about whether a sentence reads naturally stays with
the CPO, permanently.

The checks, each traceable to a real defect:
  1. EM DASHES in shipped copy. The CPO flagged them twice as an AI tell, in prose
     AND in product copy. #867 shipped 14. Mechanical, zero false positives.
  2. LOCALE COMPLETENESS. A key present in one locale and missing in another. #866
     is the live instance in the other direction (a value never translated).
  3. TERMINOLOGY drift against the 381-string validated corpus in `site/i18n/`
     (127 leaf strings per locale, verified). Football Finnish says `kunto` for
     form, not `muoto`; a string that uses a term the validated corpus contradicts
     is flagged with both spellings so a human can settle it.
  4. UNTRANSLATED VALUES. A non-EN locale carrying a value byte-identical to EN
     for a key whose EN value contains a lowercase alphabetic word. Numbers,
     symbols, brand names and pure abbreviations are exempt, because those are
     legitimately identical across locales.

Exit 1 on any finding, and on an absent or unparseable `strings.ts`. Fails CLOSED,
as a CI check should.

**WIRED, 2026-08-06.** Runs in `.gitlab-ci.yml` `validate:governance` and in the
`validate-local` skill.

It was deliberately unwired for its first weeks, and the reason is worth keeping: it
exited 1 on `main` with 16 findings (14 em dashes, `fi.secForm` = `Muotovertailu`,
`fi.footerDataSource` left in English), and every one of those fixes is copy, which
is the CPO's alone (§10) — so the builder could not green it. Wiring it then would
have reddened CI on strings only he could touch.

MR !7 cleared all 16 with his rulings, which made wiring a one-line change. That
sequencing was the point: fix, then wire, so the default branch never goes red.

The interval is the lesson, not the exception. A guard that runs nowhere is
indistinguishable from no guard, and this repo already carries that failure with
`seo-expert-reviewer`. "Not wired yet" is only honest while it is temporary and
someone is counting the days.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
STRINGS = REPO_ROOT / "site_v2" / "src" / "i18n" / "strings.ts"
CORPUS_DIR = REPO_ROOT / "site" / "i18n"
LOCALES = ("en", "de", "fi")
# Floor under the extraction, enforced in the gate itself (see main()). The fixture
# page alone needs about two dozen labels, so anything under this means the regex
# broke rather than the copy shrank.
MIN_KEYS = 20
# Floor for the metric-label maps (#370). 18 metrics get a name today; 15 leaves room for a row to be
# retired without a false alarm, while still tripping if the quoted-dotted-key regex breaks.
MIN_METRIC_KEYS = 15

# Terms the validated corpus settles. term -> (wrong, right, why)
# Only entries evidenced by the corpus or by a recorded CPO correction belong here.
TERMINOLOGY = {
    "fi": [("muoto", "kunto", "football Finnish uses `kunto` for form; `muoto` is shape/format "
                             "(CPO correction, #867)")],
}

# A dictionary literal: `const EN: Dict = { key: "value", ... };`
# Values are ALWAYS double-quoted by contract — strings.ts says so at its head,
# because check-page-specs.mjs extracts keys on the double quote.
_DICT_RE = re.compile(r"^const\s+([A-Z]{2}):\s*Dict\s*=\s*\{(.*?)^\};", re.S | re.M)
_ENTRY_RE = re.compile(r'^\s*([A-Za-z0-9_-]+):\s*"((?:[^"\\]|\\.)*)"', re.M)

# NO COMMENT-BASED EXEMPTION, and that is the decision rather than an omission.
#
# Check 4's message used to promise one — "the value needs a comment saying so" — while the code
# parsed no comment, so the only way past it was to change the copy. A marker (`i18n:same-as-en`)
# was built to honour that promise and then REMOVED after cto-reviewer at opus argued it down.
# The argument, kept because it is the reusable part:
#
#   · The case the exemption was for is ALREADY exempt. Check 4 skips any value with no
#     `[a-z]{3,}` word (numbers, symbols, abbreviations) and any single capitalised token
#     (brand names). The residual case is a multi-word English string deliberately kept in
#     de/fi — of which this repo has ZERO.
#   · The one historical instance, `fi.footerDataSource`, was ruled on by the CPO by
#     TRANSLATING it, in a decision taken with no exemption available.
#   · Translation is §10, the CPO's alone. A self-serve comment would let any future agent whose
#     change reddens check 4 go green on its own authority — a guard bypass added ahead of any
#     demonstrated need, in the direction the last real ruling went against.
#
# So the message is corrected instead: it now points at the CPO rather than promising a hatch.
# If a genuine identical-string case ever appears, it is a CPO ruling, and THAT is when an
# exemption gets designed — with the case in hand.

# #370 added a SECOND string class this gate has to see: metric display names, in their own
# `METRIC_LABELS_<LOC>` maps keyed by the catalogue's `label_i18n_key`. Their keys are QUOTED and
# DOTTED, which `_ENTRY_RE` above cannot match by design — it requires a bare identifier. So without
# this second parser the 54 metric labels would be invisible here and would skip the em dash,
# completeness and terminology checks entirely: 54 user-visible strings past the gate that exists to
# catch exactly those defects.
_METRIC_DICT_RE = re.compile(
    r"^const\s+METRIC_LABELS_([A-Z]{2}):\s*MetricLabels\s*=\s*\{(.*?)^\};", re.S | re.M)
_METRIC_ENTRY_RE = re.compile(r'^\s*"(metrics\.[A-Za-z0-9_]+\.label)":\s*"((?:[^"\\]|\\.)*)"', re.M)


def _dicts(text: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for m in _DICT_RE.finditer(text):
        out[m.group(1).lower()] = dict(_ENTRY_RE.findall(m.group(2)))
    return out


def _metric_labels(text: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for m in _METRIC_DICT_RE.finditer(text):
        out[m.group(1).lower()] = dict(_METRIC_ENTRY_RE.findall(m.group(2)))
    return out


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
    # (platform-reviewer at opus, 2026-07-31.)
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
        print(f"FAIL: strings.ts has no METRIC_LABELS block for {missing_metric_locales}")
        return 1
    thin_metrics = {loc: len(metrics[loc]) for loc in LOCALES if len(metrics[loc]) < MIN_METRIC_KEYS}
    if thin_metrics:
        print(f"FAIL: extracted too few metric labels {thin_metrics} (floor {MIN_METRIC_KEYS} per "
              "locale). The METRIC_LABELS entry regex has stopped matching, which would let every "
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
            if not re.search(r"[a-z]{3,}", en_val):
                continue
            if len(en_val.split()) == 1 and en_val[0].isupper():
                continue
            findings.append(
                f"untranslated: {loc}.{key} is byte-identical to en ({en_val!r}). "
                "Translate it, or — if sameness is genuinely correct for this locale — "
                "that is a §10 wording call: take it to the CPO. There is deliberately "
                "no self-serve exemption comment; see the note above check 4."
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
          f"{sum(len(v) for v in corpus.values())} corpus strings consulted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
