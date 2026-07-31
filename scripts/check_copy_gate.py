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

**DELIBERATELY NOT WIRED INTO CI YET, and that is a decision, not an oversight.**
It exits 1 on `main` today with 16 real findings: 14 em dashes (worst
`heroVerdictUnder`, in all three locales), `fi.secForm` = `Muotovertailu`, and
`fi.footerDataSource` left in English. **Every one of those fixes is copy, which is
the CPO's alone (§10), so the builder cannot green it.** Wiring it into `ci-ui.yml`
is one line the moment he rewrites them; until then CI would be red on strings only
he may touch. Recorded in the contract's `decisions_reserved` and in the handover,
because a check that runs nowhere is the exact failure this repo already carries
with `seo-expert-reviewer` and must not be claimed as working.
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


def _dicts(text: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for m in _DICT_RE.finditer(text):
        out[m.group(1).lower()] = dict(_ENTRY_RE.findall(m.group(2)))
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
                "If that is correct for this locale, the value needs a comment "
                "saying so."
            )

    if findings:
        print(f"COPY GATE: {len(findings)} finding(s)\n")
        for f in findings:
            print(f"  - {f}")
        print("\nWording is the CPO's call (§10). This gate only reports mechanical "
              "defects; it never approves copy.")
        return 1

    total = sum(len(dicts[loc]) for loc in LOCALES)
    print(f"COPY GATE ok: {total} strings across {len(LOCALES)} locales, "
          f"{sum(len(v) for v in corpus.values())} corpus strings consulted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
