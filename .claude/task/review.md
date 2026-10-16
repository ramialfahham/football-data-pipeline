# Review — fix/175-played-match-title-year — 2026-10-17

diff_sha256: a5a106ae46174c5049b9e5d513c08409b159f8cc21d5af940b232e91583d5ab9

rounds: 2

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Binding rule: the only new value is the served kick-off through the existing formatDayYear, a field the page already reads; no new field, no sample key, no export change.
- Read the built dist heads of Hoffenheim–Dortmund in EN, DE and FI: title, h1 and description carry the year as criteria 1 and 2 state; other played pages show the date after the round.
- The h1 is visually hidden, so the longer text changes no layout and draws no second visible date.
- The next match branch keeps formatShortDate and aboutNoH2h; criterion 3 holds from the code.
- The wireframe sentence matches criterion 7; the "inside the 600px budget" line stays true for upcoming matches.
- A played page with an empty round would render "· ·"; no such page exists in the full-scale build (0 of the EN pages).

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 failed the width test for measuring one German date in all three templates; round 2 measures each template with its own locale's widest real date over twelve months, with format.ts's Intl options, and the finding is resolved.
- The played assertion holds the year form under the 660px cap and the next match assertion holds the short form under the 600px budget, each with its locale's real date.
- One title constant feeds the head, h1, og and JSON-LD; played is defined before it; the next match branch is unchanged.
- No hook, workflow, CI, package or hosting file changes; the 660px cap in audit-seo.mjs still fails closed.
- One cached formatter call per played page and no change in page count; consistent with the full-scale build's 204,498 pages in 724s at 8 GiB.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope_paths; format.ts, strings.ts, the export and dbt are untouched; the next match page is untouched.
- The year, the wireframe sentence and the seven criteria are approved in chat (2026-10-16); the hard-cap amendment (2026-10-16) and the "Sept" amendment (2026-10-17) are named and dated.
- The reserved decisions (the two Nyasa Big Bullets team ids, the deploy export's entity list) are not touched.
- No new mechanism, no recurring cost, no decision history in code or docs, no unapproved wording.

## escalations
(none)
