# Task contract — the deploy exports every data set the pages read

objective: >
  The site deploy builds every page from one full export and none from the committed sample:
  deploy:export exports every data set a built page reads into a staging folder, and
  deploy:site-v2 empties site_v2/src/data except its README and copies that export in before it
  builds. Today the export holds teams and fixtures only and lands over the sample, so the home
  page, the competition pages, the competitions index and the day pages are built from the sample
  of 25 Sep, and 54 of their links lead to matches the warehouse has since moved.

refs: >
  #156, the site built from live data (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/156),
  its step 1 (the entity list) and its third requirement (production no longer shows the
  committed sample). The nightly schedule stays in #156. The plan: approved in chat, 2026-10-17.

scope_paths:
  - .gitlab-ci.yml
  - site_v2/src/data/README.md
  - docs/wireframes/08_browse.md
  - docs/site_architecture.md
  - tests/test_sentence_length_in_docs.py
  - tests/test_no_decision_history_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

protected_override: >
  .gitlab-ci.yml, jobs deploy:export and deploy:site-v2 only (their scripts, artifact path and
  comments; rules and needs unchanged): approved in chat, 2026-10-17, as the plan for #156 step 1
  and its amendment.

impact_map: >
  writers: deploy:export runs scripts/export_site_data.py into site_v2/export_data and hands that
  folder to deploy:site-v2 as its artifact; no BigQuery table is written.
  downstream: deploy:site-v2 (needs deploy:export) starts from its own checkout, which holds the
  committed sample; it empties site_v2/src/data except README.md, copies the artifact's files in,
  then builds and publishes the site. No other job reads the artifact; the MR and main builds
  (build:site-v2) keep building from the committed sample, which this change does not touch in the
  repository.
  guard: both jobs' rules stay `web` only, manual (deploy:site-v2 on success of the export);
  nothing new fires them. The emptying step runs in deploy:site-v2's own clone, so it removes
  nothing from the repository. If the export fails, deploy:site-v2 does not start; if the copy or
  the build fails, nothing is deployed, as today.
  layer_rules: the export selects and shapes served values only; no export code changes.
  deploy_order: none; the first manual deploy from main after the merge is the proof on GitLab.
  blast_radius: the published site is built from the export alone: competition pages for every
  competition and season, the home page, the competitions index, the day pages, and the player
  pages the full export brings, 221,721 pages measured locally. The export reads 0.370 GiB more
  per deploy (dry run: competitions 0.193, landing 0.158, matches 0.019, competition_index
  0.000; metric_groups and metric_rows read the seeds, not BigQuery), about 1.30 GiB per deploy
  in all. The deploy runs only when started by hand, so the cost is not recurring.

acceptance_criteria:
  - "1. deploy:export runs the export with --entities teams,fixtures,competitions,competition_index,landing,matches,metric_groups,metric_rows into a staging folder, its artifact; deploy:site-v2 empties site_v2/src/data except README.md and copies that folder's files in before it builds; both jobs' rules are unchanged."
  - "2. A full-scale build from that data, the sample removed and only exported files present, passes the page build at the deploy heap; audit-seo lists none of the 54 dead links that came from the committed sample, and every violation it does list is named on the MR with its cause."
  - "3. site_v2/src/data/README.md says the deploy builds from a full export and never from the committed sample, which is the MR build's input."
  - "4. The MR pipeline passes: lint, tests and the sample build."

decisions_taken: >
  Approved in chat, 2026-10-17: the plan, the four acceptance criteria, the entity list (every data set a page reads; nav,
  leaderboards, glossary and players have no reader and stay out), emptying the data folder
  in the build job before the export is copied in, and the 0.370 GiB added per manual deploy.
  THRESHOLD: a cost change on a manual job, measured and approved; not recurring. No test pins the
  CI script: the full-scale audit on each deploy fails on a page built from stale data (approved
  in chat, 2026-10-17).

decisions_reserved:
  - The player pages that share a heading or title with another player (453 violations at full scale).
  - The competition tab titles over the 660px hard cap (8 violations).
  - The World Cup Qualification Africa page linking an Eritrea team page that is not built (3 violations).
  - The two Nyasa Big Bullets team ids (9 violations).

done_when:
  - The full-scale build from export-only data shows none of the sample's dead links.
  - Reviewers cto-reviewer, platform-reviewer, bi-analyst-reviewer and scope-auditor pass.
  - The MR pipeline is green.

amendments: >
  2026-10-17: + docs/wireframes/08_browse.md — authority: the standing rule that a claim made false
  by a change is removed in the same MR; content: the "CI wiring" bullet, which says
  competition_index is not in the deploy's entity list, is removed.
  2026-10-17: the emptying moves from deploy:export to deploy:site-v2, because deploy:site-v2 starts
  from its own checkout holding the sample and unpacking the artifact deletes nothing; the export
  goes to a staging folder; criterion 1, the objective, protected_override and impact_map say so —
  authority: approved in chat, 2026-10-17.
  2026-10-17: + docs/site_architecture.md — authority: the standing rule that a claim made false by
  a change is corrected in the same MR; content: the deploy bullet, which says deploy:export runs
  the export into site_v2/src/data, names the staging folder and deploy:site-v2's copy.
  2026-10-17: + tests/test_sentence_length_in_docs.py — authority: the test's own rule that its pin
  moves down when a document loses a long sentence; content: the README's pin drops from 22 to 21.
  2026-10-17: + tests/test_no_decision_history_in_docs.py — authority: the test's own rule that its
  pin moves down when a document loses history lines; content: the README's pin drops from 18 to 16.