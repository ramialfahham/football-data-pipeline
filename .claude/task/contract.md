# Task contract — handover refresh + §8 NT-context doc-sync (post-#655/#654)

> Written on a CLEAN tree (branch chore/handover-nt-docsync-post-655 off main @ 712f16b).
> Doc-only. Handover refresh (bookkeeping) + de-stale metrics_context_model.md §8 after the NT-context
> thread closed. Plan mode skipped per the CPO handover carve-out + CPO's explicit go on the doc loose ends;
> contract + review + gate run. Required reviewer (routing): scope-auditor only (no dbt/scripts/CI/wireframe path).

objective: >
  (1) Bring `.claude/active_work.md` current from post-#653 (pointer c4489aa) to post-#655 (712f16b): record #655
  MERGED+CLOSED (season-record campaign=season note cleanup), #654 CLOSED as no-consumer (recent NT context is
  served on the national fixture preview via momentum #653 + the career NT record via the Career screen #634; a
  standing profile block failed display-first), the two concurrent-session merges (450c205 squad /players
  skip-if-cached; 81eb1ed exclude All-Star teams from player affiliation), and this doc-sync. National-team window
  thread is now fully SETTLED; #3 (career NT by competition type) stays PARKED on ingest. NEXT = an open CPO pick.
  (2) De-stale `docs/metrics_context_model.md` §8: the §8-intro + §8.7 "#480/#484 build follow-ups (not built)"
  references and the §8.4 `form_window_kind` enum claim — #480 shipped (#630), #484 closed, #654 closed, and the
  promised catalogue enum was never added (the window kinds live as the models' window_type accepted_values).
refs: #655 (712f16b, merged+closed); #654 (closed, no consumer); #653 (#484, merged); #630 (#480); #634 (Career); #3 (parked).

scope_paths:
  - .claude/active_work.md
  - docs/metrics_context_model.md
  - .claude/task/**

impact_map: >
  Doc-only, no structural surface. `.claude/active_work.md` (handover) + `docs/metrics_context_model.md` (a spec
  doc, no code binding) + the task scaffolding. No dbt_project/** model, no scripts/export_*.py, no ingestion/**,
  no site*/ — zero data/number/metric/build impact. metrics_context_model.md is not referenced by any model
  (it's prose governance), so editing it changes no compiled SQL. contract.md is artifact_only_never → scope-auditor required.

decisions_taken: >
  Record-only. #655 merged+closed, #654 closed, #480 shipped — all already happened (CPO-directed this session).
  The §8 edits REMOVE stale build-follow-up references + a false "enum was set in the catalogue" claim; they
  invent no new decision. The window SET stays fixed by the §4 matrix (unchanged); only the realization note is
  corrected (window_type accepted_values, not a catalogue form_window_kind column).

decisions_reserved:
  - The actual next task — CPO picks later (candidates: task_f876b853 chip; #545–#547 programs; #530(c)
    model-conformance test; portfolio social-preview image). #3 career-NT-by-type parked on a data/cost call.

done_when:
  - active_work.md header + FIRST STEPS point at 712f16b; #655 recorded merged+closed; #654 recorded closed
    (no consumer); the concurrent merges noted; NEXT is an open CPO pick (national-team thread fully settled).
  - metrics_context_model.md §8-intro + §8.4 + §8.7 no longer claim #480/#484 are unbuilt follow-ups or that a
    form_window_kind catalogue enum was set; they reflect: #480 shipped, national context served (fixture strip +
    Career section), #654 closed, window kinds = window_type accepted_values.
  - scope-auditor PASS (>=2 named risks); review.md diff_sha256 binds; CPO merges.

amendments: (none)
