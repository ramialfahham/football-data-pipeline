# Review — claude/362-b-design-checks — 2026-11-28

diff_sha256: b3df7dfa90f2d07f6ccb01cd4691479d5ad3b4545eea527e14733ecfca5f99dd

rounds: 4
rounds_cap_override: approved in chat, 28 Nov 2026

## cto-reviewer
VERDICT: PASS
findings:
- [nit] cost wording: contract.md decisions_taken - the extra width is a small recurring validate:ui cost, better stated as measured than as none.
- [nit] unpinned token value: scripts/check_component_registry.py _governed - --logo-green is admitted whatever value the stylesheet gives it; only its use is restricted.
risks_checked:
- New mechanisms: join_continued and the "(continued)" Pages-row convention live inside the existing check and are declared as an engineering call; no new workflow step, hook, package or service.
- Dependencies: no requirements or package file change; the only new import is stdlib dataclasses.
- Fail-closed: mocks skipped at 520 only (a width main never measured); "nothing measured" skipped at 520 only for a page no Pages row owns; collect() raises on any other missing render; a mismatched continued row stays its own row and fails; --viewports clears built_only.
- Colour-set exception admits only fill: var(--logo-green) in a rule whose whole selector is .brand .logo .pv; a second token gets no pass.
- Protected paths check_design_inventory.py and test_design_inventory.py route to cto + platform; protected_override and impact_map are real content.
- No pin rises; no credentials, workflow or pipeline file touched; no warehouse reads, deploy or schedule change.

## platform-reviewer
VERDICT: PASS
findings:
- [nit] stale comment: .gitlab-ci.yml:584 - still says the full sweep renders 6 widths; out of this branch's scope.
- [nit] partial test coverage: scripts/check_design_inventory.py join_continued - it compares kind, source, URL and FI mode; the test only varies FI.
- [nit] latent misalignment: scripts/check_design_inventory.py join_continued - concatenates expect_when without a length check; unreachable from load() today.
- [nit] literal suffix: scripts/parts_page.py:241 - matches a literal " (continued)" and skips a mismatched continued row.
- [nit] summary wording: scripts/check_design_inventory.py summary line - reports 7 widths while mocks render 6.
- [nit] formatting: tests/test_design_inventory.py:663 - missing space after the equals sign.
risks_checked:
- _LOGO_USE now starts only at stylesheet start or after }: continued selector lists, a selector on the previous line, compound selectors and a second declaration are all counted as colours outside the sets; the parametrised cases fail against an unanchored pattern.
- join_continued test goes through plan(): removing the join or the FI comparison fails it; a continued row before its page fails closed.
- --pages selects on joined rows; the unknown-page check uses joined names; the test exits 0 under the old filter-by-name and so pins the fix.
- A missing built render at 520 still raises; nothing new fails open.
- The three scripts are read-only checks; a rerun or an interrupted run leaves no state.
- design_baseline.json names no viewports, so the 7-width default is the compared scope; merge_ready.full_widths() and its test agree.
- No dependency, credential or workflow permission change; validate:ui stays under its timeout with one more width.

## fixes
- logo exemption stripped a continued selector list | sweep: every multi-line and compound selector shape before and after the logo rule, and a second token | test: tests/test_check_component_registry.py::test_the_logo_green_outside_the_logos_rule_is_a_value_no_set_holds
- untested continued-row join | sweep: a joined pair and a mismatched pair through plan() | test: tests/test_design_inventory.py::test_a_continued_row_joins_its_page_and_no_other_pair_does
- --pages dropped the continued row's expects | sweep: every place a page name is selected before the join | test: tests/test_design_inventory.py::test_a_run_naming_a_page_also_checks_what_its_continued_row_expects

## escalations
(none)
