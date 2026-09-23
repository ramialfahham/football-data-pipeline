# Task contract — page addresses use the reader's language: the rules and the word list

objective: >
  Write down how page addresses are formed now that the CPO has decided their words follow the
  reader's language, and propose the word for every page the site has, in English, German and
  Finnish. Documentation only: the site keeps emitting the English words under every locale until
  the address switch is built, which is its own issue, filed once this word list is approved.

refs: >
  The decision, taken in this session on 2026-09-23. Asked "Should page addresses use the reader's
  language (/de/spiele/, /fi/ottelut/), or stay English in every language (/de/matches/)?", the
  CPO chose "Reader's language (Recommended)". The costs were put with the question: about two days
  of build work now, one name per word per language, and every future language naming them again;
  against English everywhere, which costs nothing now and means redirects for every German and
  Finnish page if changed after launch. He then approved the plan that carries these rules and this
  list as proposed wording, "yours to change".

  ROUND 2 (same day). He asked whether the first word list was researched ("are you guessing
  again?"); it was not. Research followed: the addresses of German, Finnish and English football
  sites, Google's autocomplete in each market, then an independent SEO assessment written by a
  reviewer with no stake in the first list (Google's documentation, John Mueller's statements, 13
  sites, about 100 autocomplete queries, sources per claim). Asked "Do you accept the address list
  in section 4 of the page, including B for the Rankings tab?", he answered "Basically, yes" and
  asked how it holds while most pages are not designed; the answer he was given: settled words for
  the pages built today, provisional words for pages not designed yet, confirmed or dropped at
  each page's own review, and tabs a future design adds named at that review by the same rule.

  Answers the open line of #46 ("Whether the tab segment is localised. /squad/ or /kader/ /
  /kokoonpano/? ... that rule was written about entity slugs, not path segments"). Restates #49
  item 1 (a competition slug can collide with a reserved segment) as a rule, which the switch
  enforces. The Matches hub (#130) needs its address word before its design can be recorded.

scope_paths:
  - docs/site_architecture.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  The direction is his, quoted above: address words in the reader's language. The two lines of
  §3 that pinned `/fixtures/` and `/rankings/` to "the same segment ... every locale" (his rulings
  on #129 and on #151's MR) are replaced, because this decision supersedes their "every locale"
  half and, since round 2, their English words too: the Matchdays tab takes the matches word and
  the Rankings tab `stats`, both accepted by him with the assessment's section 4 (see refs). The
  "every kind of competition" half stands.

  Names stay one spelling in every language. That is the existing rule of §3 "Slugs
  (locale-independent)", ruled 2026-07-27, and this task does not reopen it; it only separates
  words from names so the two rules cannot be read as one.

  The rules and the word list are written into the document that owns the URL scheme, where a
  changed mind replaces the text (working_agreement §11). Each word carries its evidence on the MR
  head, and his merge is the approval of every word.

  Threshold declarations: no new mechanism (a document edit; the word table in code, the collision
  check and the hreflang change are the switch's, in its own issue), no recurring cost.

decisions_reserved:
  - The words themselves. Accepted by him as the assessment's section 4 ("Basically, yes"); his
    merge of the MR head, which lists them with their sources, is the approval of each.
  - The words for pages not designed yet (the menu pages for Matches, Teams, Players, Standings and
    Statistics, the day pages, the per-statistic lists, head-to-head) and for any tab a future
    design adds. Written as PROVISIONAL, confirmed, changed or dropped at each page's own review.
  - Whether a metric's definition lives on its per-statistic page, replacing the separate glossary
    the scheme still lists. The Statistics section's review decides.
  - The match address's date: it moves when a league fixes its schedule, and it is the UTC date,
    not the local one (the assessment's section 6, risk 2). A separate decision, brought to him
    later; the scheme keeps the date until then.
  - The address switch itself: its build issue, its order against the Matches hub build.
  - Whether the country hub line (`/football/{country-slug}/`, struck from the menu by #128)
    leaves §3. Not this task; the word table simply does not name it.

done_when:
  - "`docs/site_architecture.md` §3 separates words from names, carries the rules and the word table in EN/DE/FI with every page marked settled (built today) or provisional (not designed yet), and no line in it says a word is the same in every locale."
  - "The URL scheme block and every other line of §3 name the new English words (`matches` for the Matchdays tab and match pages, `stats` for the Rankings tab, `teams`, `players`), so the document never shows two words for one page."
  - "A sweep of docs/ for the old rule (`every locale`, `same segment`) finds no other home of it."
  - "Every word in the table checked against the 48 competition slugs in `docs/competition_registry.yml`: no clash."
  - "Routed reviewers PASS; `review.md` bound with `--staged-hash`; MR open with the word list on its head."

amendments:
  - 2026-09-23, round 2, on a clean tree: the word list and rule 2 are replaced by the independent
    assessment's section 4, which he accepted ("Basically, yes"). The rule becomes: the address
    word is the menu word in that language, plural, and every page sits under the page that lists
    it (English uses `stats`). Changed words: teams `mannschaften` (was a guess), players
    `spieler`, the Matchdays tab takes the matches word (`matches` / `spiele` / `ottelut`), so
    match pages sit under their list page; the Rankings tab takes `stats` / `statistiken` /
    `tilastot` (option B) and keeps its on-screen name. Planned pages listed as provisional. No
    path added.
