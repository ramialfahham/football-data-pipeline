# Task contract — Nation pages: an h1 of their own

objective: >
  Issue #296: a nation page (/{lang}/{players word}/{nation}/) gets an h1 that differs from its
  national team page's h1 (the bare team name) in EN, DE and FI, so audit-seo reports no
  "h1 is not unique" on a nation page. The committed sample holds one national team whose nation
  page is in the sample too, so the MR build and a unit test catch a collision.

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
  - site_v2/src/data/teams/1104.json
  - site_v2/src/data/README.md
  - .gitignore

impact_map: >
  writers: none; the h1 is template text, no dbt model, export or ingestion change.
  consumption: the nation page template only, `grep -rn "seoNation" site_v2/src` shows the two
  readers of its strings, the page's title and description in the same file; every other page keeps
  its h1. The sample gains one real exported team payload, teams/1104.json (Georgia, 312 KB),
  produced by fetch_team_payloads of scripts/export_site_data.py unchanged, read-only, 347.5 MB
  dry-run size for the 8 queries (no write to the warehouse); teams_index.json already lists it.
  site: the Georgia national team page appears in the sample build in EN, DE and FI.
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
  Which national team joins the sample (Georgia) is an engineering call of this session: the
  smallest national team payload of a nation that has a nation page. The sample refresh rule of
  site_v2/src/data/README.md ("never hand-edit a payload") is kept: the file is the unchanged
  output of fetch_team_payloads for that one team.

decisions_reserved:
  - none: the wording is the coordinating session's call, not a CPO-class decision, and the country
    names in the page's language are #233

acceptance_criteria:
  - On the built sample, the Georgia nation page and the Georgia national team page have different h1 text in EN, DE and FI.
  - audit-seo reports no "h1 is not unique" finding on any nation page of the sample build.
  - The committed sample holds a nation page and a national team page of the same nation, and a unit test fails when it does not.
  - audit-seo reports no "h1 is not unique" finding on a nation page of the live build the #156 session leaves locally, if it is still there.

done_when:
  - python scripts/ci_local.py --mr is green
  - node --test site_v2/src/lib/playerIndex.test.mjs passes
  - audit-seo on the built sample reports 0 violations

amendments: (none)
