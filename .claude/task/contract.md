# Task contract — frontend foundation shell (#825)

> Written on a CLEAN tree, branch `feat/site-v2-foundation-shell` off `main` (`f855f12`).
> See docs/working_agreement.md §2 (contract), §10 (decision rights), §11 (blinded escalation).

objective: >
  Build the v2 site's shared shell: Layout.astro gains a global header (logo, 6-item nav, search,
  a working dark/light theme toggle, mobile hamburger+drawer) and a footer; system.css gains the
  responsive layout system it never had (nav inline >=700px, two-column main+rail page grid
  max ~1100px >=900px, full search field >=1010px). Turns the CPO-approved foundation mock
  (artifact 87d14109, "looks good for now") into real code, composing only from the locked
  system.css tokens. Writes the two missing specs (docs/wireframes/09_chrome.md + a layout-system
  section in 00_overview.md). Issue #825.

refs: >
  .claude/active_work.md (2026-07-26 handover); docs/site_architecture.md §4 (nav is fixed:
  "Competitions · Matches · Teams · Players · Standings · Stats"); docs/ui_design_brief.md §5/§7
  (persistent search + nav, footer/legal component); mock artifacts 87d14109 (foundation, approved)
  and 1c35e7aa (home content, reference only — not built here); memory feedback_design_off_the_cuff
  (build approved designs, no invention) and feedback_doc_clutter_discipline (fold into the
  authoritative doc).

scope_paths:
  - site_v2/src/layouts/Layout.astro
  - site_v2/src/components/chrome/**
  - site_v2/src/styles/system.css
  - site_v2/src/i18n/strings.ts
  - docs/wireframes/09_chrome.md
  - docs/wireframes/00_overview.md
  - .claude/active_work.md

impact_map: >
  Leaf/cosmetic short-form (site_v2/** is structural surface by path, but carries no dbt/warehouse
  read or write): this PR touches only Astro components, one CSS file, one i18n dict, and two
  wireframe docs under site_v2/src and docs/wireframes. No dbt model, mart, seed, or BigQuery
  table is read or written; no export script changes. Blast radius: every page that imports
  Layout.astro (today: site_v2/src/pages/[lang]/teams/[team].astro and
  .../[competition]/matches/[fixture].astro) visually gains a header and footer — their own
  template files are not edited, and their existing data bindings/content are unchanged. The
  per-locale index.astro placeholder stub does NOT import Layout today and is untouched. CI
  surface: .github/workflows/ci-site-v2.yml (Astro build, path-filtered to site_v2/**) is the
  applicable gate; ci-ui.yml only path-filters the legacy site/ MVP and does not apply.

decisions_taken: >
  Foundation-first + lean process (CPO 2026-07-26, active_work.md). Foundation mock 87d14109
  approved "looks good for now". Approved this session (active_work.md): widen the shell chrome
  to two-column ~1100px; dark default + a light toggle; the nav list
  (Competitions/Matches/Teams/Players/Standings/Stats) as the specified start; the three
  breakpoints (700/900/1010px). Plan-mode approved 2026-07-26: nav/footer items with no built
  target render inert (span, not <a>) — same convention already shipped on the fixture page
  breadcrumb and the team page's Explore chips (both hrefless-by-comment for unbuilt targets);
  team/fixture pages are not restructured into the two-column grid (no file edits to either page);
  theme choice persists via localStorage so the toggle survives static-page navigation; search is
  visually present but inert; the layout-system doc section folds into 00_overview.md.

decisions_reserved:
  - Exact nav contents/order — the listed order is the specified start; refine only on CPO word.
  - Search style/mechanism — a real input, autocomplete, and any backend are undecided; this PR
    ships the mock's inert placeholder only.
  - What fills the desktop RAIL per page type (home = standings/trending/scorers per the
    home-content mock 1c35e7aa) — the .shell/.page-grid/.rail primitive is built generically in
    system.css but wired into zero pages this task.
  - Footer/legal content — the Imprint slot stays pending (blocked on the operator/address
    question, #799); not resolved here.
  - Default-theme policy (dark-fixed vs follow-OS) — this PR ships hard-coded dark as the
    no-preference default, per the approved default; whether the site should ever read
    prefers-color-scheme instead is not decided.
  - The fixture/team wireframes' (01/02) own desktop spec calling for those pages to widen to
    ~1100px is a real, currently open gap. Retrofitting an already-shipped, CPO-approved 680px
    page's width is a separate design decision, not made in this task — recorded as an open note
    in the new layout-system section, not closed.

done_when:
  - cd site_v2 && npm ci && npm run build succeeds; dist/index.html and dist/{de,en,fi}/index.html
    exist (mirrors ci-site-v2.yml).
  - Team page and fixture page render with the new header/footer, at phone/tablet/desktop widths,
    with the three breakpoints (700/900/1010px) firing correctly.
  - Theme toggle flips data-theme and the choice survives navigating between the fixture and team
    pages (localStorage persistence).
  - docs/wireframes/09_chrome.md written per the 00_overview.md template; 00_overview.md's screen
    inventory row 09 flips from pending to spec'd; component census updated.
  - ONE commit; review.md with scope-auditor + cto-reviewer + bi-analyst-reviewer verdicts, hash
    matching the staged diff; pushed with an explicit refspec; PR opened. CPO merges.

amendments: (none)
