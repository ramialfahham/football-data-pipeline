# Task contract — the committed team samples, re-exported from prod

objective: >
  The Team page (#235) builds in merge requests from the 34 team payloads committed in
  site_v2/src/data/teams/, and those predate the data the page now needs: the Competitions block,
  the league strip, recent matches, last season's place from the official table and appearances
  in the squad. The same 34 teams are re-exported from prod by the exporter's own code, with
  their slugs unchanged, so every page that links to them still resolves.

refs: >
  #235 (build order approved in chat, 2026-10-28: the committed team samples are re-exported from
  prod once the warehouse work merges); the plan approved in chat, 2026-10-30.

scope_paths:
  - site_v2/src/data/teams/*.json
  - site_v2/src/data/README.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: scripts/export_site_data.py (fetch_team_payloads, write_entity), run once against prod;
  no model, mart or code changes. downstream: the two pages that read site_v2/src/data/teams,
  pages/[lang]/[teams]/[team].astro (one page per file and locale) and
  pages/[lang]/[competition]/[matches]/[fixture].astro (links a team only when its slug is
  built). layer_rules: data selected and shaped by the exporter, nothing computed in the site.
  deploy_order: none; deploy:site-v2 replaces this sample with the full export. blast_radius: the
  34 Team pages of the merge-request build; same files and slugs, so no link changes.

approved_design:
  - team: #134

acceptance_criteria:
  - "site_v2/src/data/teams/ holds the same 34 files as before, each written by the exporter's write_entity from fetch_team_payloads against prod, none edited by hand."
  - "Every one of the 34 payloads has the same slug as the committed file it replaces."
  - "teams/33.json carries recent_matches, and its featured season carries competitions and league_strip; its squad members carry appearances."
  - "After git clean -fX site_v2/src/data, the site_v2 build passes its prebuild tests, audit-seo and the built-page checks."

decisions_taken: >
  The plan, approved in chat, 2026-10-30: only the 34 team files move; landing.json, the
  Bundesliga payload, the fixtures and the .gitignore allowlist stay as they are. No code change:
  a scratch driver runs the exporter's sample path restricted to the 34 ids, with the whole-table
  reads the league views need left whole. One export of about 311 MB, no recurring cost, no new
  mechanism or dependency.

decisions_reserved:
  - A slug that differs from the committed one stops the task and goes to the CPO.

done_when:
  - The four acceptance criteria hold, shown in acceptance_evidence.md.
  - pytest and the offline gates pass; the MR's build:site-v2 and validate:ui pass.

amendments: >
  The impact map is added before the README edit, as the structural-surface gate requires.
