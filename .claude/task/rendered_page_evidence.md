# Rendered page evidence — the sample roll-forward

Branch `chore/roll-forward-sample`, base main `7caaf21`.

Read from `site_v2/dist/` after `npm run build`, comments stripped and whitespace collapsed before
any comparison — never from source, never from `outerHTML`.

⭐ **This MR's whole purpose is a rendered-page outcome**, so unlike the recent naming MRs the dist
read is not a confirmation that nothing moved; it is the deliverable.

| | before (main `7caaf21`) | after |
|---|---|---|
| distinct comparison labels, EN | 12 | **16** |
| `% Shots from box` | absent | **renders** |
| `% Goals per shot on goal` | absent | **renders** |
| `% Pass accuracy` | absent | **renders** |
| `Ø Key passes` | absent | **renders** |
| fixture pages per locale | 19 | 4 |
| build | 66 pages, `audit-seo … OK.` | **21 pages, `audit-seo: 22 built page(s) checked. OK.`** |

The sixteen EN labels now rendered:

    Ø Goals · Ø Goals against · Clean sheets · Ø Shots · % Shots from box · Ø Shots on goal ·
    % Goals per shot on goal · Ø Duels · % Duels won · Ø Defensive actions · Ø Passes ·
    % Pass accuracy · Ø Key passes · Ø Corners · Ø Corners against · % Save percentage

⭐ Note `Ø Shots on goal` and `% Goals per shot on goal` — step 5's wording, now rendering on a
sample that postdates it. `!134` could only prove one of its four changed labels from the build
because three rendered nowhere; **this roll-forward renders a second of them**
(`% Goals per shot on goal`), narrowing that disclosed gap without being asked to.

## Per WINDOW, because per page still averages two different numbers

⚠ **Corrected after round 1.** I first reported this per page — 16 on three, 15 on one — by dividing
each page's labels by its two windows. `bi-analyst` read the built HTML and found the two windows
differ, so the division averaged them. Re-measured by splitting at the `win win-w2` marker:

    fixture                                       w1 (Last 5)          w2 (This season)
    2026-09-01-parma-vs-us-cremonese              16 rows / 7 groups   16 rows / 7 groups
    2026-09-01-torino-fc-vs-monza                 16 rows / 7 groups   16 rows / 7 groups
    2026-09-01-al-hilal-saudi-fc-vs-al-ahli-...   16 rows / 7 groups   16 rows / 7 groups
    2026-09-01-hebc-vs-borussia-dortmund          15 rows / 6 groups   16 rows / 7 groups

**Seven of eight windows render the full 16/7.** The exception is `1550704`'s **w1 only**: HEBC has
no Last-5 window at all and Dortmund's `w1.defensive_actions_per_match` is null, so the Defending row
has data on neither side and is omitted with its single-row heading. In **w2** Dortmund's figure is
24.33, so the same row renders with an em-dash on the HEBC side.

⭐ **That one fixture therefore exercises BOTH null-display paths on the same page** — row omitted
entirely (w1) and one-side-null shows "–" (w2). ⚠ Those are **two different rules** and an earlier
draft cited only one: `01_fixture_page.md:235` governs the one-side-null "–"; the both-null omission
is `00_overview.md:37-39` ("omitted entirely where absence is by design") and
`MetricComparison.astro`'s header — *"A row whose value is missing on BOTH sides is hidden (avoid a
wall of dashes)"*. Corrected after `bi-analyst` flagged the citation.
**DE and FI match EN page for page**, 4 fixture pages each.

## What the smaller page count does and does not mean

21 built pages against 66 before, because the set is 4 fixtures rather than 19. That is the direct
consequence of the matchday, not a regression: `audit-seo` checks every built page and every internal
link, and passes. ⚠ It does mean **CI now exercises fewer pages**, which is the cost the CPO accepted
when he ruled the sample is infrastructure rather than a display. The component coverage that
matters was measured instead of assumed — three form paths plus the row-omission path, and both
competition shapes — and is set out in `acceptance_evidence.md`.

## The check a local build cannot make

`audit-seo.mjs` fails on an internal link resolving to no emitted page, and that is the only guard on
landing↔fixtures consistency. It cannot be reproduced locally: a full export leaves thousands of
untracked payloads on disk, so every link resolves while CI sees only the tracked set. Two things
close that here — `git clean -fX site_v2/src/data` before building, so the local build is honest, and
the four-list assertion in `acceptance_evidence.md`, which is a check rather than a guard.
