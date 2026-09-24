# Review — feat/address-words — #158

diff_sha256: bff15cbb8ace1bad72ae64387c170f96318042b2a25ecac507eaf0517b4606be

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1: every changed file matched against scope_paths, all inside; the word table and its rules predate the diff and are implemented, not authored; the clash check is declared under THRESHOLD DECLARATIONS with its authority and placement (existing build and pytest job, no new CI job), recurring cost none; the impact_map enumerates the real link sites; decisions_reserved items untouched; no credential-shaped string.
- Round 2 delta: the amendment adding tests/test_no_decision_history_in_docs.py quotes the CPO's answer; the patch's file list equals round 1's plus that one file; the two pins move down by exactly the two dated lines removed; both corrected rows state what this branch built.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 1 (FAIL, fixed): docs/wireframes/00_overview.md:138 still named the Matchdays tab at /fixtures/, a directory the branch removes.
- Traced every localeHref call site in site_v2/src: no hardcoded English word left in a link, each goes through word(lang, key); addressWords.mjs, href.ts alternatePaths and check_design_inventory.py translate_path read against the "Address words" rules 1-8; specPathFor resolves the renamed route folders to the unchanged spec files; rendered_page_evidence.md read as built-output evidence (1330 pages, design check 147 renders 0 failures, 3987 reciprocal hreflang pairs, dev-server 200/404).
- Round 2 delta: 00_overview.md:138 and the site_architecture.md decisions row now state the built state without dates; pins 8->7 and 22->21 match; no /fixtures/ or /rankings/ literal left in audit-seo.mjs or its test.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1: the changed check functions (translate_path/resolve_built, wordParam/specRouteRegex/entityKey/hreflang reciprocity, tabPath/checkTabPagesFound) are pure and re-run safe; new tests fail if the code reverts to the language-agnostic form; the new build checks fail closed; no dependency, lockfile, hosting or CI change; old route folders are deleted, not left beside the new ones. Noted: the positional rule is duplicated in Python with mirrored test cases only; a drift fails closed through resolve_built's Failure, so not a defect.
- Round 2 delta: the pin changes match the two real history-line removals; the audit-seo changes are fixture strings and one docstring, no logic.

## escalations
- question: May I add tests/test_no_decision_history_in_docs.py to the #158 contract, so I can remove the dates from the two stale rows, correct them, and lower their pins (00_overview.md 8->7, site_architecture.md 22->21)?
  CPO ANSWER: Yes, amend (answered in chat; recorded in contract.md amendments).
