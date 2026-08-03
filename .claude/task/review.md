# Review — chore/handover-ingest-and-cost — 2026-08-03

branch: chore/handover-ingest-and-cost
diff_sha256: a6f53f1d7f980bead1d17bc1dc32ba55b01b968dc03a777f638f0c0c58abc3a4

rounds: 1
# Only `scope-auditor` is required: the diff touches `.claude/task/contract.md` and
# `.claude/active_work.md`, and no routing row matches either. The commit is NOT artifact-exempt,
# because `contract.md` is never artifact-exempt (F10/#409).

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: the only file in the reviewed patch is `contract.md`, which is in `scope_paths`.
  `.claude/active_work.md` is correctly absent from the patch because it sits in
  `review_exclude_paths`, and was read from the working tree instead.
- Accuracy, spot-checked against the code rather than taken on trust: `settings.py:146` does default
  `API_FOOTBALL_REQUEST_PAUSE_MS` to 0 under the `full` profile; `loads/squads.py:35-66` does delete
  prior rows for the same key after appending; the "tables grew while data was destroyed" claim is
  coherent, because failed responses add an empty row and delete the good one while successful
  fetches add more; the coaches full-snapshot behaviour matches the 2026-06-23 CPO ruling in
  `escalations.log`; `stg_apif__squads` has zero consumers outside its own schema test, verified by
  grep.
- The `transfers` healing is stated as UNVERIFIED, which is accurate: healing is verified in code but
  not yet observed in a completed run, and the handover gives the query that would settle it.
- "No public site" is correct and the ingest findings are not overstated as a live user incident.
- `decisions_taken: None` is accurate. Every item either records a decision already made with its
  authority, or is listed as open.
- The standing correction-replaces rule is honoured: grep found no "an earlier version said X"
  narration anywhere in the rewrite; corrected cost claims appear in final form only.
- Threshold declarations match the diff: no new mechanism, and "none" for recurring cost is safe here
  because the diff contains no executable line.
- Appendix A: none of A1 to A6 apply. No credential or secret in the diff.

## escalations
(none)
