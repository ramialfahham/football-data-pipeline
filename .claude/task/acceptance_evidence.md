# Acceptance evidence — #190 How step 2, the football reviewer and the plain-language line

Read from the files on disk, `git diff main`, and exit codes read bare.

criteria_demonstrated:
  - THE PLAIN-LANGUAGE LINE. `git diff main -- docs/working_agreement.md` adds one line to section 9,
    "Explanations, issues and MR heads follow ISO 24495-1 (plain language): the reader finds,
    understands and can use what they need.", the issue's text word for word; the same line is
    added to the Cursor mirror, `.cursor/rules/agent-behavior.mdc`, "Communication style".
  - THE FOOTBALL REVIEWER. A script compares the brief's intro, inputs and hunt, and the whole role
    doc, with the texts shown to the CPO for his yes: "identical" for both. From "## Verdict
    rules" to the end the brief is byte for byte main's; its frontmatter keeps name
    `football-analytics-expert-reviewer`, tools, model and effort. The routing pin in
    tests/test_governance_hooks.py and the history pin of 2 dated lines in
    tests/test_no_decision_history_in_docs.py pass; pytest "1352 passed, 2 skipped"; the
    governance gates exit 0.
