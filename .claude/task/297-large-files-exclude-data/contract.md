# Task contract — the large-file check skips generated page data

objective: >
  Issue #297, unblocking: the large-file check skips generated page data under `site_v2/src/data/`;
  every other path keeps the 1 MB limit. `.pre-commit-config.yaml` gives the `check-added-large-files`
  hook `exclude: ^site_v2/src/data/`, the same exclusion every other hook in that file already carries.

refs: >
  #297.

scope_paths:
  - .claude/task/297-large-files-exclude-data/
  - .pre-commit-config.yaml

protected_override: >
  The `exclude` line on the `check-added-large-files` hook in .pre-commit-config.yaml: approved in
  chat, 2026-11-21.

impact_map: >
  writers: none; no table, model or page output changes.
  guard: the `check-added-large-files` hook (pre-commit-hooks v5.0.0, `--maxkb=1024`) gains
  `exclude: ^site_v2/src/data/`. Files under that folder are generated page data; main already holds
  team JSON files there of about 1.4 MB, and the approved feature branch for #297 adds two more of
  1.3 MB and 1.15 MB, which the hook refuses today. Every other path keeps the 1 MB limit.
  readers: pre-commit reads the file locally and in the `lint:python` CI job; no repo script parses
  the key. The other hooks in the file already exclude the same folder.
  failure: if the pattern did not match, the state is the one before this change: large data files
  are refused. A pattern that matched too much would need to start with something other than
  `site_v2/src/data/`; it is anchored at the repository root.
  tests: none added; the change is one configuration line.
  blast_radius: one hook setting.

approved_design:
  - none: no page output changes

depends_on:
  - none: the change stands alone on main

shared_files:
  - none: no design, registry, font or chart baseline changes

decisions_taken: >
  The exclusion is approved in chat, 2026-11-21. No new dependency, no recurring cost.

decisions_reserved:
  - none: the exclusion is the approved change.

done_when:
  - .pre-commit-config.yaml parses as YAML and the `check-added-large-files` hook carries `exclude: ^site_v2/src/data/`.
  - python scripts/ci_local.py --mr is green.
  - the MR pipeline is green and python scripts/merge_ready.py <iid> says ready.

amendments: (none)
