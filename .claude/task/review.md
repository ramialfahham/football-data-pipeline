# Review — feat/153-check-in-ci — 2026-09-17

diff_sha256: f3bc804e907a9a9d5c591f9c958aee11617440a68c6a898d42c877a1155e2c59

rounds: 1

Round 1: all four PASS. The cumulative diff includes the stacked base branch (!196); its
files are outside this contract's scope by design and reviewed there. This MR's own change is
`.gitlab-ci.yml`, the CI-pin block at the tail of `tests/test_design_inventory.py`, two rows in
the validate-local skill's mapping table and the contract. Every pin went red on a one-line
mutation of its property before the review (needs, image tag, script step, artifact path, rules
anchor, stage) and green on restore.

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: the diff is confined to the four files in `scope_paths`; the `design-mocks/README.md` and other hunks in the patch belong to the stacked base branch and were not re-reviewed.
- `protected_override`: the quoted blinded answer and the plan-mode approval match the plan file's "MR 3" section and its "Decided in this planning" item 1 — no contradiction.
- `validate:ui` and `build:site-v2` share the widened `*ui_paths` anchor, identical `rules` with `*not_on_schedule` first, the same `build` stage — matching `impact_map`'s "what fires it" and "failure behaviour" exactly.
- Image/pin: the image tag's version equals `requirements-ui.txt`'s `playwright==` pin and the test pins the equality plus the install line — `decisions_taken`'s claim is evidenced.
- The CI-shape tests pin `needs`, shared stage and rules, the artifact path and the three steps — what `impact_map`'s "what imports it" claims.
- `decisions_taken` declares, not hides: the anchor widening spelled out path by path, the stage move and the requirements switch named as implementation of the approved plan; no new cadence or schedule branch.
- Credential sweep of the four hunks: none. `done_when` entries each checkable.

## platform-reviewer
VERDICT: PASS
risks_checked:
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
