# Acceptance evidence — product work is no longer blocked; say so in the handover

Branch `chore/handover-after-161`, from main `b29f2e0`.

criteria_demonstrated:

  - **The "BLOCKED ON THE CPO" line is gone**, verified by string search on the final file. It said
    *"one question, and until it is answered 463 team-seasons show no statistics. Do not start it."*
    A cold session would have stood still waiting for an answer that is not owed — the rule was
    settled on 2026-06-25 and `!161` states it in `docs/metric_layer.md`. The next action now reads
    as one line with no precondition, followed by *"Nothing is blocked on the CPO."*

  - **#110 is retyped, not deleted.** It is still a real defect — forfeits the provider labels `FT`
    blank 18 of 19 Süper Lig 2022 team-seasons — but it is a defect to fix, not a question to answer.
    ⚠ The entry now also carries the boundary that stops the next reader over-fixing it: of 9,515
    fixtures with no team statistics, **ZERO have statistics in the raw payload our models discard**
    (3,405 carry an empty array, 6,110 have no statistics section). The other 435 blanked
    team-seasons are correct output, and a blanket rule would silently convert genuine coverage gaps
    into complete-looking seasons.

  - **#111 is recorded** — no test compares a metric's value to the formula its own catalogue
    publishes, and no dbt unit tests exist. It did not exist when the handover was last written.

  - **A session touching metric behaviour is pointed at `docs/metric_layer.md` first**, with the rule
    stated in one sentence and the fact that it has been re-opened twice by builders who assumed the
    nulling was an oversight — which is why the pointer is in the next-action block rather than
    buried in reference material.

  - **Header facts re-derived**: `main b29f2e0` from `git log gitlab/main`, "no open MRs" from
    `glab mr list` after `!161` merged, range `!154`–`!161` from the merge commits.

  - **15,221 of 16,000 characters**, measured with Python `len()`. No trap dropped: the
    incremental-fact trap, the diff3 fourth marker, CP1252, the `--review-patch` redirect, the push
    guard on main and the column-0 parser all survive.

  - ⚠ **A duplication introduced by my own earlier edit was caught and removed.** The next action was
    stated twice — once as the new two-line summary and once as the old heading below it — leaving an
    orphaned sentence starting mid-clause. Found by reading the rendered section rather than the
    diff.

## What this does NOT do

- **It does not fix #110 or build #111.** Both are recorded as defects with their measurements.
- **It does not resolve the round cap**, which stays unsettled and unchanged.
- **It touches no code.** One tracked document plus the task artifacts.
