# Acceptance evidence — reasoning lives in git, not in code comments

criteria_demonstrated:
  - §1.2 SAYS IT, FOR EVERY LANGUAGE, WITH THE RECIPE. `dbt_project/docs/engineering_standards.md`
    §1.2's heading now reads "every language in the repo — Python, SQL, Astro, TypeScript, YAML";
    the new subsection "Reasoning lives in git, not in the comment" states: a comment says why, in
    one line; who decided, when, which reviewer, which round, which MR or issue — never in code;
    the commit message, the MR and the issue are the home; three commands reach them from any
    line. THE RECIPE WAS RUN, not copied: `git blame -L 36,36 --porcelain CLAUDE.md` → commit
    `82ddb9c5`; `git log -1 --format=%B` → "Closes #117"; `git log --merges --ancestry-path
    --first-parent --reverse … | grep -m1 "See merge request"` → "…football-data-pipeline!175".
    The first draft's third command found the LATEST merge, not the commit's; caught by running
    it, replaced by the ancestry-path form, output recorded in the section.
  - `CLAUDE.md` SAYS IT IN ONE SENTENCE-BULLET, under "Operational notes": "Reasoning lives in
    git, not in code comments … `git blame` reaches all three from any line", pointing at §1.2 for
    the recipe and naming the 429 and step 8.
  - THE TWO TEMPLATE FOLDS SAY THEY ARE THE PLACE. `.gitlab/issue_templates/Task.md` fold comment:
    "THIS IS WHERE REASONING LIVES — not in a code comment. A future reader reaches it from any
    line: git blame → commit → Closes #N." `.gitlab/merge_request_templates/Default.md` fold
    comment: "THIS IS WHERE THE REVIEW RECORD LIVES … not in a code comment next to the line. The
    merge commit points here."
  - THE CONTRACT TEMPLATE SAYS WHERE TO ARGUE. `.claude/task/TEMPLATE.md` under `decisions_taken:`:
    "THIS AND `amendments:` ARE WHAT THE REVIEWERS READ. Argue with a reviewer here — never in a
    code comment next to the line."
  - THE COUNT IS RECORDED. §1.2 states 429 with the per-tree split and the exact grep; `CLAUDE.md`
    names the same 429. Re-run on this branch after the edits: 429 — unchanged, as it must be,
    since no code is touched. `pytest tests/test_governance_doc_parity.py
    tests/test_no_dead_issue_refs.py`: 45 passed, 1 skipped.

## What is NOT demonstrated

- That the rule holds. It did not hold before, on its own; that is why step 8 is a hook. This
  branch gives the hook its number and the rule its place.
- That the grep is exact. It is a starting number for a ratchet, stated as such in the contract and
  in §1.2; step 8 decides the pattern.
