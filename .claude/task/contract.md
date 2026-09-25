# Task contract — #155: two meetings of the same clubs share one match-page title

objective: >
  Give every match preview page a title no other match page of its language shares, by adding the
  match's date to seoFixtureTitle in EN/DE/FI, so the full-scale build's SEO audit passes and #160's
  every-competition sample can ship.

refs: >
  #155 (the build issue; its What exactly is the requirement); docs/wireframes/01_fixture_page.md §8
  (the title rule: the competition is not in the title); the plan approved in plan mode, with its
  measurement over last night's 4,795 upcoming fixtures x 3 languages.

scope_paths:
  - site_v2/src/i18n/strings.ts
  - site_v2/src/pages/[[]lang]/[[]competition]/[[]matches]/[[]fixture].astro
  - docs/wireframes/01_fixture_page.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  writers: none; the date is the fixture payload's served `kickoff`, formatted by the existing
    formatShortDate (UTC, the day the match's address already carries).
  downstream: seoFixtureTitle has one consumer, the match page ([fixture].astro), which feeds
    <title>, og:title and twitter:title through Layout.astro; the JSON-LD name and the description
    are unchanged. `grep -rn seoFixtureTitle site_v2/src` → strings.ts (3 locales), [fixture].astro,
    src/specs/competition/matches/fixture.spec.json (the key, unchanged).
  layer_rules: consumption layer formats only; no value computed.
  deploy_order: site-only; deploy:site-v2 is manual; the site is unlisted and noindex.
  blast_radius: every match page title in three languages: 849 in the committed sample, 14,385 at
    full scale. Measured: duplicates 30 -> 0; worst width 551px -> 535px; every title inside the
    600px budget.

acceptance_criteria:
  - "Two match preview pages of one locale never share a `<title>`. Today the title is `{home} vs {away}: Preview` (`seoFixtureTitle`, EN/DE/FI), so two unplayed meetings of the same two clubs collide: a cup tie and a league match (SC Paderborn 07 vs VfB Stuttgart in the DFB-Pokal on 2026-10-27 and in the Bundesliga on 2026-10-10), or two league meetings inside one season (Gangwon FC vs Incheon United, K League 1, 2026-09-27 and 2026-10-18). The audit's check 5 fails the build on each."
  - "The wording of the corrected title is the CPO's (user-visible copy, all three languages), put on the MR that changes it; the competition and the date are the two facts that tell the meetings apart, both served on the fixture payload."
  - "`node scripts/audit-seo.mjs site_v2/dist` is clean on a build that carries every unplayed match (`check-built-pages` proves the count: 5,022 on 2026-09-19)."

decisions_taken: >
  The competition stays out of the title, as 01_fixture_page.md §8 rules; measured, adding it puts
  1,672 titles over the 660px hard cap. The date alone leaves no duplicate. The CPO chose, in chat,
  "Date replaces Preview": EN `{home} vs {away}, {date}`, DE `{home} - {away}, {date}`, FI
  `{home}–{away}, {date}`, the date in the short month form ("29 Dec", "29. Dez.", "29.12.");
  measured worst 535px, every title inside the 600px budget, so the budget guard stands. The word
  "Preview" leaves the title. The final wording is shown on the MR head, as #155 says.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - The final title wording in all three languages: shown to the CPO on the MR head.
  - The match page's content (#132).

done_when:
  - npm run build on the committed sample exits 0; pytest passes; check_copy_gate passes.
  - A build carrying every unplayed fixture (last night's export) passes audit-seo with 0 violations
    and check-built-pages proves its match page count; with {date} removed from the EN title the
    same build fails check 5.

amendments: (none)
