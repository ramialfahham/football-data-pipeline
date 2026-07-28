# Review — feat/rename-matchday-pilot — 2026-07-28

> Machine-checked review artifact (governance G3). Written in step 4 (Lock), after staging and after
> the blinded reviewers returned. **Three rounds, at the cap.** Both FAILs were real, and both were
> the same failure class, so the history is here rather than lost:
>
> **Round 1 — bi-analyst-reviewer FAIL: no rendered-page evidence.** #827 requires it for any
> `site_v2/src/**` diff. I had quoted `dist/` strings inline, which proves text substitution and says
> NOTHING about layout. Its specific finding: the wordmark grows from `MatchdayIQ` to
> `MatchdayPilot` while `.brand` is `flex: none` (`system.css:363`) in a header where, below 700px,
> `.mainnav` is `display:none`. My claim that the rename "changes the word and nothing visual" was an
> assertion about layout I had never measured. Measured since: **+19px, 40px clearance remaining at
> 320px**, no overflow, no horizontal scroll.
>
> **Round 2 — cto-reviewer FAIL, on a REAL missed rename.** `SiteFooter.astro` was never renamed, so
> every shipped page carried `MatchdayPilot` in the header and `MatchdayIQ` in the footer — both
> present in one built file.
>
> **Why every check in this contract was structurally incapable of finding it, which is the lesson.**
> The wordmark is split across markup — `Matchday` then `<span>IQ</span>` — so no file contains the
> literal `"Matchday IQ"` and none contains `mdiq`. The impact_map's own grep evidence could never
> have caught it. Worse, it falsified my round-1 evidence artifact: it claimed
> `staleBrandAnywhere: false` from a regex over `document.documentElement.outerHTML`, which
> **preserves the span split**. Over `textContent` the string is contiguous `MatchdayIQ` and matches.
> **A rename is verified against RENDERED TEXT — never a source grep, never `outerHTML`.**
>
> A second, self-inflicted instance of the same class inside the fix: the explanatory comment I first
> added to `SiteFooter` was an HTML comment naming the old brand, and **Astro emits `<!-- -->` into
> the built page** — shipping the stale string straight back into the output. Both wordmark comments
> are now Astro expression comments (`{/* … */}`).
>
> **Round 3 — all three PASS**, each re-verified against the real `dist/` rather than against the
> corrected prose. `grep -rl "Matchday IQ\|MatchdayIQ\|matchdayiq" dist/` returns nothing;
> all 12 wordmark occurrences read `Pilot`; the only comment surviving in any built page is the
> pre-existing `noindex` note.

diff_sha256: e71d5494102cc330c83a1db7b24f8f3a14431ccda58579c0df8652128dbd4c6b

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- **Four amendments on a "rename the site surface" PR — ruled DISCOVERY, not drift.** I put the
  question to it in exactly those terms, including that my own reading was self-serving, rather than
  defend it. Its ruling, per amendment: 1 (fnmatch patterns) is a syntax repair covering the same
  four files, no scope change; 2 (`page-spec.schema.json`) was already in `scope_paths` and makes
  this contract's own `done_when` TRUE rather than weakening it; 3 (`launch.json` +
  `rendered_page_evidence.md`) are both in `scope_paths` and required to satisfy `done_when`'s #827
  clause; 4 (`SiteFooter.astro`) was NOT in `scope_paths` and is the one that mattered — admitted on
  the grounds that the objective *"rename the SITE surface"* covers all surface renderings, the
  omission was an impact_map blind spot rather than builder convenience, and the amendment was
  prompted by a reviewer FAIL. No `decisions_reserved` item moved; no §10 boundary crossed.
- **Grep-based impact_map evidence has a structural blind spot on split markup.** Recorded as the
  transferable lesson: for frontend markup work, string search is necessary but not sufficient, and
  the only reason this did not ship was that the review cycle caught what the contract's own
  evidence commands could not. (Appendix A6.)
- **Header/footer brand consistency verified at the source**, not from my description: both
  components now render the same `Matchday<span class="iq">Pilot</span>` structure and both take the
  brand from the single exported constant.
- **The refused fifth amendment is correct discipline.** `system.css:2` still carries
  `MATCHDAY IQ — v2 DESIGN SYSTEM` in a header comment. Leaving it beats amending the LOCKED design
  system for a comment that is not load-bearing and is stripped at build.

## cto-reviewer
VERDICT: PASS
risks_checked:
- **The round-2 FAIL is closed in the BUILD, not just the source.** Re-verified all 12 wordmark
  occurrences across the built pages read `Pilot`; the header/footer pair in a single file was the
  specific defect and both now agree.
- **No HTML comment leaks the old brand into any built page.** The only comment surviving anywhere
  in `dist/` is the pre-existing `noindex` note — confirming the self-inflicted second instance is
  closed, and that the `{/* … */}` conversion behaves as claimed.
- **`mdiq-theme` → `mdp-theme` is a deliberate, stated discard**, not a silent side effect: it drops
  every saved theme preference, which is free only because the site is unpublished (`noindex`,
  unlisted) so there is no reader to lose one. `SiteHeader.astro` and `Layout.astro` were checked to
  use the same key — a mismatch would silently break the toggle's persistence.
- **`astro.config.mjs` `site` corrected from a host DELETED on 2026-07-21** to `matchdaypilot.com`.
  Nothing consumes `Astro.site` yet (no canonical, no sitemap — that is C2), so this is a
  latent-wrong value fixed before anything depends on it. `www → apex` is configured at domain
  connection, NOT in `firebase.json`, where a path-only redirect would loop.
- Agreed with leaving `system.css:2`'s stale comment untouched: the file is locked and the comment
  is stripped at build.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- **The split-wordmark defect is fixed at the byte level**, verified by grepping the real
  `dist/en/teams/manchester-united/index.html` directly rather than trusting the corrected evidence
  doc: `Matchday<span class="iq">Pilot</span>` appears twice (header and footer), and a
  case-insensitive sweep of the whole `dist/` tree for the old brand returns zero files.
- **Footer wordmark layout at 320x720 — a container neither reviewer had measured.** `.footer-in`,
  104px wordmark (smaller footer type), `footerBrandOverflows: false`, no horizontal scroll. This
  closes the round-1 layout finding symmetrically with the header measurement.
- **No third reader-visible brand surface was missed**, verified by its own sweep of all of
  `site_v2/` — wider than `site_v2/src/`. The only additional hits are `"matchday-aligned"` in
  `TeamPerformance.astro`/`DeservedHero.astro`, which is football-window vocabulary and not the
  brand, and `package.json`'s `"name": "matchdayiq-site-v2"`, an npm identifier that never appears in
  any HTTP response. Left for C2, which edits `package.json` anyway to add `@astrojs/sitemap`.
- **`{brand}` interpolates in all three locales** rather than rendering literally — a literal
  `{brand}` would have shipped silently. Confirmed the EN key count extracted by
  `check-page-specs.mjs`'s own regex is 110 before and after, proving the `t()`-param form (not a
  template literal) did not blind the existing gate.
- On sufficiency for #827: yes, and the stated rule — verify a rename against rendered/joined text,
  never source greps or `outerHTML` — is the correct generalization of what let this past both of us.

## escalations
(none)
