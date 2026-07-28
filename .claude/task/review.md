# Review — feat/844-seo-build-gate — 2026-07-28

> Machine-checked review artifact (governance G3). **Three rounds.** Round 1 was 1 PASS and 2 FAILs,
> round 2 was 2 PASS and 1 FAIL, round 3 PASS. Every FAIL was correct and every one of them found a
> defect in something I had already declared finished.
>
> **Round 1 — cto-reviewer FAIL: the gate's own declare-verify loop was not closed.** The schema
> promised "the audit parses the emitted @graph and fails if the type is absent", but `audit-seo.mjs`
> built its expected-`@type` map from a HARDCODED path table and never read a spec. The two agreed
> only by coincidence of consistent authorship; the next entity spec would have drifted silently.
> That is the exact defect class this whole PR exists to eliminate, sitting inside the mechanism.
> It also found `requireConfig()` regex-scraping `indexability.mjs` instead of importing it — so the
> audit could disagree with the two consumers that do import it — and that my `MIN_EXPECTED_PAGES`
> self-check covered only `<title>` while claiming file-wide coverage. The dead-link and OG checks
> are written `if (value) {…}`, so a broken regex there would have made them find nothing and the
> gate would have **failed open**.
>
> **Round 1 — bi-analyst-reviewer FAIL on §10, and it was the most consequential finding of the
> PR.** I shipped nine user-visible strings on a CPO ruling that covered only whether to keep the
> brand suffix. §10 makes copy a CPO decision *every time*. What followed proved the rule: four of
> my strings were wrong. The German dropped an article German grammar requires. The Finnish used
> `sarjassa` with an uninflected borrowed noun. Both used `muoto` (shape) where the football sense of
> form is `kunto` — the retired MVP's own corpus says `kuntojakso`, and the CPO's source agreed. And
> I had changed the Finnish fixture separator to an en dash on an unverified claim that bi-analyst
> itself had agreed with. It also caught my rendered-evidence document contradicting itself: §1 said
> the locale landing gained header and footer, §6 said nothing changes a pixel.
>
> **Round 2 — bi-analyst FAIL again, and this one stings.** The ENGLISH description carried the
> identical defect I had just fixed in German: `{team} in {competition}` assumes an article the
> template cannot know ("in **the** Premier League", "in Serie A"). I fixed German for exactly that
> reason **in the same PR** and left English alone, because I was still treating it as the trusted
> baseline — which is precisely what the contract amendment I wrote *in this same session* says I
> must stop doing. Writing the lesson down and then not applying it is worse than never noticing.
>
> **Round 3 — PASS.** bi-analyst swept every interpolation site in all three locales for the general
> class (a template assuming a grammatical property of an interpolated value it cannot know) and
> confirmed no other instance exists.
>
> ## What the CPO decided, and what he reversed
>
> He wrote the Finnish himself, then ruled three more times: em dashes "look terribly like AI
> generated" (titles took a colon), the shortened titles were "too short" once the brand freed the
> budget, and — after `seo-expert-reviewer` was told explicitly not to soften its answer because he
> had already ruled — **he reversed his own brand-suffix ruling**. The fact that moved him is that
> `Layout.astro` emits `og:site_name` unconditionally, so the brand leaves the indexed title without
> leaving the site.
>
> ## Hash note, stated rather than glossed
>
> The verdicts below were formed at `c2da69e1…` (scope-auditor, cto) and `d4af3213…` (bi-analyst
> round 3). The final hash differs because I then applied **bi-analyst's own non-blocking finding**:
> three comment blocks still described a "dash" mechanism no current string uses. **Comment text
> only — no string value, no code path, no test changed.** Burning a fourth round on comment prose,
> past the cap, to re-approve a reviewer's own recommendation would be ceremony.

diff_sha256: c304ed5fafb946d0c8c460dedd8578eb359a9d8fb1fa6faf2b7fd0e64caa6079

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- **Seven amendments ruled DISCOVERED SCOPE, not creep.** I put the question to it in those terms
  and flagged my own conflict of interest. It verified each amendment names CPO or reviewer
  AUTHORITY rather than my convenience, and that the code changes behind them are real and
  non-trivial: the brand suffix removed from nine templates, the width check, the competition
  lookup. Its summary of the distinction: the objective held while review and the CPO discovered the
  work's true extent.
- **The fixture competition lookup is SELECTION, not derivation.** It traced
  `competitions[fixture.league_code]?.name ?? fixture.league_name ?? fixture.league_code` and
  confirmed it picks between pre-existing fields with no computation. Preferring the registry over
  the provider is a consumed-data choice; the consumption-layer contract holds.
- **All eight `decisions_reserved` items verified untouched** — LinksFooter's conditional-link rule,
  the redirect/alias mechanism, the 404 strategy, structured-data completeness, the rich/thin tier
  split, OG-image fitness, localised competition names, SectionHead. It noted the copy iterations
  touched many strings, which is exactly when a reserved item slips, and confirmed none did.

## cto-reviewer
VERDICT: PASS
risks_checked:
- **The declare-verify loop is genuinely closed**, traced by hand rather than accepted: it converted
  all three committed specs through `specRouteRegex()` and confirmed the regexes match the real
  emitted URL shapes and reject wrong-depth siblings, then traced a hypothetical `schema_org` edit
  through `main()` into the `@type` check. The `specs.length === 0` guard stops a broken walk
  passing vacuously.
- **`Layout.astro`, `robots.txt.ts` and the audit can no longer disagree** — it compared the three
  import specifiers directly and confirmed Node's module cache guarantees one evaluation per
  resolved path.
- **The self-check widening covers the right set**, not just a relabel: the checks written
  `if (!value) complain` already fail loud, so flooring `<title>`, `<a href>` and `og:title` covers
  exactly the three written `if (value) compare` — the fail-open shape.
- **It separated two arguments I had bundled into one threshold, and it is right.** The 660px gate
  mixes legitimate calibration (my estimator buckets characters, so ±30-50px error is plausible and
  failing at exactly 600 would fire on noise) with a **product decision wearing an engineering
  constant's clothes**: accepting that some real fixture titles will be permanently truncated. It
  noted the sharpness given this PR's own history of copy decisions turning out to be CPO-class.
  Disclosed, tested and bounded, so not blocking — surfaced to the CPO rather than left in a comment.
- **Two concrete gaps, both fixed after its review**: the width table's uppercase test was ASCII-only,
  so `Ö`/`Ä`/`Ü` fell into the narrow generic bucket in a site whose live locales are German and
  Finnish (now `\p{Lu}`; verified `Ö` and `O` now weigh the same); and `TITLE_PX_BUDGET` was
  documented as "used for reporting" with **zero runtime effect**, so nobody would learn how many
  pages sit in the accepted 600-660 zone. The audit now counts and prints it. Today: zero.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- **The English fix verified in the BUILT output**, and judged against real convention rather than
  assumed: `Manchester United (Premier League): …`. It ruled the parenthetical **idiomatic** in
  English — the standard entity-then-context form used by squad databases and transfer listings —
  so consistency did not cost English its naturalness.
- **A full-file sweep for the defect class, not a sample.** It categorised every `{team}`,
  `{competition}`, `{home}`, `{away}` and `{brand}` interpolation across all three locales by
  grammatical position and confirmed no other instance sits after a case-governing preposition. The
  one remaining `{competition}` use (`heroCaption`) is attributive in all three languages, which is
  safe by construction.
- **The German and Finnish fixes verified in `dist/`**, not from my description: parentheses render
  correctly, `sarjassa` is gone, `kunto` replaces `muoto`.
- **The rendered-evidence gap it opened in round 1 is closed** — §6 now carries an accessibility-tree
  read and 320x720 geometry for the locale landing's new chrome composition, measured against the
  live dev server rather than derived from source.
- **The metric display contract is untouched** — no metric-rendering component appears anywhere in
  the diff across all three rounds.
- Its one non-blocking finding (three comment blocks naming a "dash" mechanism no string uses) is
  fixed; see the hash note above. Its suggestion of a stronger-than-byte-identical uniqueness check
  (edit distance) is recorded as a follow-up rather than added at round 3.

## escalations
(none blocking — two CPO decisions were taken inline during review and are recorded in
`contract.md` amendments: the brand-suffix reversal, and the nine SEO strings, which he wrote.)
