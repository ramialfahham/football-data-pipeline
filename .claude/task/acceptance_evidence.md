# Acceptance evidence — navigation rules, and Next matches applying them

Everything below is read from the BUILT output (`site_v2/dist/`) or from the committed files, never
from source intent. The build is green: `audit-seo: 166 built page(s) checked. OK.`

criteria_demonstrated:

  - **The navigation rule is in `docs/site_architecture.md`, names all three families and the four
    content-link shapes, and says it is provisional in the CPO's own words.** The section is
    `### Navigation — what is clickable, and where it goes`, under §3 beside the URL scheme. It
    opens with his words: *"the rules might be subject to change. We have not built every page yet,
    so actually we don't know yet."* It carries a table of the three families (chrome / content
    links / controls) and a second table of the four shapes (row / heading / chip / prose), each
    with its destination and its at-rest affordance.
  - **The row half is stated explicitly.** Verbatim: *"every content link points at the one entity
    it names, and a row names its subject. Nothing inside a row is separately clickable."* Applied
    examples follow for match, Top players, Top teams, standings and squad rows.
  - **The competition heading is a real link in all three locales, read from `dist/`.**
    `grep -o '<a class="cnm" href="[^"]*"' dist/en/index.html` returns
    `/en/coppa-italia/`, `/en/dfb-pokal/`, `/en/saudi-pro-league/` — three of three groups. Same in
    `de` and `fi`. The accessible text is carried: the rendered DOM gives
    `[{href:"/en/dfb-pokal/", text:"DFB-Pokal"}, …]`.
  - **The chevron is present AT REST, not on hover.** In the emitted markup, `class="chev"` appears
    3 times in `dist/en/index.html`, once per heading — i.e. it is in the HTML, not applied by a
    `:hover` rule. Measured on the rendered page:
    `{display:"block", visibility:"visible", opacity:"1", w:15, h:15, visibleAtRest:true}`, and the
    svg carries `aria-hidden="true"` so it is decoration, not a second label.
    ⚠ Measured rather than reasoned about, because the whole point of the rule is that an
    affordance which exists only on hover does not exist on a phone.
  - **A match row is still a single link with nothing clickable inside it.** Over
    `dist/en/index.html`: 4 `.fxrow` anchors found, and **0** of them contain a nested `<a`.
  - **Every competition URL the home page links to is emitted.** `audit-seo.mjs` check 8 fails the
    build on any internal href resolving to no emitted page; the audit passes over 166 pages, with
    the page-count driver reporting `/[lang]/[competition] -> 144`.
  - **The route is driven by the MART payload, not a literal list.** The page imports
    `../../../data/competition_index.json` (from `mart_competition_index`), and
    `grep -nE '"(BL1|PL|SA|BSA|DFBP|bundesliga|dfb-pokal|premier-league)"'` over the page source
    returns nothing. The spec's `page_count_driver` is the formula
    `count(competition_index.json .competitions) x count(locales)`, not a constant.
  - **The three locales' competition pages emit non-identical titles.** For `dfb-pokal`:
    `de` → `DFB-Pokal: Überblick` · `en` → `DFB-Pokal: Overview` · `fi` → `DFB-Pokal: yleiskatsaus`.
    The audit's cross-locale uniqueness check (the one written for the live defect where all three
    shipped byte-identical) passes.
  - **`STUB_PAGES` lists the competition page and still blocks go-live.**
    `export const STUB_PAGES = ["[lang]/[competition]/index.astro"];` and `audit-seo.mjs:505-506`
    raises *"INDEXABLE is true while STUB_PAGES is non-empty … a stub is a thin page"*. So shipping
    this scaffold TIGHTENS the go-live gate rather than loosening it.

## The audit defect this branch exposed, and the guard added for it

`audit-seo.mjs` matched a page to its spec with `specs.find((s) => s.match.test(p))` — the FIRST
match, in `walkJson` directory order. `specRouteRegex` compiles every `[param]` to `[^/]+`, so
`[lang]/[competition]/index.astro` matches `/en/competitions/` as readily as `/en/bundesliga/`, and
the competitions INDEX was judged against the competition HUB's spec: three violations, one per
locale, on a page that was correct.

Fixed with a specificity rule — most literal segments wins — extracted into an exported
`specForPath()` so the tie-break is testable rather than buried in `main()`.

⚠ **Mutation-tested, because the first two tests I wrote would NOT have caught a regression.** They
asserted `routeSpecificity()` and the regex collision directly, both of which stay true whether the
selection uses `find` or the tie-break. Reverting `specForPath` to `specs.find(...)`:

```
✖ specForPath: the literal route wins the collision, in EITHER array order
ℹ pass 78   ℹ fail 1
```

Exactly one test red, and it is the one that asserts BOTH array orders — which is what makes `find`
impossible to satisfy, since it can only ever be right for one of them. Restored: `79 pass, 0 fail`.

## Round-1 review findings, and what they changed

- **`bi-analyst-reviewer` FAIL** — `rendered_page_evidence.md` documented a different branch, and
  the 375px check this contract's `done_when` requires had never been run. Running it found a real
  defect: the heading link measured **100x21** at mobile width, under the 24x24 minimum target size
  and a third the height of the 81px row beside it. Fixed (33px hit area, text unchanged) and the
  artifact rewritten for this branch. Full measurements in `rendered_page_evidence.md`.
- **`platform-reviewer` FAIL** — the tie branch of `specForPath` was untested (mutating `>` to `>=`
  turned zero tests red) and the code silently resolved an equal-specificity overlap by walk order,
  which its own comment called a bug not to paper over. A gate wired into `astro build` must fail
  CLOSED. `specTie()` now reports the overlap as a build issue; its test uses the reviewer's own
  counterexample and goes red when the guard is neutered.
- **`scope-auditor` FAIL** — `decisions_taken` cited CPO chat quotes with no `escalations.log`
  entry behind them. The rulings were real; the record was missing. Written to the log, and the
  contract now cites the log rather than restating the quotes. **PASSed round 2.**

## Round-2 finding — the guard I added was itself under-tested

**`platform-reviewer` FAIL, and a sharper finding than its first.** My round-1 fix added `specTie`,
and my test for it did not pin `Math.max`: mutating it to `Math.min` survived all 81 tests. The
reason is exact — every fixture I wrote had at most ONE spec per specificity level, and with one
spec per level `max` and `min` both end up with a single winner, so `winners.length > 1` is false
either way and the mutant is indistinguishable.

It named the shape that separates them: **three** matching specs at specificities `[2, 2, 1]`.

```
Math.max -> top = 2, winners = the two specificity-2 specs -> TIE reported   (correct)
Math.min -> top = 1, winners = the one specificity-1 spec  -> []             (silently resolved)
```

That is the round-1 defect surviving inside the round-1 fix, one collision-member out of view. Test
added with a `[2, 2, 1]` fixture; the mutation now turns exactly that test red (`pass 80, fail 1`)
and restoring gives `pass 81, fail 0`.

⚠ **The lesson is mine, not the reviewer's to keep repeating:** I mutation-tested the fix and
declared it guarded, but only against the mutation I had thought of. A fixture that cannot
distinguish two implementations does not test the thing it appears to test.

## Round-3 finding — the focus ring, and a second overclaim in the write-up

**`bi-analyst-reviewer` FAIL, twice over, and both were right.**

**(a) A real defect.** The focus ring is drawn from the border-box the tap-target fix moved, and I
had verified rest state and tap size but never focus. Measured: the ring's bottom sat at **168.2**
against the group divider at **165.8** — crossing the line — with 16px unused above. Fixed by
biasing the padding upward (`padding-block: 9px 3px`), same 33px target. Re-measured on all three
groups: clears by 0.7px below, 13px above, no collision either side. Detail in
`rendered_page_evidence.md`.

**(b) An overclaim in the fix's own evidence.** I then wrote the post-fix numbers under a "Measured
with REAL keyboard focus" header when they were computed from a static box plus assumed outline
constants, disclosing it only in a footnote. Round 3 caught that — the same overclaim, committed
while certifying the fix for an overclaim, in the artifact meant to prove it had stopped. Redone
under a confirmed `:focus-visible` on every group, with the outline constants read from
`getComputedStyle`.

⭐ **One of its hypotheses was disproved BY the measurement, and that is worth keeping.** It derived
~1px of clearance above the first group from margin collapse. Measured: 13px, the same as the
others, because the ring's reach starts at the padded border-box rather than the text. A reasonable
derivation, still wrong — which is the entire argument for measuring rather than reasoning about
single-digit pixels.

## Gates

```
npm test (site_v2)                     79 pass, 0 fail
npm run build + audit-seo.mjs          166 built page(s) checked. OK.
check-page-specs.mjs                   5 page(s) validated against their specs. OK.
check_copy_gate.py                     ok, 3 locales
```

## What this does NOT do

- **No competition page has content.** It is a scaffold: URL, canonical, hreflang, title, breadcrumb
  and an `<h1>`. #47 owns the real page.
- **The competitions index page's 48 rows are still inert.** They are now unblocked — the hub they
  would link to exists — but wiring them is a second surface and was kept out of scope.
- **No player route exists**, so Top players (#40) still has no destination. That block is not in
  this branch.
