# Task contract — rename the site surface to Matchday Pilot (PR C1 of two)

> Written on a CLEAN tree, branch `feat/rename-matchday-pilot` off `main` (`27b26e9`).
> PR C was split on its own scope warning: **C1 = this rename (small, independent), C2 = the SEO gate
> and the emitted surface**. C1 goes first because it touches `strings.ts`, which C2's title work also
> touches — sequencing them avoids two conflicting edits to the same file.

objective: >
  The CPO secured `matchdaypilot.com` (2026-07-28) and confirmed the product is becoming **Matchday
  Pilot**. Rename the SITE surface — the brand string, the wordmark, the four scaffold titles and the
  theme storage key — and correct `astro.config.mjs`'s `site`, which currently points at a host that
  was deleted on 2026-07-21.

  Done now, deliberately, because the surface is three pages plus one i18n file. After the remaining
  6 of 15 screens are built it is a materially wider change.

refs: >
  CPO, 2026-07-28: *"It will be matchday pilot"*, and on the domain: *"matchdaypilot.com"*.
  PR C plan (approved) — Part 4 and the Scope warning that recommends this split.
  #860 (the north star still describes the retired MVP and is titled "Matchday IQ" — the POSITIONING
  and tagline are settled there, NOT here).

  Domain knowledge gathered before building, per #858: two independent challenges of the PR C plan.
  The second found the trap this contract's done_when now guards — see decisions_taken.

scope_paths:
  - site_v2/src/i18n/strings.ts
  - site_v2/src/components/chrome/SiteHeader.astro
  - site_v2/src/components/chrome/SiteFooter.astro
  - site_v2/src/layouts/Layout.astro
  # NOTE: patterns, not literal paths. `task_contract_gate.py:285` matches with `fnmatch`, which
  # treats `[lang]` as a CHARACTER CLASS — so the literal path of any Astro dynamic route can never
  # match itself. `site_v2/src/pages/[lang]/teams/[team].astro` as a pattern matches
  # `site_v2/src/pages/l/teams/t.astro` and nothing real. Verified with fnmatch before rewriting.
  - site_v2/src/pages/index.astro
  - site_v2/src/pages/*/index.astro
  - site_v2/src/pages/*/teams/*.astro
  - site_v2/src/pages/*/*/matches/*.astro
  - site_v2/astro.config.mjs
  - site_v2/src/specs/page-spec.schema.json
  - .claude/launch.json
  - .claude/task/rendered_page_evidence.md
  - .claude/active_work.md

impact_map: >
  writers: all seven files are hand-authored source; none is generated. No dbt model, no export, no
    warehouse object is touched — this PR contains zero data changes.

  downstream: EVIDENCE (grep over the real tree):

      $ grep -rn "Matchday IQ" site_v2/src/ --include=*.ts --include=*.astro
      i18n/strings.ts:46,100,152,206,258,312   (6, all double-quoted, 3 locales x 2 keys)
      pages/index.astro:13,24                  (<title>, <h1>)
      pages/[lang]/index.astro:12,13,14,24     (3 headlines, <title>)
      $ grep -rn "mdiq" site_v2/src/
      components/chrome/SiteHeader.astro:83    (const KEY = "mdiq-theme")
      layouts/Layout.astro:39                  (localStorage.getItem("mdiq-theme"))
      $ grep -rn "footnote\|teamFootnote" site_v2/src/ --include=*.astro
      [team].astro:111 · [fixture].astro:104   (the only two call sites)

    `SiteHeader.astro:34` renders the wordmark as MARKUP, not a string:
    `Matchday<span class="iq">IQ</span>`, styled by `.brand .iq` at `system.css:364`.

  layer_rules: `site_v2/**` is the consumption layer. No fact is derived here — this changes display
    strings only. `system.css` is the LOCKED design system (transcribed verbatim from the approved
    mockup) and is deliberately NOT in scope: the `.iq` class name and its two-tone treatment are
    preserved, so this changes the word and nothing visual.

  deploy_order: no migration. `ci-site-v2` builds from the two committed samples on any `site_v2/**`
    change; `deploy-site-v2` is `workflow_dispatch` only, so nothing reaches the deployed site until
    the CPO triggers it. No warehouse rebuild, no nightly interaction.

  blast_radius: 6 i18n strings, 1 wordmark, 4 scaffold titles/headlines, 1 localStorage key, 1 config
    value. Every page's `<title>` changes on the two scaffolds; the two real pages' titles are
    entity-driven and do NOT contain the brand today, so they are unaffected until C2.
    ⚠ `mdiq-theme` -> `mdp-theme` DISCARDS every saved theme preference. Free today: the site is
    unpublished (`noindex`, unlisted `.web.app`), so there are no readers to lose one. Stated rather
    than left as a silent side effect.
    ⚠ `astro.config.mjs` `site` currently reads `https://ramialfahham.github.io` — a host DELETED on
    2026-07-21. Nothing consumes `Astro.site` yet (no canonical, no sitemap — that is C2), so this is
    a latent-wrong value being corrected before anything starts depending on it.

decisions_taken: >
  - The product is renamed to Matchday Pilot. CPO, 2026-07-28, verbatim above.
  - `site` becomes `https://matchdaypilot.com` (apex). NOTE: `www -> apex` is configured when the
    custom domain is connected in Firebase Hosting, NOT in `firebase.json` — Hosting redirects match
    on path only, so a path-based redirect would loop. That is the CPO's to do and does not block this.
  - The brand becomes ONE exported constant so a later change is one edit, not a sweep.
  - **The constant is interpolated via `t()`'s existing `{param}` mechanism, NOT a template literal.**
    `check-page-specs.mjs:90` extracts the EN i18n key set with `/([A-Za-z0-9_-]+):\s*"/g` — it matches
    on a DOUBLE QUOTE. Rewriting `footnote` as a backtick template would silently drop `footnote` and
    `teamFootnote` from the checked set, and `MIN_EXPECTED_KEYS = 50` would not trip on losing 2 of
    ~115. That is exactly the "silently lose a check" failure `check-page-specs.test.mjs` exists to
    prevent. Found by the second independent challenge, not by me.
  - The wordmark keeps its `.iq` class and two-tone treatment: `Matchday<span class="iq">Pilot</span>`.
    Renaming the class would be an edit to the locked design system for no visual benefit.

decisions_reserved:
  - **Positioning and the tagline.** "Football analytics for fans" stays untouched (and lives only in
    the retired `site/` MVP). The CPO asked whether to sharpen it; the answer is that it should follow
    the north star rewrite, not lead it. #860.
  - **The docs sweep.** `Matchday IQ` appears across `AGENTS.md`, `docs/roles/*`, `docs/north_star.md`
    and others. Renaming those is not this PR: `north_star.md` is owned by #860, and a repo-wide doc
    sweep is scope creep with no user-visible effect. This PR is the SITE surface only.
  - **`t()`'s `String.replace` interprets `$&`, `` $` `` and `$'` in the replacement** (`strings.ts:336`),
    and params can carry provider-supplied names. A real correctness bug, deliberately NOT fixed here —
    it belongs with C2's i18n work, where the title/description templates make it load-bearing. `{brand}`
    is a safe literal, so this PR adds no new exposure.
  - Promoting `SectionHead` to a real heading level, and the `<h1>`/`<h2>`-`<h6>` gaps generally. C2.

done_when:
  - `grep -rn "Matchday IQ" site_v2/src/` returns NOTHING.
  - `grep -rn "mdiq" site_v2/src/` returns NOTHING.
  - The EN i18n key count extracted by `check-page-specs.mjs`'s own regex is UNCHANGED before and
    after — proving the brand refactor did not blind the existing gate. Verified by running the
    extractor, not by reading the diff.
  - `astro.config.mjs` `site` is `https://matchdaypilot.com`.
  - `cd site_v2 && npm test` passes (the page-spec checker's suite).
  - `npm run build` succeeds and the built pages show the new brand — shown as rendered evidence, per
    #827, since this is a `site_v2/src/**` change.
  - ONE commit; `--staged-hash` equals CI's recomputed `main...HEAD` only when the branch is a single
    commit.
  - Required reviewers for these paths: scope-auditor (always), cto-reviewer (`site_v2/**`),
    bi-analyst-reviewer (`site_v2/src/**`).

amendments:
  - 2026-07-28: scope_paths rewritten from literal dynamic-route paths to fnmatch PATTERNS —
    authority: no scope change is intended or made; the same four files are covered. The original
    entries could not match anything, because `task_contract_gate.py:285` uses `fnmatch` and
    `[lang]`/`[team]` are character classes there. Verified before and after:
    `fnmatch('site_v2/src/pages/[lang]/teams/[team].astro', <literal itself>)` -> **False**, while it
    DOES match `site_v2/src/pages/l/teams/t.astro`. The replacement patterns were each asserted to
    match their real path.
    This is a trap for every future frontend task, since every Astro route under `[lang]/` is a
    dynamic route — recorded here and in the handover so the next contract does not repeat it.
  - 2026-07-28: + site_v2/src/specs/page-spec.schema.json — authority: this contract's own
    `done_when` requires `grep -rn "Matchday IQ" site_v2/src/` to return NOTHING, and after the
    rename exactly one occurrence remained: line 4, `"title": "Matchday IQ v2 page spec"`. It is
    JSON Schema metadata (an editor tooltip), not user-visible, and PR C2 rewrites this file to add
    the `seo` block — so deferring was an option. Making the assertion TRUE was chosen over weakening
    it, because a stale brand string left in a file is exactly the kind of thing that survives
    forever. One word; no schema semantics touched.
  - 2026-07-28: + .claude/launch.json and .claude/task/rendered_page_evidence.md — authority:
    bi-analyst-reviewer FAILed round 1 on exactly this. #827 requires rendered-page evidence for a
    `site_v2/src/**` diff, and it does not exist; inline prose quoting `dist/` strings proves text
    substitution and says NOTHING about layout. Its specific finding: the wordmark grows from 10 to
    13 characters ("MatchdayIQ" -> "MatchdayPilot") while `.brand` is `flex: none` (system.css:363)
    in a header where, below 700px, `.mainnav` is `display:none` and only the brand plus three 36px
    icon buttons share the row. My claim that this "changes the word and nothing visual" was an
    assertion about layout I never checked. `launch.json` is how this repo starts a preview, so it is
    needed to produce the evidence this PR's own done_when requires.
  - 2026-07-28: + site_v2/src/components/chrome/SiteFooter.astro — authority: cto-reviewer FAILed on
    a REAL missed rename. `SiteFooter.astro:31` still rendered `Matchday<span class="iq">IQ</span>`,
    so every shipped page carried `MatchdayPilot` in the header and `MatchdayIQ` in the footer —
    verified in the built output, both wordmarks present in one file.
    **Why every grep in this contract missed it, and the lesson:** the footer's brand is split across
    MARKUP (`Matchday` then `<span>IQ</span>`), so the document contains no literal `"Matchday IQ"`
    substring and no `mdiq`. The impact_map's own evidence commands were structurally incapable of
    finding it. A rename must be verified against RENDERED TEXT, not source greps.
    That same blind spot falsified my rendered-evidence artifact: it claimed
    `staleBrandAnywhere: false` from a regex over `document.documentElement.outerHTML`, where the
    string is broken by the span. Over `textContent` it is contiguous `MatchdayIQ` and matches. The
    evidence document is corrected and the check re-run against rendered text.
