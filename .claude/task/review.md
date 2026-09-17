# Review — feat/153-check-in-ci — 2026-09-17

diff_sha256: 2f02d4aa229716e53f6d370a75b79e417d842f1f1335e996f520697c735e6811

rounds: 4
rounds_cap_override: round 4 swaps two script lines after the throwaway proof the CPO asked for
  (!199) showed the inventory tests' fixture stopping the job before the check reached the built
  pages, and his reply to that proof was "fail"; no reviewer FAIL stands from round 3, and he did
  not rule on the cap.

Round 1: all four PASS. The cumulative diff includes the stacked base branch (!196); its
files are outside this contract's scope by design and reviewed there. This MR's own change is
`.gitlab-ci.yml`, the CI-pin block at the tail of `tests/test_design_inventory.py`, two rows in
the validate-local skill's mapping table and the contract. Every pin went red on a one-line
mutation of its property before the review (needs, image tag, script step, artifact path, rules
anchor, stage) and green on restore.

Round 2, after the first pipeline: `validate:ui` went red on the three CI-pin tests themselves,
which parse the CI file with PyYAML — absent from `requirements-ui.txt`, present on the
workstation from `requirements.txt`. Round 1's platform verdict had asserted the job's imports
were covered; the pipeline showed otherwise. The fix: `PyYAML==6.0.3` pinned in
`requirements-ui.txt` (added to `scope_paths`, the round recorded in `amendments`), and a test
that walks the imports of the test file and the three scripts the job runs and fails on any not
pinned there — red on the first pipeline's state, green with the pin. scope-auditor,
platform-reviewer and cto-reviewer re-ran on the three staged files; bi-analyst-reviewer's
round-1 PASS stands, none of its surfaces changed. platform-reviewer's verdict at round 2 was
a fail (resolved at round 3): the coverage test walked a hand-written list of four files and
missed `check_ui_i18n_metrics.py`, which the job also runs. Round 3: the test derives its
files from the job's own script lines and follows imports into `scripts/` siblings; red on
an `import requests` added to the i18n script, red without the PyYAML pin, green on the tree.

Round 4, after the proof on !199: the check runs before the inventory tests in `validate:ui`,
so a page or stylesheet defect yields the per-page lines and the screenshot artifact instead of
stopping at the fixture; a pin holds the order, red with the old order. scope-auditor,
platform-reviewer and cto-reviewer re-ran; bi-analyst-reviewer's PASS stands.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 4 (a fail first, resolved in the round): the coverage-test rewrite of round 3 had reached the auditor only through the review record, not the contract; the contract's `amendments` now names it. Then the full read: the regex runs over the parsed `script` list, so only real steps match and argument paths like `site_v2/dist` cannot; the sibling walk checked against all 33 files in `scripts/` — no collision today; caveat recorded: a third-party import sharing a name with a file in `scripts/` would be followed as a sibling and its pin not checked (fail-open in the general case, not fail-closed as the builder had said — though `scripts/` is first on `sys.path` for the test and for every `python scripts/x.py`, so the sibling is what would import at runtime too); the order pin matches the file; the CPO's words attributed as said.
- Round 2: the scope widening is one path, `requirements-ui.txt`, matching the fix's footprint; the amendment's account matches the mechanism (`_ci()` imports `yaml` to parse the CI file; the new test walks the AST of the test file and the three scripts, maps `yaml` to `pyyaml`, fails when the distribution is absent); the pin is an exact pin of a library the repo already uses, in a file round 1 had already established as carrying every package the job needs — a bug-fix-level implementation detail, not a §10 dependency decision; the three staged files are the only change since round 1; the AST walk reaches the deferred `import yaml` inside a function body.
- Round 1: the diff is confined to the four files in `scope_paths`; the `design-mocks/README.md` and other hunks in the patch belong to the stacked base branch and were not re-reviewed.
- `protected_override`: the quoted blinded answer and the plan-mode approval match the plan file's "MR 3" section and its "Decided in this planning" item 1 — no contradiction.
- `validate:ui` and `build:site-v2` share the widened `*ui_paths` anchor, identical `rules` with `*not_on_schedule` first, the same `build` stage — matching `impact_map`'s "what fires it" and "failure behaviour" exactly.
- Image/pin: the image tag's version equals `requirements-ui.txt`'s `playwright==` pin and the test pins the equality plus the install line — `decisions_taken`'s claim is evidenced.
- The CI-shape tests pin `needs`, shared stage and rules, the artifact path and the three steps — what `impact_map`'s "what imports it" claims.
- `decisions_taken` declares, not hides: the anchor widening spelled out path by path, the stage move and the requirements switch named as implementation of the approved plan; no new cadence or schedule branch.
- Credential sweep of the four hunks: none. `done_when` entries each checkable.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 4: no enforcement lost by the swap — a check that wrongly exits 0 is followed by the pytest step, a check that exits non-zero is the job red at the right step, a green tree runs both as before; the check writes its screenshots inside its page loop and returns its exit code at the end, so with the check first the on-failure artifact is populated before the job stops; GitLab stops at the first non-zero step, and skipping the RED-proof tests on a run that is already red for a real defect is no coverage loss since both steps run on every green tree; the order pin's two substrings each occur once in the job's script and `str.index` fails loud if either is removed; the file order at `.gitlab-ci.yml` 499-504 matches the pin; the round-3 coverage test is order-independent; the round-4 amendment matches the diff without overclaim.
- Round 3: the coverage test derives its files from `validate:ui`'s own script lines — the regex traced against the job's real list, catching `python scripts/x.py --flag` and `python -m pytest tests/x.py -q`; the final `>=` assertion pins that `check_ui_i18n_metrics.py` is reached; `assert queue` catches an empty walk and a captured non-existent path errors the test rather than passing it; sibling resolution checked against all 33 files in `scripts/` — no third-party name collides today, and the failure direction if one ever did is a spurious fail, not a silent pass; no relative imports in `scripts/`; the regex runs on parsed YAML, so a commented line cannot match.
- Round 2 (a fail, resolved at round 3): the coverage test walked a hand-written list of four files and omitted `scripts/check_ui_i18n_metrics.py`, run by the same job in the same environment — stdlib-only today, but the test promised every package the job imports and structurally could not see a future third-party import there. Also checked then: the `PyYAML==6.0.3` pin matches the file's convention; the deferred `from playwright.sync_api import ...` in the check and the test and the `import yaml` inside `_ci()` are all caught by `ast.walk`; `sys.stdlib_module_names` exists on the image's 3.12; the two local modules excluded; one `pip install` call, no ordering issue; the contract's amendment accurate and its scope entry matching the file touched.
- Artifact hand-off: `build:site-v2` declares `artifacts.paths: [site_v2/dist]` relative to the project root although it `cd site_v2`s to build; `validate:ui` never `cd`s and reads `--dist site_v2/dist` — both ends match.
- `--artifacts artifacts/design_inventory` matches the on-failure `artifacts.paths`; `check_design_inventory.py` creates the folder when the flag is given and writes `failures.json` and screenshots on hard failures, so the artifact is non-empty when it matters.
- CLI shape: `check_design_inventory.py` accepts `--dist` (default `site_v2/dist`) and `--artifacts`; `check_page_css.py` takes only an optional `--inventory`.
- Rules identity and the `needs:`-target constraint satisfied through the single anchor; `*not_on_schedule` first in both; only the four known `if:` spellings; the schedule guard in `tests/test_governance_hooks.py` evaluates both jobs to never on a schedule.
- Dependencies: every module the job's script imports is stdlib or in `requirements-ui.txt`; `pytest` is scoped to the one test file, so `requirements.txt` is not needed.
- Removing `<<: *python` lost the `python:3.11` image, `needs: []` and the `requirements.txt` cache key — each replaced explicitly; `PIP_BREAK_SYSTEM_PACKAGES` is job-level and merges with the global `PIP_CACHE_DIR`.
- The widened anchor's new firings (`validate:ui` on `.gitlab-ci.yml`-only and `site/**`-only changes, `build:site-v2` on `site/**`) are the documented consequence of the shared anchor, priced in `impact_map`.
- `test_persist_docs_policy.py` keys on `dbt docs generate` cadence and `test_governance_doc_parity.py` on the protected-path set — neither touched by a job-body edit.
- The CI-pin tests import `yaml` locally, as `tests/test_governance_hooks.py` does; both jobs are stateless, so a re-run or a kill leaves nothing to reconcile.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- This MR's own diff touches none of the display surfaces: the four files and their hunks confirmed against the patch; every `site_v2/src/**` and `docs/wireframes/**` hunk belongs to the stacked base branch reviewed on !196.
- Both jobs in `stage: build`, both on `*ui_paths`, `*not_on_schedule` first.
- Coverage: the Pages table's five built rows cover five of the seven `site_v2/src/pages/**` routes; the player page has no row, a CSS-conformance gap that belongs to the block standard on !196, not to this MR.
- The check measures CSS and layout facts only (sizes, colours, gaps, edges, stripes, tints, fit, visibility); it never reads metric values, percentages, field bindings, row order or i18n strings, so which pages CI measures adds or removes no enforcement of the metric or i18n display contract; `metrics_display.md` (LOCKED) unaffected.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Round 4: a step reorder inside the already-ruled job — no new script, dependency, cost or cadence — is implementation of the ruled mechanism, not a new §10 class; the order is pinned by test, not prose; fail-closed preserved (no `allow_failure`, no `|| true`; only the diagnostic detail on a red run changes); a false-negative check still falls through to the RED-proof tests, so no defect goes undetected because of the reorder; the override line attributes to the CPO only what he answered ("fail" on the proof) and says he did not rule on the cap — round 4 finishes the already-approved proof criterion rather than opening scope; whether an honest-but-non-explicit override satisfies the gate is process, not authority, and noted; no credential or protected-path change beyond the covered CI file.
- Round 2: the `PyYAML==6.0.3` pin fills a gap in the already-ruled "own small requirements file, pinned" mechanism for a package the repo already depends on (`requirements.txt`'s `PyYAML>=6.0`) — no new dependency, no new mechanism, no fresh approval needed; `*requirements*.txt` routes to cto and platform and the contract declares it; the floor-in-one-file, exact-pin-in-the-other pattern already exists for `pytest` and needs no guard now; the coverage test fails closed (an unpinned import fails the assertion, which fails the job) and catches the deferred playwright import inside a function body; the hand-maintained file list it walked was noted as platform territory — resolved in round 3 by deriving the list from the job's script lines. `.gitlab-ci.yml` untouched this round.
- `protected_override` quotes a blinded two-path CPO ruling naming exactly this shape (the Playwright image, the pinned `requirements-ui.txt`, "no money; a minute or two per pipeline", the single runner) and the diff stays inside it: no mechanism beyond the job wiring `decisions_taken` enumerates.
- `impact_map` non-placeholder: writers, what fires it, what imports it, what stops being enforced, failure behaviour, deploy order, blast radius.
- Routing: `.gitlab-ci.yml` is one of the three guard paths carrying both cto and platform, per `review_routing.json` and the doc-parity test.
- The image as a new dependency: pin equality enforced by test, logic checked by hand against the real tag and pin.
- Nothing enforced stops: the new anchor is a strict superset of both old anchors; `validate:ui`'s existing steps kept byte for byte, three appended.
- The stage move: `stages:` is UI grouping by the file's own comment; nothing needs either job; the two stage-keyed governance tests key on `deploy` only.
- The `needs:` shape is pinned, and the `deploy:nightly-image`/`build:nightly-image` precedent the contract cites is real and does the same.
- Cost: `scripts/check_*.py` in the widened anchor also match `.data_paths_mr`, so the two design scripts already fire the BigQuery-billed `data:build:mr` — pre-existing from the stacked branch and disclosed in `blast_radius`, not left implicit.
- `test:python` unaffected: the test file's browser import is deferred and its `ImportError` caught, so it skips there.
- `decisions_taken` against §10: the stage placement and the shared anchor are forced by GitLab's constraints, the requirements file is in the CPO's own quote, the seven-day retention has three sibling precedents in the file — none crosses into a CPO-only class beyond the ruling cited. No credential or permission widening.

## escalations
(none)
