# Task contract — #153, the measured check in CI: `validate:ui` renders and measures every page on every MR

objective: >
  The last mechanism of #153: the cross-page measured check "runs in `validate:ui` on every
  MR", so one page breaking while another is worked on turns the pipeline red. `build:site-v2`
  keeps its built site as an artifact; `validate:ui` runs on the Playwright image, needs that
  build, and runs the page-CSS lint, the inventory tests (the RED proof) and the measured check
  beside its existing steps. Branch stacked on `feat/153-design-inventory` (!196), which holds
  the check, the lint and their tests; nothing here runs without them.

refs: >
  #153 ("A cross-page check that fails the build … Runs in `validate:ui` on every MR"; How step
  2); !196 (the check and the lint); the #153 plan approved in plan mode on 2026-09-17 (MR 3);
  `.gitlab-ci.yml` (`validate:ui` at 438, `build:site-v2` at 541, the path anchors at 362);
  `tests/test_governance_hooks.py` (the rule-condition classifier and the schedule guard every
  job must satisfy).

scope_paths:
  - .gitlab-ci.yml
  - requirements-ui.txt
  - tests/test_design_inventory.py
  - .claude/skills/validate-local/SKILL.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

protected_override: >
  `.gitlab-ci.yml` is a protected path. The mechanism it wires was the CPO's choice, to a
  blinded two-path question in chat on 2026-09-16 — "The cross-page check has to measure real
  pages (gaps, edges, tints, tab-bar fit). That needs a browser engine, and CI has none today.
  Which way?" — answered "Headless Chromium via Playwright, Python (Recommended)": "The
  measuring job uses Microsoft's ready-made image (browser preinstalled, no per-job download), a
  pinned playwright version in its own small requirements file. First image pull ~1.5 GB on
  ci-runner-01, cached after. No money; a minute or two per pipeline." The plan carrying this
  MR's job shape was approved in plan mode on 2026-09-17. The MR head repeats this quote under
  `Locked files`; the merge is the approval.

impact_map: >
  writers: none in the warehouse; no raw writer, no dbt model, no export script. The structural
  surface is the protected CI file itself.
  what fires it: every merge-request pipeline, every push to `main` and every web run whose
  changes match the widened `ui_paths` anchor — `site/**`, `site_v2/**` (the stylesheet and the
  components), `design-mocks/**`, `docs/wireframes/block_standard.md`, the three scripts, the
  inventory test, `requirements-ui.txt`, the CI file — the same anchor for `build:site-v2` and
  `validate:ui`, because GitLab refuses to construct a pipeline whose `needs:` target its own
  rules excluded (the `deploy:nightly-image` precedent in this file and its test). Schedules never
  run either job (`*not_on_schedule` first in both).
  what imports it: `tests/test_governance_hooks.py` parses the file — the rule classifier
  `_CONDITION_TRUTH` raises on an `if:` spelling it does not know (only the three known ones are
  used here), the schedule guard checks every job, `test_persist_docs_policy.py` counts jobs with
  a `script`, `test_governance_doc_parity.py` keeps the file in the protected set;
  `tests/test_design_inventory.py` gains pins on the new shape (the `needs`, the shared rules,
  the shared stage, the artifact path, the image tag equal to the `playwright==` pin, both
  scripts in the job's `script`).
  what stops being enforced if it is wrong: nothing that is enforced today — `validate:ui`'s
  existing steps (the legacy `site/` JSON and `node --check`, `check_ui_i18n_metrics.py`) stay
  in the job verbatim and keep their triggers, since the widened anchor is a superset of the
  old one; `build:site-v2` keeps its steps and gains only an artifact. What starts being
  enforced: the lint, the RED proof and the measured check on every MR that touches the site,
  the mocks or the inventory. #150 and #151 do not merge until that check passes on their pages
  (#153 How, step 4).
  failure behaviour: a red `validate:ui` blocks the MR like any job; the check's failing pages
  are screenshotted into a job artifact kept seven days. `validate:ui` moves to the `build`
  stage because a `needs:` target may not sit in a later stage than the job that needs it;
  stages are pipeline-UI grouping only (`.python`'s own comment), so nothing else moves. The
  image `mcr.microsoft.com/playwright/python:v1.63.0-noble` carries Python 3.12 and the
  browsers; the playwright package (`requirements-ui.txt`) must match the tag, pinned by test;
  `PIP_BREAK_SYSTEM_PACKAGES=1` because noble's system Python refuses `pip install` otherwise;
  apt's Node 18 keeps the legacy `node --check` working (jammy's Node 12 would not parse `??`).
  deploy_order: nothing reaches a host; `deploy:site-v2` is manual-only and untouched.
  blast_radius: the `data:build:mr` job is untouched and keeps firing on `scripts/check_*.py`
  (cost, not breakage). Recurring cost: the image pull once per runner (~1.5 GB, cached), then
  a job of a few minutes per qualifying pipeline on the self-hosted runner — no money.

decisions_taken: >
  The CPO's choice of a headless browser in CI (quoted above) and the approved plan's job shape.
  Taken here as implementation: one path anchor for both jobs (the `needs:` constraint);
  `validate:ui` in the `build` stage; `requirements-ui.txt` installed instead of
  `requirements.txt` (the job's steps import nothing from it — `check_ui_i18n_metrics.py` is
  stdlib); the check's screenshots kept as an on-failure artifact for seven days; the
  validate-local skill's mapping table naming the two new gates. No new mechanism beyond the
  one ruled; no other protected path.

decisions_reserved:
  - none: the mechanism and its shape were ruled and approved as cited; nothing here is a product, metric, naming or cost question beyond the recurring cost stated above (no money).

done_when:
  - `python -m pytest tests/test_governance_hooks.py tests/test_persist_docs_policy.py tests/test_governance_doc_parity.py tests/test_design_inventory.py -q` green locally (the CI-pin tests included).
  - `python -c "import yaml; yaml.safe_load(open('.gitlab-ci.yml'))"` parses; `glab ci lint` accepts the file.
  - The MR pipeline runs `build:site-v2` then `validate:ui` green (the check's summary line in the job log); a throwaway commit setting `.eyebrow` to 11px turns `validate:ui` red on every page, then is reverted — pasted into the MR head.
  - The MR open against `main` from the stacked branch, `Locked files:` carrying the quote above.

amendments: >
  Round 2: `requirements-ui.txt` added to scope. The first pipeline turned `validate:ui` red on
  the three CI-pin tests themselves — they parse the CI file with PyYAML, which the job's
  requirements file did not carry (the workstation had it from `requirements.txt`, so the
  tests were green locally). `PyYAML==6.0.3` pinned there, exact like the file's other pins.
  The pins still run in `test:python` as well, where `requirements.txt` provides it.
  Round 3 (the platform reviewer's finding): the coverage test no longer walks a hand-written
  list of files — it takes every `scripts/*.py` and `tests/*.py` the job's own script lines
  name and follows imports into `scripts/` siblings, so a step added to the job is covered
  without editing the test; a final assertion pins that the five files known today are reached.
  Round 4, after the proof on !199: the measured check now runs BEFORE the inventory tests in
  `validate:ui`. The tests' green fixture is measured against the live stylesheet, so with the
  tests first a stylesheet defect stopped the job at the fixture — one fixture page, two lines,
  no screenshots — and the check never reached the built pages; the proof the CPO asked for
  ("Do the throwaway proof on its own branch") showed exactly that and he called it a fail. With
  the check first, a page or stylesheet defect yields the per-page lines and the screenshot
  artifact; the RED-proof tests still run on every green tree and guard the check's own code.
  Enforcement is unchanged: the job is red if either step fails. A pin holds the order.
