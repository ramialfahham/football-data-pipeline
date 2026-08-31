# Rendered page evidence — STEP 5, the English label "on target" → "on goal"

Branch `refactor/metric-label-on-goal`, base main `649b11c`.

Read from `site_v2/dist/` after `npm run build` (66 pages, `audit-seo: 67 built page(s) checked.
OK.`) — never from source, never from `outerHTML`. HTML comments stripped and whitespace collapsed
before any comparison, because Astro splits interpolated text with `<!-- -->` and a line-based grep
misses a phrase straddling a break.

⭐ **THIS IS THE CRITERION THAT PROVES THE NEW RULING, and it is the only one that can.** The CPO
extended RULING 2 from "in the catalogue" to catalogue + website precisely so the change is visible.
A seed-only change would leave this table unmoved.

| | base (`649b11c`) | after |
|---|---|---|
| EN pages containing **"on target"** | 38 | **0** |
| EN pages containing **"on goal"** | 0 | **38** |
| DE / FI containing either | 0 / 0 | **0 / 0** |
| comparison rows per window — EN / DE / FI | 12 / 12 / 12 | **12 / 12 / 12** |
| group headings per window | 7 / 7 / 7 | **7 / 7 / 7** |
| distinct rendered labels per locale | 12 | **12** |

Across all **19** fixture pages in each locale, both windows. **Exactly one label string moved and
the structure did not**: the EN set now reads `Ø Shots on goal` where it read `Ø Shots on target`,
and the other eleven are byte-identical.

    EN   % Duels won · % Save percentage · Clean sheets · Ø Corners · Ø Corners against ·
         Ø Defensive actions · Ø Duels · Ø Goals · Ø Goals against · Ø Passes · Ø Shots ·
         Ø Shots on goal          <- the only change
    DE   Ø Torschüsse             <- unchanged, already "goal shots"
    FI   Ø Maalilaukaukset        <- unchanged, already "goal shots"

## ⛔ WHAT THIS BUILD CANNOT PROVE, stated before it is asked

**All 38 EN occurrences are the SAME label**, `Ø Shots on goal` — two per fixture page across 19
pages. The other three labels this MR changes render on **zero** built pages:

    Ø Shots on goal against        team Performance surface — not built
    Ø Shots on goal difference     team Performance surface + hero — not built
    % Goals per shot on goal       team Performance surface — not built

The one EN team page in the sample (`teams/manchester-united-fc`) carries none of them; its
Performance tab still renders "coming soon". **So the dist read proves one of the four rendered
labels and cannot see the other three.** They were verified by reading `strings.ts` directly, and
`acceptance_evidence.md` §(c) records that no test pins their wording either — a mutation putting
`"Ø Bananas per fortnight"` in one of them leaves `npm test` **green**.

## The chrome strings that did NOT move, and what a reader will see

⛔ `strings.ts`'s `Dict` holds four strings that name this same metric in rendered English and are
**deliberately out of scope** (copy is §10; the approved scope named the four `METRIC_LABELS` values):

    axPlay          "Shots on target difference / match"        the hero chart's x-axis
    heroVerdictUnder / heroVerdictOver / heroCaption            "a shots-on-target difference of …"

None renders in this sample either, for the same reason — the hero is on the unbuilt Performance
surface. ⚠ **But when that surface ships, the axis will read "Shots on target difference / match"
beside a metric row reading "Ø Shots on goal difference".** Flagged for the CPO rather than folded
in, and recorded here so the build that first renders the hero does not ship the mismatch unnoticed.

## Step 5 is confirmed as still-pending by its own predecessor

`!132`'s rendered evidence recorded, as a passing observation, that the EN comparison block still
read **"Ø Shots on target"** — which was the standing proof that step 5 had not run. That line now
reads **"Ø Shots on goal"**, and the same measurement re-run on this branch is what closes it.

## Row count in context

12 is where `!123` left it — 16 catalogue rows minus the four the committed sample cannot feed. The
sample roll-forward is what restores them, it is owed and unscheduled, and **nothing in this MR
moves that number**: a label change cannot add or drop a row.
