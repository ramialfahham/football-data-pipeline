# Task contract — Nation pages: an h1 of their own

objective: >
  Issue #296: a nation page (/{lang}/{players word}/{nation}/) gets an h1 that differs from its
  national team page's h1 (the bare team name) in EN, DE and FI, so audit-seo reports no
  "h1 is not unique" on a nation page. A unit test fails when a nation page's h1 equals the bare
  nation name in any of the three languages; the nightly's audit-seo on the full build refuses the
  deploy if any h1 repeats.

refs: >
  #296; #290 go-live; #135 Players page design (nation pages came with its build); #233 country
  names in the page's language (not in scope).

depends_on:
  - none: the nation page and audit-seo are on main (7bcb1db2); no open MR changes them

shared_files:
  - none: no design baseline, component registry or chart screenshot changes

scope_paths:
  - .claude/task/296-nation-h1/
  - site_v2/src/pages/[[]lang[]]/[[]players[]]/[[]nation[]].astro
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/playerIndex.test.mjs

impact_map: >
  writers: none; the h1 is template text, no dbt model, export or ingestion change.
  consumption: the nation page template only, `grep -rn "seoNation" site_v2/src` shows the two
  readers of its strings, the page's title and description in the same file; every other page keeps
  its h1. The committed sample, the design baselines and the data README do not change.
  layer_rules: no dbt layer touched; audit-seo's h1 uniqueness check is unchanged and is the gate.
  deploy_order: none; the nightly's export and build read the same template.
  blast_radius: 101 nation pages per locale on a full build change their h1 text; the sample's 27
  nation pages likewise; no number changes.

approved_design:
  - players: #135

decisions_taken: >
  The nation page h1 reuses the page's own title string, seoNationTitle ("{nation} players",
  "Spieler aus {nation}", "{nation}: pelaajat"), so no new copy is created. Fan wording before
  go-live: the coordinating session's call of 21 Nov 2026, an engineering call that reuses existing
  copy.
  The sample holds no national team page: the design inventory's Team page glob measures a
  national team page as a club page, and the national-team design work owns that and adds the
  sample pair with its own pins. The guard is the unit test in three languages plus the nightly's
  audit-seo on the full build. This changes #296's criterion "the sample holds a nation page and a
  national team page of one nation"; the coordinating session's call of 21 Nov 2026, an
  engineering decision.

decisions_reserved:
  - none: the wording is the coordinating session's call, not a CPO-class decision, and the country
    names in the page's language are #233

acceptance_criteria:
  - On the built sample, every nation page's h1 differs from the bare nation name in EN, DE and FI.
  - audit-seo reports no "h1 is not unique" finding on any nation page of the sample build.
  - A unit test fails when a nation page's h1 equals the bare nation name in EN, DE or FI.
  - audit-seo reports no "h1 is not unique" finding on a nation page of the live build the #156 session leaves locally, if it is still there.

done_when:
  - python scripts/ci_local.py --mr is green
  - node --test site_v2/src/lib/playerIndex.test.mjs passes
  - audit-seo on the built sample reports 0 violations

amendments:
  - 21 Nov 2026: the sample national team (teams/1104.json, README, .gitignore) leaves scope and the acceptance criteria 1 and 3 are reworded to the unit-test guard; authority: the coordinating session's call of 21 Nov 2026 (engineering decision).
