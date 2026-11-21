# Task contract — a team row links only to a team page the build makes

objective: >
  Issue #333: a team row in a table leads to the team page only when this build makes that page,
  and is plain text otherwise, as a player row already is. A first full build from live data had 3
  dead internal links (Eritrea in the World Cup qualification Africa standings, EN/DE/FI), so
  `audit-seo` refused to deploy.

refs: "#333; #170 (a team page for every club the site shows); #132"

scope_paths:
  - .claude/task/333-team-link-built-only/**
  - site_v2/src/lib/builtTeams.mjs
  - site_v2/src/lib/builtTeams.test.mjs
  - site_v2/src/components/ui/TableRow.astro
  - site_v2/src/pages/*teams*/index.astro

impact_map: >
  writers: none; the export is unchanged, the module reads `src/data/teams/*.json`, the files
  `[team].astro` builds a page from.
  downstream: `TableRow` is used by StandingsTable, DeservedTable, RankingBoard (team boards),
  TeamDeserved and LastSeasonTable (`grep -rn "TableRow" site_v2/src --include=*.astro`), so the
  pages reached are Home (Top teams), the competition page (standings, deserved points, team
  boards), the Statistics page (team boards through RankingsBlock), the Teams page and the Team
  page; LastSeasonTable passes no team slug and the match page's Match leaders are player rows
  with `linked={false}`. A row
  whose team has a payload renders exactly as before; one without becomes a `div`. The Teams page
  already links a team only when a payload exists; it takes the same lookup from the module.
  layer_rules: no dbt, no export, no new page.
  deploy_order: none; site code only.
  blast_radius: rows of teams without a payload: today a dead link, afterwards plain text. On the
  live export of 21 Nov that is Eritrea's row on the Africa qualification standings, 3 locales.
  The committed sample's teams all have payloads, so its pages are unchanged.

approved_design:
  - home: #127
  - competition: #129
  - teams: #133
  - team: #134
  - statistics: #139

depends_on:
  - none: site code on main alone
shared_files:
  - none: no design, registry, font or chart baseline changes

acceptance_criteria:
  - A team row on any page leads to the team page when this build makes one, and is plain text when it does not.
  - The World Cup qualification Africa page (EN, DE, FI) has no dead internal link: Eritrea's row in the standings is plain text.
  - The Teams page and every table row take "the team has a built page" from one place.

decisions_taken: >
  The rule that a row leads only where a page exists is the one players already follow and the
  Teams page already applies to teams; plain text for a team with no page was ruled by the
  coordinating session, approved in chat, 21 Nov 2026. No new dependency, no recurring cost, no
  new mechanism: one lookup module beside builtPlayers.

decisions_reserved:
  - none: the rule and the scope are the approved issue text; whether a team that has played no match ever gets a page stays with #170.

done_when:
  - cd site_v2 && node --test passes, with a test that pins the lookup (a slug in a teams directory is built, an absent one is not).
  - A build of the committed sample plus the live export's Africa qualification payload has Eritrea's row as plain text on the page in EN, DE and FI and `node scripts/audit-seo.mjs` reports no dead link.
  - python scripts/ci_local.py --mr is green on this branch.

amendments: (none)
