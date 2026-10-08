# Task contract — #145, the sentence generator, first used by the match page's head-to-head intro

objective: >
  The export fills a page's sentence from that page's served numbers and names, in EN, DE and FI,
  from templates in strings.ts, and writes nothing when an input is missing. Its first use is the
  match page's head-to-head intro: which of the approved wordings applies follows from the served
  split of the last meetings, and the fixture payload carries the intro per language.

refs: >
  #145 (one data-backed sentence per page: the generator in the export); #166 (match page, state 1):
  the head-to-head intro "generated in the export as #145 sets for sentences", eight wordings
  covering every split; render match-page_2026-10-07_75 and design-mocks/gen_match_page.py
  h2h_sentence. Part 1 of the page build in three MRs, and the order: approved in chat, 2026-10-08.

scope_paths:
  - scripts/export_site_data.py
  - tests/test_sentence.py
  - site_v2/src/i18n/strings.ts
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md

impact_map: >
  writers: scripts/export_site_data.py writes site_v2/src/data/fixtures/{fixture_id}.json; the only
    payload change is head_to_head.intro ({en, de, fi} or null). strings.ts gains eleven keys.
  downstream: the frontend reads head_to_head by named fields (HeadToHead.astro), so an added field
    renders nothing until the match page uses it. No dbt model, seed or BigQuery read changes; the
    generator reads strings.ts from disk. check_copy_gate.py and check-page-specs.mjs read strings.ts:
    the new keys must exist in all three locales, carry no em dash, and differ from EN.
  layer_rules: the consumption layer may not derive a number; the generator substitutes served values
    only and picks the wording from the served split, as #145 places it in the export.
  deploy_order: the nightly export writes the field after merge; nothing reads it until the page MR.
  blast_radius: fixture payloads gain one field; no page output changes.

acceptance_criteria:
  - For every split of 1 to 5 meetings (55 splits), the export writes an intro in EN, DE and FI with every placeholder filled, shown by the test output.
  - A head-to-head row with a missing count or a missing team name gets no intro, shown by the test output.
  - Run over the 628 committed fixture payloads, every one with a head-to-head row gets an intro in all three languages, and one example per language is quoted.
  - The built site is byte-identical before and after the change, shown by diff -rq of two builds.

decisions_taken: >
  The generator follows #145's How: sentence(key, lang, values) in the export, templates as strings.ts
  keys, None on a missing value. The head-to-head wordings are render 75's h2h_sentence; their DE and
  FI text and the acceptance criteria: approved in chat, 2026-10-08. Choosing the wording from the
  served split is the generator's job where #145 places it; no number is derived, every number shown is
  a served count, and a missing team name gives no intro. "No meetings on record" is the
  page's empty state and ships with the page MR.

  THRESHOLD DECLARATIONS: NEW MECHANISM: the sentence generator, specified by #145. RECURRING COST:
  none (no BigQuery read).

decisions_reserved:
  - Every other page's sentence: #145, at each page's review.
  - The match page's rendering of the intro: the page MR.

done_when:
  - pytest tests/ passes; check_copy_gate.py passes; npm test passes.
  - The acceptance criteria are shown in .claude/task/acceptance_evidence.md.
