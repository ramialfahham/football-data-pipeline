# Task contract — player photos off and the build fails on an image from a foreign origin

objective: >
  Apply the photos-off ruling: no built page shows or names a provider player photo. A player row and
  the player header show the initials. The player page names no image in its meta or JSON-LD.
  `npm run build` gains a pin on the images the built pages name: an `<img>` or `<source>` address,
  an `og:image` or `twitter:image` address and a JSON-LD `image` or `logo` address. Each is classed
  as a provider player-photo, a provider crest or logo, or another foreign origin. Player photos and
  other foreign origins are pinned at 0 on every build. Provider crests and logos are pinned at the
  count measured on the committed sample build; the pin holds on a sample build, in both directions,
  and is reported on a full export. The crest hosting (#36) lowers the crest pin to 0.
refs: "#36, #290 (gate item: 0 img from the provider's player-photo path), #293 (shirts replace the initials later)"

scope_paths:
  - site_v2/scripts/check-built-pages.mjs
  - site_v2/scripts/check-built-pages.test.mjs
  - site_v2/src/components/ui/PlayerRow.astro
  - site_v2/src/components/player/PlayerHeader.astro
  - site_v2/src/components/player/PlayerIndexRow.astro
  - site_v2/src/components/fixture/MatchLineups.astro
  - site_v2/src/components/fixture/PlayerToWatch.astro
  - site_v2/src/components/team/TeamSquad.astro
  - site_v2/src/pages/[[]lang]/[[]players]/[[]player].astro
  - docs/site_architecture.md
  - docs/ui_design_brief.md
  - .claude/task/36-img-origin-pin/contract.md
  - .claude/task/36-img-origin-pin/review.md
  - .claude/task/36-img-origin-pin/review_input.patch
  - .claude/task/36-img-origin-pin/acceptance_evidence.md
  - .claude/task/36-img-origin-pin/rendered_page_evidence.md

impact_map: >
  writers: none. No table or model is written. The export keeps serving `photo` and
  `player_photo_url` in the payloads; the components stop reading them.
  downstream: `PlayerRow.astro` is imported by `PlayerIndexRow.astro`, `TeamSquad.astro`,
  `MatchLineups.astro` and `PlayerToWatch.astro` (grep over `site_v2/src`: no other importer). The
  player header and the player page read `player.photo` only to pass it to `Crest.astro` and to the
  layout's `image` and the JSON-LD entity. `check-built-pages.mjs` runs as the last step of `npm run
  build` (pinned by `site_v2/scripts/build-wiring.test.mjs`). No dbt model, export script or other
  page file changes; no dbt lineage applies.
  layer_rules: none apply. `check_layer_contract.py` reads `dbt_project/models/**` only. The
  components drop a field and add no logic.
  deploy_order: independent. A full export build reports the provider counts while their pins are
  above 0 and fails on any player photo and any other foreign origin.
  blast_radius: every page that shows a player row or the player header loses its `<img>` and shows
  the initials: the Players page, the nation pages, the Team page squad, the match page line-ups
  and Players to watch, the Player page. The CSS slot `.pphoto` and the registry slot `photo` stay.
  The measured counts, before and after, are in the MR head.

depends_on:
  - none: the change reads the built pages and the components; no open MR's code is needed. Open MRs !503 and !504 touch other files.
shared_files:
  - none: no design baseline, chart manifest or chart pin changes; the player rows keep the same box and show the initials the rows already show when a player has no photo

decisions_taken: >
  The coordinating session's message of 2026-11-21 applies the photos-off ruling (CPO, approved in
  chat, 2026-11-12, #290): the initials are today's no-photo display, #293 replaces them with shirts
  later, so no new design choice is made. Three core-document lines drop the word "photo" and
  change nothing else: the `Person` row of the SEO table in `docs/site_architecture.md`, and the
  Images row and the Player Identity line in `docs/ui_design_brief.md`. The edit is strip-only,
  describes the output the photos-off ruling removed, and its exact text stands in the MR head,
  where the CPO's merge approves it (working_agreement §10, core text). The same message pins player photos at 0 on every
  build, crests and logos at the measured sample count, and other hosts at 0. No new dependency, no
  cost, no new pipeline run. The check extends the existing built-pages check.

decisions_reserved:
  - "none: the change shows the initials the rows already show when a player has no photo, per the photos-off ruling of 2026-11-12. The licence question for re-hosting crests and logos is answered separately and belongs to step 2 of #36."

approved_design:
  - match: #132
  - team: #134
  - players: #135
  - player: #136

acceptance_criteria:
  - "No built page names a provider player or coach photo: the built-pages check, with the player-photo pin at 0, passes on the build of the committed sample and counts 0 player photos in `img`, `source`, `og:image`, `twitter:image` and JSON-LD addresses."
  - "A player row on the Players page, a nation page, the Team page squad, the match page line-ups and Players to watch shows the player's initials in `.pphoto` and holds no `<img>`."
  - "The Player page header shows the initials in its crest circle and holds no `<img>`."
  - "The Player page carries no `og:image`, no `twitter:image` and no JSON-LD `image` from the player's photo."
  - "A built page with a provider player-photo address fails the built-pages check, whatever the build (unit test)."
  - "A provider crest or logo count that differs from its pin fails a sample build and is only reported on a full export, with the manifest-present branch of `main` covered by a test."

done_when:
  - "`cd site_v2 && node --test scripts/check-built-pages.test.mjs scripts/build-wiring.test.mjs` passes."
  - "`cd site_v2 && npm run build` on the committed sample passes and prints the image counts, 0 player photos."
  - "`python scripts/ci_local.py --mr` passes."

amendments: (none)
