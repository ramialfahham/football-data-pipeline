# Task contract — German is measured like the other two languages

objective: >
  The measured design check renders German as well as English and Finnish, so a German layout
  break fails `validate:ui` instead of passing it silently; its summary stops overstating its own
  coverage; and the check's language set is pinned against the site's declared locales so it
  cannot drift again. Separately, the one German string still saying "Team" for a club takes the
  word the rest of the German copy uses. No page, route, payload, mart or rule changes.

refs: >
  Both items are the builder's, handed back by the CPO on 2026-09-23 after being put to him as
  open questions: "Well, here is a lot of blabla that reads like you need something from me!!"
  Neither is a naming or product decision. The third item raised with them — whether page
  addresses follow a written vocabulary — IS his and is not in this task.

  1. THE CHECK HAS NEVER RENDERED GERMAN. `scripts/check_design_inventory.py:39` reads
  `DEFAULT_LANGS = ("en", "fi")`, and CI invokes it with no `--langs`. This is NOT a rule
  extension: `docs/wireframes/block_standard.md:77` already RULES the tab bar "the tabs share the
  row and fit in one row at 375px in EN, DE and FI". The ruling names three languages; the guard
  enforces two, so it has never enforced the rule as written. Tuning a guard toward its own rule
  is the builder's (memory: guard tuning is the builder's).
  It cost something real on #151: the German tab bar took the longest word of the nine
  (`Ranglisten`, 118px of 343) and had to be measured BY HAND, outside the gate, because the gate
  does not look. A German-only overflow would have shipped green.
  Measured before planning, on `main` at `db70ab1d` with a fresh build:
  `--langs en,de,fi` → `20 pages · 2 viewports · 3 languages · 94 renders · 0 failures · 0
  warnings`. German passes clean today, so this closes a blind spot rather than opening a backlog.

  2. ONE GERMAN STRING STILL SAYS TEAM. `searchPlaceholder` (`strings.ts`, DE) reads "Teams,
  Spieler suchen…". Every other German club reference is Mannschaft(en) — `navTeams`,
  `homeTopTeams`, `homeTopTeamsIntro`, `compDeservedExplainer`, and, since !216, the competition
  page's title, description and headings. A sweep of the German dictionary shows this is the only
  remaining outlier. The bi-analyst flagged it while reviewing !216 and correctly ruled it out of
  that branch's scope: "pre-existing, branch-untouched … worth a future consistency pass". This is
  that pass. The word itself is settled by the CPO's ruling on !216, so no new naming call.

scope_paths:
  - scripts/check_design_inventory.py
  - tests/test_design_inventory.py
  - site_v2/src/i18n/strings.ts
  - docs/wireframes/block_standard.md
  - design-mocks/README.md
  - .claude/skills/validate-local/SKILL.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/active_work.md
  - docs/tracker/gitlab_snapshot.md

impact_map: >
  Two independent leaf changes, ridden together deliberately — see decisions_taken.

  THE CHECK. `DEFAULT_LANGS` feeds one `--langs` default. Built pages need no other code:
  `resolve_built` substitutes the first `en/` of the Pages-table URL, and the German tree is the
  same shape (443 `index.html` under both `dist/de` and `dist/en`). The `FI` column does NOT gate
  built pages — that branch is inside `if p.kind == "mock"`. The mocks stay EN/FI: their
  generators emit `(en, fi, probe)` tuples into one HTML with a CSS toggle, there is no German
  text in any mock, and the FI strings are documented as width probes, not approved copy. The
  existing guard `if lang not in ("en", "fi"): continue` already skips them correctly.
  ⚠ Because of that skip, the summary's `len(langs)` would claim "3 languages" while 13 of the 20
  pages saw two. A gate overstating its own coverage is the very defect being fixed, so the
  summary states the mock set.
  ⚠ SWEEP BY THE CONCEPT: four LIVE places write "EN and FI" in prose and go stale on this
  commit — `block_standard.md:12`, the `validate:ui` comment in `.gitlab-ci.yml`,
  `.claude/skills/validate-local/SKILL.md`, `design-mocks/README.md`. THREE ARE FIXED HERE; THE
  CI COMMENT IS NOT, AND STAYS STALE. `.gitlab-ci.yml` is a protected governance path: the
  contract gate refuses the edit without a CPO-approved `protected_override`, and a comment is
  not worth loosening a guard or spending a governance task on. Disclosed on the MR head rather
  than quietly left. Not touched, deliberately:
  `docs/tracker/gitlab_snapshot.md` (generated from GitLab, never hand-edited) and
  `.claude/task/acceptance_evidence.md`'s pasted historical readings.
  No test asserts a language or render count: `tests/test_design_inventory.py` pins floors and
  shapes, and its two subprocess proofs pass `--langs en` explicitly, so they are unaffected.
  CI: `.ui_paths` already covers every file here, so `validate:ui` fires on its own.

  THE STRING. One value, read at one call site (`SiteHeader.astro`, the search input's
  placeholder). `docs/wireframes/09_chrome.md` names the KEY, not the value, so it does not move.
  The legacy corpus has no search placeholder. Nothing pins the value.
  blast_radius: the check does 14 more renders per run; every German page shows the new
  placeholder; no page, link, payload or rule changes.

acceptance_criteria:
  - `python scripts/check_design_inventory.py --dist site_v2/dist`, with NO `--langs` flag, exits 0 and reports 3 languages and 94 renders, naming the two languages the mocks were measured in.
  - The German built pages are actually measured: a deliberately broken German-only rule is caught. Demonstrated by running the check against a mutated German string and showing the FAIL line carries `de`, then reverting.
  - `tests/test_design_inventory.py` fails when `DEFAULT_LANGS` drops a locale the site declares in `site_v2/src/lib/href.ts`, and passes as shipped. Seen RED.
  - Every built page under `site_v2/dist/de/` shows the header search placeholder "Mannschaften, Spieler suchen…", and no German page still shows "Teams, Spieler suchen…".
  - The German header at 375 and 700 px: the search input's placeholder is not clipped, and the page's `scrollWidth` is no worse than it was before this change (the 700px header overflow is pre-existing and disclosed, not introduced here).
  - No live document the contract may touch still says the check renders "EN and FI"; the one in `.gitlab-ci.yml` is named on the MR head as knowingly left, being behind a protected path.

decisions_taken: >
  ONE BRANCH FOR TWO UNRELATED ITEMS, stated so the scope-auditor judges it rather than discovers
  it. The design check would never have caught a word choice; they are connected only by both
  being German parity and both being one-liners. One review cycle rather than two is the whole
  reason. If the auditor calls it scope drift, splitting is cheap and the builder splits.
  The mocks are NOT given German. Inventing German copy for a width probe is the coined-word trap
  the CPO caught on !216's Finnish label; the mocks' own header says the FI strings are probes,
  not approved copy.
  The `FI` column is NOT renamed to a general per-language field. It would touch the schema, the
  table header and all 20 rows and buys nothing: German reaches built pages without it, and the
  mocks have no German to reach. Its definition line is corrected to say it governs the mocks'
  toggle only, which is already true.
  The German placeholder keeps the existing comma form ("Mannschaften, Spieler suchen…"), mirroring
  the English "Search teams, players…", so only the word changes.

decisions_reserved:
  - Whether page addresses follow a written vocabulary before go-live. The CPO's, raised by him on !216, deliberately not touched here.
  - Whether the mocks should ever carry German copy. That needs approved German strings, which would be a naming decision; today the mocks are measured in EN and a documented FI width probe.

done_when:
  - `python scripts/check_design_inventory.py --dist site_v2/dist` exits 0 with the new summary; the German FAIL demonstrated and reverted.
  - `python -m pytest tests/test_design_inventory.py -q` green, the new pin seen RED.
  - `python scripts/check_copy_gate.py`, `python scripts/check_ui_i18n_metrics.py` exit 0; `cd site_v2 && npm test` green; `npm run build` green.
  - `grep -rn "EN and FI" docs/ design-mocks/ .claude/skills/` returns nothing that describes this check (`.gitlab-ci.yml` excluded and disclosed).
  - The German header measured at 375 and 700 px and recorded in `rendered_page_evidence.md`.

amendments:
  - none yet
