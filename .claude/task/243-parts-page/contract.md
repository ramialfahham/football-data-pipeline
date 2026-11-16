# Task contract — the parts page: every form each registered part takes today

objective: >
  Part of issue 243 (the component system). Build `scripts/parts_page.py`, a read-only tool that
  crawls the running Astro dev server over one page of each built page type, collects every
  rendered instance of every part in `docs/design/components.yml`, and writes one self-contained
  HTML page (gitignored, `design-mocks/parts_page.html`): a consistency report on top (distinct
  forms per kind; the same text on one page in more than one style; the same part with other
  child elements or other style values from page to page), then a section per kind showing each
  part's distinct forms side by side at 375px, then at 1000px, with what tells them apart. An
  inventory only: no page, no style and no `system.css` changes.

refs: >
  Issue 243, reopened 16 Nov 2026; the parts sheet is the step before composing pages from
  registered parts. Task brief from the coordinating session, 16 Nov 2026.

scope_paths:
  - scripts/parts_page.py
  - tests/test_parts_page.py
  - .claude/task/243-parts-page/contract.md
  - .claude/task/243-parts-page/review.md
  - .claude/task/243-parts-page/review_input.patch

depends_on:
  - none: reads main's site and registry as they are; no open MR.

shared_files:
  - none: no design baseline, chart manifest or chart pin changes.

approved_design:
  - none: no page output changes

decisions_taken: >
  The page list is the built rows of the Pages table in `docs/wireframes/block_standard.md`, each
  given one concrete URL from the local data; the Team page row is crawled twice, a club and a
  national team. A built row without a URL fails the run. A part's selector is the registry
  check's own rule (`selector`, else `.` + class). Each instance keeps a shallow clone of every
  ancestor plus that ancestor's `input` children: the tabs, folds, filters and switches are CSS
  radio state, and without the input a tab panel renders hidden. The dev-only
  `data-astro-source-*` attributes are dropped; a same-origin `url()` in the CSS (the Inter font)
  is inlined as a data URI so the page is self-contained. Every form is re-rendered in its frame
  and its computed style compared with the live capture; a form that differs is flagged on the
  page. Kinds are a fixed table in the script from component and part keys; a part in no kind is
  listed under "Not placed" with its count. Same-text detection runs over every visible text node
  on a page at one width, text of 3+ characters with a letter. A part's child elements are its
  descendants' classes, leaving out the classes that follow the data or the state (W, D, L,
  winner, the active tab, the unbreakable unit, the fitted form); a style value counts as a
  page-to-page difference only when one page's set of values differs from another's. The page is
  written to a draft file and moved into place only after the drawing check. The browser tests
  skip where Playwright's Chromium is missing, which includes CI's `test:python`; running them in
  `validate:ui` would edit `.gitlab-ci.yml` and is left out. No new mechanism: a manual tool,
  no gate, no CI job; Playwright is already pinned in `requirements-ui.txt`. No recurring cost.
  One read-only BigQuery export of one national team (Germany) for local data, about 352 MB,
  not committed.

decisions_reserved:
  - which form each part keeps: the CPO's, one part per round, after this page.

done_when:
  - python -m pytest tests/test_parts_page.py -q passes.
  - python -m pytest tests/ -q is green.
  - python scripts/ci_local.py --mr passes.
  - The generated page opens from a localhost URL served by python -m http.server.
  - The MR pipeline is green and python scripts/merge_ready.py <IID> says ready.

amendments: (none)
