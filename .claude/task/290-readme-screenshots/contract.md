# Task contract — README screenshots of the site

objective: >
  The README shows the site: five pages (Home, Match preview, Match report, Team, Player), three
  views each at phone and desktop width, 30 images in all, taken by one script so they can be
  regenerated with one command after the page styles change.

refs: >
  Go-live issue #290. The five pages, the three views per page, the images and the README section
  were approved in chat, 2026-11-12, through the coordinating session.

scope_paths:
  - .claude/task/290-readme-screenshots/
  - scripts/readme_screenshots.py
  - docs/images/readme/
  - README.md
  - tests/test_readme_screenshots.py

impact_map: >
  writers: none; new script, image files and a README section. site_v2/src is not touched.
  downstream: none; nothing imports the script, no model or page reads the images.
  layer_rules: not applicable; no dbt model or ingestion file.
  deploy_order: none; the GitHub mirror shows the README after the merge.
  blast_radius: none; leaf docs and a standalone script. The script only reads site_v2/dist, which the person running it builds and which is gitignored.

approved_design:
  - none: no page output changes; the images show the pages as their approved designs define them

decisions_taken: >
  The script never installs or builds: it needs an existing site_v2/dist and stops with "run
  npm run build in site_v2 first" when there is none. It serves dist from a local static server and
  drives the Playwright pinned in requirements-ui.txt. Each page gives a crop of the top of the page
  and two block crops scrolled to a named section, as PNG, under 300 KB, with the site header.
  The Team top crop shows the Performance tab, the page choice the CPO made for this task
  (approved in chat, 2026-11-12).
  Where a page's approved design is not built yet, `--mock <page>=<html file>` renders the approved
  design mock of that page instead; with no flag every page is the built one. The mock's own
  controls, including its language switcher, are hidden. The mock files are not committed; they are
  kept outside the repository and their path is passed on the command line. The images of the Match
  preview, Team and Player pages come from mocks today; Home and Match report come from the built
  site.
  No player photo from the data provider is shown: the script replaces every player photo with the
  initials fallback of the site's own components, on built pages and in mocks, and stops if any
  remains (approved in chat, 2026-11-12). Club crests stay.
  The README section, its captions, the line "Phone and desktop views from the approved designs."
  and the sentence naming the two commands that regenerate the images were approved in chat,
  2026-11-12, through the coordinating session.

decisions_reserved:
  - none

done_when:
  - One command, after npm run build in site_v2, regenerates the 12 images of the built pages (Home,
    Match report). The other 18 (Match preview, Team, Player) come from the approved design mocks,
    kept outside the repo and passed with --mock, until those pages are built; then the same
    command, without the flag, regenerates all 30. This is temporary: approved in chat, 2026-11-12,
    through the coordinating session.
  - Each image is under 300 KB, and every image in docs/images/readme/ is used by the README.
  - pytest tests and the offline gates pass.

amendments: (none)
