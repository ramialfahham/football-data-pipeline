# Task contract — point the live match-preview data at the catalogue (#500 PR-d, step 2)

> Governance G2/G3 contract. Written on a clean tree BEFORE any edit.
> CPO-approved architecture (this session): the metric_catalogue.csv SSoT stays clean (defines
> metrics); the live display-wiring (which JSON column feeds each number + render context) lives in a
> small separate file; the export composes the two. Invisible swap — byte-identical output.

objective: >
  Switch the producer of site/match-preview/metric_definitions.json from the legacy
  metric_definitions.csv seed to (metric_catalogue.csv + a new small bindings file), then delete the
  legacy seed. The generated JSON must stay byte-for-byte identical to today's. After this, the live
  match-preview site is fed by the single SSoT (the catalogue) plus a thin UI-wiring file, and the
  duplicate legacy seed is gone. No visible change; translations + page code untouched; catalogue unchanged.

refs: #500 PR-d step 2 (follows #582 = step 1, WC-block deletion); plan
  C:\Users\Rami\.claude\plans\scalable-snuggling-lightning.md (approved).

scope_paths:
  - site/match-preview/metric_bindings.csv
  - scripts/export_metric_definitions_json.py
  - dbt_project/seeds/metric_definitions.csv
  - dbt_project/seeds/schema.yml
  - tests/test_metric_definitions_seed.py
  - tests/test_metric_bindings.py

impact_map: >
  WRITERS / LINEAGE:
    - site/match-preview/metric_definitions.json — sole writer is scripts/export_metric_definitions_json.py.
      Input today = metric_definitions.csv. After = metric_bindings.csv (live ids + column wiring + context)
      + metric_catalogue.csv (format + lower_is_better/direction). Output unchanged (byte-identical).
    - VERIFIED catalogue parity: all 13 live ids map to a catalogue row, and format + direction are
      IDENTICAL for every one (re-checked post-#582; zero mismatches, zero missing).
  CALLERS OF THE EXPORT (must keep working): pages-match-preview.yml:129 and export_matchday_insights.ps1:14
    both invoke `python scripts/export_metric_definitions_json.py` with NO args → default-driven. New defaults
    (--bindings, --catalogue, --out) keep them working; the script's CLI gains args but breaks no caller.
  CONSUMERS / BLAST RADIUS:
    - site/match-preview/index.html renders only the 13 ids in metric_manifest.json from the JSON; JSON is
      byte-identical → zero UI effect. Translations + manifest + page code untouched.
    - dbt: zero model/test refs to the metric_definitions seed (only its own schema.yml:151 entry; verified
      clean of target/). Deleting the seed + its schema block is warehouse-clean.
    - Deploy (pages-match-preview.yml): regenerates the JSON at deploy with no args → byte-identical. The
      now-stale trigger line `dbt_project/seeds/metric_definitions.csv` is HARMLESS (any real bindings/catalogue
      edit must change the committed JSON — enforced by the new regen test — and the JSON is itself a trigger,
      so auto-deploy still fires). Updating the workflow trigger list is a PROTECTED-path follow-up, OUT of scope.
  LAYER RULES: metric_bindings.csv = UI display-wiring config → lives in site/match-preview/ beside
    metric_manifest.json (NOT a dbt seed; no model reads it). The export composes catalogue (definition:
    format/direction) + bindings (wiring: columns/context) and SELECTS/RENAMES into JSON — no fact derivation,
    no computation (consumption-layer compliant). The catalogue SSoT is read-only here.
  DEPLOY ORDERING: static files; the export is deterministic; commit the regenerated (identical) JSON so the
    committed artifact stays in sync. No migration / no full-refresh.

decisions_taken: >
  Execute the CPO-approved swap: catalogue stays the clean metric SSoT (unchanged); live wiring in the new
  metric_bindings.csv; export composes the two; legacy seed deleted. No metric added/changed; no §10 here —
  the architecture (catalogue-clean + separate wiring) was decided by the CPO earlier this session.

decisions_reserved:
  - The single i18n/labelling scheme (step 3 — CPO decision), corners _conceded→_against rename (step 4),
    the team-season _season suffix drop (step 5), final teardown of build_match_preview_site + dead labels
    (step 6). NONE here. The pages-match-preview.yml trigger-list tidy (protected path) is a separate follow-up.

done_when:
  - The export builds the JSON from metric_bindings.csv + metric_catalogue.csv; regenerating yields a
    byte-identical site/match-preview/metric_definitions.json (`git diff --exit-code` clean).
  - The legacy metric_definitions.csv + its schema.yml block are gone; tests/test_metric_definitions_seed.py
    is replaced by tests/test_metric_bindings.py which (a) checks every binding's catalogue id resolves +
    paired columns, and (b) regenerates the JSON and asserts it equals the committed file (the durable
    byte-identity guard).
  - validate-local green (incl. the new test); no dbt model affected.
  - Routes to: scope-auditor (always) + analytics-engineer (dbt_project/** + scripts/export_*.py) + cto
    (scripts/export_*.py + tests/**). The commit carries contract.md → NOT artifact-exempt. CPO merges.

amendments: (none)
