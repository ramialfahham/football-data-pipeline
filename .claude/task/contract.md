# Task contract — the non-core files no longer quote the CPO

objective: >
  Remove the CPO's chat words from the non-core files that still carry them, keeping each rule
  in plain words. The core documents follow in their own strip MRs; the protected reviewer briefs
  belong to the protected-files cleanup.

refs: >
  The cleanup of quoted chat words, approved in chat, 2026-10-06.

acceptance_criteria:
  - No non-core, non-protected tracked file quotes the CPO's chat words

scope_paths:
  - docs/wireframes/10_home.md
  - docs/wireframes/99_gaps_register.md
  - docs/wireframes/09_chrome.md
  - dbt_project/docs/layering.md
  - docs/roles/cto.md
  - design-mocks/gen_competitions.py
  - design-mocks/rows.py
  - design-mocks/check_row_consistency.py
  - design-mocks/gen_matches.py
  - design-mocks/interaction.py
  - design-mocks/renders/competition-hub-groups_2026-09-17_01.html
  - design-mocks/renders/competition-hub-groups_2026-09-17_02.html
  - design-mocks/renders/competition-matchdays_2026-09-16_01.html
  - design-mocks/renders/competition-overview_2026-09-16_01.html
  - design-mocks/renders/competition-overview_2026-09-17_02.html
  - design-mocks/renders/competition-rankings_2026-09-16_01.html
  - design-mocks/renders/competition-rankings_2026-09-17_02.html
  - design-mocks/renders/home_2026-09-16_01.html
  - design-mocks/renders/home_2026-09-17_02.html
  - scripts/export_site_data.py
  - site_v2/src/i18n/strings.ts
  - tests/test_no_decision_history_in_code.py
  - tests/test_no_decision_history_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

impact_map: >
  Short form: comment, docstring and prose lines only. In scripts/export_site_data.py and
  site_v2/src/i18n/strings.ts every changed line is a comment or a docstring line; no executable
  line, string value, model, mart or export payload changes, so no number on any page moves. In
  the nine renders only a CSS comment changes, so each page renders as reviewed.

decisions_taken: >
  Readings, under the delegation of 2026-10-02:
  - A quote is the CPO's chat words. Quotes of a document's own earlier text, of a file header,
    of supplied copy or of an option's name are not his chat words and stay.
  - Each quote is replaced by the rule it carried, in plain words; where the sentence already
    states the rule, the quote is only removed.
  - The words that replace a quote carry no date, issue or MR number or review story; where a
    whole line is rewritten, the line drops the ones it carried. Other history in these files is
    left for their own cleanup. The history-line pins move down by what the rewrites removed.
  - A render of record is not overwritten by a CSS-comment change: the page renders as reviewed.

  Threshold declarations. NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - None.

done_when:
  - A sweep of the tree finds no quote of the CPO's chat words outside the core documents and the
    protected reviewer briefs.
  - pytest (whole suite) and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
