# Task contract — the menu's last item reads Leaderboards, not Stats

objective: >
  Apply a ruling that was made and never shipped: the header and footer menu item "Stats" is
  renamed "Leaderboards". One copy key in three languages and its two call sites; no page, no
  link, no layout changes. The item stays dead text until #139 builds the hub behind it.

refs: >
  The ruling: #127 (CPO, 2026-09-13), recorded in `docs/wireframes/10_home.md` ("the menu item
  Stats is renamed Leaderboards") and in the approved-design section of #127 as the tracker
  snapshot carries it ("**Stats is renamed Leaderboards** (menu, footer, milestone 7, issues
  #139/#140)"). Milestone 7 was renamed; the menu was not. #143 built the other #127 rulings and
  its checklist does not carry this one, so the rename had no build item. #139 owns the hub the
  item will point at and is unbuilt; the label does not wait on it.
  Measured on `main` at `af081cae`: `navStats` is "Stats" / "Statistiken" / "Tilastot" in
  `strings.ts`, rendered by `SiteHeader.astro` (6th nav item, no href) and `SiteFooter.astro`
  (4th footer link) on every built page in all three locales.

scope_paths:
  - site_v2/src/i18n/strings.ts
  - site_v2/src/components/chrome/SiteHeader.astro
  - site_v2/src/components/chrome/SiteFooter.astro
  - docs/wireframes/09_chrome.md
  - docs/site_architecture.md
  - docs/north_star.md
  - docs/ui_design_brief.md
  - design-mocks/gen_navmap.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/active_work.md
  - docs/tracker/gitlab_snapshot.md

impact_map: >
  Leaf copy change on the consumption surface. `navStats` is read at exactly two call sites
  (`grep -rn "navStats" site_v2/` → `SiteHeader.astro:32`, `SiteFooter.astro:24`, and the three
  `strings.ts` definitions); two documents name the key (`docs/wireframes/09_chrome.md`'s chrome
  key table, `design-mocks/gen_navmap.py`'s navigation map). No page, route, payload, mart or
  export is touched; no `href` exists on the item, so no link graph changes and `audit-seo`'s
  link resolution is unaffected. The rendered change is one word in the header and one in the
  footer of every built page, per locale.
  blast_radius: every page of the built site shows the new word; nothing else moves.

acceptance_criteria:
  - Every built page under `site_v2/dist` shows "Leaderboards" as the sixth header item and in the footer link row in EN, the German word in `/de/`, the Finnish word in `/fi/`, and no page in any locale still shows "Stats", "Statistiken" or "Tilastot" as a menu item.
  - The item is still dead text (no `href`), since #139 has not built the hub: no page gains a link.
  - `python scripts/check_copy_gate.py` exits 0 and `cd site_v2 && npm test` is green; `python scripts/check_design_inventory.py --dist site_v2/dist` exits 0 (the chrome is on every measured page).

decisions_taken: >
  The English word is the CPO's ruling on #127, quoted in `refs`. The key is renamed
  `navStats` → `navLeaderboards` rather than left under its old name with a new value: the key
  is the name a reader of the code sees, and a key that says "stats" while rendering
  "Leaderboards" is the drift this task exists to fix.

decisions_reserved:
  - The German and Finnish words. The ruling gives English only. Drafted on the MR head for the CPO, as every new label is: DE "Bestenlisten" (the standard German term for leaderboards; the competition tab's DE "Rankings" is a different object, ruled 2026-09-17), FI "Kärkilistat" (the "Kärki" stem the validated corpus already uses for Home's "Kärkipelaajat" / "Kärkijoukkueet"). His merge is the approval; if he wants other words they are a one-line change.

done_when:
  - `grep -rn "navStats" site_v2/ docs/ design-mocks/` returns nothing.
  - `python scripts/check_copy_gate.py`, `python scripts/check_ui_i18n_metrics.py` exit 0; `cd site_v2 && npm test` green.
  - `npm run build` green; the acceptance criteria read from `dist` in `acceptance_evidence.md`.
  - `python scripts/check_design_inventory.py --dist site_v2/dist` exits 0.

amendments:
  - 2026-09-22: + `docs/site_architecture.md`, `docs/north_star.md`, `docs/ui_design_brief.md` — authority: the bi-analyst's round-1 FAIL (a document the diff contradicts must move in the same branch) and the rule that a correction replaces the old text everywhere it is written; content: the impact map swept for the KEY name (`navStats`) and the key name does not appear in prose, so five places that write the menu out in words kept saying "Stats" — `09_chrome.md` lines 19, 33, 38 and 81 (the quote, both ASCII diagrams, the states prose), `site_architecture.md:222` (the sentence `09_chrome.md:19` cites as its authority), `north_star.md:115` and `ui_design_brief.md:71`. Prose only; no code, no second behaviour change. The lesson recorded here rather than only fixed: sweep by the CONCEPT, not by the identifier.
