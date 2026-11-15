# Task contract — phone fixes, the causes a written rule already settles (#231 audit, MR 1)

objective: >
  Five causes the phone audit found on the built site at 280-768px are fixed where a written rule
  already says what the page does: every page's breadcrumb is the shared Breadcrumb component; a name
  never splits between its initial and surname; the match header's venue breaks between words; a
  Competitions list name wraps between words; no chart axis label is clipped.

refs: >
  Go-live issue #290 (gate item 1: the phone sweep finds 0 breaks); #231 (narrow-screen rules).
  Causes 4a, 5, 7b, 10 and 13 of the phone audit. Causes 1, 3, 4b, 6, 9, 11a, 12 and 14 wait for the
  CPO; 2 is #289; 7a and 8 are #230; 11b is #250 MR 2. The Player club link and the Teams league
  heading link are not breadcrumbs: their tap area is cause 4b, left out (agreed through the
  coordinating session, 2026-11-12).

scope_paths:
  - .claude/task/231-phone-fixes-mr1/
  - site_v2/src/components/matches/MatchesDay.astro
  - site_v2/src/components/fixture/Masthead.astro
  - site_v2/src/pages/[[]lang]/[[]competitions]/index.astro
  - site_v2/src/pages/[[]lang]/[[]competition]/index.astro
  - site_v2/src/pages/[[]lang]/[[]competition]/[[]matches]/index.astro
  - site_v2/src/pages/[[]lang]/[[]competition]/[[]stats]/index.astro
  - site_v2/src/pages/[[]lang]/[[]players]/index.astro
  - site_v2/src/pages/[[]lang]/[[]players]/[[]nation].astro
  - site_v2/src/pages/[[]lang]/[[]players]/[[]player].astro
  - site_v2/src/pages/[[]lang]/[[]teams]/index.astro
  - site_v2/src/pages/[[]lang]/[[]teams]/[[]team].astro
  - site_v2/src/lib/wholeWords.mjs
  - site_v2/src/lib/wholeWords.test.mjs
  - site_v2/src/lib/chartTheme.ts
  - site_v2/src/styles/system.css
  - tests/test_phone_fixes_231.py
  - tests/fixtures/design_inventory/baseline.json
  - site_v2/src/components/fixture/Breadcrumb.astro
  - docs/design/components.yml

protected_override: >
  docs/design/components.yml: the Breadcrumb's narrow form states that a trail of two levels keeps
  Home as a link under 700px, approved in chat, 2026-11-15.

impact_map: >
  writers: none; these are page templates, one build-step module, one chart-layout module and the
  stylesheet. No dbt model, no export script.
  downstream: site_v2/dist only. Breadcrumb.astro changes by one condition: a trail of two levels
  (the Competitions, Teams, Players and Matches pages) no longer marks Home far, so Home stays under
  700px; the component is already used by the Match page and its trails of three or more levels are
  unchanged.
  wholeWords.mjs runs in middleware.ts over every page's body text.
  layer_rules: not applicable; consumption layer, no computation added (markup, a text join, a
  stylesheet rule and drawing margins).
  deploy_order: none; deploy:site-v2 is manual.
  blast_radius: every page's breadcrumb markup (20px to 44px links; on the four two-level pages Home
  now shows on a phone), names written as an initial and
  a surname (wrapped in the no-break span), the venue item, the Competitions list name (the Teams list's team name shares the rule and wraps the same way), the Team
  Performance scatter margins. Counts before and after are in the MR.

acceptance_criteria:
  - On the built site no page but Home emits a nav.crumb that is not the Breadcrumb component's nav.trail, and every breadcrumb link measures 44px tall at 280-768px in EN, DE and FI.
  - At 280-768px in EN, DE and FI the audit's sweep finds 0 names split between an initial and its surname.
  - At 280-320px the match header's venue breaks between words, and no Match page scrolls sideways because of it.
  - At 280-768px no Competitions list name is cut with an ellipsis; a long name wraps between words.
  - At 280-768px no chart axis label on the Team Performance scatter lies outside its svg.
  - The sweep shows no new break class against the gitlab/main baseline, and no class rises except the middle-dot counts of cause 3 (the player-row stat dot and the kick-off dot), which MR 1b removes; no pin baseline is raised.

approved_design:
  - competitions: #128
  - competition: #129
  - matches: #130
  - match: #132
  - statistics: #139
  - teams: #133
  - team: #134
  - players: #135
  - player: #136

decisions_taken: >
  Each change applies a written rule: the registry's Breadcrumb (used on every page but Home, narrow
  form, 44px link), the rule that a name never breaks inside itself, and the registry's "breaks:
  between words" for the kick-off line and the Competitions name. The initial-and-surname join is one
  shared step in wholeWords.mjs, not four component edits (agreed through the coordinating session,
  2026-11-12). The criteria above are drafted here and go to the CPO through the coordinating
  session before review round 1.

decisions_reserved:
  - none: the Player club link and the Teams league heading link (tap area) stay with cause 4b, which the CPO decides.

done_when:
  - The sweep scripts re-run on the built branch at 280-768px in EN, DE and FI show causes 4a, 5, 7b, 10 and 13 at 0 and no new break; before and after counts are in the MR.
  - The full pytest, the site's node tests and the offline gates pass.

amendments:
  - The Players hub and the nation page join the scope: they take the shared Breadcrumb with 44px links and nothing else changes on them (page design: players #135). Approved in chat, 2026-11-14.
  - The six acceptance criteria are approved, criterion 6 as worded above. Approved in chat, 2026-11-14.
  - The design inventory's pin file joins the scope for lowering only: removing the Competitions name's text-overflow rule drops banned_properties for system.css from 7 to 6 and the count test demands the lower pin. Approved in chat, 2026-11-14.
  - On a two-level trail (Home and the page: the Competitions, Teams, Players and Matches pages) phones under 700px keep Home as a 44px link; trails of three or more levels are unchanged. Breadcrumb.astro and the Breadcrumb's narrow-form line in components.yml join the scope; the system.css rule is already in scope. Approved in chat, 2026-11-15.