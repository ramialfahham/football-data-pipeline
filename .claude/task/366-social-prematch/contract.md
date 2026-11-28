# Task contract — the pre-match social image generator

objective: >
  One command with a fixture slug writes the approved German pre-match image. The template lives in
  design-mocks/social/ with its own frozen CSS, font and logo, and reads every per-match value from
  the marts.

refs: >
  #366 (the requirement). #251 (the logo). The image design was approved in chat, 28 Nov 2026.

scope_paths:
  - .claude/task/366-social-prematch/
  - design-mocks/social/**
  - tests/test_social_prematch.py

approved_design:
  - none: no page output changes

depends_on:
  - none: no code of an open merge request is used

shared_files:
  - none: no design baseline, pin or font-coverage file changes

impact_map: >
  No structural path in scope: no ingestion, dbt model, export script, site tree or protected path.
  Nothing imports design-mocks/social/. scripts/check_design_inventory.py runs only the top-level
  design-mocks/gen_*.py files, and the new script is neither. The script reads three marts and
  copies two crest files from the crest bucket; it writes only into its own ignored out/ folder.

decisions_taken: >
  The design, its labels and its metric order are the first posted image, unchanged (approved in
  chat, 28 Nov 2026). The template moves into the repo as its own merge request (approved in chat,
  28 Nov 2026). The two crests are copied at run time into an ignored folder and never committed
  (approved in chat, 28 Nov 2026). The logo files are copies of the mark and the wordmark of the
  approved logo. The run refuses a match whose round is not a numbered matchday, whose kickoff is
  not confirmed, whose standing is a knockout round, or where a team's window holds fewer than five
  matches with team stats: the image's text claims each of these. Dependencies: only packages
  already in requirements.txt, and the Edge browser already on the machine. No new gate. Cost: one
  on-demand BigQuery read of about 0.1 GB, capped in the code at 1 GB; no recurring cost.

decisions_reserved:
  - none: questions go to the coordinating session.

done_when:
  - python -m pytest tests/test_social_prematch.py is green.
  - The render from the first match's saved data matches the approved PNG pixel for pixel, or each
    difference is shown.
  - A live run with the fixture slug writes a 1080x1350 PNG; its dry-run size is under 1 GB.
  - python scripts/ci_local.py --mr is green.

amendments: (none)
