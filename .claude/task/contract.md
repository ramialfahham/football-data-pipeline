# Task contract — #166: the footer repeats the menu, and the menu marks the page's section

objective: >
  The footer's link row repeats the menu's six items in its order, then About and Imprint, each a link
  exactly when the menu's item is. The menu and the phone drawer mark the section the page sits in.
  09_chrome.md says what the chrome now is.

refs: >
  #166 (the footer and the menu marking lines) as #132 decided them; render match-page_2026-10-07_75
  for the marked item. The plan, its readings and the acceptance criteria: approved in chat, 2026-10-09.

scope_paths:
  - site_v2/src/lib/menu.ts
  - site_v2/src/components/chrome/SiteHeader.astro
  - site_v2/src/components/chrome/SiteFooter.astro
  - site_v2/src/layouts/Layout.astro
  - site_v2/src/pages/*/*/*/*fixture*.astro
  - site_v2/src/pages/*/*/*/index.astro
  - site_v2/src/pages/*/*/index.astro
  - site_v2/src/pages/*/*/*day*.astro
  - site_v2/src/pages/*/*/*team*.astro
  - site_v2/src/pages/*/*/*player*.astro
  - site_v2/src/styles/system.css
  - docs/wireframes/09_chrome.md
  - tests/test_sentence_length_in_docs.py
  - tests/test_no_decision_history_in_code.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md

impact_map: >
  writers: none; no export or data change. menu.ts holds the six menu items SiteHeader.astro holds
    today.
  downstream: SiteHeader and SiteFooter render on every page through Layout.astro, so every built page
    changes in its footer row and, except Home, in one marked menu item. The new `section` prop is
    optional; a page that passes none marks nothing. system.css gains rules for `.mainnav .on` and
    `.drawer .on` only; `.on` is also used by `.comp-tabs .tab.on`, which the new selectors do not
    reach.
  layer_rules: the page names its section; the chrome formats and routes only.
  deploy_order: the site changes on the next manual deploy (deploy:site-v2).
  blast_radius: the footer and the menu on every page; no other text.

acceptance_criteria:
  - On every built page the footer's link row reads the six menu items in the menu's order, then About and Imprint (pending), in the page's language; each item is a link exactly when the menu's item is a link.
  - On every built page but Home, exactly one menu item, the page's section, carries aria-current="true", in the menu and in the drawer; Home marks none.
  - The marked item is ink and bold, with the 2px line in the menu; no other item changes look.
  - Apart from the footer row and the marking, every page shows the same text as main's build.

decisions_taken: >
  The plan, the readings and the acceptance criteria: approved in chat, 2026-10-09. Readings: the
  section rule holds on every page, an inert item (Teams, Players) marked the same way; Imprint
  keeps its "(pending)" label, the publication gate not lifted; no new strings.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - The Imprint label and page: the publication gate.
  - Links inside text, the team page's rows, Home's intros and the Rankings tab order: their own MRs.

done_when:
  - npm test, npm run build (audit-seo, check-built-pages), check_copy_gate.py, check_page_css.py and
    check_design_inventory.py pass.
  - The acceptance criteria are shown in .claude/task/acceptance_evidence.md from the built pages.

amendments:
  - The two pin tests added to scope_paths; their counts lowered to what this change leaves, 09_chrome.md's long sentences 9 to 8 and the code's history lines 751 to 749: approved in chat, 2026-10-09.
