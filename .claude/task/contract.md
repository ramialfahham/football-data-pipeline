# Task contract — the menu item reads Statistics, the word football sites use

objective: >
  The header and footer menu item is "Statistics" / "Statistiken" / "Tilastot". One copy key in
  three languages and its two call sites, plus the documents that write the menu out. No page, no
  link, no layout change; the item stays dead text until #139 builds the hub behind it.

refs: >
  The ruling: the CPO on !217's thread, 2026-09-22 — "Premier League uses a menu 'Statistics'
  for leaderboards as well. Let's go with Statistics / Statistiken / Tilastot", after asking
  whether the German and Finnish drafts had been researched in a football context. They had not.
  The research, done then: premierleague.com's top-level item is Statistics and its page is
  the scorers and club-stats leaderboards; bundesliga.com's German section is Statistiken
  (`/de/bundesliga/stats`, "Statistiken 2025/26 | Spieler | Tore"); veikkausliiga.com's Finnish
  section is Tilastot (`/tilastot/pelaajat/`), with the individual lists named maalipörssi,
  syöttöpörssi and pistepörssi; kicker uses Rangliste for one ranking table and Torjäger for the
  scorers list. No German or Finnish football site in that search labels the section
  "Bestenlisten" or "Kärkilistat".
  This SUPERSEDES the English half of #127 (2026-09-13, "the menu item Stats is renamed
  Leaderboards"), which !217 shipped this morning together with two drafted words the research
  does not support. The hub behind the item keeps its own name — #139 is "Leaderboards hub: what
  this menu item lands on", milestone 7 is "7 · Leaderboards" — because what that page is called
  is #139's question, not the menu label's.
  Measured on `main` at `c0688e3b`: `navLeaderboards` is "Leaderboards" / "Bestenlisten" /
  "Kärkilistat" in `strings.ts`, rendered by `SiteHeader.astro` (6th nav item, no href) and
  `SiteFooter.astro` (4th footer link) on every built page in all three locales.

scope_paths:
  - site_v2/src/i18n/strings.ts
  - site_v2/src/components/chrome/SiteHeader.astro
  - site_v2/src/components/chrome/SiteFooter.astro
  - docs/wireframes/09_chrome.md
  - docs/wireframes/10_home.md
  - docs/site_architecture.md
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
  Leaf copy change on the consumption surface, the same shape as !217 a few hours earlier.
  The key is read at exactly two call sites (`SiteHeader.astro:32`, `SiteFooter.astro:24`) and
  named in two documents (`09_chrome.md`'s chrome key table, `design-mocks/gen_navmap.py`'s
  navigation map). No page, route, payload, mart or export is touched; the item has no `href`,
  so no link graph changes and `audit-seo`'s link resolution is unaffected.
  ⚠ SWEEP BY THE CONCEPT, NOT THE KEY — !217's round-1 FAIL. The word also appears as prose in
  the six-item menu list in `09_chrome.md` (the quote, both ASCII diagrams, the States bullet),
  `site_architecture.md:222` and `ui_design_brief.md:71`, and as a superseded ruling in
  `10_home.md:9`. Each of those is a menu label and moves. Each of these is NOT and stays:
  `site_architecture.md:247` (the `leaderboards/{league_code}` export payload row),
  `north_star.md:115` (the GitLab MILESTONE list, and milestone 7 is named Leaderboards),
  `10_home.md:1002` and `gen_navmap.py:155` (the Leaderboards PAGE, #139) — the hub keeps its name.
  blast_radius: every page of the built site shows the new word; nothing else moves.

acceptance_criteria:
  - Every built page under `site_v2/dist` shows "Statistics" as the sixth header item and in the footer link row in EN, "Statistiken" in `/de/`, "Tilastot" in `/fi/`, and no page in any locale still shows "Leaderboards", "Bestenlisten" or "Kärkilistat" as a menu item.
  - The item is still dead text (no `href`): no page gains a link, and `audit-seo` passes.
  - The word "Leaderboards" survives exactly where it names the HUB and not the menu item: `site_architecture.md`'s export payload row, `north_star.md`'s milestone list, `10_home.md`'s reference to the #139 page, and `gen_navmap.py`'s competition-page note.
  - `python scripts/check_copy_gate.py` exits 0; `cd site_v2 && npm test` green; `python scripts/check_design_inventory.py --dist site_v2/dist` exits 0.

decisions_taken: >
  All three words are the CPO's, quoted in `refs` with the evidence he cited (the Premier League
  menu) and the evidence gathered for the other two languages. The key is renamed
  `navLeaderboards` → `navStatistics` so the identifier says what the item says, the same reason
  `navStats` → `navLeaderboards` carried this morning.

decisions_reserved:
  - Whether the HUB and its milestone keep the name Leaderboards while the menu item leading there says Statistics. Not this task's: #139 owns what that page is called, and nothing published depends on it. Named on the MR head so the CPO sees the divergence rather than discovers it.

done_when:
  - `grep -rn "navLeaderboards" site_v2/ docs/ design-mocks/` returns nothing.
  - `python scripts/check_copy_gate.py`, `python scripts/check_ui_i18n_metrics.py` exit 0; `cd site_v2 && npm test` green.
  - `npm run build` green; the acceptance criteria read from `dist` in `acceptance_evidence.md`.
  - `python scripts/check_design_inventory.py --dist site_v2/dist` exits 0.

amendments:
  - none yet
