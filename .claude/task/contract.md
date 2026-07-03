# Task contract — add MVP screenshot asset (docs-only, binary)

> Written on a CLEAN tree (branch docs/add-mvp-screenshot off main @ e60b091).
> Completes the deliverable reserved in the prior contract (README portfolio polish, MERGED #640):
> the README references docs/assets/screenshot.png, which the CPO has now supplied. Docs-only; no
> dbt/SQL/Python. Adds one binary image; no text/code behaviour changes.

objective: >
  Add the MVP screenshot the merged README already references (docs/assets/screenshot.png), so the
  README hero image resolves instead of showing a broken-image placeholder on main. The image is the
  CPO-supplied Matchday IQ landing/competitions view (PNG, 584x821). No other change.
refs: closes the docs/assets/screenshot.png reference added in #640; portfolio/visibility request 2026-07-03

scope_paths:
  - docs/assets/**
  - .claude/task/**

impact_map: >
  writers: NEW binary docs/assets/screenshot.png (CPO-supplied). No text file, no code, no models,
    no scripts, no CI, no seeds touched. The README reference to this path already exists on main (#640).
  downstream: none — a static image resolves an existing README <img>. No dbt graph, export, or build change.
  layer_rules: not applicable (no dbt models).
  deploy_order: not applicable — docs merge; GitHub serves the image and the README hero renders on merge.
  blast_radius: the README hero image on main resolves (currently a broken icon). No numbers, data, or
    behaviour. Social-preview upload (Settings UI, landscape 1280x640) remains a separate CPO manual step.

decisions_taken: >
  Path/name = docs/assets/screenshot.png (the exact path the merged README + docs/assets/README.md spec
  point at). Content = the CPO-supplied landing/competitions screenshot (portrait mobile), accepted as the
  README hero for now; a match-detail hero + a landscape social-preview crop are deferred (noted below).
  No image processing/cropping applied — the file is committed as supplied.

decisions_reserved:
  - The GitHub social-preview image (landscape 1280x640) is a separate CPO manual step (Settings UI).
  - Swapping the hero to a match-detail view is a later, optional change once v2 screens exist.

done_when:
  - docs/assets/screenshot.png exists in the repo and is a valid PNG; the README hero reference resolves.
  - No other file changed (scope = the image + .claude/task/** artifacts only).
  - scope-auditor PASS (docs/binary-only, no scope creep); review.md binds; CPO merges.

amendments:
  - 2026-07-03: fresh contract (prior task README portfolio polish merged as #640). CPO supplied the
    screenshot in-session and directed adding it at docs/assets/screenshot.png (option A).
