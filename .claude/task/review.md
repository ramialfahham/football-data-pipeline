# Review — feat/153-design-mocks-of-record — 2026-09-17

diff_sha256: 01d4ad98d3b426be79832930389c0377048f9cbcf2f7531654f47ca5415b29a4

rounds: 3

Round 1 (2026-09-16, the four generators and five pulls): scope-auditor PASS. Round 2 (the render
naming rule added under the contract's amendment): scope-auditor PASS; platform-reviewer's verdict
then was a fail (resolved at round 3): the overwrite guard in `render.py` was reached by no test,
so deleting it left every test green. Round 3: a test reaches the guard through `main()` with the
name picker patched to return an existing name; the guard replaced by `if False:` turns it red.

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every file in the cumulative diff (`design-mocks/render.py`, `tests/test_design_mock_renders.py`, the four `design-mocks/renders/*.html`, `design-mocks/README.md`, `.claude/task/contract.md`, the round-1 generators and JSON pulls) matches `scope_paths` exactly; nothing extra touched.
- New mechanism (`render.py`'s naming and refuse-overwrite): a §10-class decision, carried by the contract's `amendments:` block — the #153 plan approved in plan mode 2026-09-17 and the CPO's answer to the blinded question, "Track them in git, in a renders folder" (2026-09-16, in chat) — not taken silently.
- `escalations.log` untouched (frozen); the amendment cites the chat answer and fabricates no log entry.
- The gitignore claim checked: `.gitignore:239` is `design-mocks/*.html`, a single-level glob that does not reach `design-mocks/renders/`, unchanged in the diff; the test verifies it independently through `git check-ignore`.
- `design-mocks/README.md` updated in the same branch for the new folder and rule (doc-sync).
- Implementation matches the amendment's prose word for word (the pattern, the per-page counter that never resets, the refusal, the four test rules); no quiet extension of the rule.
- Secrets swept across the full patch including the four HTML renders: only CSS "design token" comments.
- Impact map: only `design-mocks/**` and `tests/**` touched — no structural path, none required.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The round-2 finding closed: `test_render_refuses_a_name_the_folder_already_holds` reaches the guard through `render.main()` via a monkeypatched `next_name`, asserts `SystemExit` matching "refusing to overwrite", the pre-existing file's content and the folder listing unchanged; the mutation (guard replaced by `if False:`) turns it red.
- `__import__("datetime")` replaced by a plain import in the test; `render.py` imports `datetime as dt`; no `__import__` remains.
- The rest of `render.py` and the test file unchanged since round 2: `parse_name`, `numbers`, `next_name`, `main`'s other exits (usage, missing generator, generator that writes nothing) and the two-writes happy path are as reviewed.
- Path handling: `render.py` passes an absolute path as the generator's one argument and each generator does `HERE / sys.argv[1]`, where an absolute right operand wins on both path flavours.
- `git check-ignore --no-index`: exit 1 means nothing ignored; only stdout is read, so it is not treated as an error.
- The `NAME` regex checked by hand against the four real file names; the comment-history markers traced against every comment and docstring line (the docstring's `home_2026-09-17_02.html` sits after `_`, so the date marker does not fire); ruff's default set clean.
- The README's description of the refusal matches the code and the test.

## escalations
(none)
