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
  half; the "every kind of competition" half and the choice of the English words stand.

  Names stay one spelling in every language. That is the existing rule of §3 "Slugs
  (locale-independent)", ruled 2026-07-27, and this task does not reopen it; it only separates
  words from names so the two rules cannot be read as one.

  The seven rules are the plan he approved, written into the document that owns the URL scheme,
  where a changed mind replaces the text (working_agreement §11). The word list is proposed copy:
  it goes on the MR head for him, and his merge is the approval of every word.

  Threshold declarations: no new mechanism (a document edit; the word table in code, the collision
  check and the hreflang change are the switch's, in its own issue), no recurring cost.

decisions_reserved:
  - The 18 words themselves (6 pages x 3 languages). User-visible naming, his. Put on the MR head
    as proposed copy; he changes any of them there or by editing before merge.
  - The words for pages not designed yet (Standings, Statistics, head-to-head, stat definitions).
    Named with each page's own design, not here.
  - The address switch itself: its build issue, its order against the Matches hub build.
  - Whether the country hub line (`/football/{country-slug}/`, struck from the menu by #128)
    leaves §3. Not this task; the word table simply does not name it.

done_when:
  - "`docs/site_architecture.md` §3 separates words from names, carries the seven rules and the word table (6 pages x EN/DE/FI), and no line in it says a word is the same in every locale."
  - "A sweep of docs/ for the old rule (`every locale`, `same segment`) finds no other home of it."
  - "Every word in the table checked against the 48 competition slugs in `docs/competition_registry.yml`: no clash."
  - "Routed reviewers PASS; `review.md` bound with `--staged-hash`; MR open with the word list on its head."

amendments: (none)
