# Rendered page evidence — #90

Read from **`site_v2/dist/`** after `npm run build` (60 pages, `audit-seo: 61 built page(s)
checked. OK.`), not from source and not from `outerHTML`. HTML comments are stripped before the
text is collapsed, because Astro splits interpolated text with `<!-- -->` and a raw grep misses a
label that straddles one.

## Team page — Performance tab, all three locales

`dist/{lang}/teams/manchester-united/index.html`

| | EN | DE | FI |
|---|---|---|---|
| season-panel rows | 16 | 16 | 16 |
| league-panel rows | **15** | **15** | **15** |
| season row 3 | `% Clean sheets – –` | `% Zu-Null-Spiele – –` | `% Nollapelit – –` |
| league-panel clean-sheet row | omitted | omitted | omitted |

**The 15-vs-16 gap is the point, and it is expected.** The committed export still keys the
benchmark `clean_sheets`; the page now looks up `clean_sheets_share`. `TeamPerformance.astro`'s
`benchByKey.has(keyOf(r))` filter therefore drops the row from "vs the league" — the honest-absent
path the tab already implements (14_team_stats.md §6: a metric with no benchmark is OMITTED, never
a zero bar). The season panel keeps its 16 rows and dashes the value and delta. It resolves itself
the first time the export is rerun after `data:build:main`.

## The full season panel, EN, in locked block order

```
 1. Ø Goals                       1.8   +0.7
 2. Ø Goals against               1.3   -0.1
 3. % Clean sheets                  –      –     <-- the only row this task changes
 4. Ø Shots                      15.7   +1.8
 5. % Shots from box               66%   +3 pp
 6. Ø Shots on target             5.7   +1.1
 7. % Goals per shot on target     29%   +7 pp
 8. Ø Duels                         99      0
 9. % Duels won                    51%   +1 pp
10. Ø Defensive actions           30.3   -3.4
11. Ø Passes                       466     -32
12. % Pass accuracy                83%   -2 pp
13. Ø Key passes                  12.0   +1.3
14. Ø Corners                      4.8   -0.4
15. Ø Corners against              4.9   +0.1
16. % Save percentage              65%      –
```

DE and FI render the same sixteen in the same order with their own labels; row 3 is
`% Zu-Null-Spiele` and `% Nollapelit`. Both were checked against the same built files, and both
sit beside sibling percent labels that already carry the `% ` prefix (`% Trefferquote`,
`% Torjuntaosuus`), which is the convention that decided the wording.

## Fixture page — the count surface, unchanged

`dist/en/champions-league/matches/2026-08-18-dinamo-zagreb-vs-viking/index.html`

```
… 1/4 Clean sheets …      (twice — one per window)
```

The count over its denominator, label untouched. This is what proves the rename did not leak into
the surface it was never about.

## Console

The dev server render of the same three pages produced two console errors, both
`Failed to load resource: 404` for remote crest images in the committed sample. Pre-existing, not
from this change, and absent from the built output check.
