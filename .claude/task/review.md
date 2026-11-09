# Review — fix/249-hyphen-names-every-tab

diff_sha256: f2471d7430a00dfd357dbf5d921c46d8b7a1ec9448235a3c116ae6d5dbb009f6

rounds: 4
rounds_cap_override: approved in chat, 2026-11-09: rounds past three for the unit test that pins the no-break span match, and for the design baselines lowered from CI's measurement.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope_paths; counts_tabs.html falls under tests/fixtures/design_inventory/*.
- protected_override names check_design_inventory.py, test_design_inventory.py, middleware.ts and the components.yml Unbreakable unit, each with its approval; the components.yml hunk touches only that unit.
- impact_map declares the new build mechanism and the recurring CI cost (+36 s per merge request, +76 s on main), accepted with its date.
- The round 4 change is one test case that pins existing behaviour; no mechanism, cost or page output change; decisions_taken and decisions_reserved unchanged.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The middleware rewrites only text/html responses and only text between tags inside `<body>`; head, attributes, script, style, SVG, select and template are skipped, so the copied and indexed text keeps its real hyphen.
- The NB match starts with whitespace, so `data-class="nb"` is not read as the no-break span; `class="nb"` and `class="x nb"` are.
- The .plrow gap takes the expression .lrow and .teams already use; no registry row pins the Player row's gap.
- No field, metric, percentage or label is added to site_v2/src; the rendered evidence reports counts from the built pages.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The no-tab test carries @needs_browser and asserts the FAIL line and exit code 1.
- The new wholeWords case feeds `data-class="nb"` and `title="x nb"` and asserts the inner wrap; it fails with the leading `\s` removed (9 pass, 1 fail).
- The every-tab check fails closed on a Tab bar with no tab to open; shared defects are counted once through a per-page set reset on each load; failure screenshots are capped at 20.
- counts_tabs.html gives its counts only when a hidden tab is opened and a shared element is counted once, so reverting either behaviour fails its test.
- The middleware passes non-HTML responses through and keeps status, statusText and headers; its cost is one linear tokenization per page.

## cto-reviewer
VERDICT: PASS
risks_checked:
- The middleware is a new build mechanism with no new package; its approval is named in protected_override; measured at 0.42 ms per page and 695 → 741 MB peak at 57,423 pages.
- The design check changes make it fail closed more often, not less.
- The recurring cost is build minutes only (+36 s per merge request, +76 s on main), declared in impact_map with its acceptance; no API, BigQuery or hosting effect.
- No secret-like content, workflow, settings or permission change in the diff.
